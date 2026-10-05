"""Runs the framework's scores for one company from data the app already has
and stores them. Called at the end of both the quick scorer and the full
analysis, so every company that gets the older scores gets these too."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.framework import store
from app.framework.business_quality import compute_business_quality
from app.framework.fundamental import LENDER_FRAMEWORKS, compute_fundamental
from app.framework.quality import compute_quality
from app.framework.screener_series import annual
from app.framework.trend import classify_trend


def score_company(db: Session, stock_id: str, basis: str, category_scores: dict, metrics: dict,
                  financial_data: dict, sector_framework: str) -> dict:
    """Never raises: a company the framework cannot score is recorded with the
    reason, not dropped."""
    lender = sector_framework in LENDER_FRAMEWORKS
    series = annual(db, stock_id)
    fundamental = compute_fundamental(category_scores, metrics, financial_data, sector_framework,
                                      db=db, company_id=stock_id, series=series)
    trend = classify_trend(metrics, lender=lender)
    business = compute_business_quality(db, stock_id, lender, series)
    quality = compute_quality(fundamental, business)
    store.save(
        db, stock_id, basis,
        {"fundamental": fundamental["score"], "business_quality": business["score"], "quality": quality["score"],
         "trend": trend["trend"], "sector_framework": sector_framework, "latest_fy": metrics.get("latest_fy")},
        {"fundamental": fundamental, "trend": trend, "business_quality": business, "quality": quality},
    )
    return {"fundamental": fundamental, "trend": trend, "business_quality": business, "quality": quality}
