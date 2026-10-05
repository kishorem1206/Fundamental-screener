# backend/app/macd/engine.py — Beginner Explanation

**Source file:** `backend/app/macd/engine.py`

## What this file does

This file is the mathematical core for MACD analysis. It takes a list of price bars and computes:
1. The MACD line (fast MA minus slow MA)
2. The Signal line (MA of the MACD line)
3. The Histogram (MACD minus Signal)
4. Histogram state (4-colour TradingView-style classification)
5. Crossover detection (MACD line crossing Signal line), with zero-line context
6. The scan looks back up to `crossover_lookback` bars for the most recent crossover

It exposes two public functions: `analyze_macd` (returns a single `MACDAnalysis` snapshot for the current bar, used by the scanner) and `compute_macd_series` (returns a full bar-by-bar series, used by the chart endpoint).

## Key sections

### Price source helper

```python
def _source(bar: dict, src: str) -> float:
```

Converts a raw OHLCV bar into the chosen price point. `HL2 = (H+L)/2`, `HLC3 = (H+L+C)/3`, `OHLC4 = (O+H+L+C)/4`.

### Moving average

```python
def _ma(series: list[float], period: int, kind: str) -> list[float]:
```

Returns either EMA or SMA over the series. For EMA: `k = 2/(period+1)`, each value is `prev*(1-k) + current*k`. The list length equals `len(series) - period + 1`, i.e. EMA/SMA length shrinks by `period-1` bars.

### Aligning slow MA and fast MA

```python
def _build_aligned_series(...):
    offset = len(fast_ma) - len(slow_ma)
    aligned_fast = fast_ma[offset:]
```

After computing both MAs separately, the longer fast MA has `offset` more bars than the slow MA (because the slow MA's warm-up period is longer). Slicing `fast_ma[offset:]` aligns them so both represent the same set of bars. This works for both EMA and SMA types.

### Histogram direction and state

```python
hist_direction = "INCREASING" if histogram >= histogram_prev else ...
```

- **STRONG_BULLISH**: histogram > 0 AND histogram ≥ histogram_prev (positive and growing)
- **BULLISH_FADING**: histogram > 0 AND histogram < histogram_prev (positive but shrinking)
- **STRONG_BEARISH**: histogram < 0 AND histogram ≤ histogram_prev (negative and getting worse)
- **BEARISH_FADING**: histogram < 0 AND histogram > histogram_prev (negative but recovering)
- **NEUTRAL**: histogram = 0

This matches TradingView's 4-colour histogram colouring exactly.

### Crossover detection

```python
if macd_prev <= signal_prev and macd_val > signal_val:
    crossover = "BULLISH"
```

A crossover only fires on the bar where the relationship *changes* — not on every bar where MACD > Signal. The zero-line context is captured at the crossover bar: if `macd_val >= 0` → ABOVE_ZERO, else BELOW_ZERO. So `BULLISH_BELOW_ZERO` means the MACD crossed above Signal while both were still in negative territory, a classic early-reversal signal.

### Lookback scan for last crossover

After checking today's bar for a crossover, the code scans backwards through up to `crossover_lookback` bars to find the most recent crossover if today has none. It records:
- `last_crossover_type`: e.g. `"BULLISH_BELOW_ZERO"`
- `last_crossover_bars_ago`: 0 = today, 1 = yesterday, …

### MACD state composite

The priority is: **today's crossover first**, then histogram direction if no crossover today. This gives 9 distinct states used for the status badge in the UI.

### `compute_macd_series`

Returns the most recent `num_bars` bars as a list of dicts, each containing `date`, `close`, `macd`, `signal`, `histogram`, `histogram_state` — everything the SVG chart widget needs.
