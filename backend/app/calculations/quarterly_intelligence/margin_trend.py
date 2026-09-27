"""Quarterly margin trend classification — reuses
`pl_intelligence/margin_trends.py::classify_margin_direction()` outright
rather than reimplementing the EXPANSION/STABLE/COMPRESSION/VOLATILE/
INSUFFICIENT_DATA logic for a second cadence.
"""
from __future__ import annotations

from app.calculations.engine import safe_div
from app.calculations.pl_intelligence.margin_trends import classify_margin_direction


def net_margin_series(sales: dict[str, float], net_profit: dict[str, float]) -> dict[str, float]:
    """{period: net_profit/sales*100}, only for periods present in both."""
    out: dict[str, float] = {}
    for period, sale in sales.items():
        profit = net_profit.get(period)
        if profit is None:
            continue
        margin = safe_div(profit, sale)
        if margin is not None:
            out[period] = round(margin * 100, 2)
    return out


def compute_margin_trend(opm_series: dict[str, float], net_margin_series_: dict[str, float]) -> dict[str, str]:
    """Trailing-window classification for both OPM and net margin. Caller
    is expected to have already trimmed each series to the trailing N
    quarters it wants classified."""
    return {
        "opm_direction": classify_margin_direction(opm_series),
        "net_margin_direction": classify_margin_direction(net_margin_series_),
    }
