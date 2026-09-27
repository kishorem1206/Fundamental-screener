"""Forensic Cash Flow Patterns (spec §38) — combinations of signals, not
single ratios. Each pattern is a small pure function over already-computed
facts; `evaluate_all_patterns()` assembles them into one list, same style
as `balance_sheet_intelligence/red_flags.py`.
"""
from __future__ import annotations

_WEAK_CFO_CONVERSION_PCT = 50.0
_MATERIAL_PAYABLES_GROWTH_PCT = 15.0


def _result(pattern_id: str, triggered: bool, evidence: list[str]) -> dict:
    return {"pattern_id": pattern_id, "status": "TRIGGERED" if triggered else "NOT_TRIGGERED", "evidence": evidence}


def pattern_a_profit_without_cash(operating_profit_growth_pct: float | None, cfo_growth_pct: float | None,
                                   conversion_declining: bool) -> dict:
    if operating_profit_growth_pct is None or cfo_growth_pct is None:
        return _result("PROFIT_CASH_DIVERGENCE", False, [])
    triggered = operating_profit_growth_pct > 0 and cfo_growth_pct < 0 and conversion_declining
    evidence = [f"Operating profit grew {operating_profit_growth_pct:.1f}% while CFO fell {cfo_growth_pct:.1f}%"] if triggered else []
    return _result("PROFIT_CASH_DIVERGENCE", triggered, evidence)


def pattern_b_receivable_driven_weakness(receivables_growth_pct: float | None, revenue_growth_pct: float | None,
                                          cfo_growth_pct: float | None) -> dict:
    if None in (receivables_growth_pct, revenue_growth_pct, cfo_growth_pct):
        return _result("RECEIVABLE_CASH_DRAG", False, [])
    triggered = receivables_growth_pct > revenue_growth_pct and cfo_growth_pct < 0
    evidence = [f"Receivables grew {receivables_growth_pct:.1f}% vs revenue's {revenue_growth_pct:.1f}%, CFO fell {cfo_growth_pct:.1f}%"] if triggered else []
    return _result("RECEIVABLE_CASH_DRAG", triggered, evidence)


def pattern_c_inventory_driven_weakness(inventory_growth_pct: float | None, cfo_growth_pct: float | None,
                                         inventory_turnover_declining: bool) -> dict:
    if inventory_growth_pct is None or cfo_growth_pct is None:
        return _result("INVENTORY_CASH_DRAG", False, [])
    triggered = inventory_growth_pct > 0 and cfo_growth_pct < 0 and inventory_turnover_declining
    evidence = [f"Inventory grew {inventory_growth_pct:.1f}%, CFO fell {cfo_growth_pct:.1f}%, turnover deteriorating"] if triggered else []
    return _result("INVENTORY_CASH_DRAG", triggered, evidence)


def pattern_d_supplier_financed_cfo(payables_growth_pct: float | None, cfo_growth_pct: float | None) -> dict:
    """Explicitly an analytical observation, not automatically a red flag
    (spec's own instruction) — `status` uses OBSERVED rather than
    TRIGGERED/NOT_TRIGGERED to keep that distinction visible downstream."""
    if payables_growth_pct is None or cfo_growth_pct is None:
        return {"pattern_id": "PAYABLE_SUPPORTED_CFO", "status": "NOT_OBSERVED", "evidence": []}
    observed = payables_growth_pct > _MATERIAL_PAYABLES_GROWTH_PCT and cfo_growth_pct > 0
    evidence = [f"Payables grew {payables_growth_pct:.1f}% alongside CFO growth of {cfo_growth_pct:.1f}%"] if observed else []
    return {"pattern_id": "PAYABLE_SUPPORTED_CFO", "status": "OBSERVED" if observed else "NOT_OBSERVED", "evidence": evidence}


def pattern_e_capex_funding_gap(cfo: float | None, capex_abs: float | None,
                                 borrowings_raised: float | None, equity_raised: float | None) -> dict:
    if cfo is None or capex_abs is None:
        return _result("CAPEX_FUNDING_DEPENDENCE", False, [])
    triggered = cfo < capex_abs
    evidence = []
    if triggered:
        gap = round(capex_abs - cfo, 2)
        evidence.append(f"CFO ({cfo:.0f}) covers only {cfo / capex_abs * 100:.0f}% of capex ({capex_abs:.0f}), gap of {gap:.0f}")
        if borrowings_raised:
            evidence.append(f"Debt raised: {borrowings_raised:.0f}")
        if equity_raised:
            evidence.append(f"Equity raised: {equity_raised:.0f}")
    return _result("CAPEX_FUNDING_DEPENDENCE", triggered, evidence)


def pattern_f_debt_funded_cash_generation(cfo: float | None, cff: float | None, borrowings_raised: float | None) -> dict:
    if cfo is None or cff is None:
        return _result("EXTERNAL_DEBT_DEPENDENCE", False, [])
    weak_cfo = cfo <= 0
    triggered = weak_cfo and cff > 0 and (borrowings_raised or 0) > 0
    evidence = [f"CFO was {cfo:.0f} while CFF was strongly positive ({cff:.0f}), driven by {borrowings_raised:.0f} in new borrowings"] if triggered else []
    return _result("EXTERNAL_DEBT_DEPENDENCE", triggered, evidence)


def pattern_g_asset_liquidation_support(cfo: float | None, cfi: float | None,
                                         fixed_assets_sold: float | None, investments_sold: float | None) -> dict:
    if cfo is None or cfi is None:
        return _result("NON_OPERATING_CASH_SUPPORT", False, [])
    weak_cfo = cfo <= 0
    liquidation = (fixed_assets_sold or 0) + (investments_sold or 0)
    triggered = weak_cfo and cfi > 0 and liquidation >= cfi * 0.5
    evidence = [f"CFO was {cfo:.0f} while CFI was positive ({cfi:.0f}), largely from asset/investment sales ({liquidation:.0f})"] if triggered else []
    return _result("NON_OPERATING_CASH_SUPPORT", triggered, evidence)


def evaluate_all_patterns(facts: dict) -> list[dict]:
    """`facts` keys (all optional, missing -> None): operating_profit_growth_pct,
    cfo_growth_pct, conversion_declining, receivables_growth_pct,
    revenue_growth_pct, inventory_growth_pct, inventory_turnover_declining,
    payables_growth_pct, cfo, capex_abs, borrowings_raised, equity_raised,
    cff, cfi, fixed_assets_sold, investments_sold."""
    return [
        pattern_a_profit_without_cash(facts.get("operating_profit_growth_pct"), facts.get("cfo_growth_pct"), bool(facts.get("conversion_declining"))),
        pattern_b_receivable_driven_weakness(facts.get("receivables_growth_pct"), facts.get("revenue_growth_pct"), facts.get("cfo_growth_pct")),
        pattern_c_inventory_driven_weakness(facts.get("inventory_growth_pct"), facts.get("cfo_growth_pct"), bool(facts.get("inventory_turnover_declining"))),
        pattern_d_supplier_financed_cfo(facts.get("payables_growth_pct"), facts.get("cfo_growth_pct")),
        pattern_e_capex_funding_gap(facts.get("cfo"), facts.get("capex_abs"), facts.get("borrowings_raised"), facts.get("equity_raised")),
        pattern_f_debt_funded_cash_generation(facts.get("cfo"), facts.get("cff"), facts.get("borrowings_raised")),
        pattern_g_asset_liquidation_support(facts.get("cfo"), facts.get("cfi"), facts.get("fixed_assets_sold"), facts.get("investments_sold")),
    ]
