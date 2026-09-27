"""Rule-based P&L diagnostics (spec Stage 19) — the 8 named flags, each a
pure function over already-computed values (never raw series, never an
LLM). `evaluate_all_rules()` runs all 8 against one `facts` dict and
returns the fired flag names — the exact `flags: [...]` list Stage 20's
narrative JSON contract expects.

`interest_burden` and `operating_overhead_pressure` use EBITDA margin and
aggregate OPEX ratio respectively in place of the spec's literal "gross
margin"/"employee cost ratio" — both dead ends in this codebase (see
package docstring); documented here, not silently substituted.
"""
from __future__ import annotations

_REVENUE_GROWTH_THRESHOLD_PCT = 10.0
_NEAR_PEAK_PCT_OF_PEAK = 0.95
_EQI_DEPENDENCY_THRESHOLD = 0.70
_CSR_RELIANCE_THRESHOLD = 0.30
_HEALTHY_EBITDA_MARGIN_PCT = 15.0
_WEAK_PAT_MARGIN_PCT = 3.0
_ELEVATED_FINANCE_COST_TO_REVENUE_PCT = 5.0


def profit_conversion_weak(revenue_growth_pct: float | None, pat_growth_pct: float | None) -> bool:
    if revenue_growth_pct is None or pat_growth_pct is None:
        return False
    return revenue_growth_pct > _REVENUE_GROWTH_THRESHOLD_PCT and pat_growth_pct < revenue_growth_pct


def margin_compression(current_pat_margin: float | None, avg_5y_pat_margin: float | None) -> bool:
    if current_pat_margin is None or avg_5y_pat_margin is None:
        return False
    return current_pat_margin < avg_5y_pat_margin


def margin_expansion_candidate(current_margin: float | None, peer_peak_margin: float | None,
                                revenue_growth_pct: float | None, margin_trend: str | None) -> bool:
    if current_margin is None or peer_peak_margin is None or revenue_growth_pct is None:
        return False
    return (current_margin < peer_peak_margin and revenue_growth_pct > 0
            and margin_trend == "EXPANSION")


def near_sector_peak(current_margin: float | None, peer_peak_margin: float | None) -> bool:
    if current_margin is None or peer_peak_margin is None or peer_peak_margin <= 0:
        return False
    return current_margin >= _NEAR_PEAK_PCT_OF_PEAK * peer_peak_margin


def non_core_income_dependency(eqi: float | None) -> bool:
    if eqi is None:
        return False
    return eqi < _EQI_DEPENDENCY_THRESHOLD


def high_subsidiary_global_reliance(csr: float | None) -> bool:
    if csr is None:
        return False
    return csr < _CSR_RELIANCE_THRESHOLD


def interest_burden(ebitda_margin: float | None, pat_margin: float | None,
                     finance_cost_to_revenue_pct: float | None) -> bool:
    if ebitda_margin is None or pat_margin is None or finance_cost_to_revenue_pct is None:
        return False
    return (ebitda_margin >= _HEALTHY_EBITDA_MARGIN_PCT
            and pat_margin < _WEAK_PAT_MARGIN_PCT
            and finance_cost_to_revenue_pct >= _ELEVATED_FINANCE_COST_TO_REVENUE_PCT)


def operating_overhead_pressure(revenue_growth_pct: float | None, ebitda_margin_trend: str | None,
                                 opex_to_revenue_delta_pp: float | None) -> bool:
    if revenue_growth_pct is None or ebitda_margin_trend is None or opex_to_revenue_delta_pp is None:
        return False
    return (revenue_growth_pct > 0 and ebitda_margin_trend == "COMPRESSION"
            and opex_to_revenue_delta_pp > 0)


def evaluate_all_rules(facts: dict) -> list[str]:
    """`facts` keys (all optional, missing -> that rule just doesn't fire):
    revenue_growth_pct, pat_growth_pct, current_pat_margin, avg_5y_pat_margin,
    current_margin, peer_peak_margin, margin_trend, eqi, csr, ebitda_margin,
    pat_margin, finance_cost_to_revenue_pct, ebitda_margin_trend,
    opex_to_revenue_delta_pp."""
    fired = []
    if profit_conversion_weak(facts.get("revenue_growth_pct"), facts.get("pat_growth_pct")):
        fired.append("profit_conversion_weak")
    if margin_compression(facts.get("current_pat_margin"), facts.get("avg_5y_pat_margin")):
        fired.append("margin_compression")
    if margin_expansion_candidate(facts.get("current_margin"), facts.get("peer_peak_margin"),
                                   facts.get("revenue_growth_pct"), facts.get("margin_trend")):
        fired.append("margin_expansion_candidate")
    if near_sector_peak(facts.get("current_margin"), facts.get("peer_peak_margin")):
        fired.append("near_sector_peak")
    if non_core_income_dependency(facts.get("eqi")):
        fired.append("non_core_income_dependency")
    if high_subsidiary_global_reliance(facts.get("csr")):
        fired.append("high_subsidiary_global_reliance")
    if interest_burden(facts.get("ebitda_margin"), facts.get("pat_margin"),
                        facts.get("finance_cost_to_revenue_pct")):
        fired.append("interest_burden")
    if operating_overhead_pressure(facts.get("revenue_growth_pct"), facts.get("ebitda_margin_trend"),
                                    facts.get("opex_to_revenue_delta_pp")):
        fired.append("operating_overhead_pressure")
    return fired
