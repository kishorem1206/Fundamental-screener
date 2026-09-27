"""Tests for `app/calculations/quarterly_intelligence/` — pure-function
tests for growth/margin-trend/flags, no DB needed, same style as
`test_pnl_history_growth_widget.py`.
"""
from __future__ import annotations

from app.calculations.quarterly_intelligence import margin_trend as qi_margin_trend
from app.calculations.quarterly_intelligence.flags import (
    margin_inflection_flags,
    sequential_deceleration_flags,
)
from app.calculations.quarterly_intelligence.growth import qoq_delta_pp, qoq_growth, yoy_growth


def test_qoq_growth_basic_sequence():
    series = {"2025-06-30": 100.0, "2025-09-30": 110.0, "2025-12-31": 99.0}
    result = qoq_growth(series)
    assert result["2025-09-30"] == 10.0
    assert result["2025-12-31"] == -10.0
    assert "2025-06-30" not in result  # no preceding period to compare against


def test_qoq_delta_pp_is_a_point_delta_not_a_percent_change():
    series = {"2025-09-30": 20.0, "2025-12-31": 18.0}
    assert qoq_delta_pp(series) == {"2025-12-31": -2.0}


def test_yoy_growth_looks_back_one_year_by_date_not_index():
    """A missing quarter in the ledger must not silently shift the
    comparison to the wrong quarter — YoY is looked up by date
    (period - 1 year), not a fixed 4-quarter positional offset."""
    series = {
        "2025-03-31": 100.0,
        # Jun 2025 missing on purpose — its 2026 counterpart must be skipped,
        # never wrongly compared against a different quarter.
        "2026-03-31": 150.0,
        "2026-06-30": 140.0,
    }
    result = yoy_growth(series)
    assert result["2026-03-31"] == 50.0  # vs 2025-03-31
    assert "2026-06-30" not in result    # 2025-06-30 has no data on record
    assert "2026-09-30" not in result   # 2025-09-30 exists but that's not a YoY match...


def test_yoy_growth_matches_same_quarter_prior_year_when_present():
    series = {"2025-09-30": 120.0, "2026-09-30": 132.0}
    result = yoy_growth(series)
    assert result["2026-09-30"] == 10.0


def test_margin_trend_reuses_pl_intelligence_classifier():
    """Confirms this package calls the existing pl_intelligence classifier
    rather than reimplementing EXPANSION/STABLE/COMPRESSION/VOLATILE logic
    for a second cadence."""
    from app.calculations.pl_intelligence.margin_trends import classify_margin_direction as pl_classifier
    assert qi_margin_trend.classify_margin_direction is pl_classifier


def test_net_margin_series_only_covers_periods_present_in_both():
    sales = {"2025-09-30": 100.0, "2025-12-31": 200.0}
    net_profit = {"2025-09-30": 10.0}
    result = qi_margin_trend.net_margin_series(sales, net_profit)
    assert result == {"2025-09-30": 10.0}


def test_sequential_deceleration_fires_after_two_positive_quarters():
    qoq = {"2025-06-30": 5.0, "2025-09-30": 8.0, "2025-12-31": -3.0}
    flags = sequential_deceleration_flags(qoq)
    assert len(flags) == 1
    assert flags[0]["period"] == "2025-12-31"
    assert flags[0]["flag"] == "sequential_deceleration"


def test_margin_inflection_fires_beyond_threshold():
    qoq_opm = {"2025-09-30": 1.0, "2025-12-31": 4.0}
    flags = margin_inflection_flags(qoq_opm)
    assert len(flags) == 1
    assert flags[0]["period"] == "2025-12-31"
