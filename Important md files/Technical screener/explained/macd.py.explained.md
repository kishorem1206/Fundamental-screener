# backend/app/indicators/plugins/macd.py — Beginner Explanation

> **Source file:** `backend/app/indicators/plugins/macd.py`

---

## 1. What is this file?

Implements the MACD (Moving Average Convergence Divergence) indicator, invented by Gerald Appel in the 1970s.

MACD measures momentum by comparing two exponential moving averages of a stock's close price. When the shorter EMA is above the longer one, the stock has upward momentum. When the two lines cross, it signals a possible trend change.

---

## 2. The three MACD numbers

| Name | Formula | What it means |
|---|---|---|
| MACD line | 12-period EMA − 26-period EMA | Momentum direction |
| Signal line | 9-period EMA of the MACD line | Smoothed momentum |
| Histogram | MACD line − Signal line | Strength of current momentum |

A positive histogram means MACD is above the Signal line (bullish momentum). A negative histogram means it's below (bearish). When the histogram crosses zero, the MACD and Signal lines are crossing — this is the classic "crossover" signal.

---

## 3. EMA calculation

```python
def _ema_series(values: list[float], period: int) -> list[float]:
    k = 2.0 / (period + 1)   # EMA multiplier (e.g. 0.1538 for 12-period)
    ema = mean(values[:period])  # Seed with SMA of first `period` bars
    for v in values[period:]:
        ema = v * k + ema * (1 - k)   # Each new bar: blend old EMA with new price
```

The `k = 2/(n+1)` multiplier is the standard Investopedia formula. A 12-period EMA gives k=0.1538 — today's price gets 15% weight, yesterday's EMA gets 85%.

---

## 4. Alignment: why we need an offset

`_ema_series(closes, 12)` returns N−11 values (starts at bar 12).
`_ema_series(closes, 26)` returns N−25 values (starts at bar 26).

The two series start at different points. We trim the fast EMA series to start at the same bar as the slow EMA:

```python
offset = slow - fast   # = 26 - 12 = 14
macd_line = [f - s for f, s in zip(fast_ema[offset:], slow_ema)]
```

Then we build the Signal line from the MACD line:
```python
signal_line = _ema_series(macd_line, signal_period)
```

The Signal line is shorter than the MACD line by `signal_period − 1` values. To read "today" and "yesterday" from both aligned, we use:
```python
macd_aligned = macd_line[sig_p - 1:]   # align start with signal_line
```

---

## 5. Crossover detection

```python
crossed_above = macd_prev < signal_prev and macd_val >= signal_val
crossed_below = macd_prev > signal_prev and macd_val <= signal_val
```

"Yesterday MACD was below Signal, today it's at or above" = bullish crossover (MACD crossed up through the Signal line). This is the classical "buy signal."

---

## 6. Values returned

| Field | Type | Meaning |
|---|---|---|
| `macd` | float | MACD line today |
| `signal_line` | float | Signal line today |
| `histogram` | float | MACD − Signal (+ = bullish, − = bearish) |
| `macd_prev` | float | MACD line yesterday (crossover detection) |
| `histogram_prev` | float | Histogram yesterday |
| `bullish_crossover` | 1.0 / 0.0 | 1.0 if MACD crossed above Signal today |
| `bearish_crossover` | 1.0 / 0.0 | 1.0 if MACD crossed below Signal today |

`bullish_crossover` and `bearish_crossover` are stored as floats (not booleans) so the filter engine can compare them with `op="eq", value=1.0` the same way it filters all numeric indicator values.

---

## 7. Signals

| Signal | Condition |
|---|---|
| `BULLISH_CROSSOVER` | MACD just crossed above Signal today |
| `BEARISH_CROSSOVER` | MACD just crossed below Signal today |
| `BULLISH` | histogram > 0 (MACD above Signal, no crossover today) |
| `BEARISH` | histogram < 0 (MACD below Signal, no crossover today) |
| `NEUTRAL` | histogram exactly 0 |
| `UNKNOWN` | Not enough price history (need at least 35 bars: 26 slow + 9 signal) |

---

## 8. Minimum data required

```
slow + signal_period = 26 + 9 = 35 bars minimum
```

Plus one more bar to compute "yesterday" for crossover detection. IPO stocks or recently listed stocks with fewer than 35 trading days will get `UNKNOWN`.

---

## 9. Registration

```python
# backend/app/indicators/registry.py
indicator_registry.register(macd_plugin)
```

In the screening engine the indicator key is `macd_1D` (name + timeframe). The AI Chat screen uses `indicator="macd"` in filter conditions — the engine appends `_1D` when querying.

---

## 10. Example AI Chat queries

| User query | Filter condition generated |
|---|---|
| "MACD bullish crossover" | `bullish_crossover eq 1.0` |
| "MACD positive" | `histogram gt 0` |
| "MACD bearish crossover" | `bearish_crossover eq 1.0` |
| "MACD below signal" | `histogram lt 0` |
