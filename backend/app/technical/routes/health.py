import time
from fastapi import APIRouter
from app.infrastructure.database.client import check_database_health
from app.technical.infrastructure.redis.client import check_redis_health
from app.technical.mcp.registry import mcp_registry
from app.technical.llm.factory import llm_provider

router = APIRouter()

_start_time = time.time()


@router.get("/health")
def health():
    database = check_database_health()
    redis_status = check_redis_health()

    mcp_services = {}
    for h in mcp_registry.health_all():
        key = h.provider_id.lower()
        entry = {"status": "ok" if h.status == "AVAILABLE" else h.status.lower()}
        if h.detail:
            entry["detail"] = h.detail
        mcp_services[key] = entry

    llm = (
        {"status": "ok", "provider": llm_provider.provider_id}
        if llm_provider.is_configured()
        else {"status": "not_configured", "provider": llm_provider.provider_id}
    )

    core_statuses = [database["status"], redis_status["status"]]
    if all(s == "ok" for s in core_statuses):
        overall = "ok"
    elif any(s == "ok" for s in core_statuses):
        overall = "degraded"
    else:
        overall = "error"

    from datetime import datetime, timezone
    body = {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": time.time() - _start_time,
        "services": {
            "database": database,
            "redis": redis_status,
            **mcp_services,
            "llm": llm,
        },
    }

    from fastapi.responses import JSONResponse
    status_code = 503 if overall == "error" else 200
    return JSONResponse(content=body, status_code=status_code)


@router.get("/health/live")
def health_live():
    from datetime import datetime, timezone
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
