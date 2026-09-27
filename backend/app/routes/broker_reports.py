"""Broker research-report history (Trendlyne, free table only) — read-only.
See app/ingestion/trendlyne_client.py's module docstring.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import BrokerResearchReport

router = APIRouter(prefix="/api/broker-reports")


@router.get("/{company_id:path}")
def get_broker_reports(company_id: str):
    db = get_db()
    try:
        rows = (
            db.query(BrokerResearchReport)
            .filter_by(company_id=company_id)
            .order_by(BrokerResearchReport.report_date.desc())
            .all()
        )
        return {
            "company_id": company_id,
            "source": "TRENDLYNE",
            "reports": [
                {
                    "report_date": r.report_date,
                    "broker_name": r.broker_name,
                    "rating": r.rating,
                    "target_price": float(r.target_price) if r.target_price is not None else None,
                    "ltp_at_capture": float(r.ltp_at_capture) if r.ltp_at_capture is not None else None,
                    "price_at_reco": float(r.price_at_reco) if r.price_at_reco is not None else None,
                    "change_since_reco_pct": float(r.change_since_reco_pct) if r.change_since_reco_pct is not None else None,
                    "upside_pct": float(r.upside_pct) if r.upside_pct is not None else None,
                    "reco_changed": r.reco_changed,
                    "target_changed": r.target_changed,
                }
                for r in rows
            ],
        }
    finally:
        db.close()
