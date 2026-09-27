"""CFO Volatility (spec §11) — never classified from one period."""
from __future__ import annotations

import statistics

_DECLINING_TOLERANCE_PCT = 5.0


def classify_cfo_volatility(cfo_series: dict[str, float]) -> dict:
    values_by_period = sorted((p, v) for p, v in cfo_series.items() if v is not None)
    values = [v for _, v in values_by_period]
    if len(values) < 3:
        return {"classification": "INSUFFICIENT_DATA", "periods_available": len(values)}

    positive_count = sum(1 for v in values if v > 0)
    negative_count = sum(1 for v in values if v < 0)
    positive_pct = round(positive_count / len(values) * 100, 1)
    stdev = round(statistics.stdev(values), 2) if len(values) >= 2 else None
    mean = statistics.fmean(values)
    coefficient_of_variation = round(abs(stdev / mean), 3) if stdev is not None and mean else None

    # Declining: the most recent 3 periods trend down, each below the prior
    # by more than the rounding-noise tolerance.
    recent = values[-3:]
    declining = all((recent[i] - recent[i - 1]) < -abs(recent[i - 1]) * _DECLINING_TOLERANCE_PCT / 100 for i in range(1, len(recent)))

    # Real bug found live-testing Maruti: a CFO that grew ~10x over 12
    # years (1840 -> 19100 Cr) has a high coefficient of variation purely
    # FROM the growth trend, not from instability — every period was
    # positive and higher than several periods back, yet the raw CoV
    # threshold alone classified it VOLATILE_CFO, which misrepresents a
    # strong secular grower as erratic. A mostly-monotonic upward series
    # (most period-over-period changes positive) reads as STABLE_CFO
    # regardless of CoV; VOLATILE_CFO is reserved for genuine up-and-down
    # swings with no consistent direction.
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    upward_share = sum(1 for d in deltas if d > 0) / len(deltas) if deltas else 0.0
    monotonic_growth = upward_share >= 0.75

    if negative_count >= 2:
        classification = "NEGATIVE_CFO_PATTERN"
    elif declining:
        classification = "DECLINING_CFO"
    elif monotonic_growth:
        classification = "STABLE_CFO"
    elif coefficient_of_variation is not None and coefficient_of_variation > 0.4:
        classification = "VOLATILE_CFO"
    else:
        classification = "STABLE_CFO"

    return {
        "classification": classification,
        "periods_available": len(values),
        "positive_period_pct": positive_pct,
        "negative_period_count": negative_count,
        "stdev": stdev,
        "coefficient_of_variation": coefficient_of_variation,
    }
