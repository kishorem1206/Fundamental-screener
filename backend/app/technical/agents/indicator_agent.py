import dataclasses
import json
from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.shared.errors import DataUnavailableError
from app.technical.indicators.engine import indicator_engine
from app.technical.indicators.registry import indicator_registry
from app.technical.data.market_data import get_ohlcv
from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.technical.shared.utils import today_date
from app.logger import logger


_DEFAULT_INDICATORS = ["rsi", "bollinger"]
_CACHE_TTL = 60 * 60 * 4  # 4 hours


def _cache_key(exchange: str, symbol: str, timeframe: str, indicators: list[str]) -> str:
    ind_str = ",".join(sorted(indicators))
    return f"indicators:{exchange.lower()}:{symbol.lower()}:{timeframe.lower()}:{ind_str}:{today_date()}"


class IndicatorAgent:
    agent_id = "indicator_agent"
    task_types = ["GET_INDICATORS"]

    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "GET_INDICATORS":
            return self._get_indicators(task)
        return self._failure(task, "UNKNOWN_TASK", f"Unknown task type: {task.task_type}")

    def _get_indicators(self, task: AgentTask) -> AgentResult:
        payload = task.payload or {}
        exchange = payload.get("exchange", "NSE")
        symbol = payload.get("symbol", "")
        timeframe = payload.get("timeframe", "1D")
        raw_indicators: str = payload.get("indicators", "rsi,bollinger")
        indicator_names = [i.strip().lower() for i in raw_indicators.split(",") if i.strip()]

        if not symbol:
            return self._failure(task, "VALIDATION_ERROR", "Symbol is required")

        # Validate requested indicators early
        unsupported = [n for n in indicator_names if n not in indicator_registry.list_available()]
        if unsupported:
            return self._failure(task, "UNSUPPORTED_INDICATOR", f"Unknown indicators: {unsupported}. Supported: {indicator_registry.list_available()}")

        # Redis cache check
        cache_key = _cache_key(exchange, symbol, timeframe, indicator_names)
        cached = cache_get(cache_key)
        if cached:
            try:
                return self._success(task, json.loads(cached))
            except Exception:
                pass

        try:
            bars = get_ohlcv(exchange, symbol, timeframe)
        except DataUnavailableError as e:
            return self._failure(task, "DATA_UNAVAILABLE", str(e))
        except Exception as e:
            logger.error("IndicatorAgent: OHLCV fetch failed", exchange=exchange, symbol=symbol, error=str(e))
            return self._failure(task, "FETCH_FAILED", str(e))

        if not bars:
            return self._failure(task, "DATA_UNAVAILABLE", f"No OHLCV data for {exchange}:{symbol}")

        data_range = f"{bars[0].date} to {bars[-1].date}"

        try:
            snapshot = indicator_engine.calculate(
                bars=bars,
                indicator_names=indicator_names,
                symbol=symbol,
                exchange=exchange,
                timeframe=timeframe,
                source="yfinance",
                data_range=data_range,
            )
        except Exception as e:
            logger.error("IndicatorAgent: calculation failed", error=str(e))
            return self._failure(task, "CALCULATION_FAILED", str(e))

        # Serialize to dict (provenance items are dataclasses)
        snapshot_dict = dataclasses.asdict(snapshot)

        # Cache result
        try:
            cache_set(cache_key, json.dumps(snapshot_dict), ttl_seconds=_CACHE_TTL)
        except Exception:
            pass

        return self._success(task, snapshot_dict)

    def _success(self, task: AgentTask, data) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="SUCCESS",
            data=data,
        )

    def _failure(self, task: AgentTask, code: str, message: str) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            agent=self.agent_id,
            status="FAILED",
            data=None,
            errors=[AgentError(code=code, message=message)],
        )


indicator_agent = IndicatorAgent()
