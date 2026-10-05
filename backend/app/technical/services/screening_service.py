import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.technical.screening.dsl import (
    ScreenDSL, parse_filter_expr, extract_indicator_needs,
    ClassificationFilter, AndGroup, OrGroup, FilterExpr,
)
from app.technical.screening.filter_engine import filter_engine
from app.technical.screening.ranking import rank_results
from app.technical.services.classification_service import classification_service, StockRow
from app.technical.data.market_data import get_ohlcv
from app.technical.indicators.engine import indicator_engine
from app.technical.scoring.engine import ScoreCriterion, score_stock
from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.technical.shared.utils import today_date, now_iso
from app.logger import logger


_IND_CACHE_TTL = 60 * 60 * 4  # 4 hours


def _ind_cache_key(exchange: str, symbol: str, indicator: str, tf: str) -> str:
    # v3 — rsi_momentum trend changed to today-vs-yesterday; invalidates v2
    return f"screen_ind:v3:{exchange.lower()}:{symbol.lower()}:{indicator.lower()}:{tf.lower()}:{today_date()}"


def _pre_pass_classification(stock: StockRow, expr: FilterExpr | None) -> bool:
    """Quick classification-only pre-filter. Returns False only if provably FAIL."""
    if expr is None:
        return True
    if isinstance(expr, ClassificationFilter):
        return filter_engine._eval_classification(expr, stock) != "FAIL"
    if isinstance(expr, AndGroup):
        return all(_pre_pass_classification(stock, c) for c in expr.children
                   if isinstance(c, (ClassificationFilter, AndGroup, OrGroup)))
    if isinstance(expr, OrGroup):
        cls_children = [c for c in expr.children
                        if isinstance(c, (ClassificationFilter, AndGroup, OrGroup))]
        if not cls_children:
            return True  # all children are IndicatorFilters; can't prove it fails
        return any(_pre_pass_classification(stock, c) for c in cls_children)
    return True  # IndicatorFilter — don't pre-filter on it


def _fetch_indicator_for_stock(
    stock: StockRow, indicator: str, timeframe: str
) -> dict | None:
    cache_key = _ind_cache_key(stock.exchange, stock.symbol, indicator, timeframe)
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    try:
        bars = get_ohlcv(stock.exchange, stock.symbol, timeframe)
        if not bars:
            return None
        data_range = f"{bars[0].date} to {bars[-1].date}"
        snapshot = indicator_engine.calculate(
            bars=bars,
            indicator_names=[indicator],
            symbol=stock.symbol,
            exchange=stock.exchange,
            timeframe=timeframe,
            source="yfinance",
            data_range=data_range,
        )
        result = snapshot.indicators.get(indicator)
        if result:
            cache_set(cache_key, json.dumps(result), ttl_seconds=_IND_CACHE_TTL)
        return result
    except Exception as e:
        logger.debug("Indicator fetch failed", symbol=stock.symbol, indicator=indicator, error=str(e))
        return None


class ScreeningService:
    def run(self, dsl: ScreenDSL) -> dict:
        start = time.time()

        # 1. Parse the filter expression
        expr = parse_filter_expr(dsl.filters)
        indicator_needs = extract_indicator_needs(expr)  # set of (indicator, timeframe)

        # 2. Get all stocks from universe (up to 500)
        stocks = classification_service.get_universe_stocks(dsl.universe, limit=2000)
        if not stocks:
            return {
                "executed_at": now_iso(),
                "universe": dsl.universe,
                "total_matched": 0,
                "stocks_screened": 0,
                "execution_time_ms": round((time.time() - start) * 1000, 1),
                "stocks": [],
            }

        # 3. Pre-filter on cheap classification conditions to reduce indicator fetches
        if expr is not None:
            stocks = [s for s in stocks if _pre_pass_classification(s, expr)]

        logger.info("Screening", universe=dsl.universe, candidates=len(stocks), indicators=len(indicator_needs))

        # Merge display-only indicators into the fetch set (not used in filter)
        fetch_needs = set(indicator_needs)
        if dsl.extra_indicators:
            for spec in dsl.extra_indicators:
                fetch_needs.add((spec.indicator, spec.timeframe.upper()))

        # 4. Fetch indicators in parallel (5 workers to avoid yfinance rate limits)
        indicators_by_stock: dict[str, dict] = {}
        if fetch_needs:
            def fetch_all_for_stock(stock: StockRow):
                result = {}
                for (ind, tf) in fetch_needs:
                    data = _fetch_indicator_for_stock(stock, ind, tf)
                    if data is not None:
                        result[f"{ind.lower()}_{tf.upper()}"] = data
                return stock.id, result

            with ThreadPoolExecutor(max_workers=5) as pool:
                futures = {pool.submit(fetch_all_for_stock, s): s for s in stocks}
                for fut in as_completed(futures):
                    try:
                        stock_id, data = fut.result(timeout=60)
                        indicators_by_stock[stock_id] = data
                    except Exception:
                        pass

        # 5. Full filter evaluation and build result list
        score_criteria: list[ScoreCriterion] | None = None
        if dsl.score_by:
            score_criteria = [
                ScoreCriterion(
                    indicator=c.indicator,
                    field=c.field,
                    timeframe=c.timeframe,
                    weight=c.weight,
                    direction=c.direction,
                    range_min=c.range_min,
                    range_max=c.range_max,
                )
                for c in dsl.score_by
            ]

        matched: list[dict] = []
        for stock in stocks:
            ind_data = indicators_by_stock.get(stock.id, {})
            verdict = filter_engine.evaluate(expr, stock, ind_data)
            if verdict == "PASS":
                entry: dict = {
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "exchange": stock.exchange,
                    "company_name": stock.company_name,
                    "sector": stock.sector,
                    "macro_sector": stock.macro_sector,
                    "market_cap_category": stock.market_cap_category,
                    "indicators": ind_data,
                }
                if score_criteria is not None:
                    sr = score_stock(ind_data, score_criteria)
                    entry["score"] = sr.score
                    entry["score_completeness"] = sr.completeness
                matched.append(entry)

        # 6. Rank if requested
        if dsl.rank_by and matched:
            matched = rank_results(matched, dsl.rank_by)

        # 7. Paginate
        total = len(matched)
        page = matched[dsl.offset: dsl.offset + dsl.limit]

        return {
            "executed_at": now_iso(),
            "universe": dsl.universe,
            "total_matched": total,
            "stocks_screened": len(stocks),
            "execution_time_ms": round((time.time() - start) * 1000, 1),
            "stocks": page,
        }


screening_service = ScreeningService()
