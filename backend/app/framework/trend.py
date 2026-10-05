"""Trend classification — the direction of the business, not of the price
(framework section 9): Improving, Stable, Cyclical, Declining or Insufficient
data.

Each signal the framework names votes up, flat or down:

    returns        ROCE trend (ROE for lenders)
    margins        operating margin and net margin trend
    debt           debt trend (not for lenders, whose borrowing is their raw material)
    cash flow      free cash flow trend (not for lenders)
    growth         whether the latest quarters are running ahead of or behind
                   the multi-year rate

Earnings revisions are also on the framework's list; they join in a later
phase when analyst estimates are read for more than a handful of companies.
"""
from __future__ import annotations

_VOTE = {"STRONGLY_IMPROVING": 1, "IMPROVING": 1, "STABLE": 0, "DETERIORATING": -1, "STRONGLY_DETERIORATING": -1}
_MIN_SIGNALS = 3
_MIN_SIGNALS_LENDER = 2  # a lender has only three signals to begin with


def _growth_vote(metrics: dict) -> tuple[int, str] | None:
    recent, annual = metrics.get("quarterly_growth_pct"), metrics.get("revenue_cagr_3y")
    if isinstance(recent, dict):  # per-metric recent growth; sales is the one compared with the sales CAGR
        recent = recent.get("revenue", recent.get("sales"))
    if recent is None or annual is None:
        return None
    gap = recent - annual
    if recent < 0 and annual < 0:
        return -1, f"sales falling: {recent:.1f}% recently, {annual:.1f}% a year over the longer period"
    if gap > 5:
        return 1, f"sales growth accelerating: {recent:.1f}% recently against {annual:.1f}% a year"
    if gap < -5:
        return -1, f"sales growth slowing: {recent:.1f}% recently against {annual:.1f}% a year"
    return 0, f"sales growth steady: {recent:.1f}% recently against {annual:.1f}% a year"


def classify_trend(metrics: dict, lender: bool = False) -> dict:
    plan = [("returns", "roe_trend" if lender else "roce_trend"), ("net margin", "pat_margin_trend")]
    if not lender:
        plan += [("operating margin", "ebitda_margin_trend"), ("debt", "debt_trend"), ("free cash flow", "fcf_trend")]
    signals, volatile = [], 0
    for name, key in plan:
        label = metrics.get(key)
        if label == "VOLATILE":
            volatile += 1
            signals.append({"signal": name, "vote": 0, "reading": "volatile"})
        elif label in _VOTE:
            signals.append({"signal": name, "vote": _VOTE[label], "reading": label.replace("_", " ").lower()})
    growth = _growth_vote(metrics)
    if growth:
        signals.append({"signal": "growth", "vote": growth[0], "reading": growth[1]})

    if len(signals) < (_MIN_SIGNALS_LENDER if lender else _MIN_SIGNALS):
        return {"trend": "INSUFFICIENT_DATA", "signals": signals, "reason": f"only {len(signals)} of the signals could be read"}
    up = sum(1 for s in signals if s["vote"] > 0)
    down = sum(1 for s in signals if s["vote"] < 0)
    cyclical = bool(metrics.get("is_cyclical"))
    # a clear direction is reported as that direction even for a cyclical business;
    # "cyclical" is for when the swings are wide and the signals disagree
    if up - down >= 2 and up > down * 2:
        trend, reason = "IMPROVING", f"{up} signals improving, {down} declining"
    elif down - up >= 2 and down > up * 2:
        trend, reason = "DECLINING", f"{down} signals declining, {up} improving"
    elif (cyclical or volatile >= 2) and up and down:
        trend, reason = "CYCLICAL", "margins swing widely through the cycle and the signals point both ways"
    elif volatile >= 2 and not up and not down:
        trend, reason = "CYCLICAL", "most signals are volatile with no clear direction"
    else:
        trend, reason = "STABLE", f"{up} improving, {down} declining, {len(signals) - up - down} flat"
    return {"trend": trend, "reason": reason, "improving": up, "declining": down, "signals": signals}
