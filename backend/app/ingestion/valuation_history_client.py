"""Historical P/E and P/B ingestion — Architecture v2 Stage 4.

Combines three independent things, per-field, taking whichever source
actually has data for a given fiscal year rather than picking one source
and accepting its gaps:
  - EPS per year: Screener.in's profit_loss() (~11 years, consolidated —
    switched from standalone 2026-09-15, same user directive/reasoning as
    pnl_history_client.py's module docstring: matches what yfinance already
    reports for Indian tickers, and what a conglomerate's real EPS is)
    first, yfinance's annual income statement (app/data/yfinance_client.py,
    ~4-5 years for Indian stocks — confirmed shallow by direct probe,
    already consolidated by default) filling whatever years Screener
    didn't have.
  - Book value per share per year: derived from Screener's balance_sheet()
    (equity_capital + reserves, scaled by face_value to get a per-share
    figure without needing historical shares-outstanding), also now
    consolidated, first, yfinance's total_equity / CURRENT shares_outstanding
    as a filler (same "current share count as an approximation" caveat
    engine.py's implied_pe_series() already accepts elsewhere in this
    codebase).
  - Price at each fiscal year-end: yfinance's monthly close price history
    (confirmed 10y+ available), matched to the nearest month on/before each
    period_end.

This is a genuinely different, more expensive computation than engine.py's
implied_pe_series() (CURRENT price / historical EPS, a cheap proxy) — here
the price is the REAL historical price at the time.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import yfinance as yf
from sqlalchemy.orm import Session

from app.calculations.engine import MetricsCalculator
from app.data.yfinance_client import fetch_financial_data
from app.infrastructure.database.models import ValuationHistory
from app.logger import logger

_MONTH_ABBR = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def _screener_period_end(year_label: str) -> str | None:
    """"Mar 2026" -> "2026-03-31". Screener's own month-end convention."""
    try:
        dt = datetime.strptime(year_label.strip(), "%b %Y")
    except ValueError:
        return None
    import calendar
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return date(dt.year, dt.month, last_day).isoformat()


def _fy_period_end(fy_label: str) -> str | None:
    """"FY2026" -> "2026-03-31" (Indian fiscal year, March year-end —
    matches the convention every other ingestion path in this codebase
    already uses, e.g. annual_report_ingestion.py)."""
    try:
        year = int(fy_label.replace("FY", "").strip())
    except ValueError:
        return None
    return date(year, 3, 31).isoformat()


def _screener_annual(symbol: str) -> dict[str, dict]:
    """{period_end: {"eps": ..., "bvps": ...}} from Screener.in, consolidated.
    Never raises — returns {} on any failure (openscreener not installed,
    network error, symbol not found), matching every other ingestion path's
    graceful-degradation contract."""
    try:
        from openscreener import Stock
    except ImportError:
        return {}

    try:
        stock = Stock(symbol, consolidated=True)
        profit_loss = stock.profit_loss()
        balance_sheet = stock.balance_sheet()
        summary = stock.summary()
    except Exception as e:
        logger.warning("valuation_history_client: screener fetch failed", symbol=symbol, error=str(e))
        return {}

    face_value = None
    ratios = summary.get("ratios") if isinstance(summary, dict) else None
    if isinstance(ratios, dict):
        face_value = ratios.get("face_value")

    bal_by_period = {}
    for row in balance_sheet:
        period_end = _screener_period_end(str(row.get("year", "")))
        if not period_end:
            continue
        equity_capital, reserves = row.get("equity_capital"), row.get("reserves")
        if equity_capital and reserves is not None and face_value:
            # BVPS = (equity_capital + reserves) / equity_capital * face_value —
            # avoids needing historical shares-outstanding: equity_capital / face_value
            # IS shares outstanding for that year, so this simplifies cleanly.
            bal_by_period[period_end] = round((equity_capital + reserves) / equity_capital * face_value, 4)

    result: dict[str, dict] = {}
    for row in profit_loss:
        year_label = str(row.get("year", ""))
        if year_label.upper() == "TTM":
            continue
        period_end = _screener_period_end(year_label)
        eps = row.get("eps")
        if not period_end:
            continue
        result.setdefault(period_end, {})
        if eps is not None:
            result[period_end]["eps"] = float(eps)
        if period_end in bal_by_period:
            result[period_end]["bvps"] = bal_by_period[period_end]
    return result


def _yfinance_annual(exchange: str, symbol: str) -> dict[str, dict]:
    """{period_end: {"eps": ..., "bvps": ...}} from yfinance's annual
    statements — shallower than Screener (~4-5 years for Indian stocks,
    confirmed by direct probe), used only to fill gaps Screener left."""
    try:
        financial_data = fetch_financial_data(exchange, symbol)
        calc = MetricsCalculator(financial_data)
    except Exception as e:
        logger.warning("valuation_history_client: yfinance fetch failed", symbol=symbol, error=str(e))
        return {}

    shares = calc._mkt("shares_outstanding")
    eps_series = calc._income_series("diluted_eps")
    equity_series = calc._bal_series("total_equity")

    result: dict[str, dict] = {}
    for fy_label, eps in eps_series.items():
        period_end = _fy_period_end(fy_label)
        if not period_end:
            continue
        result.setdefault(period_end, {})
        if eps is not None:
            result[period_end]["eps"] = float(eps)
        equity = equity_series.get(fy_label)
        if equity is not None and shares:
            result[period_end]["bvps"] = round(equity / shares, 4)
    return result


def _monthly_prices(exchange: str, symbol: str) -> list[tuple[str, float]]:
    """[(date_iso, close), ...] ascending, from yfinance monthly history.
    Never raises — returns [] on failure."""
    suffix = ".BO" if exchange.upper() == "BSE" else ".NS"
    try:
        ticker = yf.Ticker(f"{symbol}{suffix}")
        hist = ticker.history(period="max", interval="1mo")
    except Exception as e:
        logger.warning("valuation_history_client: price history fetch failed", symbol=symbol, error=str(e))
        return []
    if hist is None or hist.empty:
        return []
    return [(idx.date().isoformat(), float(row["Close"])) for idx, row in hist.iterrows() if row["Close"]]


def _nearest_price(prices: list[tuple[str, float]], target: str) -> tuple[str, float] | None:
    """Closest available monthly price on or before `target`; falls back to
    the closest one after if nothing on/before exists (early listing years)."""
    on_or_before = [p for p in prices if p[0] <= target]
    if on_or_before:
        return max(on_or_before, key=lambda p: p[0])
    after = [p for p in prices if p[0] > target]
    return min(after, key=lambda p: p[0]) if after else None


def ingest_valuation_history(db: Session, company_id: str, symbol: str, exchange: str = "NSE") -> dict:
    """Fetch, merge (per-field, best-available-source), and store historical
    P/E and P/B for every fiscal year either Screener or yfinance can supply
    EPS for. Never raises — logs and returns zero counts on total failure."""
    screener_data = _screener_annual(symbol)
    yfinance_data = _yfinance_annual(exchange, symbol)
    prices = _monthly_prices(exchange, symbol)

    periods = set(screener_data) | set(yfinance_data)
    now = datetime.now(timezone.utc)
    stored = 0

    for period_end in periods:
        s, y = screener_data.get(period_end, {}), yfinance_data.get(period_end, {})

        eps, eps_source = (s.get("eps"), "SCREENER") if s.get("eps") is not None else (y.get("eps"), "YFINANCE")
        bvps, bvps_source = (s.get("bvps"), "SCREENER") if s.get("bvps") is not None else (y.get("bvps"), "YFINANCE")
        if eps is None and bvps is None:
            continue

        price_match = _nearest_price(prices, period_end)
        price_date, price = price_match if price_match else (None, None)

        pe = round(price / eps, 2) if price and eps and eps > 0 else None
        pb = round(price / bvps, 2) if price and bvps and bvps > 0 else None

        existing = db.query(ValuationHistory).filter_by(company_id=company_id, period_end=period_end).first()
        fields = dict(
            eps=eps, eps_source=eps_source if eps is not None else None,
            price=price, price_date=price_date, pe=pe,
            book_value_per_share=bvps, bvps_source=bvps_source if bvps is not None else None,
            pb=pb, retrieved_at=now,
        )
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
        else:
            db.add(ValuationHistory(id=str(uuid.uuid4()), company_id=company_id, period_end=period_end, **fields))
        stored += 1

    logger.info("valuation_history_client: ingested", symbol=symbol, periods_stored=stored,
                screener_years=len(screener_data), yfinance_years=len(yfinance_data), price_points=len(prices))
    return {"periods_stored": stored, "screener_years": len(screener_data), "yfinance_years": len(yfinance_data)}
