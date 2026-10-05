# backend/app/tradingview_screener/util.py — Beginner Explanation

**Source file:** `backend/app/tradingview_screener/util.py`

Part of the vendored copy of the open-source TradingView-Screener library (v3.2.2, MIT licence — see `LICENSE` in the same folder). It was copied in so the app owns the code and can change it; imports were rewritten from `tradingview_screener.*` to `app.tradingview_screener.*`.

Small helper `format_technical_rating` converting the numeric Recommend.* rating into Strong Buy / Buy / Neutral / Sell / Strong Sell.

Used by `app/services/tv_screener_service.py`.
