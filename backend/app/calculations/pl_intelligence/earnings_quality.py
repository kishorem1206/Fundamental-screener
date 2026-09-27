"""Quality of Earnings engine (spec Stage 10-11).

EQI = core_operating_income / total_income, where `core_operating_income`
is REVENUE (the reported core-operating-activity income line) and
`total_income` = revenue + other_income — both measured at the same
"income" level, not revenue-vs-profit. (An earlier draft of this function
divided EBITDA — a post-opex PROFIT figure — by total_income instead;
caught live-testing Maruti Suzuki, whose genuinely healthy ~13% EBITDA
margin produced an EQI of 0.13, reading as "low quality earnings" for one
of the more core-business-driven companies on the exchange. The spec's own
worked example (Jio Financial Services: "reported income contained a
significant dividend component while core operating income was much
smaller") only makes sense as a revenue-vs-other-income comparison — a
company whose OTHER INCOME dwarfs its REVENUE is genuinely non-core-income
dependent; a normal company's EBITDA margin being "only" 13% of revenue
says nothing about non-core dependency at all.) The spec's Stage 11 non-core sub-decomposition
(dividend vs. interest vs. investment gains vs. capital gains vs.
exceptional) is a further dead end: Screener's `pnl_other_income` is one
aggregate line, same root cause as `cost_structure.py`'s employee-cost gap
— only the AGGREGATE other-income ratios are computable, so that block is
returned as an explicit `not_available` shape (never a missing key a
caller could KeyError on, and never a fabricated split).
"""
from __future__ import annotations

from app.calculations.engine import safe_div

# EQI scoring thresholds — spec's own explicit numbers (Stage 10), kept as
# configurable constants (also directly reused as M4's scoring table in
# scoring.py).
EQI_HIGH_THRESHOLD = 0.90
EQI_MEDIUM_THRESHOLD = 0.70


def compute_eqi(cascade_period: dict) -> dict:
    """`cascade_period`: one period's entry from
    `cascade.build_income_cascade()`. `core_operating_income` here is
    REVENUE itself — the reported core-operating-activity income line, the
    same "income" basis as `total_income` (revenue + other_income). See
    module docstring for why this is NOT EBITDA."""
    revenue = cascade_period.get("revenue")
    other_income = cascade_period.get("other_income")

    if revenue is None or other_income is None:
        return {
            "eqi": None, "confidence": "UNAVAILABLE",
            "core_operating_income": revenue, "total_income": None,
            "classification": None,
        }

    total_income = revenue + other_income
    eqi = safe_div(revenue, total_income)
    if eqi is None:
        return {
            "eqi": None, "confidence": "UNAVAILABLE",
            "core_operating_income": revenue, "total_income": total_income,
            "classification": None,
        }

    if eqi >= EQI_HIGH_THRESHOLD:
        classification = "HIGH_QUALITY"
    elif eqi >= EQI_MEDIUM_THRESHOLD:
        classification = "MODERATE_QUALITY"
    else:
        classification = "LOW_QUALITY_NON_CORE_DEPENDENT"

    return {
        "eqi": round(eqi, 4),
        "confidence": "MEDIUM",  # derived, not a single reported line
        "core_operating_income": revenue,
        "total_income": round(total_income, 2),
        "classification": classification,
    }


def compute_non_core_income_ratios(cascade_period: dict) -> dict:
    """Only the aggregate ratios (Stage 11's decomposition sub-buckets are
    not computable — see module docstring). Shape is stable/always present
    so a caller never needs to guard for a missing key, only for `None`
    values inside it."""
    other_income = cascade_period.get("other_income")
    pat = cascade_period.get("pat")
    ebitda = cascade_period.get("ebitda")

    return {
        "decomposition": "not_available",
        "reason": (
            "Screener.in's P&L reports Other Income as one aggregate line "
            "— dividend/interest/investment-gains/capital-gains/exceptional "
            "sub-buckets cannot be separated from what this app ingests."
        ),
        "aggregate_ratios": {
            "other_income_to_pat_pct": _pct(safe_div(other_income, pat)),
            "other_income_to_ebitda_pct": _pct(safe_div(other_income, ebitda)),
        },
    }


def _pct(fraction: float | None) -> float | None:
    return round(fraction * 100, 2) if fraction is not None else None
