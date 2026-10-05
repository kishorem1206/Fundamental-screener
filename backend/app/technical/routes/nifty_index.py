"""
Nifty Index Classification API.

GET  /nifty/indices                        — list all known indices
GET  /nifty/indices/{index_code}/constituents   — stocks in an index
GET  /nifty/stocks/{symbol}/indices        — which indices a stock belongs to
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.technical.agents.message_bus import agent_message_bus
from app.technical.shared.schemas import AgentTask

router = APIRouter(prefix="/nifty", tags=["nifty-index"])


def _dispatch(task_type: str, payload: dict) -> dict:
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


@router.get("/indices")
def list_indices(category: Optional[str] = Query(default=None)):
    """List all Nifty indices.  ?category=SECTORAL to filter."""
    return _dispatch("NIFTY_LIST_INDICES", {"category": category})


@router.get("/indices/{index_code}/constituents")
def index_constituents(index_code: str, as_of: Optional[str] = Query(default=None)):
    """
    Return constituents of a Nifty index.

    index_code examples: nifty-50, nifty-bank, nifty-it
    ?as_of=2026-06-15 → historical membership on that date
    """
    return _dispatch("NIFTY_INDEX_STOCKS", {"index_code": index_code, "as_of": as_of})


@router.get("/stocks/{symbol}/indices")
def stock_indices(
    symbol: str,
    as_of: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
):
    """
    Return all Nifty indices a stock belongs to.

    ?as_of=2026-06-15 → historical membership on that date
    ?category=SECTORAL → filter to one category
    """
    return _dispatch("NIFTY_STOCK_INDICES", {"symbol": symbol, "as_of": as_of, "category": category})


@router.get("/indices/{index_a}/intersection/{index_b}")
def index_intersection(index_a: str, index_b: str):
    """Return stocks present in both indices (current membership)."""
    return _dispatch("NIFTY_INDEX_INTERSECTION", {"index_a": index_a, "index_b": index_b})
