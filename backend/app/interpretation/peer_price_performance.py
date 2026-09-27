"""Rebased peer price performance — Premium PDF System, Stage B4. Fetches
1Y daily close history via yfinance for the subject company + its peers
(same `.NS`/`.BO` suffix convention already used in
valuation_history_client.py's `_monthly_prices`), rebases every series to
100 at its own first available point in the window, so performance is
comparable independent of each stock's absolute price level — the doc's
own example: "Company A -> 122, Company B -> 96".

Computed live at request/render time, never stored — same choice as
live_price.py's module docstring: a price series this recent goes stale
immediately, so there's nothing worth caching beyond the request.
"""
from __future__ import annotations

import yfinance as yf

from app.logger import logger


def _daily_closes(symbol: str, exchange: str, period: str) -> list[tuple[str, float]]:
    """[(date_iso, close), ...] ascending. Never raises — returns [] on failure."""
    suffix = ".BO" if (exchange or "NSE").upper() == "BSE" else ".NS"
    try:
        ticker = yf.Ticker(f"{symbol}{suffix}")
        hist = ticker.history(period=period, interval="1d")
    except Exception as e:
        logger.warning("peer_price_performance: history fetch failed", symbol=symbol, error=str(e))
        return []
    if hist is None or hist.empty:
        return []
    return [(idx.date().isoformat(), float(row["Close"])) for idx, row in hist.iterrows() if row["Close"]]


def _rebase(prices: list[tuple[str, float]]) -> list[dict]:
    if not prices:
        return []
    base = prices[0][1]
    if not base:
        return []
    return [{"date": d, "value": round(c / base * 100, 2)} for d, c in prices]


def compute_rebased_performance(
    subject: dict, peers: list[dict], period: str = "1y",
) -> dict:
    """`subject`/each peer: {"name": str, "symbol": str, "exchange": str}.
    Never raises — a company whose history can't be fetched is simply
    omitted from `series`, not a fatal error for the whole chart."""
    series = []
    for company in [subject, *peers]:
        symbol = company.get("symbol")
        if not symbol:
            continue
        prices = _daily_closes(symbol, company.get("exchange") or "NSE", period)
        points = _rebase(prices)
        if points:
            series.append({
                "name": company.get("name") or symbol, "symbol": symbol,
                "is_subject": company is subject, "points": points,
            })

    logger.info("peer_price_performance: computed", subject=subject.get("symbol"),
                peers_requested=len(peers), series_returned=len(series))
    return {"period": period, "series": series}
