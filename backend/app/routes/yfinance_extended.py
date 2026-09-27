"""Yahoo Finance extended fundamental data — read endpoints. Ingestion is
autonomous (app/ingestion/yfinance_extended_client.py, wired into every
analysis run in orchestrator.py) — these routes only read what's already
stored, they don't trigger a fetch.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import (
    CompanyNews, CorporateAction, EarningsCalendar, ForwardEstimate, InsiderActivity,
)

router = APIRouter(prefix="/api/yfinance")


@router.get("/{company_id:path}/forward-estimates")
def get_forward_estimates(company_id: str):
    """Consensus EPS/revenue estimates and growth estimates, by period —
    Yahoo Finance analysts."""
    db = get_db()
    try:
        rows = db.query(ForwardEstimate).filter_by(company_id=company_id).all()
        by_metric: dict[str, list[dict]] = {}
        for r in rows:
            by_metric.setdefault(r.metric_type, []).append({
                "period_label": r.period_label,
                "avg": float(r.avg) if r.avg is not None else None,
                "low": float(r.low) if r.low is not None else None,
                "high": float(r.high) if r.high is not None else None,
                "num_analysts": r.num_analysts,
                "growth_pct": float(r.growth_pct) if r.growth_pct is not None else None,
            })
        return {
            "company_id": company_id, "source": "YAHOO_FINANCE",
            "estimates": by_metric,
        }
    finally:
        db.close()


@router.get("/{company_id:path}/insider-activity")
def get_insider_activity(company_id: str):
    """Dated, named insider transactions — Yahoo Finance."""
    db = get_db()
    try:
        rows = (
            db.query(InsiderActivity).filter_by(company_id=company_id)
            .order_by(InsiderActivity.transaction_date.desc()).all()
        )
        return {
            "company_id": company_id, "source": "YAHOO_FINANCE",
            "transactions": [
                {
                    "date": r.transaction_date, "insider_name": r.insider_name,
                    "position": r.position, "text": r.transaction_text,
                    "shares": float(r.shares) if r.shares is not None else None,
                    "value": float(r.value) if r.value is not None else None,
                    "ownership_type": r.ownership_type,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@router.get("/{company_id:path}/corporate-actions")
def get_corporate_actions(company_id: str):
    """Dividend/split history — Yahoo Finance."""
    db = get_db()
    try:
        rows = (
            db.query(CorporateAction).filter_by(company_id=company_id)
            .order_by(CorporateAction.action_date.desc()).all()
        )
        return {
            "company_id": company_id, "source": "YAHOO_FINANCE",
            "actions": [
                {"date": r.action_date, "type": r.action_type, "value": float(r.value)}
                for r in rows
            ],
        }
    finally:
        db.close()


@router.get("/{company_id:path}/news")
def get_company_news(company_id: str):
    """Recent news headlines — Yahoo Finance (aggregates Reuters and other
    wire services)."""
    db = get_db()
    try:
        rows = (
            db.query(CompanyNews).filter_by(company_id=company_id)
            .order_by(CompanyNews.published_at.desc()).all()
        )
        return {
            "company_id": company_id, "source": "YAHOO_FINANCE",
            "news": [
                {
                    "headline": r.headline, "summary": r.summary, "provider": r.provider,
                    "url": r.url, "published_at": r.published_at.isoformat() if r.published_at else None,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@router.get("/{company_id:path}/calendar")
def get_earnings_calendar(company_id: str):
    """Next earnings date + expected EPS/revenue range — Yahoo Finance
    ("future schedules")."""
    db = get_db()
    try:
        row = db.query(EarningsCalendar).filter_by(company_id=company_id).first()
        if row is None:
            return {"company_id": company_id, "source": "YAHOO_FINANCE", "calendar": None}
        return {
            "company_id": company_id, "source": "YAHOO_FINANCE",
            "calendar": {
                "next_earnings_date": row.next_earnings_date,
                "ex_dividend_date": row.ex_dividend_date,
                "expected_eps_avg": float(row.expected_eps_avg) if row.expected_eps_avg is not None else None,
                "expected_eps_low": float(row.expected_eps_low) if row.expected_eps_low is not None else None,
                "expected_eps_high": float(row.expected_eps_high) if row.expected_eps_high is not None else None,
                "expected_revenue_avg": float(row.expected_revenue_avg) if row.expected_revenue_avg is not None else None,
                "expected_revenue_low": float(row.expected_revenue_low) if row.expected_revenue_low is not None else None,
                "expected_revenue_high": float(row.expected_revenue_high) if row.expected_revenue_high is not None else None,
            },
        }
    finally:
        db.close()
