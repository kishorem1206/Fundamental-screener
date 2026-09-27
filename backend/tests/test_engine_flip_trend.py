"""Regression tests for `app/calculations/engine.py::flip_trend` — a real
bug found live: Debt/Equity is a "lower is better" metric (falling
leverage is good), but `debt_trend` was built by feeding its raw value
series straight into `trend_direction()`, which only knows UP/DOWN in
value terms. A shrinking Debt/Equity ratio (an improving balance sheet)
was therefore rendered as "Deteriorating" in red — the opposite of the
truth. Same bug class applies to inventory/receivable days and the cash
conversion cycle (CCC): falling days is an efficiency improvement, not a
decline. Payable days is the mirror case — RISING payable days is good
(more supplier credit) and must NOT be flipped.

`flip_trend()` fixes this by inverting the IMPROVING/DETERIORATING label
(STABLE/VOLATILE/INSUFFICIENT_DATA pass through unchanged) for exactly
the "lower is better" metrics, applied at the point each trend is
exposed (`debt_trend` in `compute_all()`, and `inventory_days_trend` /
`receivable_days_trend` / `ccc_trend` in `working_capital_trends()`).
"""
from __future__ import annotations

from app.calculations.engine import MetricsCalculator, flip_trend, trend_direction


def test_flip_trend_inverts_improving_and_deteriorating():
    assert flip_trend("IMPROVING") == "DETERIORATING"
    assert flip_trend("STRONGLY_IMPROVING") == "STRONGLY_DETERIORATING"
    assert flip_trend("DETERIORATING") == "IMPROVING"
    assert flip_trend("STRONGLY_DETERIORATING") == "STRONGLY_IMPROVING"


def test_flip_trend_passes_through_non_directional_labels():
    assert flip_trend("STABLE") == "STABLE"
    assert flip_trend("VOLATILE") == "VOLATILE"
    assert flip_trend("INSUFFICIENT_DATA") == "INSUFFICIENT_DATA"


def _calculator(balance: dict, revenue: dict | None = None) -> MetricsCalculator:
    return MetricsCalculator({
        "income": {"revenue": revenue or {}},
        "balance": balance,
    })


def test_falling_debt_to_equity_is_improving_not_deteriorating():
    """The exact bug scenario: leverage shrinking year over year."""
    calc = _calculator({
        "total_debt":   {"FY22": 800, "FY23": 700, "FY24": 600, "FY25": 500},
        "total_equity": {"FY22": 1000, "FY23": 1000, "FY24": 1000, "FY25": 1000},
    })
    d_e = calc.debt_to_equity_series()
    raw = trend_direction([d_e[y] for y in sorted(d_e)])
    assert raw in ("DETERIORATING", "STRONGLY_DETERIORATING")  # raw value-direction is "falling"

    debt_trend = flip_trend(raw)
    assert debt_trend in ("IMPROVING", "STRONGLY_IMPROVING")


def test_rising_debt_to_equity_is_deteriorating():
    """Mirror case: leverage growing year over year should stay red."""
    calc = _calculator({
        "total_debt":   {"FY22": 500, "FY23": 600, "FY24": 700, "FY25": 800},
        "total_equity": {"FY22": 1000, "FY23": 1000, "FY24": 1000, "FY25": 1000},
    })
    d_e = calc.debt_to_equity_series()
    raw = trend_direction([d_e[y] for y in sorted(d_e)])
    assert raw in ("IMPROVING", "STRONGLY_IMPROVING")  # raw value-direction is "rising"

    debt_trend = flip_trend(raw)
    assert debt_trend in ("DETERIORATING", "STRONGLY_DETERIORATING")


def test_working_capital_trends_flips_days_but_not_payables():
    revenue = {"FY22": 3650, "FY23": 3650, "FY24": 3650, "FY25": 3650}  # /365 = 10/day, clean day-count math
    calc = _calculator(
        balance={
            "inventory":          {"FY22": 600, "FY23": 550, "FY24": 500, "FY25": 450},
            "receivables":        {"FY22": 400, "FY23": 420, "FY24": 440, "FY25": 460},
            "payables":           {"FY22": 300, "FY23": 320, "FY24": 340, "FY25": 360},
            "current_assets":     {"FY22": 1000, "FY23": 1000, "FY24": 1000, "FY25": 1000},
            "current_liabilities": {"FY22": 500, "FY23": 500, "FY24": 500, "FY25": 500},
        },
        revenue=revenue,
    )
    trends = calc.working_capital_trends()

    # Inventory days falling (faster turnover) -> improving, not deteriorating.
    assert trends["inventory_days_trend"] in ("IMPROVING", "STRONGLY_IMPROVING")
    # Receivable days rising (collecting slower) -> deteriorating, not improving.
    assert trends["receivable_days_trend"] in ("DETERIORATING", "STRONGLY_DETERIORATING")
    # Payable days rising (more supplier credit) -> improving, and NOT flipped.
    assert trends["payable_days_trend"] in ("IMPROVING", "STRONGLY_IMPROVING")
    # CCC falling (shorter cash conversion cycle) -> improving, not deteriorating.
    assert trends["ccc_trend"] in ("IMPROVING", "STRONGLY_IMPROVING")
