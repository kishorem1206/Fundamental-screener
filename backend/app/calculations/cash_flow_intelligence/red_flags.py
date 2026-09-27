"""Red Flag engine — the 2 source-mandated flags (spec §39) plus a small
set of additional application-level diagnostics (spec §40) that aren't
already covered by `forensic_patterns.py`'s 7 combination patterns. All
flags use the spec §48 JSON schema. `evaluate_all_flags()` always returns
every rule ID, matching the same "never silently omit a rule" discipline
as `balance_sheet_intelligence/red_flags.py`.
"""
from __future__ import annotations

_LOW_CONVERSION_THRESHOLD_PCT = 50.0
_UNALLOCATED_CAPITAL_DRAG_THRESHOLD_PCT = 25.0


def _flag(flag_id: str, severity: str, status: str, metric: str, actual, threshold,
          period: str | None, persistence: int, evidence: list[str], source: list[str], confidence: str) -> dict:
    return {
        "flag_id": flag_id, "severity": severity, "status": status, "metric": metric,
        "actual": actual, "threshold": threshold, "period": period, "persistence": persistence,
        "evidence": evidence, "source": source, "confidence": confidence,
    }


def rule_1_low_cfo_conversion(current_ratio_pct: float | None, prior_ratio_pct: float | None, period: str | None) -> dict:
    """Spec §39 Red Flag 1: <50% for 1 year -> WATCH, 2 consecutive years
    -> RED_FLAG."""
    if current_ratio_pct is None:
        return _flag("LOW_CFO_CONVERSION", "WATCH", "NOT_TRIGGERED", "CFO / Operating Profit",
                      None, _LOW_CONVERSION_THRESHOLD_PCT, period, 0, [], ["SCREENER"], "UNAVAILABLE")

    current_low = current_ratio_pct < _LOW_CONVERSION_THRESHOLD_PCT
    prior_low = prior_ratio_pct is not None and prior_ratio_pct < _LOW_CONVERSION_THRESHOLD_PCT

    if current_low and prior_low:
        severity, status, persistence = "RED", "TRIGGERED", 2
        evidence = [f"CFO conversion was {current_ratio_pct:.0f}% this period and {prior_ratio_pct:.0f}% the prior period, both below {_LOW_CONVERSION_THRESHOLD_PCT:.0f}%"]
    elif current_low:
        severity, status, persistence = "WATCH", "TRIGGERED", 1
        evidence = [f"CFO conversion was {current_ratio_pct:.0f}%, below {_LOW_CONVERSION_THRESHOLD_PCT:.0f}% — single period, not yet a persistent pattern"]
    else:
        severity, status, persistence, evidence = "WATCH", "NOT_TRIGGERED", 0, []

    return _flag("LOW_CFO_CONVERSION", severity, status, "CFO / Operating Profit",
                 current_ratio_pct, _LOW_CONVERSION_THRESHOLD_PCT, period, persistence, evidence, ["SCREENER"], "HIGH")


def rule_2_unallocated_capital_drag(other_investing: float | None, annual_cfo: float | None, period: str | None) -> dict:
    """Spec §39 Red Flag 2. This app cannot verify "clear asset disclosures
    are unavailable" (that needs annual-report note-reading this app
    doesn't do) — always tagged confidence=LOW when triggered, never
    presented as a confirmed finding."""
    if other_investing is None or not annual_cfo:
        return _flag("UNALLOCATED_CAPITAL_DRAG", "AMBER", "NOT_TRIGGERED", "Other Investing Items / Annual CFO",
                     None, _UNALLOCATED_CAPITAL_DRAG_THRESHOLD_PCT, period, 0, [], ["SCREENER"], "UNAVAILABLE")
    ratio_pct = abs(other_investing) / abs(annual_cfo) * 100
    triggered = ratio_pct > _UNALLOCATED_CAPITAL_DRAG_THRESHOLD_PCT
    evidence = [f"Other investing items are {ratio_pct:.0f}% of annual CFO — disclosure quality not independently verifiable"] if triggered else []
    return _flag("UNALLOCATED_CAPITAL_DRAG", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
                 "Other Investing Items / Annual CFO", round(ratio_pct, 2), _UNALLOCATED_CAPITAL_DRAG_THRESHOLD_PCT,
                 period, 0, evidence, ["SCREENER"], "LOW" if triggered else "MEDIUM")


def rule_3_cfo_negative_multiple_periods(cfo_volatility_classification: str | None, period: str | None) -> dict:
    triggered = cfo_volatility_classification == "NEGATIVE_CFO_PATTERN"
    evidence = ["CFO was negative in 2 or more of the tracked periods"] if triggered else []
    return _flag("CFO_NEGATIVE_MULTIPLE_PERIODS", "RED", "TRIGGERED" if triggered else "NOT_TRIGGERED",
                 "CFO volatility classification", cfo_volatility_classification, "NEGATIVE_CFO_PATTERN",
                 period, 0, evidence, ["SCREENER"], "HIGH" if cfo_volatility_classification else "UNAVAILABLE")


def rule_4_fcf_negative_multiple_periods(fcf_quality_classification: str | None, period: str | None) -> dict:
    triggered = fcf_quality_classification == "PERSISTENT_NEGATIVE_FCF"
    evidence = ["FCF has been negative across every tracked period"] if triggered else []
    return _flag("FCF_NEGATIVE_MULTIPLE_PERIODS", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
                 "FCF quality classification", fcf_quality_classification, "PERSISTENT_NEGATIVE_FCF",
                 period, 0, evidence, ["SCREENER"], "HIGH" if fcf_quality_classification else "UNAVAILABLE")


def rule_5_cash_reconciliation_mismatch(reconciliation_status: str | None, difference_pct: float | None, period: str | None) -> dict:
    triggered = reconciliation_status == "CASH_FLOW_RECONCILIATION_ERROR"
    evidence = [f"Cash bridge residual is {difference_pct:.1f}% of the closing balance, beyond the rounding-noise tolerance"] if triggered and difference_pct is not None else []
    return _flag("CASH_RECONCILIATION_MISMATCH", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
                 "Cash bridge reconciliation", reconciliation_status, "VALID", period, 0, evidence,
                 ["SCREENER"], "HIGH" if reconciliation_status else "UNAVAILABLE")


def evaluate_all_flags(facts: dict) -> list[dict]:
    """`facts` keys (all optional): period, current_conversion_pct,
    prior_conversion_pct, other_investing, annual_cfo,
    cfo_volatility_classification, fcf_quality_classification,
    reconciliation_status, reconciliation_difference_pct."""
    period = facts.get("period")
    return [
        rule_1_low_cfo_conversion(facts.get("current_conversion_pct"), facts.get("prior_conversion_pct"), period),
        rule_2_unallocated_capital_drag(facts.get("other_investing"), facts.get("annual_cfo"), period),
        rule_3_cfo_negative_multiple_periods(facts.get("cfo_volatility_classification"), period),
        rule_4_fcf_negative_multiple_periods(facts.get("fcf_quality_classification"), period),
        rule_5_cash_reconciliation_mismatch(facts.get("reconciliation_status"), facts.get("reconciliation_difference_pct"), period),
    ]
