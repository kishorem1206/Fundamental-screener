# Stock Screener — Claude Instructions

## ⚠️ MANDATORY: Explained Files Rule

**Every time you create or significantly modify a backend Python file, you MUST also create or update its corresponding explained file in `docs/explained/`.**

Naming convention: `docs/explained/<module>.<filename>.py.explained.md`

Examples:
- `backend/app/agents/scoring_agent.py` → `docs/explained/scoring_agent.py.explained.md`
- `backend/app/scoring/engine.py` → `docs/explained/scoring.engine.py.explained.md`
- `backend/app/routes/quotes.py` → `docs/explained/routes.quotes.py.explained.md`

Format for each explained file — see any existing file in `docs/explained/` as a template:
1. Title: `# backend/app/path/file.py — Beginner Explanation`
2. Source file path
3. What the file does (1–2 paragraphs)
4. Key sections with line-by-line explanation of non-obvious code

**This is not optional. Do not mark a phase complete without creating explained files for every new file in that phase.**

---

## Project Rules (always enforced)

- V1 is **read-only**. No automatic order execution.
- Never expose credentials to the browser. Use environment variables.
- LLM must NOT directly access databases, execute raw SQL, or call arbitrary MCP tools.
- Never allow arbitrary frontend JavaScript from the LLM.
- Cache all MCP/yfinance responses in Redis.
- Filter before score; cheap classification filters before expensive yfinance calls.

## Stack

- **Backend**: Python 3.12, FastAPI, uvicorn, SQLAlchemy 2.0 sync, Alembic, psycopg2, structlog
- **Data**: yfinance (OHLCV), INDMoney MCP (fundamentals when connected), Kite MCP (quotes when connected)
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS
- **Infra**: PostgreSQL (port 5433 via Docker), Redis (port 6379 via Docker)
- **Run**: `cd containers && docker compose up -d` then `cd backend && make dev`

## Ports

- Backend API: `http://localhost:3001`
- Frontend dev: `http://localhost:5173` (Vite proxies `/api` → 3001)

## Agent pattern

Each agent in `app/agents/` follows the same pattern:
- `agent_id: str` class variable
- `task_types: list[str]` class variable  
- `handle(task: AgentTask) -> AgentResult` method
- Module-level singleton (e.g. `scoring_agent = ScoringAgent()`)
- Registered in `app/main.py` lifespan via `agent_registry.register(...)`

## Phase status

- Phase 0–6 ✅ complete
- Phase 7: Dashboard & Frontend (partial — RSI Momentum + Divergence pages done, Screen page done, Chat panel done)
- Phase 8: Advanced Analysis (next)
- Phase 9: Future (news, FII/DII, portfolio)
