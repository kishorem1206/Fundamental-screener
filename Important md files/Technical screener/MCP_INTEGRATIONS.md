# MCP Integrations

## Available MCP Servers

### 1. TradingView MCP — `mcp__tradingview__*`
**Status**: AVAILABLE ✓

Primary use: Technical indicators, charts, OHLCV data, Pine Script execution.

#### Confirmed Tool List

**Chart / State**
- `chart_get_state` — get symbol, timeframe, all indicator names + entity IDs
- `chart_get_visible_range` — get visible date range
- `chart_set_symbol` — change chart ticker
- `chart_set_timeframe` — change resolution
- `chart_set_type` — change chart style
- `chart_set_visible_range` — set visible range
- `chart_manage_indicator` — add/remove studies (use FULL names e.g. "Relative Strength Index")
- `chart_scroll_to_date` — jump to ISO date

**Data**
- `data_get_ohlcv` — get price bars (always pass summary=true unless individual bars needed)
- `data_get_study_values` — get current numeric values from ALL visible indicators (RSI, MACD, BB, EMA, etc.)
- `data_get_equity` — equity data
- `data_get_indicator` — indicator data
- `data_get_pine_boxes` — price zones {high, low} from custom indicators
- `data_get_pine_labels` — text annotations with prices
- `data_get_pine_lines` — horizontal price levels
- `data_get_pine_tables` — table data from custom indicators
- `data_get_strategy_results` — strategy backtest results
- `data_get_trades` — trades data
- `depth_get` — market depth

**Quotes**
- `quote_get` — real-time price snapshot (last, OHLC, volume)
- `symbol_info` — symbol metadata
- `symbol_search` — search for symbols

**Indicators**
- `indicator_add` — add indicator to chart
- `indicator_search` — search indicator library
- `indicator_set_inputs` — change indicator parameters (length, source, etc.)
- `indicator_toggle_visibility` — show/hide indicator

**Layouts & Panes**
- `layout_list`, `layout_new`, `layout_switch`
- `pane_focus`, `pane_list`, `pane_set_layout`, `pane_set_symbol`
- `tab_close`, `tab_list`, `tab_new`, `tab_switch`

**Alerts**
- `alert_create`, `alert_delete`, `alert_list`

**Drawing**
- `draw_clear`, `draw_get_properties`, `draw_list`, `draw_remove_one`
- `draw_shape` — horizontal_line, trend_line, rectangle, text

**Pine Script**
- `pine_analyze`, `pine_check`, `pine_compile`, `pine_smart_compile`
- `pine_get_console`, `pine_get_errors`, `pine_get_source`
- `pine_list_scripts`, `pine_new`, `pine_open`, `pine_save`, `pine_set_source`

**Replay**
- `replay_autoplay`, `replay_start`, `replay_status`, `replay_step`, `replay_stop`, `replay_trade`

**UI Automation**
- `ui_click`, `ui_evaluate`, `ui_find_element`, `ui_fullscreen`
- `ui_hover`, `ui_keyboard`, `ui_mouse_click`, `ui_open_panel`, `ui_scroll`, `ui_type_text`

**Watchlist**
- `watchlist_add`, `watchlist_add_bulk`, `watchlist_get`, `watchlist_remove`

**Batch**
- `batch_run` — run action across multiple symbols/timeframes

**Screenshots**
- `capture_screenshot` — regions: "full", "chart", "strategy_tester"

**System**
- `tv_discover`, `tv_health_check`, `tv_launch`, `tv_ui_state`, `tv_update`

#### Capability Matrix — TradingView MCP

| Capability | Tool | Notes |
|---|---|---|
| RSI | `data_get_study_values` | Indicator must be visible on chart |
| Bollinger Bands | `data_get_study_values` | Indicator must be visible on chart |
| MACD | `data_get_study_values` | Indicator must be visible on chart |
| EMA/SMA | `data_get_study_values` | Indicator must be visible on chart |
| OHLCV | `data_get_ohlcv` | Use summary=true for batch |
| Real-time quote | `quote_get` | last, OHLC, volume |
| Symbol info | `symbol_info` | metadata |
| Symbol search | `symbol_search` | lookup |
| Multi-stock batch | `batch_run` | key for 750-stock screening |
| Alerts | `alert_create` | Price/indicator alerts |
| Pine Script | `pine_set_source` + `pine_smart_compile` | Custom calculations |

#### IMPORTANT: TradingView MCP Gotcha
- Indicators must be **VISIBLE on chart** for `data_get_study_values` to work.
- Always call `chart_get_state` first to get entity IDs.
- Always use `indicator_add` with **FULL names**: "Relative Strength Index" not "RSI".
- `batch_run` is essential for screening 750 stocks — use it instead of sequential symbol changes.

---

### 2. INDMoney MCP — `mcp__claude_ai_INDMoney__*`
**Status**: AVAILABLE ✓

Primary use: Indian market data, stock details, OHLC, F&O, fundamentals, portfolio.

#### Confirmed Tool List

**Lookup**
- `lookup_ind_keys` — **ALWAYS call first** to resolve stock/index/derivative/MF name to `ind_key`
  - filter_type: "IN_STOCKS_FNO" for equity/index derivatives
  - filter_type: "IN_COMMODITY" for MCX commodities

**Stock Data**
- `get_indian_stocks_details` — stock details (price, fundamentals, classification)
- `get_indian_stocks_ohlc` — OHLC data
- `get_indian_stocks_movers` — top gainers/losers/volume
- `get_indian_stocks_greeks_history` — options greeks history
- `get_indian_stocks_option_chain` — option chain data

**Mutual Funds**
- `get_mf_by_category` — MF by category
- `get_mf_funds_details` — MF details
- `mf_sips` — MF SIP data

**US Stocks**
- `get_us_stocks_details`

**Indian Stock SIPs**
- `indian_stocks_sips`

**Portfolio / Net Worth**
- `networth_snapshot` — total net worth, full allocation, liabilities
- `networth_allocation_breakdown` — breakdown by asset class
- `networth_holdings` — holdings detail
- `get_family_asset_holdings`
- `get_family_members`
- `get_family_portfolio`

**Other**
- `user_watchlist` — user's watchlist

#### Capability Matrix — INDMoney MCP

| Capability | Tool | Notes |
|---|---|---|
| Market cap | `get_indian_stocks_details` | After `lookup_ind_keys` |
| PE, PB, ROE | `get_indian_stocks_details` | Fundamentals |
| OHLC | `get_indian_stocks_ohlc` | After `lookup_ind_keys` |
| Sector/Industry | `get_indian_stocks_details` | Classification |
| Option chain | `get_indian_stocks_option_chain` | F&O data |
| Top movers | `get_indian_stocks_movers` | Gainers/losers |
| Portfolio | `networth_snapshot` | User's own portfolio |

#### IMPORTANT: INDMoney MCP Gotcha
- **Always call `lookup_ind_keys` first** before any stock/index/derivative/MF call.
- Never assume or guess `ind_key` values.
- MCX commodities use `filter_type="IN_COMMODITY"` — never IN_STOCKS_FNO for commodities.

---

### 3. Kite MCP — `mcp__kite__*`
**Status**: AVAILABLE ✓ (confirmed 2026-08-21)

Config: `npx mcp-remote https://mcp.kite.trade/mcp` (remote MCP via Zerodha)
Project file: `.mcp.json` → approved in `.claude/settings.json`

**Authentication**: Call `mcp__kite__login` first if session expired — it returns an OAuth link for the user to click.

**Symbol format**: `exchange:tradingsymbol` e.g. `NSE:INFY`, `NSE:SBIN`, `BSE:RELIANCE`

**Instrument tokens**: `get_historical_data` requires a numeric `instrument_token` — always call `search_instruments` first to get it. Never guess tokens.

#### Confirmed Tool List (all 22 tools)

**Auth**
- `mcp__kite__login` — returns OAuth link; call at session start if tools fail

**Market Data (V1 READ-ONLY)**
- `mcp__kite__get_ltp` — latest trading price for list of `exchange:symbol` instruments
- `mcp__kite__get_ohlc` — OHLC snapshot for list of instruments
- `mcp__kite__get_quotes` — full market data snapshot up to **500 instruments** at once (OHLC, depth, OI, volume); key for bulk screening
- `mcp__kite__get_historical_data` — historical candles (minute/3min/5min/10min/15min/30min/60min/day); requires `instrument_token` from `search_instruments`
- `mcp__kite__search_instruments` — search by name/symbol to get numeric `instrument_token`

**Portfolio (V1 READ-ONLY)**
- `mcp__kite__get_profile` — user profile, available exchanges and products
- `mcp__kite__get_holdings` — equity holdings (paginated)
- `mcp__kite__get_positions` — current intraday/overnight positions (paginated)
- `mcp__kite__get_margins` — account margins
- `mcp__kite__get_mf_holdings` — mutual fund holdings (paginated)
- `mcp__kite__get_trades` — trade history (paginated)

**Orders (READ-ONLY in V1 — use for monitoring only, NEVER for placement)**
- `mcp__kite__get_orders` — all orders (paginated)
- `mcp__kite__get_order_history` — history of a specific order
- `mcp__kite__get_order_trades` — trades for a specific order
- `mcp__kite__get_gtts` — active GTT orders (paginated)

**⛔ ORDER EXECUTION — DO NOT USE IN V1**
- `mcp__kite__place_order` — place order (blocked in V1)
- `mcp__kite__modify_order` — modify order (blocked in V1)
- `mcp__kite__cancel_order` — cancel order (blocked in V1)
- `mcp__kite__place_gtt_order` — place GTT (blocked in V1)
- `mcp__kite__modify_gtt_order` — modify GTT (blocked in V1)
- `mcp__kite__delete_gtt_order` — delete GTT (blocked in V1)

#### Capability Matrix — Kite MCP

| Capability | Tool | Notes |
|---|---|---|
| Real-time LTP | `get_ltp` | `NSE:SYMBOL` format |
| OHLC snapshot | `get_ohlc` | `NSE:SYMBOL` format |
| Full market depth | `get_quotes` | Up to **500 instruments** per call |
| Historical candles | `get_historical_data` | Needs `instrument_token` from `search_instruments` |
| Symbol → token | `search_instruments` | Required before `get_historical_data` |
| Holdings | `get_holdings` | User's equity holdings |
| Positions | `get_positions` | Current positions |

#### IMPORTANT: Kite MCP Gotchas
- `get_quotes` handles 500 instruments per call — use 2 calls for full 750-stock Nifty Total Market.
- `get_historical_data` needs a numeric `instrument_token`, NOT a symbol string. Always call `search_instruments` first.
- Symbol format is `exchange:tradingsymbol` — `NSE:INFY` not just `INFY`.
- Exchanges: `NSE`, `BSE`, `MCX`, `NFO`, `BFO`.

---

## MCP Capability Registry

```json
{
  "TRADINGVIEW_MCP": {
    "status": "AVAILABLE",
    "capabilities": [
      "RSI", "BOLLINGER_BANDS", "MACD", "EMA", "SMA",
      "OHLCV", "REAL_TIME_QUOTE", "SYMBOL_INFO", "SYMBOL_SEARCH",
      "BATCH_INDICATOR", "ALERTS", "PINE_SCRIPT", "CHARTS"
    ]
  },
  "INDMONEY_MCP": {
    "status": "AVAILABLE",
    "capabilities": [
      "MARKET_CAP", "FUNDAMENTALS", "OHLC",
      "SECTOR_CLASSIFICATION", "OPTION_CHAIN", "TOP_MOVERS",
      "PORTFOLIO", "WATCHLIST"
    ]
  },
  "KITE_MCP": {
    "status": "AVAILABLE",
    "capabilities": [
      "LTP", "OHLC", "QUOTES_BULK_500", "HISTORICAL_CANDLES",
      "INSTRUMENT_SEARCH", "HOLDINGS", "POSITIONS", "MARGINS"
    ],
    "note": "mcp-remote to kite.trade. Symbol format: NSE:SYMBOL. get_quotes handles 500 instruments/call."
  }
}
```

## Provider Preference Table

| Capability | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| RSI | TradingView MCP | Internal IndicatorEngine | — |
| Bollinger Bands | TradingView MCP | Internal IndicatorEngine | — |
| OHLCV (historical) | Kite MCP | TradingView MCP | INDMoney MCP |
| Real-time quote / LTP | Kite MCP | TradingView MCP | INDMoney MCP |
| Bulk quotes (500 stocks) | Kite MCP `get_quotes` | TradingView `batch_run` | — |
| Market cap | INDMoney MCP | — | — |
| Fundamentals (PE/PB/ROE) | INDMoney MCP | — | — |
| Sector/Industry | INDMoney MCP | Static seed data | — |
| Option chain | INDMoney MCP | — | — |
| Instrument token lookup | Kite `search_instruments` | — | — |
