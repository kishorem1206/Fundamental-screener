"""Bounded, resumable batch job that fills fa_bulk_metrics — Architecture v2
Stage 2. Runs only the cheap, deterministic first half of the analysis
pipeline (fetch_financial_data + compute_metrics, both pure Python/yfinance,
no LLM, no OCR) across the whole active stock universe, so the declarative
screening engine (engine.py) has real breadth to run rules against without
needing every stock to have gone through a full 13-stage analysis.

Same bounded/resumable shape as banking_ingestion.backfill_all_banks and
annual_report_ingestion.ingest_all_banks_annual_reports: process up to
`max_companies_per_run`, skip anything already fresh, stop — meant to be
invoked repeatedly (daily cron, or manually) until the universe is covered.
yfinance has no known daily quota like Groq does, so this can run with a
much larger batch size and a short politeness delay rather than Groq's
1-second-per-call pacing.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.calculations.engine import compute_metrics
from app.data.yfinance_client import fetch_financial_data
from app.infrastructure.database.models import BulkMetrics, Stock
from app.logger import logger

_STALE_AFTER = timedelta(hours=24)  # matches fetch_financial_data's own Redis cache TTL


def _stocks_needing_refresh(db: Session, limit: int) -> list[Stock]:
    cutoff = datetime.now(timezone.utc) - _STALE_AFTER
    fresh_stock_ids = {
        row.stock_id for row in
        db.query(BulkMetrics.stock_id).filter(BulkMetrics.computed_at >= cutoff).all()
    }
    candidates = (
        db.query(Stock)
        .filter(Stock.is_active == True)
        .order_by(Stock.symbol)
        .all()
    )
    return [s for s in candidates if s.id not in fresh_stock_ids][:limit]


def refresh_one(db: Session, stock: Stock) -> bool:
    """Compute and upsert one stock's bulk metrics. Returns True on success.
    Never raises — logs and returns False, matching every other ingestion
    path's graceful-degradation contract, since one bad symbol (delisted,
    yfinance mismatch) shouldn't abort the whole batch."""
    try:
        financial_data = fetch_financial_data(stock.exchange, stock.symbol)
        if financial_data.get("error") and not any(
            financial_data.get(k) for k in ["income", "balance", "cash_flow"]
        ):
            logger.info("bulk_metrics: no usable financial data", symbol=stock.symbol,
                        error=financial_data.get("error"))
            return False
        metrics = compute_metrics(financial_data)
    except Exception as e:
        logger.warning("bulk_metrics: compute failed", symbol=stock.symbol, error=str(e))
        return False

    existing = db.query(BulkMetrics).filter_by(stock_id=stock.id).first()
    now = datetime.now(timezone.utc)
    if existing:
        existing.metrics = metrics
        existing.computed_at = now
    else:
        db.add(BulkMetrics(id=str(uuid.uuid4()), stock_id=stock.id, metrics=metrics, computed_at=now))
    return True


def refresh_bulk_metrics(db: Session, max_companies_per_run: int = 50) -> dict:
    """Batch driver — see module docstring. Bounded and resumable, not a
    single unbounded run across ~884 stocks."""
    processed, failed = [], []
    for stock in _stocks_needing_refresh(db, max_companies_per_run):
        try:
            ok = refresh_one(db, stock)
            db.commit()
            (processed if ok else failed).append(stock.symbol)
        except Exception as e:
            db.rollback()
            logger.warning("refresh_bulk_metrics: company failed", symbol=stock.symbol, error=str(e))
            failed.append(stock.symbol)
        time.sleep(0.2)  # light politeness delay, not a hard rate limit like Groq's

    logger.info("refresh_bulk_metrics: run complete", processed=len(processed), failed=len(failed))
    return {"processed": processed, "failed": failed}
