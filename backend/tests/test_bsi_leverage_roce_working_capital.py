"""Tests for `balance_sheet_intelligence.leverage`/`roce`/`working_capital`
and `snapshot`'s cross-source fiscal-year bridge (Balance Sheet Analysis
Engine, Milestone 3).
"""
from __future__ import annotations

import pytest

from app.calculations.balance_sheet_intelligence import leverage, roce, snapshot, working_capital

# ── snapshot.py: fiscal-year bridge + unit conversion ───────────────────────

def test_fiscal_year_extracts_from_iso_date():
    assert snapshot.fiscal_year("2026-03-31") == "2026"


def test_fiscal_year_extracts_from_fy_label():
    assert snapshot.fiscal_year("FY2026") == "2026"


def test_value_at_fiscal_year_bridges_formats():
    yfinance_series = {"FY2024": 100.0, "FY2025": 200.0, "FY2026": 300.0}
    assert snapshot.value_at_fiscal_year(yfinance_series, "2026-03-31") == 300.0
    assert snapshot.value_at_fiscal_year(yfinance_series, "2025-03-31") == 200.0


def test_value_at_fiscal_year_missing_year_returns_none():
    assert snapshot.value_at_fiscal_year({"FY2024": 100.0}, "2026-03-31") is None


def test_yfinance_value_in_crores_converts_units():
    """Regression test for a real bug found live: yfinance's raw balance
    figures are in Rupees, Screener's are in Crores. Mixing them without
    dividing by 1e7 produced a Capital Employed of -364 BILLION and a
    garbage negative ROCE the first time this was tested end to end."""
    yfinance_series = {"FY2026": 364_802_000_000.0}  # raw Rupees, confirmed live for Maruti's current_liabilities
    result = snapshot.yfinance_value_in_crores(yfinance_series, "2026-03-31")
    assert result == pytest.approx(36480.2)


def test_yfinance_value_in_crores_missing_returns_none():
    assert snapshot.yfinance_value_in_crores({}, "2026-03-31") is None


# ── leverage.py ──────────────────────────────────────────────────────────────

def test_debt_to_equity_and_liabilities_to_equity_are_different_numbers():
    """Spec's explicit instruction: these must never be aliased."""
    result = leverage.compute_leverage(
        equity_capital=100.0, reserves=400.0, borrowings=150.0,
        total_liabilities=1000.0, total_assets=1000.0, cash_value=50.0, ebitda=200.0,
    )
    assert result["debt_to_equity"] == pytest.approx(150.0 / 500.0)
    # total_liabilities(1000) includes equity(500) -> external liabilities = 500
    assert result["liabilities_to_equity"] == pytest.approx(500.0 / 500.0)
    assert result["debt_to_equity"] != result["liabilities_to_equity"]


def test_net_cash_position_flagged_when_negative():
    result = leverage.compute_leverage(
        equity_capital=100.0, reserves=400.0, borrowings=50.0,
        total_liabilities=1000.0, total_assets=1000.0, cash_value=200.0, ebitda=100.0,
    )
    assert result["net_debt"] == pytest.approx(-150.0)
    assert result["net_cash_position"] is True


def test_leverage_handles_missing_cash_gracefully():
    result = leverage.compute_leverage(
        equity_capital=100.0, reserves=400.0, borrowings=50.0,
        total_liabilities=1000.0, total_assets=1000.0, cash_value=None, ebitda=100.0,
    )
    assert result["net_debt"] == 50.0
    assert result["net_debt_source"] == "BORROWINGS_ONLY_NO_CASH_FOR_PERIOD"


def test_leverage_none_when_no_equity():
    result = leverage.compute_leverage(
        equity_capital=None, reserves=None, borrowings=50.0,
        total_liabilities=1000.0, total_assets=1000.0, cash_value=None, ebitda=100.0,
    )
    assert result["debt_to_equity"] is None
    assert result["total_equity"] is None


# ── roce.py ──────────────────────────────────────────────────────────────────

def test_roce_capital_employed_and_dupont_identity():
    result = roce.compute_roce(total_assets=1000.0, current_liabilities=200.0, ebit=120.0, revenue=800.0)
    assert result["capital_employed"] == 800.0
    assert result["roce"] == pytest.approx(15.0)
    assert result["ebit_margin"] == pytest.approx(15.0)
    assert result["capital_employed_turnover"] == pytest.approx(1.0)
    # DuPont identity: ebit_margin * capital_employed_turnover == roce
    assert result["ebit_margin"] * result["capital_employed_turnover"] == pytest.approx(result["roce"])


def test_roce_unavailable_when_current_liabilities_missing():
    result = roce.compute_roce(total_assets=1000.0, current_liabilities=None, ebit=120.0, revenue=800.0)
    assert result["capital_employed"] is None
    assert result["roce"] is None
    assert result["capital_employed_source"] == "UNAVAILABLE"


@pytest.mark.parametrize("margin_delta,turnover_delta,expected", [
    (10.0, 0.5, "MARGIN_DRIVEN"),
    (0.5, 10.0, "TURNOVER_DRIVEN"),
    (10.0, 10.0, "BOTH"),
    (-10.0, 0.5, "MIXED"),
    (None, None, "MIXED"),
])
def test_classify_roce_driver(margin_delta, turnover_delta, expected):
    assert roce.classify_roce_driver(margin_delta, turnover_delta) == expected


def test_roce_cross_check_flags_divergence():
    result = roce.roce_cross_check(13.16, 17.22, 19.0)
    assert result["max_divergence_pct"] > 0
    assert result["screener_methodology_roce"] == 13.16


# ── working_capital.py ────────────────────────────────────────────────────────
# `screener_ratios` fixtures below are `snapshot.screener_ratios_history()`'s
# shape: {canonical_field: {period: value}} — full multi-year history, not a
# single latest-period dict (that was the 2026-09-23 bug: Screener's own
# Ratios tab has years of history, confirmed by the user's own screenshot,
# but this module used to only ever read the latest point).

def test_working_capital_blend_screener_overrides_every_year_it_covers():
    """Screener is the PRIMARY source (2026-09-23 directive, corrected same
    day after an initial latest-period-only version): it overrides EVERY
    fiscal year it has a value for, not just the latest one, even where
    yfinance also has a (now-superseded) number for that same year."""
    metrics = {
        "receivable_days_series": {"FY2025": 10.0, "FY2026": 11.0},
        "inventory_days_series": {"FY2025": 20.0, "FY2026": 23.3},
        "payable_days_series": {"FY2025": 55.0, "FY2026": 59.3},
        "ccc_series": {"FY2025": -25.0, "FY2026": -25.0},
        "curr_ratio_series": {"FY2026": 1.1},
        "quick_ratio_series": {"FY2026": 0.5},
        "cash_ratio_series": {"FY2026": 0.01},
    }
    screener_ratios = {
        "debtor_days": {"2025-03-31": 12.0, "2026-03-31": 11.0},
        "inventory_days": {"2025-03-31": 21.0, "2026-03-31": 31.0},
        "days_payable": {"2025-03-31": 56.0, "2026-03-31": 61.0},
        "cash_conversion_cycle": {"2025-03-31": -24.0, "2026-03-31": -19.0},
    }
    result = working_capital.compute_working_capital_blend(metrics, screener_ratios)
    # Screener's values win at BOTH years, landing on yfinance's own
    # "FY2025"/"FY2026" keys (matched by fiscal year), not new ISO keys.
    assert result["dso_series"] == {"FY2025": 12.0, "FY2026": 11.0}
    assert result["dio_series"] == {"FY2025": 21.0, "FY2026": 31.0}
    assert result["dpo_series"] == {"FY2025": 56.0, "FY2026": 61.0}
    assert result["ccc_series"] == {"FY2025": -24.0, "FY2026": -19.0}
    assert result["methodology"] == "CLOSING_BALANCE_OVER_TOTAL_REVENUE"
    assert result["latest_period"] == "FY2026"
    assert result["single_period_fallback"] == {"dso": True, "dio": True, "dpo": True, "ccc": True}


def test_working_capital_blend_cross_check_divergence():
    metrics = {
        "receivable_days_series": {"FY2026": 11.0},
        "inventory_days_series": {"FY2026": 23.3},
        "payable_days_series": {"FY2026": 59.3},
        "ccc_series": {"FY2026": -25.0},
    }
    screener_ratios = {
        "debtor_days": {"2026-03-31": 11.0}, "inventory_days": {"2026-03-31": 31.0},
        "days_payable": {"2026-03-31": 61.0}, "cash_conversion_cycle": {"2026-03-31": -19.0},
    }
    result = working_capital.compute_working_capital_blend(metrics, screener_ratios)
    assert result["latest_cross_check"]["dso"]["divergence_pct"] == 0.0
    assert result["latest_cross_check"]["dio"]["divergence_pct"] == pytest.approx(33.05, abs=0.1)


def test_working_capital_blend_empty_metrics_never_raises():
    result = working_capital.compute_working_capital_blend({}, {})
    assert result["latest_period"] is None
    assert result["dso_series"] == {}


def test_working_capital_blend_extends_series_with_a_year_yfinance_lacks():
    """Regression test for a real gap found live-testing Tata Technologies
    (an IT-services company with NO 'Inventory' line on yfinance's balance
    sheet at all): `inventory_days_series`/`ccc_series` come back entirely
    empty from yfinance, but Screener's `.ratios()` DOES carry real values
    across multiple years (confirmed live: `inventory_days: 0`, a genuine
    "no inventory" business fact) — those must be used instead of showing
    a blank, added under Screener's own period keys since yfinance has no
    matching keys to reuse for this field at all."""
    metrics = {
        "receivable_days_series": {"FY2025": 70.0, "FY2026": 61.2},
        "inventory_days_series": {},
        "payable_days_series": {"FY2025": 47.0, "FY2026": 54.7},
        "ccc_series": {},
    }
    screener_ratios = {
        "debtor_days": {"2026-03-31": 79.0},
        "inventory_days": {"2025-03-31": 0.0, "2026-03-31": 0.0},
        "cash_conversion_cycle": {"2026-03-31": 79.0},
    }
    result = working_capital.compute_working_capital_blend(metrics, screener_ratios)
    # The 2025 point (not the overall latest year) keeps Screener's own ISO
    # key since nothing reconciles older years; the 2026 (latest) point
    # gets reconciled onto "FY2026" — the key DSO/DPO already use for that
    # year — so a cross-metric "latest period" lookup resolves consistently.
    assert result["dio_series"] == {"2025-03-31": 0.0, "FY2026": 0.0}
    assert result["ccc_series"] == {"FY2026": 79.0}
    assert result["ccc_latest"] == 79.0
    assert result["single_period_fallback"] == {"dso": True, "dio": True, "ccc": True}
    assert "dpo" not in result["single_period_fallback"]
    assert result["dso_series"] == {"FY2025": 70.0, "FY2026": 79.0}
    assert result["dpo_series"] == metrics["payable_days_series"]


def test_working_capital_blend_reconciles_latest_year_onto_one_shared_key():
    """Regression test for a bug caught while building the multi-year
    merge: each of the 4 series is merged independently, so two metrics
    can land on DIFFERENT key formats for the SAME fiscal year — DSO here
    reuses yfinance's "FY2026" (yfinance has DSO data), while DIO/CCC get
    Screener's ISO "2026-03-31" (yfinance has neither at all). Without
    reconciliation, `latest_period` picked from one metric's key format
    can't find the SAME year's value in a series keyed the other way —
    concretely, this broke the CCC=DIO+DSO-DPO recompute below (DIO's
    value existed but under the "wrong" key for the lookup) until this
    fix. All 4 series must end up sharing ONE key for the latest year."""
    metrics = {
        "receivable_days_series": {"FY2026": 61.2},
        "inventory_days_series": {}, "payable_days_series": {"FY2026": 54.7}, "ccc_series": {},
    }
    screener_ratios = {"inventory_days": {"2026-03-31": 5.0}}
    result = working_capital.compute_working_capital_blend(metrics, screener_ratios)
    assert result["latest_period"] == "FY2026"
    assert result["dio_series"] == {"FY2026": 5.0}, "DIO's Screener-only value must be reconciled onto DSO/DPO's FY2026 key"
    # And the CCC recompute (proof the reconciliation actually unblocked
    # a downstream cross-series lookup, not just a cosmetic key rename):
    assert result["ccc_series"] == {"FY2026": pytest.approx(5.0 + 61.2 - 54.7)}


def test_working_capital_blend_recomputes_ccc_from_backfilled_components():
    """When Screener's ratios don't include cash_conversion_cycle directly
    but DIO/DSO/DPO are all available (mix of yfinance + Screener
    backfill), CCC = DIO + DSO - DPO is computed locally rather than left
    blank."""
    metrics = {
        "receivable_days_series": {"FY2026": 61.2},
        "inventory_days_series": {},
        "payable_days_series": {"FY2026": 54.7},
        "ccc_series": {},
    }
    screener_ratios = {"inventory_days": {"2026-03-31": 5.0}}
    result = working_capital.compute_working_capital_blend(metrics, screener_ratios)
    assert result["ccc_series"] == {"FY2026": pytest.approx(5.0 + 61.2 - 54.7)}
    assert result["single_period_fallback"]["ccc"] is True


def test_working_capital_blend_no_fallback_when_screener_also_empty():
    """A genuinely unavailable ratio on BOTH sources stays empty — never a
    fabricated value."""
    metrics = {"receivable_days_series": {"FY2026": 61.2}, "inventory_days_series": {},
               "payable_days_series": {}, "ccc_series": {}}
    result = working_capital.compute_working_capital_blend(metrics, {})
    assert result["dio_series"] == {}
    assert result["ccc_series"] == {}
    assert result["single_period_fallback"] == {}


def test_working_capital_blend_screener_only_company_needs_no_yfinance_at_all():
    """When yfinance has NO data at all for dso/dio/dpo/ccc (not just one
    gap, ALL four), the merge must still produce a full multi-year series
    straight from Screener — this used to require a special-cased
    `fallback_period` hack; now it falls out naturally from merging
    Screener's own period keys directly (no yfinance keys exist to match
    against, so Screener's ISO keys are used as-is)."""
    metrics = {
        "receivable_days_series": {}, "inventory_days_series": {},
        "payable_days_series": {}, "ccc_series": {},
    }
    screener_ratios = {
        "debtor_days": {"2025-03-31": 40.0, "2026-03-31": 45.0},
        "inventory_days": {"2025-03-31": 28.0, "2026-03-31": 30.0},
        "days_payable": {"2025-03-31": 18.0, "2026-03-31": 20.0},
        "cash_conversion_cycle": {"2025-03-31": 50.0, "2026-03-31": 55.0},
    }
    result = working_capital.compute_working_capital_blend(metrics, screener_ratios)
    assert result["latest_period"] == "2026-03-31"
    assert result["dso_series"] == {"2025-03-31": 40.0, "2026-03-31": 45.0}
    assert result["dio_series"] == {"2025-03-31": 28.0, "2026-03-31": 30.0}
    assert result["dpo_series"] == {"2025-03-31": 18.0, "2026-03-31": 20.0}
    assert result["ccc_series"] == {"2025-03-31": 50.0, "2026-03-31": 55.0}
    assert result["single_period_fallback"] == {"dso": True, "dio": True, "dpo": True, "ccc": True}


def test_working_capital_amounts():
    result = working_capital.compute_working_capital_amounts(current_assets=500.0, current_liabilities=300.0, revenue=1000.0)
    assert result["net_working_capital"] == 200.0
    assert result["working_capital_pct_revenue"] == pytest.approx(20.0)
