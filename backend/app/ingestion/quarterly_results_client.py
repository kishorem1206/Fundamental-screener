"""Quarterly Report Extraction Engine — Tier 1. Screener.in's
`quarterly_results()` returns the same per-quarter P&L shape as
`profit_loss()` (confirmed live on PIDILITIND: 13 quarters, both
statement types), keyed `date` ("Mon YYYY") instead of `year`, but is
almost entirely unused today: `screener_client.py::ingest_quarterly_metrics`
only ever reads the SINGLE latest quarter and only persists 2-3 banking
fields (gross_npa/net_npa/cost_to_income_ratio). This module ingests every
quarter, every field, for every company — mirrors
`pnl_history_client.py::ingest_pnl_history()`'s exact architecture.

Critical namespace decision: every metric_key here is `qtr_`-prefixed, NOT
`pnl_`-prefixed. `metric_store.py` has no `period_type` column, so a Q4
quarter-end ISO date (e.g. "2026-03-31") is textually identical to that
year's fiscal-year-end date — reusing the `pnl_` namespace would let a
quarterly Q4 row collide with the annual FY row for the same
company/period/statement_type. `qtr_` is a fully separate metric_key
namespace, the same fix pattern already used for "TTM" vs a real date.

Deliberately does NOT touch `screener_client.py::ingest_quarterly_metrics`
(banking NPA/cost-to-income) — purely additive, same non-interference
precedent `pnl_history_client.py`'s own docstring documents.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.ingestion.pnl_history_client import _fmt_period
from app.ingestion.screener_client import _SCREENER_REQUEST_DELAY_SECONDS
from app.logger import logger

SOURCE = "SCREENER"
SOURCE_TIER = 2
CONFIDENCE = "MEDIUM"

# Screener field name -> (metric_key, unit). Same industrial/banking dual
# vocabulary as pnl_history_client.py's _FIELD_MAP (banks report
# "revenue"/"financing_profit"/"financing_margin" instead of "sales"/
# "operating_profit"/"operating_margin_percent") — mapped to the same
# qtr_ keys so the universal quarterly view renders for every sector.
_FIELD_MAP = {
    "sales": ("qtr_sales", "cr"),
    "revenue": ("qtr_sales", "cr"),
    "expenses": ("qtr_expenses", "cr"),
    "operating_profit": ("qtr_operating_profit", "cr"),
    "financing_profit": ("qtr_operating_profit", "cr"),
    "operating_margin_percent": ("qtr_opm", "%"),
    "financing_margin": ("qtr_opm", "%"),
    "other_income": ("qtr_other_income", "cr"),
    "interest": ("qtr_interest", "cr"),
    "depreciation": ("qtr_depreciation", "cr"),
    "profit_before_tax": ("qtr_pbt", "cr"),
    "tax_percent": ("qtr_tax_pct", "%"),
    "net_profit": ("qtr_net_profit", "cr"),
    "eps": ("qtr_eps", "INR"),
}


def ingest_quarterly_results(db: Session, company_id: str, symbol: str) -> list:
    """Fetch and store ALL of Screener.in's per-quarter P&L rows (not just
    the latest) for `symbol`, both standalone and consolidated. Never
    raises — logs and returns whatever it managed to insert (possibly
    empty) on failure, matching every other ingestion path's contract.

    2026-09-24: `_SCREENER_REQUEST_DELAY_SECONDS` between the two statement-
    type requests — see `screener_client.py`'s module-level comment on that
    constant for the rate-limit incident (Voltas cash-flow schedules) this
    same fix pattern was applied everywhere else for."""
    try:
        from openscreener import Stock  # noqa: F401
        from app.ingestion.screener_pages import screener_stock
    except ImportError:
        logger.warning("quarterly_results_client: openscreener not installed", symbol=symbol)
        return []

    now = datetime.now(timezone.utc)
    source_url = f"https://www.screener.in/company/{symbol}/"
    inserted = []
    quarters_seen = 0

    for pass_index, (statement_type, consolidated) in enumerate((("STANDALONE", False), ("CONSOLIDATED", True))):
        if pass_index > 0:
            time.sleep(_SCREENER_REQUEST_DELAY_SECONDS)
        try:
            stock = screener_stock(symbol, consolidated)
            rows = stock.quarterly_results()
        except Exception as e:
            logger.warning("quarterly_results_client: quarterly_results fetch failed", symbol=symbol,
                            statement_type=statement_type, error=str(e))
            continue

        quarters_seen = max(quarters_seen, len(rows))

        for row in rows:
            date_label = str(row.get("date", ""))
            if date_label.upper() == "TTM":
                continue
            period = _fmt_period(date_label)
            if period is None:
                continue

            for field, (metric_key, unit) in _FIELD_MAP.items():
                value = row.get(field)
                if value is None or not isinstance(value, (int, float)):
                    continue
                result = metric_store.insert_metric_value(
                    db,
                    company_id=company_id,
                    metric_key=metric_key,
                    period=period,
                    value=float(value),
                    unit=unit,
                    statement_type=statement_type,
                    source=SOURCE,
                    source_tier=SOURCE_TIER,
                    reported_or_calculated="REPORTED",
                    confidence=CONFIDENCE,
                    source_url=source_url,
                    source_document=f"Screener.in quarterly results ({statement_type.title()})",
                    source_date=now,
                    raw_reported_value=str(value),
                )
                if result is not None:
                    inserted.append(result)

    logger.info("quarterly_results_client: ingested", symbol=symbol, quarters=quarters_seen,
                rows_inserted=len(inserted))
    return inserted
