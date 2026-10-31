"""Market & Macro page (app/macro/): context only, nothing here feeds a score."""
from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.macro.overview import overview

router = APIRouter(prefix="/api/macro")


_STRONG_FUNDAMENTAL = 70


def _day_group(held: bool, fundamental: float | None) -> str:
    return "held" if held else "strong" if fundamental is not None and fundamental >= _STRONG_FUNDAMENTAL else "other"


def _surprise(actual: float | None, estimate: float | None) -> float | None:
    if actual is None or not estimate:
        return None
    return round((actual - estimate) / abs(estimate) * 100, 1)


def _held(db) -> set[str]:
    from app.infrastructure.database.models import PortfolioHolding

    return {sid for (sid,) in db.query(PortfolioHolding.stock_id).filter(PortfolioHolding.stock_id.isnot(None)).distinct()}


@router.get("/results-calendar")
def results_calendar(month: str | None = None):
    """A month of results dates, and how the daily re-reads are getting on. `month`: YYYY-MM."""
    from datetime import date

    from sqlalchemy import func

    from app.infrastructure.database.models import ResultsCalendar as RC

    db = get_db()
    try:
        today = date.today()
        year, mon = (int(x) for x in month.split("-")) if month else (today.year, today.month)
        start, end = date(year, mon, 1), date(year + mon // 12, mon % 12 + 1, 1)
        held = _held(db)
        days: dict[str, dict] = {}
        for sid, on in db.query(RC.stock_id, RC.board_date).filter(RC.board_date >= start, RC.board_date < end):
            d = days.setdefault(on.isoformat(), {"date": on.isoformat(), "count": 0, "held": 0})
            d["count"] += 1
            d["held"] += sid in held
        counts = dict(db.query(RC.status, func.count()).filter(RC.board_date < today).group_by(RC.status).all())
        first, last = db.query(func.min(RC.board_date), func.max(RC.board_date)).one()
        return {"month": f"{year:04d}-{mon:02d}", "today": today.isoformat(), "days": sorted(days.values(), key=lambda d: d["date"]),
                "first": first.isoformat()[:7] if first else None, "last": last.isoformat()[:7] if last else None,
                "updated": counts.get("DONE", 0), "waiting": counts.get("PENDING", 0), "gave_up": counts.get("GAVE_UP", 0)}
    finally:
        db.close()


@router.get("/results-calendar/day")
def results_day(on: str):
    """One date's results: holdings first, then strong fundamentals, then the rest."""
    from datetime import date

    from sqlalchemy import text

    from app.framework.screener_series import quarterly
    from app.infrastructure.database.models import ResultsCalendar as RC, Stock

    def num(v):
        return float(v) if v is not None else None

    db = get_db()
    try:
        rows = db.query(RC, Stock).join(Stock, Stock.id == RC.stock_id).filter(RC.board_date == date.fromisoformat(on)).all()
        ids = [s.id for _, s in rows]
        scores = {sid: (num(f), num(q), c) for sid, f, q, c in db.execute(text(
            "select distinct on (stock_id) stock_id, fundamental, quality, classification from fw_scores where stock_id = any(:ids) "
            "order by stock_id, as_of desc, (basis = 'FULL') desc"), {"ids": ids})} if ids else {}
        held, out = _held(db), []
        for r, s in rows:
            fundamental, quality, classification = scores.get(s.id, (None, None, None))
            actual_eps = actual_sales = None
            if r.status == "DONE" and r.quarter:
                row = quarterly(db, s.id)["rows"].get(r.quarter) or {}
                actual_eps, actual_sales = row.get("eps"), row.get("sales")
            is_held = s.id in held
            out.append({"symbol": s.symbol, "company_name": s.company_name, "basic_industry": s.basic_industry, "group": _day_group(is_held, fundamental),
                        "held": is_held, "fundamental": fundamental, "quality": quality, "classification": classification, "status": r.status, "quarter": r.quarter,
                        "eps_estimate": num(r.eps_estimate), "eps_low": num(r.eps_low), "eps_high": num(r.eps_high), "eps_year_ago": num(r.eps_year_ago), "eps_analysts": r.eps_analysts,
                        "revenue_estimate_cr": num(r.revenue_estimate_cr), "revenue_year_ago_cr": num(r.revenue_year_ago_cr), "revenue_analysts": r.revenue_analysts,
                        "actual_eps": actual_eps, "actual_sales_cr": actual_sales, "eps_surprise_pct": _surprise(actual_eps, num(r.eps_estimate)),
                        "revenue_surprise_pct": _surprise(actual_sales, num(r.revenue_estimate_cr)), "market_cap": num(s.market_cap)})
        out.sort(key=lambda x: (not x["held"], -(x["fundamental"] if x["fundamental"] is not None else -1), -(x["market_cap"] or 0)))
        return {"date": on, "stocks": out}
    finally:
        db.close()


@router.get("/overview")
def macro_overview():
    db = get_db()
    try:
        return overview(db)
    finally:
        db.close()
