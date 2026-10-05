# backend/app/services/screening_service.py — Beginner Explanation

> **Source file:** `backend/app/services/screening_service.py`

---

## 1. What is this file?

The core screening pipeline. `ScreeningService.run(dsl)` takes a `ScreenDSL` request, fetches indicator data for each stock in the universe in parallel, evaluates every filter condition, optionally scores results, ranks them, and paginates.

---

## 2. Pipeline steps

```
1. Parse DSL filters → FilterExpr tree
2. Load all stocks in universe from database (up to 2000)
3. Pre-filter on cheap classification conditions (no yfinance)
4. Compute fetch_needs = indicator_needs ∪ extra_indicators (for display columns)
5. Fetch all needed indicators in parallel (ThreadPoolExecutor, 5 workers)
6. Evaluate full filter expression per stock → PASS / FAIL / SKIP
7. Optionally compute composite score per matched stock
8. Rank matched stocks
9. Paginate and return
```

---

## 3. Pre-filter (Step 3)

```python
stocks = [s for s in stocks if _pre_pass_classification(s, expr)]
```

Before making any yfinance calls, we run classification-only conditions against the database data. A stock that provably fails a classification filter (wrong sector, wrong market cap) is dropped immediately.

**OrGroup edge case:** if an `OrGroup` contains only `IndicatorFilter` children (no classification children), we cannot prove any stock fails — so we return `True` to let the stock through. Without this, an `OrGroup` of purely indicator conditions (e.g. `signal_rank == 4.5 OR signal_rank == 4.0`) would incorrectly return `any([]) = False` and reject every stock before fetching any indicators.

```python
if isinstance(expr, OrGroup):
    cls_children = [c for c in expr.children
                    if isinstance(c, (ClassificationFilter, AndGroup, OrGroup))]
    if not cls_children:
        return True  # can't prove failure — let the indicator fetch decide
```

---

## 4. Fetch needs (Step 4)

```python
fetch_needs = set(indicator_needs)
if dsl.extra_indicators:
    for spec in dsl.extra_indicators:
        fetch_needs.add((spec.indicator, spec.timeframe.upper()))
```

`indicator_needs` = indicators required to evaluate the filter conditions.
`extra_indicators` = additional indicators the frontend wants displayed (BB, MACD, Volume) even when not filtering by them.

Both sets are merged into `fetch_needs` so a single parallel fetch covers everything.

---

## 5. Parallel indicator fetch (Step 5)

```python
with ThreadPoolExecutor(max_workers=5) as pool:
    futures = {pool.submit(fetch_all_for_stock, s): s for s in stocks}
```

For 50 stocks with 5 workers, this runs ~10 batches of parallel yfinance calls instead of 50 sequential ones. 5 workers is deliberate — too many workers triggers yfinance rate limits.

Each fetch is Redis-cached:
```
screen_ind:v3:{exchange}:{symbol}:{indicator}:{timeframe}:{today}  →  TTL 4h
```

On re-runs the same day, all stocks come from cache in ~1s instead of ~6s.

---

## 6. Scoring (Step 7)

```python
if score_criteria is not None:
    sr = score_stock(ind_data, score_criteria)
    entry["score"] = sr.score
    entry["score_completeness"] = sr.completeness
```

Scoring runs inline (not via the agent message bus) to avoid per-stock dispatch overhead. The `score_stock()` call is pure in-memory math — no I/O.

---

## 7. Response shape

```json
{
  "executed_at": "2026-08-23T06:00:00Z",
  "universe": "NIFTY_50",
  "total_matched": 12,
  "stocks_screened": 50,
  "execution_time_ms": 4043.9,
  "stocks": [
    {
      "id": "NSE:ITC",
      "symbol": "ITC",
      "sector": "Consumer Staples",
      "market_cap_category": "LARGE_CAP",
      "indicators": {
        "rsi_momentum_1D": {"signal_rank": 4.5, "signal": "APPROACHING_AGAIN"},
        "bollinger_1D": {"percent_b": 0.72},
        "macd_1D": {"histogram": 2.251},
        "volume_strength_1D": {"volume_ratio": 190.0}
      }
    }
  ]
}
```

Extra indicator data (BB, MACD, Volume) appears in the `indicators` map even when those were not used as filter conditions — they're fetched for display purposes via `extra_indicators`.
