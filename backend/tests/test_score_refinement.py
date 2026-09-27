"""Tests for `app/calculations/score_refinement.py` — the explicit "fold
the new intelligence engines into the overall score" deliverable. Pins the
blend bounds (`_MAX_ADJUSTMENT`) so a future change to the proxy tables
can't silently make a single category score move further than intended.
"""
from __future__ import annotations

from app.calculations.score_refinement import (
    _MAX_ADJUSTMENT,
    apply_score_refinement,
    refine_balance_sheet_score,
    refine_cashflow_score,
    refine_profitability_score,
)
from app.calculations.scoring import recompute_overall

# ── refine_cashflow_score ────────────────────────────────────────────────────

def test_cashflow_refinement_no_data_leaves_base_untouched():
    result = refine_cashflow_score(60.0, None)
    assert result["refined_score"] == 60.0
    assert result["adjustment"] == 0.0
    assert result["proxy_score"] is None
    assert result["source"] is None


def test_cashflow_refinement_strong_signals_pulls_up_but_bounded():
    cfi_result = {
        "conversion": {"latest": {"band": "~100%"}},
        "archetype": {"classification": "CASH_COMPOUNDER"},
        "volatility": {"classification": "STABLE_CFO"},
        "risk_flags": [],
    }
    result = refine_cashflow_score(30.0, cfi_result)
    assert result["proxy_score"] > 80.0
    assert result["adjustment"] <= _MAX_ADJUSTMENT
    assert result["adjustment"] > 0
    assert result["refined_score"] == round(30.0 + result["adjustment"], 1)


def test_cashflow_refinement_weak_signals_pulls_down_but_bounded():
    cfi_result = {
        "conversion": {"latest": {"band": "<50%"}},
        "archetype": {"classification": "DEBT_FUNDED_BUSINESS"},
        "volatility": {"classification": "NEGATIVE_CFO_PATTERN"},
        "risk_flags": [{"status": "TRIGGERED"}, {"status": "TRIGGERED"}, {"status": "NOT_TRIGGERED"}],
    }
    result = refine_cashflow_score(90.0, cfi_result)
    assert result["adjustment"] >= -_MAX_ADJUSTMENT
    assert result["adjustment"] < 0
    assert result["refined_score"] < 90.0


def test_cashflow_refinement_adjustment_never_exceeds_cap_even_from_zero():
    """The bounded-blend cap must hold even for the maximal possible
    base-to-proxy gap (base=0, proxy=100)."""
    cfi_result = {
        "conversion": {"latest": {"band": "~100%"}},
        "archetype": {"classification": "CASH_COMPOUNDER"},
        "volatility": {"classification": "STABLE_CFO"},
        "risk_flags": [],
    }
    result = refine_cashflow_score(0.0, cfi_result)
    assert result["adjustment"] == _MAX_ADJUSTMENT
    assert result["refined_score"] == _MAX_ADJUSTMENT


# ── refine_balance_sheet_score ──────────────────────────────────────────────

def test_balance_sheet_refinement_not_applicable_leaves_base_untouched():
    """Banks route through `NOT_APPLICABLE` archetype — refinement must
    not force a proxy for them (they already have bank-specific scoring)."""
    result = refine_balance_sheet_score(55.0, {"archetype": {"classification": "NOT_APPLICABLE"}, "risk_flags": []})
    assert result["refined_score"] == 55.0
    assert result["proxy_score"] is None


def test_balance_sheet_refinement_strong_archetype_pulls_up():
    result = refine_balance_sheet_score(40.0, {"archetype": {"classification": "STRONG"}, "risk_flags": []})
    assert result["adjustment"] > 0
    assert result["adjustment"] <= _MAX_ADJUSTMENT


def test_balance_sheet_refinement_red_flags_reduce_proxy():
    no_flags = refine_balance_sheet_score(50.0, {"archetype": {"classification": "STRONG"}, "risk_flags": []})
    with_flags = refine_balance_sheet_score(50.0, {
        "archetype": {"classification": "STRONG"},
        "risk_flags": [{"status": "TRIGGERED"}] * 5,
    })
    assert with_flags["proxy_score"] < no_flags["proxy_score"]


# ── refine_profitability_score ──────────────────────────────────────────────

def test_profitability_refinement_uses_master_pl_score_directly():
    result = refine_profitability_score(50.0, {"score": {"master_pl_score": 90.0}})
    assert result["proxy_score"] == 90.0
    assert result["adjustment"] == _MAX_ADJUSTMENT  # (90-50)*0.5=20, capped at 10


def test_profitability_refinement_none_score_leaves_base_untouched():
    result = refine_profitability_score(50.0, {"score": {"master_pl_score": None}})
    assert result["refined_score"] == 50.0
    assert result["source"] is None


# ── apply_score_refinement (end-to-end) ─────────────────────────────────────

def test_apply_score_refinement_without_weights_returns_unchanged():
    scores = {"overall": 60.0, "profitability": 60.0, "cash_flow": 60.0, "balance_sheet": 60.0}
    result = apply_score_refinement(scores, None, None, None)
    assert result is scores


def test_apply_score_refinement_recomputes_overall_via_shared_helper():
    weights = {"growth": 0.18, "profitability": 0.22, "cash_flow": 0.17,
               "balance_sheet": 0.17, "efficiency": 0.12, "valuation": 0.14}
    scores = {
        "overall": 60.0, "growth": 60.0, "profitability": 60.0, "cash_flow": 60.0,
        "balance_sheet": 60.0, "efficiency": 60.0, "valuation": 60.0, "weights": weights,
    }
    cfi_result = {
        "conversion": {"latest": {"band": "~100%"}},
        "archetype": {"classification": "CASH_COMPOUNDER"},
        "volatility": {"classification": "STABLE_CFO"},
        "risk_flags": [],
    }
    result = apply_score_refinement(scores, None, None, cfi_result)
    assert result is not scores  # never mutates in place
    assert result["cash_flow"] > scores["cash_flow"]
    expected_overall = recompute_overall(
        {"growth": result["growth"], "profitability": result["profitability"], "cash_flow": result["cash_flow"],
         "balance_sheet": result["balance_sheet"], "efficiency": result["efficiency"], "valuation": result["valuation"]},
        weights,
    )
    assert result["overall"] == expected_overall
    assert result["refinement"]["pre_refinement_overall"] == 60.0
    assert "cash_flow" in result["refinement"]


def test_apply_score_refinement_all_none_engines_keeps_overall_stable():
    weights = {"growth": 0.18, "profitability": 0.22, "cash_flow": 0.17,
               "balance_sheet": 0.17, "efficiency": 0.12, "valuation": 0.14}
    scores = {
        "overall": 60.0, "growth": 60.0, "profitability": 60.0, "cash_flow": 60.0,
        "balance_sheet": 60.0, "efficiency": 60.0, "valuation": 60.0, "weights": weights,
    }
    result = apply_score_refinement(scores, None, None, None)
    assert result["overall"] == 60.0
    assert result["profitability"] == 60.0
    assert result["balance_sheet"] == 60.0
    assert result["cash_flow"] == 60.0
