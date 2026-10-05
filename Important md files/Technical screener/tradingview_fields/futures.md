# Futures fields

Futures contracts (market: `futures`).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/futures.html>

**472 fields** (472 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 1 values: `futures` |
| `is_primary` | Primary Listing | bool |  |  |
| `active_symbol` | Current trading day | bool |  |  |
| `change` | Change % | percent |  |  |
| `change_abs` | Change | price |  |  |
| `close` | Price | price |  |  |
| `price_earnings_ttm` | Price to Earnings Ratio (TTM) | number |  |  |
| `sector` | Group | text |  | 6 values: `Agricultural`, `Currencies`, `Energy`, `Financials`, `Indexes`, `Metals` |
| `Recommend.All` | Technical Rating | number |  |  |
| `volume` | Volume | number |  |  |
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
| `Aroon.Down` | Aroon Down (14) | number |  |  |
| `Aroon.Up` | Aroon Up (14) | number |  |  |
| `ADR` | Average Day Range (14) | number |  |  |
| `ADX` | Average Directional Index (14) | number |  |  |
| `ATR` | Average True Range (14) | number |  |  |
| `average_volume_10d_calc` | Average Volume (10 day) | number |  |  |
| `average_volume_30d_calc` | Average Volume (30 day) | number |  |  |
| `average_volume_60d_calc` | Average Volume (60 day) | number |  |  |
| `average_volume_90d_calc` | Average Volume (90 day) | number |  |  |
| `AO` | Awesome Oscillator | number |  |  |
| `BB.lower` | Bollinger Lower Band (20) | number |  |  |
| `BB.upper` | Bollinger Upper Band (20) | number |  |  |
| `BBPower` | Bull Bear Power | number |  |  |
| `ChaikinMoneyFlow` | Chaikin Money Flow (20) | number |  |  |
| `change_from_open` | Change from Open % | percent |  |  |
| `change_from_open_abs` | Change from Open | price |  |  |
| `CCI20` | Commodity Channel Index (20) | number |  |  |
| `DonchCh20.Lower` | Donchian Channels Lower Band (20) | number |  |  |
| `DonchCh20.Upper` | Donchian Channels Upper Band (20) | number |  |  |
| `exchange` | Exchange | text |  | 52 values: `ABAXX`, `ADX`, `ASX24`, `BET`, `BIST`, `BMFBOVESPA`, `BSE`, `CBOE`, `CBOT`, `CBOT_MINI`, `CFFEX`, `CME`, `CME_MINI`, `COMEX`, `COMEX_MINI`, `DFM`, `EEX`, `EUREX`, `EURONEXT`, `GPW`, `HKEX`, `HNX`, `ICEAD`, `ICEENDEX`, `ICEEUR` … |
| `EMA5` | Exponential Moving Average (5) | number |  |  |
| `EMA10` | Exponential Moving Average (10) | number |  |  |
| `EMA20` | Exponential Moving Average (20) | number |  |  |
| `EMA30` | Exponential Moving Average (30) | number |  |  |
| `EMA50` | Exponential Moving Average (50) | number |  |  |
| `EMA100` | Exponential Moving Average (100) | number |  |  |
| `EMA200` | Exponential Moving Average (200) | number |  |  |
| `free_cash_flow_margin_fy` | Free Cash Flow Margin (FY) | percent |  |  |
| `free_cash_flow_margin_ttm` | Free Cash Flow Margin (TTM) | percent |  |  |
| `gap` | Gap % | percent |  |  |
| `gross_profit_margin_fy` | Gross Margin (FY) | percent |  |  |
| `high` | High | price |  |  |
| `HullMA9` | Hull Moving Average (9) | number |  |  |
| `Ichimoku.BLine` | Ichimoku Base Line (9, 26, 52, 26) | number |  |  |
| `Ichimoku.CLine` | Ichimoku Conversion Line (9, 26, 52, 26) | number |  |  |
| `Ichimoku.Lead1` | Ichimoku Leading Span A (9, 26, 52, 26) | number |  |  |
| `Ichimoku.Lead2` | Ichimoku Leading Span B (9, 26, 52, 26) | number |  |  |
| `KltChnl.lower` | Keltner Channels Lower Band (20) | number |  |  |
| `KltChnl.upper` | Keltner Channels Upper Band (20) | number |  |  |
| `low` | Low | price |  |  |
| `MACD.macd` | MACD Level (12, 26) | number |  |  |
| `MACD.signal` | MACD Signal (12, 26) | number |  |  |
| `Mom` | Momentum (10) | number |  |  |
| `MoneyFlow` | Money Flow (14) | number |  |  |
| `Perf.1M` | Monthly Performance | number |  |  |
| `Recommend.MA` | Moving Averages Rating | number |  |  |
| `ADX-DI` | Negative Directional Indicator (14) | number |  |  |
| `net_income_bef_disc_oper_margin_fy` | Net Margin (FY) | percent |  |  |
| `open` | Open | price |  |  |
| `oper_income_margin_fy` | Operating Margin (FY) | percent |  |  |
| `Recommend.Other` | Oscillators Rating | number |  |  |
| `P.SAR` | Parabolic SAR | number |  |  |
| `Pivot.M.Camarilla.Middle` | Pivot Camarilla P | number |  |  |
| `Pivot.M.Camarilla.R1` | Pivot Camarilla R1 | number |  |  |
| `Pivot.M.Camarilla.R2` | Pivot Camarilla R2 | number |  |  |
| `Pivot.M.Camarilla.R3` | Pivot Camarilla R3 | number |  |  |
| `Pivot.M.Camarilla.S1` | Pivot Camarilla S1 | number |  |  |
| `Pivot.M.Camarilla.S2` | Pivot Camarilla S2 | number |  |  |
| `Pivot.M.Camarilla.S3` | Pivot Camarilla S3 | number |  |  |
| `Pivot.M.Classic.Middle` | Pivot Classic P | number |  |  |
| `Pivot.M.Classic.R1` | Pivot Classic R1 | number |  |  |
| `Pivot.M.Classic.R2` | Pivot Classic R2 | number |  |  |
| `Pivot.M.Classic.R3` | Pivot Classic R3 | number |  |  |
| `Pivot.M.Classic.S1` | Pivot Classic S1 | number |  |  |
| `Pivot.M.Classic.S2` | Pivot Classic S2 | number |  |  |
| `Pivot.M.Classic.S3` | Pivot Classic S3 | number |  |  |
| `Pivot.M.Demark.Middle` | Pivot DM P | number |  |  |
| `Pivot.M.Demark.R1` | Pivot DM R1 | number |  |  |
| `Pivot.M.Demark.S1` | Pivot DM S1 | number |  |  |
| `Pivot.M.Fibonacci.Middle` | Pivot Fibonacci P | number |  |  |
| `Pivot.M.Fibonacci.R1` | Pivot Fibonacci R1 | number |  |  |
| `Pivot.M.Fibonacci.R2` | Pivot Fibonacci R2 | number |  |  |
| `Pivot.M.Fibonacci.R3` | Pivot Fibonacci R3 | number |  |  |
| `Pivot.M.Fibonacci.S1` | Pivot Fibonacci S1 | number |  |  |
| `Pivot.M.Fibonacci.S2` | Pivot Fibonacci S2 | number |  |  |
| `Pivot.M.Fibonacci.S3` | Pivot Fibonacci S3 | number |  |  |
| `Pivot.M.Woodie.Middle` | Pivot Woodie P | number |  |  |
| `Pivot.M.Woodie.R1` | Pivot Woodie R1 | number |  |  |
| `Pivot.M.Woodie.R2` | Pivot Woodie R2 | number |  |  |
| `Pivot.M.Woodie.R3` | Pivot Woodie R3 | number |  |  |
| `Pivot.M.Woodie.S1` | Pivot Woodie S1 | number |  |  |
| `Pivot.M.Woodie.S2` | Pivot Woodie S2 | number |  |  |
| `Pivot.M.Woodie.S3` | Pivot Woodie S3 | number |  |  |
| `ADX+DI` | Positive Directional Indicator (14) | number |  |  |
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
| `ROC` | Rate Of Change (9) | number |  |  |
| `RSI7` | Relative Strength Index (7) | number |  |  |
| `RSI` | Relative Strength Index (14) | number |  |  |
| `relative_volume_10d_calc` | Relative Volume | number |  |  |
| `research_and_dev_ratio_fy` | Research & development Ratio (FY) | percent |  |  |
| `research_and_dev_ratio_ttm` | Research & development Ratio (TTM) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_fy` | Selling General & Admin expenses Ratio (FY) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_ttm` | Selling General & Admin expenses Ratio (TTM) | percent |  |  |
| `SMA5` | Simple Moving Average (5) | number |  |  |
| `SMA10` | Simple Moving Average (10) | number |  |  |
| `SMA20` | Simple Moving Average (20) | number |  |  |
| `SMA30` | Simple Moving Average (30) | number |  |  |
| `SMA50` | Simple Moving Average (50) | number |  |  |
| `SMA100` | Simple Moving Average (100) | number |  |  |
| `SMA200` | Simple Moving Average (200) | number |  |  |
| `Stoch.D` | Stochastic %D (14, 3, 3) | number |  |  |
| `Stoch.K` | Stochastic %K (14, 3, 3) | number |  |  |
| `Stoch.RSI.K` | Stochastic RSI Fast (3, 3, 14, 14) | number |  |  |
| `Stoch.RSI.D` | Stochastic RSI Slow (3, 3, 14, 14) | number |  |  |
| `submarket` | Submarket | text |  | 1 values: `` |
| `UO` | Ultimate Oscillator (7, 14, 28) | number |  |  |
| `Volatility.D` | Volatility | number |  |  |
| `Volatility.M` | Volatility Month | number |  |  |
| `Volatility.W` | Volatility Week | number |  |  |
| `VWAP` | Volume Weighted Average Price | number |  |  |
| `VWMA` | Volume Weighted Moving Average (20) | number |  |  |
| `Perf.W` | Weekly Performance | number |  |  |
| `W.R` | Williams Percent Range (14) | number |  |  |
| `Perf.Y` | Yearly Performance | number |  |  |
| `Perf.YTD` | YTD Performance | number |  |  |
| `currency` | Quote currency | text |  | 37 values: `AED`, `ARS`, `AUD`, `BRL`, `CAD`, `CHF`, `CLP`, `CNH`, `CNY`, `CZK`, `DKK`, `EUR`, `GBP`, `GBX`, `HKD`, `HUF`, `INR`, `JPY`, `KRW`, `MXN`, `MYR`, `NOK`, `NZD`, `PLN`, `RON` … |
| `24h_vol_to_market_cap` |  | number |  |  |
| `ADRP` |  | number |  |  |
| `ADX+DI[1]` |  | number |  |  |
| `ADX+DI_9` |  | number |  |  |
| `ADX+DI_20` |  | number |  |  |
| `ADX+DI_100[1]` |  | number |  |  |
| `ADX+DI_50` |  | number |  |  |
| `ADX+DI_20[1]` |  | number |  |  |
| `ADX+DI_50[1]` |  | number |  |  |
| `ADX+DI_9[1]` |  | number |  |  |
| `ADX+DI_100` |  | number |  |  |
| `ADX-DI[1]` |  | number |  |  |
| `ADX-DI_9` |  | number |  |  |
| `ADX-DI_20` |  | number |  |  |
| `ADX-DI_100[1]` |  | number |  |  |
| `ADX-DI_50` |  | number |  |  |
| `ADX-DI_20[1]` |  | number |  |  |
| `ADX-DI_50[1]` |  | number |  |  |
| `ADX-DI_9[1]` |  | number |  |  |
| `ADX-DI_100` |  | number |  |  |
| `ADX_9` |  | number |  |  |
| `ADX_20` |  | number |  |  |
| `ADX_50` |  | number |  |  |
| `ADX_100` |  | number |  |  |
| `AO[1]` |  | number |  |  |
| `AO[2]` |  | number |  |  |
| `ATRP` |  | number |  |  |
| `BB.basis` |  | number |  |  |
| `BB.basis_50` |  | number |  |  |
| `BB.lower_50` |  | number |  |  |
| `BB.upper_50` |  | number |  |  |
| `CCI20[1]` |  | number |  |  |
| `Candle.3BlackCrows` |  | number |  |  |
| `Candle.3WhiteSoldiers` |  | number |  |  |
| `Candle.AbandonedBaby.Bearish` |  | number |  |  |
| `Candle.AbandonedBaby.Bullish` |  | number |  |  |
| `Candle.DarkCloudCover.Bearish` |  | number |  |  |
| `Candle.Doji` |  | number |  |  |
| `Candle.Doji.Dragonfly` |  | number |  |  |
| `Candle.Doji.Gravestone` |  | number |  |  |
| `Candle.DojiStar.Bearish` |  | number |  |  |
| `Candle.DojiStar.Bullish` |  | number |  |  |
| `Candle.DownsideTasukiGap.Bearish` |  | number |  |  |
| `Candle.Engulfing.Bearish` |  | number |  |  |
| `Candle.Engulfing.Bullish` |  | number |  |  |
| `Candle.EveningDojiStar.Bearish` |  | number |  |  |
| `Candle.EveningStar` |  | number |  |  |
| `Candle.FallingThreeMethods.Bearish` |  | number |  |  |
| `Candle.FallingWindow.Bearish` |  | number |  |  |
| `Candle.Hammer` |  | number |  |  |
| `Candle.HangingMan` |  | number |  |  |
| `Candle.Harami.Bearish` |  | number |  |  |
| `Candle.Harami.Bullish` |  | number |  |  |
| `Candle.HaramiCross.Bearish` |  | number |  |  |
| `Candle.HaramiCross.Bullish` |  | number |  |  |
| `Candle.InvertedHammer` |  | number |  |  |
| `Candle.Kicking.Bearish` |  | number |  |  |
| `Candle.Kicking.Bullish` |  | number |  |  |
| `Candle.LongShadow.Lower` |  | number |  |  |
| `Candle.LongShadow.Upper` |  | number |  |  |
| `Candle.Marubozu.Black` |  | number |  |  |
| `Candle.Marubozu.White` |  | number |  |  |
| `Candle.MorningDojiStar.Bullish` |  | number |  |  |
| `Candle.MorningStar` |  | number |  |  |
| `Candle.OnNeck.Bearish` |  | number |  |  |
| `Candle.Piercing.Bullish` |  | number |  |  |
| `Candle.RisingThreeMethods.Bullish` |  | number |  |  |
| `Candle.RisingWindow.Bullish` |  | number |  |  |
| `Candle.ShootingStar` |  | number |  |  |
| `Candle.SpinningTop.Black` |  | number |  |  |
| `Candle.SpinningTop.White` |  | number |  |  |
| `Candle.TriStar.Bearish` |  | number |  |  |
| `Candle.TriStar.Bullish` |  | number |  |  |
| `Candle.TweezerBottom.Bullish` |  | number |  |  |
| `Candle.TweezerTop.Bearish` |  | number |  |  |
| `Candle.UpsideTasukiGap.Bullish` |  | number |  |  |
| `DonchCh20.Middle` |  | number |  |  |
| `EMA2` |  | number |  |  |
| `EMA3` |  | number |  |  |
| `EMA6` |  | number |  |  |
| `EMA7` |  | number |  |  |
| `EMA8` |  | number |  |  |
| `EMA9` |  | number |  |  |
| `EMA12` |  | number |  |  |
| `EMA13` |  | number |  |  |
| `EMA14` |  | number |  |  |
| `EMA15` |  | number |  |  |
| `EMA21` |  | number |  |  |
| `EMA25` |  | number |  |  |
| `EMA26` |  | number |  |  |
| `EMA34` |  | number |  |  |
| `EMA40` |  | number |  |  |
| `EMA55` |  | number |  |  |
| `EMA60` |  | number |  |  |
| `EMA75` |  | number |  |  |
| `EMA89` |  | number |  |  |
| `EMA120` |  | number |  |  |
| `EMA144` |  | number |  |  |
| `EMA150` |  | number |  |  |
| `EMA250` |  | number |  |  |
| `EMA300` |  | number |  |  |
| `High.1M.Date` |  | time |  |  |
| `High.3M.Date` |  | time |  |  |
| `High.5D` |  | number |  |  |
| `High.6M.Date` |  | time |  |  |
| `High.All.Calc` |  | number |  |  |
| `High.All.Calc.Date` |  | time |  |  |
| `High.All.Date` |  | time |  |  |
| `HullMA20` |  | number |  |  |
| `HullMA200` |  | number |  |  |
| `Ichimoku.BLine_20_60_120_30` |  | number |  |  |
| `Ichimoku.CLine_20_60_120_30` |  | number |  |  |
| `Ichimoku.Lead1_20_60_120_30` |  | number |  |  |
| `Ichimoku.Lead2_20_60_120_30` |  | number |  |  |
| `KltChnl.basis` |  | number |  |  |
| `Low.1M.Date` |  | time |  |  |
| `Low.3M.Date` |  | time |  |  |
| `Low.5D` |  | number |  |  |
| `Low.6M.Date` |  | time |  |  |
| `Low.After.High.All` |  | price |  |  |
| `Low.All.Calc` |  | number |  |  |
| `Low.All.Calc.Date` |  | time |  |  |
| `Low.All.Date` |  | time |  |  |
| `MACD.hist` |  | number |  |  |
| `Mom[1]` |  | number |  |  |
| `Mom_14` |  | number |  |  |
| `Mom_14[1]` |  | number |  |  |
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
| `RSI2` |  | number |  |  |
| `RSI3` |  | number |  |  |
| `RSI4` |  | number |  |  |
| `RSI5` |  | number |  |  |
| `RSI9` |  | number |  |  |
| `RSI10` |  | number |  |  |
| `RSI20` |  | number |  |  |
| `RSI21` |  | number |  |  |
| `RSI30` |  | number |  |  |
| `RSI10[1]` |  | number |  |  |
| `RSI20[1]` |  | number |  |  |
| `RSI21[1]` |  | number |  |  |
| `RSI2[1]` |  | number |  |  |
| `RSI30[1]` |  | number |  |  |
| `RSI3[1]` |  | number |  |  |
| `RSI4[1]` |  | number |  |  |
| `RSI5[1]` |  | number |  |  |
| `RSI7[1]` |  | number |  |  |
| `RSI9[1]` |  | number |  |  |
| `RSI[1]` |  | number |  |  |
| `Rec.BBPower` |  | number |  |  |
| `Rec.HullMA9` |  | number |  |  |
| `Rec.Ichimoku` |  | number |  |  |
| `Rec.Stoch.RSI` |  | number |  |  |
| `Rec.UO` |  | number |  |  |
| `Rec.VWMA` |  | number |  |  |
| `Rec.WR` |  | number |  |  |
| `SMA2` |  | number |  |  |
| `SMA3` |  | number |  |  |
| `SMA6` |  | number |  |  |
| `SMA7` |  | number |  |  |
| `SMA8` |  | number |  |  |
| `SMA9` |  | number |  |  |
| `SMA12` |  | number |  |  |
| `SMA13` |  | number |  |  |
| `SMA14` |  | number |  |  |
| `SMA15` |  | number |  |  |
| `SMA21` |  | number |  |  |
| `SMA25` |  | number |  |  |
| `SMA26` |  | number |  |  |
| `SMA34` |  | number |  |  |
| `SMA40` |  | number |  |  |
| `SMA55` |  | number |  |  |
| `SMA60` |  | number |  |  |
| `SMA75` |  | number |  |  |
| `SMA89` |  | number |  |  |
| `SMA120` |  | number |  |  |
| `SMA144` |  | number |  |  |
| `SMA150` |  | number |  |  |
| `SMA250` |  | number |  |  |
| `SMA300` |  | number |  |  |
| `Stoch.D[1]` |  | number |  |  |
| `Stoch.D_14_1_3` |  | number |  |  |
| `Stoch.D_14_1_3[1]` |  | number |  |  |
| `Stoch.D_5_3_3` |  | number |  |  |
| `Stoch.D_5_3_3[1]` |  | number |  |  |
| `Stoch.D_6_3_3` |  | number |  |  |
| `Stoch.D_6_3_3[1]` |  | number |  |  |
| `Stoch.D_8_3_3` |  | number |  |  |
| `Stoch.D_8_3_3[1]` |  | number |  |  |
| `Stoch.K[1]` |  | number |  |  |
| `Stoch.K_14_1_3` |  | number |  |  |
| `Stoch.K_14_1_3[1]` |  | number |  |  |
| `Stoch.K_5_3_3` |  | number |  |  |
| `Stoch.K_5_3_3[1]` |  | number |  |  |
| `Stoch.K_6_3_3` |  | number |  |  |
| `Stoch.K_6_3_3[1]` |  | number |  |  |
| `Stoch.K_8_3_3` |  | number |  |  |
| `Stoch.K_8_3_3[1]` |  | number |  |  |
| `all_time_high` |  | price |  |  |
| `all_time_high_day` |  | time |  |  |
| `all_time_low` |  | price |  |  |
| `all_time_low_day` |  | time |  |  |
| `all_time_open` |  | price |  |  |
| `bars_count` |  | number |  |  |
| `base_currency_kind` |  | text |  | 2 values: `crypto`, `fiat` |
| `cash_n_short_term_invest_to_total_current_liabilities_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fy` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fy` |  | number |  |  |
| `circulating_to_max_supply_ratio` |  | percent |  |  |
| `country_code` |  | text |  | 33 values: `AE`, `AR`, `AU`, `BE`, `BR`, `CA`, `CN`, `DE`, `DK`, `EU`, `FI`, `FR`, `GB`, `HK`, `HU`, `IN`, `IT`, `JP`, `KR`, `MY`, `NL`, `NO`, `NZ`, `PL`, `PT` … |
| `coupon` |  | number |  |  |
| `cryptoasset-info.description` |  | text |  |  |
| `cryptoasset-info.id` |  | text |  |  |
| `currency_id` |  | text |  | 37 values: `AED`, `ARS`, `AUD`, `BRL`, `CAD`, `CHF`, `CLP`, `CNY`, `CZK`, `DKK`, `EUR`, `GBP`, `HKD`, `HUF`, `INR`, `JPY`, `KRW`, `MXN`, `MYR`, `NOK`, `NZD`, `PLN`, `RON`, `RSD`, `RUB` … |
| `currency_kind` |  | text |  | 1 values: `fiat` |
| `current_session` |  | text |  | 3 values: `holiday`, `market`, `out_of_session` |
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
| `fractional` |  | text |  | 2 values: `false`, `true` |
| `fully_diluted_value` |  | price |  |  |
| `fundamental_currency_code` |  | text |  |  |
| `gap_down` |  | percent |  |  |
| `gap_down_abs` |  | price |  |  |
| `gap_up` |  | percent |  |  |
| `gap_up_abs` |  | price |  |  |
| `indexes` |  | interface |  |  |
| `indicators_bars_count` |  | number |  |  |
| `is_blacklisted` |  | bool |  |  |
| `is_shariah_compliant` |  | bool |  |  |
| `is_symbol_primary_listing` |  | bool |  |  |
| `kind` |  | text |  | 1 values: `rt` |
| `kind-delay` |  | number |  |  |
| `last-price-update-time` |  | time |  |  |
| `last-price-update-time-intraday` |  | time |  |  |
| `last_bar_update_time` |  | number |  |  |
| `logoid` |  | text |  |  |
| `low_after_high_all_change` |  | percent |  |  |
| `low_after_high_all_change_abs` |  | price |  |  |
| `market` |  | text |  | 1 values: `futures` |
| `market_cap_to_tvl` |  | number |  |  |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `minmov` |  | number |  |  |
| `minmove2` |  | number |  |  |
| `name` |  | text |  |  |
| `non_gaap_price_to_earnings_per_share_forecast_next_fy` |  | number |  |  |
| `nvt` |  | number |  |  |
| `open_interest` |  | number |  |  |
| `open_interest_to_volume_24h` |  | number |  |  |
| `popularity_rank` |  | number |  |  |
| `post_change` |  | percent |  |  |
| `pre_change` |  | percent |  |  |
| `pre_change_abs` |  | price |  |  |
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
| `product` |  | text |  | 99 values: `Commodity/Agriculture`, `Commodity/Agriculture/Dairy`, `Commodity/Agriculture/Fertilizer`, `Commodity/Agriculture/Fish`, `Commodity/Agriculture/GrainAndSeed`, `Commodity/Agriculture/GrainAndSeed/AdzukiBean`, `Commodity/Agriculture/GrainAndSeed/Barley`, `Commodity/Agriculture/GrainAndSeed/Corn`, `Commodity/Agriculture/GrainAndSeed/Millet`, `Commodity/Agriculture/GrainAndSeed/Oats`, `Commodity/Agriculture/GrainAndSeed/PalmOil`, `Commodity/Agriculture/GrainAndSeed/Rapeseed`, `Commodity/Agriculture/GrainAndSeed/Rapeseed/Meal`, `Commodity/Agriculture/GrainAndSeed/Rapeseed/Oil`, `Commodity/Agriculture/GrainAndSeed/Rice/Rough`, `Commodity/Agriculture/GrainAndSeed/Soybean`, `Commodity/Agriculture/GrainAndSeed/Soybean/Meal`, `Commodity/Agriculture/GrainAndSeed/Soybean/Oil`, `Commodity/Agriculture/GrainAndSeed/Sunflower`, `Commodity/Agriculture/GrainAndSeed/Wheat`, `Commodity/Agriculture/GrainAndSeed/Wheat/HRS`, `Commodity/Agriculture/GrainAndSeed/Wheat/HRW`, `Commodity/Agriculture/GrainAndSeed/Wheat/SRW`, `Commodity/Agriculture/Livestock`, `Commodity/Agriculture/Livestock/Cattle/Feeder` … |
| `provider-id` |  | text |  | 3 values: `abaxx`, `alor`, `ice` |
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
| `revenue_surprise_percent_fq` |  | percent |  |  |
| `shrhldrs_equity_to_total_assets_fq` |  | number |  |  |
| `shrhldrs_equity_to_total_assets_fy` |  | number |  |  |
| `source-logoid` |  | text |  | 52 values: `source/ABAXX`, `source/ADX`, `source/ASX24`, `source/BET`, `source/BIST`, `source/BMFBOVESPA`, `source/BSE`, `source/CBOE`, `source/CBOT`, `source/CBOT_MINI`, `source/CFFEX`, `source/CME`, `source/CME_MINI`, `source/COMEX`, `source/COMEX_MINI`, `source/DFM`, `source/EEX`, `source/EUREX`, `source/EURONEXT`, `source/GPW`, `source/HKEX`, `source/HNX`, `source/ICEAD`, `source/ICEENDEX`, `source/ICEEUR` … |
| `subsessions` |  | interface |  |  |
| `subtype` |  | text |  | 4 values: ``, `continuous`, `micro`, `mini` |
| `time` |  | time |  |  |
| `time_business_day` |  | number |  |  |
| `total_debt_to_ebitda_fq` |  | number |  |  |
| `total_debt_to_ebitda_fy` |  | number |  |  |
| `total_to_max_supply_ratio` |  | percent |  |  |
| `typespecs` |  | set |  | 6 values: ``, `continuous`, `expired`, `micro`, `mini`, `synthetic` |
| `update-time` |  | number |  |  |
| `update_mode` |  | text |  | 1 values: `streaming` |
| `update_time` |  | time |  |  |
| `velocity` |  | number |  |  |
| `volume_change` |  | percent |  |  |
| `volume_change_abs` |  | number |  |  |
