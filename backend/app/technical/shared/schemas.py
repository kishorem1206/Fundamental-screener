from __future__ import annotations
from typing import Any, Literal, Union
from pydantic import BaseModel, Field
import uuid


# ─── Agent schemas (mirrors shared/src/schemas/agent.ts) ─────────────────────

class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: str | None = None
    from_agent: str
    to_agent: str
    task_type: str
    payload: Any = None
    priority: Literal["HIGH", "NORMAL", "LOW"] = "NORMAL"
    created_at: str = Field(default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat() + "Z")
    deadline: str | None = None


class AgentError(BaseModel):
    code: str
    message: str
    detail: Any = None


class DataProvenance(BaseModel):
    source: Literal[
        "KITE_MCP", "TRADINGVIEW_MCP", "INDMONEY_MCP",
        "INTERNAL_ENGINE", "STATIC_SEED", "CACHE",
    ]
    provider: str
    retrieved_at: str
    calculated_at: str | None = None
    timeframe: str | None = None
    parameters: dict[str, Any] | None = None
    data_version: str | None = None
    cache_hit: bool
    cache_key: str | None = None


class AgentResult(BaseModel):
    task_id: str
    correlation_id: str
    agent: str
    status: Literal["SUCCESS", "PARTIAL", "FAILED", "UNKNOWN"]
    data: Any
    errors: list[AgentError] = []
    warnings: list[str] = []
    provenance: list[DataProvenance] = []
    duration_ms: float | None = None


# ─── DSL schemas (mirrors shared/src/schemas/dsl.ts) ─────────────────────────

class DSLCondition(BaseModel):
    field: str
    timeframe: str | None = None
    operator: Literal[
        "EQ", "NE", "GT", "GTE", "LT", "LTE",
        "BETWEEN", "IN", "NOT_IN", "CONTAINS",
        "CROSSED_ABOVE", "CROSSED_BELOW",
        "RISING", "FALLING", "NEAR",
    ]
    value: Any
    parameters: dict[str, Any] | None = None


class DSLAnd(BaseModel):
    and_: list[DSLExpression] = Field(..., alias="and")
    model_config = {"populate_by_name": True}


class DSLOr(BaseModel):
    or_: list[DSLExpression] = Field(..., alias="or")
    model_config = {"populate_by_name": True}


class DSLNot(BaseModel):
    not_: DSLExpression = Field(..., alias="not")
    model_config = {"populate_by_name": True}


DSLExpression = Union[DSLAnd, DSLOr, DSLNot, DSLCondition]

DSLAnd.model_rebuild()
DSLOr.model_rebuild()
DSLNot.model_rebuild()
