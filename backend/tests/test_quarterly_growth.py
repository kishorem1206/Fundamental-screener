"""Tests for `app/calculations/quarterly_growth.py` — the recent-quarters-
first growth score (2026-09-27 brief). Pure-function tests for the block
math, plus a real-data regression test on Anthem Biosciences: the exact
company this feature was built to fix (its FY revenue_cagr_3y of 26% scores
~93/100 alone, hiding that its trailing 4 quarters of revenue are flat-to-
down against the 4 quarters before that)."""
from __future__ import annotations

from app.calculations.quarterly_growth import (
    _block_avg_delta_pp,
    _block_growth_pct,
    _weighted_growth_pct,
    compute_quarterly_growth,
)
from app.calculations.scoring import _annual_growth_score, _growth_score
from app.infrastructure.database import metric_store


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


# ── OPM margin trend (2026-09-29, explicit user request) ────────────────────

def test_block_avg_delta_pp_anchors_to_the_most_recent_quarter():
    # 9 values, newest last -> drop the OLDEST (index 0), same anchoring
    # discipline _block_growth_pct() already enforces.
    values = [40, 40, 40, 40, 40, 40, 40, 40, 20]  # a sharp final-quarter margin drop
    delta = _block_avg_delta_pp(values)
    # block1 = values[1:5] avg = 40; block2 = values[5:9] avg = (40+40+40+20)/4 = 35
    assert delta == [35 - 40]


def test_block_avg_delta_pp_needs_at_least_two_full_blocks():
    assert _block_avg_delta_pp([1, 2, 3, 4, 5, 6, 7]) == []
    assert _block_avg_delta_pp([1, 2, 3, 4, 5, 6, 7, 8]) != []


def test_block_avg_delta_pp_is_a_point_difference_not_a_percent_growth():
    # 20% -> 25% is a +5pp delta, NOT a +25% "growth rate" — confirms this
    # helper never runs the _block_growth_pct() percent-of-percent math.
    values = [20.0] * 4 + [25.0] * 4
    assert _block_avg_delta_pp(values) == [5.0]


def _seed_quarters(db, company_id, metric_key, values, start_year=2024):
    """8 consecutive quarter-end periods, oldest first."""
    quarters = ["03-31", "06-30", "09-30", "12-31"]
    periods = []
    y = start_year
    for i in range(len(values)):
        periods.append(f"{y}-{quarters[i % 4]}")
        if i % 4 == 3:
            y += 1
    for period, value in zip(periods, values):
        metric_store.insert_metric_value(
            db, company_id=company_id, metric_key=metric_key, period=period, value=value,
            unit="cr" if "opm" not in metric_key else "%", statement_type="CONSOLIDATED",
            source="SCREENER", source_tier=2, reported_or_calculated="REPORTED", confidence="MEDIUM",
        )


def test_margin_contraction_pulls_the_quarterly_score_down(db):
    from datetime import datetime, timezone
    from app.infrastructure.database.models import Stock
    now = datetime.now(timezone.utc)
    company_id = "TEST:QGMARGIN"
    db.add(Stock(id=company_id, symbol="QGMARGIN", exchange="TEST", company_name="QG Margin Ltd",
                 is_active=True, created_at=now, updated_at=now))
    db.flush()

    flat_growth = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]  # no revenue/pat/eps growth at all
    _seed_quarters(db, company_id, "qtr_sales", flat_growth)
    _seed_quarters(db, company_id, "qtr_net_profit", flat_growth)
    _seed_quarters(db, company_id, "qtr_eps", flat_growth)
    contracting_opm = [40.0, 40.0, 40.0, 40.0, 25.0, 25.0, 25.0, 25.0]  # -15pp block-avg contraction
    _seed_quarters(db, company_id, "qtr_opm", contracting_opm)

    result = compute_quarterly_growth(db, company_id, "CONSOLIDATED")
    assert result is not None
    assert result["growth_pct"]["margin"] == -15.0
    # revenue/pat/eps are all flat (0% growth -> neutral-ish ~55 on the
    # annual CAGR bands) — the severe margin contraction must pull the
    # blended score meaningfully below that neutral baseline.
    assert result["score"] < 40.0
