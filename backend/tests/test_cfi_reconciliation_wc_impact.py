"""Tests for `cash_flow_intelligence.reconciliation`/`working_capital_impact`/
`snapshot` (Cash Flow Analysis Engine, Milestone 2). Uses Maruti Suzuki as
the real-data fixture, matching this suite's established convention.
"""
from __future__ import annotations

import pytest

from app.calculations.cash_flow_intelligence import (
    reconciliation,
    snapshot,
    working_capital_impact,
)
from app.infrastructure.database.models import Stock

_FIXTURE_SYMBOL = "MARUTI"


def _fixture_company_id(db, symbol: str) -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


# ── snapshot.py ──────────────────────────────────────────────────────────────

def test_build_cfo_schedule_series_rejects_missing_statement_type(db):
    with pytest.raises(TypeError):
        snapshot.build_cfo_schedule_series(db, "any-company")  # type: ignore[call-arg]


def test_build_top_level_series_uses_cf_prefix(db):
    """Regression test for a real bug found live: `TOP_LEVEL_FIELDS` stores
    bare field names ("operating_cash_flow"), but the ledger key
    `ingest_cash_flow()` actually writes is `cf_operating_cash_flow` — the
    lookup must add the prefix back, or every top-level series reads empty."""
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    top_level = snapshot.build_top_level_series(db, company_id, statement_type="CONSOLIDATED")
    assert top_level["cfo"], "expected non-empty CFO series — the cf_ prefix bug would make this {}"


def test_real_company_cfo_schedule_has_data(db):
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    series = snapshot.build_cfo_schedule_series(db, company_id, statement_type="CONSOLIDATED")
    assert series["operating_profit"]
    assert series["receivables_change"]


# ── reconciliation.py ────────────────────────────────────────────────────────

def test_cfo_bridge_arithmetic():
    period = {
        "operating_profit": 135.0, "receivables_change": -40.0, "inventory_change": -22.0,
        "payables_change": 17.0, "loans_advances_change": None, "other_wc_change": -4.0,
        "working_capital_change": -49.0, "taxes_paid": -30.0, "exceptional_items": None,
    }
    bridge = reconciliation.cfo_bridge(period)
    assert bridge["computed_cfo"] == pytest.approx(56.0)  # 135 + (-49) + (-30)


def test_cfo_bridge_real_maruti_data_matches_reported(db):
    """The whole point of this engine's reconciliation layer — the bridge
    computed from real ingested schedule line items must match Screener's
    own directly-reported CFO total, not just look plausible."""
    company_id = _fixture_company_id(db, _FIXTURE_SYMBOL)
    cfo_series = snapshot.build_cfo_schedule_series(db, company_id, statement_type="CONSOLIDATED")
    top_level = snapshot.build_top_level_series(db, company_id, statement_type="CONSOLIDATED")
    period = snapshot.latest_period(cfo_series)
    p = snapshot.period_snapshot(cfo_series, period)
    bridge = reconciliation.cfo_bridge(p)
    reported_cfo = top_level["cfo"].get(period)
    check = reconciliation.cfo_bridge_check(bridge["computed_cfo"], reported_cfo)
    assert check["status"] == "VALID"
    assert check["difference_pct"] < 1.0


def test_cfo_bridge_check_missing_data():
    check = reconciliation.cfo_bridge_check(None, 100.0)
    assert check["status"] == "MISSING_DATA"


def test_cash_bridge_valid_when_reconciled():
    result = reconciliation.cash_bridge(10.0, 5.0, -3.0, -1.0, 11.0)
    assert result["status"] == "VALID"
    assert result["other_adjustment"] == 0.0


def test_cash_bridge_flags_error_when_mismatched():
    result = reconciliation.cash_bridge(10.0, 5.0, -3.0, -1.0, 50.0)
    assert result["status"] == "CASH_FLOW_RECONCILIATION_ERROR"


def test_cash_bridge_missing_data_when_incomplete():
    result = reconciliation.cash_bridge(None, 5.0, -3.0, -1.0, 11.0)
    assert result["status"] == "MISSING_DATA"
    assert result["other_adjustment"] is None


# ── working_capital_impact.py ─────────────────────────────────────────────────

def test_working_capital_impact_sums_correctly():
    period = {"receivables_change": -40.0, "inventory_change": -22.0, "payables_change": 17.0, "other_wc_change": -4.0}
    result = working_capital_impact.working_capital_impact(period)
    assert result["net_wc_impact"] == pytest.approx(-49.0)


def test_receivables_cash_drag_triggers():
    result = working_capital_impact.receivables_cash_drag(50.0, 10.0)
    assert result["triggered"] is True
    assert result["flag_id"] == "RECEIVABLE_CASH_DRAG"


def test_receivables_cash_drag_persistent_flag():
    result = working_capital_impact.receivables_cash_drag(50.0, 10.0, persisted_periods=2)
    assert result["flag_id"] == "PERSISTENT_RECEIVABLE_CASH_DRAG"


def test_receivables_cash_drag_not_triggered():
    result = working_capital_impact.receivables_cash_drag(5.0, 10.0)
    assert result["triggered"] is False


def test_inventory_cash_drag_triggers():
    result = working_capital_impact.inventory_cash_drag(40.0, 10.0)
    assert result["triggered"] is True


def test_payables_cash_support_never_auto_positive():
    result = working_capital_impact.payables_cash_support(50.0)
    assert result["interpretation"] == "cash_retained_via_supplier_financing"
    # the function itself never labels this "good" or "bad" — no severity/tone key at all
    assert "severity" not in result
