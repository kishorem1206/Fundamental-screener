"""Reading each macro source into `macro_points`. One function a source, each
returns how many points it stored and never raises: one source being down
must not stop the others. The parsers are separate from the fetching so they
can be tested on fixed text.

    MoSPI MCP   https://mcp.mospi.gov.in/ (no key): GDP, CPI, IIP, WPI, FX reserves
    RBI         the "Current Rates" block on website.rbi.org.in: policy rates,
                reserve ratios, FBIL dollar rate, call rate, G-sec yields. RBI
                keeps no history there, so these build up from the first run
    CBOE        VIX_History.csv
    Yahoo       ^TNX, DX-Y.NYB, BZ=F, GC=F (FRED's key-free CSV times out; its
                API needs a key)
    World Bank  api.worldbank.org, annual, India
"""
from __future__ import annotations

import csv
import io
import re
from calendar import monthrange
from datetime import date, datetime, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import IndexBar, MacroPoint
from app.logger import logger

MOSPI_URL = "https://mcp.mospi.gov.in/"
RBI_URL = "https://website.rbi.org.in/web/rbi"
CBOE_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
WORLD_BANK = "https://api.worldbank.org/v2/country/IND/indicator/{code}?format=json&per_page=80"
_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
_MONTHS = {m: i for i, m in enumerate(("january", "february", "march", "april", "may", "june", "july", "august", "september",
                                       "october", "november", "december"), 1)}
_QUARTER_END = {"Q1": (6, 30), "Q2": (9, 30), "Q3": (12, 31), "Q4": (3, 31)}
_YAHOO = {"us_10y": "^TNX", "dollar_index": "DX-Y.NYB", "brent": "BZ=F", "gold": "GC=F"}


def store(db: Session, points: list[tuple[str, date, float]]) -> int:
    """Upsert (series, date, value)."""
    now = datetime.now(timezone.utc)
    rows = list({(s, d): {"series": s, "on_date": d, "value": v, "retrieved_at": now} for s, d, v in points}.values())
    for i in range(0, len(rows), 2000):
        stmt = insert(MacroPoint).values(rows[i:i + 2000])
        db.execute(stmt.on_conflict_do_update(index_elements=["series", "on_date"],
                                              set_={"value": stmt.excluded.value, "retrieved_at": stmt.excluded.retrieved_at}))
    db.commit()
    return len(rows)


def month_end(year: int, month_name: str) -> date | None:
    m = _MONTHS.get(str(month_name).strip().lower())
    return date(year, m, monthrange(year, m)[1]) if m else None


def _num(v) -> float | None:
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


# ── MoSPI ────────────────────────────────────────────────────────────────────

def yoy(points: dict[date, float]) -> dict[date, float]:
    """Year-on-year change against the same period a year earlier."""
    out = {}
    for d, v in points.items():
        day = monthrange(d.year - 1, d.month)[1]
        before = points.get(date(d.year - 1, d.month, min(d.day, day)))
        if before:
            out[d] = round((v / before - 1) * 100, 2)
    return out


def parse_cpi(rows: list[dict]) -> list[tuple[str, date, float]]:
    out = []
    for r in rows:
        d, v = month_end(int(r["year"]), r["month"]), _num(r.get("inflation"))
        if d and v is not None:
            out.append(("cpi_inflation", d, v))
    return out


def parse_iip(rows: list[dict]) -> list[tuple[str, date, float]]:
    out = []
    for r in rows:
        d, v = month_end(int(r["year"]), r["month"]), _num(r.get("growth_rate"))
        if d and v is not None:
            out.append(("iip_growth", d, v))
    return out


def parse_wpi(rows: list[dict]) -> list[tuple[str, date, float]]:
    index = {}
    for r in rows:
        if r.get("group"):  # the headline row has no group
            continue
        d, v = month_end(int(r["year"]), r["month"]), _num(r.get("index_value"))
        if d and v is not None:
            index[d] = v
    return [("wpi_inflation", d, v) for d, v in yoy(index).items()]


def _fy_quarter_end(year: str, quarter: str) -> date:
    first = int(year[:4])
    month, day = _QUARTER_END[quarter]
    return date(first + (1 if quarter == "Q4" else 0), month, day)


def parse_gdp(quarters: list[dict], years: list[dict]) -> list[tuple[str, date, float]]:
    q = {_fy_quarter_end(r["year"], r["quarter"]): _num(r.get("constant_price")) for r in quarters if r.get("quarter") in _QUARTER_END}
    a = {date(int(r["year"][:4]) + 1, 3, 31): _num(r.get("constant_price")) for r in years}
    return ([("gdp_growth_q", d, v) for d, v in yoy({k: v for k, v in q.items() if v}).items()]
            + [("gdp_growth_a", d, v) for d, v in yoy({k: v for k, v in a.items() if v}).items()])


def parse_fx_reserves(rows: list[dict]) -> list[tuple[str, date, float]]:
    out = []
    for r in rows:
        if str(r.get("foreign_exchange_reserve_type", "")).strip().lower() != "total" or "US" not in str(r.get("foreign_exchange_reserve_currency", "")):
            continue
        d, v = month_end(int(r["year"]), r["month"]), _num(r.get("value"))
        if d and v is not None:
            out.append(("fx_reserves", d, round(v / 1000, 2)))
    return out


def ingest_mospi(db: Session) -> dict:
    from app.nse_mcp.client import NseMcp

    client = NseMcp(MOSPI_URL, timeout=45)
    this = date.today().year
    years = ",".join(str(y) for y in range(this - 3, this + 1))

    def rows(dataset: str, **filters) -> list[dict]:
        out, page = [], 1
        while True:
            data = client.call("get_data", dataset=dataset, filters={"limit": 100, "page": page, **filters})
            if not isinstance(data, dict):
                return out
            out += data.get("data") or []
            if page >= ((data.get("meta_data") or {}).get("totalPages") or 1):
                return out
            page += 1

    jobs = {
        # All India is state 99 in the 2012 base and state 1 in the 2024 base; the 2024 base has inflation only from 2026
        "cpi": lambda: parse_cpi(rows("CPI", base_year="2012", series="Current", year=f"{this - 3},{this - 2},{this - 1}", state_code=99, sector_code=3, group_code=0)
                                 + rows("CPI", base_year="2024", series="Current", year=f"{this - 1},{this}", state_code=1, sector_code=3, division_code=0)),
        "iip": lambda: parse_iip(rows("IIP", base_year="2022-23", frequency="Monthly", type="General", category_code=4, year=years)),
        "wpi": lambda: parse_wpi(rows("WPI", base_year="2022-23", major_group_code="1000000000", year=years)),
        "gdp": lambda: parse_gdp(rows("NAS", base_year="2022-23", series="Current", frequency_code="Quarterly", indicator_code=5),
                                 rows("NAS", base_year="2022-23", series="Current", frequency_code="Annually", indicator_code=5)),
        "fx": lambda: parse_fx_reserves(rows("RBI", sub_indicator_code=47, year=f"{this - 2},{this - 1},{this}")),
    }
    out = {}
    for name, job in jobs.items():
        try:
            out[name] = store(db, job())
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.warning("macro: MoSPI series not read", series=name, error=str(exc)[:160])
            out[name] = f"failed: {str(exc)[:80]}"
    return out


# ── RBI ──────────────────────────────────────────────────────────────────────

def parse_rbi(html: str, today: date | None = None) -> list[tuple[str, date, float]]:
    today = today or date.today()
    text = re.sub(r"&nbsp;", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S))
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))
    out = []
    for series, label in (("repo", "Policy Repo Rate"), ("sdf", "Standing Deposit Facility Rate"), ("msf", "Marginal Standing Facility Rate"),
                          ("crr", "CRR"), ("slr", "SLR")):
        m = re.search(rf"{label}\s*:\s*([\d.]+)\s*%", text)
        if m:
            out.append((series, today, float(m.group(1))))
    m = re.search(r"INR\s*/\s*1\s*USD\s*:\s*([\d.]+)", text)
    if m:
        out.append(("usd_inr", today, float(m.group(1))))
    m = re.search(r"Call Rates\s*:\s*[\d.]+\s*%\s*-\s*([\d.]+)\s*%", text)
    if m:
        out.append(("call_rate", today, float(m.group(1))))
    bonds = [(int(y), float(v)) for y, v in re.findall(r"[\d.]+%\s*GS\s*(\d{4})\s*:\s*([\d.]+)\s*%", text)]
    if bonds:
        out.append(("gsec_10y", today, min(bonds, key=lambda b: abs(b[0] - (today.year + 10)))[1]))
    return out


def ingest_rbi(db: Session) -> int:
    r = httpx.get(RBI_URL, headers=_UA, timeout=40, follow_redirects=True)
    r.raise_for_status()
    return store(db, parse_rbi(r.text))


# ── CBOE, Yahoo, World Bank, NSE's index file ───────────────────────────────

def parse_cboe(text: str, since: date) -> list[tuple[str, date, float]]:
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        d = datetime.strptime(row["DATE"], "%m/%d/%Y").date()
        if d >= since:
            out.append(("cboe_vix", d, float(row["CLOSE"])))
    return out


def ingest_cboe(db: Session, since: date) -> int:
    r = httpx.get(CBOE_URL, headers=_UA, timeout=60, follow_redirects=True)
    r.raise_for_status()
    return store(db, parse_cboe(r.text, since))


def ingest_yahoo(db: Session, since: date) -> dict:
    import yfinance as yf

    out = {}
    for series, ticker in _YAHOO.items():
        try:
            bars = yf.Ticker(ticker).history(start=since.isoformat())
            out[series] = store(db, [(series, i.date(), round(float(c), 4)) for i, c in bars["Close"].items() if c == c])
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.warning("macro: Yahoo series not read", series=series, error=str(exc)[:160])
            out[series] = "failed"
    return out


def parse_world_bank(series: str, data: list) -> list[tuple[str, date, float]]:
    rows = data[1] if isinstance(data, list) and len(data) > 1 and data[1] else []
    return [(series, date(int(r["date"]), 12, 31), round(float(r["value"]), 2)) for r in rows if r.get("value") is not None]


def ingest_world_bank(db: Session) -> int:
    n = 0
    for series, code in (("wb_gdp_growth", "NY.GDP.MKTP.KD.ZG"), ("wb_inflation", "FP.CPI.TOTL.ZG")):
        r = httpx.get(WORLD_BANK.format(code=code), headers=_UA, timeout=40, follow_redirects=True)
        r.raise_for_status()
        n += store(db, parse_world_bank(series, r.json()))
    return n


def ingest_indices(db: Session) -> int:
    """India VIX and Nifty 50 valuation are already in the price store: copied in, nothing fetched."""
    points = []
    for b in db.query(IndexBar).filter(IndexBar.index_name.in_(("India VIX", "Nifty 50"))):
        if b.index_name == "India VIX":
            points.append(("india_vix", b.bar_date, float(b.close)))
        else:
            for series, v in (("nifty_pe", b.pe), ("nifty_pb", b.pb), ("nifty_yield", b.div_yield)):
                if v is not None:
                    points.append((series, b.bar_date, float(v)))
    return store(db, points)
