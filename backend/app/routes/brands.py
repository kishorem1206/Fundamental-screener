"""Structured brand intelligence — read-only. See
app/interpretation/brand_extraction.py's module docstring.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import CompanyBrand

router = APIRouter(prefix="/api/brands")


@router.get("/{company_id:path}")
def get_company_brands(company_id: str):
    db = get_db()
    try:
        rows = (
            db.query(CompanyBrand)
            .filter_by(company_id=company_id)
            .order_by(CompanyBrand.category, CompanyBrand.brand_name)
            .all()
        )
        return {
            "company_id": company_id,
            "brands": [
                {
                    "brand_name": r.brand_name,
                    "category": r.category,
                    "ownership": r.ownership,
                    "market_share_pct": float(r.market_share_pct) if r.market_share_pct is not None else None,
                    "market_share_context": r.market_share_context,
                    "license_expiry": r.license_expiry,
                }
                for r in rows
            ],
        }
    finally:
        db.close()
