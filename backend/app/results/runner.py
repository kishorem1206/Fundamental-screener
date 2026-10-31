"""The daily results job: sync NSE's calendar, then re-read and re-score only the
stocks whose results were yesterday or earlier and are not in yet.

    cd backend && .venv/bin/python -m app.results.runner
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock
from app.logger import logger
from app.results import calendar

_BATCH = 25


def run(db, log=print) -> dict:
    """Never raises for one failed stock: what is not done stays pending for tomorrow."""
    from app.framework.decisions import refresh_all
    from app.quick_analysis import runner as quick

    try:
        log(f"calendar: {calendar.sync(db)}")
    except Exception as exc:  # noqa: BLE001 — what is already due can still be worked through
        db.rollback()
        log(f"calendar: NSE did not answer ({str(exc)[:120]})")
    rows = calendar.due(db)
    now = datetime.now(timezone.utc)
    latest = calendar.latest_quarters(db, sorted({r.stock_id for r in rows}))
    waiting = []
    for r in rows:
        calendar.settle(r, latest.get(r.stock_id), now, tried=False)  # already in: nothing to read
        if r.status == "PENDING":
            waiting.append(r)
    db.commit()
    by_stock: dict[str, list] = {}
    for r in waiting:
        by_stock.setdefault(r.stock_id, []).append(r)
    stocks = sorted((s for s in (db.get(Stock, sid) for sid in by_stock) if s is not None), key=lambda s: -float(s.market_cap or 0))
    log(f"due: {len(rows)} meetings, {len(stocks)} stocks to read")
    for i in range(0, len(stocks), _BATCH):
        batch = stocks[i:i + _BATCH]
        try:
            quick.run(batch, workers=4, stocks_per_sec=1.5, store=True, force_screener=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("results: batch failed", error=str(exc)[:160])
        db.expire_all()
        after = calendar.latest_quarters(db, [s.id for s in batch])
        now = datetime.now(timezone.utc)
        for s in batch:
            for r in by_stock[s.id]:
                calendar.settle(r, after.get(s.id), now, tried=True)
        db.commit()
        log(f"  ...{min(i + _BATCH, len(stocks))}/{len(stocks)} stocks read")
    if stocks:
        log(f"decisions: {refresh_all(db)}")
    return dict(Counter(r.status for r in rows))


def main() -> None:
    db = get_db()
    try:
        print("RESULTS:", run(db, log=lambda m: print(m, flush=True)), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
