# backend/app/routes/rsi_divergence.py — Beginner Explanation

> **Source file:** `backend/app/routes/rsi_divergence.py`

---

## 1. What is this file?

Registers one FastAPI route that exposes RSI divergence scanning to the frontend and any API consumer.

**Endpoint:** `POST /rsi-divergence/scan`

---

## 2. Request body

```json
{
  "universe": "NIFTY_500",
  "pivot_left": 3,
  "pivot_right": 3,
  "max_recency_bars": 10,
  "min_bars_between": 5,
  "max_bars_between": 50,
  "min_rsi_change": 1.0,
  "min_price_chg_pct": 0.1,
  "max_pivot_rsi": 40.0,
  "min_pivot_rsi": null,
  "require_rsi_rising": false,
  "div_types": ["REGULAR_BULLISH"],
  "limit": 100,
  "offset": 0
}
```

All fields have sensible defaults so a minimal `{}` body is valid.

---

## 3. Parameter validation

Pydantic `Field` constraints prevent bad inputs:

| Parameter | Range | Notes |
|-----------|-------|-------|
| `pivot_left`, `pivot_right` | 1–10 | Swing detection sensitivity |
| `max_recency_bars` | 1–30 | How recently P2 must have occurred |
| `min_bars_between` | 2–50 | Minimum gap between P1 and P2 |
| `max_bars_between` | 5–50 | Maximum gap — same upper bound as min to allow a dual-range slider |
| `min_rsi_change` | 0–20 | Minimum RSI improvement from P1 to P2 |
| `min_price_chg_pct` | 0–10% | Minimum price movement between pivots |
| `max_pivot_rsi` | 0–100 | Filter: P2 RSI must be below this (e.g. 40 keeps oversold setups) |
| `min_pivot_rsi` | 0–100 or null | Optional lower bound on pivot RSI |
| `require_rsi_rising` | bool | If true, only return stocks where today's RSI > yesterday's RSI |
| `limit` | 1–500 | Page size |

---

## 4. require_rsi_rising

When `true`, the service applies a post-filter after retrieving cached divergence rows. Only stocks where `rsi_today > rsi_prev` are returned. This is not part of the cache key — it's cheap enough to apply in Python after cache lookup.

---

## 5. Response shape

```json
{
  "executed_at": "2026-08-23T10:00:00Z",
  "universe": "NIFTY_500",
  "total_matched": 12,
  "stocks_screened": 500,
  "execution_time_ms": 8400.0,
  "divergences": [
    {
      "symbol": "BDL",
      "div_type": "REGULAR_BULLISH",
      "status": "RECENT_CONFIRMED",
      "pivot1_rsi": 32.1,
      "pivot2_rsi": 38.5,
      "rsi_today": 56.8,
      "rsi_prev": 50.1,
      ...
    }
  ]
}
```

`total_matched` = total divergences found (may exceed `limit`). `divergences` is the page slice.
