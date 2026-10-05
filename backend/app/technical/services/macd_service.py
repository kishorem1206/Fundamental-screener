"""
MACD Scan Service

Scans a stock universe using the MACD engine. Architecture mirrors
rsi_divergence_service: threaded fetch, Redis cache per stock per config per day.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.technical.macd.engine import analyze_macd, compute_macd_series
from app.technical.services.classification_service import classification_service, StockRow
from app.technical.data.market_data import get_ohlcv
from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.technical.shared.utils import today_date, now_iso
from app.logger import logger

_CACHE_TTL = 60 * 60 * 4  # 4 hours

_VALID_SOURCES  = {"Close", "Open", "High", "Low", "HL2", "HLC3", "OHLC4"}
_VALID_MA_TYPES = {"EMA", "SMA"}
_VALID_TFS      = {"1H", "4H", "1D", "1W"}

# All valid histogram filter keys
HIST_FILTER_KEYS = {
    "STRONG_BULLISH", "BULLISH_FADING",
    "STRONG_BEARISH", "BEARISH_FADING",
    "POSITIVE", "NEGATIVE",
}

# All valid crossover filter keys
CROSS_FILTER_KEYS = {
    "BULLISH", "BEARISH",
    "BULLISH_BELOW_ZERO", "BULLISH_ABOVE_ZERO",
    "BEARISH_ABOVE_ZERO", "BEARISH_BELOW_ZERO",
}


def _cache_key(
    exchange: str, symbol: str,
    source: str, fast: int, slow: int, signal: int,
    osc_ma: str, sig_ma: str, tf: str,
) -> str:
    return (
        f"macd_scan:v2:{exchange.lower()}:{symbol.lower()}"
        f":{source.lower()}:f{fast}:s{slow}:sg{signal}"
        f":{osc_ma.lower()}:{sig_ma.lower()}:{tf.lower()}:{today_date()}"
    )


def _fetch_one(
    stock: StockRow,
    source: str,
    fast: int, slow: int, signal: int,
    osc_ma: str, sig_ma: str,
    tf: str,
    crossover_lookback: int,
) -> dict | None:
    key    = _cache_key(stock.exchange, stock.symbol, source, fast, slow, signal, osc_ma, sig_ma, tf)
    cached = cache_get(key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    try:
        bars = get_ohlcv(stock.exchange, stock.symbol, tf)
        if not bars:
            return None

        # Strip trailing bars where close is NaN — yfinance sometimes returns a stub
        # row for the current day (market holiday or pre-open) with only volume filled.
        import math
        while bars and math.isnan(bars[-1].close):
            bars = bars[:-1]
        if not bars:
            return None

        analysis = analyze_macd(
            bars, source=source,
            fast=fast, slow=slow, signal=signal,
            osc_ma=osc_ma, sig_ma=sig_ma,
            crossover_lookback=crossover_lookback,
        )
        if analysis is None:
            return None

        row = {
            "id":                    stock.id,
            "symbol":                stock.symbol,
            "exchange":              stock.exchange,
            "company_name":          stock.company_name,
            "sector":                stock.sector,
            "macro_sector":          stock.macro_sector,
            "market_cap_category":   stock.market_cap_category,
            "close_price":           round(bars[-1].close, 2),
            "macd":                  analysis.macd,
            "signal_line":           analysis.signal_line,
            "histogram":             analysis.histogram,
            "histogram_prev":        analysis.histogram_prev,
            "histogram_direction":   analysis.histogram_direction,
            "histogram_state":       analysis.histogram_state,
            "zero_line_status":      analysis.zero_line_status,
            "crossover":             analysis.crossover,
            "crossover_location":    analysis.crossover_location,
            "last_crossover_type":   analysis.last_crossover_type,
            "last_crossover_bars_ago": analysis.last_crossover_bars_ago,
            "macd_state":            analysis.macd_state,
        }
        cache_set(key, json.dumps(row), ttl_seconds=_CACHE_TTL)
        return row

    except Exception as e:
        logger.debug("MACD fetch failed", symbol=stock.symbol, error=str(e))
        return None


def _passes_hist_filter(row: dict, hist_filters: list[str]) -> bool:
    if not hist_filters:
        return True
    state = row["histogram_state"]
    hist  = row["histogram"]
    for f in hist_filters:
        if f == "POSITIVE" and hist > 0:      return True
        if f == "NEGATIVE" and hist < 0:      return True
        if f == state:                         return True
    return False


def _passes_cross_filter(row: dict, cross_filters: list[str], cross_bars: int) -> bool:
    if not cross_filters:
        return True
    last_type = row["last_crossover_type"]
    last_bars = row["last_crossover_bars_ago"]
    if last_type is None or last_bars is None or last_bars > cross_bars:
        return False
    for f in cross_filters:
        # Exact match (e.g., BULLISH_BELOW_ZERO)
        if f == last_type:
            return True
        # Generic direction match (BULLISH / BEARISH)
        if f == "BULLISH" and last_type.startswith("BULLISH"):
            return True
        if f == "BEARISH" and last_type.startswith("BEARISH"):
            return True
    return False


class MACDService:
    def scan(
        self,
        universe: str = "NIFTY_500",
        source: str = "Close",
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        osc_ma: str = "EMA",
        sig_ma: str = "EMA",
        timeframe: str = "1D",
        hist_filters: list[str] | None = None,
        cross_filters: list[str] | None = None,
        cross_bars: int = 5,
        crossover_lookback: int = 20,
        limit: int = 300,
        offset: int = 0,
    ) -> dict:
        start = time.time()
        hist_filters  = [f for f in (hist_filters  or []) if f in HIST_FILTER_KEYS]
        cross_filters = [f for f in (cross_filters or []) if f in CROSS_FILTER_KEYS]

        stocks = classification_service.get_universe_stocks(universe, limit=2000)
        if not stocks:
            return _empty(universe, now_iso())

        logger.info("MACD scan", universe=universe, candidates=len(stocks),
                    source=source, fast=fast, slow=slow, signal=signal,
                    osc_ma=osc_ma, sig_ma=sig_ma, tf=timeframe)

        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                pool.submit(
                    _fetch_one, s, source, fast, slow, signal, osc_ma, sig_ma,
                    timeframe.upper(), crossover_lookback,
                ): s
                for s in stocks
            }
            for fut in as_completed(futures):
                try:
                    row = fut.result(timeout=60)
                    if row:
                        results.append(row)
                except Exception:
                    pass

        # Apply filters
        filtered = [
            r for r in results
            if _passes_hist_filter(r, hist_filters)
            and _passes_cross_filter(r, cross_filters, cross_bars)
        ]

        # Sort: crossovers first, then by |histogram| descending
        filtered.sort(key=lambda r: (
            0 if r["crossover"] != "NONE" else 1,
            -abs(r["histogram"]),
        ))

        total = len(filtered)
        page  = filtered[offset: offset + limit]

        return {
            "executed_at":       now_iso(),
            "universe":          universe,
            "total_matched":     total,
            "stocks_screened":   len(stocks),
            "execution_time_ms": round((time.time() - start) * 1000, 1),
            "results":           page,
        }

    def get_chart_data(
        self,
        exchange: str,
        symbol: str,
        source: str = "Close",
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        osc_ma: str = "EMA",
        sig_ma: str = "EMA",
        timeframe: str = "1D",
        num_bars: int = 80,
    ) -> dict | None:
        try:
            bars   = get_ohlcv(exchange, symbol, timeframe.upper())
            series = compute_macd_series(bars, source, fast, slow, signal, osc_ma, sig_ma, num_bars)
            if series is None:
                return None
            return {
                "symbol":    symbol,
                "exchange":  exchange,
                "timeframe": timeframe,
                "bars": [
                    {
                        "date":            b.date,
                        "close":           b.close,
                        "macd":            b.macd,
                        "signal":          b.signal,
                        "histogram":       b.histogram,
                        "histogram_state": b.histogram_state,
                    }
                    for b in series.bars
                ],
            }
        except Exception as e:
            logger.debug("MACD chart failed", symbol=symbol, error=str(e))
            return None


def _empty(universe: str, ts: str) -> dict:
    return {
        "executed_at": ts, "universe": universe,
        "total_matched": 0, "stocks_screened": 0,
        "execution_time_ms": 0.0, "results": [],
    }


macd_service = MACDService()
