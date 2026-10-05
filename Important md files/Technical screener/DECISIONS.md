# Architectural Decisions

## ADR-001 — Kite MCP configured via mcp-remote; INDMoney MCP as primary fundamental/classification provider
**Date**: 2026-08-21 (revised 2026-08-21)
**Status**: Accepted

**Context**: The project spec (Readme.md) references Kite MCP for market data and OHLC. Kite MCP was initially believed unavailable but was found configured globally as `npx mcp-remote https://mcp.kite.trade/mcp`. It has been added to the project's `.mcp.json`.

**Decision**: 
- Kite MCP: configured, used for quotes/LTP/OHLC/historical candles when Kite session is active. `KiteMCPAdapter` starts with capabilities `UNAVAILABLE` and upgrades to `AVAILABLE` once actual tool names are confirmed from a live session.
- INDMoney MCP: primary provider for fundamentals (PE, PB, ROE), sector/industry classification, and market cap — capabilities Kite does not provide.
- TradingView MCP: primary provider for technical indicators (RSI, BB) and batch indicator fetching.
- Provider priority for OHLCV: Kite MCP > TradingView MCP > INDMoney MCP.

**Consequences**: Three MCP providers available (two confirmed active, one session-dependent). MCPRouter selects by capability with fallback chain. No business logic changes needed when Kite session becomes active — only the adapter capability registry updates.

---

## ADR-002 — pnpm workspaces for monorepo
**Date**: 2026-08-21
**Status**: Accepted

**Context**: Project needs a web frontend (apps/web) and an API backend (apps/api) with shared backend modules (src/).

**Decision**: Use pnpm workspaces. Simpler than Turborepo for an early-stage project while still providing proper dependency isolation.

---

## ADR-003 — Drizzle ORM for PostgreSQL
**Date**: 2026-08-21
**Status**: Proposed

**Context**: Need a TypeScript-native PostgreSQL ORM. Options: Drizzle, Prisma, TypeORM, raw pg.

**Decision**: Drizzle ORM. Type-safe, lightweight, excellent TypeScript inference, migration support, no code generation overhead at runtime.

---

## ADR-004 — No microservices in V1
**Date**: 2026-08-21
**Status**: Accepted

**Context**: Spec explicitly says modular monolith.

**Decision**: Single API process with strictly bounded modules. `AgentMessageBus` is in-process. Can be extracted to Redis Streams / NATS when scale demands it — agent contracts will not change.

---

## ADR-005 — PASS/FAIL/UNKNOWN filter semantics
**Date**: 2026-08-21
**Status**: Accepted

**Context**: Data from MCP providers may be unavailable for some stocks/timeframes.

**Decision**: Every DSL condition evaluates to PASS, FAIL, or UNKNOWN. Missing data → UNKNOWN (never fabricated as 0 or false). The user can configure how UNKNOWN values are treated in a screen (exclude, include, or separate bucket).

---

## ADR-006 — LLM never calls MCP directly
**Date**: 2026-08-21
**Status**: Accepted

**Context**: Spec rule 7 and 72.

**Decision**: LLM → Application Tools → Orchestrator → Agent → MCPRouter → MCPAdapter → MCP Server. The LLM only sees a controlled toolset of application-level tools (create_screen, run_screen, explain_stock, etc.). All Zod-validated before execution.

---

## ADR-007 — TradingView batch_run for 750-stock indicator fetching
**Date**: 2026-08-21
**Status**: Proposed

**Context**: Fetching RSI/BB for 750 stocks sequentially would be extremely slow.

**Decision**: Use TradingView MCP's `batch_run` tool to run indicator queries across multiple symbols/timeframes in parallel. Apply cheap filters (market cap, sector) first via INDMoney MCP to reduce the candidate set before requesting expensive indicator data.

---

## ADR-008 — Nifty Total Market stock list seeded from static data initially
**Date**: 2026-08-21
**Status**: Proposed

**Context**: INDMoney MCP provides stock details per symbol but not a full index constituent list. TradingView MCP has `symbol_search` but not an index membership query.

**Decision**: Seed the ~750 Nifty Total Market constituents from a curated CSV/JSON seed file (sourced from NSE website). This data is quasi-static (NSE updates it quarterly). Implement a manual refresh mechanism. Store in `universe_memberships` table with source and effective dates.

---

## ADR-009 — Redis cache TTL strategy
**Date**: 2026-08-21
**Status**: Proposed

**Context**: MCP calls have latency. Indicator values are stable within a trading day.

**Decision**:
- End-of-day indicator values (1D timeframe): cache until next market open (TTL ~18h)
- Real-time quotes: cache 60s during market hours, 300s post-market
- Fundamentals (PE/PB): cache 24h
- Universe membership: cache 7 days (changes quarterly)
- Sector classification: cache 7 days

---

## ADR-010 — GPT-OSS 20B as initial LLM, via LLMProvider interface
**Date**: 2026-08-21
**Status**: Accepted

**Context**: Spec specifies GPT-OSS 20B. Provider must be swappable.

**Decision**: Implement `LLMProvider` interface. `GPTOSSProvider` is the first implementation. If API key is not configured, return `NOT_CONFIGURED` status without crashing. All LLM model names come from env vars, never hard-coded in business logic.
