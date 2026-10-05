"""
FundamentalAgent — fundamental data for a stock.

Primary source: yfinance Ticker.info (always available).
When INDMoney MCP reconnects it can be plugged in as an enrichment layer.

Task types:
  GET_FUNDAMENTALS  payload: {exchange, symbol}
"""
import json
from datetime import datetime, timezone

import yfinance as yf

from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.logger import logger


_FUND_TTL = 60 * 60 * 24   # 24 hours — fundamentals change slowly


def _yf_symbol(exchange: str, symbol: str) -> str:
    if exchange.upper() == "BSE":
        return f"{symbol.upper()}.BO"
    return f"{symbol.upper()}.NS"


def _fund_cache_key(exchange: str, symbol: str) -> str:
    return f"fundamentals:{exchange.lower()}:{symbol.lower()}"


def _safe_float(val) -> float | None:
    try:
        v = float(val)
        return round(v, 4) if v is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


class FundamentalAgent:
    agent_id = "fundamental_agent"
    task_types = ["GET_FUNDAMENTALS"]

    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "GET_FUNDAMENTALS":
            return self._get_fundamentals(task)
        return self._failure(task, "UNKNOWN_TASK", f"Unknown task: {task.task_type}")

    def _get_fundamentals(self, task: AgentTask) -> AgentResult:
        payload = task.payload or {}
        exchange = payload.get("exchange", "NSE")
        symbol = payload.get("symbol", "")

        if not symbol:
            return self._failure(task, "VALIDATION_ERROR", "Symbol is required")

        cache_key = _fund_cache_key(exchange, symbol)
        cached = cache_get(cache_key)
        if cached:
            try:
                return self._success(task, json.loads(cached))
            except Exception:
                pass

        yf_sym = _yf_symbol(exchange, symbol)
        try:
            info = yf.Ticker(yf_sym).info
        except Exception as e:
            logger.warning("FundamentalAgent: yfinance fetch failed", symbol=yf_sym, error=str(e))
            return self._failure(task, "FETCH_FAILED", f"Could not fetch fundamentals for {yf_sym}: {e}")

        if not info or not info.get("longName"):
            return self._failure(task, "DATA_UNAVAILABLE", f"No fundamental data for {yf_sym}")

        data = {
            "symbol": symbol,
            "exchange": exchange,
            "company_name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "description": (info.get("longBusinessSummary") or "")[:500] or None,
            "employees": _safe_int(info.get("fullTimeEmployees")),
            "website": info.get("website"),
            # Valuation
            "market_cap": _safe_int(info.get("marketCap")),
            "trailing_pe": _safe_float(info.get("trailingPE")),
            "forward_pe": _safe_float(info.get("forwardPE")),
            "price_to_book": _safe_float(info.get("priceToBook")),
            "price_to_sales": _safe_float(info.get("priceToSalesTrailing12Months")),
            "ev_to_ebitda": _safe_float(info.get("enterpriseToEbitda")),
            # Per-share
            "trailing_eps": _safe_float(info.get("trailingEps")),
            "forward_eps": _safe_float(info.get("forwardEps")),
            "book_value": _safe_float(info.get("bookValue")),
            "dividend_yield": _safe_float(info.get("dividendYield")),
            "dividend_rate": _safe_float(info.get("dividendRate")),
            # Growth & profitability
            "revenue_growth": _safe_float(info.get("revenueGrowth")),
            "earnings_growth": _safe_float(info.get("earningsGrowth")),
            "profit_margin": _safe_float(info.get("profitMargins")),
            "operating_margin": _safe_float(info.get("operatingMargins")),
            "return_on_equity": _safe_float(info.get("returnOnEquity")),
            "return_on_assets": _safe_float(info.get("returnOnAssets")),
            # Balance sheet ratios
            "debt_to_equity": _safe_float(info.get("debtToEquity")),
            "current_ratio": _safe_float(info.get("currentRatio")),
            "quick_ratio": _safe_float(info.get("quickRatio")),
            # Price stats
            "beta": _safe_float(info.get("beta")),
            "week52_high": _safe_float(info.get("fiftyTwoWeekHigh")),
            "week52_low": _safe_float(info.get("fiftyTwoWeekLow")),
            "avg_volume": _safe_int(info.get("averageVolume")),
            # Source
            "source": "yfinance",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            cache_set(cache_key, json.dumps(data), ttl_seconds=_FUND_TTL)
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


fundamental_agent = FundamentalAgent()
