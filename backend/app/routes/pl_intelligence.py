"""P&L Analysis Engine — read-only, frontend-facing REST surface (spec
Stage 26). Compute-on-read, same pattern as `history_charts.py`: calls
`compute_pl_intelligence()` fresh per request rather than reading the
persisted `pl_score_components`/etc. tables — those are for point-in-time
reproducibility/backtesting (Milestone 7), not for serving live requests,
matching this codebase's existing "recompute at render/request time"
convention (`pnl_engine.py`, `live_price`, `history_charts.py` all do the
same).

Path convention: `/api/pl-intelligence/{company_id}` (+ sub-paths), not the
spec's literal `/api/v1/stocks/{symbol}/fundamentals/pl` — this app has no
`/api/v1/` prefix or symbol-keyed routing anywhere (every other route here
is `company_id`-keyed under a flat `/api/...` prefix), so the route follows
THIS app's actual convention rather than the spec's aspirational one.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from app.calculations.pl_intelligence import compute_pl_intelligence
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis

router = APIRouter(prefix="/api/pl-intelligence")


def _latest_sector_name(db, company_id: str) -> str | None:
    analysis = (
        db.query(FundamentalAnalysis)
        .filter_by(stock_id=company_id, status="COMPLETED")
        .order_by(FundamentalAnalysis.completed_at.desc())
        .first()
    )
    return (analysis.sector_analysis or {}).get("sector_name") if analysis else None


# The 3 specific sub-paths (/peers, /history, /score) MUST be registered
# before the bare "/{company_id:path}" route below — Starlette matches
# routes in registration order, and a `:path` converter is greedy (it
# matches slashes too), so if the bare route came first it would swallow
# "NSE:MARUTI/score" whole as company_id="NSE:MARUTI/score" and never reach
# the /score handler at all. Confirmed live (2026-09-15): exactly that
# happened on first deploy — /score and /peers both silently fell through
# to the bare handler and returned an all-null "company not found" shape
# for a company that has real data.
@router.get("/{company_id:path}/peers")
def get_pl_intelligence_peers(company_id: str):
    db = get_db()
    try:
        sector_name = _latest_sector_name(db, company_id)
        result = compute_pl_intelligence(db, company_id, sector_name=sector_name)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "peer_percentiles": result.get("peer_percentiles"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}/history")
def get_pl_intelligence_history(company_id: str):
    db = get_db()
    try:
        sector_name = _latest_sector_name(db, company_id)
        result = compute_pl_intelligence(db, company_id, sector_name=sector_name)
        return {
            "company_id": company_id,
            "statement_type": result.get("statement_type"),
            "cascade": result.get("cascade"),
            "earnings_bridge": result.get("earnings_bridge"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}/score")
def get_pl_intelligence_score(company_id: str):
    db = get_db()
    try:
        sector_name = _latest_sector_name(db, company_id)
        result = compute_pl_intelligence(db, company_id, sector_name=sector_name)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "score": result.get("score"),
            "diagnostic_flags": result.get("diagnostic_flags"),
            "diagnostics": result.get("diagnostics"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}")
def get_pl_intelligence(company_id: str, statement_type: Literal["CONSOLIDATED", "STANDALONE"] | None = None):
    """`statement_type` powers the frontend's Consolidated/Standalone
    toggle — when given, forces exactly that one with NO fallback (see
    `compute_pl_intelligence()`'s own docstring); omitted, it picks
    whichever actually has data, preferring CONSOLIDATED."""
    db = get_db()
    try:
        sector_name = _latest_sector_name(db, company_id)
        kwargs = {"allow_fallback": False, "statement_type": statement_type} if statement_type else {}
        return compute_pl_intelligence(db, company_id, sector_name=sector_name, **kwargs)
    finally:
        db.close()
