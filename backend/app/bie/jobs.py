"""Deep-report build jobs of this server process, shared by the API (the
build button) and the full-analysis pipeline (which starts a build for every
stock it analyses). One build per symbol at a time; state is in memory, so a
server restart forgets a job in progress though not the facts it had saved.
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import BieFact
from app.logger import logger

# Kinds of fact only a company's own build writes; a company built merely as someone's peer has results and identity alone.
OWN_BUILD = ("acquisition", "sector_kpi", "business_profile", "business_activity", "corporate_event", "group_structure", "group_entity",
             "concentration", "footprint", "market_share", "product", "guidance")
# symbol -> {state, step, steps_done, started_at, finished_at, errors}
JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()
STEP_LABELS = {
    "identity": "Company identity", "results": "Financial results", "brsr": "Sustainability report", "annual_report": "Annual report",
    "corporate_events": "Corporate announcements", "guidance": "Management guidance", "entities_read": "Group structure",
    "acquisitions": "Acquisition filings", "sector_measures": "Presentations and call transcripts",
    "segment_industries": "Matching segments to industries", "derive": "Calculations", "macro": "Economic data",
    "industry_benchmarks": "Industry benchmarks", "official_production_data": "Government production data", "unit_volumes": "Sector volumes",
    "verify": "Verifying every figure", "links": "Checking source links",
}


def built_at(db, company_id: str):
    return db.query(func.max(BieFact.created_at)).filter(BieFact.company_id == company_id, BieFact.fact_type.in_(OWN_BUILD)).scalar()


def _label(name: str) -> str:
    if name in STEP_LABELS:
        return STEP_LABELS[name]
    if name.startswith("peer:"):
        return f"Peer: {name.split(':')[1]}"
    if name.startswith("stake:"):
        return f"Listed stake: {name.split(':')[1]}"
    return name.replace("_", " ").capitalize()


def run(symbol: str) -> None:
    """Build one company's facts; progress and the outcome are written to JOBS[symbol]."""
    from app.bie.pipeline import build_company
    job = JOBS[symbol]

    def on_step(name: str) -> None:
        job["steps_done"] += 1
        job["step"] = _label(name)

    db = get_db()
    try:
        summary = build_company(db, symbol, on_step=on_step)
        job.update(state="done", errors=summary.get("errors") or {})
        if any(isinstance(summary.get(step), dict) and summary[step].get("model_unavailable") for step in ("segment_industries", "sector_measures")):
            mark_pending(symbol)  # the model was out of allowance: its steps are retried later without a rebuild
            job["model_steps_pending"] = True
    except Exception as e:  # noqa: BLE001 — the failure is reported through the status endpoint
        logger.warning("bie: build failed", symbol=symbol, error=str(e)[:300])
        job.update(state="failed", errors={"build": f"{type(e).__name__}: {e}"})
    finally:
        job.update(step=None, finished_at=datetime.now(timezone.utc).isoformat())
        db.close()


def claim(symbol: str) -> bool:
    """Mark a build as started for `symbol`; False if one is already running."""
    symbol = symbol.upper()
    with _LOCK:
        if JOBS.get(symbol, {}).get("state") == "running":
            return False
        JOBS[symbol] = {"state": "running", "step": "Starting", "steps_done": 0, "started_at": datetime.now(timezone.utc).isoformat(),
                        "finished_at": None, "errors": {}}
        return True


def start_in_background(symbol: str, *, if_older_than: timedelta | None = None) -> str:
    """Start a build on its own thread. With `if_older_than`, a company built more recently than that is left alone.
    Returns 'started', 'already running' or 'fresh'."""
    symbol = symbol.upper()
    if if_older_than is not None:
        db = get_db()
        try:
            from app.infrastructure.database.models import Stock
            stock = db.query(Stock).filter(Stock.symbol == symbol, Stock.is_active.is_(True)).first()
            last = built_at(db, stock.id) if stock is not None else None
        finally:
            db.close()
        if last is not None and datetime.now(timezone.utc) - last < if_older_than:
            return "fresh"
    if not claim(symbol):
        return "already running"
    threading.Thread(target=run, args=(symbol,), name=f"bie-build-{symbol}", daemon=True).start()
    return "started"


# ── steps that wait for the language model ───────────────────────────────────
# When the configured model is out of allowance during a build, its two reading jobs (segment matching, measures for
# sectors without fixed patterns) are skipped and the company is marked here. The mark is retried, at most every
# twenty minutes, whenever someone looks at the company, until the model answers; nothing has to be rebuilt by hand.

def _pending_file(symbol: str):
    from pathlib import Path

    from app.config import config
    folder = Path(config.reports_dir).resolve() / ".pending-model-steps"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / symbol.upper()


def mark_pending(symbol: str) -> None:
    _pending_file(symbol).touch()


def is_pending(symbol: str) -> bool:
    return _pending_file(symbol).exists()


def _model_steps(symbol: str) -> None:
    from app.bie import llm_assist
    from app.bie.audit import verify_pending
    from app.bie.kpis import ingest_sector_measures
    from app.bie.nse_filings import NseFilings
    from app.infrastructure.database.models import Stock
    db = get_db()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if stock is None:
            return
        unavailable = False
        result = llm_assist.classify_segments(db, stock)
        db.commit()
        unavailable |= bool(result.get("model_unavailable"))
        if db.query(BieFact.id).filter(BieFact.company_id == stock.id, BieFact.fact_type == "sector_kpi").count() < 2:
            measures = ingest_sector_measures(db, NseFilings(), stock)
            db.commit()
            unavailable |= bool(measures.get("model_unavailable"))
        verify_pending(db)
        from app.bie.audit import check_links
        check_links(db)
        if not unavailable:
            _pending_file(symbol).unlink(missing_ok=True)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        logger.warning("bie: retry of model steps failed", symbol=symbol, error=str(e)[:200])
    finally:
        db.close()


def retry_pending(symbol: str, every: timedelta = timedelta(minutes=20)) -> bool:
    """Retry the model's steps for a marked company unless one ran recently or a build is running. True if a retry started."""
    import os
    import time
    marker = _pending_file(symbol)
    if not marker.exists() or JOBS.get(symbol.upper(), {}).get("state") == "running":
        return False
    if time.time() - marker.stat().st_mtime < every.total_seconds() and marker.stat().st_size:
        return False
    marker.write_text(datetime.now(timezone.utc).isoformat())  # non-empty: a retry has been made; its time is the file's
    os.utime(marker, None)
    threading.Thread(target=_model_steps, args=(symbol,), name=f"bie-model-{symbol}", daemon=True).start()
    return True
