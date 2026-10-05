# backend/app/indicators/plugins/rsi_momentum.py — Beginner Explanation

> **Source file:** `backend/app/indicators/plugins/rsi_momentum.py`

---

## 1. What is this file?

An indicator plugin that detects **where a stock is in its RSI momentum cycle** relative to a threshold (default: 60). Rather than simply comparing "RSI > 60", it detects whether the stock is *approaching* that level for the first time, *just crossing* it as a fresh breakout, *pulling back for a second-chance entry*, *already above it*, or *overextended*.

---

## 2. The six signals

| Signal | Rank | Condition | Meaning |
|---|---|---|---|
| `FRESH_BREAKOUT` | 5.0 | RSI yesterday < threshold, today ≥ threshold, no RSI≥threshold in lookback | First crossing — start of momentum |
| `APPROACHING_AGAIN` | 4.5 | RSI in approaching zone AND was above threshold in lookback | Second-chance entry — pulled back from above |
| `APPROACHING` | 4.0 | RSI within 5pts below threshold, rising, never crossed in lookback | About to break — early watch |
| `ALREADY_STRONG` | 3.0 | RSI ≥ threshold (below 70) | Momentum underway but not fresh |
| `EXTENDED` | 2.0 | RSI ≥ 70 | Overextended, higher reversal risk |
| `NEUTRAL` | 1.0 | Everything else | Below approaching zone or falling |

---

## 3. How RSI series is computed

The existing RSI plugin only returns today's RSI. This plugin computes the **full series** using Wilder's smoothing to get yesterday's RSI and the full lookback window:

```python
def _compute_rsi_series(closes, period=14):
    avg_gain = mean(gains[:period])
    avg_loss = mean(losses[:period])
    series = [rsi(avg_gain, avg_loss)]

    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        series.append(rsi(avg_gain, avg_loss))

    return series
```

`series[-1]` = today's RSI, `series[-2]` = yesterday's.

---

## 4. Key derived metrics

### RSI Trend (today vs yesterday)
```python
_FLAT_THRESHOLD = 0.5  # changes smaller than 0.5 RSI points = sideways

if rsi_change > _FLAT_THRESHOLD:
    rsi_trend = 1.0   # RISING
elif rsi_change < -_FLAT_THRESHOLD:
    rsi_trend = -1.0  # FALLING
else:
    rsi_trend = 0.0   # FLAT
```
`rsi_change = rsi_today - rsi_prev`. A tiny change (< 0.5 pts) is classified as sideways to avoid noise.

### `above_60_in_20d` / `above_in_lookback`
```python
prev_vals = rsi_series[-(lookback + 1):-1]   # last `lookback` days, excluding today
above_in_lookback = any(r >= threshold for r in prev_vals)
```
Stored as `1.0`/`0.0` float (all plugin values must be numeric for the filter engine).

### Days since last above threshold
```python
for i, r in enumerate(reversed(prev_vals)):
    if r >= threshold:
        days_since = float(i + 1)  # yesterday = 1
        break
```
If never found: `999.0` → displayed as "Never" in the UI.

---

## 5. Signal priority order

```python
# Checked in this order — first match wins:
if rsi_prev < threshold and rsi_today >= threshold and not above_in_lookback:
    signal = "FRESH_BREAKOUT"
elif approaching_zone <= rsi_today < threshold and above_in_lookback:
    signal = "APPROACHING_AGAIN"      # pulled back from above — second chance
elif approaching_zone <= rsi_today < threshold and rsi_change > 0 and not above_in_lookback:
    signal = "APPROACHING"
elif rsi_today >= 70:
    signal = "EXTENDED"
elif rsi_today >= threshold:
    signal = "ALREADY_STRONG"
else:
    signal = "NEUTRAL"
```

EXTENDED is checked before ALREADY_STRONG so RSI=73 is correctly classified as EXTENDED.

---

## 6. Default params

```python
default_params = {"period": 14, "lookback_days": 50, "threshold": 60.0}
```

`lookback_days=50` is the default used by the AI Chat filter engine. The RSI Momentum page passes its own slider value so it isn't affected by this default.

---

## 7. How it fits in the architecture

1. **Plugin** (`rsi_momentum.py`) → registered in `registry.py` as `"rsi_momentum"`
2. **Service** (`rsi_momentum_service.py`) → fetches OHLCV in parallel, runs the plugin, caches 4h, converts float trend to string, sorts by signal rank
3. **Route** (`routes/rsi_momentum.py`) → `POST /rsi-momentum/scan`
4. **Filter engine** → uses `default_params` (lookback=50) when called from AI Chat screen

---

## 8. Cache key design

```python
# v3 — trend changed to today-vs-yesterday; invalidates v2
f"rsi_mom:v3:{exchange}:{symbol}:{lookback}:{threshold:.0f}:{today_date()}"
```

Bumped to v3 when trend logic changed from 3-period to today-vs-yesterday.
