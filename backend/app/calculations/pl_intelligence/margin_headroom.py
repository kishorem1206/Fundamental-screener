"""Margin ceiling / headroom engine (spec Stage 6).

The spec describes the 4 classification bands and the headroom x growth
interpretation matrix qualitatively but gives no numeric band boundaries
(unlike Stage 16's M1/M3/M4, which do specify exact percentile/year
breakpoints) — per Rule 8, the thresholds below are explicit, documented,
configurable constants, not a claim that the spec itself specifies these
exact numbers.
"""
from __future__ import annotations

# Configurable thresholds (spec Rule 8) — headroom_pct = how far below the
# sector's peak margin the company sits, as a % of that peak.
_NEAR_PEAK_MAX_PCT = 5.0
_MODERATE_HEADROOM_MAX_PCT = 20.0
_HIGH_HEADROOM_MAX_PCT = 40.0
# above _HIGH_HEADROOM_MAX_PCT => SEVERE_UNDERPERFORMANCE

# Revenue-growth threshold used only to bucket "high" vs "weak" growth for
# the 2D headroom x growth interpretation matrix below.
_HIGH_REVENUE_GROWTH_PCT = 10.0


def compute_headroom(company_margin: float | None, peer_max_margin: float | None) -> dict:
    """`company_margin`/`peer_max_margin` are percentages (e.g. PAT margin).
    Returns `{headroom, headroom_pct, classification}`; all `None` if either
    input is missing (never fabricated)."""
    if company_margin is None or peer_max_margin is None or peer_max_margin <= 0:
        return {"headroom": None, "headroom_pct": None, "classification": None}

    headroom = round(peer_max_margin - company_margin, 2)
    headroom_pct = round((headroom / peer_max_margin) * 100, 2)

    if headroom_pct <= _NEAR_PEAK_MAX_PCT:
        classification = "NEAR_PEAK"
    elif headroom_pct <= _MODERATE_HEADROOM_MAX_PCT:
        classification = "MODERATE_HEADROOM"
    elif headroom_pct <= _HIGH_HEADROOM_MAX_PCT:
        classification = "HIGH_HEADROOM"
    else:
        classification = "SEVERE_UNDERPERFORMANCE"

    return {"headroom": headroom, "headroom_pct": headroom_pct, "classification": classification}


def interpret_headroom_and_growth(headroom_classification: str | None, revenue_growth_pct: float | None) -> str | None:
    """Spec Stage 6's 2D interpretation matrix — headroom alone isn't
    enough (a low-margin company with declining revenue should not read as
    a growth opportunity)."""
    if headroom_classification is None or revenue_growth_pct is None:
        return None

    has_headroom = headroom_classification in ("HIGH_HEADROOM", "SEVERE_UNDERPERFORMANCE")
    has_growth = revenue_growth_pct >= _HIGH_REVENUE_GROWTH_PCT

    if has_headroom and has_growth:
        return "STRONG_EXPANSION_CANDIDATE"
    if has_headroom and not has_growth:
        return "POTENTIAL_EFFICIENCY_TURNAROUND"
    if not has_headroom and has_growth:
        return "GROWTH_LED_COMPOUNDER"
    return "MATURE_STAGNANT_CANDIDATE"
