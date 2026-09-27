"""Tests for `cash_flow_intelligence.investing`/`financing`/`fcf`/
`conversion` (Cash Flow Analysis Engine, Milestone 3).
"""
from __future__ import annotations

import pytest

from app.calculations.cash_flow_intelligence import conversion, fcf, financing, investing

# ── investing.py ─────────────────────────────────────────────────────────────

def test_asset_sale_dependency_triggers_when_cfi_positive_from_liquidation():
    result = investing.asset_sale_dependency(cfi=50.0, fixed_assets_sold=10.0, investments_sold=40.0)
    assert result["triggered"] is True
    assert result["flag_id"] == "INVESTING_CASH_LIQUIDATION"


def test_asset_sale_dependency_not_triggered_when_cfi_negative():
    """Real case found live on Maruti: large gross investment purchase/sale
    churn (normal treasury management) must not trigger this just because
    the liquidation proceeds are large in absolute terms — CFI itself must
    be positive first."""
    result = investing.asset_sale_dependency(cfi=-14734.0, fixed_assets_sold=52.0, investments_sold=101969.0)
    assert result["triggered"] is False


def test_unallocated_capital_drag_triggers_above_25pct():
    result = investing.unallocated_capital_drag(other_investing=-30.0, annual_cfo=100.0)
    assert result["triggered"] is True
    assert result["confidence"] == "LOW"


def test_unallocated_capital_drag_not_triggered_below_threshold():
    result = investing.unallocated_capital_drag(other_investing=-10.0, annual_cfo=100.0)
    assert result["triggered"] is False


# ── financing.py ─────────────────────────────────────────────────────────────

def test_debt_financing_net_borrowing():
    result = financing.debt_financing_analysis(borrowings_raised=100.0, borrowings_repaid=-20.0)
    assert result["classification"] == "NET_BORROWING"
    assert result["net_debt_cash_flow"] == pytest.approx(80.0)


def test_debt_financing_net_deleveraging():
    result = financing.debt_financing_analysis(borrowings_raised=10.0, borrowings_repaid=-50.0)
    assert result["classification"] == "NET_DELEVERAGING"


def test_debt_financing_neutral_when_both_zero():
    result = financing.debt_financing_analysis(borrowings_raised=0.0, borrowings_repaid=0.0)
    assert result["classification"] == "NEUTRAL"


def test_dividend_analysis_ratios():
    result = financing.dividend_analysis(dividends_paid=-40.0, cfo=200.0, fcf=100.0)
    assert result["dividend_to_cfo_pct"] == pytest.approx(20.0)
    assert result["dividend_to_fcf_pct"] == pytest.approx(40.0)


def test_buyback_analysis_missing_when_zero():
    result = financing.buyback_analysis(share_redemption=0.0, fcf=100.0, cfo=200.0)
    assert result["status"] == "MISSING_INPUT"


def test_buyback_analysis_partial_when_present():
    result = financing.buyback_analysis(share_redemption=-20.0, fcf=100.0, cfo=200.0)
    assert result["status"] == "PARTIAL"
    assert result["confidence"] == "LOW"


# ── fcf.py ───────────────────────────────────────────────────────────────────

def test_compute_fcf_matches_reported_within_tolerance():
    result = fcf.compute_fcf(reported_fcf=8754.0, cfo=19100.0, capex=-10398.0)
    assert result["computed_fcf"] == pytest.approx(8702.0)
    assert result["divergent"] is False


def test_compute_fcf_flags_large_divergence():
    result = fcf.compute_fcf(reported_fcf=100.0, cfo=200.0, capex=-50.0)  # computed=150, way off from reported=100
    assert result["divergent"] is True


def test_classify_fcf_quality_consistent_positive():
    series = {"FY23": 10.0, "FY24": 20.0, "FY25": 15.0, "FY26": 25.0}
    result = fcf.classify_fcf_quality(series)
    assert result["classification"] == "CONSISTENT_POSITIVE_FCF"


def test_classify_fcf_quality_persistent_negative():
    series = {"FY23": -10.0, "FY24": -20.0, "FY25": -5.0}
    result = fcf.classify_fcf_quality(series)
    assert result["classification"] == "PERSISTENT_NEGATIVE_FCF"


def test_classify_fcf_quality_insufficient_data():
    result = fcf.classify_fcf_quality({"FY26": 10.0})
    assert result["classification"] == "INSUFFICIENT_DATA"


# ── conversion.py ────────────────────────────────────────────────────────────

def test_cfo_operating_profit_ratio_bands():
    assert conversion.cfo_operating_profit_ratio(30.0, 100.0)["band"] == "<50%"
    assert conversion.cfo_operating_profit_ratio(70.0, 100.0)["band"] == "50-100%"
    assert conversion.cfo_operating_profit_ratio(105.0, 100.0)["band"] == "~100%"
    assert conversion.cfo_operating_profit_ratio(150.0, 100.0)["band"] == ">100%"


def test_cfo_operating_profit_ratio_real_maruti_value():
    result = conversion.cfo_operating_profit_ratio(19100.0, 21802.0)
    assert result["ratio_pct"] == pytest.approx(87.61, abs=0.1)


def test_cumulative_conversion_never_cagr_just_sums():
    cfo = {"FY24": 100.0, "FY25": 110.0, "FY26": 120.0}
    op = {"FY24": 120.0, "FY25": 130.0, "FY26": 140.0}
    pat = {"FY24": 80.0, "FY25": 85.0, "FY26": 90.0}
    result = conversion.cumulative_conversion(cfo, op, pat, years=3)
    assert result["cumulative_cfo"] == pytest.approx(330.0)
    assert result["cumulative_operating_profit"] == pytest.approx(390.0)


def test_classify_conversion_trend_improving():
    assert conversion.classify_conversion_trend(80.0, 50.0) == "IMPROVING_CASH_CONVERSION"


def test_classify_conversion_trend_deteriorating():
    assert conversion.classify_conversion_trend(40.0, 70.0) == "DETERIORATING_CASH_CONVERSION"


def test_classify_conversion_trend_stable():
    assert conversion.classify_conversion_trend(52.0, 50.0) == "STABLE_CASH_CONVERSION"
