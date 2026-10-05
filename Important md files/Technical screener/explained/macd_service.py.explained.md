# backend/app/services/macd_service.py — Beginner Explanation

**Source file:** `backend/app/services/macd_service.py`

## What this file does

This is the orchestration layer between the MACD route and the MACD engine. It:
1. Loops over every stock in a universe (in parallel via `ThreadPoolExecutor`)
2. Fetches OHLCV price history from yfinance (cached in Redis)
3. Calls `engine.analyze_macd()` to get the MACD analysis for that stock
4. Applies the user-chosen histogram and crossover filters
5. Sorts the results (crossovers first, then by absolute histogram size)
6. Returns the paginated `MACDScanResult` dict

The chart endpoint `get_chart_data()` does the same fetch/compute path but returns the full time series for one stock rather than a scan.

## Key sections

### Cache key

```python
f"macd_scan:v1:{exchange}:{symbol}:{source}:f{fast}:s{slow}:sg{signal}:{osc_ma}:{sig_ma}:{tf}:{today_date()}"
```

Every parameter that changes the computation is included. `today_date()` causes the cache to expire at midnight, so yesterday's data is never served after a new trading session opens. TTL is set to 4 hours for intra-day freshness.

### Filter: `_passes_hist_filter`

```python
def _passes_hist_filter(analysis, hist_filters):
```

If no filters are selected, everything passes. Otherwise the function checks:
- `"POSITIVE"` → histogram > 0 (matches STRONG_BULLISH and BULLISH_FADING)
- `"NEGATIVE"` → histogram < 0 (matches STRONG_BEARISH and BEARISH_FADING)
- Named states like `"STRONG_BULLISH"` → exact match on `histogram_state`

Multiple filters are OR-combined — a stock passes if it matches **any** selected filter.

### Filter: `_passes_cross_filter`

```python
def _passes_cross_filter(analysis, cross_filters, cross_bars):
```

`cross_bars` is the "within N candles" window. If the last crossover happened more bars ago than `cross_bars`, the stock fails. The filter types:
- `"BULLISH"` → matches any crossover whose `last_crossover_type` starts with `"BULLISH"` (covers both ABOVE_ZERO and BELOW_ZERO variants)
- `"BEARISH"` → similar
- `"BULLISH_BELOW_ZERO"` → exact match (only that specific sub-type)

Multiple cross filters are also OR-combined.

### Parallel fetch

```python
with ThreadPoolExecutor(max_workers=5) as pool:
    futures = {pool.submit(_process_one, s): s for s in stocks}
```

Each stock is processed independently. `max_workers=5` matches the rate limit budget for the yfinance + Redis cache pattern used throughout the app.

### Sort order

```python
key=lambda r: (0 if r["crossover"] != "NONE" else 1, -abs(r["histogram"]))
```

Stocks with a crossover today bubble to the top. Within each group, stocks are sorted by absolute histogram size descending — the strongest momentum signal first.

### `get_chart_data`

Fetches more bars than the scan needs (`num_bars * 3` to allow for MA warm-up), calls `compute_macd_series` from the engine, and returns the last `num_bars` in the result. This is a separate endpoint so the chart doesn't slow down the scan.
