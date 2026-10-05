from fastapi import APIRouter, HTTPException, Request
from app.technical.agents.message_bus import agent_message_bus
from app.technical.shared.schemas import AgentTask
from app.technical.shared.utils import generate_id, now_iso

router = APIRouter(tags=["fundamentals"])


@router.get("/stocks/{exchange}/{symbol}/fundamentals")
def get_fundamentals(exchange: str, symbol: str, request: Request):
    task = AgentTask(
        task_id=generate_id(),
        correlation_id=request.state.correlation_id,
        from_agent="fundamentals_route",
        to_agent="fundamental_agent",
        task_type="GET_FUNDAMENTALS",
        payload={"exchange": exchange.upper(), "symbol": symbol.upper()},
        created_at=now_iso(),
    )
    result = agent_message_bus.dispatch(task)
    if result.status == "FAILED":
        errors = result.errors
        code = errors[0].code if errors else "FETCH_FAILED"
        raise HTTPException(
            status_code=404 if code in ("DATA_UNAVAILABLE", "VALIDATION_ERROR") else 500,
            detail=errors[0].message if errors else "Fundamentals fetch failed",
        )
    return result.data
