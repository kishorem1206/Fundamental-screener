# CFD fields

Contracts for difference (market: `cfd`).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/cfd.html>

**515 fields** (3170 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 2 values: `commodity`, `index` |
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
| `exchange` | Exchange | text |  | 54 values: `ATHEX`, `BCBA`, `BCS`, `BELEX`, `BET`, `BIST`, `BLACKBULL`, `BME`, `BMFBOVESPA`, `BMV`, `BSE`, `BVB`, `BVC`, `BVL`, `CBOE`, `CRYPTOCAP`, `DFM`, `DJ`, `EASYMARKETS`, `EGX`, `EIGHTCAP`, `EURONEXT`, `FOREXCOM`, `FTSEMYX`, `FX` … |
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
| `currency` | Quote currency | text |  | 11 values: `AUD`, `CHF`, `EUR`, `GBP`, `HKD`, `JPY`, `KRW`, `NZD`, `SGD`, `USD`, `ZAR` |
| `ask` | Ask | price |  |  |
| `bid` | Bid | price |  |  |
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
| `AvgValue.Traded_10d` |  | number |  |  |
| `AvgValue.Traded_30d` |  | number |  |  |
| `AvgValue.Traded_60d` |  | number |  |  |
| `AvgValue.Traded_90d` |  | number |  |  |
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
| `Perf.1M.MarketCap` |  | number |  |  |
| `Perf.1M_abs` |  | number |  |  |
| `Perf.1W.MarketCap` |  | number |  |  |
| `Perf.1Y.MarketCap` |  | number |  |  |
| `Perf.3M.MarketCap` |  | number |  |  |
| `Perf.3M_abs` |  | number |  |  |
| `Perf.3Y` |  | number |  |  |
| `Perf.3Y_abs` |  | number |  |  |
| `Perf.5D` |  | number |  |  |
| `Perf.5D_abs` |  | number |  |  |
| `Perf.5Y.MarketCap` |  | number |  |  |
| `Perf.5Y_abs` |  | number |  |  |
| `Perf.6M.MarketCap` |  | number |  |  |
| `Perf.6M_abs` |  | number |  |  |
| `Perf.All_abs` |  | number |  |  |
| `Perf.W_abs` |  | number |  |  |
| `Perf.YTD.MarketCap` |  | number |  |  |
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
| `all_time_high` |  | price |  |  |
| `all_time_high_day` |  | time |  |  |
| `all_time_low` |  | price |  |  |
| `all_time_low_day` |  | time |  |  |
| `all_time_open` |  | price |  |  |
| `aum_perf.1M` |  | number |  |  |
| `aum_perf.1Y` |  | number |  |  |
| `aum_perf.3M` |  | number |  |  |
| `aum_perf.3Y` |  | number |  |  |
| `aum_perf.5Y` |  | number |  |  |
| `aum_perf.YTD` |  | number |  |  |
| `bars_count` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `base_currency_kind` |  | text |  |  |
| `bid_ask_spread_pct` |  | percent |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fy` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fy` |  | number |  |  |
| `circulating_to_max_supply_ratio` |  | percent |  |  |
| `country2` |  | text |  |  |
| `coupon` |  | number |  |  |
| `cryptoasset-info.description` |  | text |  | 420 values: `00 Token`, `0G`, `0x Protocol`, `1inch`, `4`, `4Stock`, `AINFT`, `AIOZ Network`, `AKEDO`, `ANDY (ETH)`, `ANyONe Protocol`, `API3`, `ARC`, `ARPA`, `AVA (Travala)`, `Aave`, `Aerodrome Finance`, `Akash Network`, `Alchemist AI`, `Aleo`, `Algorand`, `Allora`, `Alon`, `AltLayer`, `Amp` … |
| `cryptoasset-info.id` |  | text |  | 420 values: `XTVC00`, `XTVC0G`, `XTVC1INCH`, `XTVC2Z`, `XTVC4`, `XTVC4STOCK`, `XTVCAAVE`, `XTVCACEF`, `XTVCADA`, `XTVCAEROD`, `XTVCAGI`, `XTVCAIARTIFI`, `XTVCAIO`, `XTVCAIOZ`, `XTVCAIXBT`, `XTVCAKE`, `XTVCAKT`, `XTVCALCH`, `XTVCALEO`, `XTVCALGO`, `XTVCALICE`, `XTVCALLO`, `XTVCALON`, `XTVCALTL`, `XTVCAMP2` … |
| `currency_id` |  | text |  | 12 values: ``, `AUD`, `CHF`, `EUR`, `GBP`, `HKD`, `JPY`, `KRW`, `NZD`, `SGD`, `USD`, `ZAR` |
| `currency_kind` |  | text |  | 1 values: `fiat` |
| `current_session` |  | text |  | 3 values: `market`, `out_of_session`, `pre_market` |
| `current_yield` |  | percent |  |  |
| `days_to_maturity` |  | number |  |  |
| `description` |  | text |  |  |
| `earnings_yield` |  | percent |  |  |
| `enterprise_value_ebit_fwd` |  | number |  |  |
| `enterprise_value_ebitda_fwd` |  | number |  |  |
| `enterprise_value_sales_fwd` |  | number |  |  |
| `eps_surprise_percent_fq` |  | percent |  |  |
| `expiration` |  | time |  |  |
| `first_bar_time` |  | time |  |  |
| `float_shares_percent_current` |  | percent |  |  |
| `forex_exotic_priority` |  | number |  |  |
| `forex_minor_priority` |  | number |  |  |
| `forex_priority` |  | number |  |  |
| `fractional` |  | text |  | 1 values: `false` |
| `fully_diluted_value` |  | price |  |  |
| `fund_flows.1M` |  | fundamental_price |  |  |
| `fund_flows.1Y` |  | fundamental_price |  |  |
| `fund_flows.3M` |  | fundamental_price |  |  |
| `fund_flows.3Y` |  | fundamental_price |  |  |
| `fund_flows.5Y` |  | fundamental_price |  |  |
| `fund_flows.YTD` |  | fundamental_price |  |  |
| `gap_down` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_down_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_up` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_up_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `indexes` |  | interface |  |  |
| `indicators_bars_count` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `is_blacklisted` |  | bool |  |  |
| `is_shariah_compliant` |  | bool |  |  |
| `is_symbol_primary_listing` |  | bool |  |  |
| `kind` |  | text |  | 3 values: `delay`, `eod`, `rt` |
| `kind-delay` |  | number |  |  |
| `last-price-update-time` |  | time |  |  |
| `last-price-update-time-intraday` |  | time |  |  |
| `last_bar_update_time` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `logoid` |  | text |  |  |
| `low_after_high_all_change` |  | percent |  |  |
| `low_after_high_all_change_abs` |  | price |  |  |
| `market` |  | text |  | 1 values: `cfd` |
| `market_cap_to_tvl` |  | number |  |  |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `minmov` |  | number |  |  |
| `minmove2` |  | number |  |  |
| `name` |  | text |  |  |
| `nav_discount_premium` |  | number |  |  |
| `nav_perf.1M` |  | number |  |  |
| `nav_perf.1Y` |  | number |  |  |
| `nav_perf.3M` |  | number |  |  |
| `nav_perf.3Y` |  | number |  |  |
| `nav_perf.5Y` |  | number |  |  |
| `nav_perf.YTD` |  | number |  |  |
| `nav_total_return.1M` |  | number |  |  |
| `nav_total_return.1Y` |  | number |  |  |
| `nav_total_return.3M` |  | number |  |  |
| `nav_total_return.3Y` |  | number |  |  |
| `nav_total_return.5Y` |  | number |  |  |
| `nav_total_return.6M` |  | number |  |  |
| `nav_total_return.YTD` |  | number |  |  |
| `non_gaap_price_to_earnings_per_share_forecast_next_fy` |  | number |  |  |
| `nvt` |  | number |  |  |
| `open_interest_to_volume_24h` |  | number |  |  |
| `popularity_rank` |  | number |  |  |
| `post_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
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
| `provider-id` |  | text |  | 13 values: `blackbullmarkets`, `easymarkets`, `eightcap`, `fxcm`, `gain`, `ice`, `oanda`, `pepperstone`, `phillipnova`, `saxobank`, `skilling`, `stonextrading`, `tvc` |
| `rates_cf` |  | map |  |  |
| `rates_current` |  | map |  |  |
| `rates_dividend_recent` |  | map |  |  |
| `rates_dividend_upcoming` |  | map |  |  |
| `rates_earnings_fq` |  | map |  |  |
| `rates_earnings_next_fq` |  | map |  |  |
| `rates_fh` |  | map |  |  |
| `rates_fq` |  | map |  |  |
| `rates_fy` |  | map |  |  |
| `rates_mc` |  | map |  |  |
| `rates_pt` |  | map |  |  |
| `rates_time_series` |  | map |  |  |
| `rates_ttm` |  | map |  |  |
| `relative_volume` |  | number |  |  |
| `relative_volume_intraday\|5` |  | number |  |  |
| `revenue_surprise_percent_fq` |  | percent |  |  |
| `rtc` |  | price |  |  |
| `shrhldrs_equity_to_total_assets_fq` |  | number |  |  |
| `shrhldrs_equity_to_total_assets_fy` |  | number |  |  |
| `source-logoid` |  | text |  | 54 values: `provider/ice`, `provider/tvc`, `source/ATHEX`, `source/BCBA`, `source/BCS`, `source/BELEX`, `source/BET`, `source/BIST`, `source/BLACKBULL`, `source/BME`, `source/BMFBOVESPA`, `source/BMV`, `source/BSE`, `source/BVB`, `source/BVC`, `source/BVL`, `source/CBOE`, `source/CRYPTOCAP`, `source/DFM`, `source/DJ`, `source/EASYMARKETS`, `source/EGX`, `source/EIGHTCAP`, `source/EURONEXT`, `source/FOREXCOM` … |
| `subsessions` |  | interface |  |  |
| `subtype` |  | text |  | 5 values: `cfd`, `crypto`, `index_other`, `main`, `synthetic` |
| `time` |  | time | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `time_business_day` |  | number |  |  |
| `total_debt_to_ebitda_fq` |  | number |  |  |
| `total_debt_to_ebitda_fy` |  | number |  |  |
| `total_to_max_supply_ratio` |  | percent |  |  |
| `typespecs` |  | set |  | 6 values: ``, `cfd`, `crypto`, `defi`, `main`, `synthetic` |
| `update-time` |  | number |  |  |
| `update_mode` |  | text | 1, 5, 15, 30, 60, 120, 240, 1W, 1M | 3 values: `delayed_streaming_900`, `endofday`, `streaming` |
| `update_time` |  | time |  |  |
| `velocity` |  | number |  |  |
| `volume_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `volume_change_abs` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
