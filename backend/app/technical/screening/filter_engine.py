from app.technical.screening.dsl import (
    ClassificationFilter, IndicatorFilter, AndGroup, OrGroup, FilterExpr
)
from app.technical.services.classification_service import StockRow


def _compare(actual, op: str, expected) -> bool:
    match op:
        case "lt":  return actual is not None and actual < expected
        case "lte": return actual is not None and actual <= expected
        case "gt":  return actual is not None and actual > expected
        case "gte": return actual is not None and actual >= expected
        case "eq":  return actual == expected
        case "neq": return actual != expected
        case "in":  return actual in expected
        case "nin": return actual not in expected
    return False


class FilterEngine:
    def evaluate(
        self,
        expr: FilterExpr | None,
        stock: StockRow,
        indicators: dict[str, dict],  # {"rsi_1d": {value, signal, ...}, "bollinger_1d": {...}}
    ) -> str:  # "PASS" | "FAIL" | "SKIP"
        if expr is None:
            return "PASS"

        if isinstance(expr, AndGroup):
            results = [self.evaluate(child, stock, indicators) for child in expr.children]
            if any(r == "FAIL" for r in results):
                return "FAIL"
            if all(r == "PASS" for r in results):
                return "PASS"
            return "SKIP"

        if isinstance(expr, OrGroup):
            results = [self.evaluate(child, stock, indicators) for child in expr.children]
            if any(r == "PASS" for r in results):
                return "PASS"
            if all(r == "FAIL" for r in results):
                return "FAIL"
            return "SKIP"

        if isinstance(expr, ClassificationFilter):
            return self._eval_classification(expr, stock)

        if isinstance(expr, IndicatorFilter):
            return self._eval_indicator(expr, indicators)

        return "SKIP"

    def _eval_classification(self, f: ClassificationFilter, stock: StockRow) -> str:
        actual = getattr(stock, f.field, None)
        if actual is None:
            return "SKIP"
        try:
            return "PASS" if _compare(actual, f.op, f.value) else "FAIL"
        except Exception:
            return "SKIP"

    def _eval_indicator(self, f: IndicatorFilter, indicators: dict) -> str:
        key = f"{f.indicator.lower()}_{f.timeframe.upper()}"
        ind_data = indicators.get(key)
        if ind_data is None:
            return "SKIP"
        actual = ind_data.get(f.field)
        if actual is None:
            return "SKIP"
        try:
            return "PASS" if _compare(float(actual), f.op, float(f.value)) else "FAIL"
        except Exception:
            return "SKIP"


filter_engine = FilterEngine()
