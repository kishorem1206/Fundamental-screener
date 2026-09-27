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

Only revenue/net-profit/EPS are used (weights carried over from
GROWTH_SCORE_CONFIG's annual revenue/pat/eps weights, renormalized without
its fcf_cagr_3y term — no quarterly FCF field exists, Screener's quarterly
table has no cash-flow statement)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.quarterly_intelligence.series import quarter_series
from app.calculations.scoring import GROWTH_SCORE_CONFIG, _score_metric

_METRIC_KEYS = {
    "revenue": ("qtr_sales", "revenue_cagr_3y"),
    "pat": ("qtr_net_profit", "pat_cagr_3y"),
    "eps": ("qtr_eps", "eps_cagr_3y"),
}
# fcf_cagr_3y's 0.15 dropped (no quarterly cash-flow data); the remaining
# revenue/pat/eps weights (0.35/0.3/0.2) renormalized to sum to 1.0.
_METRIC_WEIGHTS = {"revenue": 0.412, "pat": 0.353, "eps": 0.235}

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


def _weighted_growth_pct(growth: list[float | None]) -> float | None:
    """`growth` oldest-comparison-first (see `_block_growth_pct`). One
    comparison -> that value. Two -> 0.7 recent / 0.3 older, matching the
    "recent 4 quarters matter most, then the previous 4" brief."""
    growth = [g for g in growth if g is not None]
    if not growth:
        return None
    if len(growth) == 1:
        return growth[0]
    return _RECENT_BLOCK_WEIGHT * growth[-1] + (1 - _RECENT_BLOCK_WEIGHT) * growth[-2]


def compute_quarterly_growth(db: Session, company_id: str, statement_type: str = "CONSOLIDATED") -> dict | None:
    """None if fewer than 8 quarters are on record for every tracked metric
    (too little data for even one recent-vs-prior comparison) — caller
    falls back to the annual-only growth score, same degrade-gracefully
    contract as every other calc module here."""
    per_metric_growth: dict[str, float] = {}
    per_metric_scores: dict[str, float] = {}
    quarters_used = 0

    for name, (metric_key, config_key) in _METRIC_KEYS.items():
        series = quarter_series(db, company_id, metric_key, statement_type)
        if not series and statement_type != "STANDALONE":
            series = quarter_series(db, company_id, metric_key, "STANDALONE")
        periods = sorted(series.keys())[-_FULL_WINDOW:]
        values = [series[p] for p in periods]
        quarters_used = max(quarters_used, len(values))
        growth = _weighted_growth_pct(_block_growth_pct(values))
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
        "statement_type": statement_type,
        "basis": "recent4_vs_middle4_weighted" if quarters_used >= _FULL_WINDOW else "recent4_vs_prior4",
    }
