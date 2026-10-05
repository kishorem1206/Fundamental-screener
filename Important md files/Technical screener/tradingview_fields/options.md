# Options fields

Options contracts (market: `options`).

Source: <https://shner-elmo.github.io/TradingView-Screener/fields/options.html>

**80 fields** (80 counting timeframe variants).
Use as `Query().select("<field>")` / `col("<field>")`. A `Timeframes` entry means the field also accepts `field|<tf>` (e.g. `RSI|60`).

| Field | Name | Type | Timeframes | Allowed values |
|---|---|---|---|---|
| `type` | Symbol Type | text |  | 1 values: `option` |
| `is_primary` | Primary Listing | bool |  |  |
| `active_symbol` | Current trading day | bool |  |  |
| `change` | Change % | percent |  |  |
| `change_abs` | Change | price |  |  |
| `close` | Price | price |  |  |
| `volume` | Volume | number |  |  |
| `Perf.All` | All Time Performance | number |  |  |
| `change_from_open` | Change from Open % | percent |  |  |
| `change_from_open_abs` | Change from Open | price |  |  |
| `exchange` | Exchange | text |  | 14 values: `ASX`, `BIST`, `BSE`, `CBOT`, `CBOT_MINI`, `CME`, `CME_MINI`, `COMEX`, `EUREX`, `MCX`, `NSE`, `NYMEX`, `OPRA`, `TFEX` |
| `gap` | Gap % | percent |  |  |
| `high` | High | price |  |  |
| `low` | Low | price |  |  |
| `open` | Open | price |  |  |
| `postmarket_change` | Post-market Change % | percent |  |  |
| `postmarket_change_abs` | Post-market Change | price |  |  |
| `premarket_change` | Pre-market Change % | percent |  |  |
| `premarket_change_abs` | Pre-market Change | price |  |  |
| `premarket_change_from_open` | Pre-market Change from Open % | percent |  |  |
| `premarket_change_from_open_abs` | Pre-market Change from Open | number |  |  |
| `premarket_gap` | Pre-market Gap % | percent |  |  |
| `submarket` | Submarket | text |  | 1 values: `` |
| `currency` | Quote currency | text |  | 12 values: `AUD`, `CAD`, `CHF`, `EUR`, `GBP`, `INR`, `JPY`, `NZD`, `THB`, `TRY`, `USD`, `USX` |
| `ask` | Ask | price |  |  |
| `bid` | Bid | price |  |  |
| `bars_count` |  | number |  |  |
| `base_currency_kind` |  | text |  | 1 values: `fiat` |
| `bid_ask_spread_pct` |  | percent |  |  |
| `coupon` |  | number |  |  |
| `cryptoasset-info.description` |  | text |  |  |
| `cryptoasset-info.id` |  | text |  |  |
| `currency_id` |  | text |  | 12 values: `AUD`, `CAD`, `CHF`, `EUR`, `GBP`, `INR`, `JPY`, `NZD`, `THB`, `TRY`, `USD`, `XTVUSX` |
| `currency_kind` |  | text |  | 1 values: `fiat` |
| `current_yield` |  | percent |  |  |
| `days_to_maturity` |  | number |  |  |
| `description` |  | text |  |  |
| `enterprise_value_ebit_fwd` |  | number |  |  |
| `enterprise_value_ebitda_fwd` |  | number |  |  |
| `enterprise_value_sales_fwd` |  | number |  |  |
| `expiration` |  | time |  |  |
| `fractional` |  | text |  | 2 values: `false`, `true` |
| `gap_down` |  | percent |  |  |
| `gap_down_abs` |  | price |  |  |
| `gap_up` |  | percent |  |  |
| `gap_up_abs` |  | price |  |  |
| `indexes` |  | interface |  |  |
| `indicators_bars_count` |  | number |  |  |
| `is_blacklisted` |  | bool |  |  |
| `is_shariah_compliant` |  | bool |  |  |
| `is_symbol_primary_listing` |  | bool |  |  |
| `kind` |  | text |  | 2 values: `delay`, `rt` |
| `kind-delay` |  | number |  |  |
| `last-price-update-time` |  | time |  |  |
| `last-price-update-time-intraday` |  | time |  |  |
| `last_bar_update_time` |  | number |  |  |
| `logoid` |  | text |  |  |
| `market` |  | text |  | 1 values: `options` |
| `maturity_date` |  | time-yyyymmdd |  |  |
| `minmov` |  | number |  |  |
| `minmove2` |  | number |  |  |
| `name` |  | text |  |  |
| `option-type` |  | text |  | 2 values: `call`, `put` |
| `post_change` |  | percent |  |  |
| `pre_change` |  | percent |  |  |
| `pre_change_abs` |  | price |  |  |
| `price_book_fwd` |  | number |  |  |
| `price_earnings_fwd` |  | number |  |  |
| `price_sales_fwd` |  | number |  |  |
| `pricescale` |  | number |  |  |
| `source-logoid` |  | text |  | 14 values: `source/ASX`, `source/BIST`, `source/BSE`, `source/CBOT`, `source/CBOT_MINI`, `source/CME`, `source/CME_MINI`, `source/COMEX`, `source/EUREX`, `source/MCX`, `source/NSE`, `source/NYMEX`, `source/OPRA`, `source/TFEX` |
| `strike` |  | price |  |  |
| `subtype` |  | text |  | 2 values: ``, `euoption` |
| `time` |  | time |  |  |
| `typespecs` |  | set |  | 2 values: ``, `euoption` |
| `update-time` |  | number |  |  |
| `update_mode` |  | text |  | 1 values: `streaming` |
| `update_time` |  | time |  |  |
| `volume_change` |  | percent |  |  |
| `volume_change_abs` |  | number |  |  |
