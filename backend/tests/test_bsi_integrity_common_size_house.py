"""Tests for `balance_sheet_intelligence.integrity`/`common_size`/
`sources_applications`/`snapshot` (Balance Sheet Analysis Engine,
Milestone 2). Uses Maruti Suzuki and HDFC Bank as real-data fixtures,
matching this suite's established convention.
"""
from __future__ import annotations

import pytest

from app.calculations.balance_sheet_intelligence import common_size, integrity, snapshot, sources_applications
from app.infrastructure.database.models import Stock

_MANUFACTURING_SYMBOL = "MARUTI"
_BANK_SYMBOL = "HDFCBANK"


def _fixture_company_id(db, symbol: str) -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


# ── snapshot.py ──────────────────────────────────────────────────────────────

def test_build_screener_series_rejects_missing_statement_type(db):
    with pytest.raises(TypeError):
        snapshot.build_screener_balance_sheet_series(db, "any-company")  # type: ignore[call-arg]


def test_build_screener_series_rejects_invalid_statement_type(db):
    with pytest.raises(ValueError):
        snapshot.build_screener_balance_sheet_series(db, "any-company", statement_type="BOTH")


def test_bank_borrowings_alias_resolves(db):
    """Confirmed live: HDFC Bank's Screener row uses singular "borrowing",
    every non-bank checked uses "borrowings" — the alias fallback in
    `snapshot._borrowings_series()` must resolve either."""
    company_id = _fixture_company_id(db, _BANK_SYMBOL)
    series = snapshot.build_screener_balance_sheet_series(db, company_id, statement_type="CONSOLIDATED")
    assert series["borrowings"], "expected HDFC Bank's singular 'borrowing' key to resolve via the alias fallback"


def test_bank_has_deposits_manufacturing_company_does_not(db):
    bank_id = _fixture_company_id(db, _BANK_SYMBOL)
    manu_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    bank_series = snapshot.build_screener_balance_sheet_series(db, bank_id, statement_type="CONSOLIDATED")
    manu_series = snapshot.build_screener_balance_sheet_series(db, manu_id, statement_type="CONSOLIDATED")
    assert bank_series.get("deposits"), "expected HDFC Bank to report deposits"
    assert not manu_series.get("deposits"), "a non-financial company should never report deposits"


def test_screener_ratios_history_falls_back_when_requested_type_is_empty(db):
    """Real gap found live on GNFC (2026-09-22): every `bs_ratio_*` row on
    record for it is tagged STANDALONE only, but `compute_balance_sheet_intelligence()`
    resolves an overall CONSOLIDATED label for it (single_statement_source
    relabeling). A strict CONSOLIDATED-only lookup silently returned `{}`,
    showing every working-capital cross-check field as "Not disclosed"
    even though the real numbers were on record under the other tag.
    (2026-09-23: `latest_screener_ratios()` was rewritten and renamed to
    `screener_ratios_history()` — full multi-year history per field, not
    just the latest point — the per-field fallback behavior this test
    covers carried over unchanged.)"""
    # A test-only company holding STANDALONE ratio rows only — the shape GNFC
    # had on 2026-09-22. GNFC itself has since gained consolidated rows from
    # the Screener-first quick run, so it no longer exercises the fallback.
    from datetime import datetime, timezone
    from app.infrastructure.database import metric_store

    now = datetime.now(timezone.utc)
    company_id = "TEST:RATIOSONLYSA"
    db.add(Stock(id=company_id, symbol="RATIOSONLYSA", exchange="TEST", company_name="x", is_active=False,
                 created_at=now, updated_at=now))
    db.flush()
    for period, days in (("2025-03-31", 61.0), ("2026-03-31", 58.0)):
        metric_store.insert_metric_value(db, company_id=company_id, metric_key="bs_ratio_debtor_days", period=period,
                                         value=days, unit="days", source="SCREENER", source_tier=2, confidence="MEDIUM",
                                         statement_type="STANDALONE", reported_or_calculated="REPORTED")
    consolidated = snapshot.screener_ratios_history(db, company_id, "CONSOLIDATED")
    assert consolidated, "expected the STANDALONE-tagged bs_ratio_* rows to be found via fallback"
    assert consolidated == snapshot.screener_ratios_history(db, company_id, "STANDALONE")


# ── integrity.py ─────────────────────────────────────────────────────────────

def test_integrity_valid_when_balanced():
    result = integrity.validate_accounting_identity(1000.0, 1000.0)
    assert result["status"] == "VALID"
    assert result["difference"] == 0.0


def test_integrity_valid_within_tolerance():
    result = integrity.validate_accounting_identity(1000.0, 1004.0, tolerance_pct=0.5)
    assert result["status"] == "VALID"


def test_integrity_error_when_materially_unbalanced():
    result = integrity.validate_accounting_identity(1000.0, 800.0)
    assert result["status"] == "BALANCE_SHEET_INTEGRITY_ERROR"
    assert result["difference"] == 200.0


def test_integrity_missing_data_not_confused_with_error():
    result = integrity.validate_accounting_identity(None, 1000.0)
    assert result["status"] == "MISSING_DATA"
    assert result["difference"] is None


def test_real_company_balances(db):
    """Screener's own total_liabilities row is confirmed to equal
    total_assets by construction for a well-formed scrape — a real
    regression here would mean a parse error, not a genuine unbalanced
    filing."""
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    series = snapshot.build_screener_balance_sheet_series(db, company_id, statement_type="CONSOLIDATED")
    period = snapshot.latest_period(series)
    assert period is not None
    p = snapshot.period_snapshot(series, period)
    result = integrity.validate_accounting_identity(p["total_assets"], p["total_liabilities"])
    assert result["status"] == "VALID"


# ── common_size.py ───────────────────────────────────────────────────────────

def test_common_size_asset_side_sums_near_100():
    period = {
        "total_assets": 1000.0, "fixed_assets": 400.0, "capital_work_in_progress": 100.0,
        "investments": 200.0, "other_assets": 300.0,
    }
    result = common_size.compute_common_size(period)
    asset_pct = result["fixed_assets"] + result["capital_work_in_progress"] + result["investments"] + result["other_assets"]
    assert asset_pct == pytest.approx(100.0, abs=0.1)


def test_common_size_empty_when_total_assets_missing():
    assert common_size.compute_common_size({"fixed_assets": 100.0}) == {}


def test_common_size_omits_absent_fields_not_zeros():
    period = {"total_assets": 1000.0, "fixed_assets": 400.0}
    result = common_size.compute_common_size(period)
    assert "deposits" not in result
    assert "investments" not in result


# ── sources_applications.py ──────────────────────────────────────────────────

def test_house_sources_equal_applications_without_cash_crossover():
    period = {
        "equity_capital": 100.0, "reserves": 400.0, "borrowings": 50.0,
        "other_liabilities": 450.0, "fixed_assets": 500.0,
        "capital_work_in_progress": 100.0, "investments": 200.0, "other_assets": 200.0,
    }
    house = sources_applications.compute_house(period, cash_value=None)
    assert house["sources_total"] == pytest.approx(house["applications_total"])
    assert house["cash_source"] == "UNAVAILABLE_FOR_PERIOD"


def test_house_pulls_out_cash_row_when_provided():
    period = {
        "equity_capital": 100.0, "reserves": 400.0, "borrowings": 50.0,
        "other_liabilities": 450.0, "fixed_assets": 500.0,
        "capital_work_in_progress": 100.0, "investments": 200.0, "other_assets": 200.0,
    }
    house = sources_applications.compute_house(period, cash_value=50.0)
    labels = [a["label"] for a in house["applications"]]
    assert "Cash" in labels
    cash_row = next(a for a in house["applications"] if a["label"] == "Cash")
    assert cash_row["value"] == 50.0
    assert cash_row["source"] == "YFINANCE"
    assert house["sources_total"] == pytest.approx(house["applications_total"])


def test_house_deposits_row_only_for_banks(db):
    bank_id = _fixture_company_id(db, _BANK_SYMBOL)
    series = snapshot.build_screener_balance_sheet_series(db, bank_id, statement_type="CONSOLIDATED")
    period = snapshot.latest_period(series)
    p = snapshot.period_snapshot(series, period)
    house = sources_applications.compute_house(p)
    labels = [s["label"] for s in house["sources"]]
    assert "Deposits" in labels
