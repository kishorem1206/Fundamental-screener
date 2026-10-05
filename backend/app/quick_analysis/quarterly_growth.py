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

OPM trend (2026-09-29, explicit user request — same reasoning as
`quarterly_growth.py`'s own margin addition: revenue/profit growth paired
with contracting margins is a materially weaker story). Yahoo has no
`operating_margin_percent` field, so this derives one — EBITDA/Revenue,
same operating-profit concept Screener's own `qtr_opm` approximates
(Screener's "Operating Profit" = Sales - Expenses, before interest AND
depreciation, i.e. EBITDA-like) — and takes its YoY percentage-POINT delta
via `yoy_delta_pp()`, not a percent-growth rate (a ratio doesn't have a
meaningful "growth rate" of its own)."""
from __future__ import annotations

from app.calculations.quarterly_growth import _METRIC_WEIGHTS, _weighted_growth_pct
from app.calculations.quarterly_intelligence.growth import yoy_delta_pp, yoy_growth
from app.calculations.scoring import GROWTH_SCORE_CONFIG, _score_metric

_METRIC_KEYS = {
    "revenue": ("revenue", "revenue_cagr_3y"),
    "pat": ("net_income", "pat_cagr_3y"),
    "eps": ("eps", "eps_cagr_3y"),
}
_MIN_QUARTERS = 5  # one real YoY comparison (latest quarter vs. the same quarter a year earlier)
# Same threshold ladder as quarterly_growth.py's _MARGIN_TREND_SCORE_CONFIG
# — kept in sync by hand since Yahoo's EBITDA-margin proxy and Screener's
# qtr_opm measure a near-identical concept.
_MARGIN_TREND_SCORE_CONFIG = [(-10, 5), (-5, 25), (-2, 45), (0, 55), (2, 70), (5, 85), (10, 95)]


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
        if not series:
            continue
        latest_period = max(series.keys())
        yoy = yoy_growth(series)

        # Real bug found live on WeWork India (2026-09-28): Yahoo's own
        # quarterly series has a hole at 2025-06-30 (revenue/net_income/eps
        # all None that quarter) — a genuine gap, not something `yoy_growth`
        # can work around, so the CURRENT quarter (2026-06-30, the one
        # whose profit just collapsed to a loss per Screener) has no valid
        # YoY comparison. Taking "the 2 most recent AVAILABLE YoY points"
        # silently substituted Dec 2025 and Mar 2026 instead — both genuinely
        # strong quarters, but neither is the current one, so the resulting
        # 99.6 score represented a quarter and a half out of date, with
        # nothing to signal the swap. The whole point of this feature is
        # "recent performance = current situation"; scoring off stale
        # quarters because the fresh one's YoY happens to be uncomputable
        # defeats that, so this metric is skipped entirely rather than
        # silently answering a different, easier question.
        if latest_period not in yoy:
            continue

        periods_with_yoy = sorted(yoy.keys())
        idx = periods_with_yoy.index(latest_period)
        # Always anchored to the true latest quarter; the one point before
        # it (if any) is the "prior" half of `_weighted_growth_pct()`'s
        # (older, recent) blend — never anything older than that.
        recent_points = [yoy[p] for p in periods_with_yoy[max(0, idx - 1):idx + 1]]
        growth = _weighted_growth_pct(recent_points)
        if growth is None:
            continue
        per_metric_growth[name] = round(growth, 1)
        per_metric_scores[name] = _score_metric(growth, GROWTH_SCORE_CONFIG[config_key])

    # OPM trend (see module docstring) — not part of the quarters_used/
    # _MIN_QUARTERS gate above: a secondary lens on top of revenue/pat/eps,
    # not a substitute for them.
    revenue_series = {p: v for p, v in (quarterly.get("revenue") or {}).items() if v}
    ebitda_series = {p: v for p, v in (quarterly.get("ebitda") or {}).items() if v is not None}
    margin_series = {
        p: round(ebitda_series[p] / revenue_series[p] * 100, 2)
        for p in revenue_series if p in ebitda_series
    }
    if margin_series:
        margin_latest = max(margin_series.keys())
        margin_yoy = yoy_delta_pp(margin_series)
        if margin_latest in margin_yoy:
            periods_with_delta = sorted(margin_yoy.keys())
            idx = periods_with_delta.index(margin_latest)
            recent_deltas = [margin_yoy[p] for p in periods_with_delta[max(0, idx - 1):idx + 1]]
            margin_delta = _weighted_growth_pct(recent_deltas)
            if margin_delta is not None:
                per_metric_growth["margin"] = round(margin_delta, 1)
                per_metric_scores["margin"] = _score_metric(margin_delta, _MARGIN_TREND_SCORE_CONFIG)

    if quarters_used < _MIN_QUARTERS or not per_metric_scores:
        return None

    total_w = sum(_METRIC_WEIGHTS[k] for k in per_metric_scores)
    score = sum(per_metric_scores[k] * _METRIC_WEIGHTS[k] for k in per_metric_scores) / total_w

    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "growth_pct": per_metric_growth,
        "quarters_used": quarters_used,
    }
