# backend/app/agents/market_data_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/market_data_agent.py`

---

## 1. What is this file?

Defines `MarketDataAgent` — fetches live market quotes for a stock using yfinance. Returns price, daily change, 52-week range, volume, and market cap. Results are cached in Redis for 5 minutes so repeated requests don't hammer yfinance.

---

## 2. Task type: `GET_QUOTE`

**Payload:** `{"exchange": "NSE", "symbol": "INFY"}`

**Result:**
```json
{
  "symbol": "INFY",
  "exchange": "NSE",
  "yf_symbol": "INFY.NS",
  "price": 1121.0,
  "change": -9.05,
  "change_pct": -0.8,
  "volume": 4823000,
  "open": 1130.5,
  "high": 1135.2,
  "low": 1118.3,
  "prev_close": 1130.05,
  "week52_high": 1728.0,
  "week52_low": 1010.0,
  "market_cap": 4642000000000,
  "timestamp": "2026-08-23T06:15:00+00:00"
}
```

---

## 3. Two yfinance calls

```python
info = ticker.fast_info     # fast metadata: price, 52w high/low, market cap
hist = ticker.history(period="5d", interval="1d")  # last 5 daily bars
```

`fast_info` is much faster than `ticker.info` (no full company profile). It provides the live price snapshot.

`history("5d", "1d")` gives the last 5 daily candles, used to compute `prev_close` (the second-to-last close, i.e. yesterday) and today's OHLC.

---

## 3a. Price fallback for NSE stocks

`fast_info.last_price` often returns `None` for Indian NSE/BSE stocks. When that happens the agent falls back to the last bar's close from the history:

```python
price = float(info.last_price) if info.last_price else None
if price is None and not hist.empty:
    price = round(float(hist["Close"].iloc[-1]), 2)
```

This ensures the price field is always populated as long as any recent history is available.

---

## 4. `change` and `change_pct` calculation

```python
prev_close = float(hist["Close"].iloc[-2])   # yesterday's close
change = price - prev_close
change_pct = (change / prev_close) * 100
```

`iloc[-2]` means "second from the end" — the bar before today's.

---

## 5. Redis cache key

```
quote:{exchange}:{symbol}   →   TTL 5 minutes
```

Short TTL because prices change throughout the trading day.
