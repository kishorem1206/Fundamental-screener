"""Quarterly Report Extraction Engine — read-only, frontend-facing REST
surface. Compute-on-read, same pattern as `pl_intelligence.py`/
`history_charts.py`: calls `compute_quarterly_intelligence()` fresh per
request rather than reading a persisted table.

Also surfaces the Quarterly Sector KPI Extraction Engine's data (2026-09-20,
`app/calculations/quarterly_sector_kpis.py`) under the same response, keyed
`"sector_kpis"` — a separate compute function, since it's sector-specific
and `available: false` for the ~29 sectors with no configured quarterly
area, but kept on this one endpoint so the frontend needs only one fetch
per company for the whole Quarterly tab.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from app.calculations.quarterly_intelligence import compute_quarterly_intelligence
from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis

router = APIRouter(prefix="/api/quarterly-intelligence")


def _latest_sector_name(db, company_id: str) -> str | None:
    analysis = (
        db.query(FundamentalAnalysis)
        .filter_by(stock_id=company_id, status="COMPLETED")
        .order_by(FundamentalAnalysis.completed_at.desc())
        .first()
    )
    return (analysis.sector_analysis or {}).get("sector_name") if analysis else None


@router.get("/{company_id:path}")
def get_quarterly_intelligence(company_id: str, statement_type: Literal["CONSOLIDATED", "STANDALONE"] | None = None):
    """`statement_type` powers the frontend's Consolidated/Standalone
    toggle — when given, forces exactly that one with NO fallback (matching
    `pl_intelligence.py`'s contract); omitted, picks whichever actually has
    data, preferring CONSOLIDATED. Same statement_type is applied to the
    generic quarterly data; sector_kpis resolves its own independently
    (it has no allow_fallback concept — always prefers CONSOLIDATED,
    same as compute_quarterly_intelligence's own default)."""
    db = get_db()
    try:
        kwargs = {"allow_fallback": False, "statement_type": statement_type} if statement_type else {}
        result = compute_quarterly_intelligence(db, company_id, **kwargs)
        sector_name = _latest_sector_name(db, company_id)
        result["sector_kpis"] = compute_quarterly_sector_kpis(db, company_id, sector_name)
        return result
    finally:
        db.close()
