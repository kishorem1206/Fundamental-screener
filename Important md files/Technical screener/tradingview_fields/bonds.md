# Bonds fields

Bonds (market: `bonds`).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/bonds.html>

**215 fields** (242 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 1 values: `bond` |
| `is_primary` | Primary Listing | bool |  |  |
| `active_symbol` | Current trading day | bool |  |  |
| `change` | Change % | percent | 1 |  |
| `change_abs` | Change | price | 1 |  |
| `close` | Price | price | 1 |  |
| `price_earnings_ttm` | Price to Earnings Ratio (TTM) | number |  |  |
| `sector` | Group | text |  |  |
| `volume` | Volume | number | 1 |  |
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
| `change_from_open` | Change from Open % | percent | 1 |  |
| `change_from_open_abs` | Change from Open | price | 1 |  |
| `exchange` | Exchange | text |  | 1 values: `TVC` |
| `free_cash_flow_margin_fy` | Free Cash Flow Margin (FY) | percent |  |  |
| `free_cash_flow_margin_ttm` | Free Cash Flow Margin (TTM) | percent |  |  |
| `gap` | Gap % | percent | 1 |  |
| `gross_profit_margin_fy` | Gross Margin (FY) | percent |  |  |
| `high` | High | price | 1 |  |
| `low` | Low | price | 1 |  |
| `Perf.1M` | Monthly Performance | number |  |  |
| `net_income_bef_disc_oper_margin_fy` | Net Margin (FY) | percent |  |  |
| `open` | Open | price | 1 |  |
| `oper_income_margin_fy` | Operating Margin (FY) | percent |  |  |
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
| `research_and_dev_ratio_fy` | Research & development Ratio (FY) | percent |  |  |
| `research_and_dev_ratio_ttm` | Research & development Ratio (TTM) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_fy` | Selling General & Admin expenses Ratio (FY) | percent |  |  |
| `sell_gen_admin_exp_other_ratio_ttm` | Selling General & Admin expenses Ratio (TTM) | percent |  |  |
| `submarket` | Submarket | text |  | 1 values: `` |
| `Volatility.D` | Volatility | number |  |  |
| `Volatility.M` | Volatility Month | number |  |  |
| `Volatility.W` | Volatility Week | number |  |  |
| `Perf.W` | Weekly Performance | number |  |  |
| `Perf.Y` | Yearly Performance | number |  |  |
| `Perf.YTD` | YTD Performance | number |  |  |
| `currency` | Quote currency | text |  | 1 values: `EUR` |
| `ask` | Ask | price |  |  |
| `bid` | Bid | price |  |  |
| `24h_vol_to_market_cap` |  | number |  |  |
| `Bond.Change` |  | number | 1 |  |
| `Bond.Change.%` |  | number | 1 |  |
| `Bond.Currency` |  | text |  | 5 values: `BRL`, `KRW`, `PCTDY`, `PCTPAR`, `PCTYTM` |
| `Bond.Price` |  | number | 1 |  |
| `High.1M.Date` |  | time |  |  |
| `High.3M.Date` |  | time |  |  |
| `High.5D` |  | number |  |  |
| `High.6M.Date` |  | time |  |  |
| `High.All.Calc` |  | number |  |  |
| `High.All.Calc.Date` |  | time |  |  |
| `High.All.Date` |  | time |  |  |
| `Low.1M.Date` |  | time |  |  |
| `Low.3M.Date` |  | time |  |  |
| `Low.5D` |  | number |  |  |
| `Low.6M.Date` |  | time |  |  |
| `Low.After.High.All` |  | price |  |  |
| `Low.All.Calc` |  | number |  |  |
| `Low.All.Calc.Date` |  | time |  |  |
| `Low.All.Date` |  | time |  |  |
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
| `all_time_high` |  | price |  |  |
| `all_time_high_day` |  | time |  |  |
| `all_time_low` |  | price |  |  |
| `all_time_low_day` |  | time |  |  |
| `all_time_open` |  | price |  |  |
| `bars_count` |  | number | 1 |  |
| `base_currency_kind` |  | text |  |  |
| `bid_ask_spread_pct` |  | percent |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fy` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fy` |  | number |  |  |
| `circulating_to_max_supply_ratio` |  | percent |  |  |
| `close_1_days_back` |  | number |  |  |
| `close_30_days_back` |  | number |  |  |
| `close_365_days_back` |  | number |  |  |
| `country_code` |  | text |  | 50 values: `AT`, `AU`, `BE`, `BR`, `CA`, `CH`, `CL`, `CN`, `CO`, `CZ`, `DE`, `DK`, `ES`, `EU`, `FI`, `FR`, `GB`, `GR`, `HK`, `HU`, `ID`, `IE`, `IL`, `IN`, `IS` … |
| `country_code_fund` |  | text |  | 50 values: `AT`, `AU`, `BE`, `BR`, `CA`, `CH`, `CL`, `CN`, `CO`, `CZ`, `DE`, `DK`, `ES`, `EU`, `FI`, `FR`, `GB`, `GR`, `HK`, `HU`, `ID`, `IE`, `IL`, `IN`, `IS` … |
| `coupon` |  | number |  |  |
| `cryptoasset-info.description` |  | text |  |  |
| `cryptoasset-info.id` |  | text |  |  |
| `currency_id` |  | text |  | 2 values: ``, `EUR` |
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
| `first_bar_time_1d` |  | number |  |  |
| `float_shares_percent_current` |  | percent |  |  |
| `forex_priority` |  | number |  |  |
| `fractional` |  | text |  | 2 values: `false`, `true` |
| `fully_diluted_value` |  | price |  |  |
| `gap_down` |  | percent | 1 |  |
| `gap_down_abs` |  | price | 1 |  |
| `gap_up` |  | percent | 1 |  |
| `gap_up_abs` |  | price | 1 |  |
| `index_priority` |  | number |  |  |
| `indexes` |  | interface |  |  |
| `indicators_bars_count` |  | number | 1 |  |
| `is_blacklisted` |  | bool |  |  |
| `is_shariah_compliant` |  | bool |  |  |
| `is_symbol_primary_listing` |  | bool |  |  |
| `kind` |  | text |  | 1 values: `rt` |
| `kind-delay` |  | number |  |  |
| `last-price-update-time` |  | time |  |  |
| `last-price-update-time-intraday` |  | time |  |  |
| `last_bar_update_time` |  | number | 1 |  |
| `logoid` |  | text |  |  |
| `low_after_high_all_change` |  | percent |  |  |
| `low_after_high_all_change_abs` |  | price |  |  |
| `market` |  | text |  | 1 values: `bonds` |
| `market_cap_to_tvl` |  | number |  |  |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `minmov` |  | number |  |  |
| `minmove2` |  | number |  |  |
| `name` |  | text |  |  |
| `non_gaap_price_to_earnings_per_share_forecast_next_fy` |  | number |  |  |
| `nvt` |  | number |  |  |
| `open_interest_to_volume_24h` |  | number |  |  |
| `popularity_rank` |  | number |  |  |
| `post_change` |  | percent | 1 |  |
| `pre_change` |  | percent | 1 |  |
| `pre_change_abs` |  | price | 1 |  |
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
| `provider-id` |  | text |  | 2 values: `refinitiv`, `tvc` |
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
| `region` |  | text |  | 6 values: `Africa`, `Americas`, `Asia`, `Europe`, `Middle East`, `Pacific` |
| `relative_volume` |  | number |  |  |
| `revenue_surprise_percent_fq` |  | percent |  |  |
| `rtc` |  | price |  |  |
| `shrhldrs_equity_to_total_assets_fq` |  | number |  |  |
| `shrhldrs_equity_to_total_assets_fy` |  | number |  |  |
| `source-logoid` |  | text |  | 1 values: `provider/tvc` |
| `subsessions` |  | interface |  |  |
| `subtype` |  | text |  | 2 values: `cfd`, `government` |
| `term-to-maturity` |  | text |  | 34 values: `P10Y`, `P11Y`, `P12Y`, `P13Y`, `P14Y`, `P15Y`, `P16Y`, `P18Y`, `P19Y`, `P1M`, `P1Y`, `P20Y`, `P24Y`, `P25Y`, `P2M`, `P2Y`, `P30Y`, `P3M`, `P3Y`, `P40Y`, `P4M`, `P4Y`, `P50Y`, `P5M`, `P5Y` … |
| `time` |  | time | 1 |  |
| `time_business_day` |  | number |  |  |
| `total_debt_to_ebitda_fq` |  | number |  |  |
| `total_debt_to_ebitda_fy` |  | number |  |  |
| `total_to_max_supply_ratio` |  | percent |  |  |
| `typespecs` |  | set |  | 4 values: `benchmark`, `cfd`, `government`, `yield` |
| `update-time` |  | number |  |  |
| `update_mode` |  | text | 1 | 1 values: `streaming` |
| `update_time` |  | time |  |  |
| `velocity` |  | number |  |  |
| `volume_change` |  | percent | 1 |  |
| `volume_change_abs` |  | number | 1 |  |
