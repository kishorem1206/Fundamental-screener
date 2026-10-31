"""Redo a stock's full analysis once its new quarter is in.

Only stocks that already have a full analysis: the report is built with the LLM
and takes about five minutes, so this is not for the whole universe. One at a
time, at most MAX_PER_RUN a night; the rest follow on later nights, because a
stock stays due until an analysis newer than its update exists.

    cd backend && .venv/bin/python -m app.results.full_analysis [--dry-run]
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis, ResultsCalendar, Stock
from app.logger import logger

MAX_PER_RUN = 10
_LOOK_BACK_DAYS = 60


def is_due(last_created, has_completed: bool, quarter_landed) -> bool:
    """Any newer attempt counts, so a failing report is not retried every night."""
    return has_completed and last_created is not None and last_created < quarter_landed


def due(db: Session) -> list[str]:
    runs: dict[str, dict] = {}
    for sid, status, created in db.query(FundamentalAnalysis.stock_id, FundamentalAnalysis.status, FundamentalAnalysis.created_at):
        r = runs.setdefault(sid, {"last": created, "completed": False})
        r["last"] = max(r["last"], created)
        r["completed"] = r["completed"] or status == "COMPLETED"
    landed: dict[str, object] = {}
    for sid, done in (db.query(ResultsCalendar.stock_id, ResultsCalendar.done_at)
                      .filter(ResultsCalendar.status == "DONE", ResultsCalendar.board_date >= date.today() - timedelta(days=_LOOK_BACK_DAYS))):
        if done is not None and (sid not in landed or done > landed[sid]):
            landed[sid] = done
    wanted = [sid for sid, when in landed.items() if sid in runs and is_due(runs[sid]["last"], runs[sid]["completed"], when)]
    caps = dict(db.query(Stock.id, Stock.market_cap).filter(Stock.id.in_(wanted)).all()) if wanted else {}
    return sorted(wanted, key=lambda s: -float(caps.get(s) or 0))


def run(db: Session, log=print) -> dict:
    from app.pipeline.orchestrator import run_analysis_pipeline
    from app.routes.fundamental import create_analysis

    stale = db.query(FundamentalAnalysis).filter(FundamentalAnalysis.started_by == "scheduler", FundamentalAnalysis.status.in_(("QUEUED", "RUNNING"))).all()
    for a in stale:  # the job that started these has gone
        a.status, a.error_message = "FAILED", "The scheduled run stopped before finishing."
    db.commit()
    waiting = due(db)
    batch, finished = waiting[:MAX_PER_RUN], 0
    for i, sid in enumerate(batch, 1):
        analysis_id = create_analysis(db, sid, started_by="scheduler")
        log(f"  {i}/{len(batch)} {sid} {analysis_id}")
        try:
            run_analysis_pipeline(analysis_id, sid)
        except Exception as exc:  # noqa: BLE001 — one failed report must not stop the rest
            logger.warning("scheduled analysis failed", stock_id=sid, error=str(exc)[:160])
        db.expire_all()
        finished += db.get(FundamentalAnalysis, analysis_id).status == "COMPLETED"
    return {"due": len(waiting), "run": len(batch), "completed": finished}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="list what is due, run nothing")
    a = ap.parse_args()
    db = get_db()
    try:
        if a.dry_run:
            print("DUE:", due(db), flush=True)
        else:
            print("FULL ANALYSES:", run(db, log=lambda m: print(m, flush=True)), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
