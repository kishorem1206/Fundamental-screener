# backend/app/divergence/engine.py — Beginner Explanation

> **Source file:** `backend/app/divergence/engine.py`

---

## 1. What is this file?

The core RSI divergence detection engine. It takes a list of OHLCV price bars and returns a list of detected divergence patterns between price swing pivots and RSI values.

**What is RSI divergence?** When price makes a lower low (LL) but the RSI indicator makes a higher low (HL), the two are "diverging" — the price is getting weaker on paper, but the RSI is telling a more bullish story. This is a well-known reversal signal called "Regular Bullish Divergence."

No database, no network calls. Pure math on a list of bars.

---

## 2. Key types

| Type | Meaning |
|------|---------|
| `DivergenceConfig` | All tuneable parameters (pivot window, recency, thresholds) |
| `SwingPivot` | One confirmed price extreme (bar index, date, price, RSI at that bar) |
| `DivergenceResult` | A matched pair of pivots with statistics |
| `DivergenceType` | `REGULAR_BULLISH`, `REGULAR_BEARISH`, `HIDDEN_BULLISH`, `HIDDEN_BEARISH` |
| `DivergenceStatus` | `DEVELOPING`, `CONFIRMED`, `RECENT_CONFIRMED` |

---

## 3. Algorithm step-by-step

### Step 1: Compute full RSI time series — `_rsi_series(closes, period)`

The existing `rsi.py` plugin only computes the *latest* RSI value. Divergence detection needs the RSI at *every* price bar. This function runs Wilder's EMA smoothing across all bars and returns a list where `series[k]` = RSI at `bars[period + k]`.

```python
out = [_r(ag, al)]          # seed RSI at bars[period]
for gi, li in zip(g[period:], l[period:]):
    ag = (ag * (period - 1) + gi) / period
    al = (al * (period - 1) + li) / period
    out.append(_r(ag, al))  # RSI at bars[period+1], bars[period+2], ...
```

The offset `period` means the first RSI is computed after seeing `period+1` closes (required for Wilder's seed). `_bar_rsi(series, bar_idx, period)` converts a bar index to a series index via `k = bar_idx - period`.

### Step 2: Find confirmed swing lows — `_swing_lows(lows, pl, pr)`

A swing low at bar `i` is confirmed when:
- All `pl` bars to the left have HIGHER lows (strict `<`)
- All `pr` bars to the right have HIGHER lows (strict `<`)

```python
for i in range(pl, N - pr):
    v = lows[i]
    if all(v < lows[i-k] for k in range(1, pl+1)) and \
       all(v < lows[i+k] for k in range(1, pr+1)):
        result.append((i, v))
```

With `pivot_left=3, pivot_right=3`: a swing low needs to be lower than 3 bars on each side (7 bars total context). The `range(pl, N-pr)` ensures both sides have enough bars — bars near the very start/end of the data are excluded.

### Step 3: Detect divergence pairs — `_detect_regular_bullish`

For each confirmed swing low that is recent enough (`divergence_age <= max_recency_bars`), search backwards through earlier pivots for a valid pivot1:

```python
for idx2, (p2_bar, p2_price) in enumerate(pivots):
    age = (N - 1) - p2_bar
    if age > cfg.max_recency_bars: continue   # not recent

    for idx1 in range(idx2 - 1, -1, -1):     # search backwards
        # Check: price LL + RSI HL + min separation + min magnitudes
        ...
        break  # stop at the nearest valid pivot1
```

The inner loop breaks at the **first** (nearest) valid pivot1 for each pivot2. This avoids spurious long-distance comparisons and mirrors how most charting platforms detect divergences.

### Step 4: Quality score — `_strength_score`

| Component | Max pts | What drives it |
|-----------|---------|----------------|
| RSI change magnitude | 4 | 15+ pt RSI improvement = max |
| Price drop magnitude | 3 | 5%+ lower low = max |
| RSI oversold level | 2 | RSI ≤ 20 at pivot2 = max, RSI ≥ 40 = 0 |
| Pivot separation | 1 | 15+ bars apart = max |

Score range: 0–10. A score ≥ 7 is a strong, textbook divergence.

---

## 4. Supported divergence types

| Type | Price | RSI | Interpretation |
|------|-------|-----|----------------|
| REGULAR_BULLISH | Lower Low | Higher Low | Reversal up signal |
| REGULAR_BEARISH | Higher High | Lower High | Reversal down signal |
| HIDDEN_BULLISH | Higher Low | Lower Low | Uptrend continuation |
| HIDDEN_BEARISH | Lower High | Higher High | Downtrend continuation |

For V1 the screener defaults to REGULAR_BULLISH only. The others are implemented but optional.

---

## 5. DivergenceConfig defaults

| Parameter | Default | Effect |
|-----------|---------|--------|
| `pivot_left` | 3 | Bars required on left of swing |
| `pivot_right` | 3 | Bars required on right of swing (confirms the pivot) |
| `max_recency_bars` | 10 | Second pivot must be within 10 bars of the last bar |
| `min_bars_between_pivots` | 5 | Avoids pairing adjacent bars |
| `min_rsi_change` | 1.0 | RSI must improve by ≥1 pt |
| `min_price_chg_pct` | 0.1 | Price must drop ≥0.1% for lower low |

Setting `pivot_left=pivot_right=2` finds faster pivots (more signals, more noise). `5/5` finds slower, more significant pivots (fewer signals, higher quality).

---

## 6. Return value

`detect_rsi_divergence(bars, cfg, div_types)` returns a `list[DivergenceResult]` sorted by recency (lowest `divergence_age` first), then by strength descending. Each result contains both `SwingPivot` objects with their dates, prices, and RSI values — everything needed for the UI table and chatbot context.

---

## 7. `get_current_rsi` (added)

```python
def get_current_rsi(bars, period=14) -> tuple[float, float] | None:
```

Returns `(rsi_today, rsi_prev)` — the last two RSI values from the series. Used by the scan service to attach current RSI momentum to each divergence result, enabling the "RSI rising today" filter without re-running full divergence detection. Returns `None` if there are not enough bars.
