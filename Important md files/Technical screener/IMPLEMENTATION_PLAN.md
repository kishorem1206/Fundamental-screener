# Implementation Plan — Indian Stock Screener

## Last Updated
2026-08-24

> **Stack note**: Backend was migrated from TypeScript (Fastify + Drizzle) to **Python (FastAPI + SQLAlchemy + Alembic)** on 2026-08-22. All completed items below reflect the Python implementation.

## Repository Assessment (Phase 0 — Complete)

**State**: Greenfield. Only `Readme.md` and `Instructions.md` exist.

**MCPs Available** (all three confirmed active):
- `TradingView MCP` — technical analysis: RSI, Bollinger, OHLCV, `batch_run`, indicators
- `INDMoney MCP` — fundamentals, sector/industry classification, market cap, option chain
- `Kite MCP` — real-time quotes/LTP/OHLC, bulk 500-instrument snapshots, historical candles, instrument search

**Key capability**: `kite.get_quotes` handles 500 instruments per call → only 2 calls for full Nifty Total Market (~750 stocks). This is the primary bulk data path for screening.

---

## Phase Roadmap

### Phase 0 — Inspect & Document ✅
- [x] Read Readme.md and Instructions.md
- [x] Inspect repository structure
- [x] Identify available MCPs and tools
- [x] Create IMPLEMENTATION_PLAN.md
- [x] Create ARCHITECTURE.md
- [x] Create DECISIONS.md
- [x] Create MCP_INTEGRATIONS.md
- [x] Create DEVELOPMENT_STATUS.md

---

### Phase 1 — Foundation ✅
**Objective**: Working skeleton with correct structure, Python (FastAPI), API, DB, Redis, MCP registry, LLM abstraction. No screener logic yet.

#### 1a — Project Scaffold ✅
- [x] `frontend/` — Vite + React 19 + TypeScript + Tailwind (unchanged)
- [x] `backend/` — FastAPI + Python 3.12 (migrated from Fastify/TypeScript)
- [x] `backend/pyproject.toml` — Python dependencies
- [x] `backend/Makefile` — `make dev / migrate / seed / generate / downgrade`
- [x] `.env.example`, `.gitignore`
- [x] `docker-compose.yml` (PostgreSQL + Redis)

#### 1b — Infrastructure ✅
- [x] PostgreSQL connection (SQLAlchemy 2.0 sync + psycopg2 pool)
- [x] Initial schema migrations via Alembic (8 tables: stocks, universes, universe_memberships, indicator_definitions, screen_definitions, chat_sessions, chat_messages, data_provenance_log)
- [x] Redis client with typed wrappers (`cache_get`, `cache_set`, `cache_del`)
- [x] structlog logging (structured, with correlation_id)
- [x] Global error handler (via FastAPI exception handlers)
- [x] Health endpoint (`GET /health`)

#### 1c — MCP Registry & Adapters ✅
- [x] `MCPRegistry` — register/query capabilities
- [x] `TradingViewMCPAdapter` — health stub
- [x] `INDMoneyMCPAdapter` — health stub
- [x] `KiteMCPAdapter` — blocks all V1 order-execution tools

#### 1d — LLM Provider Abstraction ✅
- [x] `LLMProvider` interface (chat, structuredOutput, stream)
- [x] `GPTOSSProvider` — returns `LLMNotConfiguredError` if no key set
- [x] `LLMProviderFactory` singleton

#### 1e — Agent Skeleton ✅
- [x] `Agent` interface with agentId, taskTypes, handle
- [x] `AgentRegistry` — register and look up agents
- [x] `AgentMessageBus` — in-process typed message bus
- [x] `AgentTask` / `AgentResult` typed schemas (Zod)

**Milestone verified**: `GET /health` returns status of PostgreSQL, Redis, TradingView MCP, INDMoney MCP, and LLM provider.

---

### Phase 2 — Universe & Classification ✅
**Objective**: Load Nifty Total Market stock universe (~750 stocks), sector/industry hierarchy, market-cap classification.

- [x] `UniverseAgent` — handles `LIST_UNIVERSES`, `GET_UNIVERSE_STOCKS`
- [x] Seed script: Nifty 50 stock list with symbol, ISIN, sector, industry, basic industry (`scripts/seeds/nifty50.json`)
- [x] `StockSeedLoader` — idempotent upsert loader
- [x] `universe_memberships` table populated (50 stocks × 3 universes)
- [x] Market-cap classification (`LARGE_CAP`, `MID_CAP`, `SMALL_CAP`, `MICRO_CAP`, `NANO_CAP`)
- [x] Sector hierarchy (macroSector → sector → industry → basicIndustry)
- [x] REST endpoints: `GET /api/universes`, `GET /api/universes/:id/stocks`, `GET /api/stocks`, `GET /api/stocks/:exchange/:symbol`
- [x] `ClassificationAgent` — handles `LIST_STOCKS`, `GET_STOCK`

**Milestone verified**: API returns Nifty 50 stocks with full classification. `kiteInstrumentToken` is null for all — populate in Phase 3 via Kite MCP `search_instruments`.

---

### Phase 3 — Indicators ✅
**Objective**: RSI and Bollinger Bands working via internal calculation engine + yfinance OHLCV.

- [x] `IndicatorPlugin` Protocol + `OHLCVBar`, `IndicatorResult`, `TechnicalSnapshot` dataclasses
- [x] `IndicatorRegistry` — plugin lookup singleton
- [x] `IndicatorEngine` — orchestrates OHLCV → plugin → TechnicalSnapshot
- [x] RSI plugin — Wilder's smoothing (EWM alpha=1/14), matches TradingView formula
- [x] Bollinger Bands plugin — SMA20 ± 2σ (population std, ddof=0), %B and bandwidth
- [x] `MarketDataFetcher` — yfinance wrapper for NSE (`INFY.NS`) / BSE (`INFY.BO`) OHLCV
- [x] `IndicatorAgent` — `GET_INDICATORS` task type, Redis caching with 4h TTL
- [x] Redis cache key: `indicators:{exchange}:{symbol}:{tf}:{sorted_indicators}:{today}`
- [x] Route: `GET /stocks/{exchange}/{symbol}/indicators?tf=1D&indicators=rsi,bollinger`
- [x] Proper error responses: 404 for unknown symbol, 422 for unsupported indicator

**Milestone verified** — `GET /stocks/NSE/INFY/indicators?tf=1D&indicators=rsi,bollinger`:
- RSI(14): 47.13, signal NEUTRAL
- BB(20,2): upper 1210.29, middle 1150.35, lower 1090.41, %B 0.2552, signal NEUTRAL
- Provenance: yfinance / INFY.NS / 125 bars / 2026-02-23 to 2026-08-21

**Note**: TradingView MCP is the planned primary source (Phase 6 via LLM tool calls). yfinance is the fallback and current implementation.

---

### Phase 4 — Screening DSL + Filter Engine ✅
**Objective**: The core screening pipeline working end-to-end.

- [x] Screening DSL (Python dataclasses + Pydantic) — `AndGroup`, `OrGroup`, `ClassificationFilter`, `IndicatorFilter`
- [x] `parse_filter_expr()` — recursive DSL parser
- [x] `FilterEngine` — evaluates DSL against stock snapshots, returns PASS/FAIL/SKIP
- [x] Cheap classification pre-filter before expensive yfinance calls
- [x] `RankingEngine` — sort by indicator field asc/desc
- [x] `FilterAgent` — handles `RUN_SCREEN` task
- [x] `ScreeningService` — ThreadPoolExecutor(5) parallel yfinance, Redis cache (4h TTL)
- [x] REST endpoint: `POST /screens/run` (body = ScreenDSL)
- [x] Universe seeded: 488 stocks in NIFTY_500 and NIFTY_TOTAL_MARKET (50 Nifty 50 + 438 additional)

**Milestone verified**: `POST /screens/run` with `NIFTY_50 + RSI<45 AND %B<0.35` → 10 matches in 6.4s. Nifty 500 RSI>65 + upper BB → found DIVISLAB RSI=73.84 %B=0.71, TITAN RSI=69.12 %B=0.73.

---

### Phase 5 — Specialized Agents ✅
- [x] `MarketDataAgent`
- [x] `ExplanationAgent`
- [x] `FundamentalAgent` (via INDMoney MCP)
- [x] `ResearchAgent` (stub)
- [x] `ScoringAgent` (configurable weights)
- [x] RSI Momentum plugin + service + route (`POST /rsi-momentum/scan`)
  - Signals: FRESH_BREAKOUT > APPROACHING_AGAIN > APPROACHING > ALREADY_STRONG > EXTENDED > NEUTRAL
  - ThreadPoolExecutor(5) with Redis cache (4h TTL)
- [x] RSI Divergence engine + service + route (`POST /rsi-divergence/scan`)
  - REGULAR/HIDDEN × BULLISH/BEARISH divergence types
  - Pivot detection with configurable left/right bars
  - `get_current_rsi()` helper — rsi_today + rsi_prev stored per stock in cache
  - `require_rsi_rising` post-filter (applied after cache, not part of cache key)
  - Cache version v3 (includes rsi_today/rsi_prev fields)
- [x] Screening DSL `extra_indicators` — fetch BB/MACD/Vol for display without filtering by them
- [x] OrGroup pre-pass bug fix — `OrGroup` with only `IndicatorFilter` children no longer incorrectly rejects all stocks

---

### Phase 6 — AI Chat ✅
- [x] `LLMChatAgent` — intent detection + dispatch (SCREEN / QUOTE / FUNDAMENTALS / GENERAL)
- [x] Intent-based routing: screen queries → `_do_screen()`, stock quotes → Kite MCP, fundamentals → INDMoney MCP
- [x] NLP helpers: `_extract_symbols`, `_extract_universe`, `_extract_market_cap`, `_extract_rsi_threshold`, `_extract_bb_condition`, `_detect_volume_condition`, `_llm_extract_filters`
- [x] Chat history: last 20 messages sent as context to LLM per turn
- [x] `chat_sessions` + `chat_messages` tables wired to routes
- [x] REST API: `POST /chat/sessions`, `GET /chat/sessions`, `POST /chat/sessions/{id}/messages`, `DELETE /chat/sessions/{id}`
- [x] `ChatPanel.tsx` frontend — 487-line component with session management, message history, typing indicator

---

### Phase 7 — Dashboard & Frontend (partial) ✅
- [x] Professional dark-theme dashboard layout (sidebar + main content)
- [x] Universe selector — Nifty 50 / Nifty 500 / Total Market
- [x] Screen page — dynamic filter builder (RSI, Bollinger), sortable results table, stats bar
- [x] RSI Momentum page
  - Universe, threshold, lookback, RSI display range (dual slider), signal selector
  - Freshness toggle (Either / Fresh only / Was above), RSI rising today toggle
  - Extra filters: Bollinger Band, MACD, Volume (always fetched for display)
  - Results table: BB %B, MACD hist, Vol% always visible; compact padding; always-visible scrollbar
  - CSV export with all columns
- [x] RSI Divergence page
  - Pivot controls, recency bar, divergence type selector
  - Dual range slider for bars between P1 & P2 (5–50)
  - Max/min pivot RSI sliders
  - RSI rising today toggle (server-side)
  - RSI NOW column (↑/↓) in results table
- [ ] Market-cap filter chips, sector filter
- [ ] Stock detail drawer/page
- [ ] Saved screens UI

---

### Phase 8 — Advanced Analysis
- [ ] `CandlestickAgent` (Doji, Hammer, Engulfing, etc.)
- [ ] `StrategyAgent` (versioned strategies)
- [ ] Additional indicators: EMA, SMA, ATR, ADX, Stochastic, VWAP
- [ ] Alerts system
- [ ] `BacktestAgent` skeleton (point-in-time historical data)

---

### Phase 9 — Future
- [ ] News MCP integration
- [ ] FII/DII data
- [ ] Market regime agent
- [ ] Portfolio agent
- [ ] Strategy discovery agent

---

## Critical Rules (always enforced)

1. Inspect before coding any new phase.
2. Never invent MCP tool names — only use names confirmed in MCP tool list.
3. Never fabricate financial data — UNKNOWN over fake.
4. LLM never executes raw SQL or raw MCP calls.
5. All LLM structured output validated with Zod.
6. Every financial value carries provenance.
7. Filter before score; cheap filters before expensive MCP calls.
8. Cache all MCP responses in Redis.
9. No order execution in V1.
10. Update this doc after every meaningful session.
