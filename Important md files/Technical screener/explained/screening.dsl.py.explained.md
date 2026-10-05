# backend/app/screening/dsl.py — Beginner Explanation

> **Source file:** `backend/app/screening/dsl.py`

---

## 1. What is this file?

Defines the data models for the Screening DSL (Domain Specific Language) — the JSON format users send to `POST /screens/run`. It also contains the parser (`parse_filter_expr`) that converts that JSON into typed Python objects the filter engine can evaluate.

---

## 2. Filter types

### ClassificationFilter

Filters on stock metadata (stored in the database — no yfinance call needed):

```python
{"type": "classification", "field": "sector", "op": "eq", "value": "Information Technology"}
{"type": "classification", "field": "market_cap_category", "op": "in", "value": ["LARGE_CAP", "MID_CAP"]}
```

Supported fields: `sector`, `macro_sector`, `market_cap_category`, `exchange`, `symbol`

### IndicatorFilter

Filters on calculated indicator values (requires yfinance fetch):

```python
{"type": "indicator", "indicator": "rsi", "field": "value", "timeframe": "1D", "op": "lt", "value": 35}
{"type": "indicator", "indicator": "bollinger", "field": "percent_b", "timeframe": "1D", "op": "lt", "value": 0.2}
```

---

## 3. Boolean grouping

```json
{
  "and": [
    {"type": "indicator", "indicator": "rsi", ...},
    {"or": [
      {"type": "classification", "field": "sector", "op": "eq", "value": "Healthcare"},
      {"type": "classification", "field": "sector", "op": "eq", "value": "Technology"}
    ]}
  ]
}
```

`AndGroup` and `OrGroup` are plain Python dataclasses (not Pydantic) because they need to be recursive — Pydantic model recursion requires forward references and `model_rebuild()`, which is more complex than needed here.

---

## 4. ScoreCriterionSpec (added Phase 5)

```python
class ScoreCriterionSpec(BaseModel):
    indicator: str
    field: str = "value"
    timeframe: str = "1D"
    weight: float = 1.0
    direction: Literal["lower_is_better", "higher_is_better"] = "lower_is_better"
    range_min: float = 0.0
    range_max: float = 100.0
```

Used in `ScreenDSL.score_by`. When present, each matched stock gets a `score` field in the results. See `scoring.engine.py.explained.md` for the formula.

---

## 5. ScreenDSL — the top-level request body

```python
class ScreenDSL(BaseModel):
    universe: str = "NIFTY_50"
    filters: dict | None = None       # raw JSON, parsed by screening_service
    rank_by: RankSpec | None = None   # sort results by one indicator field
    score_by: list[ScoreCriterionSpec] | None = None  # compute composite score
    extra_indicators: list[ExtraIndicatorSpec] | None = None  # always-fetch for display
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
```

`filters` stays as raw `dict` (not parsed here) because the DSL parser can raise validation errors that are better handled inside `ScreeningService` with proper error propagation.

`extra_indicators` lists additional indicators to always compute and include in result data, even when they are not part of the filter expression. This is used by the RSI Momentum combined scan to always return BB, MACD, and Volume data for display in the results table regardless of which specific filters are active.

---

## 6. `extract_indicator_needs`

```python
def extract_indicator_needs(expr: FilterExpr | None) -> set[tuple[str, str]]:
```

Walks the filter tree and collects every `(indicator_name, timeframe)` pair needed. Used by `ScreeningService` to fetch only the indicators actually required — not all possible indicators. This is the "cheap filter first" optimization: classification filters run for free, indicator fetches only happen for the indicators in use.
