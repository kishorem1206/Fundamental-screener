# backend/app/middleware/correlation.py — Beginner Explanation

> **Source file:** `backend/app/middleware/correlation.py`

---

## 1. What is this file?

Defines `CorrelationMiddleware` — a piece of code that runs on **every HTTP request** before the route handler. It reads or generates a correlation ID and attaches it to the request.

Equivalent to TypeScript's correlation ID middleware for Fastify.

---

## 2. What is a correlation ID?

A **correlation ID** is a unique identifier (UUID) that travels with a request through every system it touches:

```
Browser → sends X-Correlation-ID: abc-123 (or none)
    ↓
CorrelationMiddleware reads it (or generates one)
    ↓
Route handler reads request.state.correlation_id
    ↓
All log lines for this request include correlation_id: "abc-123"
    ↓
AgentTask.correlation_id = "abc-123"
    ↓
Agent logs also include correlation_id: "abc-123"
    ↓
Response header X-Correlation-ID: "abc-123"
```

When something goes wrong, you can search logs for `correlation_id = "abc-123"` and see the complete journey of that one request.

---

## 3. Line-by-line explanation

```python
class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        return response
```

**`BaseHTTPMiddleware`** — Starlette (the framework FastAPI is built on) base class for middleware. Requires implementing `async def dispatch(...)`.

**`async def dispatch`** — Must be `async` because `call_next(request)` is asynchronous (it awaits the rest of the request pipeline).

**`request.headers.get("x-correlation-id")`** — Checks if the browser sent a correlation ID. Returns `None` if not present.

**`or str(uuid.uuid4())`** — If no correlation ID in the request headers, generate a new UUID. `uuid.uuid4()` generates a random UUID like `"a3f8b2c1-4d5e-6789-abcd-ef0123456789"`.

**`request.state.correlation_id = correlation_id`** — Starlette's `request.state` is a simple object where you can attach arbitrary data. Route handlers can read it with `request.state.correlation_id`.

**`await call_next(request)`** — Passes the request to the next middleware or route handler. Returns the response. The `await` is necessary because the route handler may be asynchronous.

**`response.headers["x-correlation-id"] = correlation_id`** — Adds the correlation ID to the response headers so the browser (or another service) can log it on their side.

---

## 4. Middleware registration

In `main.py`:
```python
app.add_middleware(CorrelationMiddleware)
```

Middlewares run in reverse order of registration. Since CORS middleware is added first and correlation middleware second, correlation middleware runs first on incoming requests (outermost → innermost).

---

## 5. How routes access the correlation ID

```python
@router.get("/universes")
def get_universes(request: Request):
    correlation_id = request.state.correlation_id
    # Pass to agent task:
    task = AgentTask(correlation_id=correlation_id, ...)
```

By injecting `request: Request` as a parameter, FastAPI provides the current request object. The correlation ID is already on `request.state` thanks to the middleware.
