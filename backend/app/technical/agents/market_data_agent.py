"""
MarketDataAgent — live quotes and OHLCV via yfinance.

Task types:
  GET_QUOTE   payload: {exchange, symbol}
              returns: {price, change, change_pct, volume, open, high, low,
                        prev_close, week52_high, week52_low, market_cap, timestamp}
"""
import json
from datetime import datetime, timezone

import yfinance as yf

from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.logger import logger


_QUOTE_TTL = 60 * 5   # 5 minutes


def _yf_symbol(exchange: str, symbol: str) -> str:
    exchange = exchange.upper()
    if exchange == "NSE":
        return f"{symbol.upper()}.NS"
    if exchange == "BSE":
        return f"{symbol.upper()}.BO"
    return symbol.upper()


def _quote_cache_key(exchange: str, symbol: str) -> str:
    return f"quote:{exchange.lower()}:{symbol.lower()}"


class MarketDataAgent:
    agent_id = "market_data_agent"
    task_types = ["GET_QUOTE"]

    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "GET_QUOTE":
            return self._get_quote(task)
        return self._failure(task, "UNKNOWN_TASK", f"Unknown task: {task.task_type}")

    def _get_quote(self, task: AgentTask) -> AgentResult:
        payload = task.payload or {}
        exchange = payload.get("exchange", "NSE")
        symbol = payload.get("symbol", "")

        if not symbol:
            return self._failure(task, "VALIDATION_ERROR", "Symbol is required")

        cache_key = _quote_cache_key(exchange, symbol)
        cached = cache_get(cache_key)
        if cached:
            try:
                return self._success(task, json.loads(cached))
            except Exception:
                pass

        yf_sym = _yf_symbol(exchange, symbol)
        try:
            ticker = yf.Ticker(yf_sym)
            info = ticker.fast_info
            hist = ticker.history(period="5d", interval="1d", auto_adjust=True)
        except Exception as e:
            logger.warning("MarketDataAgent: fetch failed", symbol=yf_sym, error=str(e))
            return self._failure(task, "FETCH_FAILED", f"Could not fetch quote for {yf_sym}: {e}")

        try:
            price = float(info.last_price) if info.last_price else None
            # fast_info.last_price often returns None for NSE/BSE — fall back to last bar close
            if price is None and not hist.empty:
                price = round(float(hist["Close"].iloc[-1]), 2)
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None
            change = round(price - prev_close, 2) if price and prev_close else None
            change_pct = round((change / prev_close) * 100, 2) if change and prev_close else None

            data = {
                "symbol": symbol,
                "exchange": exchange,
                "yf_symbol": yf_sym,
                "price": round(price, 2) if price else None,
                "change": change,
                "change_pct": change_pct,
                "volume": int(info.last_volume) if info.last_volume else None,
                "open": round(float(hist["Open"].iloc[-1]), 2) if not hist.empty else None,
                "high": round(float(hist["High"].iloc[-1]), 2) if not hist.empty else None,
                "low": round(float(hist["Low"].iloc[-1]), 2) if not hist.empty else None,
                "prev_close": round(prev_close, 2) if prev_close else None,
                "week52_high": round(float(info.year_high), 2) if info.year_high else None,
                "week52_low": round(float(info.year_low), 2) if info.year_low else None,
                "market_cap": int(info.market_cap) if info.market_cap else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.warning("MarketDataAgent: parse failed", symbol=yf_sym, error=str(e))
            return self._failure(task, "PARSE_FAILED", f"Could not parse quote data: {e}")

        try:
            cache_set(cache_key, json.dumps(data), ttl_seconds=_QUOTE_TTL)
        except Exception:
            pass

        return self._success(task, data)

    def _success(self, task: AgentTask, data) -> AgentResult:
        return AgentResult(task_id=task.task_id, correlation_id=task.correlation_id,
                           agent=self.agent_id, status="SUCCESS", data=data)

    def _failure(self, task: AgentTask, code: str, message: str) -> AgentResult:
        return AgentResult(task_id=task.task_id, correlation_id=task.correlation_id,
                           agent=self.agent_id, status="FAILED", data=None,
                           errors=[AgentError(code=code, message=message)])


market_data_agent = MarketDataAgent()
