# backend/app/routes/health.py — Beginner Explanation

> **Source file:** `backend/app/routes/health.py`

---

## 1. What is this file?

Defines two health check endpoints that report whether the server, database, and Redis are working. Used by monitoring tools and Docker health checks.

Equivalent to TypeScript's `health.route.ts`.

---

## 2. The two endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Full check: DB + Redis + MCP status |
| `GET /health/live` | Lightweight: just "is the process alive?" |

---

## 3. Line-by-line explanation

### Router setup

```python
router = APIRouter(tags=["health"])
```

**`APIRouter`** — FastAPI's way to group related routes. The `tags=["health"]` groups these routes under the "health" section in the `/docs` Swagger UI.

---

### `/health/live` — liveness probe

```python
@router.get("/health/live")
def health_live():
    return {"status": "ok"}
```

Returns immediately with `{"status": "ok"}` and HTTP 200. No database or Redis calls. Used by Kubernetes/Docker to check "is this process responding at all?"

---

### `GET /health` — full readiness check

```python
@router.get("/health")
def health_check(request: Request):
    db_healthy = check_database_health()
    redis_healthy = check_redis_health()
    mcp_statuses = mcp_registry.health_all()

    overall = "ok" if (db_healthy and redis_healthy) else "error"

    body = {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "correlation_id": getattr(request.state, "correlation_id", None),
        "checks": {
            "database": "ok" if db_healthy else "error",
            "redis": "ok" if redis_healthy else "error",
            "mcp": [
                {
                    "provider": s.provider_id,
                    "status": s.status,
                    "available_tools": s.available_tools,
                    "blocked_tools": s.blocked_tools,
                }
                for s in mcp_statuses
            ],
        },
    }

    return JSONResponse(content=body, status_code=200 if overall == "ok" else 503)
```

**`check_database_health()`** — Runs `SELECT 1` against PostgreSQL. Returns `True` or `False`.

**`check_redis_health()`** — Calls `PING` on Redis. Returns `True` or `False`.

**`mcp_registry.health_all()`** — Returns the health status of each MCP provider (Kite, TradingView, INDMoney).

**`overall = "ok" if (db_healthy and redis_healthy) else "error"`** — If either DB or Redis is down, the overall status is `"error"`. MCP health doesn't affect overall — MCP being unavailable is degraded, not broken.

**`JSONResponse(content=body, status_code=503)`** — When something is broken, return HTTP 503 (Service Unavailable), not 200. This matters for monitoring tools: a 503 triggers alerts; a 200 does not.

**`datetime.utcnow().isoformat() + "Z"`** — Adds the current UTC timestamp in ISO 8601 format. The `+ "Z"` appends the timezone indicator (UTC).

---

## 4. Example response

```json
{
  "status": "ok",
  "timestamp": "2026-08-22T10:30:00.123456Z",
  "correlation_id": "abc-123-def-456",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "mcp": [
      {
        "provider": "kite",
        "status": "AVAILABLE",
        "available_tools": ["get_holdings", "get_positions", ...],
        "blocked_tools": ["place_order", "cancel_order", ...]
      }
    ]
  }
}
```
