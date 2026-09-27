"""Tests for `screener_client.ingest_cash_flow_schedules()` (Cash Flow
Analysis Engine, Milestone 1). Uses Maruti Suzuki (NSE:MARUTI) as the
real-data fixture — re-ingested live during this milestone's
implementation, matching this suite's established convention of testing
against real ledger rows rather than mocking network calls.
"""
from __future__ import annotations

from app.infrastructure.database.models import MetricDataPoint, Stock
from app.ingestion.screener_client import (
    _extract_screener_company_id,
    _parse_schedule_value,
)

_FIXTURE_SYMBOL = "MARUTI"


def _fixture_company_id(db, symbol: str) -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


def test_parse_schedule_value_handles_comma_formatting():
    assert _parse_schedule_value("1,236") == 1236.0
    assert _parse_schedule_value("-4,244") == -4244.0
    assert _parse_schedule_value("-0") == 0.0


def test_parse_schedule_value_rejects_non_numeric():
    assert _parse_schedule_value("—") is None
    assert _parse_schedule_value("-") is None
    assert _parse_schedule_value({"class": "strong"}) is None
    assert _parse_schedule_value(None) is None


def test_parse_schedule_value_passes_through_numbers():
    assert _parse_schedule_value(42) == 42.0
    assert _parse_schedule_value(-3.5) == -3.5


def test_extract_company_id_from_real_page_markup():
    html = '<div data-company-id="2023" data-warehouse-id="6597252" data-consolidated="true"></div>'
    assert _extract_screener_company_id(html) == "2023"


def test_extract_company_id_missing_returns_none():
    assert _extract_screener_company_id("<div>no id here</div>") is None


def test_cfo_schedule_rows_present_with_real_field_names(db):
    """These field names were confirmed live and must keep landing
    correctly — a regression here silently breaks the whole engine's
    working-capital-impact analysis."""
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    for metric_key in ("cf_sched_op_receivables", "cf_sched_op_inventory", "cf_sched_op_payables",
                       "cf_sched_op_direct_taxes", "cf_sched_op_profit_from_operations"):
        row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key=metric_key, statement_type="CONSOLIDATED").first()
        assert row is not None, f"expected {metric_key} for the fixture company"
        assert row.source == "SCREENER" and row.source_tier == 2
        assert row.unit == "cr"


def test_gross_debt_raised_and_repaid_both_present(db):
    """The whole point of using Screener's schedules over yfinance for
    this engine — gross figures, not just a net issuance number."""
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    raised = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key="cf_sched_fin_proceeds_from_borrowings", statement_type="CONSOLIDATED").first()
    repaid = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key="cf_sched_fin_repayment_of_borrowings", statement_type="CONSOLIDATED").first()
    assert raised is not None
    assert repaid is not None


def test_investing_schedule_fields_present(db):
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    for metric_key in ("cf_sched_inv_fixed_assets_purchased", "cf_sched_inv_fixed_assets_sold",
                       "cf_sched_inv_investments_purchased", "cf_sched_inv_interest_received"):
        row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key=metric_key, statement_type="CONSOLIDATED").first()
        assert row is not None, f"expected {metric_key} for the fixture company"
