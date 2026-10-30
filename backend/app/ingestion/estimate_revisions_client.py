"""Earnings estimate revisions, from Yahoo Finance.

Yahoo keeps each consensus estimate as it stood 7, 30, 60 and 90 days ago
(`eps_trend`), counts analysts' changes (`eps_revisions`) and gives the number
of analysts (`earnings_estimate`), so revisions are measurable from the first
read, without waiting months for a history of our own. A snapshot is stored
each run so one builds up anyway.

Yahoo writes 0 for a value it does not have, and when a financial year rolls
the current-year estimate can be blank, so next year's estimate is read first
and a 0 counts as missing. A move of more than 60% is left out: that is a split,
a bonus or a reset of the estimate base far more often than a real change of view.

Analysts' opinion, so shown on the stock for context and never scored (user's
decision, 2026-10-30).

    cd backend && .venv/bin/python -m app.ingestion.estimate_revisions_client [--symbols A,B] [--stale-days 6]
"""
from __future__ import annotations

import argparse
import time
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import EstimateSnapshot, Stock
from app.logger import logger

_PERIODS = ("+1y", "0y")
_MAX_MOVE = 60.0
_PACE = 0.7


def _clean(v) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def _count(v) -> int | None:
    try:
        return int(v) if v == v else None
    except (TypeError, ValueError):
        return None


def _move(now: float, then: float | None) -> float | None:
    if then is None:
        return None
    pct = (now / then - 1) * 100
    return round(pct, 2) if abs(pct) <= _MAX_MOVE else None


def parse(trend: dict, revisions: dict, estimates: dict) -> dict | None:
    """`trend`, `revisions`, `estimates`: {period: {field: value}}. None when no usable estimate exists."""
    for period in _PERIODS:
        row = trend.get(period) or {}
        now = _clean(row.get("current"))
        if now is None:
            continue
        back30, back90 = _clean(row.get("30daysAgo")), _clean(row.get("90daysAgo"))
        m30, m90 = _move(now, back30), _move(now, back90)
        if m30 is None and m90 is None:
            continue
        rev = revisions.get(period) or {}
        return {"period": period, "eps_now": now, "eps_30d_ago": back30, "eps_90d_ago": back90,
                "revision_30d_pct": m30, "revision_90d_pct": m90, "up_30d": _count(rev.get("upLast30days")),
                "down_30d": _count(rev.get("downLast30days")), "analysts": _count((estimates.get(period) or {}).get("numberOfAnalysts"))}
    return None


def _frame(df) -> dict:
    return {} if df is None or getattr(df, "empty", True) else df.to_dict("index")


def read_one(symbol: str) -> dict | None:
    import yfinance as yf

    t = yf.Ticker(f"{symbol}.NS")
    return parse(_frame(t.eps_trend), _frame(t.eps_revisions), _frame(t.earnings_estimate))


def ingest(db: Session, symbols: list[str] | None = None, stale_days: float = 6, log=print) -> dict:
    """Never raises. A stock read within `stale_days` is skipped."""
    q = db.query(Stock).filter(Stock.is_active.is_(True), Stock.exchange == "NSE")
    if symbols:
        q = q.filter(Stock.symbol.in_(symbols))
    stocks = q.order_by(Stock.market_cap.desc().nullslast()).all()
    cutoff = date.today() - timedelta(days=stale_days)
    fresh = {sid for sid, d in db.query(EstimateSnapshot.stock_id, func.max(EstimateSnapshot.on_date)).group_by(EstimateSnapshot.stock_id) if d > cutoff}
    todo = [s for s in stocks if symbols or s.id not in fresh]
    stored = none = failed = 0
    for i, s in enumerate(todo, 1):
        time.sleep(_PACE)
        try:
            p = read_one(s.symbol)
        except Exception as exc:  # noqa: BLE001
            if "too many" in str(exc).lower() or "rate" in str(exc).lower():
                logger.warning("estimates: throttled, waiting", symbol=s.symbol)
                time.sleep(90)
            failed += 1
            continue
        if p is None:
            none += 1
        else:
            row = {"stock_id": s.id, "on_date": date.today(), **p, "retrieved_at": datetime.now(timezone.utc)}
            stmt = insert(EstimateSnapshot).values(**row)
            db.execute(stmt.on_conflict_do_update(index_elements=["stock_id", "on_date"], set_={k: stmt.excluded[k] for k in row if k not in ("stock_id", "on_date")}))
            db.commit()
            stored += 1
        if i % 200 == 0:
            log(f"  ...{i}/{len(todo)}: {stored} with estimates, {none} without, {failed} failed")
    return {"read": len(todo), "with_estimates": stored, "without": none, "failed": failed}


def latest(db: Session, stock_id: str, max_age_days: int = 30) -> EstimateSnapshot | None:
    return (db.query(EstimateSnapshot).filter(EstimateSnapshot.stock_id == stock_id, EstimateSnapshot.on_date >= date.today() - timedelta(days=max_age_days))
            .order_by(EstimateSnapshot.on_date.desc()).first())


def for_stock(db: Session, stock_id: str) -> dict | None:
    """What the stock page shows."""
    row = latest(db, stock_id)
    if row is None:
        return None
    pct = row.revision_90d_pct if row.revision_90d_pct is not None else row.revision_30d_pct
    return {"eps_now": float(row.eps_now), "estimate_for": "next financial year" if row.period == "+1y" else "this financial year",
            "revision_pct": float(pct) if pct is not None else None, "over": "90 days" if row.revision_90d_pct is not None else "30 days",
            "raised_30d": row.up_30d, "cut_30d": row.down_30d, "analysts": row.analysts, "as_of": row.on_date.isoformat(), "source": "Yahoo Finance consensus"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", help="comma-separated NSE symbols (default: every active stock)")
    ap.add_argument("--stale-days", type=float, default=6)
    a = ap.parse_args()
    db = get_db()
    try:
        print("ESTIMATES:", ingest(db, a.symbols.split(",") if a.symbols else None, a.stale_days, log=lambda m: print(m, flush=True)), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
