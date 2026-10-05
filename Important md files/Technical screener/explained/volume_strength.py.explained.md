# backend/app/indicators/plugins/volume_strength.py — Beginner Explanation

> **Source file:** `backend/app/indicators/plugins/volume_strength.py`

---

## 1. What is this file?

An indicator plugin that measures how today's trading volume compares to the stock's recent average. A stock trading at 3× its normal volume is very different from one trading at 50% of its normal volume — this plugin captures that difference and classifies it into four tiers.

---

## 2. What does it output?

Four values are stored in `indicators["volume_strength_1D"]`:

| Field | Type | Meaning |
|---|---|---|
| `volume_today` | float | Today's raw volume (shares traded) |
| `avg_volume` | float | Average volume over the previous 30 trading days |
| `volume_ratio` | float | `(today / avg) × 100` — 100 means equal to average |
| `volume_score` | float | 0/2/3/5 — a discrete score for the scoring engine |

The `signal` string is the classification: `BELOW_AVERAGE`, `ABOVE_AVERAGE`, `STRONG`, or `EXCEPTIONAL`.

---

## 3. Classification thresholds

| Signal | Volume Ratio | Score |
|---|---|---|
| `BELOW_AVERAGE` | < 100% | 0 |
| `ABOVE_AVERAGE` | 100–149% | 2 |
| `STRONG` | 150–199% | 3 |
| `EXCEPTIONAL` | ≥ 200% | 5 |

---

## 4. Key sections explained

### Lookback window

```python
LOOKBACK = 30
prev_bars = bars[-(LOOKBACK + 1):-1]  # last 30 bars excluding today
```

`bars[-31:-1]` selects the 30 bars that end just before today. Slice notation: `-31` is 31 positions from the end, `-1` is "up to but not including the last element." This ensures today's volume does not inflate its own average.

### Minimum data guard

```python
if len(bars) < LOOKBACK + 1:
    return IndicatorResult(..., signal="UNKNOWN")
```

We need at least 31 bars: 30 for the average plus 1 for today. Fewer than that → all values are `None`, signal is `UNKNOWN`. The filter engine treats UNKNOWN as SKIP (the stock passes through without being filtered).

### Zero-average guard

```python
if avg_volume == 0:
    return IndicatorResult(..., signal="UNKNOWN")
```

If all previous 30 bars had zero volume (halted stock, missing data), division would produce `ZeroDivisionError`. We detect this case first and return UNKNOWN instead of crashing.

### Scoring as a float

```python
"volume_score": float(volume_score),
```

The scoring engine reads this field as a float for normalisation. We explicitly cast the integer (0/2/3/5) to float so it is consistent with how RSI value and %B are stored.

---

## 5. How volume_score contributes to the overall score

The scoring engine ([`backend/app/scoring/engine.py`](../scoring/engine.py)) normalises `volume_score` from `[0, 5]` to `[0, 1]` and multiplies by weight `2/19 ≈ 0.1053`. At full score (5/5), this contributes `(0.1053 / (1 + 1 + 0.1053)) × 100 ≈ 5 points` out of 100 to the overall stock score.

---

## 6. How it plugs into the architecture

1. **Plugin** (`volume_strength.py`) exposes `volume_strength_plugin` singleton.
2. **Registry** (`registry.py`) registers it under the key `"volume_strength"`.
3. **ScreeningService** calls `indicator_registry.get("volume_strength").calculate(bars, params)` when a filter or scoring criterion references it.
4. **Filter engine** reads `indicators["volume_strength_1D"]["volume_ratio"]` or `["volume_score"]` to evaluate user-defined filter conditions.
5. **Scoring engine** reads `indicators["volume_strength_1D"]["volume_score"]` as a ScoreCriterion contribution.
6. **Frontend** shows `Vol Ratio` and `Vol Score` columns in the results table with colour-coded EXCEPTIONAL/STRONG/ABOVE AVG/BELOW AVG labels.
