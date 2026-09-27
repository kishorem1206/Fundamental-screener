"""Cash Flow Archetypes (spec §61) — 6 descriptive patterns, explicitly
"analytical archetypes," not investment ratings (spec's own instruction).
Configurable thresholds, versioned for future tuning traceability, same
discipline as `balance_sheet_intelligence/archetype.py`.
"""
from __future__ import annotations

CF_ARCHETYPE_RULESET_VERSION = "CF_ENGINE_V1.0"

_DEFAULT_THRESHOLDS = {
    "healthy_conversion_pct": 70.0,
    "weak_conversion_pct": 50.0,
    "high_capex_to_cfo_pct": 70.0,
    "moderate_capex_to_cfo_pct": 40.0,
}


def classify_cash_flow_archetype(
    cfo_volatility_classification: str | None,
    fcf_quality_classification: str | None,
    latest_conversion_pct: float | None,
    capex_to_cfo_pct: float | None,
    debt_classification: str | None,
    asset_liquidation_triggered: bool,
    dividends_or_buybacks_present: bool,
    thresholds: dict | None = None,
) -> dict:
    t = {**_DEFAULT_THRESHOLDS, **(thresholds or {})}
    evidence: list[str] = []

    cfo_consistent = cfo_volatility_classification == "STABLE_CFO"
    fcf_consistent_positive = fcf_quality_classification == "CONSISTENT_POSITIVE_FCF"
    healthy_conversion = latest_conversion_pct is not None and latest_conversion_pct >= t["healthy_conversion_pct"]
    weak_conversion = latest_conversion_pct is not None and latest_conversion_pct < t["weak_conversion_pct"]
    high_capex = capex_to_cfo_pct is not None and capex_to_cfo_pct >= t["high_capex_to_cfo_pct"]
    weak_cfo = cfo_volatility_classification in ("NEGATIVE_CFO_PATTERN", "DECLINING_CFO")

    # Type F — Asset Liquidation Supported (checked first: a real, specific
    # signal that would otherwise get masked by a generic "weak CFO" read)
    if asset_liquidation_triggered:
        evidence.append("Cash flow relies materially on asset/investment sales rather than core operations")
        return {"classification": "ASSET_LIQUIDATION_SUPPORTED", "evidence": evidence,
                "ruleset_version": CF_ARCHETYPE_RULESET_VERSION, "confidence": "MEDIUM"}

    # Type D — Debt-Funded Business
    if weak_cfo and debt_classification == "NET_BORROWING":
        evidence.append("Weak/negative CFO combined with net new borrowing")
        return {"classification": "DEBT_FUNDED_BUSINESS", "evidence": evidence,
                "ruleset_version": CF_ARCHETYPE_RULESET_VERSION, "confidence": "MEDIUM"}

    # Type C — Working Capital Trap
    if weak_conversion and not weak_cfo:
        evidence.append(f"CFO conversion of {latest_conversion_pct:.0f}% is below the {t['weak_conversion_pct']:.0f}% threshold despite positive operating profit")
        return {"classification": "WORKING_CAPITAL_TRAP", "evidence": evidence,
                "ruleset_version": CF_ARCHETYPE_RULESET_VERSION, "confidence": "MEDIUM"}

    # Type A — Cash Compounder
    if cfo_consistent and fcf_consistent_positive and healthy_conversion:
        evidence.append(f"CFO stable, FCF consistently positive, conversion at {latest_conversion_pct:.0f}%")
        return {"classification": "CASH_COMPOUNDER", "evidence": evidence,
                "ruleset_version": CF_ARCHETYPE_RULESET_VERSION, "confidence": "MEDIUM"}

    # Type E — Cash Harvest
    if healthy_conversion and not high_capex and dividends_or_buybacks_present:
        evidence.append("Healthy cash conversion, moderate reinvestment, visible shareholder distributions/debt reduction")
        return {"classification": "CASH_HARVEST", "evidence": evidence,
                "ruleset_version": CF_ARCHETYPE_RULESET_VERSION, "confidence": "MEDIUM"}

    # Type B — Growth Reinvestment
    if not weak_cfo and high_capex:
        evidence.append(f"Positive CFO with high reinvestment (capex is {capex_to_cfo_pct:.0f}% of CFO)")
        return {"classification": "GROWTH_REINVESTMENT", "evidence": evidence,
                "ruleset_version": CF_ARCHETYPE_RULESET_VERSION, "confidence": "MEDIUM"}

    evidence.append("No single archetype signal dominates — mixed or insufficient evidence")
    return {"classification": "MIXED", "evidence": evidence,
            "ruleset_version": CF_ARCHETYPE_RULESET_VERSION,
            "confidence": "LOW" if latest_conversion_pct is None else "MEDIUM"}
