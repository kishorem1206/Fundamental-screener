# Stocks fields

Equities, funds/ETFs and DRs (markets: `america`, `india`, `uk`, ... any country).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/stocks.html>

**1135 fields** (3799 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 4 values: `dr`, `fund`, `stock`, `structured` |
| `is_primary` | Primary Listing | bool |  |  |
| `active_symbol` | Current trading day | bool |  |  |
| `index` | Index | text |  | 784 values: `ADX:FADGI FTSE ADX General`, `ADX:FADGMI FTSE ADX Growth Market`, `ADX:FADSI FTSE ADX Dividend Stars`, `ADX:FADX15 FTSE ADX 15`, `ADX:FADXI15 FTSE ADX 15 Islamic`, `ADX:FADXSI FTSE ADX ESG Screened`, `ASX:XAO All Ordinaries`, `ASX:XFL S&P/ASX 50`, `ASX:XJO S&P/ASX 200`, `ASX:XKO S&P/ASX 300`, `ASX:XMJ S&P/ASX 200 Materials`, `ATHEX:FTSE FTSE/ATHEX Large Cap`, `ATHEX:FTSEA FTSE ATHEX Market Index`, `ATHEX:FTSEM FTSE/ATHEX Mid Cap`, `ATHEX:GD ATHEX Composite`, `BAHRAIN:BHBX Bahrain All Share`, `BAHRAIN:BIX Bahrain Islamic Index`, `BCBA:IMV S&P MERVAL`, `BELEX:BELEX15 BELEX15`, `BELEX:BELEXLINE BELEXline`, `BET:BUMIX BUMIX`, `BET:BUX BUX`, `BIST:X030C BIST 30 Capped 25 Return`, `BIST:X030EA BIST 30 Equal Weighted Return`, `BIST:X030S BIST 30 Capped 10` … |
| `earnings_per_share_basic_ttm` | Basic EPS (TTM) | fundamental_price |  |  |
| `change` | Change % | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `change_abs` | Change | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `market_cap_basic` | Market Capitalization | fundamental_price |  |  |
| `number_of_employees` | Number of Employees | number |  |  |
| `close` | Price | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `price_earnings_ttm` | Price to Earnings Ratio (TTM) | number |  |  |
| `sector` | Group | text |  | 21 values: `Commercial Services`, `Communications`, `Consumer Durables`, `Consumer Non-Durables`, `Consumer Services`, `Distribution Services`, `Electronic Technology`, `Energy Minerals`, `Finance`, `Government`, `Health Services`, `Health Technology`, `Industrial Services`, `Miscellaneous`, `Non-Energy Minerals`, `Process Industries`, `Producer Manufacturing`, `Retail Trade`, `Technology Services`, `Transportation`, `Utilities` |
| `Recommend.All` | Technical Rating | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `volume` | Volume | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Value.Traded` | Volume*Price | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `High.1M` | 1-Month High | number |  |  |
| `Low.1M` | 1-Month Low | number |  |  |
| `beta_1_year` | 1-Year Beta | number |  |  |
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
| `basic_eps_net_income` | Basic EPS (FY) | fundamental_price |  |  |
| `BB.lower` | Bollinger Lower Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BB.upper` | Bollinger Upper Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `BBPower` | Bull Bear Power | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `cash_n_short_term_invest_fy` | Cash and short term investments (FY) | fundamental_price |  |  |
| `cash_n_short_term_invest_fq` | Cash and short term investments (MRQ) | fundamental_price |  |  |
| `cash_n_equivalents_fy` | Cash & Equivalents (FY) | fundamental_price |  |  |
| `cash_n_equivalents_fq` | Cash & Equivalents (MRQ) | fundamental_price |  |  |
| `ChaikinMoneyFlow` | Chaikin Money Flow (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `change_from_open` | Change from Open % | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `change_from_open_abs` | Change from Open | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `CCI20` | Commodity Channel Index (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `country` | Region | text |  | 114 values: `Aland Islands`, `Argentina`, `Australia`, `Austria`, `Azerbaijan`, `Bahamas`, `Bahrain`, `Bangladesh`, `Barbados`, `Belgium`, `Bermuda`, `Botswana`, `Brazil`, `British Virgin Islands`, `Bulgaria`, `Cambodia`, `Canada`, `Cayman Islands`, `Chile`, `China`, `Colombia`, `Costa Rica`, `Croatia`, `Cyprus`, `Czech Republic` … |
| `current_ratio` | Current Ratio (MRQ) | number |  |  |
| `debt_to_equity` | Debt to Equity Ratio (MRQ) | number |  |  |
| `dividends_paid` | Dividends Paid (FY) | fundamental_price |  |  |
| `dps_common_stock_prim_issue_yoy_growth_fy` | Dividends per share (Annual YoY Growth) | percent |  |  |
| `dps_common_stock_prim_issue_fy` | Dividends per Share (FY) | fundamental_price |  |  |
| `dividends_per_share_fq` | Dividends per Share (MRQ) | fundamental_price |  |  |
| `dividend_yield_recent` | Dividend Yield Forward | number |  |  |
| `DonchCh20.Lower` | Donchian Channels Lower Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `DonchCh20.Upper` | Donchian Channels Upper Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ebitda_yoy_growth_fy` | EBITDA (Annual YoY Growth) | percent |  |  |
| `ebitda_qoq_growth_fq` | EBITDA (Quarterly QoQ Growth) | percent |  |  |
| `ebitda_yoy_growth_fq` | EBITDA (Quarterly YoY Growth) | percent |  |  |
| `ebitda` | EBITDA (TTM) | fundamental_price |  |  |
| `ebitda_yoy_growth_ttm` | EBITDA (TTM YoY Growth) | percent |  |  |
| `enterprise_value_ebitda_ttm` | Enterprise Value/EBITDA (TTM) | number |  |  |
| `enterprise_value_fq` | Enterprise Value (MRQ) | fundamental_price |  |  |
| `earnings_per_share_diluted_yoy_growth_fy` | EPS Diluted (Annual YoY Growth) | percent |  |  |
| `last_annual_eps` | EPS Diluted (FY) | fundamental_price |  |  |
| `earnings_per_share_fq` | EPS Diluted (MRQ) | fundamental_price |  |  |
| `earnings_per_share_diluted_qoq_growth_fq` | EPS Diluted (Quarterly QoQ Growth) | percent |  |  |
| `earnings_per_share_diluted_yoy_growth_fq` | EPS Diluted (Quarterly YoY Growth) | percent |  |  |
| `earnings_per_share_diluted_ttm` | EPS Diluted (TTM) | fundamental_price |  |  |
| `earnings_per_share_diluted_yoy_growth_ttm` | EPS Diluted (TTM YoY Growth) | percent |  |  |
| `earnings_per_share_forecast_next_fq` | EPS Forecast (MRQ) | fundamental_price |  |  |
| `exchange` | Exchange | text |  | 101 values: `ADX`, `AMEX`, `AQUIS`, `ASX`, `ATHEX`, `BAHRAIN`, `BCBA`, `BCS`, `BELEX`, `BET`, `BIST`, `BIVA`, `BME`, `BMFBOVESPA`, `BMV`, `BSE`, `BSESOF`, `BSSE`, `BVB`, `BVC`, `BVCV`, `BVL`, `BVMT`, `BX`, `CBOE` … |
| `EMA5` | Exponential Moving Average (5) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA10` | Exponential Moving Average (10) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA20` | Exponential Moving Average (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA30` | Exponential Moving Average (30) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA50` | Exponential Moving Average (50) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA100` | Exponential Moving Average (100) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `EMA200` | Exponential Moving Average (200) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `free_cash_flow_yoy_growth_fy` | Free Cash Flow (Annual YoY Growth) | percent |  |  |
| `free_cash_flow_margin_fy` | Free Cash Flow Margin (FY) | percent |  |  |
| `free_cash_flow_margin_ttm` | Free Cash Flow Margin (TTM) | percent |  |  |
| `free_cash_flow_qoq_growth_fq` | Free Cash Flow (Quarterly QoQ Growth) | percent |  |  |
| `free_cash_flow_yoy_growth_fq` | Free Cash Flow (Quarterly YoY Growth) | percent |  |  |
| `free_cash_flow_yoy_growth_ttm` | Free Cash Flow (TTM YoY Growth) | percent |  |  |
| `gap` | Gap % | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `goodwill` | Goodwill | fundamental_price |  |  |
| `gross_profit_margin_fy` | Gross Margin (FY) | percent |  |  |
| `gross_margin` | Gross Margin (TTM) | percent |  |  |
| `gross_profit_yoy_growth_fy` | Gross Profit (Annual YoY Growth) | percent |  |  |
| `gross_profit` | Gross Profit (FY) | fundamental_price |  |  |
| `gross_profit_fq` | Gross Profit (MRQ) | fundamental_price |  |  |
| `gross_profit_qoq_growth_fq` | Gross Profit (Quarterly QoQ Growth) | percent |  |  |
| `gross_profit_yoy_growth_fq` | Gross Profit (Quarterly YoY Growth) | percent |  |  |
| `gross_profit_yoy_growth_ttm` | Gross Profit (TTM YoY Growth) | percent |  |  |
| `high` | High | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `HullMA9` | Hull Moving Average (9) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.BLine` | Ichimoku Base Line (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.CLine` | Ichimoku Conversion Line (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.Lead1` | Ichimoku Leading Span A (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Ichimoku.Lead2` | Ichimoku Leading Span B (9, 26, 52, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `industry` | Industry | text |  | 131 values: `Advertising/Marketing Services`, `Aerospace & Defense`, `Agricultural Commodities/Milling`, `Air Freight/Couriers`, `Airlines`, `Alternative Power Generation`, `Aluminum`, `Apparel/Footwear`, `Apparel/Footwear Retail`, `Auto Parts: OEM`, `Automotive Aftermarket`, `Beverages: Alcoholic`, `Beverages: Non-Alcoholic`, `Biotechnology`, `Broadcasting`, `Building Products`, `Cable/Satellite TV`, `Casinos/Gaming`, `Catalog/Specialty Distribution`, `Chemicals: Agricultural`, `Chemicals: Major Diversified`, `Chemicals: Specialty`, `Coal`, `Commercial Printing/Forms`, `Computer Communications` … |
| `KltChnl.lower` | Keltner Channels Lower Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `KltChnl.upper` | Keltner Channels Upper Band (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `last_annual_revenue` | Last Year Revenue (FY) | fundamental_price |  |  |
| `low` | Low | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `MACD.macd` | MACD Level (12, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `MACD.signal` | MACD Signal (12, 26) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Mom` | Momentum (10) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `MoneyFlow` | Money Flow (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Perf.1M` | Monthly Performance | number |  |  |
| `Recommend.MA` | Moving Averages Rating | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `ADX-DI` | Negative Directional Indicator (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `net_debt` | Net Debt (MRQ) | fundamental_price |  |  |
| `net_income_yoy_growth_fy` | Net Income (Annual YoY Growth) | percent |  |  |
| `net_income` | Net Income (FY) | fundamental_price |  |  |
| `net_income_qoq_growth_fq` | Net Income (Quarterly QoQ Growth) | percent |  |  |
| `net_income_yoy_growth_fq` | Net Income (Quarterly YoY Growth) | percent |  |  |
| `net_income_yoy_growth_ttm` | Net Income (TTM YoY Growth) | percent |  |  |
| `net_income_bef_disc_oper_margin_fy` | Net Margin (FY) | percent |  |  |
| `after_tax_margin` | Net Margin (TTM) | percent |  |  |
| `number_of_shareholders` | Number of Shareholders | number |  |  |
| `open` | Open | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `oper_income_margin_fy` | Operating Margin (FY) | percent |  |  |
| `operating_margin` | Operating Margin (TTM) | percent |  |  |
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
| `postmarket_close` | Post-market Close | price |  |  |
| `postmarket_high` | Post-market High | price |  |  |
| `postmarket_low` | Post-market Low | price |  |  |
| `postmarket_open` | Post-market Open | price |  |  |
| `postmarket_volume` | Post-market Volume | number |  |  |
| `premarket_change` | Pre-market Change % | percent |  |  |
| `premarket_change_abs` | Pre-market Change | price |  |  |
| `premarket_change_from_open` | Pre-market Change from Open % | percent |  |  |
| `premarket_change_from_open_abs` | Pre-market Change from Open | number |  |  |
| `premarket_close` | Pre-market Close | price |  |  |
| `premarket_gap` | Pre-market Gap % | percent |  |  |
| `premarket_high` | Pre-market High | price |  |  |
| `premarket_low` | Pre-market Low | price |  |  |
| `premarket_open` | Pre-market Open | price |  |  |
| `premarket_volume` | Pre-market Volume | number |  |  |
| `pre_tax_margin` | Pretax Margin (TTM) | percent |  |  |
| `price_book_ratio` | Price to Book (FY) | number |  |  |
| `price_book_fq` | Price to Book (MRQ) | number |  |  |
| `price_free_cash_flow_ttm` | Price to Free Cash Flow (TTM) | number |  |  |
| `price_revenue_ttm` | Price to Revenue Ratio (TTM) | number |  |  |
| `price_sales_ratio` | Price to Sales (FY) | number |  |  |
| `quick_ratio` | Quick Ratio (MRQ) | number |  |  |
| `ROC` | Rate Of Change (9) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `earnings_release_date` | Recent Earnings Date | time |  |  |
| `RSI7` | Relative Strength Index (7) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `RSI` | Relative Strength Index (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `relative_volume_10d_calc` | Relative Volume | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `research_and_dev_ratio_fy` | Research & development Ratio (FY) | percent |  |  |
| `research_and_dev_ratio_ttm` | Research & development Ratio (TTM) | percent |  |  |
| `return_on_assets` | Return on Assets (TTM) | percent |  |  |
| `return_on_equity` | Return on Equity (TTM) | percent |  |  |
| `return_on_invested_capital` | Return on Invested Capital (TTM) | percent |  |  |
| `total_revenue_yoy_growth_fy` | Revenue (Annual YoY Growth) | percent |  |  |
| `revenue_per_employee` | Revenue per Employee (FY) | fundamental_price |  |  |
| `total_revenue_qoq_growth_fq` | Revenue (Quarterly QoQ Growth) | percent |  |  |
| `total_revenue_yoy_growth_fq` | Revenue (Quarterly YoY Growth) | percent |  |  |
| `total_revenue_yoy_growth_ttm` | Revenue (TTM YoY Growth) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_fy` | Selling General & Admin expenses Ratio (FY) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_ttm` | Selling General & Admin expenses Ratio (TTM) | percent |  |  |
| `float_shares_outstanding` | Shares Float | number |  |  |
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
| `submarket` | Submarket | text |  | 10 values: ``, `MAIN`, `OTCQB`, `OTCQX`, `PINK`, `PMTP`, `SPFM`, `STARS`, `SUBMARKET`, `WL` |
| `total_assets_yoy_growth_fy` | Total Assets (Annual YoY Growth) | percent |  |  |
| `total_assets` | Total Assets (MRQ) | fundamental_price |  |  |
| `total_assets_qoq_growth_fq` | Total Assets (Quarterly QoQ Growth) | percent |  |  |
| `total_assets_yoy_growth_fq` | Total Assets (Quarterly YoY Growth) | percent |  |  |
| `total_current_assets` | Total Current Assets (MRQ) | fundamental_price |  |  |
| `total_debt_yoy_growth_fy` | Total Debt (Annual YoY Growth) | percent |  |  |
| `total_debt` | Total Debt (MRQ) | fundamental_price |  |  |
| `total_debt_qoq_growth_fq` | Total Debt (Quarterly QoQ Growth) | percent |  |  |
| `total_debt_yoy_growth_fq` | Total Debt (Quarterly YoY Growth) | percent |  |  |
| `total_liabilities_fy` | Total Liabilities (FY) | fundamental_price |  |  |
| `total_liabilities_fq` | Total Liabilities (MRQ) | fundamental_price |  |  |
| `total_revenue` | Total Revenue (FY) | fundamental_price |  |  |
| `total_shares_outstanding_fundamental` | Total Shares Outstanding | number |  |  |
| `UO` | Ultimate Oscillator (7, 14, 28) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `earnings_release_next_date` | Upcoming Earnings Date | time |  |  |
| `Volatility.D` | Volatility | number |  |  |
| `Volatility.M` | Volatility Month | number |  |  |
| `Volatility.W` | Volatility Week | number |  |  |
| `VWAP` | Volume Weighted Average Price | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `VWMA` | Volume Weighted Moving Average (20) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Perf.W` | Weekly Performance | number |  |  |
| `W.R` | Williams Percent Range (14) | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `Perf.Y` | Yearly Performance | number |  |  |
| `Perf.YTD` | YTD Performance | number |  |  |
| `currency` | Quote currency | text |  | 53 values: `AED`, `ARS`, `AUD`, `BDT`, `BHD`, `BRL`, `CAD`, `CHF`, `CLP`, `CNY`, `COP`, `CZK`, `DKK`, `EGP`, `EUR`, `GBP`, `GBX`, `HKD`, `HUF`, `IDR`, `ILA`, `INR`, `ISK`, `JPY`, `KES` … |
| `total_shares_outstanding` | Available Coins | number |  |  |
| `market_cap_calc` | Market Capitalization | number |  |  |
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
| `actively_managed` |  | text |  | 2 values: `0`, `1` |
| `all_time_high` |  | price |  |  |
| `all_time_high_day` |  | time |  |  |
| `all_time_low` |  | price |  |  |
| `all_time_low_day` |  | time |  |  |
| `all_time_open` |  | price |  |  |
| `altman_z_score_fy` |  | number |  |  |
| `altman_z_score_ttm` |  | number |  |  |
| `amount_recent` |  | fundamental_price |  |  |
| `amount_upcoming` |  | fundamental_price |  |  |
| `asset_class` |  | text |  | 6 values: `1af0389838508d7016a9841eb6273962`, `4071518f1736a5a43dae51b47590322f`, `8fe80395f389e29e3ea42210337f0350`, `b090e99b8d95f5837ec178c2d3d3fc50`, `b6e443a6c4a8a2e7918c5dbf3d45c796`, `c05f85d35d1cd0be6ebb2af4be16e06a` |
| `asset_turnover_current` |  | number |  |  |
| `asset_turnover_fy` |  | number |  |  |
| `aum` |  | fundamental_price |  |  |
| `aum_perf.1M` |  | number |  |  |
| `aum_perf.1Y` |  | number |  |  |
| `aum_perf.3M` |  | number |  |  |
| `aum_perf.3Y` |  | number |  |  |
| `aum_perf.5Y` |  | number |  |  |
| `aum_perf.YTD` |  | number |  |  |
| `average_volume` |  | number |  |  |
| `bars_count` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `base_currency_kind` |  | text |  |  |
| `beta_3_year` |  | number |  |  |
| `beta_5_year` |  | number |  |  |
| `book_tangible_per_share_current` |  | fundamental_price |  |  |
| `book_tangible_per_share_fh` |  | fundamental_price |  |  |
| `book_tangible_per_share_fq` |  | fundamental_price |  |  |
| `book_tangible_per_share_fy` |  | fundamental_price |  |  |
| `book_value_per_share_current` |  | fundamental_price |  |  |
| `book_value_per_share_estimate_fh` |  | fundamental_price |  |  |
| `book_value_per_share_estimate_fq` |  | fundamental_price |  |  |
| `book_value_per_share_estimate_fy` |  | fundamental_price |  |  |
| `book_value_per_share_fh` |  | fundamental_price |  |  |
| `book_value_per_share_fq` |  | fundamental_price |  |  |
| `book_value_per_share_fy` |  | fundamental_price |  |  |
| `brand` |  | text |  | 1040 values: `10X`, `1nvest`, `21Shares`, `27Four Funds`, `360 ONE`, `3Edge`, `3V Invest`, `3iQ`, `AAM`, `AB Funds`, `ABF`, `ABF PAIF`, `ABSA`, `ACE`, `ACSI Funds`, `ACV`, `ADRhedged`, `AGF`, `AGP`, `AK`, `ALPS`, `AMG`, `AMINA`, `AORIS`, `AOT` … |
| `buyback_yield` |  | fundamental_price |  |  |
| `capex_per_share_current` |  | fundamental_price |  |  |
| `capex_per_share_fh` |  | fundamental_price |  |  |
| `capex_per_share_fq` |  | fundamental_price |  |  |
| `capex_per_share_fy` |  | fundamental_price |  |  |
| `capex_per_share_ttm` |  | fundamental_price |  |  |
| `capital_expenditures_estimate_fh` |  | fundamental_price |  |  |
| `capital_expenditures_estimate_fq` |  | fundamental_price |  |  |
| `capital_expenditures_estimate_fy` |  | fundamental_price |  |  |
| `capital_expenditures_estimate_ntm` |  | fundamental_price |  |  |
| `capital_expenditures_fh` |  | fundamental_price |  |  |
| `capital_expenditures_fq` |  | fundamental_price |  |  |
| `capital_expenditures_fy` |  | fundamental_price |  |  |
| `capital_expenditures_qoq_growth_fq` |  | percent |  |  |
| `capital_expenditures_ttm` |  | fundamental_price |  |  |
| `capital_expenditures_unchanged_fq_h` |  | num_slice |  |  |
| `capital_expenditures_unchanged_fy_h` |  | num_slice |  |  |
| `capital_expenditures_unchanged_ttm_h` |  | num_slice |  |  |
| `capital_expenditures_yoy_growth_fq` |  | percent |  |  |
| `capital_expenditures_yoy_growth_fy` |  | percent |  |  |
| `capital_expenditures_yoy_growth_ttm` |  | percent |  |  |
| `cash_dividend_coverage_ratio_fy` |  | number |  |  |
| `cash_dividend_coverage_ratio_ttm` |  | number |  |  |
| `cash_f_financing_activities_estimate_fh` |  | fundamental_price |  |  |
| `cash_f_financing_activities_estimate_fq` |  | fundamental_price |  |  |
| `cash_f_financing_activities_estimate_fy` |  | fundamental_price |  |  |
| `cash_f_financing_activities_estimate_ntm` |  | fundamental_price |  |  |
| `cash_f_financing_activities_fh` |  | fundamental_price |  |  |
| `cash_f_financing_activities_fq` |  | fundamental_price |  |  |
| `cash_f_financing_activities_fy` |  | fundamental_price |  |  |
| `cash_f_financing_activities_ttm` |  | fundamental_price |  |  |
| `cash_f_investing_activities_estimate_fh` |  | fundamental_price |  |  |
| `cash_f_investing_activities_estimate_fq` |  | fundamental_price |  |  |
| `cash_f_investing_activities_estimate_fy` |  | fundamental_price |  |  |
| `cash_f_investing_activities_estimate_ntm` |  | fundamental_price |  |  |
| `cash_f_investing_activities_fh` |  | fundamental_price |  |  |
| `cash_f_investing_activities_fq` |  | fundamental_price |  |  |
| `cash_f_investing_activities_fy` |  | fundamental_price |  |  |
| `cash_f_investing_activities_ttm` |  | fundamental_price |  |  |
| `cash_f_operating_activities_estimate_fh` |  | fundamental_price |  |  |
| `cash_f_operating_activities_estimate_fq` |  | fundamental_price |  |  |
| `cash_f_operating_activities_estimate_fy` |  | fundamental_price |  |  |
| `cash_f_operating_activities_estimate_ntm` |  | fundamental_price |  |  |
| `cash_f_operating_activities_fh` |  | fundamental_price |  |  |
| `cash_f_operating_activities_fq` |  | fundamental_price |  |  |
| `cash_f_operating_activities_fy` |  | fundamental_price |  |  |
| `cash_f_operating_activities_ttm` |  | fundamental_price |  |  |
| `cash_n_short_term_invest_estimate_fh` |  | fundamental_price |  |  |
| `cash_n_short_term_invest_estimate_fq` |  | fundamental_price |  |  |
| `cash_n_short_term_invest_estimate_fy` |  | fundamental_price |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fy` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fy` |  | number |  |  |
| `cash_per_share_current` |  | fundamental_price |  |  |
| `cash_per_share_fh` |  | fundamental_price |  |  |
| `cash_per_share_fq` |  | fundamental_price |  |  |
| `cash_per_share_fy` |  | fundamental_price |  |  |
| `cash_ratio` |  | number |  |  |
| `category` |  | text |  | 29 values: `1`, `26`, `27`, `3`, `34`, `35`, `4`, `44`, `5`, `50`, `56`, `57`, `58`, `59`, `6`, `60`, `61`, `62`, `63`, `64`, `65`, `66`, `68`, `69`, `7` … |
| `cfi_code` |  | text |  | 254 values: `CBCIXU`, `CBOIXU`, `CECGBS`, `CECGBU`, `CECGES`, `CECGEU`, `CECGLS`, `CECGMS`, `CECGMX`, `CECIBS`, `CECIBU`, `CECIES`, `CECIEU`, `CECIMS`, `CECIMU`, `CECIMX`, `CECJLS`, `CECJLU`, `CECJMS`, `CECJMU`, `CECJRS`, `CECJXU`, `CEMGLS`, `CEMGLU`, `CEMILS` … |
| `circulating_to_max_supply_ratio` |  | percent |  |  |
| `continuous_dividend_growth` |  | number |  |  |
| `continuous_dividend_payout` |  | number |  |  |
| `cost_of_goods_estimate_fh` |  | fundamental_price |  |  |
| `cost_of_goods_estimate_fq` |  | fundamental_price |  |  |
| `cost_of_goods_estimate_fy` |  | fundamental_price |  |  |
| `cost_of_goods_estimate_ntm` |  | fundamental_price |  |  |
| `country_code_fund` |  | text |  | 114 values: `AE`, `AR`, `AT`, `AU`, `AX`, `AZ`, `BB`, `BD`, `BE`, `BG`, `BH`, `BM`, `BR`, `BS`, `BW`, `CA`, `CH`, `CI`, `CL`, `CN`, `CO`, `CR`, `CY`, `CZ`, `DE` … |
| `coupon` |  | number |  |  |
| `cryptoasset-info.description` |  | text |  |  |
| `cryptoasset-info.id` |  | text |  |  |
| `currency_hedged_flag` |  | text |  | 2 values: `0`, `1` |
| `currency_id` |  | text |  | 53 values: `AED`, `ARS`, `AUD`, `BDT`, `BHD`, `BRL`, `CAD`, `CHF`, `CLP`, `CNY`, `COP`, `CZK`, `DKK`, `EGP`, `EUR`, `GBP`, `HKD`, `HUF`, `IDR`, `INR`, `ISK`, `JPY`, `KES`, `KRW`, `LKR` … |
| `currency_kind` |  | text |  | 1 values: `fiat` |
| `current_ratio_current` |  | number |  |  |
| `current_ratio_fq` |  | number |  |  |
| `current_ratio_fy` |  | number |  |  |
| `current_session` |  | text |  | 4 values: `market`, `out_of_session`, `post_market`, `pre_market` |
| `current_yield` |  | percent |  |  |
| `daily-bar.time` |  | number |  |  |
| `days_to_maturity` |  | number |  |  |
| `debt_to_asset_fq` |  | number |  |  |
| `debt_to_asset_fy` |  | number |  |  |
| `debt_to_assets` |  | number |  |  |
| `debt_to_equity_fq` |  | number |  |  |
| `debt_to_equity_fy` |  | number |  |  |
| `debt_to_revenue_fy` |  | number |  |  |
| `debt_to_revenue_ttm` |  | number |  |  |
| `description` |  | text |  |  |
| `diluted_shares_outstanding_fq` |  | fundamental_price |  |  |
| `dividend_amount_recent` |  | fundamental_price |  |  |
| `dividend_amount_upcoming` |  | fundamental_price |  |  |
| `dividend_ex_date_recent` |  | time |  |  |
| `dividend_ex_date_upcoming` |  | time |  |  |
| `dividend_frequency_recent` |  | text |  |  |
| `dividend_frequency_upcoming` |  | text |  |  |
| `dividend_payment_date_recent` |  | time |  |  |
| `dividend_payment_date_upcoming` |  | time |  |  |
| `dividend_payout_ratio_fy` |  | percent |  |  |
| `dividend_payout_ratio_percent_fq` |  | percent |  |  |
| `dividend_payout_ratio_percent_fy` |  | percent |  |  |
| `dividend_payout_ratio_ttm` |  | percent |  |  |
| `dividend_treatment` |  | text |  | 2 values: `Capitalizes`, `Distributes` |
| `dividend_yield_upcoming` |  | number |  |  |
| `dividends_frequency` |  | text |  | 6 values: `Annual`, `Monthly`, `Other`, `Quarterly`, `Semi-annual`, `Weekly` |
| `dividends_yield` |  | number |  |  |
| `dividends_yield_current` |  | percent |  |  |
| `dividends_yield_fq` |  | percent |  |  |
| `dividends_yield_fy` |  | percent |  |  |
| `documents` |  | number |  |  |
| `dps_common_stock_prim_issue_fh` |  | fundamental_price |  |  |
| `dps_common_stock_prim_issue_fq` |  | fundamental_price |  |  |
| `dps_common_stock_prim_issue_fy_h` |  | num_slice |  |  |
| `dps_common_stock_prim_issue_ttm` |  | fundamental_price |  |  |
| `dps_estimate_fh` |  | fundamental_price |  |  |
| `dps_estimate_fq` |  | fundamental_price |  |  |
| `dps_estimate_fy` |  | fundamental_price |  |  |
| `dps_estimate_ntm` |  | fundamental_price |  |  |
| `earnings_fq_h` |  | interface |  |  |
| `earnings_per_share_basic_cagr_5y` |  | percent |  |  |
| `earnings_per_share_basic_fh` |  | fundamental_price |  |  |
| `earnings_per_share_basic_fq` |  | fundamental_price |  |  |
| `earnings_per_share_basic_fy` |  | fundamental_price |  |  |
| `earnings_per_share_basic_fy_h` |  | num_slice |  |  |
| `earnings_per_share_diluted_5y_growth_fy` |  | percent |  |  |
| `earnings_per_share_diluted_fh` |  | fundamental_price |  |  |
| `earnings_per_share_diluted_fq` |  | fundamental_price |  |  |
| `earnings_per_share_diluted_fq_h` |  | num_slice |  |  |
| `earnings_per_share_diluted_fy` |  | fundamental_price |  |  |
| `earnings_per_share_diluted_fy_h` |  | num_slice |  |  |
| `earnings_per_share_diluted_ttm_h` |  | num_slice |  |  |
| `earnings_per_share_fh` |  | fundamental_price |  |  |
| `earnings_per_share_forecast_fq` |  | fundamental_price |  |  |
| `earnings_per_share_forecast_next_fh` |  | fundamental_price |  |  |
| `earnings_per_share_forecast_next_fy` |  | fundamental_price |  |  |
| `earnings_per_share_fy` |  | fundamental_price |  |  |
| `earnings_publication_type_fq` |  | number |  |  |
| `earnings_publication_type_next_fq` |  | number |  |  |
| `earnings_release_calendar_date` |  | time |  |  |
| `earnings_release_next_calendar_date` |  | time |  |  |
| `earnings_release_next_time` |  | number |  |  |
| `earnings_release_next_trading_date_fq` |  | time |  |  |
| `earnings_release_next_trading_date_fy` |  | time |  |  |
| `earnings_release_time` |  | number |  |  |
| `earnings_release_trading_date_fq` |  | time |  |  |
| `earnings_release_trading_date_fy` |  | time |  |  |
| `earnings_yield` |  | percent |  |  |
| `ebit_estimate_fh` |  | fundamental_price |  |  |
| `ebit_estimate_fq` |  | fundamental_price |  |  |
| `ebit_estimate_fy` |  | fundamental_price |  |  |
| `ebit_estimate_ntm` |  | fundamental_price |  |  |
| `ebit_per_share_current` |  | fundamental_price |  |  |
| `ebit_per_share_fh` |  | fundamental_price |  |  |
| `ebit_per_share_fq` |  | fundamental_price |  |  |
| `ebit_per_share_fy` |  | fundamental_price |  |  |
| `ebit_per_share_ttm` |  | fundamental_price |  |  |
| `ebit_ttm` |  | fundamental_price |  |  |
| `ebitda_estimate_fh` |  | fundamental_price |  |  |
| `ebitda_estimate_fq` |  | fundamental_price |  |  |
| `ebitda_estimate_fy` |  | fundamental_price |  |  |
| `ebitda_estimate_ntm` |  | fundamental_price |  |  |
| `ebitda_fh` |  | fundamental_price |  |  |
| `ebitda_fq` |  | fundamental_price |  |  |
| `ebitda_fq_h` |  | num_slice |  |  |
| `ebitda_fy` |  | fundamental_price |  |  |
| `ebitda_fy_h` |  | num_slice |  |  |
| `ebitda_interst_cover_fy` |  | number |  |  |
| `ebitda_interst_cover_ttm` |  | number |  |  |
| `ebitda_less_capex_interst_cover_fy` |  | number |  |  |
| `ebitda_less_capex_interst_cover_ttm` |  | number |  |  |
| `ebitda_margin_fy` |  | percent |  |  |
| `ebitda_margin_ttm` |  | percent |  |  |
| `ebitda_per_employee_fy` |  | fundamental_price |  |  |
| `ebitda_per_share_current` |  | fundamental_price |  |  |
| `ebitda_per_share_fh` |  | fundamental_price |  |  |
| `ebitda_per_share_fq` |  | fundamental_price |  |  |
| `ebitda_per_share_fy` |  | fundamental_price |  |  |
| `ebitda_per_share_ttm` |  | fundamental_price |  |  |
| `ebitda_ttm` |  | fundamental_price |  |  |
| `ebitda_ttm_h` |  | num_slice |  |  |
| `effective_interest_rate_on_debt_fy` |  | percent |  |  |
| `effective_interest_rate_on_debt_ttm` |  | percent |  |  |
| `enterprise_value_current` |  | fundamental_price |  |  |
| `enterprise_value_ebit_fwd` |  | number |  |  |
| `enterprise_value_ebitda_current` |  | number |  |  |
| `enterprise_value_ebitda_fwd` |  | number |  |  |
| `enterprise_value_sales_fwd` |  | number |  |  |
| `enterprise_value_to_ebit_ttm` |  | number |  |  |
| `enterprise_value_to_free_cash_flow_ttm` |  | number |  |  |
| `enterprise_value_to_gross_profit_ttm` |  | number |  |  |
| `enterprise_value_to_revenue_ttm` |  | number |  |  |
| `eps_diluted_growth_percent_fq` |  | percent |  |  |
| `eps_diluted_growth_percent_fy` |  | percent |  |  |
| `eps_estimate_ntm` |  | fundamental_price |  |  |
| `eps_surprise_fq` |  | fundamental_price |  |  |
| `eps_surprise_percent_fq` |  | percent |  |  |
| `etf_fund_currency` |  | text |  | 40 values: `AED`, `AUD`, `BGN`, `BRL`, `CAD`, `CHF`, `CLP`, `CNY`, `COP`, `CZK`, `DKK`, `EUR`, `GBP`, `HKD`, `HUF`, `IDR`, `ILS`, `INR`, `JPY`, `KRW`, `KWD`, `MXN`, `MYR`, `NOK`, `NZD` … |
| `etf_holdings_count` |  | number |  |  |
| `ex_dividend_date_recent` |  | time |  |  |
| `ex_dividend_date_upcoming` |  | time |  |  |
| `expected_annual_dividends` |  | number |  |  |
| `expense_ratio` |  | number |  |  |
| `expiration` |  | time |  |  |
| `first_bar_time` |  | time |  |  |
| `fiscal_period_current` |  | text |  | 9 values: `2025-H2`, `2025-Q3`, `2025-Q4`, `2026-H1`, `2026-H2`, `2026-Q1`, `2026-Q2`, `2026-Q3`, `2026-Q4` |
| `fiscal_period_end_current` |  | time |  |  |
| `fiscal_period_end_fh` |  | time |  |  |
| `fiscal_period_end_fh_h` |  | num_slice |  |  |
| `fiscal_period_end_fq` |  | time |  |  |
| `fiscal_period_end_fy` |  | time |  |  |
| `fiscal_period_fy` |  | text |  | 3 values: `2024`, `2025`, `2026` |
| `fiscal_period_fy_h` |  | num_slice |  |  |
| `fixed_assets_turnover_fq` |  | number |  |  |
| `fixed_assets_turnover_fy` |  | number |  |  |
| `float_shares_outstanding_current` |  | number |  |  |
| `float_shares_percent_current` |  | percent |  |  |
| `focus` |  | text |  | 184 values: `1`, `10`, `102`, `105`, `106`, `11`, `111`, `113`, `115`, `117`, `118`, `12`, `121`, `122`, `123`, `13`, `14`, `15`, `16`, `17`, `18`, `20`, `2004`, `2005`, `2011` … |
| `fractional` |  | text |  | 1 values: `false` |
| `free_cash_flow` |  | fundamental_price |  |  |
| `free_cash_flow_cagr_5y` |  | percent |  |  |
| `free_cash_flow_estimate_fh` |  | fundamental_price |  |  |
| `free_cash_flow_estimate_fq` |  | fundamental_price |  |  |
| `free_cash_flow_estimate_fy` |  | fundamental_price |  |  |
| `free_cash_flow_estimate_ntm` |  | fundamental_price |  |  |
| `free_cash_flow_fh` |  | fundamental_price |  |  |
| `free_cash_flow_fq` |  | fundamental_price |  |  |
| `free_cash_flow_fq_h` |  | num_slice |  |  |
| `free_cash_flow_fy` |  | fundamental_price |  |  |
| `free_cash_flow_fy_h` |  | num_slice |  |  |
| `free_cash_flow_per_employee_fy` |  | fundamental_price |  |  |
| `free_cash_flow_per_share_current` |  | fundamental_price |  |  |
| `free_cash_flow_per_share_fh` |  | fundamental_price |  |  |
| `free_cash_flow_per_share_fq` |  | fundamental_price |  |  |
| `free_cash_flow_per_share_fy` |  | fundamental_price |  |  |
| `free_cash_flow_per_share_ttm` |  | fundamental_price |  |  |
| `free_cash_flow_ttm` |  | fundamental_price |  |  |
| `free_cash_flow_ttm_h` |  | num_slice |  |  |
| `frequency_recent` |  | text |  |  |
| `frequency_upcoming` |  | text |  |  |
| `fully_diluted_value` |  | price |  |  |
| `fund_flows.1M` |  | fundamental_price |  |  |
| `fund_flows.1Y` |  | fundamental_price |  |  |
| `fund_flows.3M` |  | fundamental_price |  |  |
| `fund_flows.3Y` |  | fundamental_price |  |  |
| `fund_flows.5Y` |  | fundamental_price |  |  |
| `fund_flows.YTD` |  | fundamental_price |  |  |
| `fundamental_currency_code` |  | text |  | 1 values: `USD` |
| `gap_down` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_down_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_up` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `gap_up_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `goodwill_fq` |  | fundamental_price |  |  |
| `goodwill_fy` |  | fundamental_price |  |  |
| `graham_numbers_fy` |  | number |  |  |
| `graham_numbers_ttm` |  | number |  |  |
| `gross_margin_fy` |  | percent |  |  |
| `gross_margin_percent_ttm` |  | percent |  |  |
| `gross_margin_ttm` |  | percent |  |  |
| `gross_profit_estimate_fh` |  | fundamental_price |  |  |
| `gross_profit_estimate_fq` |  | fundamental_price |  |  |
| `gross_profit_estimate_fy` |  | fundamental_price |  |  |
| `gross_profit_estimate_ntm` |  | fundamental_price |  |  |
| `gross_profit_fh` |  | fundamental_price |  |  |
| `gross_profit_fq_h` |  | num_slice |  |  |
| `gross_profit_fy` |  | fundamental_price |  |  |
| `gross_profit_fy_h` |  | num_slice |  |  |
| `gross_profit_ttm` |  | fundamental_price |  |  |
| `gross_profit_ttm_h` |  | num_slice |  |  |
| `has_ipo_data` |  | bool |  |  |
| `has_ipo_details_visible` |  | bool |  |  |
| `holdings_region` |  | text |  | 10 values: `176a9161fef684328415321c640ada1a`, `2402e241d9f16aa08de32421e0fa211f`, `3e8961795f30b441beb6aa81b2478c76`, `460491fc520f4dbfcff22d1a45f6b056`, `55a6587f79a2d84489e92e46d0a83f09`, `7612e84033b6f5f1a8b8039d9e25d9b5`, `96685265014af86dfee96774c03f6bab`, `9c70933aff6b2a6d08c687a6cbb6b765`, `a48e5d3946d87117fc67cd7de5f2c02a`, `cb2afe0cf8f6511856c8a73ea8de821e` |
| `holds_derivatives_flag` |  | text |  | 2 values: `0`, `1` |
| `income_from_cont_ops_fh` |  | fundamental_price |  |  |
| `income_from_cont_ops_fq` |  | fundamental_price |  |  |
| `income_from_cont_ops_fy` |  | fundamental_price |  |  |
| `income_from_cont_ops_ttm` |  | fundamental_price |  |  |
| `index_id` |  | text |  | 784 values: `SYML:ADX;FADGI`, `SYML:ADX;FADGMI`, `SYML:ADX;FADSI`, `SYML:ADX;FADX15`, `SYML:ADX;FADXI15`, `SYML:ADX;FADXSI`, `SYML:ASX;XAO`, `SYML:ASX;XFL`, `SYML:ASX;XJO`, `SYML:ASX;XKO`, `SYML:ASX;XMJ`, `SYML:ATHEX;FTSE`, `SYML:ATHEX;FTSEA`, `SYML:ATHEX;FTSEM`, `SYML:ATHEX;GD`, `SYML:BAHRAIN;BHBX`, `SYML:BAHRAIN;BIX`, `SYML:BCBA;IMV`, `SYML:BELEX;BELEX15`, `SYML:BELEX;BELEXLINE`, `SYML:BET;BUMIX`, `SYML:BET;BUX`, `SYML:BIST;X030C`, `SYML:BIST;X030EA`, `SYML:BIST;X030S` … |
| `index_priority` |  | number |  |  |
| `index_provider` |  | text |  | 209 values: `ARK Investment Management LP`, `Abacus FCF Advisors LLC`, `Acquirers Funds LLC`, `Akros S.R.L.`, `American Century Investment Management, Inc.`, `Arch Indices Investment Advisors LLC`, `Asia Index Pvt Ltd.`, `Associação Brasileira das Entidades dos Mercados Financeiro`, `Athens Stock Exchange`, `Auspice Capital Advisors Ltd.`, `Aztlan Equity Management LLC (Mexico)`, `B3 SAS`, `BITA GmbH`, `BNP Paribas SA (Italia)`, `BUZZ Indexes`, `Barclays Capital, Inc.`, `Beeland Interests, Inc.`, `Bianco Research Advisors LLC`, `Big Tree Capital LLC`, `Bitwise Asset Management, Inc.`, `Bitwise Index Services LLC`, `BlackRock Index Services LLC`, `Bloomberg Finance LP`, `Bloomberg Index Services Ltd.`, `BlueStar Global Investors LLC` … |
| `indexes` |  | interface |  |  |
| `indicated_annual_dividend` |  | fundamental_price |  |  |
| `indicators_bars_count` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `interst_cover_fy` |  | number |  |  |
| `interst_cover_ttm` |  | number |  |  |
| `invent_turnover_current` |  | number |  |  |
| `invent_turnover_fy` |  | number |  |  |
| `inverse_flag` |  | number |  |  |
| `ipo_announcement_date` |  | time |  |  |
| `ipo_blank_check_flag` |  | bool |  |  |
| `ipo_deal_amount` |  | price |  |  |
| `ipo_deal_amount_usd` |  | number |  |  |
| `ipo_market_cap` |  | price |  |  |
| `ipo_market_cap_usd` |  | number |  |  |
| `ipo_offer_date` |  | time |  |  |
| `ipo_offer_price` |  | price |  |  |
| `ipo_offer_price_performance` |  | percent |  |  |
| `ipo_offer_price_usd` |  | number |  |  |
| `ipo_offer_time` |  | time |  |  |
| `ipo_offered_shares` |  | number |  |  |
| `ipo_offered_shares_primary` |  | number |  |  |
| `ipo_offered_shares_secondary` |  | number |  |  |
| `ipo_price_range` |  | text |  | 4348 values: `0.00675-0.00825`, `0.08 - 0.08`, `0.10 - 0.15`, `0.11 - 0.16`, `0.12 - 0.14`, `0.12 - 0.16`, `0.13 - 0.17`, `0.14 - 0.16`, `0.15 - 0.25`, `0.17 - 0.23`, `0.18 - 0.22`, `0.19 - 0.25`, `0.20 - 0.24`, `0.20 - 0.26`, `0.20 - 0.30`, `0.20 - 0.35`, `0.20 - 0.40`, `0.20 - 0.60`, `0.21 - 0.25`, `0.21 - 0.29`, `0.22 - 0.26`, `0.22 - 0.27`, `0.22 - 0.28`, `0.22 - 0.30`, `0.22 - 0.34` … |
| `ipo_price_range_max` |  | price |  |  |
| `ipo_price_range_min` |  | price |  |  |
| `ipo_price_range_usd_max` |  | number |  |  |
| `ipo_price_range_usd_min` |  | number |  |  |
| `ipo_shares_outstanding` |  | number |  |  |
| `ipo_splitfactor_to_offer` |  | number |  |  |
| `is_blacklisted` |  | bool |  |  |
| `is_shariah_compliant` |  | bool |  |  |
| `is_symbol_primary_listing` |  | bool |  |  |
| `issuance_of_stock_net_ttm` |  | fundamental_price |  |  |
| `issuer` |  | text |  | 843 values: `10X Fund Managers (RF) Proprietary Ltd`, `10X Investments (Pty) Ltd.`, `21Shares AG`, `21co Holdings Ltd.`, `27four Collective Investments (RF) (Pty) Ltd.`, `360 One Wam Ltd.`, `3EDGE Asset Management LP`, `3Fourteen & SMI Advisory Services LLC`, `3iQ Corp.`, `483A Bay Street Holdings LP`, `818, Inc.`, `ABC-CA Fund Management Co., Ltd.`, `ABN AMRO Bank NV`, `ABSA Bank Ltd.`, `ACATIS Investment Kapitalverwaltungsgesellschaft mbH`, `AG Financial Services Group`, `AGF Management Ltd.`, `AI Funds, Inc.`, `AJM Ventures LLC`, `AMG National Corp.`, `AMMB Holdings Bhd.`, `ARK Invest LLC`, `ARK Investment Management LP`, `AXA-SPDB Investment Managers Co., Ltd.`, `Abacus Global Management, Inc.` … |
| `k1_form` |  | text |  | 2 values: `0`, `1` |
| `kind` |  | text |  | 2 values: `delay`, `rt` |
| `kind-delay` |  | number |  |  |
| `last-price-update-time` |  | time |  |  |
| `last-price-update-time-intraday` |  | time |  |  |
| `last_bar_update_time` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `last_report_frequency` |  | number |  |  |
| `launch_date` |  | time |  |  |
| `leverage` |  | text |  | 22 values: `006a8d8a2d5f12e33a74d69fb6433ba9`, `03c3e49bdc7aeee29cfd314c475fb410`, `1437a5ebc1f95c484fe8cd180aea771c`, `1636f70a7bf29b6ae3bdd70362782a50`, `176120eec53119ba0b1bb2b7a4e77538`, `205b83335c9d5a9dad8dae82e0856c1f`, `2c72cb32dc2f849b1df36621bbe622de`, `3c10eee496eb162ae0ed866403f2f032`, `40ae032593e6551c0ada26bc3cb0c8a7`, `49204706ae89a84f49643608a4a1eccb`, `496c5d6ea632c128a304c0b683f2bdfc`, `4e470efe30c902cb55523e3e03220099`, `70963b2ddfe1f798eda29e875ace6ab4`, `832d32f3f136894002cbfdd85961c8cf`, `88ba1211175189c63246bb29132b1d2e`, `a91c78e040f7b9d158f381e197f8beb4`, `b17077929ec55058d0eafe7827587934`, `c8bb3176ea791b632824fe397e9d0935`, `ca2e0331f4d1d23b2cd299f128853317`, `ded39cc46d3bcec2b9a969a7fdb5fabe`, `e782cde821fae6ce1b676cfd4d140aa8`, `ea26d532fadeb8bf0bc57e3ef88cec27` |
| `leverage_ratio` |  | text |  | 7 values: `1.25x`, `1.5x`, `1.75x`, `2x`, `3x`, `Other`, `Variable` |
| `leveraged_flag` |  | text |  | 3 values: `Inverse`, `Leveraged`, `Non-leveraged` |
| `logoid` |  | text |  |  |
| `long_term_capital` |  | number |  |  |
| `long_term_debt_fq` |  | fundamental_price |  |  |
| `long_term_debt_fy` |  | fundamental_price |  |  |
| `long_term_debt_to_assets_fq` |  | number |  |  |
| `long_term_debt_to_assets_fy` |  | number |  |  |
| `long_term_debt_to_equity_fq` |  | number |  |  |
| `low_after_high_all_change` |  | percent |  |  |
| `low_after_high_all_change_abs` |  | price |  |  |
| `market` |  | text |  | 71 values: `america`, `argentina`, `australia`, `austria`, `bahrain`, `bangladesh`, `belgium`, `brazil`, `bulgaria`, `canada`, `chile`, `china`, `colombia`, `croatia`, `cyprus`, `czech`, `denmark`, `egypt`, `estonia`, `finland`, `france`, `germany`, `greece`, `hongkong`, `hungary` … |
| `market_cap_to_tvl` |  | number |  |  |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `minmov` |  | number |  |  |
| `minmove2` |  | number |  |  |
| `minute-bar.time` |  | number |  |  |
| `most_recent_quarter_date` |  | time |  |  |
| `name` |  | text |  |  |
| `nav` |  | fundamental_price |  |  |
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
| `ncavps_ratio_current` |  | fundamental_price |  |  |
| `ncavps_ratio_fh` |  | fundamental_price |  |  |
| `ncavps_ratio_fq` |  | fundamental_price |  |  |
| `ncavps_ratio_fy` |  | fundamental_price |  |  |
| `neg_capital_expenditures_fh` |  | fundamental_price |  |  |
| `neg_capital_expenditures_fq` |  | fundamental_price |  |  |
| `neg_capital_expenditures_fy` |  | fundamental_price |  |  |
| `neg_capital_expenditures_ttm` |  | fundamental_price |  |  |
| `neg_research_and_dev_fh` |  | fundamental_price |  |  |
| `neg_research_and_dev_fq` |  | fundamental_price |  |  |
| `neg_research_and_dev_fy` |  | fundamental_price |  |  |
| `neg_research_and_dev_ttm` |  | fundamental_price |  |  |
| `neg_total_cash_dividends_paid_fh` |  | fundamental_price |  |  |
| `neg_total_cash_dividends_paid_fq` |  | fundamental_price |  |  |
| `neg_total_cash_dividends_paid_fy` |  | fundamental_price |  |  |
| `neg_total_cash_dividends_paid_ttm` |  | fundamental_price |  |  |
| `net_debt_fq` |  | fundamental_price |  |  |
| `net_debt_fy` |  | fundamental_price |  |  |
| `net_debt_to_ebitda_fq` |  | number |  |  |
| `net_debt_to_ebitda_fy` |  | number |  |  |
| `net_income_bef_disc_oper_fy` |  | fundamental_price |  |  |
| `net_income_cagr_5y` |  | percent |  |  |
| `net_income_estimate_fh` |  | fundamental_price |  |  |
| `net_income_estimate_fq` |  | fundamental_price |  |  |
| `net_income_estimate_fy` |  | fundamental_price |  |  |
| `net_income_estimate_ntm` |  | fundamental_price |  |  |
| `net_income_fh` |  | fundamental_price |  |  |
| `net_income_fq` |  | fundamental_price |  |  |
| `net_income_fq_h` |  | num_slice |  |  |
| `net_income_fy` |  | fundamental_price |  |  |
| `net_income_fy_h` |  | num_slice |  |  |
| `net_income_per_employee_fy` |  | fundamental_price |  |  |
| `net_income_ttm` |  | fundamental_price |  |  |
| `net_income_ttm_h` |  | num_slice |  |  |
| `net_margin` |  | percent |  |  |
| `net_margin_fy` |  | percent |  |  |
| `net_margin_ttm` |  | percent |  |  |
| `net_revenue_after_provision_fh` |  | fundamental_price |  |  |
| `net_revenue_after_provision_fq` |  | fundamental_price |  |  |
| `net_revenue_after_provision_fy` |  | fundamental_price |  |  |
| `net_revenue_after_provision_ttm` |  | fundamental_price |  |  |
| `net_revenue_fh` |  | fundamental_price |  |  |
| `net_revenue_fq` |  | fundamental_price |  |  |
| `net_revenue_fy` |  | fundamental_price |  |  |
| `net_revenue_ttm` |  | fundamental_price |  |  |
| `next_dividend_date` |  | time |  |  |
| `niche` |  | text |  | 214 values: `10`, `100`, `1000`, `101`, `1011`, `1013`, `1015`, `1016`, `1017`, `1018`, `1019`, `102`, `1020`, `1021`, `1028`, `1029`, `1033`, `1034`, `1035`, `1037`, `1038`, `104`, `1040`, `1043`, `1044` … |
| `non_gaap_price_to_earnings_per_share_forecast_next_fy` |  | number |  |  |
| `number_of_employees_fy` |  | number |  |  |
| `number_of_shareholders_fy` |  | number |  |  |
| `nvt` |  | number |  |  |
| `open_interest_to_volume_24h` |  | number |  |  |
| `oper_income_fh` |  | fundamental_price |  |  |
| `oper_income_fq` |  | fundamental_price |  |  |
| `oper_income_fy` |  | fundamental_price |  |  |
| `oper_income_per_employee_fy` |  | fundamental_price |  |  |
| `oper_income_ttm` |  | fundamental_price |  |  |
| `operating_cash_flow_per_share_current` |  | fundamental_price |  |  |
| `operating_cash_flow_per_share_fh` |  | fundamental_price |  |  |
| `operating_cash_flow_per_share_fq` |  | fundamental_price |  |  |
| `operating_cash_flow_per_share_fy` |  | fundamental_price |  |  |
| `operating_cash_flow_per_share_ttm` |  | fundamental_price |  |  |
| `operating_margin_fy` |  | percent |  |  |
| `operating_margin_ttm` |  | percent |  |  |
| `payment_date_recent` |  | time |  |  |
| `payment_date_upcoming` |  | time |  |  |
| `piotroski_f_score_fy` |  | number |  |  |
| `piotroski_f_score_ttm` |  | number |  |  |
| `post_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `postmarket_time` |  | time |  |  |
| `pre_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `pre_change_abs` |  | price | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `pre_tax_margin_ttm` |  | percent |  |  |
| `preferred_dividends` |  | number |  |  |
| `premarket_time` |  | time |  |  |
| `price_52_week_high_date` |  | time |  |  |
| `price_52_week_low_date` |  | time |  |  |
| `price_annual_book` |  | number |  |  |
| `price_annual_sales` |  | number |  |  |
| `price_book_current` |  | number |  |  |
| `price_book_fwd` |  | number |  |  |
| `price_cash_flow_current` |  | number |  |  |
| `price_earnings_current` |  | number |  |  |
| `price_earnings_forward_fy` |  | number |  |  |
| `price_earnings_fwd` |  | number |  |  |
| `price_earnings_growth_ttm` |  | number |  |  |
| `price_free_cash_flow_current` |  | number |  |  |
| `price_sales` |  | price |  |  |
| `price_sales_current` |  | number |  |  |
| `price_sales_fwd` |  | number |  |  |
| `price_target_1y` |  | price |  |  |
| `price_target_1y_delta` |  | percent |  |  |
| `price_target_average` |  | number |  |  |
| `price_target_high` |  | number |  |  |
| `price_target_low` |  | number |  |  |
| `price_target_median` |  | number |  |  |
| `price_to_cash_f_operating_activities_ttm` |  | number |  |  |
| `price_to_cash_ratio` |  | number |  |  |
| `price_to_working_capital_fq` |  | number |  |  |
| `pricescale` |  | number |  |  |
| `provider-id` |  | text |  | 3 values: `alor`, `ice`, `sixgroup` |
| `quick_ratio_current` |  | number |  |  |
| `quick_ratio_fq` |  | number |  |  |
| `quick_ratio_fy` |  | number |  |  |
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
| `receivables_turnover_fq` |  | number |  |  |
| `receivables_turnover_fy` |  | number |  |  |
| `recommendation_buy` |  | number |  |  |
| `recommendation_hold` |  | number |  |  |
| `recommendation_mark` |  | number |  |  |
| `recommendation_over` |  | number |  |  |
| `recommendation_sell` |  | number |  |  |
| `recommendation_total` |  | number |  |  |
| `recommendation_under` |  | number |  |  |
| `relative_volume` |  | number |  |  |
| `relative_volume_intraday\|5` |  | number |  |  |
| `research_and_dev_estimate_fh` |  | fundamental_price |  |  |
| `research_and_dev_estimate_fq` |  | fundamental_price |  |  |
| `research_and_dev_estimate_fy` |  | fundamental_price |  |  |
| `research_and_dev_estimate_ntm` |  | fundamental_price |  |  |
| `research_and_dev_fh` |  | fundamental_price |  |  |
| `research_and_dev_fq` |  | fundamental_price |  |  |
| `research_and_dev_fy` |  | fundamental_price |  |  |
| `research_and_dev_per_employee_fy` |  | fundamental_price |  |  |
| `research_and_dev_ttm` |  | fundamental_price |  |  |
| `return_of_invested_capital_percent_ttm` |  | percent |  |  |
| `return_on_assets_fq` |  | percent |  |  |
| `return_on_assets_fy` |  | percent |  |  |
| `return_on_capital_employed_fq` |  | percent |  |  |
| `return_on_capital_employed_fy` |  | percent |  |  |
| `return_on_common_equity_fy` |  | percent |  |  |
| `return_on_common_equity_ttm` |  | percent |  |  |
| `return_on_equity_adjust_to_book_fy` |  | percent |  |  |
| `return_on_equity_adjust_to_book_ttm` |  | percent |  |  |
| `return_on_equity_fq` |  | percent |  |  |
| `return_on_equity_fy` |  | percent |  |  |
| `return_on_invested_capital_fq` |  | percent |  |  |
| `return_on_invested_capital_fy` |  | percent |  |  |
| `return_on_tang_assets_fq` |  | percent |  |  |
| `return_on_tang_assets_fy` |  | percent |  |  |
| `return_on_tang_equity_fq` |  | percent |  |  |
| `return_on_tang_equity_fy` |  | percent |  |  |
| `return_on_total_capital_fq` |  | percent |  |  |
| `return_on_total_capital_fy` |  | percent |  |  |
| `revenue_estimate_ntm` |  | fundamental_price |  |  |
| `revenue_forecast_fq` |  | fundamental_price |  |  |
| `revenue_forecast_next_fh` |  | fundamental_price |  |  |
| `revenue_forecast_next_fq` |  | fundamental_price |  |  |
| `revenue_forecast_next_fy` |  | fundamental_price |  |  |
| `revenue_fq` |  | fundamental_price |  |  |
| `revenue_per_employee_fy` |  | fundamental_price |  |  |
| `revenue_per_share_current` |  | fundamental_price |  |  |
| `revenue_per_share_fh` |  | fundamental_price |  |  |
| `revenue_per_share_fq` |  | fundamental_price |  |  |
| `revenue_per_share_fy` |  | fundamental_price |  |  |
| `revenue_per_share_ttm` |  | fundamental_price |  |  |
| `revenue_surprise_fq` |  | fundamental_price |  |  |
| `revenue_surprise_percent_fq` |  | percent |  |  |
| `revenues_fq_h` |  | interface |  |  |
| `rtc` |  | price |  |  |
| `selection_criteria` |  | text |  | 34 values: `1`, `10`, `12`, `13`, `14`, `16`, `17`, `2`, `20`, `21`, `23`, `24`, `25`, `26`, `27`, `28`, `29`, `3`, `30`, `31`, `32`, `35`, `36`, `37`, `38` … |
| `sell_gen_admin_exp_other_fy` |  | fundamental_price |  |  |
| `sell_gen_admin_exp_other_ttm` |  | fundamental_price |  |  |
| `sell_gen_admin_exp_total_estimate_fh` |  | fundamental_price |  |  |
| `sell_gen_admin_exp_total_estimate_fq` |  | fundamental_price |  |  |
| `sell_gen_admin_exp_total_estimate_fy` |  | fundamental_price |  |  |
| `sell_gen_admin_exp_total_estimate_ntm` |  | fundamental_price |  |  |
| `share_buyback_ratio_fq` |  | percent |  |  |
| `share_buyback_ratio_fy` |  | percent |  |  |
| `shares_outstanding` |  | number |  |  |
| `short_term_debt_fq` |  | fundamental_price |  |  |
| `short_term_debt_fy` |  | fundamental_price |  |  |
| `shrhldrs_equity_fq` |  | fundamental_price |  |  |
| `shrhldrs_equity_fy` |  | fundamental_price |  |  |
| `shrhldrs_equity_to_total_assets_fq` |  | number |  |  |
| `shrhldrs_equity_to_total_assets_fy` |  | number |  |  |
| `sloan_ratio_fy` |  | percent |  |  |
| `sloan_ratio_ttm` |  | percent |  |  |
| `source-logoid` |  | text |  | 101 values: `source/ADX`, `source/AMEX`, `source/AQUIS`, `source/ASX`, `source/ATHEX`, `source/BAHRAIN`, `source/BCBA`, `source/BCS`, `source/BELEX`, `source/BET`, `source/BIST`, `source/BIVA`, `source/BME`, `source/BMFBOVESPA`, `source/BMV`, `source/BSE`, `source/BSESOF`, `source/BSSE`, `source/BVB`, `source/BVC`, `source/BVCV`, `source/BVL`, `source/BVMT`, `source/BX`, `source/CBOE` … |
| `strategy` |  | text |  | 30 values: `1`, `10`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `2`, `20`, `22`, `23`, `24`, `25`, `26`, `27`, `28`, `30`, `31`, `32`, `33`, `34`, `35`, `4` … |
| `subsessions` |  | interface |  |  |
| `subtype` |  | text |  | 8 values: ``, `closedend`, `common`, `etf`, `mutual`, `preferred`, `reit`, `unit` |
| `sum_for_enterprise_value` |  | fundamental_price |  |  |
| `sustainable_growth_rate_fy` |  | percent |  |  |
| `sustainable_growth_rate_ttm` |  | percent |  |  |
| `time` |  | time | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `time_business_day` |  | number |  |  |
| `tobin_q_ratio_fq` |  | number |  |  |
| `tobin_q_ratio_fy` |  | number |  |  |
| `top_revenue_country_code` |  | text |  | 139 values: `AE`, `AM`, `AO`, `AR`, `AT`, `AU`, `AZ`, `BA`, `BD`, `BE`, `BF`, `BG`, `BH`, `BM`, `BO`, `BR`, `BW`, `CA`, `CD`, `CG`, `CH`, `CI`, `CL`, `CM`, `CN` … |
| `total_assets_estimate_fh` |  | fundamental_price |  |  |
| `total_assets_estimate_fq` |  | fundamental_price |  |  |
| `total_assets_estimate_fy` |  | fundamental_price |  |  |
| `total_assets_fq` |  | fundamental_price |  |  |
| `total_assets_fq_h` |  | num_slice |  |  |
| `total_assets_fy` |  | fundamental_price |  |  |
| `total_assets_fy_h` |  | num_slice |  |  |
| `total_assets_per_employee_fy` |  | fundamental_price |  |  |
| `total_assets_to_equity_fq` |  | number |  |  |
| `total_assets_to_equity_fy` |  | number |  |  |
| `total_capital` |  | number |  |  |
| `total_cash_dividends_paid_fh` |  | fundamental_price |  |  |
| `total_cash_dividends_paid_fq` |  | fundamental_price |  |  |
| `total_cash_dividends_paid_fy` |  | fundamental_price |  |  |
| `total_cash_dividends_paid_ttm` |  | fundamental_price |  |  |
| `total_current_assets_fq` |  | fundamental_price |  |  |
| `total_current_assets_fy` |  | fundamental_price |  |  |
| `total_current_liabilities_fq` |  | fundamental_price |  |  |
| `total_current_liabilities_fy` |  | fundamental_price |  |  |
| `total_debt_estimate_fh` |  | fundamental_price |  |  |
| `total_debt_estimate_fq` |  | fundamental_price |  |  |
| `total_debt_estimate_fy` |  | fundamental_price |  |  |
| `total_debt_fq` |  | fundamental_price |  |  |
| `total_debt_fq_h` |  | num_slice |  |  |
| `total_debt_fy` |  | fundamental_price |  |  |
| `total_debt_fy_h` |  | num_slice |  |  |
| `total_debt_per_employee_fy` |  | fundamental_price |  |  |
| `total_debt_per_share_current` |  | fundamental_price |  |  |
| `total_debt_per_share_fh` |  | fundamental_price |  |  |
| `total_debt_per_share_fq` |  | fundamental_price |  |  |
| `total_debt_per_share_fy` |  | fundamental_price |  |  |
| `total_debt_to_capital_fq` |  | number |  |  |
| `total_debt_to_capital_fy` |  | number |  |  |
| `total_debt_to_ebitda_fq` |  | number |  |  |
| `total_debt_to_ebitda_fy` |  | number |  |  |
| `total_equity_fq` |  | fundamental_price |  |  |
| `total_equity_fy` |  | fundamental_price |  |  |
| `total_revenue_5y_growth_fy` |  | percent |  |  |
| `total_revenue_cagr_5y` |  | percent |  |  |
| `total_revenue_fh` |  | fundamental_price |  |  |
| `total_revenue_fq` |  | fundamental_price |  |  |
| `total_revenue_fq_h` |  | num_slice |  |  |
| `total_revenue_fy` |  | fundamental_price |  |  |
| `total_revenue_fy_h` |  | num_slice |  |  |
| `total_revenue_ttm` |  | fundamental_price |  |  |
| `total_revenue_ttm_h` |  | num_slice |  |  |
| `total_shares_outstanding_calculated` |  | number |  |  |
| `total_shares_outstanding_current` |  | number |  |  |
| `total_to_max_supply_ratio` |  | percent |  |  |
| `transparent_holding_flag` |  | text |  | 2 values: `0`, `1` |
| `typespecs` |  | set |  | 11 values: ``, `closedend`, `common`, `etf`, `mutual`, `odd`, `otc`, `preferred`, `reit`, `sharia`, `unit` |
| `ucits_compliant_flag` |  | text |  | 2 values: `0`, `1` |
| `update-time` |  | number |  |  |
| `update_mode` |  | text | 1, 5, 15, 30, 60, 120, 240, 1W, 1M | 2 values: `delayed_streaming_1200`, `streaming` |
| `update_time` |  | time |  |  |
| `velocity` |  | number |  |  |
| `volume_change` |  | percent | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `volume_change_abs` |  | number | 1, 5, 15, 30, 60, 120, 240, 1W, 1M |  |
| `weight_top_10` |  | percent |  |  |
| `weight_top_25` |  | percent |  |  |
| `weight_top_50` |  | percent |  |  |
| `weighting_scheme` |  | text |  | 23 values: `1`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `22`, `25`, `28`, `3`, `4`, `5`, `6`, `7`, `8`, `9` |
| `working_capital_fq` |  | fundamental_price |  |  |
| `working_capital_per_share_current` |  | fundamental_price |  |  |
| `working_capital_per_share_fh` |  | fundamental_price |  |  |
| `working_capital_per_share_fq` |  | fundamental_price |  |  |
| `working_capital_per_share_fy` |  | fundamental_price |  |  |
| `yield_recent` |  | number |  |  |
| `yield_upcoming` |  | number |  |  |
| `zmijewski_score_fy` |  | number |  |  |
| `zmijewski_score_ttm` |  | number |  |  |
