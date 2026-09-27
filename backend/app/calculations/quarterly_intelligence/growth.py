"""QoQ (sequential) and YoY growth over a quarterly `{period: value}` series
(periods are ISO quarter-end dates, e.g. "2026-03-31", as produced by
`quarterly_results_client.py`/`series.py::quarter_series()`).
"""
from __future__ import annotations

from datetime import date


def _pct_change(old: float | None, new: float | None) -> float | None:
    if old is None or new is None or old == 0:
        return None
    return round((new - old) / abs(old) * 100, 2)


def qoq_growth(series: dict[str, float]) -> dict[str, float]:
    """{period: pct_change_vs_immediately_preceding_period_on_record}.
    "Preceding" is positional (sorted order), not date-arithmetic — safe
    because a `qtr_*` series only ever contains actual quarter-end periods,
    never a gap-filled calendar sequence."""
    periods = sorted(series.keys())
    out: dict[str, float] = {}
    for i in range(1, len(periods)):
        prev_period, cur_period = periods[i - 1], periods[i]
        change = _pct_change(series.get(prev_period), series.get(cur_period))
        if change is not None:
            out[cur_period] = change
    return out


def qoq_delta_pp(series: dict[str, float]) -> dict[str, float]:
    """For a series that's ALREADY a percentage (e.g. OPM) — the raw
    percentage-point delta vs the immediately preceding period, not a
    percent-change-of-a-percent (which `qoq_growth()` would give)."""
    periods = sorted(series.keys())
    out: dict[str, float] = {}
    for i in range(1, len(periods)):
        prev_v, cur_v = series.get(periods[i - 1]), series.get(periods[i])
        if prev_v is None or cur_v is None:
            continue
        out[periods[i]] = round(cur_v - prev_v, 2)
    return out


def yoy_growth(series: dict[str, float]) -> dict[str, float]:
    """{period: pct_change_vs_the_same_quarter_one_year_earlier}. Looked up
    by date (period minus 1 year), not a fixed 4-quarter index offset —
    a missing quarter in the ledger must not silently shift the comparison
    to the wrong quarter."""
    out: dict[str, float] = {}
    for period, value in series.items():
        try:
            d = date.fromisoformat(period)
        except ValueError:
            continue
        try:
            prior_year_date = d.replace(year=d.year - 1)
        except ValueError:
            # Feb 29 on a non-leap prior year — not a real concern for
            # quarter-end dates (always month-end), kept defensive anyway.
            continue
        prior_value = series.get(prior_year_date.isoformat())
        change = _pct_change(prior_value, value)
        if change is not None:
            out[period] = change
    return out
