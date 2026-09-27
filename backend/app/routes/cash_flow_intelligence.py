"""Cash Flow Analysis Engine — read-only, frontend-facing REST surface.
Compute-on-read, same pattern as `app/routes/balance_sheet_intelligence.py`:
calls `compute_cash_flow_intelligence()` fresh per request rather than
persisting a score table (this package has none — see its `__init__.py`
docstring).

Path convention: `/api/cash-flow-intelligence/{company_id}` (+ sub-paths),
matching `balance_sheet_intelligence.py`'s own convention.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from app.calculations.balance_sheet_intelligence import compute_balance_sheet_intelligence
from app.calculations.cash_flow_intelligence import compute_cash_flow_intelligence
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis

router = APIRouter(prefix="/api/cash-flow-intelligence")


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


def _compute(db, company_id: str, statement_type: str | None = None) -> dict:
    sector_name, metrics = _latest_analysis_context(db, company_id)
    # Reuses balance_sheet_intelligence's own working_capital DSO/DIO/DPO
    # series as a receivables/inventory-growth proxy — same cross-package
    # call the orchestrator's pipeline stage makes, see
    # `cash_flow_intelligence/__init__.py`'s own docstring for why. Passes
    # the same forced `statement_type` through to both calls so a toggled
    # request stays internally consistent (DSO/DIO from the same statement
    # type as the cash-flow schedule data it's blended with).
    bsi_result = compute_balance_sheet_intelligence(
        db, company_id, sector_name=sector_name, yfinance_metrics=metrics, statement_type=statement_type,
    )
    return compute_cash_flow_intelligence(
        db, company_id, sector_name=sector_name, yfinance_metrics=metrics,
        balance_sheet_intelligence_result=bsi_result, statement_type=statement_type,
    )


# The specific sub-paths MUST be registered before the bare
# "/{company_id:path}" route below — Starlette matches routes in
# registration order and a `:path` converter is greedy, so a bare route
# registered first would swallow "NSE:MARUTI/coverage" whole as
# company_id="NSE:MARUTI/coverage" and never reach the /coverage handler at
# all (same ordering bug documented in `balance_sheet_intelligence.py`,
# applied here from the start).
@router.get("/{company_id:path}/coverage")
def get_cash_flow_coverage(company_id: str):
    db = get_db()
    try:
        result = _compute(db, company_id)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "coverage": result.get("coverage"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}/red-flags")
def get_cash_flow_red_flags(company_id: str):
    db = get_db()
    try:
        result = _compute(db, company_id)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "risk_flags": result.get("risk_flags"),
            "forensic_patterns": result.get("forensic_patterns"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}/archetype")
def get_cash_flow_archetype(company_id: str):
    db = get_db()
    try:
        result = _compute(db, company_id)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "archetype": result.get("archetype"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}/reconciliation")
def get_cash_flow_reconciliation(company_id: str):
    db = get_db()
    try:
        result = _compute(db, company_id)
        return {
            "company_id": company_id,
            "period": result.get("period"),
            "reconciliation": result.get("reconciliation"),
            "conversion": result.get("conversion"),
        }
    finally:
        db.close()


@router.get("/{company_id:path}")
def get_cash_flow_intelligence(company_id: str, statement_type: Literal["CONSOLIDATED", "STANDALONE"] | None = None):
    """`statement_type` powers the frontend's Consolidated/Standalone
    toggle — when given, forces exactly that one with NO fallback; omitted,
    it picks whichever actually has schedule data, preferring
    CONSOLIDATED."""
    db = get_db()
    try:
        return _compute(db, company_id, statement_type=statement_type)
    finally:
        db.close()
