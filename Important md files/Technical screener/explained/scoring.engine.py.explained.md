# backend/app/scoring/engine.py — Beginner Explanation

> **Source file:** `backend/app/scoring/engine.py`

---

## 1. What is this file?

The composite scoring engine. Given a stock's indicator values and a list of `ScoreCriterion` objects, it produces a single 0–100 score representing how "interesting" the stock is (higher = better match for the configured criteria).

Used by `ScoringAgent` (for individual stock scoring) and by `ScreeningService` (when `score_by` is set in the screen DSL).

---

## 2. Key concepts

### ScoreCriterion

```python
@dataclass
class ScoreCriterion:
    indicator: str          # "rsi" | "bollinger"
    field: str              # "value" | "percent_b" | ...
    timeframe: str          # "1D" | "1H" | ...
    weight: float           # relative importance (any positive number)
    direction: Literal["lower_is_better", "higher_is_better"]
    range_min: float        # expected minimum (e.g. 0 for RSI)
    range_max: float        # expected maximum (e.g. 100 for RSI)
```

### ScoreResult

```python
@dataclass
class ScoreResult:
    score: float            # 0–100 final weighted score
    completeness: float     # 0–1 fraction of criteria that had data
    breakdown: dict         # per-criterion normalised contributions
```

---

## 3. The scoring formula

For each criterion that has a value:

```
normalised = clamp((raw - range_min) / (range_max - range_min), 0, 1)
```

This converts the raw value to a 0–1 scale within the expected range.

```
if direction == "lower_is_better":
    contribution = (1 - normalised) * weight
else:
    contribution = normalised * weight
```

So a RSI of 25 (very low) with `lower_is_better` and range [0,100]:
- `normalised = 0.25`
- `contribution = (1 - 0.25) * weight = 0.75 * weight`  → high contribution

Final score:
```
score = (sum of contributions / sum of weights) * 100
```

---

## 4. Default criteria

```python
DEFAULT_SCORE_CRITERIA = [
    ScoreCriterion("rsi",             "value",        "1D", weight=1.0,   direction="lower_is_better",  range_min=0, range_max=100),
    ScoreCriterion("bollinger",       "percent_b",    "1D", weight=1.0,   direction="lower_is_better",  range_min=0, range_max=1),
    ScoreCriterion("volume_strength", "volume_score", "1D", weight=2/19,  direction="higher_is_better", range_min=0, range_max=5),
]
```

| Criterion | Direction | Max contribution |
|---|---|---|
| RSI | lower is better (oversold) | ~47.5 pts |
| Bollinger %B | lower is better (near lower band) | ~47.5 pts |
| Volume Score | higher is better (0/2/3/5) | ~5 pts |

### Why weight `2/19` for volume?

At full volume score (5/5, normalised to 1.0), the contribution to the final score is:
```
(weight / total_weights) * 100 = (2/19) / (1 + 1 + 2/19) * 100 ≈ 5%
```
This means volume contributes at most **5 points out of 100** — a tiebreaker, not a dominant factor.

---

## 5. Partial data handling

If a criterion's value is `None` (data not available), it is excluded from both the numerator and denominator. The `completeness` field tells you what fraction of criteria had data — so you know if the score was computed on partial information.
