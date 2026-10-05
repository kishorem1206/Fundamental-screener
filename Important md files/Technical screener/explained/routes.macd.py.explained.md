# backend/app/routes/macd.py — Beginner Explanation

**Source file:** `backend/app/routes/macd.py`

## What this file does

This file defines two HTTP endpoints that the MACD page calls:

- `POST /macd/scan` — runs a full universe scan with configurable MACD parameters and filters, returns up to 1000 matched stocks
- `POST /macd/chart` — fetches the MACD time series for a single stock (used when the user clicks a row to open the chart)

The file handles request validation via Pydantic models and delegates all business logic to `macd_service`.

## Key sections

### `MACDScanRequest`

```python
class MACDScanRequest(BaseModel):
    universe:           str         = "NIFTY_500"
    source:             SourceType  = "Close"
    fast:               int         = Field(default=12,  ge=2,  le=50)
    slow:               int         = Field(default=26,  ge=3,  le=200)
    signal_period:      int         = Field(default=9,   ge=1,  le=50)
    osc_ma_type:        MAType      = "EMA"
    sig_ma_type:        MAType      = "EMA"
    timeframe:          TFType      = "1D"
    hist_filters:       list[HistFilter]   = []
    cross_filters:      list[CrossFilter]  = []
    cross_bars:         int         = Field(default=5,   ge=1,  le=50)
    crossover_lookback: int         = Field(default=20,  ge=5,  le=50)
    limit:              int         = Field(default=300, ge=1,  le=1000)
    offset:             int         = Field(default=0,   ge=0)
```

- `source`: which price to use for computing MA values (Close, Open, High, Low, HL2, HLC3, OHLC4)
- `osc_ma_type` / `sig_ma_type`: EMA or SMA independently for the oscillator and signal line
- `hist_filters`: OR-list of histogram states to require (empty = show all)
- `cross_filters`: OR-list of crossover types to require (empty = show all)
- `cross_bars`: the "within N candles" window for crossover filters
- `crossover_lookback`: how far back to scan for the most recent crossover event (default 20 bars)

Pydantic enforces all the `ge`/`le` constraints before the route function is ever called, so the service never receives out-of-range values.

### `MACDChartRequest`

```python
class MACDChartRequest(BaseModel):
    exchange:      str       = "NSE"
    symbol:        str
    ...
    num_bars:      int       = Field(default=80, ge=20, le=300)
```

`symbol` has no default — it is required. `num_bars` controls how many bars the chart SVG receives; more bars = more history but slower response.

### Chart 404 handling

```python
if data is None:
    raise HTTPException(status_code=404, detail="Could not compute MACD series for this stock")
```

`get_chart_data` returns `None` when there isn't enough price history to satisfy the MA warm-up period (e.g. a recently listed stock). The frontend treats a chart error as non-fatal and just shows "Chart unavailable".

### Registration in `main.py`

```python
app.include_router(macd.router)
```

No prefix is set — the routes are `/macd/scan` and `/macd/chart` at the root level, consistent with the other indicator routes (`/rsi-momentum/scan`, `/rsi-divergence/scan`).
