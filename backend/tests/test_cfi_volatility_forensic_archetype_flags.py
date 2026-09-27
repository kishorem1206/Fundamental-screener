"""Tests for `cash_flow_intelligence.volatility`/`forensic_patterns`/
`archetype`/`red_flags` (Cash Flow Analysis Engine, Milestone 4).
"""
from __future__ import annotations

import pytest

from app.calculations.cash_flow_intelligence import archetype, forensic_patterns, red_flags, volatility

# ── volatility.py ────────────────────────────────────────────────────────────

def test_smooth_growth_classified_stable_not_volatile():
    """Regression test for a real issue found live: a company whose CFO
    grows steadily (every period positive and higher, on a clean
    compounding curve) has a high coefficient of variation purely from
    the growth trend — classifying that as VOLATILE_CFO would misrepresent
    a strong grower as erratic."""
    series = {f"FY{20+i}": 100.0 * (1.3 ** i) for i in range(8)}
    result = volatility.classify_cfo_volatility(series)
    assert result["classification"] == "STABLE_CFO"


def test_genuinely_choppy_series_classified_volatile():
    """Maruti's real 12Y CFO history — two sharp single-year drops (COVID,
    a commodity-cost-driven margin hit) mixed with growth periods — is a
    real, correctly-volatile pattern, not a growth-trend artifact."""
    series = {
        "FY15": 6449.0, "FY16": 8482.0, "FY17": 10282.0, "FY18": 11788.0,
        "FY19": 6601.0, "FY20": 3496.0, "FY21": 8856.0, "FY22": 1840.0,
        "FY23": 10815.0, "FY24": 16801.0, "FY25": 16180.0, "FY26": 19100.0,
    }
    result = volatility.classify_cfo_volatility(series)
    assert result["classification"] == "VOLATILE_CFO"


def test_negative_cfo_pattern():
    series = {"FY23": -10.0, "FY24": -5.0, "FY25": 3.0, "FY26": 8.0}
    result = volatility.classify_cfo_volatility(series)
    assert result["classification"] == "NEGATIVE_CFO_PATTERN"


def test_declining_cfo():
    series = {"FY23": 100.0, "FY24": 80.0, "FY25": 60.0, "FY26": 40.0}
    result = volatility.classify_cfo_volatility(series)
    assert result["classification"] == "DECLINING_CFO"


def test_insufficient_data():
    result = volatility.classify_cfo_volatility({"FY26": 10.0})
    assert result["classification"] == "INSUFFICIENT_DATA"


# ── forensic_patterns.py ─────────────────────────────────────────────────────

def test_pattern_a_profit_without_cash_triggers():
    result = forensic_patterns.pattern_a_profit_without_cash(15.0, -10.0, True)
    assert result["status"] == "TRIGGERED"


def test_pattern_a_not_triggered_when_cfo_also_grows():
    result = forensic_patterns.pattern_a_profit_without_cash(15.0, 10.0, False)
    assert result["status"] == "NOT_TRIGGERED"


def test_pattern_d_payable_supported_is_observation_not_flag():
    """Explicitly NOT a TRIGGERED/NOT_TRIGGERED flag — the spec calls this
    an analytical observation, not automatically a red flag."""
    result = forensic_patterns.pattern_d_supplier_financed_cfo(20.0, 15.0)
    assert result["status"] == "OBSERVED"
    assert "TRIGGERED" not in result["status"]


def test_pattern_e_capex_funding_gap():
    result = forensic_patterns.pattern_e_capex_funding_gap(cfo=50.0, capex_abs=100.0, borrowings_raised=40.0, equity_raised=None)
    assert result["status"] == "TRIGGERED"
    assert result["pattern_id"] == "CAPEX_FUNDING_DEPENDENCE"


def test_pattern_f_debt_funded_cash_generation():
    result = forensic_patterns.pattern_f_debt_funded_cash_generation(cfo=-20.0, cff=100.0, borrowings_raised=120.0)
    assert result["status"] == "TRIGGERED"


def test_pattern_g_asset_liquidation_support():
    result = forensic_patterns.pattern_g_asset_liquidation_support(cfo=-10.0, cfi=50.0, fixed_assets_sold=20.0, investments_sold=30.0)
    assert result["status"] == "TRIGGERED"


def test_evaluate_all_patterns_returns_seven():
    results = forensic_patterns.evaluate_all_patterns({})
    assert len(results) == 7
    ids = {r["pattern_id"] for r in results}
    assert len(ids) == 7


# ── archetype.py ─────────────────────────────────────────────────────────────

def test_cash_compounder():
    result = archetype.classify_cash_flow_archetype(
        cfo_volatility_classification="STABLE_CFO", fcf_quality_classification="CONSISTENT_POSITIVE_FCF",
        latest_conversion_pct=80.0, capex_to_cfo_pct=30.0, debt_classification="NEUTRAL",
        asset_liquidation_triggered=False, dividends_or_buybacks_present=False,
    )
    assert result["classification"] == "CASH_COMPOUNDER"


def test_working_capital_trap():
    result = archetype.classify_cash_flow_archetype(
        cfo_volatility_classification="VOLATILE_CFO", fcf_quality_classification="VOLATILE_FCF",
        latest_conversion_pct=30.0, capex_to_cfo_pct=20.0, debt_classification="NEUTRAL",
        asset_liquidation_triggered=False, dividends_or_buybacks_present=False,
    )
    assert result["classification"] == "WORKING_CAPITAL_TRAP"


def test_debt_funded_business():
    result = archetype.classify_cash_flow_archetype(
        cfo_volatility_classification="NEGATIVE_CFO_PATTERN", fcf_quality_classification="PERSISTENT_NEGATIVE_FCF",
        latest_conversion_pct=None, capex_to_cfo_pct=None, debt_classification="NET_BORROWING",
        asset_liquidation_triggered=False, dividends_or_buybacks_present=False,
    )
    assert result["classification"] == "DEBT_FUNDED_BUSINESS"


def test_asset_liquidation_supported_takes_priority():
    result = archetype.classify_cash_flow_archetype(
        cfo_volatility_classification="NEGATIVE_CFO_PATTERN", fcf_quality_classification="VOLATILE_FCF",
        latest_conversion_pct=None, capex_to_cfo_pct=None, debt_classification="NET_BORROWING",
        asset_liquidation_triggered=True, dividends_or_buybacks_present=False,
    )
    assert result["classification"] == "ASSET_LIQUIDATION_SUPPORTED"


def test_mixed_fallback():
    result = archetype.classify_cash_flow_archetype(
        cfo_volatility_classification=None, fcf_quality_classification=None,
        latest_conversion_pct=None, capex_to_cfo_pct=None, debt_classification=None,
        asset_liquidation_triggered=False, dividends_or_buybacks_present=False,
    )
    assert result["classification"] == "MIXED"


# ── red_flags.py ─────────────────────────────────────────────────────────────

def test_low_cfo_conversion_watch_for_one_year():
    flag = red_flags.rule_1_low_cfo_conversion(current_ratio_pct=30.0, prior_ratio_pct=80.0, period="FY26")
    assert flag["status"] == "TRIGGERED"
    assert flag["severity"] == "WATCH"
    assert flag["persistence"] == 1


def test_low_cfo_conversion_red_flag_for_two_consecutive_years():
    flag = red_flags.rule_1_low_cfo_conversion(current_ratio_pct=30.0, prior_ratio_pct=35.0, period="FY26")
    assert flag["severity"] == "RED"
    assert flag["persistence"] == 2


def test_unallocated_capital_drag_low_confidence_when_triggered():
    flag = red_flags.rule_2_unallocated_capital_drag(other_investing=-30.0, annual_cfo=100.0, period="FY26")
    assert flag["status"] == "TRIGGERED"
    assert flag["confidence"] == "LOW"


def test_evaluate_all_flags_returns_five():
    flags = red_flags.evaluate_all_flags({})
    assert len(flags) == 5
    ids = {f["flag_id"] for f in flags}
    assert len(ids) == 5
