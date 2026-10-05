from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import Literal, Any


# ── Individual filter conditions ──────────────────────────────────────────────

class ClassificationFilter(BaseModel):
    type: Literal["classification"]
    field: Literal["sector", "macro_sector", "market_cap_category", "exchange", "symbol"]
    op: Literal["eq", "neq", "in", "nin"]
    value: str | list[str]


class IndicatorFilter(BaseModel):
    type: Literal["indicator"]
    indicator: str                  # "rsi" | "bollinger"
    field: str = "value"            # RSI → "value"; BB → "percent_b" | "upper" | "lower" | "middle" | "bandwidth"
    timeframe: str = "1D"
    op: Literal["lt", "lte", "gt", "gte", "eq", "neq"]
    value: float | int


# ── Boolean grouping ───────────────────────────────────────────────────────────

@dataclass
class AndGroup:
    children: list[Any]  # list[ClassificationFilter | IndicatorFilter | AndGroup | OrGroup]


@dataclass
class OrGroup:
    children: list[Any]


FilterExpr = ClassificationFilter | IndicatorFilter | AndGroup | OrGroup


def parse_filter_expr(data: dict | None) -> FilterExpr | None:
    """Recursively parses a raw filter dict into typed objects."""
    if data is None:
        return None
    if "and" in data:
        return AndGroup(children=[parse_filter_expr(c) for c in data["and"]])
    if "or" in data:
        return OrGroup(children=[parse_filter_expr(c) for c in data["or"]])
    t = data.get("type")
    if t == "classification":
        return ClassificationFilter.model_validate(data)
    if t == "indicator":
        return IndicatorFilter.model_validate(data)
    raise ValueError(f"Cannot parse filter expression: {data}")


def extract_indicator_needs(expr: FilterExpr | None) -> set[tuple[str, str]]:
    """Returns set of (indicator_name, timeframe) pairs needed by the expression."""
    if expr is None:
        return set()
    if isinstance(expr, (AndGroup, OrGroup)):
        needs: set[tuple[str, str]] = set()
        for child in expr.children:
            needs |= extract_indicator_needs(child)
        return needs
    if isinstance(expr, IndicatorFilter):
        return {(expr.indicator, expr.timeframe.upper())}
    return set()


# ── Top-level screen definition ───────────────────────────────────────────────

class RankSpec(BaseModel):
    indicator: str
    field: str = "value"
    timeframe: str = "1D"
    order: Literal["asc", "desc"] = "asc"


class ScoreCriterionSpec(BaseModel):
    """One criterion in a composite score config."""
    indicator: str
    field: str = "value"
    timeframe: str = "1D"
    weight: float = 1.0
    direction: Literal["lower_is_better", "higher_is_better"] = "lower_is_better"
    range_min: float = 0.0
    range_max: float = 100.0


class ExtraIndicatorSpec(BaseModel):
    indicator: str
    timeframe: str = "1D"


class ScreenDSL(BaseModel):
    universe: str = "NIFTY_50"
    filters: dict | None = None   # raw dict; parsed into FilterExpr by screening_service
    rank_by: RankSpec | None = None
    # Optional composite scoring — if set, each matched stock gets a `score` field
    score_by: list[ScoreCriterionSpec] | None = None
    # Indicators to always fetch and include in results (not used for filtering)
    extra_indicators: list[ExtraIndicatorSpec] | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
