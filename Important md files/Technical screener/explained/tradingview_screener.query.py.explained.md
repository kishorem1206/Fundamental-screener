# backend/app/tradingview_screener/query.py — Beginner Explanation

**Source file:** `backend/app/tradingview_screener/query.py`

Part of the vendored copy of the open-source TradingView-Screener library (v3.2.2, MIT licence — see `LICENSE` in the same folder). It was copied in so the app owns the code and can change it; imports were rewritten from `tradingview_screener.*` to `app.tradingview_screener.*`.

The `Query` builder: `select`, `where` / `where2` (AND/OR trees), `order_by`, `limit`, `offset`, `set_markets`, `set_tickers`, `set_index`, `set_property`, `copy`, and `get_scanner_data()` which POSTs to scanner.tradingview.com and returns `(total_count, DataFrame)`. Also holds the default stock filters and HTTP headers.

Used by `app/services/tv_screener_service.py`.
