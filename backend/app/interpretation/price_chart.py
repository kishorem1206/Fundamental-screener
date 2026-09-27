"""1-year and 5-year price history — yfinance, no login/broker dependency
(2026-09-15: TradingView Desktop wouldn't stay running long enough for CDP
to connect, Dhan MCP's historical-data tool needs a fresh broker login;
user confirmed yfinance is fine). Computed live at render time, same
"don't store what changes every day" choice as `live_price.py` and
`peer_price_performance.py` (which this mirrors almost exactly, just for
one company's absolute price instead of several rebased-to-100).
"""
from __future__ import annotations

import yfinance as yf

from app.logger import logger


def _closes(symbol: str, exchange: str, period: str, interval: str) -> list[dict]:
    """[{"date": iso, "close": float}, ...] ascending. Never raises —
    returns [] on failure."""
    suffix = ".BO" if (exchange or "NSE").upper() == "BSE" else ".NS"
    try:
        ticker = yf.Ticker(f"{symbol}{suffix}")
        hist = ticker.history(period=period, interval=interval)
    except Exception as e:
        logger.warning("price_chart: history fetch failed", symbol=symbol, period=period, error=str(e))
        return []
    if hist is None or hist.empty:
        return []
    return [{"date": idx.date().isoformat(), "close": float(row["Close"])} for idx, row in hist.iterrows() if row["Close"]]


def build_price_charts(symbol: str, exchange: str) -> dict:
    """{"1y": [...daily...], "5y": [...weekly...]}. Weekly for the 5Y
    window keeps point count reasonable (~260 vs ~1,825 daily) without
    needing a separate downsample pass."""
    if not symbol:
        return {"1y": [], "5y": []}
    return {
        "1y": _closes(symbol, exchange, "1y", "1d"),
        "5y": _closes(symbol, exchange, "5y", "1wk"),
    }
