"""Runs the framework's scores for one company from data the app already has
and stores them. Called at the end of both the quick scorer and the full
analysis, so every company that gets the older scores gets these too."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.framework import price_stats, store
from app.framework.business_quality import compute_business_quality
from app.framework.fundamental import LENDER_FRAMEWORKS, compute_fundamental
from app.framework.momentum import compute_momentum
from app.framework.quality import compute_quality
from app.framework.quantitative import compute_quantitative
from app.framework.relative_strength import compute_relative_strength, why_holding_up
from app.framework.technical import compute_technical
from app.framework.valuation import INTERPRETATION, compute_valuation
from app.infrastructure.database.models import Stock
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
    momentum = compute_momentum(db, stock_id, sector_framework, lender, quality["score"])
    end = price_stats.as_of(db)
    quantitative = compute_quantitative(db, stock_id, series, lender, end)
    relative = compute_relative_strength(db, stock_id, end)
    holding_up = why_holding_up(relative, fundamental, quantitative, business)
    if holding_up:
        relative["why_holding_up"] = holding_up
    technical = compute_technical(db, stock_id, end)
    stock = db.get(Stock, stock_id)
    # multiples are compared within the industry when it is big enough (banks with banks), else the sector
    peer_label, peer_ids = None, []
    for column in ("industry", "sector"):
        value = getattr(stock, column, None) if stock else None
        if value:
            ids = [sid for (sid,) in db.query(Stock.id).filter(getattr(Stock, column) == value, Stock.is_active.is_(True),
                                                               Stock.id != stock_id)]
            if len(ids) >= 8 or column == "sector":
                peer_label, peer_ids = value, ids
                break
    valuation = compute_valuation(db, stock_id, series, metrics, lender, end, peer_label, peer_ids)
    if valuation.get("view") and quality.get("score") is not None:
        valuation["interpretation"] = INTERPRETATION[(quality["score"] >= 65, valuation["view"])]
    store.save(
        db, stock_id, basis,
        {"fundamental": fundamental["score"], "business_quality": business["score"], "quality": quality["score"],
         "quantitative": quantitative["score"], "relative_strength": relative["score"],
         "technical": technical["score"], "valuation": valuation["score"], "valuation_view": valuation.get("view"),
         "quality_change_6m": (momentum.get("6m") or {}).get("change"), "quality_change_12m": (momentum.get("12m") or {}).get("change"),
         "quality_direction": momentum["direction"],
         "trend": trend["trend"], "sector_framework": sector_framework, "latest_fy": metrics.get("latest_fy")},
        {"fundamental": fundamental, "trend": trend, "business_quality": business, "quality": quality,
         "quantitative": quantitative, "relative_strength": relative, "technical": technical, "valuation": valuation,
         "momentum": momentum},
    )
    from app.framework.decisions import decide_one
    decision = decide_one(db, stock_id)
    return {"decision": decision, "fundamental": fundamental, "trend": trend, "business_quality": business, "quality": quality,
            "quantitative": quantitative, "relative_strength": relative, "technical": technical, "valuation": valuation,
            "momentum": momentum}
