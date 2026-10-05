# Where to Start Reading the Code

This guide gives you the best reading order for understanding the Python backend — from the outside in.

---

## Start here: the big picture

1. **[docker-compose.yml](docker-compose.yml.explained.md)** — What services run (PostgreSQL, Redis). The infrastructure the app depends on.

2. **[.env.example](env.example.explained.md)** — All the configuration knobs. Read this to understand what can be changed.

3. **[pyproject.toml](pyproject.toml.explained.md)** — All Python dependencies and why each exists.

4. **[Makefile](Makefile.explained.md)** — The 5 commands you'll actually use (`make dev`, `make migrate`, `make seed`, etc.).

---

## Then: how the server starts

5. **[config.py](config.py.explained.md)** — How environment variables become typed Python attributes (pydantic-settings).

6. **[logger.py](logger.py.explained.md)** — How logging is configured (structlog, pretty in dev / JSON in prod).

7. **[main.py](main.py.explained.md)** — The FastAPI app, middleware registration, route registration, and startup/shutdown sequence.

---

## Then: the database layer

8. **[models.py](models.py.explained.md)** — The 8 database tables as SQLAlchemy ORM classes.

9. **[database.client.py](database.client.py.explained.md)** — Connection pool, session factory, `get_db()`, health check.

10. **[alembic.migration.py](alembic.migration.py.explained.md)** — How the schema was created (Alembic migration file).

---

## Then: the service layer (business logic)

11. **[classification_service.py](classification_service.py.explained.md)** — Queries for listing stocks, filtering, pagination, get-by-ID.

12. **[stock_seed_loader.py](stock_seed_loader.py.explained.md)** — How Nifty 50 stocks are loaded into the database on first setup.

13. **[seed_stocks.py](seed_stocks.py.explained.md)** — The CLI script that calls the seed loader (`make seed`).

---

## Then: the agent layer

14. **[shared/schemas.py](schemas.py.explained.md)** — `AgentTask` and `AgentResult` — the envelopes agents pass to each other.

15. **[agents/registry.py](agents.registry.py.explained.md)** — The phone book: maps agent IDs to agent instances.

16. **[agents/message_bus.py](agents.message_bus.py.explained.md)** — The dispatcher: routes tasks to the right agent.

17. **[universe_agent.py](universe_agent.py.explained.md)** — Handles universe-related tasks.

18. **[classification_agent.py](classification_agent.py.explained.md)** — Handles stock-related tasks.

---

## Then: HTTP layer (routes + middleware)

19. **[correlation.py](correlation.py.explained.md)** — Adds a unique ID to every request for traceability.

20. **[health.py](health.py.explained.md)** — `/health` endpoint: checks DB, Redis, MCP status.

21. **[routes.universes.py](routes.universes.py.explained.md)** — `GET /universes` and `GET /universes/{id}/stocks`.

22. **[routes.stocks.py](routes.stocks.py.explained.md)** — `GET /stocks` and `GET /stocks/{exchange}/{symbol}`.

---

## Then: MCP and LLM (Phase 3 prep)

23. **[mcp/types.py](mcp.types.py.explained.md)** — `MCPAdapter` Protocol and health/quote data structures.

24. **[mcp/kite.py](mcp.kite.py.explained.md)** — Kite adapter: available tools, blocked V1 write tools.

25. **[mcp/registry.py](mcp.registry.py.explained.md)** — MCP provider registry (like agent registry but for MCP adapters).

26. **[llm/types.py](llm.types.py.explained.md)** — `LLMMessage`, `LLMCompletionOptions`, `LLMProvider` Protocol.

27. **[llm/gpt_oss.py](llm.gpt_oss.py.explained.md)** — OpenAI-compatible LLM provider using httpx.

28. **[llm/factory.py](llm.factory.py.explained.md)** — Creates the right LLM provider based on config.

---

## Frontend (unchanged from TypeScript)

29. **[vite.config.ts](vite.config.ts.explained.md)** — Dev server + proxy (`/api` → `localhost:3001`).

30. **[App.tsx](App.tsx.explained.md)** — The main React component with the health dashboard.

---

## Shared types and errors

31. **[shared/types.py](shared.types.py.explained.md)** — `Literal` type aliases (Exchange, MarketCapCategory, etc.).

32. **[shared/errors.py](errors.py.explained.md)** — Error class hierarchy (`AppError` → `NotFoundError`, etc.).

33. **[shared/utils.py](shared.utils.py.explained.md)** — `generate_id()`, `now_iso()`, `build_cache_key()`, `chunk()`.

---

## Key concepts to understand Python/FastAPI (vs TypeScript/Node)

| TypeScript/Node | Python/FastAPI |
|----------------|----------------|
| `package.json` | `pyproject.toml` |
| `pnpm install` | `uv pip install ...` |
| `tsx watch` | `uvicorn --reload` |
| Fastify | FastAPI |
| Drizzle ORM | SQLAlchemy 2.0 |
| drizzle-kit migrate | Alembic |
| Zod | Pydantic v2 |
| ioredis | redis-py (sync) |
| Pino | structlog |
| fetch() | httpx |
| `async/await` | `def` (FastAPI runs in thread pool) |
| TypeScript interfaces | Python Protocols |
| Union types | `Literal[...]` types |
| `process.env` | `pydantic-settings` BaseSettings |
