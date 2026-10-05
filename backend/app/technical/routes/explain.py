from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.technical.agents.message_bus import agent_message_bus
from app.technical.shared.schemas import AgentTask
from app.technical.shared.utils import generate_id, now_iso

router = APIRouter(tags=["explain"])


class ExplainRequest(BaseModel):
    stock: dict
    filters: dict | None = None
    indicators: dict = {}


@router.post("/stocks/explain")
def explain_result(body: ExplainRequest, request: Request):
    task = AgentTask(
        task_id=generate_id(),
        correlation_id=request.state.correlation_id,
        from_agent="explain_route",
        to_agent="explanation_agent",
        task_type="EXPLAIN_RESULT",
        payload={"stock": body.stock, "filters": body.filters, "indicators": body.indicators},
        created_at=now_iso(),
    )
    result = agent_message_bus.dispatch(task)
    if result.status == "FAILED":
        errors = result.errors
        raise HTTPException(status_code=422, detail=errors[0].message if errors else "Explanation failed")
    return result.data
