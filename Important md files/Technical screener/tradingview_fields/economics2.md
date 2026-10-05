# Economy fields

Economic indicators (market: `economics2`).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/economics2.html>

**130 fields** (130 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 1 values: `economic` |
| `is_primary` | Primary Listing | bool |  |  |
| `active_symbol` | Current trading day | bool |  |  |
| `change` | Change % | percent |  |  |
| `change_abs` | Change | price |  |  |
| `close` | Price | price |  |  |
| `price_earnings_ttm` | Price to Earnings Ratio (TTM) | number |  |  |
| `volume` | Volume | number |  |  |
| `Perf.All` | All Time Performance | number |  |  |
| `change_from_open` | Change from Open % | percent |  |  |
| `change_from_open_abs` | Change from Open | price |  |  |
| `exchange` | Exchange | text |  | 2 values: `ECONOMICS`, `FRED` |
| `free_cash_flow_margin_fy` | Free Cash Flow Margin (FY) | percent |  |  |
| `free_cash_flow_margin_ttm` | Free Cash Flow Margin (TTM) | percent |  |  |
| `gap` | Gap % | percent |  |  |
| `gross_profit_margin_fy` | Gross Margin (FY) | percent |  |  |
| `high` | High | price |  |  |
| `low` | Low | price |  |  |
| `net_income_bef_disc_oper_margin_fy` | Net Margin (FY) | percent |  |  |
| `open` | Open | price |  |  |
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
| `currency` | Quote currency | text |  | 143 values: `AED`, `AFN`, `ALL`, `AMD`, `AOA`, `ARS`, `AUD`, `AWG`, `AZN`, `BAM`, `BBD`, `BDT`, `BGN`, `BHD`, `BIF`, `BMD`, `BND`, `BOB`, `BRL`, `BSD`, `BTN`, `BWP`, `BYN`, `BZD`, `CAD` … |
| `24h_vol_to_market_cap` |  | number |  |  |
| `bars_count` |  | number |  |  |
| `base_currency_kind` |  | text |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fy` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fy` |  | number |  |  |
| `circulating_to_max_supply_ratio` |  | percent |  |  |
| `country_code` |  | text |  | 202 values: `AD`, `AE`, `AF`, `AG`, `AL`, `AM`, `AO`, `AR`, `AT`, `AU`, `AW`, `AZ`, `BA`, `BB`, `BD`, `BE`, `BF`, `BG`, `BH`, `BI`, `BJ`, `BM`, `BN`, `BO`, `BR` … |
| `coupon` |  | number |  |  |
| `cryptoasset-info.description` |  | text |  |  |
| `cryptoasset-info.id` |  | text |  |  |
| `currency_id` |  | text |  | 144 values: ``, `AED`, `AFN`, `ALL`, `AMD`, `AOA`, `ARS`, `AUD`, `AWG`, `AZN`, `BAM`, `BBD`, `BDT`, `BGN`, `BHD`, `BIF`, `BMD`, `BND`, `BOB`, `BRL`, `BSD`, `BTN`, `BWP`, `BYN`, `BZD` … |
| `currency_kind` |  | text |  | 1 values: `fiat` |
| `current_yield` |  | percent |  |  |
| `days_to_maturity` |  | number |  |  |
| `description` |  | text |  |  |
| `earnings_yield` |  | percent |  |  |
| `economic-category-id` |  | text |  | 13 values: `bsnss`, `clmt`, `cnsm`, `enrg`, `gdp`, `gov`, `hlth`, `hse`, `lbr`, `mny`, `prce`, `trd`, `txs` |
| `enterprise_value_ebit_fwd` |  | number |  |  |
| `enterprise_value_ebitda_fwd` |  | number |  |  |
| `enterprise_value_sales_fwd` |  | number |  |  |
| `eps_surprise_percent_fq` |  | percent |  |  |
| `expiration` |  | time |  |  |
| `float_shares_percent_current` |  | percent |  |  |
| `fully_diluted_value` |  | price |  |  |
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
| `market` |  | text |  | 1 values: `economics2` |
| `market_cap_to_tvl` |  | number |  |  |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `measure` |  | text |  | 3 values: `currency`, `price`, `unit` |
| `name` |  | text |  |  |
| `non_gaap_price_to_earnings_per_share_forecast_next_fy` |  | number |  |  |
| `nvt` |  | number |  |  |
| `open_interest_to_volume_24h` |  | number |  |  |
| `post_change` |  | percent |  |  |
| `pre_change` |  | percent |  |  |
| `pre_change_abs` |  | price |  |  |
| `price_book_fwd` |  | number |  |  |
| `price_earnings_fwd` |  | number |  |  |
| `price_sales` |  | price |  |  |
| `price_sales_fwd` |  | number |  |  |
| `price_target_1y` |  | price |  |  |
| `price_target_1y_delta` |  | percent |  |  |
| `price_to_cash_f_operating_activities_ttm` |  | number |  |  |
| `price_to_cash_ratio` |  | number |  |  |
| `price_to_working_capital_fq` |  | number |  |  |
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
| `subtype` |  | text |  | 1 values: `` |
| `time` |  | time |  |  |
| `total_debt_to_ebitda_fq` |  | number |  |  |
| `total_debt_to_ebitda_fy` |  | number |  |  |
| `total_to_max_supply_ratio` |  | percent |  |  |
| `typespecs` |  | set |  | 1 values: `` |
| `unit-id` |  | text |  | 8 values: `DAY`, `HOUR`, `LTR`, `MONTH`, `MTK`, `MWH`, `WEEK`, `YEAR` |
| `update_mode` |  | text |  | 1 values: `streaming` |
| `update_time` |  | time |  |  |
| `value-unit-id` |  | text |  | 25 values: `BLL`, `BUA`, `CAP`, `CMPNY`, `DEGC`, `FTQ`, `GWH`, `HOUR`, `JOU`, `KGM`, `MMTR`, `MTK`, `NBL`, `PCT`, `PCTGDP`, `PMP`, `POINT`, `PSN`, `PTP`, `RATIO`, `TIV`, `TNE`, `TWH`, `UNIT`, `YEAR` |
| `velocity` |  | number |  |  |
| `volume_change` |  | percent |  |  |
| `volume_change_abs` |  | number |  |  |
