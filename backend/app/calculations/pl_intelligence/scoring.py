"""M1-M5 weighted P&L Master Score (spec Stage 16-17).

Weights and M1/M3/M4 breakpoints are the spec's own explicit numbers.
M2 (margin headroom opportunity) and M5 (Consolidated Structural Ratio) are
**not** given complete numeric tables by the spec (Stage 16 says so
explicitly for both) — their scoring functions below are documented,
versioned, invented conventions, not literal spec content (Rule 8: "make
thresholds configurable... do not silently invent unversioned rules").

`ALGORITHM_VERSION` is this codebase's first version-stamped calculation —
confirmed zero prior precedent anywhere else in the app. Any future change
to a weight or threshold in this file must bump it; old persisted
`pl_score_components` rows are never overwritten in place (see the
Milestone 3 migration's unique constraint on `(company_id, period,
statement_type, algorithm_version)`).
"""
from __future__ import annotations

ALGORITHM_VERSION = "PL_ENGINE_V1.0"

# Master score weights — spec's own exact numbers (Stage 17).
_WEIGHTS = {"M1": 0.25, "M2": 0.20, "M3": 0.20, "M4": 0.20, "M5": 0.15}

# M1 — Sector Margin Percentile thresholds (spec's own exact numbers, Stage 16).
_M1_TOP_PERCENTILE = 80
_M1_MID_PERCENTILE = 50

# M3 — Sales Doubling Velocity thresholds (spec's own exact numbers, Stage 16).
# The 8-10y gap is explicitly called out by the spec as needing
# "configurable interpolation" rather than a silently invented boundary.
_M3_FAST_YEARS = 5.0
_M3_STRONG_YEARS = 8.0
_M3_SLOW_YEARS = 10.0

# M4 — Earnings Quality Index thresholds (spec's own exact numbers, Stage 16;
# same thresholds `earnings_quality.py` classifies EQI with).
from app.calculations.pl_intelligence.earnings_quality import (  # noqa: E402
    EQI_HIGH_THRESHOLD,
    EQI_MEDIUM_THRESHOLD,
)

# M2 — NOT spec-complete. Scores `margin_headroom.interpret_headroom_and_growth()`'s
# 4-case classification: a company with high headroom AND high growth is the
# strongest margin-expansion opportunity; low headroom + low growth the
# weakest. Invented convention, versioned under ALGORITHM_VERSION.
_M2_SCORE_BY_CLASSIFICATION = {
    "STRONG_EXPANSION_CANDIDATE": 100.0,
    "GROWTH_LED_COMPOUNDER": 80.0,
    "POTENTIAL_EFFICIENCY_TURNAROUND": 50.0,
    "MATURE_STAGNANT_CANDIDATE": 30.0,
}

# M5 — NOT spec-complete either. Scores `standalone_consolidated.py`'s CSR
# band. This treats a higher standalone/consolidated overlap (more
# "parent-transparent") as a HIGHER score — NOT a claim that
# subsidiary-heavy structures are worse investments, only that this proxy
# reflects the structural-complexity risk the spec's own CSR<0.30 flag is
# about, until real per-subsidiary quality data exists to score on
# separately. Invented convention, versioned under ALGORITHM_VERSION.
_M5_SCORE_BY_BAND = {
    "PRIMARILY_PARENT_DOMESTIC": 100.0,
    "MATERIAL_SUBSIDIARY_CONTRIBUTION": 75.0,
    "SIGNIFICANT_GROUP_CONTRIBUTION": 50.0,
    "CONSOLIDATED_STRUCTURE_DOMINATES": 25.0,
}


def score_m1_sector_margin_percentile(percentile: int | float | None) -> float | None:
    if percentile is None:
        return None
    if percentile > _M1_TOP_PERCENTILE:
        return 100.0
    if percentile >= _M1_MID_PERCENTILE:
        return 70.0
    return 30.0


def score_m2_margin_headroom(headroom_growth_classification: str | None) -> float | None:
    if headroom_growth_classification is None:
        return None
    return _M2_SCORE_BY_CLASSIFICATION.get(headroom_growth_classification)


def score_m3_doubling_velocity(doubling_years: float | None) -> float | None:
    if doubling_years is None:
        return None
    if doubling_years < _M3_FAST_YEARS:
        return 100.0
    if doubling_years <= _M3_STRONG_YEARS:
        return 80.0
    if doubling_years >= _M3_SLOW_YEARS:
        return 40.0
    # spec-flagged gap: linearly interpolate strong (80) -> slow (40)
    t = (doubling_years - _M3_STRONG_YEARS) / (_M3_SLOW_YEARS - _M3_STRONG_YEARS)
    return round(80.0 - t * 40.0, 2)


def score_m4_eqi(eqi: float | None) -> float | None:
    if eqi is None:
        return None
    if eqi >= EQI_HIGH_THRESHOLD:
        return 100.0
    if eqi >= EQI_MEDIUM_THRESHOLD:
        return 60.0
    return 20.0


def score_m5_csr(csr_band: str | None) -> float | None:
    if csr_band is None:
        return None
    return _M5_SCORE_BY_BAND.get(csr_band)


def compute_master_score(m1: float | None, m2: float | None, m3: float | None,
                          m4: float | None, m5: float | None) -> dict:
    """Weighted `0.25*M1 + 0.20*M2 + 0.20*M3 + 0.20*M4 + 0.15*M5`. A missing
    component is EXCLUDED and the remaining weights renormalized (per Rule
    4 — a missing input must never silently become a 0 that drags the
    score down, nor a neutral 50 that overstates confidence) rather than
    computed over a fixed denominator. `components` is always populated,
    never omitted (Rule 6 — never expose a score without its components).
    If every component is missing, `master_pl_score` is `None`.
    """
    components = {"M1": m1, "M2": m2, "M3": m3, "M4": m4, "M5": m5}
    available = {k: v for k, v in components.items() if v is not None}

    if not available:
        master_pl_score = None
    else:
        weight_sum = sum(_WEIGHTS[k] for k in available)
        weighted = sum(_WEIGHTS[k] * v for k, v in available.items())
        master_pl_score = round(weighted / weight_sum, 2)

    classification = _classify_master_score(master_pl_score)

    return {
        "master_pl_score": master_pl_score,
        "classification": classification,
        "components": components,
        "weights": dict(_WEIGHTS),
        "algorithm_version": ALGORITHM_VERSION,
    }


def _classify_master_score(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 80:
        return "PREMIUM_QUALITY_GROWTH_EFFICIENCY_LEADER"
    if score >= 60:
        return "STABLE_COMPOUNDER_MARGIN_EXPANSION_CANDIDATE"
    return "HIGH_OVERHEAD_NON_CORE_TRAP_STAGNANT_PERFORMER"
