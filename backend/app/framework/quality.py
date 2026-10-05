"""Quality Score — the framework's first gate (section 2).

    Quality = 70% Fundamental Score + 30% Business Quality   (user's choice, 2026-10-06)

When Business Quality cannot be measured, Quality is the Fundamental Score
alone and says so. A major governance red flag (promoter pledge above 10% of
the promoter holding, or a governance penalty of 10 points or more from the
NSE shareholding checks) caps Quality at 49: such a company cannot pass the
core-portfolio gate of 50 (section 17, "no major governance red flag").

Bands (section 2): 65+ strong, 50-64 good / acceptable, 40-49 borderline,
below 40 weak, below 30 very weak.
"""
from __future__ import annotations

FUNDAMENTAL_SHARE, BUSINESS_SHARE = 0.70, 0.30
GOVERNANCE_CAP = 49.0
_PLEDGE_EVENTS = {("PLEDGE_PRESENT", "MEDIUM"), ("PLEDGE_PRESENT", "HIGH")}


def band(score: float | None) -> str | None:
    if score is None:
        return None
    return ("STRONG" if score >= 65 else "GOOD" if score >= 50 else "BORDERLINE" if score >= 40
            else "WEAK" if score >= 30 else "VERY_WEAK")


def governance_red_flag(business_quality: dict) -> str | None:
    promoter = (business_quality.get("components") or {}).get("promoter_behaviour") or {}
    for flag in promoter.get("governance_flags") or []:
        if (flag["event_type"], flag["severity"]) in _PLEDGE_EVENTS:
            return f"promoter pledge ({flag['severity'].lower()}, {flag['event_date']})"
    if (promoter.get("governance_penalty") or 0) >= 10:
        return f"governance penalty of {promoter['governance_penalty']} points from NSE shareholding checks"
    return None


def compute_quality(fundamental: dict, business_quality: dict) -> dict:
    f, b = fundamental.get("score"), business_quality.get("score")
    if f is None:
        return {"score": None, "band": None, "reason": "no Fundamental Score"}
    if b is None:
        score, formula = f, "Fundamental Score only: Business Quality could not be measured"
    else:
        score, formula = FUNDAMENTAL_SHARE * f + BUSINESS_SHARE * b, "70% Fundamental + 30% Business Quality"
    out = {"formula": formula, "fundamental": f, "business_quality": b}
    flag = governance_red_flag(business_quality)
    if flag and score > GOVERNANCE_CAP:
        out["capped"] = f"capped at {GOVERNANCE_CAP:.0f} from {score:.1f}: {flag}"
        score = GOVERNANCE_CAP
    if flag:
        out["governance_red_flag"] = flag
    score = round(score, 1)
    return {"score": score, "band": band(score), **out}
