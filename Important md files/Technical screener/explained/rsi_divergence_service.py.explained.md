# backend/app/services/rsi_divergence_service.py — Beginner Explanation

> **Source file:** `backend/app/services/rsi_divergence_service.py`

---

## 1. What is this file?

Scans a full stock universe for recent RSI divergences using the divergence engine. Follows the same architecture as `rsi_momentum_service.py` — threaded fetching with Redis caching.

---

## 2. How it works

```
scan(universe, config params, require_rsi_rising)
  ↓
classification_service.get_universe_stocks(universe, limit=2000)
  ↓
ThreadPoolExecutor(max_workers=5)
  → for each stock: _fetch_one(stock, cfg, div_types)
      → check Redis cache (4h TTL per stock per day per config)
      → if miss: get_ohlcv(exchange, symbol, "1D")
               → detect_rsi_divergence(bars, cfg)
               → get_current_rsi(bars) → rsi_today, rsi_prev
               → serialize result to dict list
               → write to Redis
  ↓
optional post-filter: require_rsi_rising (client-side, not cached)
  ↓
sort by recency then strength → paginate → return
```

---

## 3. Cache key design

```python
f"rsi_div:v3:{exchange}:{symbol}:pl{pl}:pr{pr}:r{recency}:mb{max_bars}:mr{maxr}:nr{minr}:{div_types}:{today}"
```

Each unique combination of stock + config + date gets its own cache entry. The `v3:` prefix was bumped when `rsi_today`/`rsi_prev` fields were added to cached rows — old `v2` entries would be missing those fields and cause key errors.

---

## 4. rsi_today / rsi_prev fields

Every cached row now includes the stock's most recent RSI values:

```python
rsi_pair  = get_current_rsi(bars, period=cfg.rsi_period)
rsi_today = round(rsi_pair[0], 2) if rsi_pair else None
rsi_prev  = round(rsi_pair[1], 2) if rsi_pair else None
```

These are the RSI of the last two candles — useful for showing whether momentum is rising right now, independent of the divergence pivot points.

---

## 5. require_rsi_rising post-filter

```python
if require_rsi_rising:
    all_divs = [
        d for d in all_divs
        if d.get("rsi_today") is not None
        and d.get("rsi_prev") is not None
        and d["rsi_today"] > d["rsi_prev"]
    ]
```

This filter is applied **after** Redis lookup (not part of the cache key) because it's cheap to compute in Python and the base divergence data is the same regardless. Keeping it out of the cache key means we don't create separate cache entries for every on/off combination of this toggle.

---

## 6. Output shape

Each divergence in the `divergences` list contains:

| Field | Type | Description |
|-------|------|-------------|
| `id`, `symbol`, `exchange` | str | Stock identity |
| `company_name`, `sector` | str | Stock metadata |
| `div_type` | str | e.g. "REGULAR_BULLISH" |
| `status` | str | "RECENT_CONFIRMED" |
| `pivot1_date`, `pivot2_date` | str | Dates of the two swing pivots |
| `pivot1_price`, `pivot2_price` | float | Prices at the two pivots |
| `pivot1_rsi`, `pivot2_rsi` | float | RSI values at the two pivots |
| `price_chg_pct` | float | (P2−P1)/P1 × 100 |
| `rsi_change` | float | P2_RSI − P1_RSI |
| `bars_between` | int | Trading days between the two pivots |
| `divergence_age` | int | Trading days since P2 |
| `strength_score` | float | 0–10 quality score |
| `rsi_today` | float\|null | RSI of the latest candle |
| `rsi_prev` | float\|null | RSI of the previous candle |

---

## 7. Threading note

`max_workers=5` limits concurrent yfinance requests. Cached results skip the network and return in microseconds, so subsequent scans with the same parameters on the same day are very fast.
