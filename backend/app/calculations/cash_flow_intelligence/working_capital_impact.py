"""Working Capital Cash Impact (spec §12-15) — where operating cash went,
broken into receivables/inventory/payables/other, plus the
receivables/inventory cash-drag cross-checks against revenue growth
(spec §13-14).
"""
from __future__ import annotations


def working_capital_impact(cfo_period: dict[str, float | None]) -> dict:
    """Flat breakdown for the "where did operating cash go?" visual (spec
    §12) — values are already cash-flow-impact-signed by Screener (a
    negative receivables_change means receivables grew, tying up cash)."""
    receivables = cfo_period.get("receivables_change")
    inventory = cfo_period.get("inventory_change")
    payables = cfo_period.get("payables_change")
    other = cfo_period.get("other_wc_change")
    net_wc_impact = None
    values = [v for v in (receivables, inventory, payables, other) if v is not None]
    if len(values) == 4:
        net_wc_impact = round(sum(values), 2)
    return {
        "receivables": receivables,
        "inventory": inventory,
        "payables": payables,
        "other_wc": other,
        "net_wc_impact": net_wc_impact,
    }


def receivables_cash_drag(receivables_growth_pct: float | None, revenue_growth_pct: float | None,
                           persisted_periods: int = 0) -> dict:
    """Spec §13: flag when Receivables Growth > Revenue Growth; a
    2+-period persistence upgrades the flag (same escalation pattern as
    the Balance Sheet engine's/this engine's own low-CFO-conversion rule)."""
    if receivables_growth_pct is None or revenue_growth_pct is None:
        return {"status": "MISSING_DATA", "triggered": False}
    triggered = receivables_growth_pct > revenue_growth_pct
    flag_id = "PERSISTENT_RECEIVABLE_CASH_DRAG" if triggered and persisted_periods >= 2 else "RECEIVABLE_CASH_DRAG"
    return {
        "status": "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "triggered": triggered,
        "flag_id": flag_id if triggered else None,
        "receivables_growth_pct": receivables_growth_pct,
        "revenue_growth_pct": revenue_growth_pct,
        "persisted_periods": persisted_periods,
    }


def inventory_cash_drag(inventory_growth_pct: float | None, revenue_growth_pct: float | None) -> dict:
    """Spec §14: inventory rising faster than demand/revenue growth. Never
    auto-negative — a genuine demand surge can also grow inventory faster
    than trailing revenue recognizes it; this flags for investigation, not
    a verdict (spec's own instruction)."""
    if inventory_growth_pct is None or revenue_growth_pct is None:
        return {"status": "MISSING_DATA", "triggered": False}
    triggered = inventory_growth_pct > revenue_growth_pct
    return {
        "status": "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "triggered": triggered,
        "flag_id": "INVENTORY_CASH_DRAG" if triggered else None,
        "inventory_growth_pct": inventory_growth_pct,
        "revenue_growth_pct": revenue_growth_pct,
    }


def payables_cash_support(payables_change: float | None) -> dict:
    """Spec §15: payables increase = supplier financing / cash retention —
    explicitly NOT auto-classified positive; the engine surfaces the
    number and a caller (LLM or red_flags.py) is responsible for weighing
    it against liquidity/AP-aging context, which this app doesn't have
    (see the Balance Sheet engine's own AP-aging gap)."""
    if payables_change is None:
        return {"status": "MISSING_DATA", "interpretation": None}
    interpretation = "cash_retained_via_supplier_financing" if payables_change > 0 else "supplier_financing_reduced"
    return {"status": "AVAILABLE", "payables_change": payables_change, "interpretation": interpretation}
