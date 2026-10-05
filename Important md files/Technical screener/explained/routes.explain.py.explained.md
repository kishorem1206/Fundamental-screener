# backend/app/routes/explain.py — Beginner Explanation

> **Source file:** `backend/app/routes/explain.py`

---

## 1. What is this file?

Defines `POST /stocks/explain`. Accepts a stock object, filter expression, and indicator snapshot, then delegates to `ExplanationAgent` and returns the explanation.

---

## 2. Endpoint

```
POST /stocks/explain
Content-Type: application/json

{
  "stock": {"symbol": "INFY", "company_name": "Infosys Limited"},
  "filters": {"and": [{"type":"indicator","indicator":"rsi","field":"value","timeframe":"1D","op":"lt","value":40}]},
  "indicators": {"rsi_1D": {"value": 35.4}}
}
```

---

## 3. Request body model

```python
class ExplainRequest(BaseModel):
    stock: dict
    filters: dict | None = None    # null = explain "no filters applied"
    indicators: dict = {}          # defaults to empty (will produce "data unavailable" reasons)
```

`filters` is optional so you can ask "explain why this stock is interesting" without a specific filter expression.

---

## 4. Why `POST` not `GET`?

The filter expression and indicator data are structured JSON — too complex for URL query parameters. `POST` with a JSON body is the appropriate HTTP method for structured input even though this is a read operation.
