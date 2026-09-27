"""Cost structure analysis (spec Stage 3) — explains WHY margins move, not
just that they moved.

Only the ratios actually computable from what `pnl_history_client.py`
ingests are implemented: finance-cost/revenue, depreciation/revenue,
tax/pbt, and aggregate opex/revenue. Employee-cost/revenue (the spec's own
headline example — "employee costs growing faster than revenue") is NOT
computable: Screener's `pnl_expenses` is one aggregate OPEX line with no
employee/material/power-fuel split (dead end #3, see package docstring).
`operating_overhead_pressure` (Milestone 3's rule engine) uses the
aggregate OPEX ratio here as its input instead, with a confidence-LOW label
attached rather than silently narrowing scope.
"""
from __future__ import annotations

from app.calculations.engine import safe_div
from app.calculations.pl_intelligence.canonical_fields import NO_COST_LINE_BREAKDOWN_REASON


def compute_cost_ratios(cascade_period: dict) -> dict:
    """Takes one period's entry from `cascade.build_income_cascade()`'s
    output and returns the Stage 3 cost ratios for that period."""
    revenue = cascade_period.get("revenue")
    pbt = cascade_period.get("pbt")

    return {
        "opex_to_revenue_pct": _pct(safe_div(cascade_period.get("opex"), revenue)),
        "finance_cost_to_revenue_pct": _pct(safe_div(cascade_period.get("finance_cost"), revenue)),
        "depreciation_to_revenue_pct": _pct(safe_div(cascade_period.get("depreciation"), revenue)),
        "tax_to_pbt_pct": _pct(safe_div(cascade_period.get("tax"), pbt)),
        "employee_cost_to_revenue_pct": None,
        "employee_cost_confidence": "UNAVAILABLE",
        "employee_cost_reason": NO_COST_LINE_BREAKDOWN_REASON,
    }


def compute_cost_ratio_deltas(current: dict, prior: dict) -> dict:
    """Period-over-period change in each Stage 3 ratio (percentage points),
    `current`/`prior` each being a `compute_cost_ratios()` output. `None` if
    either side is missing for that ratio."""
    deltas = {}
    for key in ("opex_to_revenue_pct", "finance_cost_to_revenue_pct",
                "depreciation_to_revenue_pct", "tax_to_pbt_pct"):
        cur_v, prior_v = current.get(key), prior.get(key)
        deltas[f"delta_{key}"] = round(cur_v - prior_v, 2) if cur_v is not None and prior_v is not None else None
    return deltas


def _pct(fraction: float | None) -> float | None:
    return round(fraction * 100, 2) if fraction is not None else None
