"""The single source of truth for the full-analysis JSON shape returned by
`GET /api/fundamental/analyses/{id}` — extracted so the standalone HTML
export (`app/reporting/html_export_service.py`) can build the exact same
payload it embeds without duplicating (and risking drift from) this logic.
"""
from __future__ import annotations

from pathlib import Path

from app.infrastructure.database.models import FundamentalAnalysis


def analysis_to_dict(a: FundamentalAnalysis) -> dict:
    return {
        "id": a.id,
        "stock_id": a.stock_id,
        "status": a.status,
        "current_stage": a.current_stage,
        "stage_progress": a.stage_progress,
        "overall_progress": a.overall_progress,
        "overall_score": float(a.overall_score) if a.overall_score is not None else None,
        "confidence_score": float(a.confidence_score) if a.confidence_score is not None else None,
        "data_quality_score": float(a.data_quality_score) if a.data_quality_score is not None else None,
        "ai_rating": a.ai_rating,
        "valuation_rating": a.valuation_rating,
        "company_info": a.company_info,
        "error_message": a.error_message,
        "report_available": a.report_path is not None and Path(a.report_path).exists(),
        "started_at": a.started_at.isoformat() if a.started_at else None,
        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        "created_at": a.created_at.isoformat(),
    }


def get_full_analysis_dict(analysis_id: str, db) -> dict | None:
    """Same shape as `GET /api/fundamental/analyses/{id}`. `None` if not found."""
    analysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
    if analysis is None:
        return None

    result = analysis_to_dict(analysis)
    # week52_high/low live in financial_data.market (yfinance_client.py),
    # fetched for every analysis already but only exposed here.
    market_snapshot = (analysis.financial_data or {}).get("market") or {}
    if result["company_info"] is not None:
        result["company_info"] = {
            **result["company_info"],
            "week52_high": market_snapshot.get("week52_high"),
            "week52_low": market_snapshot.get("week52_low"),
        }
    result["metrics"] = analysis.metrics
    result["scores"] = analysis.scores
    result["sector_analysis"] = analysis.sector_analysis
    result["peers"] = analysis.peers
    result["risks"] = analysis.risks or []
    result["catalysts"] = analysis.catalysts or []
    result["ai_analysis"] = analysis.ai_analysis
    result["metric_validations"] = analysis.metric_validations
    result["report_blueprint"] = analysis.report_blueprint
    return result
