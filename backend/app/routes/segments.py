"""Business segment revenue history — read-only. See
app/ingestion/tradingview_segments_client.py's module docstring.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import BusinessSegment

router = APIRouter(prefix="/api/segments")


@router.get("/{company_id:path}")
def get_business_segments(company_id: str):
    db = get_db()
    try:
        rows = (
            db.query(BusinessSegment)
            .filter_by(company_id=company_id)
            .order_by(BusinessSegment.segment_name, BusinessSegment.fiscal_year)
            .all()
        )
        return {
            "company_id": company_id,
            "source": "TRADINGVIEW",
            "segments": [
                {
                    "segment_name": r.segment_name,
                    "fiscal_year": r.fiscal_year,
                    "revenue": float(r.revenue),
                    "currency": r.currency,
                }
                for r in rows
            ],
        }
    finally:
        db.close()
