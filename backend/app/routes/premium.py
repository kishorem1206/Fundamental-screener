"""Premium PDF System's remaining frontend-facing data — read-only.
Reuses the exact `build_premium_extras` builder both PDF paths already call
(see app/reporting/premium_report_data.py) so the frontend can never drift
from what the PDF shows: rebased peer price performance (B4), the sources
& evidence ledger (B6), the "what changed since last analysis" diff (B7,
against the company's most recent COMPLETED analysis), and the 1Y/5Y price
chart (yfinance — 2026-09-15, chosen over TradingView Desktop, which
wouldn't stay running long enough for CDP to connect in this environment,
and Dhan's historical-data API, which needs a fresh broker login). B1
(brands) has its own existing route (app/routes/brands.py); B2/B3/B5 live
under app/routes/concall.py since they're concall-specific.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis
from app.reporting.premium_report_data import build_premium_extras

router = APIRouter(prefix="/api/premium")


@router.get("/{company_id:path}")
def get_premium_extras(company_id: str):
    db = get_db()
    try:
        analysis = (
            db.query(FundamentalAnalysis)
            .filter_by(stock_id=company_id, status="COMPLETED")
            .order_by(FundamentalAnalysis.completed_at.desc())
            .first()
        )
        if analysis is None:
            raise HTTPException(status_code=404, detail=f"No completed analysis found for '{company_id}'")
        extras = build_premium_extras(db, company_id, analysis)
        return {
            "company_id": company_id,
            "peer_performance": extras.get("peer_performance"),
            "source_ledger": extras.get("source_ledger"),
            "change_log": extras.get("change_log"),
            "price_chart": extras.get("price_chart"),
        }
    finally:
        db.close()
