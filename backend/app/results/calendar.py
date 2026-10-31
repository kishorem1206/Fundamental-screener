"""NSE's calendar of results meetings, and which stocks are due a re-read."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import MetricDataPoint, ResultsCalendar, Stock

DAYS_BACK, DAYS_AHEAD = 40, 45
MAX_ATTEMPTS = 5
_QUARTER_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))


def parse(rows: list[dict], ids: dict[str, str]) -> list[dict]:
    """`ids`: {symbol: stock_id}. Results meetings of stocks in the universe; one
    row a stock a day, whatever else the meeting covers."""
    out: dict[tuple[str, date], dict] = {}
    for r in rows:
        purpose, sid = (r.get("purpose") or "").strip(), ids.get(r.get("symbol") or "")
        if sid is None or "financial results" not in purpose.lower():
            continue
        try:
            day = datetime.strptime(r["date"], "%d-%b-%Y").date()
        except (KeyError, TypeError, ValueError):
            continue
        out[(sid, day)] = {"stock_id": sid, "board_date": day, "purpose": purpose[:200]}
    return list(out.values())


def sync(db: Session, today: date | None = None) -> dict:
    """Store NSE's calendar. A future meeting NSE no longer lists was moved, so
    its row goes. Raises if NSE does not answer: the caller still works through
    what is already due."""
    from app.bie.nse_filings import NseFilings

    today = today or date.today()
    start, end = today - timedelta(days=DAYS_BACK), today + timedelta(days=DAYS_AHEAD)
    rows = NseFilings()._json(f"event-calendar?index=equities&from_date={start:%d-%m-%Y}&to_date={end:%d-%m-%Y}") or []
    ids = {s: i for s, i in db.query(Stock.symbol, Stock.id).filter(Stock.is_active.is_(True), Stock.exchange == "NSE")}
    meetings = parse(rows, ids)
    if not meetings:
        return {"meetings": 0}
    for m in meetings:
        stmt = insert(ResultsCalendar).values(**m)
        db.execute(stmt.on_conflict_do_update(index_elements=["stock_id", "board_date"], set_={"purpose": stmt.excluded.purpose}))
    listed = {(m["stock_id"], m["board_date"]) for m in meetings}
    moved = [r for r in db.query(ResultsCalendar).filter(ResultsCalendar.board_date >= today, ResultsCalendar.status == "PENDING")
             if (r.stock_id, r.board_date) not in listed]
    for r in moved:
        db.delete(r)
    db.commit()
    return {"meetings": len(meetings), "moved": len(moved)}


def expected_quarter(board_date: date) -> date:
    """The quarter a results meeting reports: the last one to end before it."""
    ends = [date(y, m, d) for y in (board_date.year - 1, board_date.year) for m, d in _QUARTER_ENDS]
    return max(e for e in ends if e < board_date)


def has_quarter(latest: str | None, board_date: date) -> bool:
    """Does the stored quarter cover the results of this meeting?"""
    return latest is not None and latest >= expected_quarter(board_date).isoformat()


def latest_quarters(db: Session, stock_ids: list[str] | None = None) -> dict[str, str]:
    q = (db.query(MetricDataPoint.company_id, func.max(MetricDataPoint.period))
         .filter(MetricDataPoint.source == "SCREENER", MetricDataPoint.metric_key == "qtr_net_profit", func.length(MetricDataPoint.period) == 10))
    if stock_ids is not None:
        q = q.filter(MetricDataPoint.company_id.in_(stock_ids))
    return dict(q.group_by(MetricDataPoint.company_id).all())


def due(db: Session, today: date | None = None) -> list[ResultsCalendar]:
    """Meetings before today still waiting for their quarter."""
    return (db.query(ResultsCalendar).filter(ResultsCalendar.status == "PENDING", ResultsCalendar.board_date < (today or date.today()))
            .order_by(ResultsCalendar.board_date).all())


def settle(row: ResultsCalendar, latest: str | None, now: datetime, tried: bool) -> None:
    """Mark a meeting done if its quarter is in, and give up after five tries."""
    row.quarter = latest
    if tried:
        row.attempts += 1
        row.last_tried_at = now
    if has_quarter(latest, row.board_date):
        row.status, row.done_at = "DONE", now
    elif row.attempts >= MAX_ATTEMPTS:
        row.status = "GAVE_UP"
