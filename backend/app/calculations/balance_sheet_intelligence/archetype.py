"""Balance Sheet Archetype classifier (spec §40-45): STRONG / WEAK / MIDDLE
/ TRANSFORMING. Framework classifications, not universal accounting
categories — spec §40's own caveat, reinforced by every threshold below
being explicitly configurable and versioned rather than hard-coded as a
universal rule.

Thresholds are sourced from the spec's own "illustrative" language (§41's
30-40% cash/investments "war chest", §42's high-leverage framing) — this is
the same documented-invented-threshold discipline
`pl_intelligence/scoring.py` already established for M2/M5's weights.
"""
from __future__ import annotations

ARCHETYPE_RULESET_VERSION = "BS_ENGINE_V1.0"

_DEFAULT_THRESHOLDS = {
    # spec §41: "an illustrative 'war chest' concept of cash/liquid
    # investments around 30-40% of assets" — using the low end as the
    # STRONG bar, explicitly not a universal rule.
    "strong_cash_investments_pct_of_assets": 30.0,
    "strong_max_debt_to_equity": 0.3,
    "weak_min_debt_to_equity": 1.0,
    "weak_min_working_capital_pct_revenue": 25.0,
    # A 3Y window is "improving"/"worsening" once it moves by more than
    # this many percentage points — mirrors the tolerance-banded direction
    # style already used in `roce.py`/`pnl_engine.py`.
    "trend_tolerance_pct": 5.0,
}


def _direction(pct_change: float | None, tolerance: float) -> str:
    if pct_change is None:
        return "UNKNOWN"
    if abs(pct_change) <= tolerance:
        return "FLAT"
    return "UP" if pct_change > 0 else "DOWN"


def classify_archetype(
    cash_investments_pct_assets: float | None,
    debt_to_equity: float | None,
    working_capital_pct_revenue: float | None,
    debt_pct_change_3y: float | None,
    cash_pct_change_3y: float | None,
    ccc_pct_change_3y: float | None,
    thresholds: dict | None = None,
) -> dict:
    """Every input is the caller's already-computed fact — this function
    only classifies, never fetches or derives. `ccc_pct_change_3y` negative
    means CCC shortened (improving); positive means it lengthened
    (worsening) — sign convention matches `historical_trends.py`'s raw
    `pct_change` output, not pre-flipped."""
    t = {**_DEFAULT_THRESHOLDS, **(thresholds or {})}
    evidence: list[str] = []

    debt_dir = _direction(debt_pct_change_3y, t["trend_tolerance_pct"])
    cash_dir = _direction(cash_pct_change_3y, t["trend_tolerance_pct"])
    ccc_dir = _direction(ccc_pct_change_3y, t["trend_tolerance_pct"])

    is_transforming = debt_dir == "DOWN" and cash_dir == "UP" and ccc_dir in ("DOWN", "FLAT")
    if is_transforming:
        evidence.append(f"Debt declined {abs(debt_pct_change_3y):.1f}% over 3Y")
        evidence.append(f"Cash grew {cash_pct_change_3y:.1f}% over 3Y")
        if ccc_dir == "DOWN":
            evidence.append(f"Cash conversion cycle shortened {abs(ccc_pct_change_3y):.1f}% over 3Y")
        return {
            "classification": "TRANSFORMING",
            "evidence": evidence,
            "ruleset_version": ARCHETYPE_RULESET_VERSION,
            "confidence": "MEDIUM" if None not in (debt_pct_change_3y, cash_pct_change_3y, ccc_pct_change_3y) else "LOW",
        }

    is_strong = (
        cash_investments_pct_assets is not None and cash_investments_pct_assets >= t["strong_cash_investments_pct_of_assets"]
        and debt_to_equity is not None and debt_to_equity <= t["strong_max_debt_to_equity"]
    )
    if is_strong:
        evidence.append(f"Cash + investments are {cash_investments_pct_assets:.1f}% of assets (>= {t['strong_cash_investments_pct_of_assets']:.0f}% threshold)")
        evidence.append(f"Debt/Equity is {debt_to_equity:.2f}x (<= {t['strong_max_debt_to_equity']:.2f}x threshold)")
        return {
            "classification": "STRONG",
            "evidence": evidence,
            "ruleset_version": ARCHETYPE_RULESET_VERSION,
            "confidence": "MEDIUM",
        }

    is_weak = (
        (debt_to_equity is not None and debt_to_equity >= t["weak_min_debt_to_equity"])
        or (working_capital_pct_revenue is not None and working_capital_pct_revenue >= t["weak_min_working_capital_pct_revenue"])
    )
    if is_weak:
        if debt_to_equity is not None and debt_to_equity >= t["weak_min_debt_to_equity"]:
            evidence.append(f"Debt/Equity is {debt_to_equity:.2f}x (>= {t['weak_min_debt_to_equity']:.2f}x threshold)")
        if working_capital_pct_revenue is not None and working_capital_pct_revenue >= t["weak_min_working_capital_pct_revenue"]:
            evidence.append(f"Working capital is {working_capital_pct_revenue:.1f}% of revenue (>= {t['weak_min_working_capital_pct_revenue']:.0f}% threshold)")
        return {
            "classification": "WEAK",
            "evidence": evidence,
            "ruleset_version": ARCHETYPE_RULESET_VERSION,
            "confidence": "MEDIUM",
        }

    evidence.append("Manageable debt, normal working capital, no strong or weak signal crossed")
    return {
        "classification": "MIDDLE",
        "evidence": evidence,
        "ruleset_version": ARCHETYPE_RULESET_VERSION,
        "confidence": "LOW" if debt_to_equity is None and cash_investments_pct_assets is None else "MEDIUM",
    }
