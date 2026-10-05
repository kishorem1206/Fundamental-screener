# backend/app/services/rsi_momentum_service.py — Beginner Explanation

> **Source file:** `backend/app/services/rsi_momentum_service.py`

---

## 1. What is this file?

Orchestrates a full-universe RSI momentum scan. Fetches OHLCV data for every stock in a universe in parallel, runs the `RSIMomentumPlugin` for each, filters by requested signals, and sorts by signal priority.

---

## 2. Key functions

### `_fetch_one(stock, lookback, threshold)`
Checks Redis cache first. If cache miss: calls `get_ohlcv(...)` to fetch bars, runs `rsi_momentum_plugin.calculate(...)`, converts the float `rsi_trend` value to a string ("RISING"/"FLAT"/"FALLING"), converts the 0.0/1.0 `above_60_in_20d` to a Python bool, and stores the result dict in Redis with a 4-hour TTL.

Returns `None` for stocks with UNKNOWN signal (insufficient data — usually IPOs or halted stocks with < 35 bars of history).

### `RSIMomentumService.scan(...)`
1. Loads all stocks for the universe (up to 2000)
2. Runs `_fetch_one` for each in a `ThreadPoolExecutor` with 5 workers
3. Filters results by `signals` list if provided
4. Sorts by signal priority desc, then `distance_to_60` asc (closer to threshold = more interesting)
5. Returns paginated result dict

---

## 3. Signal priority

```python
_SIGNAL_PRIORITY = {
    "FRESH_BREAKOUT":    5,
    "APPROACHING_AGAIN": 4.5,
    "APPROACHING":       4,
    "ALREADY_STRONG":    3,
    "EXTENDED":          2,
    "NEUTRAL":           1,
}
```

APPROACHING_AGAIN (4.5) sits between FRESH_BREAKOUT and APPROACHING — it's a second-chance entry for stocks that were above the threshold in the lookback window and have pulled back.

---

## 4. Sort order

```python
results.sort(key=lambda r: (
    -_SIGNAL_PRIORITY.get(r["signal"], 0),   # highest priority first
    r["distance_to_60"],                      # within same signal: closest to threshold first
))
```

---

## 5. Cache key

```python
# v3 — trend logic changed to today-vs-yesterday; invalidates v2
f"rsi_mom:v3:{exchange}:{symbol}:{lookback}:{threshold:.0f}:{today_date()}"
```

The version prefix is bumped whenever the plugin's classification logic changes so all users get fresh results without waiting for the daily TTL expiry. Different `lookback` / `threshold` values also produce separate cache entries.
