"""
ExplanationAgent — explains why a stock passed or failed a screen.

Rule-based (no LLM). Generates human-readable reasons for each filter condition.
The LLM-enhanced version comes in Phase 6.

Task type: EXPLAIN_RESULT
Payload:
  {
    stock: {symbol, company_name, sector, market_cap_category, ...},
    filters: <raw filter dict — same as ScreenDSL.filters>,
    indicators: {"rsi_1D": {"value": 35.4, "signal": "NEUTRAL"}, ...}
  }
"""
from __future__ import annotations
from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.screening.dsl import (
    parse_filter_expr, FilterExpr,
    ClassificationFilter, IndicatorFilter, AndGroup, OrGroup,
)
from app.logger import logger


# ── Human-readable templates ───────────────────────────────────────────────────

_OP_LABEL = {"lt": "below", "lte": "at or below", "gt": "above", "gte": "at or above",
             "eq": "equal to", "neq": "not equal to"}

_RSI_CONTEXT = {
    "lt_30":  "deeply oversold — strong selling has pushed price to potential reversal zone",
    "lt_40":  "oversold territory — momentum is weak and a bounce may be forming",
    "lt_50":  "below midpoint — bears have the short-term edge",
    "gt_70":  "overbought — strong buying pressure, watch for pullback",
    "gt_60":  "above midpoint — bulls have the short-term edge",
    "gt_50":  "just above neutral — mild bullish momentum",
    "default": "in neutral territory",
}

_BB_PB_CONTEXT = {
    "lt_0.2":  "price is hugging the lower Bollinger Band — near statistical support",
    "lt_0.35": "price is in the lower quarter of the Bollinger range",
    "gt_0.8":  "price is hugging the upper Bollinger Band — near statistical resistance",
    "gt_0.65": "price is in the upper quarter of the Bollinger range",
    "default": "price is mid-range within the Bollinger Bands",
}


def _rsi_context(op: str, value: float, actual: float | None) -> str:
    if actual is None:
        return ""
    if op in ("lt", "lte"):
        if actual < 30:
            return _RSI_CONTEXT["lt_30"]
        if actual < 40:
            return _RSI_CONTEXT["lt_40"]
        return _RSI_CONTEXT["lt_50"]
    if op in ("gt", "gte"):
        if actual > 70:
            return _RSI_CONTEXT["gt_70"]
        if actual > 60:
            return _RSI_CONTEXT["gt_60"]
        return _RSI_CONTEXT["gt_50"]
    return _RSI_CONTEXT["default"]


def _pb_context(op: str, value: float, actual: float | None) -> str:
    if actual is None:
        return ""
    if op in ("lt", "lte"):
        if actual < 0.2:
            return _BB_PB_CONTEXT["lt_0.2"]
        return _BB_PB_CONTEXT["lt_0.35"]
    if op in ("gt", "gte"):
        if actual > 0.8:
            return _BB_PB_CONTEXT["gt_0.8"]
        return _BB_PB_CONTEXT["gt_0.65"]
    return _BB_PB_CONTEXT["default"]


def _explain_indicator(f: IndicatorFilter, indicators: dict) -> dict:
    key = f"{f.indicator.lower()}_{f.timeframe.upper()}"
    ind_data = indicators.get(key, {})
    actual = ind_data.get(f.field)
    passed = actual is not None and _compare(actual, f.op, f.value)

    op_label = _OP_LABEL.get(f.op, f.op)
    ind_name = f.indicator.upper() if f.indicator == "rsi" else "Bollinger %B"
    if f.indicator == "bollinger" and f.field != "percent_b":
        ind_name = f"Bollinger {f.field.replace('_', ' ').title()}"

    actual_str = f"{actual:.2f}" if actual is not None else "N/A"
    status = "passed" if passed else ("failed" if actual is not None else "skipped — data unavailable")

    if f.indicator == "rsi":
        context = _rsi_context(f.op, f.value, actual)
    elif f.indicator == "bollinger" and f.field == "percent_b":
        context = _pb_context(f.op, f.value, actual)
    else:
        context = ""

    message = (
        f"{ind_name} ({f.timeframe}) is {actual_str}, "
        f"which is {op_label} the threshold of {f.value}"
        + (f" — {context}" if context else "")
    )

    return {"type": "indicator", "indicator": f.indicator, "field": f.field,
            "timeframe": f.timeframe, "threshold": f.value, "actual": actual,
            "status": status, "message": message}


def _explain_classification(f: ClassificationFilter, stock: dict) -> dict:
    actual = stock.get(f.field)
    passed = actual is not None and _compare(actual, f.op, f.value)
    op_label = _OP_LABEL.get(f.op, f.op)
    message = (
        f"{f.field.replace('_', ' ').title()} is '{actual}'"
        + (f", which matches '{f.value}'" if passed else f", does not match '{f.value}'")
    )
    return {"type": "classification", "field": f.field, "threshold": f.value,
            "actual": actual, "status": "passed" if passed else "failed", "message": message}


def _compare(actual, op: str, expected) -> bool:
    try:
        match op:
            case "lt":  return actual < expected
            case "lte": return actual <= expected
            case "gt":  return actual > expected
            case "gte": return actual >= expected
            case "eq":  return actual == expected
            case "neq": return actual != expected
            case "in":  return actual in expected
            case "nin": return actual not in expected
    except Exception:
        pass
    return False


def _walk(expr: FilterExpr, stock: dict, indicators: dict, reasons: list, depth: int = 0):
    prefix = "AND" if depth % 2 == 0 else "OR"
    if isinstance(expr, AndGroup):
        for child in expr.children:
            _walk(child, stock, indicators, reasons, depth + 1)
    elif isinstance(expr, OrGroup):
        for child in expr.children:
            _walk(child, stock, indicators, reasons, depth + 1)
    elif isinstance(expr, IndicatorFilter):
        reasons.append(_explain_indicator(expr, indicators))
    elif isinstance(expr, ClassificationFilter):
        reasons.append(_explain_classification(expr, stock))


class ExplanationAgent:
    agent_id = "explanation_agent"
    task_types = ["EXPLAIN_RESULT"]

    def handle(self, task: AgentTask) -> AgentResult:
        if task.task_type == "EXPLAIN_RESULT":
            return self._explain(task)
        return self._failure(task, "UNKNOWN_TASK", f"Unknown task: {task.task_type}")

    def _explain(self, task: AgentTask) -> AgentResult:
        payload = task.payload or {}
        stock = payload.get("stock", {})
        raw_filters = payload.get("filters")
        indicators = payload.get("indicators", {})

        if not stock:
            return self._failure(task, "VALIDATION_ERROR", "stock is required")

        try:
            expr = parse_filter_expr(raw_filters)
        except Exception as e:
            return self._failure(task, "VALIDATION_ERROR", f"Invalid filters: {e}")

        reasons: list[dict] = []
        if expr is not None:
            _walk(expr, stock, indicators, reasons)

        passed_count = sum(1 for r in reasons if r["status"] == "passed")
        failed_count = sum(1 for r in reasons if r["status"] == "failed")
        skipped_count = sum(1 for r in reasons if r["status"].startswith("skipped"))

        symbol = stock.get("symbol", "this stock")
        company = stock.get("company_name", symbol)

        if failed_count > 0:
            summary = f"{company} ({symbol}) did not pass all filter criteria — {failed_count} condition(s) failed."
        elif skipped_count > 0:
            summary = f"{company} ({symbol}) passed {passed_count} condition(s), but {skipped_count} could not be evaluated (data unavailable)."
        elif reasons:
            summary = f"{company} ({symbol}) passed all {passed_count} filter condition(s)."
        else:
            summary = f"{company} ({symbol}) — no filters to evaluate (all stocks pass)."

        data = {
            "symbol": symbol,
            "company_name": company,
            "summary": summary,
            "passed": failed_count == 0 and skipped_count == 0,
            "reasons": reasons,
            "stats": {"passed": passed_count, "failed": failed_count, "skipped": skipped_count},
        }

        return self._success(task, data)

    def _success(self, task: AgentTask, data) -> AgentResult:
        return AgentResult(task_id=task.task_id, correlation_id=task.correlation_id,
                           agent=self.agent_id, status="SUCCESS", data=data)

    def _failure(self, task: AgentTask, code: str, message: str) -> AgentResult:
        return AgentResult(task_id=task.task_id, correlation_id=task.correlation_id,
                           agent=self.agent_id, status="FAILED", data=None,
                           errors=[AgentError(code=code, message=message)])


explanation_agent = ExplanationAgent()
