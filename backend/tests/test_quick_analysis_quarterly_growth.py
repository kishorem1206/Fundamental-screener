"""Tests for the quick-analysis (Yahoo-only) quarterly growth path —
`app/data/yfinance_client.py`'s dated quarterly extraction and
`app/quick_analysis/quarterly_growth.py`'s scoring on top of it.

Real bug this guards against (2026-09-27): `_df_to_dict()`'s `_fy_label()`
collapses same-calendar-year quarters to one key, so a genuine 5-quarter
`quarterly_financials` DataFrame silently became a 2-entry "FY2026"/"FY2025"
dict — quick analysis then had nothing real to compute quarterly growth
from, even though Yahoo actually serves the data.
"""
from __future__ import annotations

import pandas as pd

from app.data.yfinance_client import _df_to_dict_dated, _try_keys_dated
from app.quick_analysis.quarterly_growth import compute_quarterly_growth


def test_dated_extraction_keeps_every_quarter_even_within_the_same_calendar_year():
    df = pd.DataFrame(
        {
            pd.Timestamp("2026-06-30"): [100.0],
            pd.Timestamp("2026-03-31"): [90.0],
            pd.Timestamp("2025-12-31"): [80.0],
            pd.Timestamp("2025-09-30"): [70.0],
            pd.Timestamp("2025-06-30"): [60.0],
        },
        index=["Total Revenue"],
    )
    result = _df_to_dict_dated(df, "Total Revenue")
    assert result == {
        "2026-06-30": 100.0, "2026-03-31": 90.0, "2025-12-31": 80.0,
        "2025-09-30": 70.0, "2025-06-30": 60.0,
    }
    # The old FY-bucketing path would have collapsed the two 2026 columns
    # (2026-06-30, 2026-03-31) into one "FY2026" key — assert that didn't happen.
    assert len(result) == 5


def test_try_keys_dated_falls_through_alias_list():
    df = pd.DataFrame({pd.Timestamp("2026-06-30"): [50.0]}, index=["Net Revenue"])
    assert _try_keys_dated(df, "Total Revenue", "Revenue", "Net Revenue") == {"2026-06-30": 50.0}


def _quarterly(revenue: dict, net_income: dict, eps: dict, ebitda: dict | None = None) -> dict:
    return {"quarterly": {"revenue": revenue, "net_income": net_income, "eps": eps, "ebitda": ebitda or {}}}


def test_compute_quarterly_growth_none_when_too_few_quarters():
    data = _quarterly({"2026-06-30": 100.0}, {"2026-06-30": 10.0}, {"2026-06-30": 1.0})
    assert compute_quarterly_growth(data) is None


def test_compute_quarterly_growth_single_yoy_point_from_five_quarters():
    # Anthem-shaped: 5 quarters, exactly one date-matched YoY comparison
    # (2026-06-30 vs 2025-06-30), a real recent decline.
    revenue = {
        "2026-06-30": 418.0, "2026-03-31": 611.0, "2025-12-31": 423.0,
        "2025-09-30": 550.0, "2025-06-30": 540.0,
    }
    net_income = {
        "2026-06-30": 120.0, "2026-03-31": 190.0, "2025-12-31": 93.0,
        "2025-09-30": 173.0, "2025-06-30": 136.0,
    }
    eps = {
        "2026-06-30": 2.13, "2026-03-31": 3.38, "2025-12-31": 1.65,
        "2025-09-30": 3.09, "2025-06-30": 2.42,
    }
    result = compute_quarterly_growth(_quarterly(revenue, net_income, eps))
    assert result is not None
    assert result["quarters_used"] == 5
    assert result["growth_pct"]["revenue"] == round((418.0 - 540.0) / 540.0 * 100, 1)
    assert result["score"] < 50.0  # a double-digit revenue decline scores poorly


def test_missing_prior_year_quarter_for_the_latest_period_skips_that_metric_rather_than_using_stale_quarters():
    """Real bug found live on WeWork India (2026-09-28): Yahoo's own
    quarterly data has a hole at 2025-06-30 (None for every field that
    quarter), so the CURRENT quarter (2026-06-30 — a real net-profit
    collapse per Screener, Rs 65.87cr to a Rs -4cr loss) has no valid YoY
    comparison. The old code fell back to "the 2 most recent AVAILABLE YoY
    points" — Dec 2025 and Mar 2026, both strong — and scored off those
    instead, silently answering a stale question. It must instead skip a
    metric entirely when the LATEST quarter's YoY isn't computable, never
    substitute older quarters for it."""
    net_income = {
        "2026-06-30": -4.06, "2026-03-31": 65.87, "2025-12-31": 16.79,
        "2025-09-30": 6.41, "2025-06-30": None,  # the real gap
        "2024-12-31": -83.12,
    }
    result = compute_quarterly_growth(_quarterly({}, net_income, {}))
    # No metric can be YoY-scored (revenue/eps are empty; net_income's
    # latest quarter has no valid prior-year base) -> overall None, falling
    # back to annual growth alone — not a misleadingly high score.
    assert result is None


def test_missing_prior_year_quarter_only_affects_the_metric_with_the_gap():
    """Same shape, but revenue has no gap — its metric must still score
    normally even though net_income's latest quarter is unscoreable."""
    revenue = {
        "2026-06-30": 683.83, "2026-03-31": 696.06, "2025-12-31": 634.11,
        "2025-09-30": 574.70, "2025-06-30": 535.31,
    }
    net_income = {
        "2026-06-30": -4.06, "2026-03-31": 65.87, "2025-12-31": 16.79,
        "2025-09-30": 6.41, "2025-06-30": None,
    }
    result = compute_quarterly_growth(_quarterly(revenue, net_income, {}))
    assert result is not None
    assert "revenue" in result["growth_pct"]
    assert "pat" not in result["growth_pct"]
    assert result["growth_pct"]["revenue"] == round((683.83 - 535.31) / 535.31 * 100, 1)


# ── OPM margin trend (2026-09-29, explicit user request) ────────────────────

_FIVE_Q_REVENUE = {"2026-06-30": 500.0, "2026-03-31": 490.0, "2025-12-31": 480.0,
                    "2025-09-30": 470.0, "2025-06-30": 500.0}
_FIVE_Q_NET_INCOME = {"2026-06-30": 100.0, "2026-03-31": 98.0, "2025-12-31": 96.0,
                       "2025-09-30": 94.0, "2025-06-30": 100.0}  # flat YoY PAT (neutral)


def test_margin_derived_from_yahoo_ebitda_over_revenue_and_pulls_score_down():
    ebitda = {"2026-06-30": 100.0, "2025-06-30": 200.0}  # margin 20% -> 40% collapsed to 20%
    result = compute_quarterly_growth(_quarterly(_FIVE_Q_REVENUE, _FIVE_Q_NET_INCOME, {}, ebitda))
    assert result is not None
    assert result["growth_pct"]["margin"] == -20.0  # 20% - 40%, a point delta not a percent change
    assert result["score"] < 50.0  # severe margin contraction must drag the blend down


def test_margin_missing_ebitda_data_is_simply_omitted():
    result = compute_quarterly_growth(_quarterly(_FIVE_Q_REVENUE, _FIVE_Q_NET_INCOME, {}))  # no ebitda
    assert result is not None
    assert "margin" not in result["growth_pct"]


def test_margin_alone_is_not_enough_without_the_min_quarters_gate():
    # Only 1 quarter of revenue/pat on record (below _MIN_QUARTERS=5) but a
    # full margin series — margin must never bypass the overall data-
    # sufficiency gate on its own.
    revenue = {"2026-06-30": 500.0}
    net_income = {"2026-06-30": 100.0}
    ebitda = {"2026-06-30": 100.0, "2025-06-30": 200.0}
    result = compute_quarterly_growth(_quarterly(revenue, net_income, {}, ebitda))
    assert result is None
