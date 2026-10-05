# backend/app/routes/rsi_momentum.py — Beginner Explanation

> **Source file:** `backend/app/routes/rsi_momentum.py`

---

## 1. What is this file?

Defines the REST endpoint for the RSI Momentum screener — a dedicated page that detects stocks approaching or breaking out above a configurable RSI threshold (default: 60) for the first time in a lookback window.

---

## 2. Endpoint

```
POST /rsi-momentum/scan
```

---

## 3. Request body

```json
{
  "universe":     "NIFTY_500",   // which stock universe to scan
  "lookback_days": 20,           // how many previous days define "fresh" (5–100)
  "threshold":    60.0,          // RSI breakout level (30–90)
  "signals":      ["APPROACHING", "FRESH_BREAKOUT"],  // empty = all signals
  "limit":        200,           // max results to return
  "offset":       0
}
```

**`signals`** filters the returned stocks to only those matching the requested signal types:
- `FRESH_BREAKOUT` — RSI just crossed threshold for the first time in `lookback_days`
- `APPROACHING` — RSI within 5 points below threshold, rising, no recent crossing
- `ALREADY_STRONG` — RSI above threshold but has already crossed recently
- `EXTENDED` — RSI ≥ 70
- `NEUTRAL` — everything else

An empty `signals` list returns all signals.

---

## 4. Response

```json
{
  "executed_at": "2026-08-23T07:26:43.249306+00:00",
  "universe": "NIFTY_500",
  "total_matched": 12,
  "stocks_screened": 500,
  "execution_time_ms": 3858.4,
  "stocks": [
    {
      "symbol": "RELIANCE",
      "company_name": "Reliance Industries",
      "rsi_today": 58.4,
      "rsi_prev": 56.1,
      "rsi_change": 2.3,
      "distance_to_60": 1.6,
      "rsi_trend": "RISING",
      "above_60_in_20d": false,
      "days_since_above_60": null,
      "signal": "APPROACHING"
    }
  ]
}
```

**`days_since_above_60`** — `null` means RSI has never been above the threshold in the available price history (within the lookback window). A number like `35` means 35 trading days ago.

**`distance_to_60`** — `threshold - rsi_today`. Negative means already above threshold.

---

## 5. Route implementation

The route is a thin delegation to `RSIMomentumService.scan()`:

```python
@router.post("/rsi-momentum/scan")
def scan_rsi_momentum(body: RSIMomentumScanRequest):
    return rsi_momentum_service.scan(
        universe=body.universe,
        lookback_days=body.lookback_days,
        threshold=body.threshold,
        signals=body.signals or None,
        ...
    )
```

All scan logic (parallel OHLCV fetching, RSI series computation, signal classification, caching, sorting) is in `rsi_momentum_service.py`. The route only validates the request body (Pydantic does this automatically) and delegates.

---

## 6. How it differs from the regular screen

| Feature | `/screens/run` | `/rsi-momentum/scan` |
|---|---|---|
| Filter DSL | Generic (RSI, Bollinger, volume operators) | Fixed to RSI momentum signals |
| Indicators computed | Only what filters need | RSI series (full 20+ day history) |
| Result format | Generic `indicators` dict | Named momentum fields |
| Sorting | By indicator value | By signal priority, then distance to threshold |
| Purpose | Flexible screening | Dedicated momentum detection page |
