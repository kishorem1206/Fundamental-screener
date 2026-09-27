"""Balance Sheet Analysis Engine — read-only, frontend-facing REST surface.
Compute-on-read, same pattern as `app/routes/pl_intelligence.py`/
`history_charts.py`: calls `compute_balance_sheet_intelligence()` fresh per
request rather than persisting a score table (this package has none — see
its `__init__.py` docstring).

Path convention: `/api/balance-sheet-intelligence/{company_id}` (+
sub-paths), matching `pl_intelligence.py`'s own convention.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from app.calculations.balance_sheet_intelligence import compute_balance_sheet_intelligence
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis

router = APIRouter(prefix="/api/balance-sheet-intelligence")


def _latest_analysis_context(db, company_id: str) -> tuple[str | None, dict]:
    analysis = (
        db.query(FundamentalAnalysis)
        .filter_by(stock_id=company_id, status="COMPLETED")
        .order_by(FundamentalAnalysis.completed_at.desc())
        .first()
    )
    if analysis is None:
        return None, {}
    sector_name = (analysis.sector_analysis or {}).get("sector_name")
    return sector_name, (analysis.metrics or {})


# The 3 specific sub-paths MUST be registered before the bare
# "/{company_id:path}" route below — Starlette matches routes in
# registration order and a `:path` converter is greedy, so a bare route
# registered first would swallow "NSE:MARUTI/coverage" whole as
# company_id="NSE:MARUTI/coverage" and never reach the /coverage handler at
# all (confirmed as a real, already-hit bug on `pl_intelligence.py`'s own
# first deploy — same ordering discipline applied here from the start).
@router.get("/{company_id:path}/coverage")
def get_balance_sheet_coverage(company_id: str):
    db = get_db()
    try:
        sector_name, metrics = _latest_analysis_context(db, company_id)
        result = compute_balance_sheet_intelligence(db, company_id, sector_name=sector_name, yfinance_metrics=metrics)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "coverage": result.get("coverage"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}/red-flags")
def get_balance_sheet_red_flags(company_id: str):
    db = get_db()
    try:
        sector_name, metrics = _latest_analysis_context(db, company_id)
        result = compute_balance_sheet_intelligence(db, company_id, sector_name=sector_name, yfinance_metrics=metrics)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "risk_flags": result.get("risk_flags"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}/archetype")
def get_balance_sheet_archetype(company_id: str):
    db = get_db()
    try:
        sector_name, metrics = _latest_analysis_context(db, company_id)
        result = compute_balance_sheet_intelligence(db, company_id, sector_name=sector_name, yfinance_metrics=metrics)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "archetype": result.get("archetype"),
            "financial_institution_summary": result.get("financial_institution_summary"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}")
def get_balance_sheet_intelligence(company_id: str, statement_type: Literal["CONSOLIDATED", "STANDALONE"] | None = None):
    """`statement_type` powers the frontend's Consolidated/Standalone
    toggle — when given, forces exactly that one with NO fallback; omitted,
    it picks whichever actually has data, preferring CONSOLIDATED."""
    db = get_db()
    try:
        sector_name, metrics = _latest_analysis_context(db, company_id)
        return compute_balance_sheet_intelligence(
            db, company_id, sector_name=sector_name, yfinance_metrics=metrics, statement_type=statement_type,
        )
    finally:
        db.close()
