"""Doubling-velocity tests (P&L Analysis Engine plan, Milestone 2) — Stage
31's edge-case list: already >2x, never doubles, declining, invalid/negative
CAGR."""
from __future__ import annotations

from app.calculations.pl_intelligence.doubling_velocity import (
    cagr_doubling,
    classify_doubling_speed,
    compare_doubling_velocity,
    empirical_doubling,
)


def test_empirical_doubling_walks_backward_from_latest():
    series = {"2018-03-31": 100.0, "2019-03-31": 130.0, "2020-03-31": 180.0,
              "2021-03-31": 210.0, "2022-03-31": 250.0}
    result = empirical_doubling(series)
    assert result is not None
    # Anchored to the latest period (2022: 250) walking backward for the
    # most recent period at/below half of it (125) — 2021's 210, 2020's
    # 180 and 2019's 130 are all still above 125, so the walk keeps going
    # until 2018's 100.
    assert result["start_year"] == 2018
    assert result["end_year"] == 2022
    assert result["doubling_years"] == 4


def test_empirical_doubling_ignores_a_loss_year_reference_instead_of_blocking_entirely():
    # Real-world regression case: GNFC's PAT series starts with a loss
    # year (FY2015: -452 Cr) — the old earliest-forward algorithm used
    # that as its sole reference and bailed out entirely ("Not doubling"),
    # even though PAT clearly grew to multiples of its post-loss level.
    # Anchoring to latest and walking backward skips the negative/zero
    # year rather than stopping on it, and finds the real 2016->2017
    # doubling further back.
    series = {"2015-03-31": -452.0, "2016-03-31": 173.0, "2017-03-31": 521.0}
    result = empirical_doubling(series)
    assert result == {"doubling_years": 1, "start_year": 2016, "end_year": 2017}


def test_empirical_doubling_revenue_already_above_2x():
    series = {"2018-03-31": 100.0, "2019-03-31": 250.0}
    result = empirical_doubling(series)
    assert result == {"doubling_years": 1, "start_year": 2018, "end_year": 2019}


def test_empirical_doubling_never_doubles():
    series = {"2018-03-31": 100.0, "2019-03-31": 110.0, "2020-03-31": 150.0}
    assert empirical_doubling(series) is None


def test_empirical_doubling_declining_series():
    series = {"2018-03-31": 100.0, "2019-03-31": 90.0, "2020-03-31": 70.0}
    assert empirical_doubling(series) is None


def test_empirical_doubling_negative_or_zero_reference():
    assert empirical_doubling({"2018-03-31": -50.0, "2019-03-31": 100.0}) is None
    assert empirical_doubling({"2018-03-31": 0.0, "2019-03-31": 100.0}) is None


def test_empirical_doubling_insufficient_data():
    assert empirical_doubling({}) is None
    assert empirical_doubling({"2018-03-31": 100.0}) is None


def test_cagr_doubling_positive_cagr():
    # 15% CAGR -> ln(2)/ln(1.15) ≈ 4.96 years
    result = cagr_doubling(15.0)
    assert result is not None
    assert 4.9 < result < 5.0


def test_cagr_doubling_zero_or_negative_cagr_returns_none():
    assert cagr_doubling(0.0) is None
    assert cagr_doubling(-5.0) is None
    assert cagr_doubling(None) is None


def test_classify_doubling_speed_bands():
    assert classify_doubling_speed(4.0) == "FAST_GROWTH"
    assert classify_doubling_speed(7.0) == "STRONG_HEALTHY_GROWTH"
    assert classify_doubling_speed(9.0) == "STEADY_COMPOUNDER"
    assert classify_doubling_speed(12.0) == "SLOW_GROWTH"
    assert classify_doubling_speed(None) is None


def test_compare_doubling_velocity_pat_faster_means_expansion():
    # Real-world regression case: PAT doubles in 3 years, revenue in 8 —
    # PAT is compounding FASTER (fewer years), which is margin expansion,
    # not compression (a live LLM hallucination this pre-computed field
    # exists to prevent — see doubling_velocity.py's docstring).
    assert compare_doubling_velocity(revenue_doubling_years=8, pat_doubling_years=3) == "PAT_FASTER"


def test_compare_doubling_velocity_pat_slower_means_compression():
    assert compare_doubling_velocity(revenue_doubling_years=4, pat_doubling_years=9) == "PAT_SLOWER"


def test_compare_doubling_velocity_roughly_same():
    assert compare_doubling_velocity(revenue_doubling_years=6, pat_doubling_years=6.5) == "ROUGHLY_SAME"


def test_compare_doubling_velocity_missing_data():
    assert compare_doubling_velocity(None, 5) == "INSUFFICIENT_DATA"
    assert compare_doubling_velocity(5, None) == "INSUFFICIENT_DATA"
