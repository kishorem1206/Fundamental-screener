# backend/app/agents/scoring_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/scoring_agent.py`

---

## 1. What is this file?

Defines `ScoringAgent` — the agent wrapper around the scoring engine. It receives a `SCORE_STOCK` task containing indicator data and an optional list of custom scoring criteria, delegates to `score_stock()`, and returns the result.

---

## 2. Task type: `SCORE_STOCK`

**Payload:**
```json
{
  "indicators": {
    "rsi_1D": {"value": 35.4, "signal": "NEUTRAL"},
    "bollinger_1D": {"percent_b": 0.12, "upper": 1234}
  },
  "criteria": [
    {"indicator": "rsi", "field": "value", "timeframe": "1D",
     "weight": 1.0, "direction": "lower_is_better",
     "range_min": 0, "range_max": 100}
  ]
}
```

`criteria` is optional — omitting it uses the default (RSI + %B, equal weight).

**Result:**
```json
{
  "score": 64.6,
  "completeness": 1.0,
  "breakdown": {"rsi_1D_value": 64.6}
}
```

---

## 3. Where it's used

- Called directly when you want to score a single stock outside of a screen.
- Scoring in bulk screens is handled inline by `ScreeningService` (not via the agent) to avoid message-bus overhead for 500 stocks.

---

## 4. Criteria validation

```python
criteria = [ScoreCriterion(**c) for c in raw_criteria]
```

`**c` unpacks each dict as keyword arguments into `ScoreCriterion`. If an unknown key is passed, Python raises a `TypeError` caught by the `except` block and returned as a `VALIDATION_ERROR`.
