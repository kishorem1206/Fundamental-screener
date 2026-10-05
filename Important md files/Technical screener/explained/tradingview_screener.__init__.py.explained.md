# backend/app/tradingview_screener/__init__.py — Beginner Explanation

**Source file:** `backend/app/tradingview_screener/__init__.py`

Part of the vendored copy of the open-source TradingView-Screener library (v3.2.2, MIT licence — see `LICENSE` in the same folder). It was copied in so the app owns the code and can change it; imports were rewritten from `tradingview_screener.*` to `app.tradingview_screener.*`.

Re-exports the public API: `Query`, `Column`/`col`, `And`/`Or` and the premade screener builders (stocks, crypto, coin, forex, futures, bond, cfd, options, crypto_dex).

Used by `app/services/tv_screener_service.py`.
