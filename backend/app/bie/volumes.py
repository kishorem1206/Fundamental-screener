"""Unit volumes from sector bodies, for the report's sector part: vehicle
retail sales (FADA, from the government's VAHAN registrations), mobile
subscribers and operator shares (TRAI), airport traffic (AAI), mutual-fund
assets and flows (AMFI), life insurers' new business premium (IRDAI) and
general insurers' gross premium (General Insurance Council).

Every monthly release is kept, so the report can show a year's trend; a
release already archived is not downloaded again. Each figure is cited to
the page or the spreadsheet cell it was read from.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from app.bie.annual_report_extract import page_texts
from app.bie.documents import archive, content_of
from app.bie.evidence import clear_document_facts, quote_on_page, record_fact
from app.bie.macro import _BROWSER
from app.infrastructure.database.models import BieFact, Document

_FRESH = timedelta(days=7)
_MONTHS_KEPT = 13
_MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
_MONTHS |= {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}


def _month_end(month: str, year: int) -> date:
    m = _MONTHS[month.lower()]
    return date(year, m, calendar.monthrange(year, m)[1])


def _num(text: str) -> float:
    return float(text.replace(",", ""))


def _hrefs(url: str, pattern: str) -> list[str]:
    html = requests.get(url, headers=_BROWSER, timeout=45).text
    return [requests.compat.urljoin(url, l.replace("&amp;", "&").replace(" ", "%20"))
            for l in dict.fromkeys(re.findall(r'href="([^"]+)"', html)) if re.search(pattern, l, re.I)]


def _already_read(db: Session, url: str) -> bool:
    return db.query(BieFact.id).join(Document, Document.id == BieFact.document_id).filter(
        Document.url == url, BieFact.fact_type == "unit_volume").first() is not None


class _Release:
    """One archived monthly release and the facts read from it."""

    def __init__(self, db: Session, *, sector: str, source: str, document_type: str, url: str, title: str, period_end: date,
                 content: bytes | None = None, spreadsheet: bool = False):
        self.db, self.sector, self.period_end, self.spreadsheet = db, sector, period_end, spreadsheet
        if content is None:
            response = requests.get(url, headers=_BROWSER, timeout=120)
            response.raise_for_status()
            content = response.content
        response = type("R", (), {"content": content, "status_code": 200})
        self.document = archive(db, company_id=None, source=source, document_type=document_type, url=url, content=response.content,
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if spreadsheet else "application/pdf",
                                title=title, period_end=period_end, published_at=datetime.now(timezone.utc))
        self.content = (content_of(self.document) or content) if self.document else content
        self.texts = page_texts(self.content) if self.document and not spreadsheet else []
        self.written, self.keys = 0, set()
        if self.document:
            clear_document_facts(db, self.document)
            self.document.link_status, self.document.link_checked_at = response.status_code, datetime.now(timezone.utc)

    def add(self, key: str, dimension: str, value: float, unit: str, page: int, quote: str, attributes: dict | None = None) -> None:
        fact = record_fact(
            self.db, scope="SECTOR", sector=self.sector, fact_type="unit_volume", key=key, dimension=dimension, period_type="MONTH",
            period_end=self.period_end, value_num=value, unit=unit, attributes=attributes, nature="THIRD_PARTY", document=self.document,
            locator_type="PAGE", page=page + 1, quote=quote, extraction_method="PDF_TEXT", source_tier=1, confidence="HIGH", replace=False)
        fact.verification_status = "VERIFIED" if quote_on_page(quote, self.texts[page]) else "FAILED"
        fact.verified_at = datetime.now(timezone.utc)
        self.written += 1
        self.keys.add((key, dimension))

    def cell(self, key: str, dimension: str, value: float, unit: str, where: str, raw, attributes: dict | None = None) -> None:
        """A figure read from a cell of the archived spreadsheet."""
        fact = record_fact(
            self.db, scope="SECTOR", sector=self.sector, fact_type="unit_volume", key=key, dimension=dimension, period_type="MONTH",
            period_end=self.period_end, value_num=value, unit=unit, attributes=attributes, nature="THIRD_PARTY", document=self.document,
            locator_type="TABLE", locator=where, quote=str(raw), extraction_method="SPREADSHEET", source_tier=1, confidence="HIGH", replace=False)
        fact.verification_status, fact.verified_at = "VERIFIED", datetime.now(timezone.utc)  # read from the archived copy itself
        self.written += 1
        self.keys.add((key, dimension))


def ingest_vehicle_retail(db: Session) -> int:
    links = _hrefs("https://fada.in/press-release-list.php", r"\d{4}(?:%20| )Vehicle(?:%20| )Retail")
    if not links:
        raise ValueError("no monthly vehicle retail release listed")
    written = 0
    # The category table every release carries: this month, last month, a year earlier, and the two changes.
    row = re.compile(r"(?m)^(2W|3W|PV|TRAC|CV|Total)\s+([\d,]+)\s+[\d,]+\s+[\d,]+\s+-?[\d.]+%\s+(-?[\d.]+)%\s*$")
    labels = {"2W": "Two-Wheelers", "3W": "Three-Wheelers", "PV": "Passenger Vehicles", "TRAC": "Tractors", "CV": "Commercial Vehicles", "Total": "Total"}
    for url in links[:_MONTHS_KEPT]:
        if _already_read(db, url):
            continue
        month, year = re.search(r"%20([A-Za-z]+)%20(\d{4})%20Vehicle%20Retail", url).groups()
        if month.lower() not in _MONTHS:
            continue
        release = _Release(db, sector="Vehicles", source="FADA", document_type="FADA_VEHICLE_RETAIL", url=url,
                           title=f"FADA vehicle retail data, {month} {year}", period_end=_month_end(month, int(year)))
        if not release.document:
            continue
        seen = set()
        for page, text in enumerate(release.texts[:8]):
            for m in row.finditer(text):
                if m.group(1) not in seen:
                    seen.add(m.group(1))
                    release.add("retail_units", labels[m.group(1)], _num(m.group(2)), "units", page, m.group(0), {"change_yoy": float(m.group(3)) / 100})
        written += release.written
        db.commit()
    return written


def ingest_airport_traffic(db: Session) -> int:
    links = _hrefs("https://www.aai.aero/en/business-opportunities/aai-traffic-news", r"traffic-news/TR\w+\.pdf")
    if not links:
        raise ValueError("no air traffic report listed")
    written = 0
    for url in links[:_MONTHS_KEPT]:
        if _already_read(db, url):
            continue
        content = requests.get(url, headers=_BROWSER, timeout=90).content
        try:
            head = re.search(r"AIR TRAFFIC REPORT\W+([A-Za-z]+)\s*,?\s*(\d{4})", page_texts(content)[0])
        except Exception:  # noqa: BLE001 — an unreadable month is skipped, the others are kept
            head = None
        if not head or head.group(1).lower() not in _MONTHS:
            continue
        release = _Release(db, sector="Aviation", source="Airports Authority of India", document_type="AAI_TRAFFIC", url=url, content=content,
                           title=f"AAI air traffic report, {head.group(1).title()} {head.group(2)}",
                           period_end=_month_end(head.group(1), int(head.group(2))))
        if not release.document:
            continue
        text = release.texts[0]
        for key, heading, unit in (("passengers_million", r"Passengers \(in million\)", "million"),
                                   ("freight_thousand_tonnes", r"Freight\(in .000 ton\)", "thousand tonnes")):
            block = re.search(heading + r"(.*?)(?:Freight|CATEGORY|$)", text, re.S)
            if not block:
                continue
            for label in ("International", "Domestic", "Total"):
                m = re.search(rf"{label}\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)", block.group(1))
                if m:
                    release.add(key, label, float(m.group(1)), unit, 0, m.group(0), {"change_yoy": float(m.group(3)) / 100})
        # The table is a picture in some months: the opening sentence still gives the totals.
        m = re.search(r"([\d.]+)\s+million\s+passengers\s+and\s+([\d.]+)\s+thousand\s+tonnes\s+of\s+freight", text)
        for key, group, unit in (("passengers_million", 1, "million"), ("freight_thousand_tonnes", 2, "thousand tonnes")):
            if m and (key, "Total") not in release.keys:
                release.add(key, "Total", float(m.group(group)), unit, 0, m.group(0))
        written += release.written
        db.commit()
    return written


def ingest_mutual_funds(db: Session) -> int:
    links = _hrefs("https://www.amfiindia.com/research-information/amfi-monthly", r"spages/am[a-z]{3}\d{4}repo\.pdf")
    if not links:
        raise ValueError("no AMFI monthly report listed")
    links.sort(key=lambda u: (int(re.search(r"am[a-z]{3}(\d{4})", u).group(1)), _MONTHS[re.search(r"am([a-z]{3})\d{4}", u).group(1)]), reverse=True)
    amount = r"(-?[\d,]+\.\d{2})"
    rows = (("Grand Total", "Industry total"), ("Sub Total - II", "Equity-oriented schemes"), ("Sub Total - I", "Debt-oriented schemes"))
    written = 0
    for url in links[:_MONTHS_KEPT]:
        if _already_read(db, url):
            continue
        month, year = re.search(r"am([a-z]{3})(\d{4})repo", url).groups()
        try:
            release = _Release(db, sector="Mutual funds", source="AMFI", document_type="AMFI_MONTHLY", url=url,
                               title=f"AMFI monthly report, {calendar.month_name[_MONTHS[month]]} {year}", period_end=_month_end(month, int(year)))
        except Exception:  # noqa: BLE001
            continue
        if not release.document:
            continue
        for marker, label in rows:
            pattern = re.compile(rf"{re.escape(marker)}(?![IV])(?: \([^)]*\))?\s+([\d,]+)\s+([\d,]+)\s+{amount}\s+{amount}\s+{amount}\s+{amount}\s+{amount}")
            for page, text in enumerate(release.texts):
                m = pattern.search(re.sub(r"[ \t]+", " ", text))
                if not m:
                    continue
                quote = m.group(0)
                release.add("assets_under_management_crore", label, _num(m.group(6)), "INR crore", page, quote)
                release.add("net_inflow_crore", label, _num(m.group(5)), "INR crore", page, quote)
                if label == "Industry total":
                    release.add("investor_folios", label, _num(m.group(2)), "count", page, quote)
                break
        written += release.written
        db.commit()
    return written


def ingest_telecom_subscribers(db: Session) -> int:
    from app.ingestion.trai_client import _BASE, _LIST_URL, parse_report

    html = requests.get(_LIST_URL, headers={**_BROWSER, "Referer": _BASE}, timeout=45).text
    links = list(dict.fromkeys(re.findall(r'href="(/sites/default/files/[^"]+PR_No[^"]+\.pdf)"', html)))
    names = {"jio": "Reliance Jio", "airtel": "Bharti Airtel", "vi": "Vodafone Idea", "bsnl": "BSNL", "mtnl": "MTNL"}
    written = 0
    for link in links[:_MONTHS_KEPT]:
        url = _BASE + link
        if _already_read(db, url):
            continue
        try:
            content = requests.get(url, headers=_BROWSER, timeout=120).content
            texts = page_texts(content)
        except Exception:  # noqa: BLE001
            continue
        parsed = parse_report("\n".join(texts))
        if not parsed:
            continue
        end = date.fromisoformat(parsed["month_end"])
        release = _Release(db, sector="Telecom", source="TRAI", document_type="TRAI_SUBSCRIBERS", url=url, content=content,
                           title=f"TRAI telecom subscription data, {end:%B %Y}", period_end=end)
        if not release.document:
            continue
        # The Annexure row the figures were computed from, quoted from the page it sits on.
        page, quote = next(((i, line.strip()) for i, t in enumerate(release.texts) for line in t.splitlines()
                            if re.match(r"\s*total\s+\d{1,3}(?:,\d{3})+", line, re.I) and len(re.findall(r"\d{1,3}(?:,\d{3})+", line)) >= 12), (None, None))
        if page is None:
            continue
        release.add("wireless_subscribers_million", "All operators", parsed["total_mn"], "million", page, quote)
        for operator, share in sorted(parsed["shares"].items(), key=lambda kv: -kv[1]):
            release.add("wireless_subscriber_share", names[operator], share / 100, "ratio", page, quote)
        written += release.written
        db.commit()
    return written


def ingest_life_insurance(db: Session) -> int:
    """IRDAI's monthly new-business statement: first-year premium for the month, by insurer."""
    import io

    import pandas as pd

    html = requests.get("https://irdai.gov.in/monthly-business-figures1", headers=_BROWSER, timeout=45).text
    links = [l.replace("&amp;", "&") for l in dict.fromkeys(re.findall(r'href="([^"]+/documents/37343/365644/[^"]+)"', html))]
    written = 0
    for url in links[:_MONTHS_KEPT]:
        stamp = re.search(r"365644/(\d\d)\.(\d\d)\.(\d{4})", url)
        if not stamp or _already_read(db, url):
            continue
        end = date(int(stamp.group(3)), int(stamp.group(2)), int(stamp.group(1)))
        try:
            release = _Release(db, sector="Life insurance", source="IRDAI", document_type="IRDAI_LIFE_NEW_BUSINESS", url=url, spreadsheet=True,
                               title=f"IRDAI first-year premium of life insurers, {end:%B %Y}", period_end=end)
            book = pd.ExcelFile(io.BytesIO(release.content))  # some months carry a Hindi sheet ahead of the English one
            sheet = next(sh for sh in (book.parse(n, header=None) for n in book.sheet_names) if (sh[1].astype(str).str.strip() == "Grand Total").any())
        except Exception:  # noqa: BLE001
            continue
        if not release.document:
            continue
        for i in range(3, len(sheet)):
            serial, name = str(sheet.iloc[i, 0]).strip(), str(sheet.iloc[i, 1]).strip()
            is_insurer = serial.replace(".0", "").isdigit()
            if not (is_insurer or name in ("Private Total", "Grand Total")):
                continue
            try:
                month_premium, growth = float(sheet.iloc[i, 3]), float(sheet.iloc[i, 4])
            except (TypeError, ValueError):
                continue
            if month_premium != month_premium:
                continue
            share = sheet.iloc[i, 8]
            release.cell("first_year_premium_crore", "Industry total" if name == "Grand Total" else name, month_premium, "INR crore",
                         f"row '{name}', column 'For the month, current year'", sheet.iloc[i, 3],
                         {"change_yoy": growth / 100 if growth == growth else None, "is_insurer": is_insurer,
                          "market_share_ytd": float(share) / 100 if isinstance(share, (int, float)) and share == share else None})
        written += release.written
        db.commit()
    return written


def ingest_general_insurance(db: Session) -> int:
    """General Insurance Council's segment-wise gross direct premium, cumulative for the financial year to the month."""
    import io

    import pandas as pd

    links = _hrefs("https://www.gicouncil.in/segmentwise-report/", r"segment_[a-z]+_\d{4}\.xlsx")
    written = 0
    for url in links[:_MONTHS_KEPT]:
        month, year = re.search(r"segment_([a-z]+)_(\d{4})", url).groups()
        if month not in _MONTHS or _already_read(db, url):
            continue
        try:
            release = _Release(db, sector="General insurance", source="General Insurance Council", document_type="GIC_SEGMENT_PREMIUM", url=url,
                               spreadsheet=True, title=f"General Insurance Council segment-wise gross direct premium, April to {month.title()} {year}",
                               period_end=_month_end(month, int(year)))
            sheet = pd.ExcelFile(io.BytesIO(release.content)).parse("Segmentwise Report", header=None)
        except Exception:  # noqa: BLE001
            continue
        if not release.document:
            continue
        head = next(i for i in range(len(sheet)) if "Grand Total" in [str(v).strip() for v in sheet.iloc[i].tolist()])
        columns = [str(v).strip() for v in sheet.iloc[head].tolist()]
        total_col, growth_col, share_col = columns.index("Grand Total"), columns.index("Growth %"), columns.index("Market %")
        for i in range(head + 1, len(sheet)):
            name = str(sheet.iloc[i, 0]).strip()
            if not name or name == "nan" or name.startswith(("Previous Year", "% Growth", "“", "\"")) or name.endswith(("Insurers", "Insurers:")):
                continue
            try:
                total, growth = float(sheet.iloc[i, total_col]), float(sheet.iloc[i, growth_col])
            except (TypeError, ValueError):
                continue
            if total != total or growth != growth:
                continue
            share = sheet.iloc[i, share_col]
            industry = name.startswith("Industry Total")
            release.cell("gross_premium_year_to_date_crore", "Industry total" if industry else name, total, "INR crore",
                         f"sheet 'Segmentwise Report', row '{name}', column 'Grand Total'", sheet.iloc[i, total_col],
                         {"change_yoy": growth, "is_insurer": not industry and "Total" not in name,
                          "market_share_ytd": float(share) if isinstance(share, (int, float)) and share == share else None})
            if industry:
                growth_row = next((j for j in range(i + 1, min(i + 4, len(sheet))) if str(sheet.iloc[j, 0]).strip().startswith("% Growth")), None)
                for segment in ("Health", "Motor Total", "Fire"):
                    col = next((c for c, label in enumerate(columns) if label == segment), None)
                    if col is not None:
                        g = sheet.iloc[growth_row, col] if growth_row is not None else None
                        release.cell("gross_premium_year_to_date_crore", f"Industry: {segment.replace(' Total', '').lower()}", float(sheet.iloc[i, col]),
                                     "INR crore", f"sheet 'Segmentwise Report', row '{name}', column '{segment}'", sheet.iloc[i, col],
                                     {"change_yoy": float(g) if isinstance(g, (int, float)) and g == g else None})
        written += release.written
        db.commit()
    return written


def ingest_power_generation(db: Session) -> int:
    """Central Electricity Authority's monthly generation report: all-India generation by source and thermal plant load factor."""
    today, written = date.today(), 0
    year, month = today.year, today.month
    row = re.compile(r"(?m)^\s*(THERMAL|NUCLEAR|HYDRO|TOTAL)\s+((?:-?[\d.]+\s+){6,}-?[\d.]+)\s*$")
    names = {"THERMAL": "Thermal", "NUCLEAR": "Nuclear", "HYDRO": "Hydro", "TOTAL": "All sources"}
    for _ in range(_MONTHS_KEPT + 1):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        mon = calendar.month_abbr[month].upper()
        urls = [f"https://npp.gov.in/public-reports/cea/monthly/generation/18_col_act/{year}/{mon}/18_col_act-1_{year}-{mon}.pdf",
                f"https://npp.gov.in/public-reports/cea/monthly/generation/18 col act/{year}/{mon}/18 col act-1_{year}-{mon}.pdf"]
        if any(_already_read(db, u) for u in urls):
            continue
        for url in urls:
            try:
                response = requests.get(url, headers=_BROWSER, timeout=60)
            except requests.RequestException:
                continue
            if response.status_code != 200 or response.content[:4] != b"%PDF":
                continue
            release = _Release(db, sector="Power", source="Central Electricity Authority", document_type="CEA_GENERATION", url=url, content=response.content,
                               title=f"CEA monthly generation report, {calendar.month_name[month]} {year}", period_end=_month_end(mon, year))
            if not release.document:
                break
            seen = set()
            for m in row.finditer(release.texts[0]):  # the first block on the first page is the all-India summary
                if m.group(1) in seen:
                    continue
                seen.add(m.group(1))
                numbers = [float(x) for x in m.group(2).split()]
                quote = " ".join(m.group(0).split())
                actual, year_ago = numbers[3], numbers[4]
                release.add("generation_gwh", names[m.group(1)], actual, "GWh", 0, quote,
                            {"change_yoy": actual / year_ago - 1 if year_ago else None, "monitored_capacity_mw": numbers[0]})
                if m.group(1) == "THERMAL" and len(numbers) >= 15:
                    release.add("plant_load_factor", "Thermal", numbers[13] / 100, "ratio", 0, quote, {"change_yoy": None, "year_ago": numbers[14] / 100})
            written += release.written
            db.commit()
            break
    return written


SOURCES = {
    "Vehicles": ("FADA_VEHICLE_RETAIL", ingest_vehicle_retail, r"passenger car|commercial vehicle|2/3 wheeler|tractor|auto component|auto ancillar|automobile|tyre|dealer"),
    "Telecom": ("TRAI_SUBSCRIBERS", ingest_telecom_subscribers, r"telecom"),
    "Aviation": ("AAI_TRAFFIC", ingest_airport_traffic, r"airline|airport|aviation"),
    "Mutual funds": ("AMFI_MONTHLY", ingest_mutual_funds, r"asset management|capital market|mutual fund|depositor|stockbroking"),
    "Power": ("CEA_GENERATION", ingest_power_generation, r"power generation|power - |integrated power|power distribution|electric utilit"),
    "Life insurance": ("IRDAI_LIFE_NEW_BUSINESS", ingest_life_insurance, r"life insurance"),
    "General insurance": ("GIC_SEGMENT_PREMIUM", ingest_general_insurance, r"general insurance|health insurance|insurance"),
}
# The series each sector's twelve-month trend shows: (key, dimension, column heading).
HEADLINES = {
    "Vehicles": [("retail_units", "Total", "All vehicles"), ("retail_units", "Passenger Vehicles", "Passenger vehicles"), ("retail_units", "Two-Wheelers", "Two-wheelers")],
    "Telecom": [("wireless_subscribers_million", "All operators", "Subscribers (million)"), ("wireless_subscriber_share", "Reliance Jio", "Jio share"),
                ("wireless_subscriber_share", "Bharti Airtel", "Airtel share"), ("wireless_subscriber_share", "Vodafone Idea", "Vodafone Idea share")],
    "Aviation": [("passengers_million", "Total", "Passengers (million)"), ("passengers_million", "Domestic", "Domestic"), ("freight_thousand_tonnes", "Total", "Freight ('000 t)")],
    "Mutual funds": [("assets_under_management_crore", "Industry total", "Assets (₹ crore)"), ("net_inflow_crore", "Equity-oriented schemes", "Equity net inflow (₹ crore)"),
                     ("investor_folios", "Industry total", "Investor accounts")],
    "Power": [("generation_gwh", "All sources", "All generation (GWh)"), ("generation_gwh", "Thermal", "Thermal"), ("plant_load_factor", "Thermal", "Thermal plant load factor")],
    "Life insurance": [("first_year_premium_crore", "Industry total", "Industry (₹ crore)"), ("first_year_premium_crore", "Private Total", "Private insurers")],
    "General insurance": [("gross_premium_year_to_date_crore", "Industry total", "Industry, year to date (₹ crore)"),
                          ("gross_premium_year_to_date_crore", "Industry: health", "Health"), ("gross_premium_year_to_date_crore", "Industry: motor", "Motor")],
}


def ingest_volumes(db: Session, force: bool = False) -> dict:
    """Fetch any monthly release not yet archived, for every source. A source checked within the week is skipped."""
    out = {}
    for sector, (document_type, run, _) in SOURCES.items():
        latest = db.query(Document).filter(Document.document_type == document_type).order_by(Document.retrieved_at.desc()).first()
        if latest is not None and not force and datetime.now(timezone.utc) - latest.retrieved_at < _FRESH:
            out[sector] = "fresh"
            continue
        try:
            out[sector] = run(db)
            db.commit()
        except Exception as e:  # noqa: BLE001
            db.rollback()
            out[sector] = f"failed: {type(e).__name__}: {e}"
    return out


def _own_name(dimension: str, company_name: str | None) -> bool:
    """True when an insurer row is the report's own company (first two words of the names agree)."""
    if not company_name:
        return False
    key = lambda n: re.sub(r"[^a-z ]", "", n.lower()).split()[:2]  # noqa: E731
    return key(dimension) == key(company_name)


def volumes_for(db: Session, *names: str | None, company_name: str | None = None) -> dict | None:
    """The latest release, a twelve-month trend of the headline series, and the company's own row where the release names it."""
    text = " | ".join(n for n in names if n)
    sector = next((s for s, (_, _, pattern) in SOURCES.items() if re.search(pattern, text, re.I)), None)
    if sector is None:
        return None
    facts = db.query(BieFact).filter(BieFact.scope == "SECTOR", BieFact.sector == sector, BieFact.fact_type == "unit_volume").all()
    if not facts:
        return None
    months = sorted({f.period_end for f in facts})[-12:]
    latest = months[-1]
    by_key = {(f.key, f.dimension, f.period_end): f for f in facts}
    current = sorted((f for f in facts if f.period_end == latest), key=lambda f: f.created_at)
    shown = [f for f in current if not (f.attributes or {}).get("is_insurer") or _own_name(f.dimension, company_name)]
    cited = list(shown)
    trend = []
    for key, dimension, heading in HEADLINES[sector]:
        series = [by_key.get((key, dimension, m)) for m in months]
        if sum(f is not None for f in series) >= 2:
            trend.append({"heading": heading, "unit": next(f.unit for f in series if f is not None),
                          "values": [float(f.value_num) if f is not None else None for f in series]})
            cited += [f for f in series if f is not None]
    own = next((f for f in current if (f.attributes or {}).get("is_insurer") and _own_name(f.dimension, company_name)), None)
    if own is not None:
        series = [by_key.get((own.key, own.dimension, m)) for m in months]
        trend.append({"heading": own.dimension, "unit": own.unit, "values": [float(f.value_num) if f is not None else None for f in series]})
        cited += [f for f in series if f is not None]

    def row(f: BieFact) -> dict:
        attributes = f.attributes or {}
        return {"measure": re.sub(r" (crore|million|thousand tonnes)$", "", f.key.replace("_", " ")), "label": f.dimension, "value": float(f.value_num),
                "unit": f.unit, "change": attributes.get("change_yoy"), "share": attributes.get("market_share_ytd"),
                "where": f"p. {f.page}" if f.page else "sheet", "own": _own_name(f.dimension, company_name)}

    return {"sector": sector, "period": latest, "facts": cited, "rows": [row(f) for f in shown],
            "months": [m.strftime("%b %y") for m in months], "trend": trend}
