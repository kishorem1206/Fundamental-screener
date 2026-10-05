# Bond (market `bond`) fields

Bonds, alternate market (market: `bond`).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/bond.html>

**278 fields** (278 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 1 values: `bond` |
| `is_primary` | Primary Listing | bool |  |  |
| `active_symbol` | Current trading day | bool |  |  |
| `change` | Change % | percent |  |  |
| `change_abs` | Change | price |  |  |
| `close` | Price | price |  |  |
| `price_earnings_ttm` | Price to Earnings Ratio (TTM) | number |  |  |
| `sector` | Group | text |  | 21 values: `Commercial Services`, `Communications`, `Consumer Durables`, `Consumer Non-Durables`, `Consumer Services`, `Distribution Services`, `Electronic Technology`, `Energy Minerals`, `Finance`, `Government`, `Health Services`, `Health Technology`, `Industrial Services`, `Miscellaneous`, `Non-Energy Minerals`, `Process Industries`, `Producer Manufacturing`, `Retail Trade`, `Technology Services`, `Transportation`, `Utilities` |
| `volume` | Volume | number |  |  |
| `Perf.All` | All Time Performance | number |  |  |
| `change_from_open` | Change from Open % | percent |  |  |
| `change_from_open_abs` | Change from Open | price |  |  |
| `country` | Region | text |  | 130 values: `Aland Islands`, `Albania`, `Andorra`, `Angola`, `Argentina`, `Armenia`, `Australia`, `Austria`, `Azerbaijan`, `Bahamas`, `Bahrain`, `Bangladesh`, `Barbados`, `Belgium`, `Benin`, `Bermuda`, `Bolivia`, `Bosnia and Herzegovina`, `Brazil`, `British Virgin Islands`, `Bulgaria`, `Burundi`, `Cameroon`, `Canada`, `Cayman Islands` … |
| `exchange` | Exchange | text |  | 51 values: `ASX`, `ATHEX`, `BET`, `BSESOF`, `BVB`, `BX`, `CHIXAU`, `DSEBD`, `DUS`, `EGX`, `EURONEXT`, `EUROTLX`, `FINRA`, `FWB`, `GETTEX`, `GPW`, `HAM`, `HAN`, `HKEX`, `JSE`, `LJSE`, `LS`, `LSE`, `LSX`, `LUXSE` … |
| `free_cash_flow_margin_fy` | Free Cash Flow Margin (FY) | percent |  |  |
| `free_cash_flow_margin_ttm` | Free Cash Flow Margin (TTM) | percent |  |  |
| `gap` | Gap % | percent |  |  |
| `gross_profit_margin_fy` | Gross Margin (FY) | percent |  |  |
| `high` | High | price |  |  |
| `industry` | Industry | text |  | 135 values: `Advertising/Marketing Services`, `Aerospace & Defense`, `Agricultural Commodities/Milling`, `Air Freight/Couriers`, `Airlines`, `Alternative Power Generation`, `Aluminum`, `Apparel/Footwear`, `Apparel/Footwear Retail`, `Auto Parts: OEM`, `Automotive Aftermarket`, `Beverages: Alcoholic`, `Beverages: Non-Alcoholic`, `Biotechnology`, `Broadcasting`, `Building Products`, `Cable/Satellite TV`, `Casinos/Gaming`, `Catalog/Specialty Distribution`, `Chemicals: Agricultural`, `Chemicals: Major Diversified`, `Chemicals: Specialty`, `Coal`, `Commercial Printing/Forms`, `Computer Communications` … |
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
| `currency` | Quote currency | text |  | 12 values: `AUD`, `EUR`, `GBX`, `MXN`, `MYR`, `NOK`, `PHP`, `QAR`, `SEK`, `TWD`, `USD`, `ZAC` |
| `ask` | Ask | price |  |  |
| `bid` | Bid | price |  |  |
| `24h_vol_to_market_cap` |  | number |  |  |
| `Bond.Currency` |  | text |  |  |
| `accrued_coupon_interest` |  | fundamental_price |  |  |
| `all_time_high` |  | price |  |  |
| `all_time_high_day` |  | time |  |  |
| `all_time_low` |  | price |  |  |
| `all_time_low_day` |  | time |  |  |
| `all_time_open` |  | price |  |  |
| `amount_outstanding_ratio` |  | number |  |  |
| `ask_net` |  | fundamental_price |  |  |
| `ask_pct` |  | percent |  |  |
| `bars_count` |  | number |  |  |
| `base_currency_kind` |  | text |  |  |
| `bid_ask_spread_pct` |  | percent |  |  |
| `bid_net` |  | fundamental_price |  |  |
| `bid_pct` |  | percent |  |  |
| `bond_agents` |  | interface |  |  |
| `bond_fitch_outlook_lt` |  | text |  | 3 values: `-1`, `0`, `1` |
| `bond_fitch_rating_lt` |  | text |  | 22 values: `500`, `530`, `550`, `570`, `580`, `590`, `600`, `610`, `620`, `630`, `640`, `650`, `660`, `670`, `680`, `690`, `700`, `710`, `720`, `730`, `740`, `750` |
| `bond_investment_grade` |  | number |  |  |
| `bond_issuer_cr_parent` |  | text |  | 4911 values: `123fahrschule SE`, `3M Co.`, `3i Group Plc`, `4iG Nyrt.`, `7C Solarparken AG`, `7R SA`, `8x8, Inc.`, `A Brown Co., Inc.`, `A.P. Møller-Mærsk A/S`, `A10 Networks, Inc.`, `A2A SpA`, `A2Dominion Housing Group Ltd.`, `AA Intermediate Co. Ltd.`, `AAC Technologies Holdings, Inc.`, `AAG FH UK Plc`, `AAR Corp.`, `AB SA`, `ABANCA Corporación Bancaria SA`, `ABAX Group AS`, `ABB Ltd.`, `ABC Co. SpA`, `ABC Transport Plc`, `ABN AMRO Bank NV`, `ABP Finance Plc`, `ACCO Brands Corp.` … |
| `bond_issuer_cr_parent_stock_symbol` |  | text |  | 3025 values: `ADX:ADCB`, `ADX:ADIB`, `ADX:ADPORTS`, `ADX:ALDAR`, `ADX:BOS`, `ADX:DANA`, `ADX:EAND`, `ADX:FAB`, `ADX:RAKBANK`, `ADX:SIB`, `AMEX:EQX`, `AMEX:GTE`, `ASX:ALD`, `ASX:AZJ`, `ASX:BEN`, `ASX:BHP`, `ASX:BOQ`, `ASX:BTR`, `ASX:BXB`, `ASX:CBA`, `ASX:CGF`, `ASX:CIA`, `ASX:CPU`, `ASX:CRN`, `ASX:CSL` … |
| `bond_issuer_snp_outlook_lt` |  | text |  | 4 values: `-1`, `0`, `1`, `2` |
| `bond_issuer_snp_outlook_st` |  | text |  |  |
| `bond_issuer_snp_rating_lt` |  | text |  | 23 values: `500`, `530`, `540`, `560`, `570`, `580`, `590`, `600`, `610`, `620`, `630`, `640`, `650`, `660`, `670`, `680`, `690`, `700`, `710`, `720`, `730`, `740`, `750` |
| `bond_issuer_snp_rating_lt_h` |  | interface |  |  |
| `bond_issuer_snp_rating_st` |  | text |  | 7 values: `500`, `570`, `610`, `660`, `680`, `700`, `730` |
| `bond_issuer_snp_rating_st_h` |  | interface |  |  |
| `bond_issuer_stock_symbol` |  | text |  | 2439 values: `ADX:ADCB`, `ADX:ADPORTS`, `ADX:ALDAR`, `ADX:EAND`, `ADX:FAB`, `ADX:RAKBANK`, `ADX:SIB`, `AMEX:EQX`, `AMEX:GTE`, `AMEX:PCG/PA`, `ASX:ALD`, `ASX:AZJ`, `ASX:BEN`, `ASX:BOQ`, `ASX:BTR`, `ASX:CAM`, `ASX:CBA`, `ASX:CGF`, `ASX:DNL`, `ASX:ECP`, `ASX:GC1`, `ASX:GFL`, `ASX:IAG`, `ASX:JDO`, `ASX:LFS` … |
| `bond_issuer_type` |  | text |  | 6 values: `agency`, `corporate`, `local-authority-political-division`, `securitized-collateralized`, `sovereign`, `supranational` |
| `bond_moodys_rating_lt` |  | text |  | 22 values: `500`, `550`, `560`, `570`, `580`, `590`, `600`, `610`, `620`, `630`, `640`, `650`, `660`, `670`, `680`, `690`, `700`, `710`, `720`, `730`, `740`, `750` |
| `bond_snp_outlook_lt` |  | text |  | 3 values: `-1`, `0`, `1` |
| `bond_snp_rating_lt` |  | text |  | 23 values: `500`, `530`, `550`, `560`, `570`, `580`, `590`, `600`, `610`, `620`, `630`, `640`, `650`, `660`, `670`, `680`, `690`, `700`, `710`, `720`, `730`, `740`, `750` |
| `bond_snp_rating_lt_h` |  | interface |  |  |
| `bond_type_gen` |  | text |  | 8 values: `asset-backed-security`, `bill-discount-note`, `bond-note`, `convertible-exchangeable`, `covered-bond`, `linked-securities`, `pass-through`, `preferred` |
| `bus_day_conv_method` |  | text |  | 8 values: `adj-following-business-day`, `adj-mod-following-business-day`, `following-business-day`, `modified-following-business-day`, `modified-previous-business-day`, `none`, `not-relevant`, `previous-business-day` |
| `call_frequency` |  | text |  | 14 values: `annual`, `continuously`, `discrete`, `every-10-years`, `every-2-years`, `every-3-years`, `every-4-years`, `every-5-years`, `every-6-years`, `every-coupon`, `monthly`, `on-effective-pmt-date`, `quarterly`, `semi-annual` |
| `call_next_date` |  | time |  |  |
| `call_next_price` |  | percent |  |  |
| `call_option` |  | text |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_current_liabilities_fy` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fq` |  | number |  |  |
| `cash_n_short_term_invest_to_total_debt_fy` |  | number |  |  |
| `cfi_code` |  | text |  | 270 values: `DAFNBB`, `DBFJCR`, `DBFJFB`, `DBFJFR`, `DBFJGR`, `DBFNAB`, `DBFNAN`, `DBFNAR`, `DBFNBB`, `DBFNBN`, `DBFNBR`, `DBFNCB`, `DBFNCR`, `DBFNDB`, `DBFNDR`, `DBFNFB`, `DBFNFM`, `DBFNFN`, `DBFNFR`, `DBFNFX`, `DBFNGB`, `DBFNGM`, `DBFNGN`, `DBFNGR`, `DBFNGX` … |
| `circulating_to_max_supply_ratio` |  | percent |  |  |
| `close_net` |  | fundamental_price |  |  |
| `close_pct` |  | percent |  |  |
| `conversion_option` |  | text |  | 3 values: `convertible`, `exchangeable`, `non-convertible` |
| `convexity` |  | number |  |  |
| `country_code` |  | text |  | 64 values: `AE`, `AL`, `AR`, `AT`, `AU`, `BD`, `BE`, `BG`, `BJ`, `BR`, `CA`, `CH`, `CN`, `CZ`, `DE`, `DK`, `EG`, `ES`, `EU`, `FI`, `FR`, `GA`, `GB`, `GR`, `HK` … |
| `country_code_fund` |  | text |  | 130 values: `AD`, `AE`, `AL`, `AM`, `AO`, `AR`, `AT`, `AU`, `AX`, `AZ`, `BA`, `BB`, `BD`, `BE`, `BG`, `BH`, `BI`, `BJ`, `BM`, `BO`, `BR`, `BS`, `CA`, `CD`, `CG` … |
| `country_fund` |  | text |  |  |
| `coupon` |  | number |  |  |
| `coupon_change_type` |  | text |  | 10 values: `combination`, `combo-fixed-floating`, `fixed-listing`, `fixed-payment`, `floating-rate`, `non-interest-bearing`, `overlap`, `step-up-down`, `variable`, `zero` |
| `coupon_currency` |  | text |  | 48 values: `AED`, `ARS`, `AUD`, `BDT`, `BGN`, `BRL`, `CAD`, `CHF`, `CLP`, `CNH`, `CNY`, `COP`, `CZK`, `DKK`, `DOP`, `EGP`, `EUR`, `GBP`, `GEL`, `HKD`, `HUF`, `IDR`, `INR`, `JMD`, `JPY` … |
| `coupon_date_next` |  | time |  |  |
| `coupon_date_prev` |  | time |  |  |
| `coupon_daycount_type` |  | text |  | 19 values: `1-1`, `1-n-rba`, `30-360`, `30-360-german`, `30-360s-german`, `30-365`, `30e-360`, `act-360`, `act-364`, `act-365`, `act-365-jpg`, `act-act`, `act-act-afb`, `act-act-canadian-comp`, `act-act-icma`, `act-act-isda`, `bus-252`, `nl-365`, `not-relevant` |
| `coupon_exdate_gap` |  | text |  | 33 values: `1-business`, `1-calendar`, `10-business`, `10-calendar`, `11-business`, `11-calendar`, `12-calendar`, `13-calendar`, `14-business`, `14-calendar`, `15-business`, `15-calendar`, `16-calendar`, `17-business`, `17-calendar`, `18-calendar`, `19-calendar`, `2-business`, `2-calendar`, `20-calendar`, `21-calendar`, `3-business`, `3-calendar`, `30-calendar`, `4-business` … |
| `coupon_exdate_gap_sort` |  | number |  |  |
| `coupon_frequency` |  | text |  | 7 values: `annual`, `monthly`, `on-aperiodic-schedule`, `on-effective-pmt-date`, `pays-at-maturity`, `quarterly`, `semi-annual` |
| `coupon_link` |  | text |  | 11 values: `credit-linked`, `credit-rating-sensitive`, `currency-linked`, `customized-index-linked`, `equity-linked`, `financial-test`, `index-linked`, `inflation-linked`, `interest-rate-linked`, `other`, `sustainability-linked` |
| `coupon_next_reset_date` |  | time |  |  |
| `coupon_pmt_date_type` |  | text |  | 2 values: `end-of-month`, `fixed-date` |
| `coupon_rate_ceiling` |  | percent |  |  |
| `coupon_rate_floor` |  | percent |  |  |
| `coupon_reset_frequency` |  | text |  | 14 values: `annual`, `daily`, `every-10-years`, `every-2-years`, `every-3-years`, `every-4-years`, `every-5-years`, `every-7-years`, `monthly`, `on-aperiodic-schedule`, `pays-at-maturity`, `quarterly`, `semi-annual`, `weekly` |
| `coupon_type_current` |  | text |  | 6 values: `conditional`, `fixed-payment`, `fixed-rate`, `floating`, `variable`, `zero` |
| `coupon_type_general` |  | text |  | 3 values: `fixed`, `variable`, `zero` |
| `coupon_underlying_index` |  | text |  | 112 values: `10y-bval-rate-php`, `12m-euribor-act-360`, `1m-euribor-act-360`, `1m-libor-usd`, `1m-term-sofr`, `3m-bid-bbsw-aud`, `3m-bubor`, `3m-cdor`, `3m-cibor`, `3m-cita`, `3m-compounded-saron`, `3m-euribor-act-360`, `3m-euribor-act-365`, `3m-jibar`, `3m-libor-chf`, `3m-libor-usd`, `3m-mid-bbsw-aud`, `3m-nibor`, `3m-robor`, `3m-stibor`, `3m-term-sofr`, `3m-vnibor`, `3m-wibor`, `6m-cibor`, `6m-cita` … |
| `covenant` |  | text |  | 4 values: `financial`, `financial-and-negative`, `negative`, `none` |
| `credit_enhancement_status` |  | text |  | 5 values: `junior-subordinate`, `senior`, `senior-subordinate`, `subordinate`, `unsubordinate` |
| `credit_enhancement_type` |  | text |  | 4 values: `guarantee`, `insured`, `none`, `statutory` |
| `cryptoasset-info.description` |  | text |  |  |
| `cryptoasset-info.id` |  | text |  |  |
| `currency_id` |  | text |  | 13 values: ``, `AUD`, `EUR`, `MXN`, `MYR`, `NOK`, `PHP`, `QAR`, `SEK`, `TWD`, `USD`, `XTVGBX`, `XTVZAC` |
| `currency_kind` |  | text |  | 1 values: `fiat` |
| `current_coupon` |  | percent |  |  |
| `current_session` |  | text |  | 4 values: `market`, `out_of_session`, `post_market`, `pre_market` |
| `current_yield` |  | percent |  |  |
| `daily-bar.close` |  | price |  |  |
| `daily-bar.time` |  | number |  |  |
| `days_to_maturity` |  | number |  |  |
| `denom_increment` |  | fundamental_price |  |  |
| `denom_min` |  | fundamental_price |  |  |
| `description` |  | text |  |  |
| `duration_type` |  | text |  | 4 values: `long-term`, `medium-term`, `perpetual`, `short-term` |
| `dv_01` |  | number |  |  |
| `earnings_yield` |  | percent |  |  |
| `enterprise_value_ebit_fwd` |  | number |  |  |
| `enterprise_value_ebitda_fwd` |  | number |  |  |
| `enterprise_value_sales_fwd` |  | number |  |  |
| `eps_surprise_percent_fq` |  | percent |  |  |
| `expiration` |  | time |  |  |
| `f_spread` |  | number |  |  |
| `final_redemption_amount` |  | percent |  |  |
| `float_shares_percent_current` |  | percent |  |  |
| `forex_priority` |  | number |  |  |
| `fractional` |  | text |  | 1 values: `false` |
| `fully_diluted_value` |  | price |  |  |
| `fundamental_currency_code` |  | text |  | 55 values: `AED`, `ARS`, `AUD`, `AZN`, `BDT`, `BGN`, `BRL`, `CAD`, `CHF`, `CLP`, `CNH`, `CNY`, `COP`, `CZK`, `DKK`, `DOP`, `EGP`, `EUR`, `GBP`, `GEL`, `HKD`, `HUF`, `IDR`, `INR`, `JMD` … |
| `g_spread` |  | number |  |  |
| `gap_down` |  | percent |  |  |
| `gap_down_abs` |  | price |  |  |
| `gap_up` |  | percent |  |  |
| `gap_up_abs` |  | price |  |  |
| `index_priority` |  | number |  |  |
| `indexes` |  | interface |  |  |
| `indicators_bars_count` |  | number |  |  |
| `inflation_protection` |  | text |  | 3 values: `coupon-uplift`, `non-protected`, `principal-uplift` |
| `is_blacklisted` |  | bool |  |  |
| `is_shariah_compliant` |  | bool |  |  |
| `is_symbol_primary_listing` |  | bool |  |  |
| `issue_amount` |  | fundamental_price |  |  |
| `issue_date` |  | time |  |  |
| `issue_status` |  | text |  | 2 values: `current`, `defaulted` |
| `issuer_fitch_outlook_lt` |  | text |  | 3 values: `-1`, `0`, `1` |
| `issuer_fitch_outlook_st` |  | text |  | 3 values: `-1`, `0`, `1` |
| `issuer_fitch_rating_lt` |  | text |  | 23 values: `500`, `530`, `550`, `560`, `570`, `580`, `590`, `600`, `610`, `620`, `630`, `640`, `650`, `660`, `670`, `680`, `690`, `700`, `710`, `720`, `730`, `740`, `750` |
| `issuer_fitch_rating_st` |  | text |  | 8 values: `500`, `540`, `570`, `610`, `660`, `680`, `700`, `730` |
| `issuer_moodys_outlook_lt` |  | text |  | 3 values: `-1`, `0`, `1` |
| `issuer_moodys_rating_lt` |  | text |  | 22 values: `500`, `550`, `560`, `570`, `580`, `590`, `600`, `610`, `620`, `630`, `640`, `650`, `660`, `670`, `680`, `690`, `700`, `710`, `720`, `730`, `740`, `750` |
| `issuer_moodys_rating_st` |  | text |  | 5 values: `500`, `630`, `660`, `680`, `730` |
| `issuer_snp_rating_lt` |  | text |  | 23 values: `500`, `530`, `540`, `560`, `570`, `580`, `590`, `600`, `610`, `620`, `630`, `640`, `650`, `660`, `670`, `680`, `690`, `700`, `710`, `720`, `730`, `740`, `750` |
| `issuer_snp_rating_st` |  | text |  | 7 values: `500`, `570`, `610`, `660`, `680`, `700`, `730` |
| `kind` |  | text |  | 1 values: `rt` |
| `kind-delay` |  | number |  |  |
| `last-price-update-time` |  | time |  |  |
| `last-price-update-time-intraday` |  | time |  |  |
| `last_bar_update_time` |  | number |  |  |
| `logoid` |  | text |  |  |
| `macaulay_duration` |  | number |  |  |
| `make_whole_call_end_date` |  | time |  |  |
| `make_whole_call_option` |  | text |  | 2 values: `callable`, `non-callable` |
| `make_whole_call_spread` |  | number |  |  |
| `make_whole_call_start_date` |  | time |  |  |
| `market` |  | text |  | 1 values: `bond` |
| `market_cap_to_tvl` |  | number |  |  |
| `maturity-date` |  | number |  |  |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `maturity_type` |  | text |  | 3 values: `extendible`, `perpetual`, `regular` |
| `measure` |  | text |  | 2 values: `price`, `unit` |
| `minmov` |  | number |  |  |
| `minmove2` |  | number |  |  |
| `minute-bar.close` |  | price |  |  |
| `minute-bar.time` |  | number |  |  |
| `modified_duration` |  | number |  |  |
| `name` |  | text |  |  |
| `nominal_value` |  | fundamental_price |  |  |
| `non_gaap_price_to_earnings_per_share_forecast_next_fy` |  | number |  |  |
| `nvt` |  | number |  |  |
| `offer_date` |  | time |  |  |
| `offer_price_pct` |  | percent |  |  |
| `offer_type` |  | text |  | 2 values: `global`, `single-country` |
| `open_interest_to_volume_24h` |  | number |  |  |
| `original_maturity` |  | number |  |  |
| `outstanding_amount` |  | fundamental_price |  |  |
| `ownership_form` |  | text |  | 6 values: `bearer`, `bearer-depository-receipt`, `bearer-registered`, `new-global-note`, `registered`, `registered-depository-receipt` |
| `placement_type` |  | text |  | 2 values: `private`, `public` |
| `pledge_status` |  | text |  | 6 values: `first-mortgage`, `secured`, `secured-1st-lien`, `secured-2nd-lien`, `secured-collateral-only`, `unsecured` |
| `poison_put_option` |  | text |  | 2 values: `non-putable`, `putable` |
| `popularity_rank` |  | number |  |  |
| `post_change` |  | percent |  |  |
| `pre_change` |  | percent |  |  |
| `pre_change_abs` |  | price |  |  |
| `premature_redemption` |  | text |  | 2 values: `non-redeemable`, `redeemable` |
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
| `principal_redemption_type` |  | text |  | 3 values: `at-maturity`, `perpetual`, `sinkable` |
| `provider-id` |  | text |  | 2 values: `ice`, `sixgroup` |
| `put_frequency` |  | text |  | 8 values: `annual`, `continuously`, `discrete`, `every-coupon`, `monthly`, `on-effective-pmt-date`, `quarterly`, `semi-annual` |
| `put_next_date` |  | time |  |  |
| `put_next_price` |  | percent |  |  |
| `put_option` |  | text |  |  |
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
| `redemption_type` |  | text |  | 4 values: `callable`, `callable-and-putable`, `none`, `putable` |
| `redemptions_h` |  | interface |  |  |
| `region` |  | text |  | 310 values: `AA`, `AB`, `AC`, `AD`, `AE`, `AG`, `AI`, `AJ`, `AK`, `AL`, `AM`, `AN`, `AR`, `AS`, `AT`, `AU`, `AV`, `AZ`, `BA`, `BB`, `BC`, `BD`, `BE`, `BF`, `BG` … |
| `relative_volume` |  | number |  |  |
| `revenue_surprise_percent_fq` |  | percent |  |  |
| `rtc` |  | price |  |  |
| `seniority_level` |  | text |  | 11 values: `debt-senior-preferred`, `junior`, `junior-preferred`, `junior-subordinate`, `not-disclosed`, `not-relevant`, `senior`, `senior-non-preferred`, `senior-preferred`, `senior-subordinate`, `subordinate` |
| `shrhldrs_equity_to_total_assets_fq` |  | number |  |  |
| `shrhldrs_equity_to_total_assets_fy` |  | number |  |  |
| `sinking_fund` |  | text |  | 2 values: `non-sinkable`, `sinkable` |
| `social_responsibility` |  | text |  | 3 values: `green-bond`, `social-bond`, `sustainable-bond` |
| `source-logoid` |  | text |  | 51 values: `source/ASX`, `source/ATHEX`, `source/BET`, `source/BSESOF`, `source/BVB`, `source/BX`, `source/CHIXAU`, `source/DSEBD`, `source/DUS`, `source/EGX`, `source/EURONEXT`, `source/EUROTLX`, `source/FINRA`, `source/FWB`, `source/GETTEX`, `source/GPW`, `source/HAM`, `source/HAN`, `source/HKEX`, `source/JSE`, `source/LJSE`, `source/LS`, `source/LSE`, `source/LSX`, `source/LUXSE` … |
| `subsessions` |  | interface |  |  |
| `subtype` |  | text |  | 2 values: `corporate`, `government` |
| `term-to-maturity` |  | text |  |  |
| `time` |  | time |  |  |
| `total_debt_to_ebitda_fq` |  | number |  |  |
| `total_debt_to_ebitda_fy` |  | number |  |  |
| `total_to_max_supply_ratio` |  | percent |  |  |
| `typespecs` |  | set |  | 3 values: `corporate`, `government`, `sharia` |
| `update-time` |  | number |  |  |
| `update_mode` |  | text |  | 1 values: `streaming` |
| `update_time` |  | time |  |  |
| `use_of_proceeds` |  | set |  | 44 values: `asset-financing`, `bank-debt-retirement-refinance`, `bankruptcy-reorganization-fees-expenses`, `capital-expenditures`, `commercial-paper-support`, `construction`, `debt-issuance`, `dividend-distribution`, `equity-issuance`, `expansion`, `export-import-finance`, `fee-expense-payment`, `finance-tender-offer-s`, `for-own-account`, `fund-eligible-receivables`, `fund-intercompany-loans`, `fund-the-closing-date-distribution`, `fund-the-interest-reserve-account`, `general-corporate-purposes`, `general-government-purposes`, `investment-in-marketable-securities`, `lease-financing`, `mergers-acquisitions`, `not-available`, `notes-redemption-refinance` … |
| `value-unit-id` |  | text |  | 1 values: `PCTPAR` |
| `velocity` |  | number |  |  |
| `volume_change` |  | percent |  |  |
| `volume_change_abs` |  | number |  |  |
| `years_to_maturity` |  | number |  |  |
| `yield_to_call` |  | percent |  |  |
| `yield_to_maturity` |  | percent |  |  |
| `yield_to_put` |  | percent |  |  |
| `yield_to_worst` |  | percent |  |  |
| `ytm_to_ask` |  | number |  |  |
| `ytm_to_bid` |  | number |  |  |
| `ytw_to_ask` |  | number |  |  |
| `ytw_to_bid` |  | number |  |  |
| `z_spread` |  | number |  |  |
