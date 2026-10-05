# backend/app/tradingview_screener/models.py — Beginner Explanation

**Source file:** `backend/app/tradingview_screener/models.py`

Part of the vendored copy of the open-source TradingView-Screener library (v3.2.2, MIT licence — see `LICENSE` in the same folder). It was copied in so the app owns the code and can change it; imports were rewritten from `tradingview_screener.*` to `app.tradingview_screener.*`.

TypedDict definitions for the JSON the scanner API sends and receives (filters, sort, range, result shapes). Types only — no logic.

Used by `app/services/tv_screener_service.py`.
