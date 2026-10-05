# backend/app/tradingview_screener/screeners.py — Beginner Explanation

**Source file:** `backend/app/tradingview_screener/screeners.py`

Part of the vendored copy of the open-source TradingView-Screener library (v3.2.2, MIT licence — see `LICENSE` in the same folder). It was copied in so the app owns the code and can change it; imports were rewritten from `tradingview_screener.*` to `app.tradingview_screener.*`.

Premade `Query` factories for each market type (e.g. `stocks('india')`, `crypto()`, `options('NASDAQ:AAPL')`) with sensible default columns/filters.

Used by `app/services/tv_screener_service.py`.
