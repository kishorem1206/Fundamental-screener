"""Margin trend engine (spec Stage 4) — classifies a margin series into
Expansion/Stable/Compression/Volatile, a stricter 4-state read than
`pnl_engine.py::_margin_stats`'s vs-average comparison (which only answers
"above/below own history", not "trending which way, and how noisily").
"""
from __future__ import annotations

import statistics

# Configurable thresholds (spec Rule 8 — never hardcode inline). A margin
# series is "Volatile" once its stdev crosses this many percentage points,
# regardless of direction; otherwise direction is read off the latest vs.
# first value in the window.
_VOLATILITY_STDEV_PP = 3.0
_STABLE_BAND_PP = 1.0  # total swing (last - first) within this = "Stable"


def classify_margin_direction(margin_series: dict[str, float]) -> str:
    """`margin_series`: {period: margin_pct}, at least 2 periods needed.
    Returns "EXPANSION" | "STABLE" | "COMPRESSION" | "VOLATILE" |
    "INSUFFICIENT_DATA"."""
    values = [v for _, v in sorted(margin_series.items()) if v is not None]
    if len(values) < 2:
        return "INSUFFICIENT_DATA"

    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
    if stdev >= _VOLATILITY_STDEV_PP:
        return "VOLATILE"

    swing = values[-1] - values[0]
    if abs(swing) <= _STABLE_BAND_PP:
        return "STABLE"
    return "EXPANSION" if swing > 0 else "COMPRESSION"
