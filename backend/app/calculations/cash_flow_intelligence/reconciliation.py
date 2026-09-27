"""CFO reconciliation bridge (spec §6) and cash bridge (spec §30-31) — the
central "how did profit become cash" story this engine exists to tell.
Pure functions over already-fetched single-period snapshots.
"""
from __future__ import annotations

_DEFAULT_TOLERANCE_PCT = 2.0  # looser than the Balance Sheet engine's 0.5% — cash-flow schedules sum several rounded line items, more rounding noise expected


def cfo_bridge(cfo_period: dict[str, float | None]) -> dict:
    """Operating Profit -> ± Working Capital -> - Taxes -> CFO (spec §6).
    `cfo_period` is a flat snapshot from `snapshot.period_snapshot()` for
    the CFO schedule series."""
    operating_profit = cfo_period.get("operating_profit")
    wc_change = cfo_period.get("working_capital_change")
    taxes_paid = cfo_period.get("taxes_paid")

    computed_cfo = None
    if operating_profit is not None and wc_change is not None and taxes_paid is not None:
        computed_cfo = round(operating_profit + wc_change + taxes_paid, 2)

    return {
        "operating_profit": operating_profit,
        "receivables_change": cfo_period.get("receivables_change"),
        "inventory_change": cfo_period.get("inventory_change"),
        "payables_change": cfo_period.get("payables_change"),
        "loans_advances_change": cfo_period.get("loans_advances_change"),
        "other_wc_change": cfo_period.get("other_wc_change"),
        "working_capital_change": wc_change,
        "taxes_paid": taxes_paid,
        "exceptional_items": cfo_period.get("exceptional_items"),
        "computed_cfo": computed_cfo,
    }


def cfo_bridge_check(computed_cfo: float | None, reported_cfo: float | None,
                      tolerance_pct: float = _DEFAULT_TOLERANCE_PCT) -> dict:
    """Cross-checks the bridge's own arithmetic against Screener's directly
    reported top-level CFO figure — a divergence beyond a rounding-noise
    tolerance usually means an `exceptional_items`-type line this company
    reports that isn't in the standard schedule shape."""
    if computed_cfo is None or reported_cfo is None:
        return {"status": "MISSING_DATA", "difference": None, "difference_pct": None}
    difference = computed_cfo - reported_cfo
    denom = abs(reported_cfo) if reported_cfo else None
    difference_pct = abs(difference) / denom * 100 if denom else None
    is_valid = difference_pct is not None and difference_pct <= tolerance_pct
    return {
        "status": "VALID" if is_valid else "DIVERGENT",
        "difference": round(difference, 2),
        "difference_pct": round(difference_pct, 2) if difference_pct is not None else None,
    }


def cash_bridge(opening_cash: float | None, cfo: float | None, cfi: float | None,
                 cff: float | None, closing_cash: float | None,
                 tolerance_pct: float = _DEFAULT_TOLERANCE_PCT) -> dict:
    """Opening Cash + CFO + CFI + CFF [+ Other] = Closing Cash (spec §30).
    `other_adjustment` is solved for (not assumed zero) whenever both cash
    endpoints are known — the spec's own FX/translation slot, computed as
    a residual rather than sourced (see `canonical_fields.NO_FX_ADJUSTMENT_REASON`
    for why no dedicated source line exists)."""
    other_adjustment = None
    reconciliation_status = "MISSING_DATA"
    difference_pct = None

    known_flows = [f for f in (cfo, cfi, cff) if f is not None]
    if opening_cash is not None and closing_cash is not None and len(known_flows) == 3:
        net_flow = cfo + cfi + cff
        other_adjustment = round(closing_cash - opening_cash - net_flow, 2)
        # "Reconciled" means the residual is small relative to the cash
        # balance itself (a real FX/rounding adjustment), not that it's
        # exactly zero — a residual comparable in size to the flows
        # themselves would mean a genuinely missing/misclassified line,
        # not a translation adjustment, and should read as unreconciled.
        denom = abs(closing_cash) if closing_cash else (abs(opening_cash) or None)
        if denom:
            difference_pct = round(abs(other_adjustment) / denom * 100, 2)
            reconciliation_status = "VALID" if difference_pct <= tolerance_pct * 5 else "CASH_FLOW_RECONCILIATION_ERROR"
        else:
            reconciliation_status = "VALID" if other_adjustment == 0 else "CASH_FLOW_RECONCILIATION_ERROR"

    return {
        "opening_cash": opening_cash,
        "cfo": cfo,
        "cfi": cfi,
        "cff": cff,
        "other_adjustment": other_adjustment,
        "closing_cash": closing_cash,
        "status": reconciliation_status,
        "difference_pct": difference_pct,
    }
