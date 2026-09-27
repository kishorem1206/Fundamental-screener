"""Historical trends (spec §58-59): absolute/pct change, CAGR, average,
median, peak, trough over 1/3/5/7/10Y windows, for every major balance
sheet line. Pure function over an already-fetched `{period: value}` series
— no DB access, matching every other module here except `snapshot.py`.

Period sorting works for either period format this package encounters
(Screener's "2026-03-31" or yfinance's "FY2026") via the same 4-digit-year
extraction `snapshot.fiscal_year()` already established for cross-source
lookups.
"""
from __future__ import annotations

import statistics

from app.calculations.balance_sheet_intelligence.snapshot import fiscal_year
from app.calculations.engine import calculate_cagr

_DEFAULT_WINDOWS = (1, 3, 5, 7, 10)


def _sorted_periods(series: dict[str, float]) -> list[str]:
    return sorted((p for p in series if series[p] is not None), key=lambda p: fiscal_year(p) or p)


def _window_stats(series: dict[str, float], periods_sorted: list[str], window: int) -> dict:
    window_periods = periods_sorted[-(window + 1):] if len(periods_sorted) > window else periods_sorted
    values = [series[p] for p in window_periods]
    if len(values) < 2:
        return {
            "absolute_change": None, "pct_change": None, "cagr": None,
            "average": statistics.fmean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "peak": max(values) if values else None,
            "trough": min(values) if values else None,
            "periods_available": len(values),
        }

    start, end = values[0], values[-1]
    absolute_change = round(end - start, 2)
    pct_change = round((end - start) / abs(start) * 100, 2) if start else None
    cagr = calculate_cagr(values, len(values) - 1)

    return {
        "absolute_change": absolute_change,
        "pct_change": pct_change,
        "cagr": cagr,
        "average": round(statistics.fmean(values), 2),
        "median": round(statistics.median(values), 2),
        "peak": max(values),
        "trough": min(values),
        "periods_available": len(values),
    }


def compute_trends(series: dict[str, float], windows: tuple[int, ...] = _DEFAULT_WINDOWS) -> dict[str, dict]:
    """{"1Y": {...}, "3Y": {...}, ...} — a window with fewer periods than
    requested (e.g. "10Y" on a company with only 6 years on record) still
    returns its stats over however many periods ARE available, with
    `periods_available` disclosing the shortfall rather than silently
    padding or omitting the window."""
    periods_sorted = _sorted_periods(series)
    return {f"{window}Y": _window_stats(series, periods_sorted, window) for window in windows}


def compute_trends_for_lines(series_by_field: dict[str, dict[str, float]],
                              windows: tuple[int, ...] = _DEFAULT_WINDOWS) -> dict[str, dict]:
    """{field: {"1Y": {...}, ...}} — spec §58's tracked lines (cash,
    receivables, inventory, PPE, CWIP, debt, payables, equity, net worth,
    working capital) in one call; the caller assembles `series_by_field`
    from whichever mix of Screener/yfinance series is appropriate per
    field, same as every other cross-source module in this package."""
    return {field: compute_trends(series, windows) for field, series in series_by_field.items() if series}
