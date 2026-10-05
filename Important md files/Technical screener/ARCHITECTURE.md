# Architecture — Stock Screener

## What Is This Application?

This is an **Indian stock market screening platform**. In plain language:

You type something like "Show me large-cap IT stocks where RSI is below 40 and price crossed above the 50-day moving average" — and the application finds every stock in the Nifty 500 that matches those conditions, right now, using live market data.

It also has an AI chat interface so you can describe what you want in normal English instead of knowing technical terms.

---

## The Big Picture

```
You (browser)
      ↓
  Frontend (React)
      ↓  HTTP
  Backend API (Fastify)
      ↓              ↓
PostgreSQL DB     Redis Cache
      ↓
  MCP Providers (Kite / TradingView / INDMoney)
      ↓
 Live Market Data
```

Every layer has a specific job. Nothing else does that job.

---

## The Layers Explained

### 1. Frontend (`frontend/`)

**What it is:** The website you see in the browser.

**Built with:** React + TypeScript + Vite + Tailwind CSS

**Its only job:** Show information to the user and send their actions to the backend. It never talks to the database or market data providers directly.

**Right now:** Shows a System Health dashboard that calls the backend's `/health` endpoint and displays whether everything is running.

**Future:** Will have a chat interface, screening results table, stock detail pages.

---

### 2. Backend API (`backend/`)

**What it is:** A server that runs on your computer (or a server in the cloud). It receives HTTP requests from the browser, does the work, and sends back responses.

**Built with:** Fastify + TypeScript + Node.js

**Its job:**
- Receives requests from the frontend
- Validates those requests
- Asks the database/cache for data
- Asks market data providers for live prices
- Runs the screening engine
- Returns results

The backend is the only thing allowed to touch the database, the cache, and the market data providers. The browser never touches these directly.

---

### 3. Shared Package (`shared/`)

**What it is:** A folder of TypeScript code that is used by BOTH the frontend and backend.

**Why it exists:** Instead of writing the same type definitions, validation schemas, and error classes twice (once for frontend, once for backend), we put them in one place and both sides import from it.

**Contains:**
- TypeScript types (what a "Stock" looks like, what a "Screen" looks like)
- Zod validation schemas (rules that check if data is correctly shaped)
- Error classes (AppError, NotFoundError, etc.)
- Utility functions (generate IDs, build cache keys, etc.)

---

### 4. Database (`containers/` + `backend/src/infrastructure/database/`)

**What it is:** PostgreSQL 16 — a relational database that stores structured data permanently.

**Runs in:** Docker container

**Stores:**
- Stock information (name, symbol, sector, market cap)
- Screen definitions (saved filter queries)
- Chat history (what the user asked, what the AI replied)
- Technical indicator definitions
- Data provenance logs (audit trail of where data came from)

**Important:** The database stores definitions and historical data. Live prices come from MCP providers, not from this database.

---

### 5. Cache (`containers/` + `backend/src/infrastructure/redis/`)

**What it is:** Redis 7 — an in-memory key-value store. Think of it as a very fast sticky-note system.

**Why it exists:** Getting live data from market providers (Kite, TradingView) takes time. If we fetch Infosys's price once, we store it in Redis for 60 seconds. The next request within that 60 seconds gets the cached copy — no waiting.

**Runs in:** Docker container

---

### 6. MCP Providers (`backend/src/mcp/`)

**What they are:** MCP stands for "Model Context Protocol" — a standardised way for AI tools to connect to external services. In practice, these are pre-built connections to:

- **Kite MCP** — Zerodha's broker API. Gives us: live prices, historical candles, order placement (blocked in V1), holdings, positions.
- **TradingView MCP** — Controls a running TradingView Desktop app via browser automation. Gives us: chart screenshots, indicator values (RSI, MACD, Bollinger Bands), Pine Script execution.
- **INDMoney MCP** — INDMoney's cloud service. Gives us: portfolio data, mutual fund info, option chains.

**Critical rule:** These providers are **read-only in V1**. The application cannot place, modify, or cancel orders. This is enforced in code by `KiteMCPAdapter.isToolBlocked()`.

---

### 7. LLM Provider (`backend/src/llm/`)

**What it is:** The AI brain. Currently configured as an OpenAI-compatible endpoint.

**Its job:** Receive user chat messages → understand what the user wants → return a structured JSON intent (CREATE_SCREEN, RUN_SCREEN, EXPLAIN_STOCK, etc.)

**Critical rules:**
- The LLM cannot directly access the database
- The LLM cannot execute arbitrary SQL
- The LLM cannot directly call MCP tools
- The LLM returns a structured intent → the backend validates it → then the backend executes it

---

### 8. Agent System (`backend/src/agents/`)

**What it is:** A collection of specialised "agents" — each one knows how to do one specific job.

Think of it like a team:
- **OrchestratorAgent** — the manager, breaks big tasks into smaller ones
- **MarketDataAgent** — fetches live prices from MCP providers
- **IndicatorAgent** — calculates RSI, Bollinger Bands, etc.
- **FilterAgent** — applies DSL filter conditions to stocks
- **LLMChatAgent** — manages the conversation with the AI

They communicate through a **message bus** (`AgentMessageBus`) — one agent sends a task, another agent picks it up.

---

## Folder Structure

```
Stock screener/
│
├── frontend/          ← The website (React + TypeScript)
│   ├── src/           ← Source code
│   │   ├── main.tsx   ← Entry point — starts the React app
│   │   ├── App.tsx    ← Root component — what the page shows
│   │   ├── pages/     ← Full-page views (PLANNED)
│   │   ├── components/← Reusable UI pieces (PLANNED)
│   │   ├── hooks/     ← React data-fetching hooks (PLANNED)
│   │   └── services/  ← HTTP calls to the backend (PLANNED)
│   ├── index.html     ← The HTML shell the browser loads
│   └── vite.config.ts ← Build tool configuration
│
├── backend/           ← The server (Fastify + TypeScript)
│   └── src/
│       ├── index.ts         ← Server entry point
│       ├── config.ts        ← Reads environment variables
│       ├── logger.ts        ← Application logging setup
│       ├── routes/          ← HTTP endpoints (/health, /screens, etc.)
│       ├── middleware/       ← Code that runs on every request
│       ├── infrastructure/  ← Database and Redis connections
│       │   ├── database/    ← PostgreSQL client + table definitions
│       │   └── redis/       ← Redis cache client
│       ├── mcp/             ← Market data provider connections
│       │   └── adapters/    ← One adapter per provider
│       ├── llm/             ← AI language model connection
│       │   └── providers/   ← One provider per LLM service
│       ├── agents/          ← The specialised work agents
│       └── engine/          ← Screening/indicator logic (PLANNED)
│
├── shared/            ← Code shared between frontend and backend
│   └── src/
│       ├── index.ts         ← Re-exports everything
│       ├── types/           ← TypeScript interfaces and type aliases
│       ├── schemas/         ← Zod validation schemas
│       ├── errors/          ← Error class definitions
│       └── utils/           ← Helper functions
│
├── containers/        ← Docker configuration
│   └── docker-compose.yml ← Defines PostgreSQL + Redis containers
│
├── database/          ← Database migrations (empty, PLANNED)
│   ├── migrations/    ← SQL migration files
│   └── seeds/         ← Initial data scripts
│
├── scripts/           ← One-off utility scripts (empty, PLANNED)
├── tests/             ← Automated test files (empty, PLANNED)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/              ← You are here
├── tsconfig.json      ← Root TypeScript configuration
├── pnpm-workspace.yaml ← Monorepo workspace definition
└── package.json       ← Root scripts and dev tools
```

---

## Data Flow: User Sends a Chat Message

```
User types: "Find IT stocks with RSI below 40"
        ↓
frontend/src/App.tsx (future: ChatPage.tsx)
  → sends POST /api/chat/message
        ↓
backend/src/routes/chat.ts (PLANNED)
  → validates request
  → dispatches task to OrchestratorAgent via AgentMessageBus
        ↓
OrchestratorAgent (PLANNED)
  → sends message to LLMChatAgent
        ↓
LLMChatAgent (PLANNED)
  → calls GPTOSSProvider.complete()
  → gets back: { intent: "CREATE_SCREEN", screen: { ... } }
  → validates the intent with Zod
        ↓
OrchestratorAgent
  → sends "RUN_SCREEN" task to ScreeningEngine (PLANNED)
        ↓
ScreeningEngine
  → asks UniverseAgent: "Get me all IT stocks"
  → asks MarketDataAgent: "Get live quotes for these stocks"
  → asks IndicatorAgent: "Calculate RSI for each stock"
  → asks FilterAgent: "Apply RSI < 40 filter"
        ↓
Results
  → cached in Redis
  → returned to frontend
        ↓
frontend shows results table
```

---

## Data Flow: Health Check (Currently Working)

```
Browser loads http://localhost:5173
        ↓
frontend/src/main.tsx
  → renders App component
        ↓
frontend/src/App.tsx
  → on page load: fetch("/api/health")
  → Vite proxy rewrites to: http://localhost:3001/health
        ↓
backend/src/routes/health.ts
  → runs database health check (SELECT 1)
  → runs Redis health check (PING)
  → checks MCP adapter status
  → checks LLM configuration
  → returns JSON: { status: "ok", services: { ... } }
        ↓
App.tsx renders status table
```

---

## Security Rules (Non-Negotiable)

These are enforced in code and will never be removed:

| Rule | Where Enforced |
|------|---------------|
| No order placement in V1 | `KiteMCPAdapter.isToolBlocked()` |
| LLM cannot access database directly | Route handlers validate LLM output first |
| LLM cannot execute arbitrary SQL | No SQL query path from LLM |
| No credentials in frontend | All secrets are in `.env` file, backend only |
| No arbitrary frontend JS from LLM | Not implemented, enforced by design |

---

## Current Status (Phase 1 Complete)

| Component | Status |
|-----------|--------|
| Backend server (Fastify) | ✅ Running on :3001 |
| Frontend (React/Vite) | ✅ Running on :5173 |
| PostgreSQL (Docker) | ✅ Running on :5433 |
| Redis (Docker) | ✅ Running on :6379 |
| /health endpoint | ✅ Working |
| MCP adapters (skeleton) | ✅ Registered, health reporting |
| LLM provider (skeleton) | ✅ Wired, needs API key |
| Agent system (skeleton) | ✅ Registry and bus ready |
| Database schema | ✅ Defined (migrations not run yet) |
| Screening engine | ⏳ Phase 2 |
| AI chat | ⏳ Phase 3 |
