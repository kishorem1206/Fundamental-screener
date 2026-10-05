from fastapi import APIRouter, HTTPException, Request
from app.technical.agents.message_bus import agent_message_bus
from app.technical.screening.dsl import ScreenDSL
from app.technical.shared.schemas import AgentTask
from app.technical.shared.utils import now_iso, generate_id

router = APIRouter(tags=["screens"])


@router.post("/screens/run")
def run_screen(body: ScreenDSL, request: Request):
    task = AgentTask(
        task_id=generate_id(),
        correlation_id=request.state.correlation_id,
        from_agent="screens_route",
        to_agent="filter_agent",
        task_type="RUN_SCREEN",
        payload=body.model_dump(),
        created_at=now_iso(),
    )
    result = agent_message_bus.dispatch(task)

    if result.status == "FAILED":
        errors = result.errors
        code = errors[0].code if errors else "SCREEN_FAILED"
        msg = errors[0].message if errors else "Screen execution failed"
        status_code = 422 if code == "VALIDATION_ERROR" else 500
        raise HTTPException(status_code=status_code, detail=msg)

    return result.data
