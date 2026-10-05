# backend/app/main.py — Beginner Explanation

> **Source file:** `backend/app/main.py`

---

## 1. What is this file?

This is the **entry point** of the Python backend — the first file FastAPI loads when the server starts. It creates the web application, registers middleware, registers routes, and wires everything together.

The equivalent of the TypeScript `backend/src/index.ts`.

---

## 2. Technology: FastAPI vs Fastify

| Fastify (was) | FastAPI (now) |
|---------------|---------------|
| `const app = Fastify({...})` | `app = FastAPI(...)` |
| `app.register(plugin)` | `app.include_router(router)` |
| `app.addMiddleware(...)` | `app.add_middleware(...)` |
| `bootstrap()` function | `lifespan` context manager |
| `process.on("SIGTERM", ...)` | Handled by uvicorn automatically |

---

## 5. Line-by-line explanation

### `lifespan` — startup + shutdown

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    agent_registry.register(universe_agent)
    agent_registry.register(classification_agent)
    logger.info("API server started", port=config.api_port, env=config.node_env)
    yield
    # Shutdown
    logger.info("Shutting down")
    close_database()
    close_redis()
```

**`@asynccontextmanager`** — A decorator that turns this function into a context manager. The code before `yield` runs on startup; the code after `yield` runs on shutdown.

**`yield`** — The server runs while execution is "paused" at this line. When FastAPI shuts down (Ctrl+C or SIGTERM), execution resumes after `yield`.

**Why register agents here?** — Agents must be registered before routes try to dispatch tasks. Registering in `lifespan` guarantees this happens before any HTTP request is handled.

**`close_database()` / `close_redis()`** — Release all connections cleanly. Without this, PostgreSQL/Redis see abandoned connections and eventually time them out.

---

### Creating the FastAPI app

```python
app = FastAPI(
    title="Stock Screener API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)
```

**`docs_url="/docs"`** — FastAPI auto-generates interactive API documentation at `http://localhost:3001/docs`. You can test all endpoints there in the browser — no curl needed.

**`lifespan=lifespan`** — Connects our startup/shutdown logic to the app.

---

### CORS middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**CORS** — Without this, the browser at `localhost:5173` (React) would refuse to call `localhost:3001` (Python API) for security reasons. This middleware explicitly allows those cross-origin requests.

**`config.cors_origins_list`** — Parses `"http://localhost:5173,http://localhost:3000"` from `.env` into a Python list.

---

### Error handlers

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message, "correlation_id": correlation_id},
    )
```

**`@app.exception_handler(AppError)`** — Registers a function that FastAPI calls whenever an `AppError` (or its subclasses like `NotFoundError`, `ValidationError`) is raised anywhere in the app.

**Result**: Routes can simply `raise NotFoundError("Stock", "NSE:XYZ")` and the handler automatically sends a 404 JSON response. No `try/except` needed in every route.

---

### Route registration

```python
app.include_router(health.router)
app.include_router(universes.router)
app.include_router(stocks.router)
```

Each `router` is an `APIRouter` object from a route file. `include_router` adds all its routes to the main app.

---

## 6. Startup sequence

```
uvicorn starts
    ↓
FastAPI app created
    ↓
CORS middleware installed
    ↓
Correlation middleware installed
    ↓
Error handlers registered
    ↓
Routes registered (health, universes, stocks)
    ↓
lifespan startup: agents registered, "API server started" logged
    ↓
uvicorn listens on port 3001
    ↓
Server handles requests
    ↓
Ctrl+C → SIGINT → lifespan shutdown: DB + Redis closed
```

---

## 7. How to start the server

```bash
cd backend/
make dev
# or directly:
PYTHONPATH=. .venv/bin/python3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

**`--reload`** — Watches files and restarts on changes (like `tsx watch`).

**`PYTHONPATH=.`** — Tells Python to look for modules starting from `backend/` (so `from app.config import config` resolves correctly).

---

## 8. Bonus: Interactive docs

Once running, visit `http://localhost:3001/docs` in your browser. You get a Swagger UI where you can call all API endpoints interactively — no curl needed.

---

## 9. Dependencies

| Depends on | Why |
|-----------|-----|
| `app/config.py` | Server port, CORS origins, env |
| `app/logger.py` | Structured logging |
| `app/middleware/correlation.py` | Correlation ID middleware |
| `app/routes/health.py` | `/health` route |
| `app/routes/universes.py` | `/universes` routes |
| `app/routes/stocks.py` | `/stocks` routes |
| `app/agents/registry.py` | Agent registry singleton |
| `app/agents/universe_agent.py` | Registered on startup |
| `app/agents/classification_agent.py` | Registered on startup |
| `app/shared/errors.py` | `AppError` base class |
