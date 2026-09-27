"""Quick-analysis (Yahoo-only) counterpart to
`app/calculations/quarterly_growth.py` — same recent-quarters-first brief,
but reading from `fetch_financial_data()`'s `quarterly` block instead of the
Screener-sourced `qtr_*` ledger, since quick analysis has no DB ingestion
step to depend on.

Yahoo only ever exposes ~4-5 real quarters (`quarterly_financials` on
Anthem Biosciences: 2026-06-30 back to 2025-06-30, confirmed live) — far
short of the Screener module's 12-quarter block-comparison window, so this
uses `quarterly_intelligence.growth.yoy_growth()`'s single-quarter,
date-matched YoY instead of 4-quarter block sums: with only 5 quarters on
hand there's exactly one YoY point to compute (the latest quarter vs. the
same quarter a year earlier), not enough data to smooth into blocks. A
ticker with more Yahoo history (2+ YoY points) still gets the same
recent-weighted-over-older blend `quarterly_growth.py` uses, via the same
`_weighted_growth_pct()` helper.

Real bug this module exists to fix (2026-09-27): `yfinance_client.py`'s
quarterly extraction keyed every quarter by `_fy_label()` (calendar year),
so two quarters landing in the same year silently collided into one
mislabeled point — the `quarterly` block looked like it held ~2 years of
annual-ish data, not ~5 real quarters, and this feature's first pass wrongly
concluded quick analysis "has no quarterly data to work from." Fixed at the
source (`_df_to_dict_dated`/`_try_keys_dated`) before this module was built.
"""
from __future__ import annotations

from app.calculations.quarterly_growth import _METRIC_WEIGHTS, _weighted_growth_pct
from app.calculations.quarterly_intelligence.growth import yoy_growth
from app.calculations.scoring import GROWTH_SCORE_CONFIG, _score_metric

_METRIC_KEYS = {
    "revenue": ("revenue", "revenue_cagr_3y"),
    "pat": ("net_income", "pat_cagr_3y"),
    "eps": ("eps", "eps_cagr_3y"),
}
_MIN_QUARTERS = 5  # one real YoY comparison (latest quarter vs. the same quarter a year earlier)


def compute_quarterly_growth(financial_data: dict) -> dict | None:
    """None if fewer than 5 quarters are on record for every tracked
    metric — caller (`quick_analysis/scorer.py`) falls back to the annual
    growth score alone, same contract as the full-pipeline version."""
    quarterly = financial_data.get("quarterly") or {}
    per_metric_growth: dict[str, float] = {}
    per_metric_scores: dict[str, float] = {}
    quarters_used = 0

    for name, (series_key, config_key) in _METRIC_KEYS.items():
        series = {p: v for p, v in (quarterly.get(series_key) or {}).items() if v is not None}
        quarters_used = max(quarters_used, len(series))
        yoy = yoy_growth(series)
        if not yoy:
            continue
        # oldest-to-newest, at most the 2 most recent YoY points — matches
        # `_weighted_growth_pct()`'s (older, recent) contract.
        recent_points = [yoy[p] for p in sorted(yoy.keys())[-2:]]
        growth = _weighted_growth_pct(recent_points)
        if growth is None:
            continue
        per_metric_growth[name] = round(growth, 1)
        per_metric_scores[name] = _score_metric(growth, GROWTH_SCORE_CONFIG[config_key])

    if quarters_used < _MIN_QUARTERS or not per_metric_scores:
        return None

    total_w = sum(_METRIC_WEIGHTS[k] for k in per_metric_scores)
    score = sum(per_metric_scores[k] * _METRIC_WEIGHTS[k] for k in per_metric_scores) / total_w

    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "growth_pct": per_metric_growth,
        "quarters_used": quarters_used,
    }
