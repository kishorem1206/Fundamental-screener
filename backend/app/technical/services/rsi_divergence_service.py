"""
RSI Divergence Scan Service

Scans a universe of stocks for recent RSI divergences.
Pattern: same as rsi_momentum_service — threaded fetch + Redis cache per stock.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

from app.technical.services.classification_service import classification_service, StockRow
from app.technical.data.market_data import get_ohlcv
from app.technical.divergence.engine import (
    DivergenceConfig,
    DivergenceType,
    detect_rsi_divergence,
    get_current_rsi,
)
from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.technical.shared.utils import today_date, now_iso
from app.logger import logger

_CACHE_TTL = 60 * 60 * 4  # 4 hours — same cadence as RSI momentum


def _cache_key(
    exchange: str,
    symbol: str,
    pl: int, pr: int,
    recency: int,
    min_bars: int,
    max_bars: int,
    max_pivot_rsi: float | None,
    min_pivot_rsi: float | None,
    div_types_key: str,
    timeframe: str,
) -> str:
    maxr = f"{max_pivot_rsi:.0f}" if max_pivot_rsi is not None else "X"
    minr = f"{min_pivot_rsi:.0f}" if min_pivot_rsi is not None else "X"
    return (
        f"rsi_div:v8:{exchange.lower()}:{symbol.lower()}"
        f":pl{pl}:pr{pr}:r{recency}:nb{min_bars}:mb{max_bars}:mr{maxr}:nr{minr}:{div_types_key}:{timeframe}:{today_date()}"
    )


def _fetch_one(
    stock: StockRow,
    cfg: DivergenceConfig,
    div_types: list[DivergenceType],
    timeframe: str,
) -> list[dict] | None:
    """Fetch OHLCV bars for one stock and run divergence detection. Returns list of raw dicts."""
    dt_key = "-".join(sorted(div_types))
    key = _cache_key(
        stock.exchange, stock.symbol,
        cfg.pivot_left, cfg.pivot_right,
        cfg.max_recency_bars,
        cfg.min_bars_between_pivots, cfg.max_bars_between_pivots,
        cfg.max_pivot_rsi, cfg.min_pivot_rsi, dt_key, timeframe,
    )
    cached = cache_get(key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    try:
        import math
        bars = get_ohlcv(stock.exchange, stock.symbol, timeframe)
        if not bars:
            return None

        while bars and math.isnan(bars[-1].close):
            bars = bars[:-1]
        if not bars:
            return None

        hits = detect_rsi_divergence(bars, cfg=cfg, div_types=div_types)

        # Current RSI values for the "RSI rising today" filter
        rsi_pair  = get_current_rsi(bars, period=cfg.rsi_period)
        rsi_today = round(rsi_pair[0], 2) if rsi_pair else None
        rsi_prev  = round(rsi_pair[1], 2) if rsi_pair else None

        if not hits:
            result: list[dict] = []
            cache_set(key, json.dumps(result), ttl_seconds=_CACHE_TTL)
            return result

        rows: list[dict] = []
        for h in hits:
            rows.append({
                "id":             stock.id,
                "symbol":         stock.symbol,
                "exchange":       stock.exchange,
                "company_name":   stock.company_name,
                "sector":         stock.sector,
                "macro_sector":   stock.macro_sector,
                "market_cap_category": stock.market_cap_category,
                "div_type":       h.div_type,
                "status":         h.status,
                "pivot1_date":    h.pivot1.date,
                "pivot2_date":    h.pivot2.date,
                "pivot1_price":   round(h.pivot1.price, 2),
                "pivot2_price":   round(h.pivot2.price, 2),
                "pivot1_rsi":     h.pivot1.rsi,
                "pivot2_rsi":     h.pivot2.rsi,
                "price_chg_pct":  h.price_chg_pct,
                "rsi_change":     h.rsi_change,
                "bars_between":   h.bars_between,
                "divergence_age": h.divergence_age,
                "strength_score": h.strength_score,
                "rsi_today":      rsi_today,
                "rsi_prev":       rsi_prev,
            })

        cache_set(key, json.dumps(rows), ttl_seconds=_CACHE_TTL)
        return rows

    except Exception as e:
        logger.debug("RSI divergence fetch failed", symbol=stock.symbol, error=str(e))
        return None


class RSIDivergenceService:
    def scan(
        self,
        universe: str = "NIFTY_500",
        timeframe: str = "1D",
        pivot_left: int = 3,
        pivot_right: int = 3,
        max_recency_bars: int = 10,
        min_bars_between: int = 5,
        max_bars_between: int = 50,
        min_rsi_change: float = 1.0,
        min_price_chg_pct: float = 0.1,
        max_pivot_rsi: float | None = 40.0,
        min_pivot_rsi: float | None = None,
        require_rsi_rising: bool = False,
        div_types: list[DivergenceType] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        start = time.time()
        if div_types is None:
            div_types = ["REGULAR_BULLISH"]

        stocks = classification_service.get_universe_stocks(universe, limit=2000)
        if not stocks:
            return {
                "executed_at": now_iso(),
                "universe": universe,
                "total_matched": 0,
                "stocks_screened": 0,
                "execution_time_ms": 0.0,
                "divergences": [],
            }

        logger.info("RSI divergence scan", universe=universe, candidates=len(stocks), div_types=div_types)

        cfg = DivergenceConfig(
            pivot_left=pivot_left,
            pivot_right=pivot_right,
            max_recency_bars=max_recency_bars,
            min_bars_between_pivots=min_bars_between,
            max_bars_between_pivots=max_bars_between,
            min_rsi_change=min_rsi_change,
            min_price_chg_pct=min_price_chg_pct,
            max_pivot_rsi=max_pivot_rsi,
            min_pivot_rsi=min_pivot_rsi,
        )

        all_divs: list[dict] = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(_fetch_one, s, cfg, div_types, timeframe): s for s in stocks}
            for fut in as_completed(futures):
                try:
                    rows = fut.result(timeout=60)
                    if rows:
                        all_divs.extend(rows)
                except Exception:
                    pass

        # Optional post-filter: only keep stocks where today's RSI > yesterday's RSI
        if require_rsi_rising:
            all_divs = [
                d for d in all_divs
                if d.get("rsi_today") is not None
                and d.get("rsi_prev") is not None
                and d["rsi_today"] > d["rsi_prev"]
            ]

        # Sort: most recent first, then highest strength
        all_divs.sort(key=lambda r: (r["divergence_age"], -r["strength_score"]))

        total = len(all_divs)
        page  = all_divs[offset: offset + limit]

        return {
            "executed_at":     now_iso(),
            "universe":        universe,
            "total_matched":   total,
            "stocks_screened": len(stocks),
            "execution_time_ms": round((time.time() - start) * 1000, 1),
            "divergences":     page,
        }


rsi_divergence_service = RSIDivergenceService()
