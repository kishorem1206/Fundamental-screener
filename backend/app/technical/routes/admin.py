from fastapi import APIRouter, HTTPException, Query
from app.technical.services.nifty_refresh_service import nifty_refresh_service
from app.technical.agents.message_bus import agent_message_bus
from app.technical.shared.schemas import AgentTask

router = APIRouter(prefix="/admin", tags=["admin"])


def _nifty_dispatch(task_type: str, payload: dict) -> dict:
    task = AgentTask(
        from_agent="API",
        to_agent="NiftyIndexAgent",
        task_type=task_type,
        payload=payload,
    )
    result = agent_message_bus.dispatch(task)
    if result.status != "SUCCESS":
        msgs = "; ".join(e.message for e in result.errors)
        raise HTTPException(status_code=500, detail=msgs or "Agent error")
    return result.data


@router.post("/universes/refresh")
def refresh_universes(force: bool = Query(default=False)):
    """
    Sync universe membership from official NSE index CSV files.

    Downloads Nifty 50, Next 50, Midcap 150, Smallcap 250, and Total Market
    CSVs from niftyindices.com, then rebuilds stock and membership records.

    ?force=true  — skip the 90-day staleness guard and always refresh.
    """
    try:
        result = nifty_refresh_service.refresh(force=force)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result


@router.get("/universes/status")
def universe_status():
    """Show whether universe data is stale and how old it is."""
    is_stale, age_days = nifty_refresh_service.is_stale()
    return {
        "is_stale": is_stale,
        "age_days": age_days,
        "stale_threshold_days": 90,
        "message": (
            "Data is fresh" if not is_stale
            else f"Data is {age_days}d old — run POST /admin/universes/refresh"
            if age_days >= 0
            else "Data has never been synced from NSE — run POST /admin/universes/refresh"
        ),
    }


# ── Nifty index ingestion (new full-featured agent) ──────────────────────────

@router.post("/nifty/seed")
def nifty_seed_catalog():
    """Seed index_categories and nifty_indices catalog rows (safe to run multiple times)."""
    return _nifty_dispatch("NIFTY_SEED_CATALOG", {})


@router.post("/nifty/ingest")
def nifty_ingest(
    dry_run: bool = Query(default=False),
    index_ids: str = Query(default=""),
):
    """
    Run Nifty index data ingestion.

    ?dry_run=true   — download + diff but do NOT commit
    ?index_ids=nifty-50,nifty-bank  — restrict to specific indices
    """
    ids = [i.strip() for i in index_ids.split(",") if i.strip()] if index_ids else None
    task_type = "NIFTY_DRY_RUN" if dry_run else "NIFTY_INGEST"
    return _nifty_dispatch(task_type, {"index_ids": ids})


@router.get("/nifty/ingestion/status")
def nifty_ingestion_status():
    """Return the most recent (non-dry-run) ingestion run status."""
    return _nifty_dispatch("NIFTY_INGEST_STATUS", {})
