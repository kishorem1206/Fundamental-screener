# backend/app/agents/explanation_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/explanation_agent.py`

---

## 1. What is this file?

Defines `ExplanationAgent` — given a stock, a filter expression, and the stock's indicator values, it produces a human-readable explanation of why the stock passed or failed the screen. This version is **fully rule-based** (no LLM). Phase 6 will upgrade it with an LLM for richer prose.

---

## 2. Task type: `EXPLAIN_RESULT`

**Payload:**
```json
{
  "stock": {"symbol": "INFY", "company_name": "Infosys Limited", "sector": "IT"},
  "filters": {"and": [
    {"type": "indicator", "indicator": "rsi", "field": "value",
     "timeframe": "1D", "op": "lt", "value": 40}
  ]},
  "indicators": {"rsi_1D": {"value": 35.4, "signal": "NEUTRAL"}}
}
```

**Result:**
```json
{
  "symbol": "INFY",
  "company_name": "Infosys Limited",
  "summary": "Infosys Limited (INFY) passed all 1 filter condition(s).",
  "passed": true,
  "reasons": [
    {
      "type": "indicator",
      "indicator": "rsi",
      "field": "value",
      "timeframe": "1D",
      "threshold": 40,
      "actual": 35.4,
      "status": "passed",
      "message": "RSI (1D) is 35.40, which is below the threshold of 40 — oversold territory — momentum is weak and a bounce may be forming"
    }
  ],
  "stats": {"passed": 1, "failed": 0, "skipped": 0}
}
```

---

## 3. How it works

### Step 1 — Parse filters

```python
expr = parse_filter_expr(raw_filters)
```

Reuses the same DSL parser as the screening engine. The filter expression becomes a tree of `AndGroup`, `OrGroup`, `IndicatorFilter`, `ClassificationFilter` objects.

### Step 2 — Walk the tree

```python
def _walk(expr, stock, indicators, reasons, depth=0):
    if isinstance(expr, AndGroup):
        for child in expr.children:
            _walk(child, ...)
    elif isinstance(expr, IndicatorFilter):
        reasons.append(_explain_indicator(expr, indicators))
```

Recursively visits every leaf node and generates one "reason" dict per condition. Group nodes (`AndGroup`, `OrGroup`) are transparent — we flatten everything into a single reason list.

### Step 3 — Generate message

For RSI conditions, `_rsi_context()` picks a contextual phrase based on actual value:

```python
if actual < 30:  return "deeply oversold — strong selling has pushed price to potential reversal zone"
if actual < 40:  return "oversold territory — momentum is weak and a bounce may be forming"
```

For Bollinger %B, `_pb_context()` does the same.

---

## 4. Status values per reason

| Status | Meaning |
|---|---|
| `"passed"` | Condition met — actual value satisfies the filter |
| `"failed"` | Condition not met |
| `"skipped — data unavailable"` | Indicator data was `None` (yfinance had no data) |

---

## 5. LLM upgrade path (Phase 6)

In Phase 6 this agent will pass the reasons list + stock context to the LLM and ask it to write a cohesive paragraph instead of the rule-based template strings. The task type and payload contract stay the same — only the internal `_explain_indicator` and `_explain_classification` methods change.
