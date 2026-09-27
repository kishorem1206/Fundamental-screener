"""Tests for `balance_sheet_intelligence.archetype`/`red_flags`/
`historical_trends` (Balance Sheet Analysis Engine, Milestone 4).
"""
from __future__ import annotations

import pytest

from app.calculations.balance_sheet_intelligence import archetype, historical_trends, red_flags

# ── historical_trends.py ─────────────────────────────────────────────────────

def test_trends_cagr_and_change_over_window():
    # "3Y" change means "now vs. 3 years ago" -> 4 data points (2023..2026),
    # start = the 2023 value (3 years before the latest 2026 period).
    series = {"2022-03-31": 100.0, "2023-03-31": 110.0, "2024-03-31": 121.0, "2025-03-31": 133.0, "2026-03-31": 146.0}
    trends = historical_trends.compute_trends(series, windows=(3,))
    window = trends["3Y"]
    assert window["absolute_change"] == pytest.approx(146.0 - 110.0, abs=0.01)
    assert window["periods_available"] == 4
    assert window["cagr"] is not None and window["cagr"] > 0


def test_trends_handles_short_series_gracefully():
    series = {"2025-03-31": 100.0, "2026-03-31": 110.0}
    trends = historical_trends.compute_trends(series, windows=(10,))
    assert trends["10Y"]["periods_available"] == 2
    assert trends["10Y"]["absolute_change"] == pytest.approx(10.0)


def test_trends_empty_series_never_raises():
    trends = historical_trends.compute_trends({}, windows=(1, 3))
    assert trends["1Y"]["periods_available"] == 0
    assert trends["1Y"]["absolute_change"] is None


def test_trends_peak_trough():
    series = {"2023-03-31": 50.0, "2024-03-31": 200.0, "2025-03-31": 10.0, "2026-03-31": 100.0}
    trends = historical_trends.compute_trends(series, windows=(5,))
    assert trends["5Y"]["peak"] == 200.0
    assert trends["5Y"]["trough"] == 10.0


def test_trends_mixed_period_formats():
    """Screener ISO-date periods and yfinance FY-labeled periods both sort
    correctly via the shared fiscal-year extraction."""
    series = {"FY2023": 100.0, "2024-03-31": 110.0, "FY2025": 121.0}
    trends = historical_trends.compute_trends(series, windows=(3,))
    assert trends["3Y"]["periods_available"] == 3
    assert trends["3Y"]["absolute_change"] == pytest.approx(21.0)


# ── archetype.py ─────────────────────────────────────────────────────────────

def test_strong_archetype():
    result = archetype.classify_archetype(
        cash_investments_pct_assets=45.0, debt_to_equity=0.1, working_capital_pct_revenue=10.0,
        debt_pct_change_3y=2.0, cash_pct_change_3y=3.0, ccc_pct_change_3y=1.0,
    )
    assert result["classification"] == "STRONG"
    assert result["evidence"]
    assert result["ruleset_version"] == archetype.ARCHETYPE_RULESET_VERSION


def test_weak_archetype_from_high_leverage():
    result = archetype.classify_archetype(
        cash_investments_pct_assets=5.0, debt_to_equity=2.5, working_capital_pct_revenue=10.0,
        debt_pct_change_3y=10.0, cash_pct_change_3y=-5.0, ccc_pct_change_3y=10.0,
    )
    assert result["classification"] == "WEAK"


def test_weak_archetype_from_ballooning_working_capital():
    result = archetype.classify_archetype(
        cash_investments_pct_assets=5.0, debt_to_equity=0.2, working_capital_pct_revenue=40.0,
        debt_pct_change_3y=0.0, cash_pct_change_3y=0.0, ccc_pct_change_3y=0.0,
    )
    assert result["classification"] == "WEAK"


def test_transforming_archetype():
    result = archetype.classify_archetype(
        cash_investments_pct_assets=10.0, debt_to_equity=0.8, working_capital_pct_revenue=15.0,
        debt_pct_change_3y=-30.0, cash_pct_change_3y=50.0, ccc_pct_change_3y=-20.0,
    )
    assert result["classification"] == "TRANSFORMING"


def test_middle_archetype_default():
    result = archetype.classify_archetype(
        cash_investments_pct_assets=15.0, debt_to_equity=0.5, working_capital_pct_revenue=15.0,
        debt_pct_change_3y=1.0, cash_pct_change_3y=1.0, ccc_pct_change_3y=1.0,
    )
    assert result["classification"] == "MIDDLE"


def test_archetype_custom_thresholds_override_defaults():
    result = archetype.classify_archetype(
        cash_investments_pct_assets=20.0, debt_to_equity=0.5, working_capital_pct_revenue=10.0,
        debt_pct_change_3y=0.0, cash_pct_change_3y=0.0, ccc_pct_change_3y=0.0,
        thresholds={"strong_cash_investments_pct_of_assets": 15.0, "strong_max_debt_to_equity": 0.6},
    )
    assert result["classification"] == "STRONG"


# ── red_flags.py ─────────────────────────────────────────────────────────────

def test_all_12_rules_always_present():
    flags = red_flags.evaluate_all_flags({})
    assert len(flags) == 12
    flag_ids = {f["flag_id"] for f in flags}
    assert len(flag_ids) == 12


def test_source_required_rules_never_fire_regardless_of_input():
    """Rules 7/8/12 have no source anywhere — must always return
    SOURCE_REQUIRED even if `facts` somehow contained plausible-looking
    values for them (it never will, since nothing computes them, but the
    rule functions themselves take no such input at all — this test locks
    that architectural guarantee down)."""
    flags = red_flags.evaluate_all_flags({"debt_to_equity": 5.0, "cfo_latest": -100.0})
    source_required_ids = {"RELATED_PARTY_EXPOSURE", "CONTINGENT_LIABILITY_RISK", "MATURITY_LIQUIDITY_RISK"}
    for f in flags:
        if f["flag_id"] in source_required_ids:
            assert f["status"] == "SOURCE_REQUIRED"
            assert f["confidence"] == "UNAVAILABLE"


def test_high_leverage_rule_triggers_above_threshold():
    flags = red_flags.evaluate_all_flags({"debt_to_equity": 0.9})
    high_lev = next(f for f in flags if f["flag_id"] == "HIGH_LEVERAGE")
    assert high_lev["status"] == "TRIGGERED"
    very_high = next(f for f in flags if f["flag_id"] == "HIGH_LEVERAGE_INVESTIGATION")
    assert very_high["status"] == "NOT_TRIGGERED"


def test_very_high_leverage_rule_triggers_above_3x():
    flags = red_flags.evaluate_all_flags({"debt_to_equity": 3.5})
    very_high = next(f for f in flags if f["flag_id"] == "HIGH_LEVERAGE_INVESTIGATION")
    assert very_high["status"] == "TRIGGERED"


def test_cfo_divergence_rule():
    flags = red_flags.evaluate_all_flags({"cumulative_3y_cfo": 40.0, "cumulative_3y_pat": 100.0})
    rule = next(f for f in flags if f["flag_id"] == "LOW_CASH_EARNINGS_CONVERSION")
    assert rule["status"] == "TRIGGERED"
    assert rule["actual"] == 40.0


def test_cfo_divergence_not_triggered_above_threshold():
    flags = red_flags.evaluate_all_flags({"cumulative_3y_cfo": 80.0, "cumulative_3y_pat": 100.0})
    rule = next(f for f in flags if f["flag_id"] == "LOW_CASH_EARNINGS_CONVERSION")
    assert rule["status"] == "NOT_TRIGGERED"


def test_receivables_inventory_spike_rule():
    flags = red_flags.evaluate_all_flags({
        "receivables_growth_pct": 50.0, "inventory_growth_pct": 5.0, "revenue_growth_pct": 10.0,
    })
    rule = next(f for f in flags if f["flag_id"] == "WORKING_CAPITAL_DRAG")
    assert rule["status"] == "TRIGGERED"


def test_equity_dilution_rule():
    flags = red_flags.evaluate_all_flags({"equity_capital_growth_pct": 20.0, "cfo_latest": -50.0})
    rule = next(f for f in flags if f["flag_id"] == "EXTERNAL_FUNDING_DEPENDENCE")
    assert rule["status"] == "TRIGGERED"


def test_equity_dilution_not_triggered_with_strong_cfo():
    flags = red_flags.evaluate_all_flags({"equity_capital_growth_pct": 20.0, "cfo_latest": 500.0})
    rule = next(f for f in flags if f["flag_id"] == "EXTERNAL_FUNDING_DEPENDENCE")
    assert rule["status"] == "NOT_TRIGGERED"


def test_capex_without_cash_generation_rule_is_low_confidence():
    """Substitutes net fixed-assets growth for the spec's literal gross
    block growth — must always be tagged LOW confidence, documenting the
    deviation, per canonical_fields.NO_GROSS_PPE_REASON."""
    flags = red_flags.evaluate_all_flags({"fixed_assets_growth_pct": 80.0, "cfo_latest": -10.0})
    rule = next(f for f in flags if f["flag_id"] == "UNPRODUCTIVE_CAPEX_INVESTIGATION")
    assert rule["status"] == "TRIGGERED"
    assert rule["confidence"] == "LOW"


def test_working_capital_stress_needs_all_four_signals():
    flags = red_flags.evaluate_all_flags({
        "dso_pct_change": 10.0, "inventory_days_pct_change": 10.0, "ccc_pct_change": 10.0, "cfo_pct_change": -10.0,
    })
    rule = next(f for f in flags if f["flag_id"] == "WORKING_CAPITAL_STRESS")
    assert rule["status"] == "TRIGGERED"


def test_working_capital_stress_not_triggered_with_mixed_signals():
    flags = red_flags.evaluate_all_flags({
        "dso_pct_change": 10.0, "inventory_days_pct_change": -10.0, "ccc_pct_change": 10.0, "cfo_pct_change": -10.0,
    })
    rule = next(f for f in flags if f["flag_id"] == "WORKING_CAPITAL_STRESS")
    assert rule["status"] == "NOT_TRIGGERED"


def test_liquidity_pressure_rule():
    flags = red_flags.evaluate_all_flags({
        "cash_pct_change": -20.0, "current_liabilities_pct_change": 15.0, "borrowings_pct_change": 10.0,
    })
    rule = next(f for f in flags if f["flag_id"] == "LIQUIDITY_PRESSURE")
    assert rule["status"] == "TRIGGERED"


def test_accounting_imbalance_rule():
    flags = red_flags.evaluate_all_flags({"integrity_status": "BALANCE_SHEET_INTEGRITY_ERROR"})
    rule = next(f for f in flags if f["flag_id"] == "ACCOUNTING_IMBALANCE")
    assert rule["status"] == "TRIGGERED"

    flags_ok = red_flags.evaluate_all_flags({"integrity_status": "VALID"})
    rule_ok = next(f for f in flags_ok if f["flag_id"] == "ACCOUNTING_IMBALANCE")
    assert rule_ok["status"] == "NOT_TRIGGERED"
