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


def _quarterly(revenue: dict, net_income: dict, eps: dict) -> dict:
    return {"quarterly": {"revenue": revenue, "net_income": net_income, "eps": eps}}


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
