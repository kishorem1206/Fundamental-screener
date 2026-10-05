# Coin fields

Crypto coins / assets (market: `coin`).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/coin.html>

**598 fields** (3253 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 1 values: `spot` |
| `is_primary` | Primary Listing | bool |  |  |
| `active_symbol` | Current trading day | bool |  |  |
| `change` | Change % | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `change_abs` | Change | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `close` | Price | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `price_earnings_ttm` | Price to Earnings Ratio (TTM) | number |  |  |
| `sector` | Group | text |  |  |
| `Recommend.All` | Technical Rating | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `volume` | Volume | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `High.1M` | 1-Month High | number |  |  |
| `Low.1M` | 1-Month Low | number |  |  |
| `High.3M` | 3-Month High | number |  |  |
| `Low.3M` | 3-Month Low | number |  |  |
| `Perf.3M` | 3-Month Performance | number |  |  |
| `Perf.5Y` | 5Y Performance | number |  |  |
| `High.6M` | 6-Month High | number |  |  |
| `Low.6M` | 6-Month Low | number |  |  |
| `Perf.6M` | 6-Month Performance | number |  |  |
| `price_52_week_high` | 52 Week High | number |  |  |
| `price_52_week_low` | 52 Week Low | number |  |  |
| `High.All` | All Time High | number |  |  |
| `Low.All` | All Time Low | number |  |  |
| `Perf.All` | All Time Performance | number |  |  |
| `Aroon.Down` | Aroon Down (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Aroon.Up` | Aroon Up (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADR` | Average Day Range (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX` | Average Directional Index (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ATR` | Average True Range (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `average_volume_10d_calc` | Average Volume (10 day) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `average_volume_30d_calc` | Average Volume (30 day) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `average_volume_60d_calc` | Average Volume (60 day) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `average_volume_90d_calc` | Average Volume (90 day) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `AO` | Awesome Oscillator | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BB.lower` | Bollinger Lower Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BB.upper` | Bollinger Upper Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BBPower` | Bull Bear Power | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ChaikinMoneyFlow` | Chaikin Money Flow (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `change_from_open` | Change from Open % | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `change_from_open_abs` | Change from Open | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `CCI20` | Commodity Channel Index (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `country` | Region | text |  |  |
| `DonchCh20.Lower` | Donchian Channels Lower Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `DonchCh20.Upper` | Donchian Channels Upper Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `exchange` | Exchange | text |  | 1 values: `CRYPTO` |
| `EMA5` | Exponential Moving Average (5) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA10` | Exponential Moving Average (10) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA20` | Exponential Moving Average (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA30` | Exponential Moving Average (30) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA50` | Exponential Moving Average (50) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA100` | Exponential Moving Average (100) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA200` | Exponential Moving Average (200) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `free_cash_flow_margin_fy` | Free Cash Flow Margin (FY) | percent |  |  |
| `free_cash_flow_margin_ttm` | Free Cash Flow Margin (TTM) | percent |  |  |
| `gap` | Gap % | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gross_profit_margin_fy` | Gross Margin (FY) | percent |  |  |
| `high` | High | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `HullMA9` | Hull Moving Average (9) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.BLine` | Ichimoku Base Line (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.CLine` | Ichimoku Conversion Line (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.Lead1` | Ichimoku Leading Span A (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.Lead2` | Ichimoku Leading Span B (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `KltChnl.lower` | Keltner Channels Lower Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `KltChnl.upper` | Keltner Channels Upper Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `low` | Low | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `MACD.macd` | MACD Level (12, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `MACD.signal` | MACD Signal (12, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Mom` | Momentum (10) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `MoneyFlow` | Money Flow (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Perf.1M` | Monthly Performance | number |  |  |
| `Recommend.MA` | Moving Averages Rating | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI` | Negative Directional Indicator (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `net_income_bef_disc_oper_margin_fy` | Net Margin (FY) | percent |  |  |
| `open` | Open | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `oper_income_margin_fy` | Operating Margin (FY) | percent |  |  |
| `Recommend.Other` | Oscillators Rating | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `P.SAR` | Parabolic SAR | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Camarilla.Middle` | Pivot Camarilla P | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Camarilla.R1` | Pivot Camarilla R1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Camarilla.R2` | Pivot Camarilla R2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Camarilla.R3` | Pivot Camarilla R3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Camarilla.S1` | Pivot Camarilla S1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Camarilla.S2` | Pivot Camarilla S2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Camarilla.S3` | Pivot Camarilla S3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Classic.Middle` | Pivot Classic P | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Classic.R1` | Pivot Classic R1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Classic.R2` | Pivot Classic R2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Classic.R3` | Pivot Classic R3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Classic.S1` | Pivot Classic S1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Classic.S2` | Pivot Classic S2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Classic.S3` | Pivot Classic S3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Demark.Middle` | Pivot DM P | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Demark.R1` | Pivot DM R1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Demark.S1` | Pivot DM S1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Fibonacci.Middle` | Pivot Fibonacci P | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Fibonacci.R1` | Pivot Fibonacci R1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Fibonacci.R2` | Pivot Fibonacci R2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Fibonacci.R3` | Pivot Fibonacci R3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Fibonacci.S1` | Pivot Fibonacci S1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Fibonacci.S2` | Pivot Fibonacci S2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Fibonacci.S3` | Pivot Fibonacci S3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Woodie.Middle` | Pivot Woodie P | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Woodie.R1` | Pivot Woodie R1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Woodie.R2` | Pivot Woodie R2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Woodie.R3` | Pivot Woodie R3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Woodie.S1` | Pivot Woodie S1 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Woodie.S2` | Pivot Woodie S2 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Pivot.M.Woodie.S3` | Pivot Woodie S3 | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI` | Positive Directional Indicator (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `postmarket_change` | Post-market Change % | percent |  |  |
| `postmarket_change_abs` | Post-market Change | price |  |  |
| `premarket_change` | Pre-market Change % | percent |  |  |
| `premarket_change_abs` | Pre-market Change | price |  |  |
| `premarket_change_from_open` | Pre-market Change from Open % | percent |  |  |
| `premarket_change_from_open_abs` | Pre-market Change from Open | number |  |  |
| `premarket_gap` | Pre-market Gap % | percent |  |  |
| `price_book_ratio` | Price to Book (FY) | number |  |  |
| `price_book_fq` | Price to Book (MRQ) | number |  |  |
| `price_free_cash_flow_ttm` | Price to Free Cash Flow (TTM) | number |  |  |
| `price_revenue_ttm` | Price to Revenue Ratio (TTM) | number |  |  |
| `price_sales_ratio` | Price to Sales (FY) | number |  |  |
| `ROC` | Rate Of Change (9) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI7` | Relative Strength Index (7) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI` | Relative Strength Index (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `relative_volume_10d_calc` | Relative Volume | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `research_and_dev_ratio_fy` | Research & development Ratio (FY) | percent |  |  |
| `research_and_dev_ratio_ttm` | Research & development Ratio (TTM) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_fy` | Selling General & Admin expenses Ratio (FY) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_ttm` | Selling General & Admin expenses Ratio (TTM) | percent |  |  |
| `SMA5` | Simple Moving Average (5) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA10` | Simple Moving Average (10) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA20` | Simple Moving Average (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA30` | Simple Moving Average (30) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA50` | Simple Moving Average (50) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA100` | Simple Moving Average (100) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA200` | Simple Moving Average (200) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D` | Stochastic %D (14, 3, 3) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K` | Stochastic %K (14, 3, 3) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.RSI.K` | Stochastic RSI Fast (3, 3, 14, 14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.RSI.D` | Stochastic RSI Slow (3, 3, 14, 14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `submarket` | Submarket | text |  | 1 values: `` |
| `UO` | Ultimate Oscillator (7, 14, 28) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Volatility.D` | Volatility | number |  |  |
| `Volatility.M` | Volatility Month | number |  |  |
| `Volatility.W` | Volatility Week | number |  |  |
| `VWAP` | Volume Weighted Average Price | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `VWMA` | Volume Weighted Moving Average (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Perf.W` | Weekly Performance | number |  |  |
| `W.R` | Williams Percent Range (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Perf.Y` | Yearly Performance | number |  |  |
| `Perf.YTD` | YTD Performance | number |  |  |
| `centralization` | Exchange type | text |  |  |
| `currency` | Quote currency | text |  | 1 values: `USD` |
| `24h_vol_change\|5` | Volume 24h Change % | number |  |  |
| `24h_vol\|5` | Volume 24h in USD | fundamental_price |  |  |
| `ask` | Ask | price |  |  |
| `total_shares_outstanding` | Available Coins | number |  |  |
| `bid` | Bid | price |  |  |
| `market_cap_diluted_calc` | Fully Diluted Market Cap | number |  |  |
| `market_cap_calc` | Market Capitalization | number |  |  |
| `total_shares_diluted` | Total Coins | number |  |  |
| `total_value_traded` | Traded Volume | fundamental_price |  |  |
| `24h_close_change\|5` |  | number |  |  |
| `24h_close_change_abs\|5` |  | number |  |  |
| `24h_close_prev\|5` |  | number |  |  |
| `24h_vol_change_abs\|5` |  | number |  |  |
| `24h_vol_change_cmc` |  | number |  |  |
| `24h_vol_cmc` |  | fundamental_price |  |  |
| `24h_vol_prev\|5` |  | number |  |  |
| `24h_vol_to_market_cap` |  | number |  |  |
| `ADRP` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_9` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_20` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_100` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_100[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_50` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_20[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_50[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX+DI_9[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_9` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_20` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_100` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_100[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_50` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_20[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_50[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI_9[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX_9` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX_20` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX_100` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX_50` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `AO[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `AO[2]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ATRP` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BB.basis` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BB.basis_50` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BB.lower_50` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BB.upper_50` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `CCI20[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.3BlackCrows` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.3WhiteSoldiers` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.AbandonedBaby.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.AbandonedBaby.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.DarkCloudCover.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Doji` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Doji.Dragonfly` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Doji.Gravestone` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.DojiStar.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.DojiStar.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.DownsideTasukiGap.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Engulfing.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Engulfing.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.EveningDojiStar.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.EveningStar` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.FallingThreeMethods.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.FallingWindow.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Hammer` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.HangingMan` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Harami.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Harami.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.HaramiCross.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.HaramiCross.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.InvertedHammer` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Kicking.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Kicking.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.LongShadow.Lower` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.LongShadow.Upper` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Marubozu.Black` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Marubozu.White` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.MorningDojiStar.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.MorningStar` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.OnNeck.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.Piercing.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.RisingThreeMethods.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.RisingWindow.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.ShootingStar` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.SpinningTop.Black` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.SpinningTop.White` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.TriStar.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.TriStar.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.TweezerBottom.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.TweezerTop.Bearish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Candle.UpsideTasukiGap.Bullish` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `DonchCh20.Middle` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA2` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA6` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA7` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA8` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA9` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA12` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA13` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA14` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA15` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA21` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA25` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA26` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA34` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA40` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA120` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA144` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA150` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA250` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA300` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA55` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA60` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA75` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA89` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `High.1M.Date` |  | time |  |  |
| `High.3M.Date` |  | time |  |  |
| `High.5D` |  | number |  |  |
| `High.6M.Date` |  | time |  |  |
| `High.All.Calc` |  | number |  |  |
| `High.All.Calc.Date` |  | time |  |  |
| `High.All.Date` |  | time |  |  |
| `HullMA20` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `HullMA200` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.BLine_20_60_120_30` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.CLine_20_60_120_30` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.Lead1_20_60_120_30` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.Lead2_20_60_120_30` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `KltChnl.basis` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Low.1M.Date` |  | time |  |  |
| `Low.3M.Date` |  | time |  |  |
| `Low.5D` |  | number |  |  |
| `Low.6M.Date` |  | time |  |  |
| `Low.After.High.All` |  | price |  |  |
| `Low.All.Calc` |  | number |  |  |
| `Low.All.Calc.Date` |  | time |  |  |
| `Low.All.Date` |  | time |  |  |
| `MACD.hist` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Mom[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Mom_14` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Mom_14[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Open.All.Calc` |  | number |  |  |
| `Perf.10Y` |  | number |  |  |
| `Perf.10Y_abs` |  | number |  |  |
| `Perf.1M_abs` |  | number |  |  |
| `Perf.3M_abs` |  | number |  |  |
| `Perf.3Y` |  | number |  |  |
| `Perf.3Y_abs` |  | number |  |  |
| `Perf.5D` |  | number |  |  |
| `Perf.5D_abs` |  | number |  |  |
| `Perf.5Y_abs` |  | number |  |  |
| `Perf.6M_abs` |  | number |  |  |
| `Perf.All_abs` |  | number |  |  |
| `Perf.W_abs` |  | number |  |  |
| `Perf.YTD_abs` |  | number |  |  |
| `Perf.Y_abs` |  | number |  |  |
| `RSI2` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI4` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI5` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI9` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI10` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI20` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI21` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI30` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI10[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI20[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI21[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI2[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI30[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI4[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI5[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI7[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI9[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Rec.BBPower` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Rec.HullMA9` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Rec.Ichimoku` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Rec.Stoch.RSI` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Rec.UO` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Rec.VWMA` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Rec.WR` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA2` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA6` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA7` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA8` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA9` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA12` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA13` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA14` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA15` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA21` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA25` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA26` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA34` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA40` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA120` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA144` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA150` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA250` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA300` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA55` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA60` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA75` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `SMA89` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_14_1_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_14_1_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_5_3_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_5_3_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_6_3_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_6_3_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_8_3_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.D_8_3_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_14_1_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_14_1_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_5_3_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_5_3_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_6_3_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_6_3_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_8_3_3` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Stoch.K_8_3_3[1]` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `active_addresses_ratio` |  | percent |  |  |
| `addresses_active` |  | number |  |  |
| `addresses_new` |  | number |  |  |
| `addresses_total` |  | number |  |  |
| `addresses_zero_balance` |  | number |  |  |
| `all_time_high` |  | price |  |  |
| `all_time_high_day` |  | time |  |  |
| `all_time_low` |  | price |  |  |
| `all_time_low_day` |  | time |  |  |
| `all_time_open` |  | price |  |  |
| `altrank` |  | number |  |  |
| `at_the_money_addresses_percentage` |  | percent |  |  |
| `average_transaction_usd` |  | fundamental_price |  |  |
| `avg_balance` |  | fundamental_price |  |  |
| `bars_count` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `base_currency_kind` |  | text |  | 1 values: `crypto` |
| `bid_ask_spread_pct` |  | percent |  |  |
| `blockchain-id` |  | text |  |  |
| `break_even_addresses_percentage` |  | percent |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fy` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fy` |  | number |  |  |
| `circulating_supply` |  | number |  |  |
| `circulating_to_max_supply_ratio` |  | percent |  |  |
| `close_usd\|5` |  | number |  |  |
| `contributorsactive` |  | number |  |  |
| `contributorscreated` |  | number |  |  |
| `coupon` |  | number |  |  |
| `crypto_blockchain_ecosystems` |  | set |  | 46 values: `abstract-chain-ecosystem`, `algorand-ecosystem`, `arbitrum-ecosystem`, `avalanche-ecosystem`, `bera-chain-ecosystem`, `bitcoin-ecosystem`, `blast-ecosystem`, `bnb-chain-ecosystem`, `cardano-ecosystem`, `celo-ecosystem`, `chiliz-ecosystem`, `chromia-ecosystem`, `cosmos-ecosystem`, `cronos-ecosystem`, `eigenlayer-ecosystem`, `ethereum-ecosystem`, `everscale-ecosystem`, `fantom-ecosystem`, `gnosis-chain-ecosystem`, `harmony-ecosystem`, `heco-ecosystem`, `hyperevm-ecosystem`, `iotex-ecosystem`, `monad-ecosystem`, `moonriver-ecosystem` … |
| `crypto_categories` |  | set |  | 119 values: `abstract-chain-ecosystem`, `algorand-ecosystem`, `algorithmic-stablecoins`, `analytics`, `animal-memes`, `arbitrum-ecosystem`, `asset-backed-stablecoins`, `asset-backed-tokens`, `asset-management`, `avalanche-ecosystem`, `bera-chain-ecosystem`, `bitcoin-ecosystem`, `blast-ecosystem`, `bnb-chain-ecosystem`, `cardano-ecosystem`, `celo-ecosystem`, `centralized-exchange`, `chiliz-ecosystem`, `chromia-ecosystem`, `collectibles-nfts`, `cosmos-ecosystem`, `cronos-ecosystem`, `cryptocurrencies`, `cybersecurity`, `dao` … |
| `crypto_code` |  | text |  |  |
| `crypto_common_categories` |  | set |  | 69 values: `algorithmic-stablecoins`, `analytics`, `animal-memes`, `asset-backed-stablecoins`, `asset-backed-tokens`, `asset-management`, `centralized-exchange`, `collectibles-nfts`, `cryptocurrencies`, `cybersecurity`, `dao`, `data-management-ai`, `decentralized-exchange`, `defi`, `depin`, `derivatives`, `developments-tools`, `distributed-computing-storage`, `e-commerce`, `education`, `energy`, `enterprise-solutions`, `events`, `exchange-based-tokens`, `fan-tokens` … |
| `crypto_consensus_algorithms` |  | set |  | 4 values: `hybrid-algorithm`, `proof-of-authority`, `proof-of-stake-algorithm`, `proof-of-work-algorithm` |
| `crypto_total_rank` |  | number |  |  |
| `cryptoasset-info.description` |  | text |  |  |
| `cryptoasset-info.id` |  | text |  |  |
| `currency_id` |  | text |  | 1 values: `USD` |
| `currency_kind` |  | text |  | 1 values: `fiat` |
| `current_session` |  | text |  | 1 values: `market` |
| `current_yield` |  | percent |  |  |
| `daily-bar.time` |  | number |  |  |
| `days_to_maturity` |  | number |  |  |
| `description` |  | text |  |  |
| `dex_buy_volume_12h` |  | price |  |  |
| `dex_buy_volume_15m` |  | price |  |  |
| `dex_buy_volume_1h` |  | price |  |  |
| `dex_buy_volume_24h` |  | price |  |  |
| `dex_buy_volume_4h` |  | price |  |  |
| `dex_buyers_12h` |  | number |  |  |
| `dex_buyers_15m` |  | number |  |  |
| `dex_buyers_1h` |  | number |  |  |
| `dex_buyers_24h` |  | number |  |  |
| `dex_buyers_4h` |  | number |  |  |
| `dex_buys_12h` |  | number |  |  |
| `dex_buys_15m` |  | number |  |  |
| `dex_buys_1h` |  | number |  |  |
| `dex_buys_24h` |  | number |  |  |
| `dex_buys_4h` |  | number |  |  |
| `dex_created_time` |  | time |  |  |
| `dex_sell_volume_12h` |  | price |  |  |
| `dex_sell_volume_15m` |  | price |  |  |
| `dex_sell_volume_1h` |  | price |  |  |
| `dex_sell_volume_24h` |  | price |  |  |
| `dex_sell_volume_4h` |  | price |  |  |
| `dex_sellers_12h` |  | number |  |  |
| `dex_sellers_15m` |  | number |  |  |
| `dex_sellers_1h` |  | number |  |  |
| `dex_sellers_24h` |  | number |  |  |
| `dex_sellers_4h` |  | number |  |  |
| `dex_sells_12h` |  | number |  |  |
| `dex_sells_15m` |  | number |  |  |
| `dex_sells_1h` |  | number |  |  |
| `dex_sells_24h` |  | number |  |  |
| `dex_sells_4h` |  | number |  |  |
| `dex_total_liquidity` |  | number |  |  |
| `dex_total_supply` |  | number |  |  |
| `dex_trading_volume_12h` |  | price |  |  |
| `dex_trading_volume_15m` |  | price |  |  |
| `dex_trading_volume_1h` |  | price |  |  |
| `dex_trading_volume_24h` |  | price |  |  |
| `dex_trading_volume_4h` |  | price |  |  |
| `dex_txs_count_12h` |  | number |  |  |
| `dex_txs_count_15m` |  | number |  |  |
| `dex_txs_count_1h` |  | number |  |  |
| `dex_txs_count_24h` |  | number |  |  |
| `dex_txs_count_4h` |  | number |  |  |
| `dex_txs_count_uniq_12h` |  | number |  |  |
| `dex_txs_count_uniq_15m` |  | number |  |  |
| `dex_txs_count_uniq_1h` |  | number |  |  |
| `dex_txs_count_uniq_24h` |  | number |  |  |
| `dex_txs_count_uniq_4h` |  | number |  |  |
| `earnings_yield` |  | percent |  |  |
| `enterprise_value_ebit_fwd` |  | number |  |  |
| `enterprise_value_ebitda_fwd` |  | number |  |  |
| `enterprise_value_sales_fwd` |  | number |  |  |
| `eps_surprise_percent_fq` |  | percent |  |  |
| `expiration` |  | time |  |  |
| `first_bar_time` |  | time |  |  |
| `float_shares_percent_current` |  | percent |  |  |
| `fractional` |  | text |  | 1 values: `false` |
| `fully_diluted_value` |  | price |  |  |
| `funding_rate` |  | number |  |  |
| `galaxyscore` |  | number |  |  |
| `gap_down` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_down_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_up` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_up_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `github_commits` |  | number |  |  |
| `in_the_money_addresses_percentage` |  | percent |  |  |
| `indexes` |  | interface |  |  |
| `indicators_bars_count` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `interactions` |  | number |  |  |
| `is_blacklisted` |  | bool |  |  |
| `is_shariah_compliant` |  | bool |  |  |
| `is_symbol_primary_listing` |  | bool |  |  |
| `kind` |  | text |  | 1 values: `rt` |
| `kind-delay` |  | number |  |  |
| `large_tx_count` |  | number |  |  |
| `large_tx_volume_usd` |  | fundamental_price |  |  |
| `last-price-update-time` |  | time |  |  |
| `last-price-update-time-intraday` |  | time |  |  |
| `last_bar_update_time` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `liquidations_volume_12h` |  | number |  |  |
| `liquidations_volume_15m` |  | number |  |  |
| `liquidations_volume_1h` |  | number |  |  |
| `liquidations_volume_24h` |  | number |  |  |
| `liquidations_volume_4h` |  | number |  |  |
| `logoid` |  | text |  |  |
| `long_liquidations_volume_12h` |  | number |  |  |
| `long_liquidations_volume_15m` |  | number |  |  |
| `long_liquidations_volume_1h` |  | number |  |  |
| `long_liquidations_volume_24h` |  | number |  |  |
| `long_liquidations_volume_4h` |  | number |  |  |
| `losses_addresses_percentage` |  | percent |  |  |
| `low_after_high_all_change` |  | percent |  |  |
| `low_after_high_all_change_abs` |  | price |  |  |
| `market` |  | text |  | 1 values: `coin` |
| `market_cap` |  | fundamental_price |  |  |
| `market_cap_to_tvl` |  | number |  |  |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `max_supply` |  | number |  |  |
| `minmov` |  | number |  |  |
| `minmove2` |  | number |  |  |
| `minute-bar.time` |  | number |  |  |
| `name` |  | text |  |  |
| `non_gaap_price_to_earnings_per_share_forecast_next_fy` |  | number |  |  |
| `nvt` |  | number |  |  |
| `open_interest` |  | number |  |  |
| `open_interest_change_percent_12h` |  | number |  |  |
| `open_interest_change_percent_15m` |  | number |  |  |
| `open_interest_change_percent_1h` |  | number |  |  |
| `open_interest_change_percent_24h` |  | number |  |  |
| `open_interest_change_percent_4h` |  | number |  |  |
| `open_interest_to_volume_24h` |  | number |  |  |
| `out_the_money_addresses_percentage` |  | percent |  |  |
| `post_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `postsactive` |  | number |  |  |
| `postscreated` |  | number |  |  |
| `pre_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `pre_change_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `price_52_week_high_date` |  | time |  |  |
| `price_52_week_low_date` |  | time |  |  |
| `price_book_fwd` |  | number |  |  |
| `price_earnings_fwd` |  | number |  |  |
| `price_sales` |  | price |  |  |
| `price_sales_fwd` |  | number |  |  |
| `price_target_1y` |  | price |  |  |
| `price_target_1y_delta` |  | percent |  |  |
| `price_to_cash_f_operating_activities_ttm` |  | number |  |  |
| `price_to_cash_ratio` |  | number |  |  |
| `price_to_working_capital_fq` |  | number |  |  |
| `pricescale` |  | number |  |  |
| `profit_addresses_percentage` |  | percent |  |  |
| `provider-id` |  | text |  | 1 values: `tvc` |
| `relative_volume` |  | number |  |  |
| `revenue_surprise_percent_fq` |  | percent |  |  |
| `rtc` |  | price |  |  |
| `sentiment` |  | percent |  |  |
| `short_liquidations_volume_12h` |  | number |  |  |
| `short_liquidations_volume_15m` |  | number |  |  |
| `short_liquidations_volume_1h` |  | number |  |  |
| `short_liquidations_volume_24h` |  | number |  |  |
| `short_liquidations_volume_4h` |  | number |  |  |
| `shrhldrs_equity_to_total_assets_fq` |  | number |  |  |
| `shrhldrs_equity_to_total_assets_fy` |  | number |  |  |
| `social_volume_24h` |  | number |  |  |
| `socialdominance` |  | percent |  |  |
| `source-logoid` |  | text |  | 1 values: `source/CRYPTO` |
| `subsessions` |  | interface |  |  |
| `subtype` |  | text |  | 1 values: `crypto` |
| `telegram_members` |  | number |  |  |
| `telegram_negative` |  | number |  |  |
| `telegram_positive` |  | number |  |  |
| `time` |  | time | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `time_business_day` |  | number |  |  |
| `total_addresses_with_balance` |  | number |  |  |
| `total_debt_to_ebitda_fq` |  | number |  |  |
| `total_debt_to_ebitda_fy` |  | number |  |  |
| `total_supply` |  | number |  |  |
| `total_to_max_supply_ratio` |  | percent |  |  |
| `tvl` |  | fundamental_price |  |  |
| `tweets` |  | number |  |  |
| `twitter_negative` |  | number |  |  |
| `twitter_positive` |  | number |  |  |
| `txs_count` |  | number |  |  |
| `txs_volume` |  | number |  |  |
| `txs_volume_usd` |  | fundamental_price |  |  |
| `typespecs` |  | set |  | 3 values: `crypto`, `cryptoasset`, `synthetic` |
| `update-time` |  | number |  |  |
| `update_mode` |  | text | 1, 5, 15, 30, 60, 120, 240, 1W, 1M | 1 values: `streaming` |
| `update_time` |  | time |  |  |
| `velocity` |  | number |  |  |
| `volume-type` |  | text |  |  |
| `volume_base\|5` |  | number |  |  |
| `volume_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `volume_change_abs` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `volume_quote\|5` |  | number |  |  |
