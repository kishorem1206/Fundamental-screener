import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.technical.services.classification_service import classification_service, StockRow
from app.technical.data.market_data import get_ohlcv
from app.technical.indicators.plugins.rsi_momentum import rsi_momentum_plugin
from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.technical.shared.utils import today_date, now_iso
from app.logger import logger

_CACHE_TTL = 60 * 60 * 4  # 4 hours

_TREND_LABELS = {1.0: "RISING", 0.0: "FLAT", -1.0: "FALLING"}

_SIGNAL_PRIORITY = {
    "FRESH_BREAKOUT":    5,
    "APPROACHING_AGAIN": 4.5,
    "APPROACHING":       4,
    "ALREADY_STRONG":    3,
    "EXTENDED":          2,
    "NEUTRAL":           1,
}


def _cache_key(exchange: str, symbol: str, lookback: int, threshold: float) -> str:
    # v3 — trend changed to today-vs-yesterday RSI (was 3-period); invalidates v2
    return f"rsi_mom:v3:{exchange.lower()}:{symbol.lower()}:{lookback}:{threshold:.0f}:{today_date()}"


def _fetch_one(stock: StockRow, lookback: int, threshold: float) -> dict | None:
    key = _cache_key(stock.exchange, stock.symbol, lookback, threshold)
    cached = cache_get(key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    try:
        bars = get_ohlcv(stock.exchange, stock.symbol, "1D")
        if not bars:
            return None
        result = rsi_momentum_plugin.calculate(bars, {
            "period": 14,
            "lookback_days": lookback,
            "threshold": threshold,
        })
        if result.signal == "UNKNOWN":
            return None

        v = result.values
        data = {
            "id": stock.id,
            "symbol": stock.symbol,
            "exchange": stock.exchange,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "macro_sector": stock.macro_sector,
            "market_cap_category": stock.market_cap_category,
            "rsi_today": v["rsi_today"],
            "rsi_prev": v["rsi_prev"],
            "rsi_change": v["rsi_change"],
            "distance_to_60": v["distance_to_60"],
            "rsi_trend": _TREND_LABELS.get(v["rsi_trend"], "FLAT"),
            "above_60_in_20d": v["above_60_in_20d"] == 1.0,
            "days_since_above_60": None if v["days_since_above_60"] >= 999.0 else int(v["days_since_above_60"]),
            "signal": result.signal,
            "signal_rank": v["signal_rank"],
        }
        cache_set(key, json.dumps(data), ttl_seconds=_CACHE_TTL)
        return data
    except Exception as e:
        logger.debug("RSI momentum fetch failed", symbol=stock.symbol, error=str(e))
        return None


class RSIMomentumService:
    def scan(
        self,
        universe: str,
        lookback_days: int = 20,
        threshold: float = 60.0,
        signals: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        start = time.time()
        stocks = classification_service.get_universe_stocks(universe, limit=2000)

        if not stocks:
            return {
                "executed_at": now_iso(),
                "universe": universe,
                "total_matched": 0,
                "stocks_screened": 0,
                "execution_time_ms": 0.0,
                "stocks": [],
            }

        logger.info("RSI momentum scan", universe=universe, candidates=len(stocks))

        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(_fetch_one, s, lookback_days, threshold): s for s in stocks}
            for fut in as_completed(futures):
                try:
                    data = fut.result(timeout=60)
                    if data:
                        results.append(data)
                except Exception:
                    pass

        # Apply signal filter
        if signals:
            sig_set = {s.upper() for s in signals}
            results = [r for r in results if r["signal"] in sig_set]

        # Sort: signal priority desc, then distance to threshold asc (closer = more interesting)
        results.sort(key=lambda r: (
            -_SIGNAL_PRIORITY.get(r["signal"], 0),
            r["distance_to_60"] if r["distance_to_60"] is not None else 999.0,
        ))

        total = len(results)
        page = results[offset: offset + limit]

        return {
            "executed_at": now_iso(),
            "universe": universe,
            "total_matched": total,
            "stocks_screened": len(stocks),
            "execution_time_ms": round((time.time() - start) * 1000, 1),
            "stocks": page,
        }


rsi_momentum_service = RSIMomentumService()
