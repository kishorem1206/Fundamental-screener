"""Tests for `app/calculations/quarterly_growth.py` — the recent-quarters-
first growth score (2026-09-27 brief). Pure-function tests for the block
math, plus a real-data regression test on Anthem Biosciences: the exact
company this feature was built to fix (its FY revenue_cagr_3y of 26% scores
~93/100 alone, hiding that its trailing 4 quarters of revenue are flat-to-
down against the 4 quarters before that)."""
from __future__ import annotations

from app.calculations.quarterly_growth import (
    _block_growth_pct,
    _weighted_growth_pct,
    compute_quarterly_growth,
)
from app.calculations.scoring import _annual_growth_score, _growth_score


def test_block_growth_anchors_to_the_most_recent_quarter():
    # 9 values -> 2 full blocks of 4 = 8 used, 1 dropped. Must drop the
    # OLDEST (index 0), never the newest (index 8) — real bug found live on
    # Anthem Biosciences (9 quarters on record): anchoring blocks from the
    # start instead silently dropped the single newest quarter from every
    # block sum, defeating the entire point of this feature.
    values = [10, 20, 30, 40, 50, 60, 70, 80, 1000]  # newest = 1000
    growth = _block_growth_pct(values)
    # block1 = values[1:5] = 20+30+40+50 = 140; block2 = values[5:9] = 60+70+80+1000 = 1210
    assert growth == [(1210 - 140) / 140 * 100]


def test_block_growth_needs_at_least_two_full_blocks():
    assert _block_growth_pct([1, 2, 3, 4, 5, 6, 7]) == []  # 7 < 8
    assert _block_growth_pct([1, 2, 3, 4, 5, 6, 7, 8]) != []  # exactly 8


def test_weighted_growth_favours_the_more_recent_comparison():
    # Two comparisons: older = +50%, recent = -50% — the blend must lean
    # toward the recent one (0.7/0.3, see _RECENT_BLOCK_WEIGHT), not average
    # them evenly, matching the brief: "recent 4 quarters matter most."
    result = _weighted_growth_pct([50.0, -50.0])
    assert result == 0.7 * -50.0 + 0.3 * 50.0
    assert result < 0  # recent decline dominates despite the equal-magnitude older gain


def test_weighted_growth_single_comparison_passes_through():
    assert _weighted_growth_pct([12.5]) == 12.5


def test_weighted_growth_empty_is_none():
    assert _weighted_growth_pct([]) is None


def test_anthem_biosciences_quarterly_growth_is_far_below_its_annual_score(db):
    # Real regression: annual revenue_cagr_3y-based growth alone scores
    # Anthem ~93 (FY23-26 revenue nearly doubled), but its trailing-4Q
    # revenue is essentially flat against the prior 4Q (-2.2%) — the
    # quarterly score must land well below the annual one.
    result = compute_quarterly_growth(db, "NSE:ANTHEM", "CONSOLIDATED")
    assert result is not None
    assert result["quarters_used"] >= 8
    assert result["score"] < 65.0  # well below the ~93 the annual-only score gives
    assert result["growth_pct"]["revenue"] < 5.0  # trailing-4Q revenue is flat/declining


def test_growth_score_blends_and_exposes_both_components():
    metrics = {"revenue_cagr_3y": 26.0, "pat_cagr_3y": 21.0, "eps_cagr_3y": 22.0, "fcf_cagr_3y": 18.0}
    annual = _annual_growth_score(metrics)
    assert annual > 85  # strong annual CAGRs alone score high

    metrics["quarterly_growth_score"] = 40.0  # a real recent slowdown
    blended = _growth_score(metrics)

    assert metrics["growth_score_annual"] == round(annual, 1)
    assert metrics["growth_score_quarterly"] == 40.0
    assert blended < annual  # the slowdown must pull the blended score down
    assert blended == round(0.65 * 40.0 + 0.35 * annual, 1) or abs(blended - (0.65 * 40.0 + 0.35 * annual)) < 0.1


def test_growth_score_falls_back_to_annual_when_no_quarterly_data():
    metrics = {"revenue_cagr_3y": 15.0, "pat_cagr_3y": 12.0}
    result = _growth_score(metrics)
    assert result == _annual_growth_score(metrics)
    assert "growth_score_quarterly" not in metrics
