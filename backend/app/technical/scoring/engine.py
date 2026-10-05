"""
Composite scoring engine.

Each ScoreCriterion maps one indicator field to a weight + direction.
The engine normalises each value to [0,1], flips it when lower is better,
multiplies by weight, and returns a 0–100 score.

Missing values are excluded from the weighted average so partial data
still produces a meaningful score (with a completeness warning).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass
class ScoreCriterion:
    indicator: str                          # "rsi" | "bollinger"
    field: str                              # "value" | "percent_b" | "upper" …
    timeframe: str                          # "1D" | "1H" …
    weight: float                           # relative weight (any positive number)
    direction: Literal["lower_is_better", "higher_is_better"] = "lower_is_better"
    range_min: float = 0.0
    range_max: float = 100.0


# Default scoring config: RSI and %B lower-is-better; volume_score higher-is-better.
# Weight 2/19 ≈ 0.10526 means volume can contribute at most 5 points out of 100.
DEFAULT_SCORE_CRITERIA: list[ScoreCriterion] = [
    ScoreCriterion("rsi", "value", "1D", weight=1.0, direction="lower_is_better", range_min=0, range_max=100),
    ScoreCriterion("bollinger", "percent_b", "1D", weight=1.0, direction="lower_is_better", range_min=0, range_max=1),
    ScoreCriterion("volume_strength", "volume_score", "1D", weight=2/19, direction="higher_is_better", range_min=0, range_max=5),
]


@dataclass
class ScoreResult:
    score: float                            # 0–100 (higher = more interesting / better match)
    completeness: float                     # 0–1 — fraction of criteria with data
    breakdown: dict[str, float | None]      # criterion_key → normalised contribution


def score_stock(
    indicators: dict[str, dict],            # {"rsi_1D": {"value": 35.4, …}, "bollinger_1D": {…}}
    criteria: list[ScoreCriterion] | None = None,
) -> ScoreResult:
    if criteria is None:
        criteria = DEFAULT_SCORE_CRITERIA

    weighted_sum = 0.0
    total_weight = 0.0
    present = 0
    breakdown: dict[str, float | None] = {}

    for c in criteria:
        key = f"{c.indicator.lower()}_{c.timeframe.upper()}"
        ind_data = indicators.get(key, {})
        raw = ind_data.get(c.field)

        crit_key = f"{c.indicator}_{c.timeframe}_{c.field}"

        if raw is None:
            breakdown[crit_key] = None
            continue

        # Normalise to [0, 1]
        span = c.range_max - c.range_min
        if span == 0:
            norm = 0.0
        else:
            norm = max(0.0, min(1.0, (float(raw) - c.range_min) / span))

        # Flip when lower is better so that a low RSI → high contribution
        contribution = (1.0 - norm) if c.direction == "lower_is_better" else norm

        breakdown[crit_key] = round(contribution * 100, 2)
        weighted_sum += contribution * c.weight
        total_weight += c.weight
        present += 1

    if total_weight == 0:
        return ScoreResult(score=0.0, completeness=0.0, breakdown=breakdown)

    score = round((weighted_sum / total_weight) * 100, 2)
    completeness = round(present / len(criteria), 4) if criteria else 0.0

    return ScoreResult(score=score, completeness=completeness, breakdown=breakdown)
