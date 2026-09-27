"""Governance/integrity read + trigger endpoints — Architecture v2 Stage 3.
Sector-agnostic (unlike app/routes/banking_data.py): shareholding pattern is
filed by every listed company, not just banks.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import GovernanceEvent, Shareholding, ShareholdingScreener, Stock
from app.logger import logger

router = APIRouter(prefix="/api/governance")


def _shareholding_to_dict(row: Shareholding) -> dict:
    return {
        "period_end": row.period_end,
        "promoter_pct": float(row.promoter_pct) if row.promoter_pct is not None else None,
        "public_pct": float(row.public_pct) if row.public_pct is not None else None,
        "pledge_pct": float(row.pledge_pct) if row.pledge_pct is not None else None,
        "source_url": row.source_url,
        "retrieved_at": row.retrieved_at.isoformat(),
    }


def _shareholding_screener_to_dict(row: ShareholdingScreener) -> dict:
    return {
        "period_end": row.period_end,
        "promoter_pct": float(row.promoter_pct) if row.promoter_pct is not None else None,
        "fii_pct": float(row.fii_pct) if row.fii_pct is not None else None,
        "dii_pct": float(row.dii_pct) if row.dii_pct is not None else None,
        "public_pct": float(row.public_pct) if row.public_pct is not None else None,
        "shareholder_count": row.shareholder_count,
        "retrieved_at": row.retrieved_at.isoformat(),
    }


def _event_to_dict(row: GovernanceEvent) -> dict:
    return {
        "event_type": row.event_type,
        "severity": row.severity,
        "event_date": row.event_date,
        "description": row.description,
        "evidence": row.evidence,
        "source": row.source,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/{company_id:path}/shareholding")
def get_shareholding_history(company_id: str):
    """Promoter/public/pledge % history, newest period first."""
    db = get_db()
    try:
        rows = (
            db.query(Shareholding)
            .filter_by(company_id=company_id)
            .order_by(Shareholding.period_end.desc())
            .all()
        )
        return {"company_id": company_id, "shareholding": [_shareholding_to_dict(r) for r in rows]}
    finally:
        db.close()


@router.get("/{company_id:path}/shareholding-screener")
def get_shareholding_screener_history(company_id: str):
    """Supplementary promoter/FII/DII/public % history from Screener.in
    (app/ingestion/screener_shareholding_client.py) — never blended with
    NSE's `shareholding` data above. No pledge % field exists on Screener's
    side at all; for pledge tracking use /shareholding, not this endpoint.
    Returns quarterly and yearly series separately, newest period first."""
    db = get_db()
    try:
        rows = (
            db.query(ShareholdingScreener)
            .filter_by(company_id=company_id)
            .order_by(ShareholdingScreener.period_end.desc())
            .all()
        )
        quarterly = [_shareholding_screener_to_dict(r) for r in rows if r.frequency == "quarterly"]
        yearly = [_shareholding_screener_to_dict(r) for r in rows if r.frequency == "yearly"]
        return {
            "company_id": company_id,
            "disclaimer": "Source: Screener.in — supplementary trend data only, no pledge % field.",
            "quarterly": quarterly,
            "yearly": yearly,
        }
    finally:
        db.close()


@router.get("/{company_id:path}/events")
def get_governance_events(company_id: str):
    """Deterministic, evidence-backed governance flags, newest first."""
    db = get_db()
    try:
        rows = (
            db.query(GovernanceEvent)
            .filter_by(company_id=company_id)
            .order_by(GovernanceEvent.event_date.desc())
            .all()
        )
        return {"company_id": company_id, "events": [_event_to_dict(r) for r in rows]}
    finally:
        db.close()


@router.post("/{company_id:path}/ingest")
def trigger_shareholding_ingest(company_id: str, quarters: int = 8):
    """Fetch/refresh shareholding history and re-run event detection for one
    company, synchronously (a handful of NSE calls — fast enough not to
    need a background task, unlike the multi-quarter OCR backfills). Also
    refreshes the supplementary Screener.in trend data in the same call."""
    from app.ingestion.shareholding_client import ingest_shareholding
    from app.ingestion.screener_shareholding_client import ingest_screener_shareholding

    db = get_db()
    try:
        stock = db.query(Stock).filter_by(id=company_id).first()
        if stock is None:
            raise HTTPException(status_code=404, detail=f"Stock {company_id} not found")
        result = ingest_shareholding(db, company_id=company_id, symbol=stock.symbol, quarters=quarters)
        result["screener"] = ingest_screener_shareholding(db, company_id=company_id, symbol=stock.symbol)
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.warning("governance: ingest trigger failed", company_id=company_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
