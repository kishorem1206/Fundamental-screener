# backend/app/data/market_data.py — Beginner Explanation

> **Source file:** `backend/app/data/market_data.py`

---

## 1. What is this file?

Fetches historical OHLCV (Open, High, Low, Close, Volume) price data from Yahoo Finance using the `yfinance` library. This is the data source for indicator calculations in Phase 3.

Added in **Phase 3**.

---

## 2. Why yfinance?

Yahoo Finance provides free historical price data for Indian stocks via NSE/BSE. No API key needed. Works for:
- **NSE**: `INFY.NS`, `RELIANCE.NS`, `TCS.NS` (append `.NS`)
- **BSE**: `INFY.BO`, `RELIANCE.BO` (append `.BO`)

In Phase 6, when the LLM chat is active, TradingView MCP will be the preferred source for real-time data. `yfinance` is the fallback for historical data.

---

## 3. Supported timeframes

| API `tf` param | yfinance `interval` | yfinance `period` | Approx bars |
|---------------|--------------------|--------------------|-------------|
| `1H` | `1h` (hourly candles) | `730d` | ~4800 |
| `4H` | synthetic (1H resampled) | 730d of 1H → every 4 bars merged | ~1200 |
| `1D` | `1d` (daily candles) | `2y` | ~500 |
| `1W` | `1wk` (weekly candles) | `5y` | ~260 |
| `1M` | `1mo` (monthly candles) | `10y` | ~120 |
| `15M` | `15m` | `60d` | ~1500 |
| `5M` | `5m` | `5d` | ~375 |

**Why 2y for 1D?** Wilder's RSI uses an exponential moving average with a very slow decay (period=14 → each step keeps 13/14 of history). After a big crash (like ETERNAL in Jan-Feb 2026, when RSI hit ~20), the initial high `avg_loss` takes hundreds of bars to smooth away. With only 6 months of data (126 bars), the computed RSI for recent bars would still be artificially depressed compared to TradingView's RSI (which uses all available history). With 2 years (~500 bars), after 486 smoothing steps the initial crash values contribute less than (13/14)^486 ≈ 0.000001% to current RSI — fully converged.

**Why is 4H synthetic?** yfinance doesn't expose a native 4-hour interval for Indian stocks. We fetch hourly data (730 days) and group every 4 consecutive 1H bars into one 4H candle using `_resample_bars(bars, 4)`. For NSE stocks (trading 9:15–15:30 = ~6 hours/day ≈ 6 1H bars/day), this yields roughly 1–2 synthetic 4H candles per session, giving ~1000 total candles — enough for RSI, MACD, and Bollinger convergence.

---

## 4. Line-by-line explanation

### Symbol mapping

```python
def _yf_symbol(exchange: str, symbol: str) -> str:
    if exchange == "NSE":
        return f"{symbol.upper()}.NS"
    if exchange == "BSE":
        return f"{symbol.upper()}.BO"
    return symbol.upper()
```

Converts our internal format (`NSE` + `INFY`) to Yahoo Finance's format (`INFY.NS`).

---

### Fetching data

```python
ticker = yf.Ticker(yf_sym)
df = ticker.history(period=period, interval=interval, auto_adjust=True)
```

**`yf.Ticker(yf_sym)`** — Creates a Ticker object. No network call yet.

**`ticker.history(...)`** — Makes the actual HTTP request to Yahoo Finance. Returns a pandas `DataFrame` with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits.

**`auto_adjust=True`** — Adjusts prices for dividends and stock splits automatically. Without this, historical prices have artificial gaps around corporate actions.

---

### Converting to `OHLCVBar`

```python
for ts, row in df.iterrows():
    date_str = ts.strftime("%Y-%m-%d")
    bars.append(OHLCVBar(
        date=date_str,
        open=float(row["Open"]),
        high=float(row["High"]),
        low=float(row["Low"]),
        close=float(row["Close"]),
        volume=float(row.get("Volume", 0)),
    ))
```

**`df.iterrows()`** — Iterates over rows. `ts` is the DatetimeIndex (timestamp), `row` is the row data.

**`ts.strftime("%Y-%m-%d")`** — Formats the timestamp as `"2026-08-21"`.

**`float(row["Open"])`** — Explicit conversion from numpy float64 to Python float. `dataclasses.asdict()` can't serialize numpy scalars to JSON; Python floats work fine.

---

## 4a. `_resample_bars(bars, n)`

```python
def _resample_bars(bars: list[OHLCVBar], n: int) -> list[OHLCVBar]:
    for i in range(0, len(bars), n):
        chunk = bars[i: i + n]
        OHLCVBar(date=chunk[0].date, open=chunk[0].open,
                 high=max(h), low=min(l), close=chunk[-1].close, volume=sum(v))
```

Groups `n` consecutive bars into one bar:
- `open` = first bar's open (session starts here)
- `high` = highest of all bars in the chunk
- `low` = lowest of all bars in the chunk
- `close` = last bar's close (session ends here)
- `volume` = sum (total shares traded in the period)

Only used for 4H synthesis. RSI/MACD/Bollinger all work on the resulting sequence of OHLCV bars without needing real timestamps.

---

## 5. Error handling

- Invalid symbol → yfinance returns an empty DataFrame → `DataUnavailableError`
- Network error → `DataUnavailableError` with the exception message
- Unsupported timeframe → `DataUnavailableError` before any network call

All `DataUnavailableError` exceptions are caught by `IndicatorAgent` and returned as 404 responses.

---

## 6. Phase 6 upgrade path

In Phase 6, the `get_ohlcv` function will be extended to:
1. Check if TradingView MCP returned data (via agent result from LLM tool call)
2. Fall back to `yfinance` only if TradingView data is unavailable

The current Phase 3 implementation goes directly to yfinance, which is the fallback path.
