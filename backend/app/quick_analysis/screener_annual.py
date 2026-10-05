"""Screener first, Yahoo as fallback — the same order the full analysis uses.

`refresh()` reads a company's two Screener pages once (app/ingestion/
screener_pages.py) and runs the existing Screener ingests over them, writing
the same ledger rows a full analysis writes: about 12 years of annual P&L,
balance sheet, cash flow and ratios, the quarterly results, shareholding and
the top-ratio strip. `apply()` then runs the full analysis's own
`apply_screener_primary_overrides()` on the Yahoo-computed metrics, so a
Screener figure replaces the Yahoo one wherever Screener has it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import MetricDataPoint, Stock
from app.ingestion.pnl_history_client import ingest_pnl_history
from app.ingestion.quarterly_results_client import ingest_quarterly_results
from app.ingestion.screener_client import (
    CONFIDENCE, SOURCE, SOURCE_TIER, _SR_FIELDS, ingest_balance_sheet, ingest_cash_flow, ingest_ratios,
)
from app.ingestion.screener_pages import prefetched, screener_stock
from app.ingestion.screener_shareholding_client import ingest_screener_shareholding
from app.logger import logger

FRESH_DAYS = 7


def _summary_ratios(db: Session, company_id: str, symbol: str) -> int:
    """The top-ratio strip (market cap, P/E, book value, ROCE, ROE …) as
    `sr_*` rows — what screener_client.ingest_company_summary() writes, minus
    its logged-in commentary fetch, which a bulk run must not do."""
    ratios = (screener_stock(symbol, True).summary() or {}).get("ratios") or {}
    now = datetime.now(timezone.utc)
    n = 0
    for field, (key, unit) in _SR_FIELDS.items():
        value = ratios.get(field)
        if isinstance(value, (int, float)):
            metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=key, period=now.date().isoformat(), value=float(value), unit=unit,
                statement_type="CONSOLIDATED", source=SOURCE, source_tier=SOURCE_TIER, reported_or_calculated="REPORTED",
                confidence=CONFIDENCE, source_url=f"https://www.screener.in/company/{symbol}/",
                source_document="Screener.in summary (top ratios)", source_date=now,
            )
            n += 1
    return n


_STEPS = (
    ("annual P&L", ingest_pnl_history), ("balance sheet", ingest_balance_sheet), ("cash flow", ingest_cash_flow),
    ("ratios", ingest_ratios), ("quarterly results", ingest_quarterly_results),
    ("shareholding", ingest_screener_shareholding), ("top ratios", _summary_ratios),
)


def last_read(db: Session, company_id: str) -> datetime | None:
    return (db.query(func.max(MetricDataPoint.retrieved_at))
            .filter(MetricDataPoint.company_id == company_id, MetricDataPoint.metric_key == "pnl_sales",
                    MetricDataPoint.source == SOURCE).scalar())


def refresh(db: Session, stock: Stock, max_age_days: float = FRESH_DAYS) -> dict:
    """Never raises. Skips a company read within `max_age_days`."""
    seen = last_read(db, stock.id)
    if seen and seen > datetime.now(timezone.utc) - timedelta(days=max_age_days):
        return {"skipped": "fresh", "last_read": seen.isoformat()}
    out: dict = {}
    with prefetched(stock.symbol) as pages:
        if all(isinstance(p, Exception) for p in pages.values()):
            return {"error": str(next(iter(pages.values())))}
        for name, step in _STEPS:
            try:
                step(db, company_id=stock.id, symbol=stock.symbol)
                db.commit()
                out[name] = "ok"
            except Exception as exc:  # noqa: BLE001 — one section failing must not lose the others
                db.rollback()
                out[name] = f"failed: {exc}"[:160]
                logger.warning("screener annual refresh step failed", symbol=stock.symbol, step=name, error=str(exc))
    return out


def apply(metrics: dict, db: Session, company_id: str, sector_framework: str) -> dict:
    from app.calculations.screener_metrics_override import apply_screener_primary_overrides

    return apply_screener_primary_overrides(metrics, db, company_id, sector_name=sector_framework)
