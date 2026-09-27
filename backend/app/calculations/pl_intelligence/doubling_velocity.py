"""Revenue & profit doubling velocity engine (spec Stage 7).

Two independent methods, both offered (never silently picking one): an
empirical walk of the actual series for the first period at/above 2x a
reference value, and a CAGR-based theoretical estimate
(`ln(2)/ln(1+CAGR)`), which only makes sense for a positive CAGR.
"""
from __future__ import annotations

import math

# Interpretation bands (spec's own explicit example numbers, Stage 7) —
# still stored as configurable constants per Rule 8 ("do not hard-code
# these as universal sector truths").
_FAST_GROWTH_MAX_YEARS = 5.0
_STRONG_GROWTH_MAX_YEARS = 8.0
_STEADY_COMPOUNDER_MAX_YEARS = 10.0
# > _STEADY_COMPOUNDER_MAX_YEARS => "SLOW_GROWTH"


def empirical_doubling(series: dict[str, float]) -> dict | None:
    """`series`: {period: value}, fiscal periods only (caller excludes
    "TTM"). Anchored to the MOST RECENT period, not the earliest — walks
    BACKWARD from there for the closest-to-today period whose value was
    still <= half of today's, i.e. "how many years back was this metric
    last at (or below) half its current level." Returns
    `{doubling_years, start_year, end_year}` or `None` when the latest
    value itself isn't usable (<=0) or no earlier positive period ever sat
    at/below half of it.

    Real bug found live on GNFC (2026-09-22, user's explicit report — "we
    do have PAT doubled, how are you calculating this?"): the original
    version walked FORWARD from the series' EARLIEST period as the sole
    reference/baseline — GNFC's earliest PAT period on record (FY2015) was
    a -452 Cr loss, so `reference <= 0` bailed the whole calculation out
    with "Not doubling," even though PAT has since grown to several
    multiples of its post-loss level (173 Cr in FY2016 -> 521 Cr in
    FY2017 alone is already >2x). One bad early year poisoned the entire
    result. Anchoring to the latest value and walking backward — the
    user's own explicit instruction ("check most recent years first and
    then move to oldest") — fixes this at the root: an old loss year no
    longer blocks the calculation, and the reported window answers the
    question an investor actually asks ("how long ago was this at half
    today's level"), not an artifact of whichever year happens to be
    earliest on record. Only a POSITIVE older value can match (a negative
    or zero period is a loss, not "at or below half of a profit," so
    matching on it would report a sign-flip turnaround as if it were 2x
    growth — nonsensical); a negative/zero year is skipped over, not
    treated as a stopping point, so the walk keeps looking further back
    for a genuine positive half-of-today reference."""
    items = sorted(series.items())
    if len(items) < 2:
        return None
    end_period, latest = items[-1]
    if latest is None or latest <= 0:
        return None
    half = latest / 2

    for period, value in reversed(items[:-1]):
        if value is not None and value > 0 and value <= half:
            start_year = int(period[:4])
            end_year = int(end_period[:4])
            return {
                "doubling_years": end_year - start_year,
                "start_year": start_year,
                "end_year": end_year,
            }
    return None


def cagr_doubling(cagr_pct: float | None) -> float | None:
    """`ln(2)/ln(1+CAGR)` — only defined for a positive CAGR; a flat or
    negative CAGR means the series never doubles on its current trajectory,
    so this returns `None` rather than a nonsensical or infinite value."""
    if cagr_pct is None or cagr_pct <= 0:
        return None
    growth_factor = 1 + (cagr_pct / 100)
    return round(math.log(2) / math.log(growth_factor), 2)


def compare_doubling_velocity(revenue_doubling_years: float | None, pat_doubling_years: float | None,
                               tolerance_years: float = 1.0) -> str:
    """Deterministic PAT-vs-revenue doubling-speed comparison — handed to
    the LLM as a pre-computed field (never left for the model to derive
    itself). Real bug caught live-testing this exact section on Maruti
    (2026-09-15): llama3.2:3b correctly read "PAT doubles in 3 years,
    revenue in 8" but then wrote "this suggests margin compression" — the
    literal opposite of what fewer years to double actually means (PAT
    compounding FASTER than revenue = margin expansion / operating
    leverage). Same failure class `pnl_engine.py::_direction()` was built
    to prevent for the sales-vs-profit-CAGR comparison; fixed the same way
    here: FEWER years = faster growth, so the comparison is inverted
    relative to a plain numeric `a > b` check."""
    if revenue_doubling_years is None or pat_doubling_years is None:
        return "INSUFFICIENT_DATA"
    if pat_doubling_years < revenue_doubling_years - tolerance_years:
        return "PAT_FASTER"  # fewer years to double = margin expansion / operating leverage
    if pat_doubling_years > revenue_doubling_years + tolerance_years:
        return "PAT_SLOWER"  # more years to double = margin compression / cost pressure
    return "ROUGHLY_SAME"


def classify_doubling_speed(doubling_years: float | None) -> str | None:
    if doubling_years is None:
        return None
    if doubling_years < _FAST_GROWTH_MAX_YEARS:
        return "FAST_GROWTH"
    if doubling_years <= _STRONG_GROWTH_MAX_YEARS:
        return "STRONG_HEALTHY_GROWTH"
    if doubling_years <= _STEADY_COMPOUNDER_MAX_YEARS:
        return "STEADY_COMPOUNDER"
    return "SLOW_GROWTH"
