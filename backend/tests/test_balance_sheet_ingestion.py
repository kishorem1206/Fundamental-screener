"""Tests for `screener_client.ingest_cash_flow()`/`ingest_ratios()` (Balance
Sheet Analysis Engine, Milestone 1). Uses Maruti Suzuki (NSE:MARUTI) and HDFC
Bank (NSE:HDFCBANK) as real-data fixtures — both already re-ingested live
during this milestone's implementation, matching this test suite's existing
`test_pl_intelligence_cascade.py` convention of testing against real ledger
rows rather than mocking `openscreener.Stock`.
"""
from __future__ import annotations

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import MetricDataPoint, Stock

_MANUFACTURING_SYMBOL = "MARUTI"
_BANK_SYMBOL = "HDFCBANK"


def _fixture_company_id(db, symbol: str) -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


def test_cash_flow_rows_present_for_manufacturing_company(db):
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    rows = (
        db.query(MetricDataPoint)
        .filter_by(company_id=company_id, metric_key="cf_operating_cash_flow", statement_type="CONSOLIDATED")
        .all()
    )
    assert rows, "expected cf_operating_cash_flow rows for the fixture company"
    assert all(r.source == "SCREENER" and r.source_tier == 2 for r in rows)
    assert all(r.unit == "cr" for r in rows)


def test_cash_flow_covers_both_statement_types(db):
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    for statement_type in ("STANDALONE", "CONSOLIDATED"):
        rows = (
            db.query(MetricDataPoint)
            .filter_by(company_id=company_id, metric_key="cf_free_cash_flow", statement_type=statement_type)
            .all()
        )
        assert rows, f"expected cf_free_cash_flow rows for statement_type={statement_type}"


def test_ratios_covers_multiple_fiscal_years(db):
    """Real gap found live on GROWW (2026-09-22, user's own report — "But
    we can take ROCE directly from screener right?"): this used to assert
    exactly ONE row per (metric, statement_type), because `.ratios()`
    silently discarded every year but the latest — not because Screener's
    Ratios section only has one year (it's a real multi-year table,
    confirmed live). `ingest_ratios()` now uses `.ratios_history()` and
    stores every year it returns, same shape as balance_sheet()/
    cash_flow(); a manufacturing fixture with over a decade of listing
    history should show several distinct fiscal-year rows, not one."""
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    rows = (
        db.query(MetricDataPoint)
        .filter_by(company_id=company_id, metric_key="bs_ratio_debtor_days", statement_type="CONSOLIDATED")
        .all()
    )
    distinct_periods = {r.period for r in rows}
    assert len(distinct_periods) > 1, "expected multiple fiscal years of Screener ratios, not just the latest"
    assert all(r.unit == "days" for r in rows)


def test_ratios_manufacturing_company_has_working_capital_fields(db):
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    for field in ("bs_ratio_debtor_days", "bs_ratio_inventory_days", "bs_ratio_days_payable", "bs_ratio_cash_conversion_cycle"):
        row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key=field, statement_type="STANDALONE").first()
        assert row is not None, f"expected {field} for a non-financial-institution fixture company"


def test_ratios_bank_only_has_roe(db):
    """Confirmed live: Screener's ratios() page doesn't compute
    manufacturing-style working-capital ratios for a bank — only
    `roe_percent`. The ingestor must not crash or fabricate the missing
    fields; it should simply never write rows for them."""
    company_id = _fixture_company_id(db, _BANK_SYMBOL)
    roe_row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key="bs_ratio_roe_percent", statement_type="STANDALONE").first()
    assert roe_row is not None
    assert roe_row.unit == "%"
    for field in ("bs_ratio_debtor_days", "bs_ratio_inventory_days", "bs_ratio_days_payable", "bs_ratio_cash_conversion_cycle"):
        row = db.query(MetricDataPoint).filter_by(company_id=company_id, metric_key=field, statement_type="STANDALONE").first()
        assert row is None, f"{field} should never exist for a bank — Screener's ratios() page doesn't compute it"


def test_repeated_ratios_ingestion_still_resolves_via_authoritative_value(db):
    """`fa_metric_data_points` is append-only by design (full audit trail,
    not an upsert store — confirmed by reading `insert_metric_value()`) — a
    company re-ingested across multiple pipeline runs accumulates multiple
    rows for the same (metric, period, statement_type). Re-inserting a
    second `bs_ratio_roce_percent` value must not corrupt what
    `get_authoritative_value()` resolves back out: same source/tier/
    confidence ties break on most-recent `retrieved_at`, so the newer
    insert should win."""
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    metric_store.insert_metric_value(
        db, company_id=company_id, metric_key="bs_ratio_roce_percent", period="2026-03-31",
        value=99.0, unit="%", statement_type="CONSOLIDATED", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    winner, superseded = metric_store.get_authoritative_value(
        db, company_id, "bs_ratio_roce_percent", "2026-03-31", statement_type="CONSOLIDATED",
    )
    assert winner is not None
    assert winner.value == 99.0
    assert len(superseded) >= 1, "the originally-ingested row should still be present in the ledger, just superseded"
