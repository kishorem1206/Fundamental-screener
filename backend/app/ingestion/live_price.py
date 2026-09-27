"""Current-price snapshot, fetched fresh at the moment it's needed (analysis
run, or report generation later) rather than reused from Stage 2's financial
data collection, which can be hours old by the time a PDF is (re)generated.

Uses yfinance's `fast_info` — a single lightweight quote call, not the full
`.info`/statements fetch `fetch_financial_data` already does — so calling
this again at report-generation time is cheap.

Dhan and Kite MCP servers were evaluated as live-price sources (2026-09-13)
but aren't usable from backend code: their OAuth sessions are scoped to the
Claude Code MCP client that authenticated them, not exposed as a reusable
API key/token this FastAPI process could call directly. Yahoo Finance
remains the only currently-wired live-price path; swapping in a real Dhan/
Kite REST integration would need separate API credentials configured for
this backend specifically.

Never raises — logs and returns None on failure, matching every other
ingestion path's contract."""
from __future__ import annotations

from datetime import datetime, timezone

from app.logger import logger

SOURCE = "YAHOO_FINANCE"


def fetch_live_price(symbol: str, exchange: str = "NSE") -> dict | None:
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("live_price: yfinance not installed")
        return None

    suffix = ".NS" if exchange == "NSE" else ".BO"
    try:
        t = yf.Ticker(f"{symbol}{suffix}")
        fi = t.fast_info
        price = fi.get("lastPrice")
        prev_close = fi.get("previousClose")
    except Exception as e:
        logger.warning("live_price: fetch failed", symbol=symbol, error=str(e))
        return None

    if price is None:
        return None

    change_pct = None
    if prev_close:
        try:
            change_pct = round((float(price) - float(prev_close)) / float(prev_close) * 100, 2)
        except (TypeError, ValueError, ZeroDivisionError):
            change_pct = None

    return {
        "price": float(price),
        "previous_close": float(prev_close) if prev_close is not None else None,
        "change_pct": change_pct,
        "day_high": fi.get("dayHigh"),
        "day_low": fi.get("dayLow"),
        "currency": fi.get("currency") or "INR",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE,
    }
