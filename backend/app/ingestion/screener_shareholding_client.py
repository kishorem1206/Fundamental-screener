"""Screener.in shareholding pattern — supplementary promoter/FII/DII/public
holding history alongside Stage 3's NSE-sourced shareholding_client.py.
Never blended with that table (see migration 0016's docstring for why):
Screener has no pledge % field at all, so it can never be authoritative for
governance flags, only useful for its materially deeper trend history (11
years yearly vs NSE's 2022-on window) and the FII/DII split NSE's summary
API doesn't provide.

Uses the same openscreener Playwright-based Stock class as screener_client.py
(sector-agnostic, works for any Screener.in company page). Never raises —
logs and returns an empty result on failure, matching every other ingestion
path's contract.
"""
from __future__ import annotations

import calendar
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import ShareholdingScreener
from app.logger import logger

SOURCE = "SCREENER"


def _fmt_period(date_label: str) -> str | None:
    """"Jul 2026" -> "2026-07-31" (last calendar day of the month), matching
    screener_client.py's own _fmt_period convention for Screener's
    month-label periods."""
    try:
        dt = datetime.strptime(date_label.strip(), "%b %Y")
    except (ValueError, AttributeError):
        return None
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return dt.replace(day=last_day).date().isoformat()


def _to_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _ingest_frequency(db: Session, company_id: str, stock, frequency: str) -> int:
    rows = stock.shareholding(frequency=frequency)
    if not rows:
        return 0

    now = datetime.now(timezone.utc)
    stored = 0
    for row in rows:
        period_end = _fmt_period(row.get("date", ""))
        if period_end is None:
            continue
        promoter_pct = _to_float(row.get("promoters"))
        fii_pct = _to_float(row.get("fiis"))
        dii_pct = _to_float(row.get("diis"))
        public_pct = _to_float(row.get("public"))
        shareholder_count = _to_int(row.get("number_of_shareholders"))

        existing = (
            db.query(ShareholdingScreener)
            .filter_by(company_id=company_id, period_end=period_end, frequency=frequency)
            .first()
        )
        if existing:
            existing.promoter_pct = promoter_pct
            existing.fii_pct = fii_pct
            existing.dii_pct = dii_pct
            existing.public_pct = public_pct
            existing.shareholder_count = shareholder_count
            existing.retrieved_at = now
        else:
            db.add(ShareholdingScreener(
                id=str(uuid.uuid4()), company_id=company_id, period_end=period_end,
                frequency=frequency, promoter_pct=promoter_pct, fii_pct=fii_pct,
                dii_pct=dii_pct, public_pct=public_pct, shareholder_count=shareholder_count,
                retrieved_at=now,
            ))
        stored += 1
    db.flush()
    return stored


def ingest_screener_shareholding(db: Session, company_id: str, symbol: str) -> dict:
    """Fetch and store both quarterly and yearly Screener shareholding
    history for `symbol`. Never raises."""
    try:
        from openscreener import Stock
    except ImportError:
        logger.warning("screener_shareholding_client: openscreener not installed", symbol=symbol)
        return {"quarterly_rows": 0, "yearly_rows": 0}

    try:
        # consolidated=True for consistency with every other ingestion
        # module's default now (2026-09-22 sweep) — verified live on GNFC
        # this makes no actual difference here (shareholding % is a
        # share-register fact about the listed entity, not a financial
        # statement, so Screener returns byte-identical rows either way),
        # but there's no reason to be the one remaining standalone-flagged
        # call in this codebase for a value that doesn't even vary by it.
        stock = Stock(symbol, consolidated=True)
        quarterly_rows = _ingest_frequency(db, company_id, stock, "quarterly")
        yearly_rows = _ingest_frequency(db, company_id, stock, "yearly")
    except Exception as e:
        logger.warning("screener_shareholding_client: fetch failed", symbol=symbol, error=str(e))
        return {"quarterly_rows": 0, "yearly_rows": 0}

    logger.info("screener_shareholding_client: ingested", symbol=symbol,
                quarterly_rows=quarterly_rows, yearly_rows=yearly_rows)
    return {"quarterly_rows": quarterly_rows, "yearly_rows": yearly_rows}
