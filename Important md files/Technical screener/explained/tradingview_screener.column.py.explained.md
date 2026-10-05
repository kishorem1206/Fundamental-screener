# backend/app/tradingview_screener/column.py — Beginner Explanation

**Source file:** `backend/app/tradingview_screener/column.py`

Part of the vendored copy of the open-source TradingView-Screener library (v3.2.2, MIT licence — see `LICENSE` in the same folder). It was copied in so the app owns the code and can change it; imports were rewritten from `tradingview_screener.*` to `app.tradingview_screener.*`.

Defines `Column`, which turns Python operators and methods into TradingView filter dictionaries: `>`, `>=`, `==`, `crosses_above`, `between`, `isin`, `has`, `above_pct`, `in_day_range`, `empty`, `like`, etc. Comparing two columns (`col('close') >= col('DonchCh20.Upper')`) is supported.

Used by `app/services/tv_screener_service.py`.
