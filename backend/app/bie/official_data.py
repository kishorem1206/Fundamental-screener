"""Official production data for the report's sector part: the Index of
Industrial Production by industry group (MoSPI) and the Index of Eight Core
Industries (Office of the Economic Adviser). Both are government series,
free, and apply to every company in the matching industry.

MoSPI's API fails the TLS handshake from Python's HTTP stack on this
machine but answers `curl`, so it is fetched through curl with certificate
checking off; the response is archived and facts are read from the archive.
"""
from __future__ import annotations

import io
import json
import re
import subprocess
from datetime import date, datetime, timedelta, timezone

import requests
from sqlalchemy.orm import Session

from app.bie.documents import archive, content_of
from app.bie.evidence import clear_document_facts, record_fact
from app.bie.macro import _BROWSER
from app.infrastructure.database.models import BieFact, Document

IIP_URL = "https://api.mospi.gov.in/api/iip/getIIPAnnual?Format=JSON&limit=100&base_year=2011-12&type=Sectoral&financial_year={fy}"
CORE_PAGE = "https://eaindustry.nic.in/ici_download_data.asp"
_FRESH = timedelta(days=25)
_YEARS = 5

# NSE industry / basic-industry name -> IIP industry group. First match wins.
_IIP_MAP = [
    (r"cigarette|tobacco", "Manufacture of Tobacco Products"), (r"pharma|biotech", "Manufacture of basic pharmaceutical products and pharmaceutical preparations"),
    (r"breweries|distiller|beverage", "Manufacture of Beverages"),
    (r"packaged food|food product|dairy|edible oil|sugar|tea|coffee|meat|seafood|agricultural food|diversified fmcg", "Manufacture of Food Products"),
    (r"garment|apparel", "Manufacture of Wearing Apparel"), (r"textile|cotton|yarn|fabric", "Manufacture of Textiles"), (r"footwear|leather", "Manufacture of Leather and Related Products"),
    (r"paper|packaging", "Manufacture of Paper and Paper Products"), (r"printing|publication", "Printing and Reproduction of Recorded Media"),
    (r"refiner|petroleum|lubricant", "Manufacture of Coke and Refined Petroleum Products"),
    (r"tyre|rubber|plastic", "Manufacture of Rubber and Plastics Products"),
    (r"chemical|fertili|pesticide|paint|dyes|explosive|personal care|household", "Manufacture of Chemicals and Chemical Products"),
    (r"cement|ceramic|glass|tiles|sanitary|refractor", "Manufacture of Other Non-metallic Mineral Products"),
    (r"steel|iron|alumin|copper|zinc|ferro|metal", "Manufacture of Basic Metals"), (r"casting|forging|fastener", "Manufacture of Fabricated Metal Products, Except Machinery and Equipment"),
    (r"computer|electronic|semiconductor|telecom.*equipment|it - hardware", "Manufacture of Computer, Electronic and Optical Products"),
    (r"electrical equipment|cable|transformer|household appliance|consumer electronics|durable", "Manufacture of Electrical Equipment"),
    (r"passenger car|commercial vehicle|auto component|auto ancillar|tractor|automobile", "Manufacture of Motor Vehicles, Trailers and Semi-trailers"),
    (r"2/3 wheeler|ship|railway|aerospace|defen[cs]e", "Manufacture of Other Transport Equipment"),
    (r"machin|industrial product|compressor|pump|bearing|capital goods|abrasive", "Manufacture of Machinery and Equipment n.e.c."),
    (r"furniture", "Manufacture of Furniture"), (r"mining|mineral|coal", "Mining"), (r"power|electric", "Electricity"),
]
_CORE_MAP = [(r"coal", "Coal"), (r"gas (transmission|distribution)|lpg|cng|oil exploration", "Natural Gas"), (r"oil exploration", "Crude Oil"),
             (r"refiner|petroleum", "Refinery Products"), (r"fertili", "Fertilizers"), (r"steel|iron", "Steel"), (r"cement", "Cement"),
             (r"power|electric", "Electricity")]


def iip_group(*names: str | None) -> str | None:
    for name in names:
        for pattern, target in _IIP_MAP if name else []:
            if re.search(pattern, name, re.I):
                return target
    return None


def core_series(*names: str | None) -> list[str]:
    return list(dict.fromkeys(target for name in names if name for pattern, target in _CORE_MAP if re.search(pattern, name, re.I)))


def _recent(db: Session, prefix: str) -> bool:
    latest = db.query(Document).filter(Document.document_type.like(f"{prefix}%")).order_by(Document.retrieved_at.desc()).first()
    return latest is not None and datetime.now(timezone.utc) - latest.retrieved_at < _FRESH


def ingest_iip(db: Session) -> int:
    today = date.today()
    last = today.year if today.month >= 6 else today.year - 1  # the latest completed April–March year with annual data
    written = 0
    for end_year in range(last, last - _YEARS, -1):
        fy = f"{end_year - 1}-{str(end_year)[2:]}"
        url = IIP_URL.format(fy=fy)
        raw = subprocess.run(["curl", "-sS", "-k", "-m", "60", "-A", "Mozilla/5.0", url], capture_output=True, timeout=90).stdout
        rows = (json.loads(raw).get("data") if raw else None) or []
        if not rows:
            continue
        document = archive(db, company_id=None, source="MoSPI", document_type=f"MOSPI_IIP_{fy}", url=url, content=raw,
                           content_type="application/json", period_end=date(end_year, 3, 31),
                           title=f"Index of Industrial Production by industry group, {fy} (base 2011-12)", published_at=datetime.now(timezone.utc))
        if document is None:
            continue
        clear_document_facts(db, document)
        archived = (content_of(document) or raw).decode("utf-8", "replace")
        for row in rows:
            group = row["sub_category"] or row["category"]
            for key, field, unit in (("production_index", "index", "index"), ("production_growth_pct", "growth_rate", "%")):
                try:
                    value = float(row[field])
                except (TypeError, ValueError):
                    continue
                quote = f'"{field}":"{row[field]}"'
                fact = record_fact(
                    db, scope="SECTOR", sector=f"IIP | {group}", fact_type="industry_output", key=key, period_type="FY",
                    period_end=date(end_year, 3, 31), value_num=value, unit=unit, nature="THIRD_PARTY", document=document,
                    locator_type="JSON", locator=f"data[sub_category='{row['sub_category']}', category='{row['category']}'].{field}",
                    quote=quote, extraction_method="API_JSON", source_tier=1, confidence="HIGH", replace=False)
                fact.verification_status = "VERIFIED" if quote in archived else "FAILED"
                fact.verified_at = datetime.now(timezone.utc)
                written += 1
        document.link_status, document.link_checked_at = 200, datetime.now(timezone.utc)
        db.commit()
    return written


def ingest_core(db: Session) -> int:
    import pandas as pd

    page = requests.get(CORE_PAGE, headers=_BROWSER, timeout=45)
    page.raise_for_status()
    links = sorted(set(re.findall(r'href="([^"]*Core_Industries_\d{4}_\d{2}_\d{8}\.xlsx)"', page.text)), key=lambda l: l[-13:-5])
    if not links:
        raise ValueError("no Eight Core Industries workbook linked from the download page")
    url = requests.compat.urljoin(CORE_PAGE, links[-1])
    response = requests.get(url, headers=_BROWSER, timeout=90)
    response.raise_for_status()
    released = datetime.strptime(links[-1][-13:-5], "%Y%m%d").replace(tzinfo=timezone.utc)
    document = archive(db, company_id=None, source="Office of the Economic Adviser, DPIIT", document_type="OEA_CORE_INDUSTRIES", url=url,
                       content=response.content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       period_end=released.date(), title=f"Index of Eight Core Industries, released {released:%d %b %Y}", published_at=released)
    if document is None:
        return 0
    clear_document_facts(db, document)
    sheet = pd.ExcelFile(io.BytesIO(content_of(document) or response.content)).parse(0, header=None)
    head = next(i for i in range(len(sheet)) if str(sheet.iloc[i, 0]).strip().startswith("Months"))
    names = [str(x).strip() for x in sheet.iloc[head].tolist()]
    written = 0
    for i in range(head + 1, len(sheet)):
        label = str(sheet.iloc[i, 0]).strip()
        if "(Apr-" not in label:
            continue  # keep the annual and year-to-date rows, not each month
        for j, name in enumerate(names[1:], 1):
            try:
                value = float(sheet.iloc[i, j])
            except (TypeError, ValueError):
                continue
            if value != value:
                continue
            fact = record_fact(
                db, scope="SECTOR", sector=f"Core | {name}", fact_type="industry_output", key="core_index", dimension=label,
                period_type="YTD" if "Apr-Mar" not in label else "FY", period_end=released.date(), value_num=value, unit="index",
                nature="THIRD_PARTY", document=document, locator_type="TABLE", locator=f"row '{label}', column '{name}'",
                quote=str(sheet.iloc[i, j]), extraction_method="SPREADSHEET", source_tier=1, confidence="HIGH", replace=False)
            fact.verification_status, fact.verified_at = "VERIFIED", datetime.now(timezone.utc)
            written += 1
    try:
        document.link_status = requests.get(url, headers=_BROWSER, timeout=30, stream=True).status_code
    except Exception:  # noqa: BLE001
        document.link_status = None
    document.link_checked_at = datetime.now(timezone.utc)
    db.commit()
    return written


def ingest_official_data(db: Session, force: bool = False) -> dict:
    out = {}
    for name, prefix, run in (("iip", "MOSPI_IIP", ingest_iip), ("core_industries", "OEA_CORE", ingest_core)):
        if not force and _recent(db, prefix):
            out[name] = "fresh"
            continue
        try:
            out[name] = run(db)
        except Exception as e:  # noqa: BLE001
            db.rollback()
            out[name] = f"failed: {type(e).__name__}: {e}"
    return out


def output_for(db: Session, basic_industry: str | None, industry: str | None) -> dict | None:
    """Production index history for the industry group this classification maps to, plus any core-industry series."""
    group = iip_group(basic_industry, industry)
    cores = core_series(basic_industry, industry)
    if not group and not cores:
        return None
    result: dict = {"group": group, "years": [], "core": [], "facts": []}
    if group:
        facts = db.query(BieFact).filter(BieFact.scope == "SECTOR", BieFact.sector == f"IIP | {group}", BieFact.fact_type == "industry_output").all()
        by_year: dict[date, dict] = {}
        for f in facts:
            by_year.setdefault(f.period_end, {})[f.key] = f
        for end in sorted(by_year):
            row = by_year[end]
            result["years"].append({"label": f"FY{str(end.year)[2:]}", "index": float(row["production_index"].value_num) if "production_index" in row else None,
                                    "growth": float(row["production_growth_pct"].value_num) / 100 if "production_growth_pct" in row else None})
            result["facts"] += list(row.values())
    for name in cores:
        facts = db.query(BieFact).filter(BieFact.scope == "SECTOR", BieFact.sector == f"Core | {name}", BieFact.fact_type == "industry_output").all()
        latest = max((f.period_end for f in facts), default=None)
        rows = {f.dimension: f for f in facts if f.period_end == latest}
        annual = sorted((d for d in rows if "Apr-Mar" in d))
        ytd = sorted((d for d in rows if "Apr-Mar" not in d))
        entry = {"name": name, "annual": None, "ytd": None}
        if len(annual) >= 2:
            a, b = rows[annual[-2]], rows[annual[-1]]
            entry["annual"] = {"label": annual[-1].split("(")[0], "growth": float(b.value_num) / float(a.value_num) - 1}
        if len(ytd) >= 2:
            a, b = rows[ytd[-2]], rows[ytd[-1]]
            entry["ytd"] = {"label": ytd[-1], "growth": float(b.value_num) / float(a.value_num) - 1}
        if entry["annual"] or entry["ytd"]:
            result["core"].append(entry)
            result["facts"] += list(rows.values())
    return result if result["years"] or result["core"] else None
