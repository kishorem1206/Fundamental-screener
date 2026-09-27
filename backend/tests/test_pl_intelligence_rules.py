"""Rule-engine tests (P&L Analysis Engine plan, Milestone 3) — each of the
8 rules independently true/false-tested with synthetic facts."""
from __future__ import annotations

from app.calculations.pl_intelligence.rules import evaluate_all_rules


def test_no_rules_fire_on_empty_facts():
    assert evaluate_all_rules({}) == []


def test_profit_conversion_weak_fires():
    facts = {"revenue_growth_pct": 18.0, "pat_growth_pct": 11.0}
    assert "profit_conversion_weak" in evaluate_all_rules(facts)


def test_profit_conversion_weak_does_not_fire_when_pat_keeps_up():
    facts = {"revenue_growth_pct": 18.0, "pat_growth_pct": 20.0}
    assert "profit_conversion_weak" not in evaluate_all_rules(facts)


def test_margin_compression_fires():
    facts = {"current_pat_margin": 10.0, "avg_5y_pat_margin": 15.0}
    assert "margin_compression" in evaluate_all_rules(facts)


def test_margin_compression_does_not_fire_when_above_average():
    facts = {"current_pat_margin": 20.0, "avg_5y_pat_margin": 15.0}
    assert "margin_compression" not in evaluate_all_rules(facts)


def test_margin_expansion_candidate_fires():
    facts = {"current_margin": 15.0, "peer_peak_margin": 22.0,
             "revenue_growth_pct": 5.0, "margin_trend": "EXPANSION"}
    assert "margin_expansion_candidate" in evaluate_all_rules(facts)


def test_margin_expansion_candidate_does_not_fire_without_expansion_trend():
    facts = {"current_margin": 15.0, "peer_peak_margin": 22.0,
             "revenue_growth_pct": 5.0, "margin_trend": "STABLE"}
    assert "margin_expansion_candidate" not in evaluate_all_rules(facts)


def test_near_sector_peak_fires():
    facts = {"current_margin": 21.5, "peer_peak_margin": 22.0}  # 97.7% of peak
    assert "near_sector_peak" in evaluate_all_rules(facts)


def test_near_sector_peak_does_not_fire_when_far_from_peak():
    facts = {"current_margin": 15.0, "peer_peak_margin": 22.0}
    assert "near_sector_peak" not in evaluate_all_rules(facts)


def test_non_core_income_dependency_fires():
    assert "non_core_income_dependency" in evaluate_all_rules({"eqi": 0.55})


def test_non_core_income_dependency_does_not_fire_for_high_eqi():
    assert "non_core_income_dependency" not in evaluate_all_rules({"eqi": 0.95})


def test_high_subsidiary_global_reliance_fires():
    assert "high_subsidiary_global_reliance" in evaluate_all_rules({"csr": 0.20})


def test_high_subsidiary_global_reliance_does_not_fire_for_high_csr():
    assert "high_subsidiary_global_reliance" not in evaluate_all_rules({"csr": 0.90})


def test_interest_burden_fires():
    facts = {"ebitda_margin": 20.0, "pat_margin": 1.0, "finance_cost_to_revenue_pct": 8.0}
    assert "interest_burden" in evaluate_all_rules(facts)


def test_interest_burden_does_not_fire_with_low_finance_cost():
    facts = {"ebitda_margin": 20.0, "pat_margin": 1.0, "finance_cost_to_revenue_pct": 1.0}
    assert "interest_burden" not in evaluate_all_rules(facts)


def test_operating_overhead_pressure_fires():
    facts = {"revenue_growth_pct": 10.0, "ebitda_margin_trend": "COMPRESSION",
             "opex_to_revenue_delta_pp": 2.5}
    assert "operating_overhead_pressure" in evaluate_all_rules(facts)


def test_operating_overhead_pressure_does_not_fire_when_opex_ratio_falling():
    facts = {"revenue_growth_pct": 10.0, "ebitda_margin_trend": "COMPRESSION",
             "opex_to_revenue_delta_pp": -1.0}
    assert "operating_overhead_pressure" not in evaluate_all_rules(facts)


def test_multiple_rules_can_fire_together():
    facts = {
        "revenue_growth_pct": 18.0, "pat_growth_pct": 11.0,
        "eqi": 0.55, "csr": 0.20,
    }
    fired = evaluate_all_rules(facts)
    assert "profit_conversion_weak" in fired
    assert "non_core_income_dependency" in fired
    assert "high_subsidiary_global_reliance" in fired
