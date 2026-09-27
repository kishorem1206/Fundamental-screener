"""Tests for `screener_client.ingest_company_summary()`'s new `sr_*`
summary-ratios ingestion (Screener.in as Primary Source of Truth, Milestone
1). Uses Maruti Suzuki (NSE:MARUTI) as the real-data fixture — re-ingested
live during this milestone's implementation, matching this suite's
established convention of testing against real ledger rows rather than
mocking network calls (see `test_cash_flow_schedules_ingestion.py`).
"""
from __future__ import annotations

from app.infrastructure.database.models import MetricDataPoint, Stock

_FIXTURE_SYMBOL = "MARUTI"


def _fixture_company_id(db, symbol: str) -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


def test_summary_ratios_present_with_correct_provenance(db):
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    for metric_key in ("sr_market_cap", "sr_current_price", "sr_pe_ratio",
                        "sr_book_value", "sr_dividend_yield", "sr_face_value"):
        row = (db.query(MetricDataPoint)
               .filter_by(company_id=company_id, metric_key=metric_key, statement_type="CONSOLIDATED")
               .order_by(MetricDataPoint.retrieved_at.desc()).first())
        assert row is not None, f"expected {metric_key} for the fixture company"
        assert row.source == "SCREENER" and row.source_tier == 2
        assert row.confidence == "MEDIUM"


def test_summary_ratios_values_are_plausible(db):
    """Real regression guard: dividend_yield must already be a plain
    percentage (e.g. 1.13, not 0.0113) — the same plausibility class of bug
    documented in engine.py's own 2026-09-15 yfinance dividend-yield fix."""
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    pe_row = (db.query(MetricDataPoint)
              .filter_by(company_id=company_id, metric_key="sr_pe_ratio", statement_type="CONSOLIDATED")
              .order_by(MetricDataPoint.retrieved_at.desc()).first())
    div_row = (db.query(MetricDataPoint)
               .filter_by(company_id=company_id, metric_key="sr_dividend_yield", statement_type="CONSOLIDATED")
               .order_by(MetricDataPoint.retrieved_at.desc()).first())
    market_cap_row = (db.query(MetricDataPoint)
                      .filter_by(company_id=company_id, metric_key="sr_market_cap", statement_type="CONSOLIDATED")
                      .order_by(MetricDataPoint.retrieved_at.desc()).first())
    assert 5.0 < float(pe_row.value) < 200.0
    assert 0.0 <= float(div_row.value) < 20.0
    assert float(market_cap_row.value) > 1000.0  # Crores — a real large-cap, not a raw-Rupee figure


def test_summary_ratios_units_correct(db):
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    expected_units = {
        "sr_market_cap": "cr", "sr_current_price": "INR", "sr_pe_ratio": "x",
        "sr_book_value": "INR", "sr_dividend_yield": "%", "sr_face_value": "INR",
    }
    for metric_key, unit in expected_units.items():
        row = (db.query(MetricDataPoint)
               .filter_by(company_id=company_id, metric_key=metric_key, statement_type="CONSOLIDATED")
               .order_by(MetricDataPoint.retrieved_at.desc()).first())
        assert row.unit == unit, f"{metric_key} expected unit {unit!r}, got {row.unit!r}"
