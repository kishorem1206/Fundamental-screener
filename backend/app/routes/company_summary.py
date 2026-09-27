"""Screener.in company summary (about + key_points) — read-only. See
app/ingestion/screener_client.py's ingest_company_summary() docstring.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import CompanySummary

router = APIRouter(prefix="/api/company-summary")


@router.get("/{company_id:path}")
def get_company_summary(company_id: str):
    db = get_db()
    try:
        row = db.query(CompanySummary).filter_by(company_id=company_id).first()
        if row is None:
            return {"company_id": company_id, "summary": None}
        return {
            "company_id": company_id,
            "summary": {
                "about": row.about,
                "key_points": row.key_points,
                "source": row.source,
                "retrieved_at": row.retrieved_at.isoformat(),
            },
        }
    finally:
        db.close()
