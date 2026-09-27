"""Red Flag engine (spec §46-53, 12 rules). Every rule ID is always present
in the output — rules 7 (related-party loans), 8 (contingent liabilities)
and 12 (debt maturity) have no source anywhere in this app and always
return `SOURCE_REQUIRED`, never silently omitted, so the coverage story
stays complete (spec §54-56's mandate) and a reader can tell "not
evaluated" apart from "evaluated and clean."

Each rule is a small pure function; `evaluate_all_flags()` assembles the
spec §64 JSON shape from an already-computed `facts` dict — this module
does no DB access, matching every calc module here except `snapshot.py`.
"""
from __future__ import annotations

from app.calculations.balance_sheet_intelligence.canonical_fields import (
    NO_CONTINGENT_LIABILITIES_REASON,
    NO_DEBT_MATURITY_REASON,
    NO_GROSS_PPE_REASON,
    NO_RELATED_PARTY_REASON,
    NO_ST_LT_DEBT_SPLIT_REASON,
)

_DE_HIGH_THRESHOLD = 0.75
_DE_VERY_HIGH_THRESHOLD = 3.0
_CFO_PAT_MIN_CONVERSION_PCT = 50.0
_WC_GROWTH_MULTIPLE = 2.0
_RELATED_PARTY_PCT_NET_WORTH = 5.0
_CONTINGENT_PCT_NET_WORTH = 10.0
_GROSS_BLOCK_GROWTH_PCT = 50.0


def _flag(flag_id: str, severity: str, status: str, metric: str, threshold, actual, comparison,
          period: str | None, evidence: list[str], source: list[str], confidence: str) -> dict:
    return {
        "flag_id": flag_id, "severity": severity, "status": status, "metric": metric,
        "threshold": threshold, "actual": actual, "comparison": comparison, "period": period,
        "evidence": evidence, "source": source, "confidence": confidence,
    }


def rule_1_accounting_imbalance(integrity_status: str, period: str | None) -> dict:
    triggered = integrity_status == "BALANCE_SHEET_INTEGRITY_ERROR"
    return _flag(
        "ACCOUNTING_IMBALANCE", "RED", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "Total Assets vs Total Liabilities + Equity", "0 (must balance)", integrity_status, None,
        period, ["Accounting identity failed validation"] if triggered else [], ["SCREENER"],
        "HIGH" if integrity_status in ("VALID", "BALANCE_SHEET_INTEGRITY_ERROR") else "LOW",
    )


def rule_2_high_leverage(debt_to_equity: float | None, period: str | None) -> dict:
    triggered = debt_to_equity is not None and debt_to_equity > _DE_HIGH_THRESHOLD
    return _flag(
        "HIGH_LEVERAGE", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "Debt/Equity", f"> {_DE_HIGH_THRESHOLD}x", debt_to_equity, _DE_HIGH_THRESHOLD,
        period, [f"D/E of {debt_to_equity:.2f}x exceeds {_DE_HIGH_THRESHOLD}x"] if triggered else [],
        ["SCREENER"], "HIGH" if debt_to_equity is not None else "UNAVAILABLE",
    )


def rule_3_very_high_leverage(debt_to_equity: float | None, period: str | None) -> dict:
    triggered = debt_to_equity is not None and debt_to_equity > _DE_VERY_HIGH_THRESHOLD
    return _flag(
        "HIGH_LEVERAGE_INVESTIGATION", "RED", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "Debt/Equity", f"> {_DE_VERY_HIGH_THRESHOLD}x", debt_to_equity, _DE_VERY_HIGH_THRESHOLD,
        period, [f"D/E of {debt_to_equity:.2f}x exceeds {_DE_VERY_HIGH_THRESHOLD}x — analytical guardrail, not a prediction"] if triggered else [],
        ["SCREENER"], "HIGH" if debt_to_equity is not None else "UNAVAILABLE",
    )


def rule_4_cfo_divergence(cumulative_3y_cfo: float | None, cumulative_3y_pat: float | None, period: str | None) -> dict:
    if cumulative_3y_cfo is None or cumulative_3y_pat is None or not cumulative_3y_pat or cumulative_3y_pat <= 0:
        return _flag("LOW_CASH_EARNINGS_CONVERSION", "AMBER", "NOT_TRIGGERED", "3Y CFO / 3Y PAT",
                      f"< {_CFO_PAT_MIN_CONVERSION_PCT}%", None, None, period, [], ["SCREENER_CASH_FLOW", "PNL_LEDGER"], "UNAVAILABLE")
    conversion_pct = cumulative_3y_cfo / cumulative_3y_pat * 100
    triggered = conversion_pct < _CFO_PAT_MIN_CONVERSION_PCT
    return _flag(
        "LOW_CASH_EARNINGS_CONVERSION", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "3Y CFO / 3Y PAT", f"< {_CFO_PAT_MIN_CONVERSION_PCT}%", round(conversion_pct, 1), _CFO_PAT_MIN_CONVERSION_PCT,
        period, [f"3Y cumulative CFO is {conversion_pct:.0f}% of 3Y cumulative PAT"] if triggered else [],
        ["SCREENER_CASH_FLOW", "PNL_LEDGER"], "MEDIUM",
    )


def rule_5_receivables_inventory_spike(receivables_growth_pct: float | None, inventory_growth_pct: float | None,
                                        revenue_growth_pct: float | None, period: str | None) -> dict:
    if revenue_growth_pct is None:
        return _flag("WORKING_CAPITAL_DRAG", "AMBER", "NOT_TRIGGERED", "Receivables/Inventory growth vs Revenue growth",
                      f"> {_WC_GROWTH_MULTIPLE}x revenue growth", None, None, period, [], ["YFINANCE"], "UNAVAILABLE")
    evidence = []
    triggered = False
    threshold_growth = revenue_growth_pct * _WC_GROWTH_MULTIPLE if revenue_growth_pct > 0 else None
    if receivables_growth_pct is not None and threshold_growth is not None and receivables_growth_pct > threshold_growth:
        triggered = True
        evidence.append(f"Receivables grew {receivables_growth_pct:.1f}% vs revenue's {revenue_growth_pct:.1f}%")
    if inventory_growth_pct is not None and threshold_growth is not None and inventory_growth_pct > threshold_growth:
        triggered = True
        evidence.append(f"Inventory grew {inventory_growth_pct:.1f}% vs revenue's {revenue_growth_pct:.1f}%")
    return _flag(
        "WORKING_CAPITAL_DRAG", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "Receivables/Inventory growth vs Revenue growth", f"> {_WC_GROWTH_MULTIPLE}x revenue growth",
        {"receivables_growth_pct": receivables_growth_pct, "inventory_growth_pct": inventory_growth_pct},
        revenue_growth_pct, period, evidence, ["YFINANCE"], "MEDIUM",
    )


def rule_6_equity_dilution(equity_capital_growth_pct: float | None, cfo_latest: float | None, period: str | None) -> dict:
    weak_cfo = cfo_latest is not None and cfo_latest <= 0
    triggered = equity_capital_growth_pct is not None and equity_capital_growth_pct > 0 and weak_cfo
    return _flag(
        "EXTERNAL_FUNDING_DEPENDENCE", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "Share Capital growth + CFO", "Capital growth with weak/zero CFO",
        {"equity_capital_growth_pct": equity_capital_growth_pct, "cfo_latest": cfo_latest}, None,
        period, [f"Share capital grew {equity_capital_growth_pct:.1f}% while CFO was {cfo_latest}"] if triggered else [],
        ["SCREENER", "SCREENER_CASH_FLOW"], "MEDIUM" if equity_capital_growth_pct is not None and cfo_latest is not None else "UNAVAILABLE",
    )


def rule_7_related_party_loans() -> dict:
    return _flag("RELATED_PARTY_EXPOSURE", "AMBER", "SOURCE_REQUIRED", "Related-party loans / Net Worth",
                 f"> {_RELATED_PARTY_PCT_NET_WORTH}%", None, None, None, [NO_RELATED_PARTY_REASON], [], "UNAVAILABLE")


def rule_8_contingent_liabilities() -> dict:
    return _flag("CONTINGENT_LIABILITY_RISK", "AMBER", "SOURCE_REQUIRED", "Contingent Liabilities / Net Worth",
                 f"> {_CONTINGENT_PCT_NET_WORTH}%", None, None, None, [NO_CONTINGENT_LIABILITIES_REASON], [], "UNAVAILABLE")


def rule_9_capex_without_cash_generation(fixed_assets_growth_pct: float | None, cfo_latest: float | None, period: str | None) -> dict:
    """Spec's literal rule needs GROSS block growth; Screener only has net
    `fixed_assets` — substituted, tagged confidence=LOW, never presented as
    the literal gross-block rule (see `NO_GROSS_PPE_REASON`)."""
    cfo_negative = cfo_latest is not None and cfo_latest < 0
    triggered = fixed_assets_growth_pct is not None and fixed_assets_growth_pct > _GROSS_BLOCK_GROWTH_PCT and cfo_negative
    return _flag(
        "UNPRODUCTIVE_CAPEX_INVESTIGATION", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "Net Fixed Assets growth + CFO", f"> {_GROSS_BLOCK_GROWTH_PCT}% growth with negative CFO",
        {"fixed_assets_growth_pct": fixed_assets_growth_pct, "cfo_latest": cfo_latest}, None,
        period, [f"Net fixed assets grew {fixed_assets_growth_pct:.1f}% while CFO was negative ({cfo_latest})"] if triggered else [],
        ["SCREENER", "SCREENER_CASH_FLOW"], "LOW",
    )


def rule_10_working_capital_stress(dso_pct_change: float | None, inventory_days_pct_change: float | None,
                                    ccc_pct_change: float | None, cfo_pct_change: float | None, period: str | None) -> dict:
    signals = [
        dso_pct_change is not None and dso_pct_change > 0,
        inventory_days_pct_change is not None and inventory_days_pct_change > 0,
        ccc_pct_change is not None and ccc_pct_change > 0,
        cfo_pct_change is not None and cfo_pct_change < 0,
    ]
    known_signals = [s for s, raw in zip(signals, (dso_pct_change, inventory_days_pct_change, ccc_pct_change, cfo_pct_change)) if raw is not None]
    triggered = len(known_signals) >= 3 and all(known_signals)
    evidence = []
    if triggered:
        if dso_pct_change: evidence.append(f"DSO changed {dso_pct_change:+.1f}%")
        if inventory_days_pct_change: evidence.append(f"Inventory days changed {inventory_days_pct_change:+.1f}%")
        if ccc_pct_change: evidence.append(f"CCC changed {ccc_pct_change:+.1f}%")
        if cfo_pct_change: evidence.append(f"CFO changed {cfo_pct_change:+.1f}%")
    return _flag(
        "WORKING_CAPITAL_STRESS", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "DSO↑ + Inventory Days↑ + CCC↑ + CFO↓", "all four signals present", None, None,
        period, evidence, ["YFINANCE", "SCREENER_CASH_FLOW"], "MEDIUM" if len(known_signals) == 4 else "LOW",
    )


def rule_11_liquidity_pressure(cash_pct_change: float | None, current_liabilities_pct_change: float | None,
                                borrowings_pct_change: float | None, period: str | None) -> dict:
    """Spec's literal rule needs short-term-debt specifically; Screener's
    `borrowings` has no ST/LT split — total borrowings substituted (see
    `NO_ST_LT_DEBT_SPLIT_REASON`)."""
    signals = [
        cash_pct_change is not None and cash_pct_change < 0,
        current_liabilities_pct_change is not None and current_liabilities_pct_change > 0,
        borrowings_pct_change is not None and borrowings_pct_change > 0,
    ]
    known_signals = [s for s, raw in zip(signals, (cash_pct_change, current_liabilities_pct_change, borrowings_pct_change)) if raw is not None]
    triggered = len(known_signals) >= 2 and all(known_signals)
    evidence = []
    if triggered:
        if cash_pct_change: evidence.append(f"Cash changed {cash_pct_change:+.1f}%")
        if current_liabilities_pct_change: evidence.append(f"Current liabilities changed {current_liabilities_pct_change:+.1f}%")
        if borrowings_pct_change: evidence.append(f"Borrowings changed {borrowings_pct_change:+.1f}% (substitutes ST-debt, {NO_ST_LT_DEBT_SPLIT_REASON})")
    return _flag(
        "LIQUIDITY_PRESSURE", "AMBER", "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "Cash↓ + Current Liabilities↑ + Borrowings↑", "all signals present", None, None,
        period, evidence, ["YFINANCE", "SCREENER"], "MEDIUM" if len(known_signals) == 3 else "LOW",
    )


def rule_12_debt_maturity_pressure() -> dict:
    return _flag("MATURITY_LIQUIDITY_RISK", "AMBER", "SOURCE_REQUIRED", "Debt due <12M vs Cash + near-term liquidity",
                 "debt due < available liquidity", None, None, None, [NO_DEBT_MATURITY_REASON], [], "UNAVAILABLE")


def evaluate_all_flags(facts: dict) -> list[dict]:
    """`facts` keys (all optional — a missing key is treated as None,
    never raises): integrity_status, debt_to_equity, cumulative_3y_cfo,
    cumulative_3y_pat, receivables_growth_pct, inventory_growth_pct,
    revenue_growth_pct, equity_capital_growth_pct, cfo_latest,
    fixed_assets_growth_pct, dso_pct_change, inventory_days_pct_change,
    ccc_pct_change, cfo_pct_change, cash_pct_change,
    current_liabilities_pct_change, borrowings_pct_change, period."""
    period = facts.get("period")
    return [
        rule_1_accounting_imbalance(facts.get("integrity_status"), period),
        rule_2_high_leverage(facts.get("debt_to_equity"), period),
        rule_3_very_high_leverage(facts.get("debt_to_equity"), period),
        rule_4_cfo_divergence(facts.get("cumulative_3y_cfo"), facts.get("cumulative_3y_pat"), period),
        rule_5_receivables_inventory_spike(facts.get("receivables_growth_pct"), facts.get("inventory_growth_pct"), facts.get("revenue_growth_pct"), period),
        rule_6_equity_dilution(facts.get("equity_capital_growth_pct"), facts.get("cfo_latest"), period),
        rule_7_related_party_loans(),
        rule_8_contingent_liabilities(),
        rule_9_capex_without_cash_generation(facts.get("fixed_assets_growth_pct"), facts.get("cfo_latest"), period),
        rule_10_working_capital_stress(facts.get("dso_pct_change"), facts.get("inventory_days_pct_change"), facts.get("ccc_pct_change"), facts.get("cfo_pct_change"), period),
        rule_11_liquidity_pressure(facts.get("cash_pct_change"), facts.get("current_liabilities_pct_change"), facts.get("borrowings_pct_change"), period),
        rule_12_debt_maturity_pressure(),
    ]
