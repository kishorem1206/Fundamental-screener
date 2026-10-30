"""FPI flows from NSDL (fpi.nsdl.co.in).

    Monthly.aspx               every day of the current month, by instrument
    Yearwise.aspx?RptType=6    net investment by month for a calendar year
                               (other years through the page's year selector)
    FPI_Fortnightly_Selection  links to one static HTML file a fortnight,
                               assets and net investment by sector

Sector names in the fortnightly report are the same NSE sector names as
`stocks.sector`. The flow signal is shown next to Relative Strength, never
scored: whether it tells us anything has not been tested.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime, timedelta, timezone

import httpx
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import FpiSectorFlow
from app.logger import logger
from app.macro.sources import _UA, month_end, store

_BASE = "https://www.fpi.nsdl.co.in/web"
_FLOW_FORTNIGHTS = 6  # about three months
_NOT_SECTORS = {"sovereign", "others", "grand total"}
_MONTHS = "january february march april may june july august september october november december".split()


def _money(v) -> float | None:
    """NSDL writes a negative as (9,231.88)."""
    s = str(v).strip().replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    try:
        x = float(s.strip("()"))
    except ValueError:
        return None
    return -x if neg else x


def parse_daily(html: str) -> list[tuple[str, date, float]]:
    table = max(pd.read_html(io.StringIO(html)), key=lambda d: d.size)
    table.columns = range(table.shape[1])
    totals: dict[tuple[str, date], float] = {}
    for _, r in table.iterrows():
        try:
            day = datetime.strptime(str(r[0]).strip(), "%d-%b-%Y").date()
        except ValueError:
            continue
        kind, route, net = str(r[1]).strip().lower(), str(r[2]).strip().lower(), _money(r[5])
        if route != "sub-total" or net is None:
            continue
        series = "fpi_equity_daily" if kind == "equity" else "fpi_debt_daily" if kind.startswith("debt") else None
        if series:
            totals[(series, day)] = totals.get((series, day), 0.0) + net
    return [(s, d, round(v, 2)) for (s, d), v in totals.items()]


def parse_yearwise(html: str) -> list[tuple[str, date, float]]:
    """Columns: month, then INR crore by instrument: equity, three debt kinds, …"""
    table = max(pd.read_html(io.StringIO(html)), key=lambda d: d.size)
    year = next((int(m) for c in table.columns for m in re.findall(r"Calendar Year - (\d{4})", str(c))), None)
    if year is None:
        return []
    cols = list(table.columns)
    inr = [i for i, c in enumerate(cols) if "INR Crores" in str(c)]
    equity = [i for i in inr if str(c := cols[i][2]).strip() == "Equity"]
    debt = [i for i in inr if str(cols[i][2]).strip() == "Debt"]
    out = []
    for _, r in table.iterrows():
        d = month_end(year, str(r.iloc[0]))
        if d is None:
            continue
        eq = [_money(r.iloc[i]) for i in equity]
        de = [_money(r.iloc[i]) for i in debt]
        if eq and eq[0] is not None:
            out.append(("fpi_equity_month", d, eq[0]))
        if any(x is not None for x in de):
            out.append(("fpi_debt_month", d, sum(x or 0 for x in de)))
    return out


def _period_end(header: str) -> date | None:
    """"Net Investment October 01-15, 2026" → 15 Oct 2026; "AUC as on October 15, 2026" likewise."""
    m = re.search(r"([A-Za-z]+)\s+(?:\d{1,2}\s*-\s*)?(\d{1,2}),?\s+(\d{4})", header)
    if not m or m.group(1).lower() not in _MONTHS:
        return None
    return date(int(m.group(3)), _MONTHS.index(m.group(1).lower()) + 1, int(m.group(2)))


def parse_sector_file(html: str) -> list[dict]:
    """One row a (period, sector): net investment and assets in equity, ₹ crore."""
    table = max(pd.read_html(io.StringIO(html)), key=lambda d: d.size)
    head = table.iloc[:4]
    rows: dict[tuple[date, str], dict] = {}
    for col in range(2, table.shape[1]):
        title, currency, family, kind = (str(head.iloc[row, col]) for row in range(4))
        # "Mutual Funds" has an Equity column of its own: FPI money into equity is the Equity family only
        if "INR" not in currency or family.strip() != "Equity" or kind.strip() != "Equity":
            continue
        end = _period_end(title)
        field = "net_cr" if title.startswith("Net Investment") else "auc_cr" if title.startswith("AUC") else None
        if end is None or field is None:
            continue
        for i in range(4, table.shape[0]):
            sector = str(table.iloc[i, 1]).strip()
            if not sector or sector == "nan" or sector.lower() in _NOT_SECTORS:
                continue
            rows.setdefault((end, sector), {"period_end": end, "sector": sector, "net_cr": None, "auc_cr": None})[field] = _money(table.iloc[i, col])
    return list(rows.values())


def _store_sector_rows(db: Session, rows: list[dict]) -> int:
    now = datetime.now(timezone.utc)
    for r in rows:
        # a later file may carry only one of the two figures for a period: keep the other
        stmt = insert(FpiSectorFlow).values(**r, retrieved_at=now)
        db.execute(stmt.on_conflict_do_update(index_elements=["period_end", "sector"], set_={
            "net_cr": stmt.excluded.net_cr if r["net_cr"] is not None else FpiSectorFlow.net_cr,
            "auc_cr": stmt.excluded.auc_cr if r["auc_cr"] is not None else FpiSectorFlow.auc_cr,
            "retrieved_at": now}))
    db.commit()
    return len(rows)


def _get(client: httpx.Client, path: str) -> str:
    r = client.get(f"{_BASE}/{path}")
    r.raise_for_status()
    return r.text


def ingest_daily(db: Session) -> int:
    with httpx.Client(headers=_UA, timeout=40, follow_redirects=True) as c:
        return store(db, parse_daily(_get(c, "Reports/Monthly.aspx")))


def ingest_yearly(db: Session, years: int = 5) -> int:
    """This year from the page as served; earlier years through its selector."""
    with httpx.Client(headers=_UA, timeout=40, follow_redirects=True) as c:
        url = f"{_BASE}/Reports/Yearwise.aspx?RptType=6"
        page = c.get(url).text
        n = store(db, parse_yearwise(page))
        for year in range(date.today().year - 1, date.today().year - years, -1):
            fields = {k: v for k, v in re.findall(r'<input[^>]*name="(__[A-Z]+)"[^>]*value="([^"]*)"', page)}
            r = c.post(url, data={**fields, "__EVENTTARGET": "ddl", "__EVENTARGUMENT": "", "ddl": str(year)})
            page = r.text
            try:
                n += store(db, parse_yearwise(page))
            except Exception as exc:  # noqa: BLE001
                logger.warning("fpi: year not read", year=year, error=str(exc)[:120])
    return n


def ingest_sectors(db: Session, fortnights: int = 72, only_new: bool = True, log=print) -> dict:
    with httpx.Client(headers=_UA, timeout=40, follow_redirects=True) as c:
        links = re.findall(r"~/(StaticReports/Fortnightly_Sector_wise_FII_Investment_Data/[^'\"]+\.html)", _get(c, "Reports/FPI_Fortnightly_Selection.aspx"))
        known = {d for (d,) in db.query(FpiSectorFlow.period_end).filter(FpiSectorFlow.net_cr.isnot(None)).distinct()}
        read = 0
        for i, link in enumerate(dict.fromkeys(links[:fortnights])):
            m = re.search(r"FIIInvestSector_([A-Za-z]{3})(\d{2})(\d{4})", link)
            when = datetime.strptime("".join(m.groups()), "%b%d%Y").date() if m else None
            if only_new and when in known:
                continue
            try:
                _store_sector_rows(db, parse_sector_file(_get(c, link)))
                read += 1
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                logger.warning("fpi: sector file not read", link=link, error=str(exc)[:120])
            if read and read % 12 == 0:
                log(f"  ...{read} fortnightly files read")
    return {"files_listed": len(links), "files_read": read}


def _flow(rows: list[FpiSectorFlow]) -> dict | None:
    """`rows`: one sector, newest first."""
    usable = [r for r in rows if r.net_cr is not None]
    if not usable:
        return None
    recent = usable[:_FLOW_FORTNIGHTS]
    held = next((float(r.auc_cr) for r in rows if r.auc_cr), None)
    net = sum(float(r.net_cr) for r in recent)
    return {"sector": rows[0].sector, "period_end": usable[0].period_end.isoformat(), "fortnights": len(recent),
            "latest_net_cr": float(usable[0].net_cr), "net_cr": round(net, 2), "held_cr": held,
            "net_pct_of_holding": round(net / held * 100, 2) if held else None,
            "history": [{"date": r.period_end.isoformat(), "net_cr": float(r.net_cr)} for r in reversed(usable[:12])]}


def sector_flows(db: Session) -> list[dict]:
    """Every sector, biggest three-month inflow against what is held first."""
    since = date.today() - timedelta(days=200)
    by: dict[str, list] = {}
    for r in db.query(FpiSectorFlow).filter(FpiSectorFlow.period_end >= since).order_by(FpiSectorFlow.period_end.desc()):
        by.setdefault(r.sector, []).append(r)
    out = [f for rows in by.values() if (f := _flow(rows))]
    out.sort(key=lambda f: f["net_pct_of_holding"] if f["net_pct_of_holding"] is not None else -1e9, reverse=True)
    for rank, f in enumerate(out, 1):
        f.update(rank=rank, of=len(out))
    return out


def flow_for_sector(db: Session, sector: str | None) -> dict | None:
    return next((f for f in sector_flows(db) if f["sector"] == sector), None) if sector else None
