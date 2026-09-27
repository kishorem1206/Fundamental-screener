"""Regression tests for `app/calculations/engine.py::calculate_cagr` — a
real bug found live-testing Tata Technologies' cash-flow historical trends:
a series with a positive start but a NEGATIVE end value (legitimate for
cash-flow figures, which can cross zero) made `(end / start) ** (1/years)`
raise a fractional power of a negative number. Python doesn't raise here —
it silently returns a `complex` number, which then crashed `round()`
downstream with "type complex doesn't define __round__" inside
`historical_trends.py`'s `_window_stats()`.
"""
from __future__ import annotations

from app.calculations.engine import calculate_cagr


def test_positive_start_negative_end_returns_none_not_complex():
    result = calculate_cagr([100.0, -50.0], 1)
    assert result is None


def test_negative_start_still_returns_none():
    result = calculate_cagr([-100.0, 50.0], 1)
    assert result is None


def test_normal_positive_series_still_computes():
    result = calculate_cagr([100.0, 121.0], 2)
    assert result == 10.0


def test_zero_end_returns_none():
    result = calculate_cagr([100.0, 0.0], 1)
    assert result is None
