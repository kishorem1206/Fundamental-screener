"""Earnings bridge (Stage 12), operating leverage detector (Stage 13),
interest & overhead trap detector (Stage 14), margin stability score
(Stage 15).

`margin_cascade_break` substitutes EBITDA margin for the spec's literal
"healthy Gross Margin" leg of the check — Gross Margin is always
unavailable in this codebase (see package docstring), so EBITDA margin is
the closest available "healthy operating economics" signal; this is a
documented deviation from the spec's exact wording, not a silent
substitution.
"""
from __future__ import annotations

import statistics

from app.calculations.engine import safe_div

_DIRECTION_TOLERANCE_PP = 2.0  # matches pnl_engine.py's own _direction tolerance

# Stage 14's "healthy EBITDA margin" / "weak-or-negative PAT margin"
# thresholds — spec gives no exact numbers here either, configurable per
# Rule 8.
_HEALTHY_EBITDA_MARGIN_PCT = 15.0
_WEAK_PAT_MARGIN_PCT = 3.0
_ELEVATED_FINANCE_COST_TO_REVENUE_PCT = 5.0

_STABILITY_STDEV_HIGH_PP = 3.0  # >= this stdev over the lookback = "volatile"
_STABILITY_HIGH_MARGIN_PCT = 15.0  # current margin >= this = "high" margin tier


def _direction(a: float | None, b: float | None, tolerance_pp: float = _DIRECTION_TOLERANCE_PP) -> str:
    """Same deterministic tolerance-banded comparison `pnl_engine.py`'s own
    `_direction()` implements — reimplemented locally (not imported) to
    keep this package's Stage-0 boundary from `pnl_engine.py` clean, same
    rationale that module documents for why this must never be left to an
    LLM to eyeball."""
    if a is None or b is None:
        return "INSUFFICIENT_DATA"
    if a > b + tolerance_pp:
        return "FASTER"
    if a < b - tolerance_pp:
        return "SLOWER"
    return "ROUGHLY_IN_LINE"


def earnings_bridge(cascade_series: dict[str, dict]) -> list[dict]:
    """`cascade_series`: `cascade.build_income_cascade()`'s full output.
    Returns one entry per fiscal year (from the second year on, since
    growth needs a prior year), each with YoY growth % for every cascade
    step. `gross_profit_growth` is always `None` (dead end #1)."""
    periods = sorted(cascade_series.keys())
    bridge = []
    for prior_period, period in zip(periods, periods[1:]):
        prior, current = cascade_series[prior_period], cascade_series[period]
        bridge.append({
            "period": period,
            "revenue_growth": _growth_pct(prior.get("revenue"), current.get("revenue")),
            "gross_profit_growth": None,
            "ebitda_growth": _growth_pct(prior.get("ebitda"), current.get("ebitda")),
            "ebit_growth": _growth_pct(prior.get("ebit"), current.get("ebit")),
            "pbt_growth": _growth_pct(prior.get("pbt"), current.get("pbt")),
            "pat_growth": _growth_pct(prior.get("pat"), current.get("pat")),
        })
    return bridge


def _growth_pct(prior: float | None, current: float | None) -> float | None:
    if prior is None or current is None or prior == 0:
        return None
    return round((current - prior) / abs(prior) * 100, 2)


def operating_leverage(revenue_growth: float | None, ebitda_growth: float | None, pat_growth: float | None) -> dict:
    """Spec Stage 13's 4 comparison rules — identifies the bottleneck
    rather than a bare "good/bad" label."""
    ebitda_vs_revenue = _direction(ebitda_growth, revenue_growth)
    pat_vs_ebitda = _direction(pat_growth, ebitda_growth)

    operating_leverage_label = {
        "FASTER": "POSITIVE", "SLOWER": "NEGATIVE", "ROUGHLY_IN_LINE": "NEUTRAL",
    }.get(ebitda_vs_revenue, "INSUFFICIENT_DATA")

    below_ebitda_label = {
        "FASTER": "BELOW_EBITDA_ITEMS_HELPING",
        "SLOWER": "BELOW_EBITDA_ITEMS_ABSORBING_GAINS",
        "ROUGHLY_IN_LINE": "BELOW_EBITDA_ITEMS_NEUTRAL",
    }.get(pat_vs_ebitda, "INSUFFICIENT_DATA")

    return {
        "ebitda_vs_revenue": ebitda_vs_revenue,
        "operating_leverage": operating_leverage_label,
        "pat_vs_ebitda": pat_vs_ebitda,
        "below_ebitda_effect": below_ebitda_label,
    }


def margin_cascade_break(ebitda_margin: float | None, pat_margin: float | None,
                          finance_cost_to_revenue_pct: float | None) -> dict | None:
    """Stage 14's diagnostic object. Fires only when EBITDA margin is
    healthy but PAT margin is weak/negative — `None` (no diagnostic) if
    that pattern doesn't hold or data is missing."""
    if ebitda_margin is None or pat_margin is None:
        return None
    if not (ebitda_margin >= _HEALTHY_EBITDA_MARGIN_PCT and pat_margin < _WEAK_PAT_MARGIN_PCT):
        return None

    likely_drivers = []
    if finance_cost_to_revenue_pct is not None and finance_cost_to_revenue_pct >= _ELEVATED_FINANCE_COST_TO_REVENUE_PCT:
        likely_drivers.append("finance_cost")
    likely_drivers.append("operating_overhead")  # always plausible per spec's own example

    severity = "HIGH" if pat_margin < 0 else "MEDIUM"
    return {
        "type": "margin_cascade_break",
        "severity": severity,
        "ebitda_margin": ebitda_margin,  # substituted for the spec's unavailable gross_margin
        "pat_margin": pat_margin,
        "likely_drivers": likely_drivers,
    }


def margin_stability_score(margin_series: dict[str, float]) -> dict:
    """`margin_series`: {period: margin_pct}. Classifies into the spec's 5
    buckets (High+Stable / High+Volatile / Low+Improving / Low+Stable /
    High+Declining) using stdev + current-vs-first-half trend."""
    items = sorted(margin_series.items())
    values = [v for _, v in items if v is not None]
    if len(values) < 2:
        return {
            "current": values[-1] if values else None, "avg_5y": None, "avg_10y": None,
            "stdev": None, "max": None, "min": None, "classification": "INSUFFICIENT_DATA",
        }

    current = values[-1]
    last_5 = values[-5:]
    last_10 = values[-10:]
    stdev = round(statistics.pstdev(last_10), 2) if len(last_10) > 1 else 0.0
    is_volatile = stdev >= _STABILITY_STDEV_HIGH_PP
    is_high = current >= _STABILITY_HIGH_MARGIN_PCT

    half = max(1, len(last_5) // 2)
    earlier_avg = statistics.mean(last_5[:half])
    later_avg = statistics.mean(last_5[half:]) if len(last_5) > half else current
    trend = _direction(later_avg, earlier_avg, tolerance_pp=1.0)

    if is_volatile:
        classification = "HIGH_VOLATILE" if is_high else "LOW_VOLATILE"
    elif is_high:
        classification = "HIGH_DECLINING" if trend == "SLOWER" else "HIGH_STABLE"
    else:
        classification = "LOW_IMPROVING" if trend == "FASTER" else "LOW_STABLE"

    return {
        "current": current,
        "avg_5y": round(statistics.mean(last_5), 2),
        "avg_10y": round(statistics.mean(last_10), 2),
        "stdev": stdev,
        "max": round(max(last_10), 2),
        "min": round(min(last_10), 2),
        "classification": classification,
    }
