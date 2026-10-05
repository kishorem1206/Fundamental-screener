from fastapi import APIRouter, HTTPException, Request
from app.technical.agents.message_bus import agent_message_bus
from app.technical.shared.schemas import AgentTask
from app.technical.shared.utils import now_iso, generate_id

router = APIRouter(tags=["indicators"])


@router.get("/stocks/{exchange}/{symbol}/indicators")
def get_indicators(
    exchange: str,
    symbol: str,
    request: Request,
    tf: str = "1D",
    indicators: str = "rsi,bollinger",
):
    task = AgentTask(
        task_id=generate_id(),
        correlation_id=request.state.correlation_id,
        from_agent="indicators_route",
        to_agent="indicator_agent",
        task_type="GET_INDICATORS",
        payload={
            "exchange": exchange.upper(),
            "symbol": symbol.upper(),
            "timeframe": tf.upper(),
            "indicators": indicators,
        },
        created_at=now_iso(),
    )
    result = agent_message_bus.dispatch(task)

    if result.status == "FAILED":
        errors = result.errors
        if errors:
            code = errors[0].code
            msg = errors[0].message
            if code == "DATA_UNAVAILABLE":
                raise HTTPException(status_code=404, detail=msg)
            if code in ("VALIDATION_ERROR", "UNSUPPORTED_INDICATOR"):
                raise HTTPException(status_code=422, detail=msg)
        raise HTTPException(status_code=500, detail=errors[0].message if errors else "Indicator calculation failed")

    return result.data
