# backend/app/indicators/ — Beginner Explanation

> **Source files:** `app/indicators/plugin.py`, `app/indicators/registry.py`, `app/indicators/engine.py`, `app/indicators/plugins/rsi.py`, `app/indicators/plugins/bollinger.py`

---

## 1. What is this package?

The indicator system calculates technical analysis values (RSI, Bollinger Bands) from OHLCV price bar data. It's a plugin-based system where each indicator is a self-contained module.

Added in **Phase 3**.

---

## 2. The Plugin pattern

Each indicator is a **plugin** — an independent class that knows how to calculate one indicator:

```
IndicatorPlugin (Protocol/interface)
  ├── RSIPlugin           → calculates RSI
  └── BollingerBandsPlugin → calculates Bollinger Bands
```

They're all registered in `IndicatorRegistry` and called through `IndicatorEngine`.

---

## 3. `plugin.py` — data types

### `OHLCVBar`
One price candle: Open, High, Low, Close, Volume for one time period.

### `IndicatorResult`
What a plugin returns after calculating: `name`, `params`, `values` (the numbers), and `signal` (human-readable interpretation).

### `TechnicalSnapshot`
The final API response object: symbol, exchange, timeframe, all indicator results, and provenance (where the data came from).

### `IndicatorPlugin` (Protocol)
The interface every plugin must implement. Any class with `name`, `default_params`, and `calculate(bars, params)` is a valid plugin.

---

## 4. RSI Plugin — Wilder's Smoothing

RSI (Relative Strength Index) measures momentum: how fast prices are moving up vs down.

```python
# Wilder's smoothing = EWM with alpha = 1/period
avg_gain = pd.Series(gains).ewm(alpha=1/period, adjust=False).mean().iloc[-1]
avg_loss = pd.Series(losses).ewm(alpha=1/period, adjust=False).mean().iloc[-1]

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
```

**Why Wilder's smoothing?** TradingView uses this exact formula. EWM = Exponential Weighted Mean. `alpha=1/14` for RSI-14, `adjust=False` means each value depends on the previous one (not the full history).

**RSI signals:**
- < 30 → `OVERSOLD` (stock may be undervalued, potential buy)
- > 70 → `OVERBOUGHT` (stock may be overvalued, potential sell)
- 30–70 → `NEUTRAL`

---

## 5. Bollinger Bands Plugin

Bollinger Bands show price volatility: two bands around a moving average.

```python
sma = series.rolling(period).mean().iloc[-1]    # Middle band = 20-day SMA
std = series.rolling(period).std(ddof=0).iloc[-1]  # Population std (matches TradingView)

upper = sma + std_dev * std   # Upper band
lower = sma - std_dev * std   # Lower band

# %B: where is price within the bands? 0=lower band, 1=upper band, 0.5=middle
percent_b = (last_price - lower) / (upper - lower)

# Bandwidth: how wide are the bands? Higher = more volatile
bandwidth = (upper - lower) / sma
```

**`ddof=0`** — Population standard deviation (matches TradingView's calculation). `ddof=1` gives sample std (slightly different values).

**Bollinger signals (based on %B):**
- %B < 0.05 → `NEAR_LOWER` (price near lower band, potential oversold)
- %B > 0.95 → `NEAR_UPPER` (price near upper band, potential overbought)
- else → `NEUTRAL`

---

## 6. `engine.py` — IndicatorEngine

Orchestrates the calculation:
1. Loops over requested indicator names
2. Gets each plugin from the registry
3. Calls `plugin.calculate(bars, params)`
4. Packages results + provenance into `TechnicalSnapshot`

---

## 7. Data flow

```
GET /stocks/NSE/INFY/indicators?tf=1D&indicators=rsi,bollinger
    ↓
indicators route → builds AgentTask
    ↓
agent_message_bus.dispatch(task)
    ↓
IndicatorAgent.handle(task)
    ↓ check Redis cache (cache key = symbol+tf+indicators+today)
    ↓ cache miss → get_ohlcv("NSE", "INFY", "1D") via yfinance
    ↓ indicator_engine.calculate(bars, ["rsi", "bollinger"])
    ↓ cache result (4 hour TTL)
    ↓
TechnicalSnapshot → JSON response
```

---

## 8. Example response

```json
{
  "symbol": "INFY",
  "exchange": "NSE",
  "timeframe": "1D",
  "data_date": "2026-08-21",
  "last_price": 1121.0,
  "indicators": {
    "rsi": {
      "params": {"period": 14},
      "value": 47.13,
      "signal": "NEUTRAL"
    },
    "bollinger": {
      "params": {"period": 20, "std_dev": 2.0},
      "upper": 1210.29,
      "middle": 1150.35,
      "lower": 1090.41,
      "percent_b": 0.2552,
      "bandwidth": 0.1042,
      "signal": "NEUTRAL"
    }
  },
  "provenance": [
    {
      "source": "yfinance",
      "symbol": "INFY.NS",
      "timeframe": "1D",
      "bars_used": 125,
      "data_range": "2026-02-23 to 2026-08-21"
    }
  ]
}
```
