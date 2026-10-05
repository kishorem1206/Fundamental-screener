"""Quarterly Growth Score — recent quarterly performance given priority over
the annual (FY) growth CAGRs `scoring.py::_growth_score()` alone would use.

User's explicit brief (2026-09-27): "past performance matters to some
extent [but] recent performance gives you the current situation of the
stock" — an FY-only growth score can hide a real recent slowdown behind a
strong multi-year CAGR (confirmed live: Anthem Biosciences' revenue_cagr_3y
of 26% scored ~93/100, while its trailing 4 quarters of revenue are flat to
down against the 4 quarters before that — a real deceleration the annual
number never shows).

Method: TTM-style block comparison, not per-quarter YoY. Takes the trailing
12 `qtr_*` quarters (or however many are on record, min 8), splits them into
up to three 4-quarter blocks (recent / middle / oldest), and compares each
consecutive pair as % growth (recent-vs-middle, middle-vs-oldest), weighting
the recent comparison higher. Deliberately NOT single-quarter YoY averaged
over 8 points — a lumpy one-off quarter (a tax credit, an FX gain) then
dominates one 1/8th-weighted term instead of being smoothed inside a
4-quarter sum, which is why an early version of this using per-quarter YoY
still scored Anthem ~90 despite its real recent slowdown.

Revenue/net-profit/EPS carry the same 0.35/0.30/0.20 weights
GROWTH_SCORE_CONFIG's annual CAGR score uses for those three. The 4th slot
— annual growth gives it to fcf_cagr_3y (0.15), which has no quarterly
equivalent (Screener's quarterly table has no cash-flow statement) — goes
instead to OPERATING MARGIN TREND (2026-09-29, explicit user request: "you
are considering OPM% as well right? ... that's as important as others...
whether it's increasing or decreasing"). Revenue/profit growing while OPM
is contracting is a materially different, weaker story than the same
growth with margins expanding — `classify_margin_direction()` already
existed for the Quarterly Intelligence tab's own display
(`quarterly_intelligence/margin_trend.py`) but was never folded into a
SCORE anywhere; this is that.

Margin is a ratio, not an absolute figure, so it can't use the same
"% growth of a 4Q block SUM" math the other three do (summing a percentage
across quarters is meaningless) — `_block_avg_delta_pp()` compares 4Q block
AVERAGES instead, as a percentage-POINT delta, scored on its own threshold
ladder (`_MARGIN_TREND_SCORE_CONFIG`), not GROWTH_SCORE_CONFIG's CAGR bands
(which are for percent-growth values, wrong units for a pp-delta)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.quarterly_intelligence.series import quarter_series
from app.calculations.scoring import GROWTH_SCORE_CONFIG, _score_metric

_METRIC_KEYS = {
    "revenue": ("qtr_sales", "revenue_cagr_3y"),
    "pat": ("qtr_net_profit", "pat_cagr_3y"),
    "eps": ("qtr_eps", "eps_cagr_3y"),
}
_MARGIN_METRIC_KEY = "qtr_opm"
_METRIC_WEIGHTS = {"revenue": 0.35, "pat": 0.30, "eps": 0.20, "margin": 0.15}

# Recent-4Q-avg-OPM minus prior-4Q-avg-OPM, in percentage points -> 0-100
# score. Calibrated against real quarterly OPM swings seen this session
# (Voltas/WeWork-shaped: a 5-10pp swing across 4 quarters is a genuine
# structural shift, not noise; under ~2pp is closer to normal quarter-to-
# quarter wobble and scores near-neutral either direction).
_MARGIN_TREND_SCORE_CONFIG = [(-10, 5), (-5, 25), (-2, 45), (0, 55), (2, 70), (5, 85), (10, 95)]

_MIN_QUARTERS = 8       # one full recent-vs-prior 4Q block comparison
_FULL_WINDOW = 12       # recent-vs-middle AND middle-vs-oldest
_RECENT_BLOCK_WEIGHT = 0.7  # vs. 0.3 for the older (middle-vs-oldest) comparison


def _block_growth_pct(values: list[float]) -> list[float]:
    """`values` oldest-to-newest, one entry per available 4Q block sum,
    consecutive blocks only (most-recent-first order dropped here — caller
    reads blocks[-1] as the newest). Returns [] if fewer than 2 blocks.

    Blocks are anchored to the END of `values` (the most recent quarter),
    so a leftover remainder (len(values) not a multiple of 4) is dropped
    from the OLDEST end. Real bug found live on Anthem Biosciences (9
    quarters on record): anchoring from the start instead silently dropped
    the single newest quarter — Q1 FY27 — from every block sum, which is
    exactly the quarter this whole feature exists to weigh most heavily."""
    n_blocks = len(values) // 4
    if n_blocks < 2:
        return []
    trimmed = values[-(n_blocks * 4):]
    block_sums = [sum(trimmed[i * 4:(i + 1) * 4]) for i in range(n_blocks)]
    growth = []
    for i in range(1, len(block_sums)):
        prev, cur = block_sums[i - 1], block_sums[i]
        if prev:
            growth.append((cur - prev) / abs(prev) * 100)
        else:
            growth.append(None)
    return growth  # oldest comparison first, most recent comparison last


def _block_avg_delta_pp(values: list[float]) -> list[float]:
    """Same recency-anchoring as `_block_growth_pct()` (a leftover
    remainder is dropped from the OLDEST end, never the newest), but for a
    MARGIN series already expressed as a percentage: each block is
    AVERAGED, not summed, and the comparison is a plain percentage-point
    difference between consecutive block averages, not a percent-of-
    percent growth rate (which is meaningless applied to a ratio)."""
    n_blocks = len(values) // 4
    if n_blocks < 2:
        return []
    trimmed = values[-(n_blocks * 4):]
    block_avgs = [sum(trimmed[i * 4:(i + 1) * 4]) / 4 for i in range(n_blocks)]
    return [block_avgs[i] - block_avgs[i - 1] for i in range(1, len(block_avgs))]


def _weighted_growth_pct(growth: list[float | None]) -> float | None:
    """`growth` oldest-comparison-first (see `_block_growth_pct`). One
    comparison -> that value. Two -> 0.7 recent / 0.3 older, matching the
    "recent 4 quarters matter most, then the previous 4" brief. Generic
    over units — also used to blend `_block_avg_delta_pp()`'s
    percentage-point deltas for the margin-trend component, not just
    `_block_growth_pct()`'s percent-growth values."""
    growth = [g for g in growth if g is not None]
    if not growth:
        return None
    if len(growth) == 1:
        return growth[0]
    return _RECENT_BLOCK_WEIGHT * growth[-1] + (1 - _RECENT_BLOCK_WEIGHT) * growth[-2]


def compute_quarterly_growth(db: Session, company_id: str, statement_type: str = "CONSOLIDATED",
                             allow_fallback: bool = True) -> dict | None:
    """None if fewer than 8 quarters are on record for every tracked metric
    (too little data for even one recent-vs-prior comparison) — caller
    falls back to the annual-only growth score, same degrade-gracefully
    contract as every other calc module here.

    `allow_fallback=False` (quick_analysis's DB-persisted Screener path,
    2026-09-28 — see quick_analysis/screener_quarterly_fallback.py) disables
    the STANDALONE fallback below: that caller's own brief is "consolidated
    only, leave it blank otherwise," same `allow_fallback` contract
    `quarterly_intelligence/__init__.py::compute_quarterly_intelligence()`
    already uses for the identical concept."""
    per_metric_growth: dict[str, float] = {}
    per_metric_scores: dict[str, float] = {}
    quarters_used = 0

    for name, (metric_key, config_key) in _METRIC_KEYS.items():
        series = quarter_series(db, company_id, metric_key, statement_type)
        if not series and allow_fallback and statement_type != "STANDALONE":
            series = quarter_series(db, company_id, metric_key, "STANDALONE")
        periods = sorted(series.keys())[-_FULL_WINDOW:]
        values = [series[p] for p in periods]
        quarters_used = max(quarters_used, len(values))
        growth = _weighted_growth_pct(_block_growth_pct(values))
        if growth is None:
            continue
        per_metric_growth[name] = round(growth, 1)
        per_metric_scores[name] = _score_metric(growth, GROWTH_SCORE_CONFIG[config_key])

    # OPM trend — pp-delta, not percent-growth, so scored on its own
    # threshold ladder (see module docstring). Not part of the
    # quarters_used/_MIN_QUARTERS gate above: OPM is a secondary lens on
    # top of revenue/pat/eps, not a substitute — if THOSE don't clear the
    # 8-quarter bar this function still returns None regardless of
    # whether margin data happens to be available.
    margin_series = quarter_series(db, company_id, _MARGIN_METRIC_KEY, statement_type)
    if not margin_series and allow_fallback and statement_type != "STANDALONE":
        margin_series = quarter_series(db, company_id, _MARGIN_METRIC_KEY, "STANDALONE")
    margin_periods = sorted(margin_series.keys())[-_FULL_WINDOW:]
    margin_values = [margin_series[p] for p in margin_periods]
    margin_delta = _weighted_growth_pct(_block_avg_delta_pp(margin_values))
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
        "statement_type": statement_type,
        "basis": "recent4_vs_middle4_weighted" if quarters_used >= _FULL_WINDOW else "recent4_vs_prior4",
    }
