"""Manual entry/override and provenance-history endpoints for banking metrics.

Needed regardless of how much ingestion automation exists: the BSE ingester
will sometimes fail to find a filing, OCR will sometimes misread a figure, and
metrics like CASA/PCR/slippage aren't sourced at all yet (they live in investor
presentations, not the standard SEBI results PDF — see
app/ingestion/banking_ingestion.py). This is the human-in-the-loop safety valve
banking.md's provenance model assumes exists.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock
from app.infrastructure.database import metric_store
from app.logger import logger

router = APIRouter(prefix="/api/banking")


class ManualMetricEntry(BaseModel):
    metric_key: str
    period: str
    value: float
    unit: str = "%"
    confidence: str = "MEDIUM"
    reported_or_calculated: str = "REPORTED"
    source_url: str | None = None
    source_document: str | None = None
    note: str | None = None


def _row_to_dict(row) -> dict:
    return {
        "id": row.id,
        "metric_key": row.metric_key,
        "period": row.period,
        "value": float(row.value),
        "unit": row.unit,
        "source": row.source,
        "source_tier": row.source_tier,
        "source_url": row.source_url,
        "source_document": row.source_document,
        "source_date": row.source_date.isoformat() if row.source_date else None,
        "retrieved_at": row.retrieved_at.isoformat(),
        "reported_or_calculated": row.reported_or_calculated,
        "calculation_formula": row.calculation_formula,
        "confidence": row.confidence,
        "raw_reported_value": row.raw_reported_value,
    }


@router.post("/{company_id}/metrics")
def add_manual_metric(company_id: str, entry: ManualMetricEntry):
    """Manual entry/correction — always source=MANUAL, tier 1 (a human asserting
    a value is treated as at least as authoritative as an automated tier-1 fetch;
    it is never silently preferred over a HIGH-confidence automated value at the
    same tier — get_authoritative_value ties break by most recent retrieval)."""
    db = get_db()
    try:
        stock = db.query(Stock).filter_by(id=company_id).first()
        if stock is None:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
        if entry.confidence not in metric_store.VALID_CONFIDENCE:
            raise HTTPException(status_code=400, detail=f"Invalid confidence: {entry.confidence}")
        if entry.reported_or_calculated not in metric_store.VALID_REPORTED_OR_CALCULATED:
            raise HTTPException(status_code=400, detail=f"Invalid reported_or_calculated: {entry.reported_or_calculated}")

        row = metric_store.insert_metric_value(
            db,
            company_id=company_id,
            metric_key=entry.metric_key,
            period=entry.period,
            value=entry.value,
            unit=entry.unit,
            source="MANUAL",
            source_tier=1,
            reported_or_calculated=entry.reported_or_calculated,
            confidence=entry.confidence,
            source_url=entry.source_url,
            source_document=entry.source_document or entry.note,
            source_date=datetime.now(timezone.utc),
        )
        if row is None:
            raise HTTPException(
                status_code=400,
                detail=f"Value {entry.value}{entry.unit} failed the plausibility guard for a "
                       f"{entry.unit} metric and was not stored — double-check the value and unit.",
            )
        db.commit()
        return _row_to_dict(row)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def _run_annual_report_batch(max_companies_per_run: int):
    from app.ingestion.annual_report_ingestion import ingest_all_banks_annual_reports
    db = get_db()
    try:
        result = ingest_all_banks_annual_reports(db, max_companies_per_run=max_companies_per_run)
        logger.info("annual-report batch finished via API trigger", **result)
    finally:
        db.close()


@router.post("/annual-reports/ingest-batch")
def trigger_annual_report_batch(background_tasks: BackgroundTasks, max_companies: int = 5):
    """Kick off the "all banks" annual-report batch (app/ingestion/annual_report_ingestion.py
    ::ingest_all_banks_annual_reports) in the background — bounded to `max_companies`
    per call and resumable (already-covered banks are skipped via a ~300-day gate),
    since one unbounded run would exceed the LLM provider's daily token quota.
    Meant to be called repeatedly (a daily cron, or manually) until the whole
    banking universe is covered."""
    background_tasks.add_task(_run_annual_report_batch, max_companies)
    return {"status": "started", "max_companies": max_companies}


def _run_backfill_batch(max_companies_per_run: int, years: int):
    from app.ingestion.banking_ingestion import backfill_all_banks
    db = get_db()
    try:
        result = backfill_all_banks(db, max_companies_per_run=max_companies_per_run, years=years)
        logger.info("backfill batch finished via API trigger", **result)
    finally:
        db.close()


@router.post("/backfill/ingest-batch")
def trigger_backfill_batch(background_tasks: BackgroundTasks, max_companies: int = 3, years: int = 5):
    """Kick off the 5-year BSE OCR backfill batch (app/ingestion/banking_ingestion.py
    ::backfill_all_banks) in the background — bounded to `max_companies` per call
    and resumable (already-backfilled banks skipped via a 30-day gate). Removed
    from the live per-analysis pipeline on 2026-09-10: ~15-20 sequential Groq
    calls per company reliably collided with the provider's per-minute rate
    limit and stalled a bank's first-ever analysis on the sector_analysis stage
    for several minutes. Meant to be called repeatedly (a daily cron, or
    manually) until the whole banking universe has historical trend data."""
    background_tasks.add_task(_run_backfill_batch, max_companies, years)
    return {"status": "started", "max_companies": max_companies, "years": years}


@router.get("/{company_id}/metrics/{metric_key}/history")
def get_metric_history(company_id: str, metric_key: str, period: str | None = None):
    """Full provenance ledger for one metric — every source that reported a
    value, not just the winner, per banking.md section 22 (never silently
    replace conflicting values).

    `statement_type=None` on the history fetch (2026-09-23) — this
    endpoint's whole purpose is "every source, not just the winner," so it
    must include both STANDALONE and CONSOLIDATED rows; the old unqualified
    call defaulted to STANDALONE only, meaning a CONSOLIDATED row could win
    authoritative_id (get_authoritative_value's own default now prefers
    CONSOLIDATED) while not even appearing in the returned history list."""
    db = get_db()
    try:
        stock = db.query(Stock).filter_by(id=company_id).first()
        if stock is None:
            raise HTTPException(status_code=404, detail=f"Company {company_id} not found")

        history = metric_store.get_metric_history(db, company_id, metric_key, period, statement_type=None)
        result = [_row_to_dict(r) for r in history]

        authoritative_period = period or (history[0].period if history else None)
        winner_id = None
        if authoritative_period:
            winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, authoritative_period)
            winner_id = winner.id if winner else None

        return {
            "company_id": company_id,
            "metric_key": metric_key,
            "authoritative_id": winner_id,
            "history": result,
        }
    finally:
        db.close()
