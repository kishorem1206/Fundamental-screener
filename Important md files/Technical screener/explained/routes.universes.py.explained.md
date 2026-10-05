# backend/app/routes/universes.py — Beginner Explanation

> **Source file:** `backend/app/routes/universes.py`

---

## 1. What is this file?

Defines two HTTP endpoints for listing universes and fetching stocks within a universe. Route handlers build an `AgentTask`, dispatch it through the message bus, and return the result as JSON.

---

## 2. The two endpoints

| Endpoint | Returns |
|----------|---------|
| `GET /universes` | List of all active universes (Nifty 50, Nifty Next 50, etc.) |
| `GET /universes/{universe_id}/stocks` | Stocks in a specific universe |

---

## 3. Line-by-line explanation

### `GET /universes`

```python
@router.get("/universes")
def get_universes(request: Request):
    task = AgentTask(
        correlation_id=request.state.correlation_id,
        from_agent="universes_route",
        to_agent="universe_agent",
        task_type="LIST_UNIVERSES",
        payload=None,
        created_at=now_iso(),
    )
    result = agent_message_bus.dispatch(task)

    if result.status == "FAILED":
        raise HTTPException(status_code=500, detail=result.errors[0].message if result.errors else "Unknown error")

    return result.data
```

**`def get_universes(request: Request)`** — A regular synchronous function (not `async def`). FastAPI automatically runs sync route handlers in a thread pool, preventing them from blocking the event loop.

**`agent_message_bus.dispatch(task)`** — Sends the task to the agent and waits for the result synchronously.

**`if result.status == "FAILED":`** — Agents never raise exceptions directly; they always return an `AgentResult`. The route checks the status and converts failures to HTTP exceptions.

**`raise HTTPException(status_code=500, ...)`** — FastAPI catches this and returns a JSON error response with the given status code.

**`return result.data`** — FastAPI automatically serializes this dict to JSON. No need to call `JSONResponse(...)` explicitly.

---

### `GET /universes/{universe_id}/stocks`

```python
@router.get("/universes/{universe_id}/stocks")
def get_universe_stocks(universe_id: str, request: Request):
    task = AgentTask(
        correlation_id=request.state.correlation_id,
        from_agent="universes_route",
        to_agent="universe_agent",
        task_type="GET_UNIVERSE_STOCKS",
        payload={"universe_id": universe_id},
        created_at=now_iso(),
    )
    result = agent_message_bus.dispatch(task)

    if result.status == "FAILED":
        errors = result.errors
        status_code = 404 if (errors and errors[0].code == "NOT_FOUND") else 500
        raise HTTPException(status_code=status_code, detail=errors[0].message if errors else "Unknown error")

    return result.data
```

**`{universe_id}` in the URL path** — FastAPI extracts this from the URL and passes it as the `universe_id` parameter. If someone calls `GET /universes/nifty50/stocks`, `universe_id = "nifty50"`.

**Status code detection** — If the error code is `"NOT_FOUND"`, return 404. Otherwise, return 500. This lets the frontend distinguish "universe doesn't exist" from "server crashed".

---

## 4. The serialization issue with `datetime`

Universes have a `last_synced_at` datetime field. Before the agent dispatches results, the service returns `UniverseRow` dataclasses with real Python `datetime` objects. `dataclasses.asdict()` converts them to... `datetime` objects, which are NOT JSON-serializable.

The agent converts `last_synced_at` to ISO string before returning:
```python
# In universe_agent.py:
row_dict = dataclasses.asdict(u)
if u.last_synced_at:
    row_dict["last_synced_at"] = u.last_synced_at.isoformat()
return self._success(task, [row_dict for u in universes])
```

FastAPI can then serialize the dict to JSON cleanly.

---

## 5. Route registration

In `main.py`:
```python
from app.routes import universes
app.include_router(universes.router)
```

No prefix is set, so the routes are at `/universes` and `/universes/{id}/stocks` — exactly what the Vite proxy expects after stripping `/api`.
