# Development Status

## Current Phase
**Phases 0–7 ✅ largely complete** (Phase 7 frontend partial)  
**Next: Phase 8 — Advanced Analysis**

---

## Folder Layout

```
project-root/
├── frontend/         React 19 + Vite 6 + Tailwind 3 (TypeScript)
│   └── src/
│       ├── components/   RSIMomentumPage, RSIDivergencePage, ScreenPage, ChatPage, App
│       ├── api.ts        All fetch helpers (runScreen, runScreenWithRSIMomentum, scanRSIDivergence, ...)
│       └── types.ts      Shared TypeScript types
├── backend/          FastAPI Python 3.12 server
│   └── app/
│       ├── agents/       Agent registry, message bus, all agents
│       ├── data/         market_data.py — yfinance OHLCV fetcher
│       ├── divergence/   engine.py — RSI divergence detection + get_current_rsi
│       ├── indicators/   plugin.py, RSI, Bollinger, MACD, Volume plugins + registry
│       ├── infrastructure/  DB (SQLAlchemy) + Redis clients
│       ├── routes/       FastAPI routers (all endpoints)
│       ├── screening/    dsl.py — ScreenDSL, FilterExpr, ExtraIndicatorSpec
│       ├── services/     screening_service, rsi_momentum_service, rsi_divergence_service, ...
│       └── shared/       errors, schemas, types, utils
├── containers/       docker-compose.yml (PostgreSQL port 5433 + Redis port 6379)
└── docs/             Architecture, decisions, implementation plan, explained/
```

---

## Completed Work

### Phase 0 — Inspect & Document ✅ (2026-08-21)
- Inspected greenfield repo; confirmed all 3 MCPs active (Kite, TradingView, INDMoney)
- Created full documentation suite: IMPLEMENTATION_PLAN.md, ARCHITECTURE.md, DECISIONS.md, MCP_INTEGRATIONS.md

---

### Phase 1 — Foundation ✅ (2026-08-22)
- FastAPI app scaffold, docker-compose (PostgreSQL 5433, Redis 6379), .env.example
- SQLAlchemy 2.0 sync + psycopg2, Alembic migrations (8 tables)
- Redis client with `cache_get` / `cache_set`
- structlog logging, correlation ID middleware, `/health` endpoint
- MCP adapter registry (Kite blocks V1 order tools), LLM provider abstraction, Agent skeleton

---

### Phase 2 — Universe & Classification ✅ (2026-08-22)
- 750+ stocks seeded across NIFTY_50, NIFTY_500, NIFTY_TOTAL_MARKET universes
- Market-cap classification (LARGE/MID/SMALL/MICRO/NANO_CAP)
- Sector hierarchy: macroSector → sector → industry → basicIndustry
- REST: `GET /universes`, `GET /universes/{id}/stocks`, `GET /stocks`, `GET /stocks/{exchange}/{symbol}`

---

### Phase 3 — Indicators ✅ (2026-08-22)
- `IndicatorPlugin` Protocol + `OHLCVBar`, `IndicatorResult` dataclasses
- `IndicatorRegistry` singleton
- RSI plugin — Wilder's smoothing (EWM alpha=1/14), matches TradingView
- Bollinger Bands plugin — SMA20 ± 2σ (population std, ddof=0), %B and bandwidth
- MACD plugin — 12/26/9 EMA, histogram, signal classification
- Volume Strength plugin — volume ratio vs 30-day average
- `market_data.py` — yfinance wrapper: NSE (`.NS`), BSE (`.BO`), 4H synthetic (resampled from 1H)
- All indicators cached in Redis (4h TTL, keyed by stock + timeframe + date)

---

### Phase 4 — Screening DSL + Filter Engine ✅ (2026-08-22)
- `ScreenDSL` Pydantic model: `AndGroup`, `OrGroup`, `ClassificationFilter`, `IndicatorFilter`
- `ExtraIndicatorSpec` + `extra_indicators` field — fetch additional indicators for display without filtering by them
- `parse_filter_expr()` — recursive DSL parser
- Cheap classification pre-filter before yfinance calls
  - **Bug fix**: `OrGroup` with only `IndicatorFilter` children correctly passes through (was returning `False` for `any([])`)
- `ScreeningService` — ThreadPoolExecutor(5), `fetch_needs = indicator_needs ∪ display_needs`
- REST: `POST /screens/run`
- Screen frontend page with live filter builder and results table

---

### Phase 5 — Specialized Agents ✅ (2026-08-22 – 2026-08-23)

**RSI Momentum:**
- `rsi_momentum.py` plugin — Wilder's RSI, signals: FRESH_BREAKOUT(5.0) > APPROACHING_AGAIN(4.5) > APPROACHING(4.0) > ALREADY_STRONG(3.0) > EXTENDED(2.0) > NEUTRAL(1.0)
- `rsi_momentum_service.py` — threaded scan with Redis cache (4h TTL)
- `POST /rsi-momentum/scan` endpoint
- Frontend: `RSIMomentumPage` with universe selector, threshold slider, lookback slider, dual RSI range filter, signal selector, freshness toggle (Either / Fresh only / Was above), RSI rising today toggle

**RSI Divergence:**
- `divergence/engine.py` — pivot detection (left/right bars), REGULAR/HIDDEN × BULLISH/BEARISH, `DivergenceConfig`, `get_current_rsi()` helper
- `rsi_divergence_service.py` — threaded scan, Redis cache (v3), `rsi_today`/`rsi_prev` stored in every cached row, `require_rsi_rising` post-filter applied after cache lookup
- `POST /rsi-divergence/scan` with params: `pivot_left/right`, `max_recency_bars`, `min/max_bars_between` (5–50), `min_rsi_change`, `min_price_chg_pct`, `max/min_pivot_rsi`, `require_rsi_rising`, `div_types`
- Frontend: `RSIDivergencePage` with dual range slider for bars between pivots, RSI rising today toggle, RSI NOW column (↑/↓)

**Other agents:**
- `ScoringAgent`, `ExplanationAgent`, `FundamentalAgent`, `MarketDataAgent`, `ResearchAgent`, `NiftyIndexAgent`

---

### Phase 7 — Dashboard & Frontend (partial) ✅

**RSI Momentum Page:**
- Combined scan always runs (BB/MACD/Vol always fetched for display via `extra_indicators`)
- Extra filter blocks: Bollinger Band (near_upper/above_upper/near_lower/below_lower), MACD (bullish/bearish), Volume (ratio slider 50–500%)
- Table: symbol, company (truncated), cap badge, signal badge, RSI, Prev, Chg, Dist, Trend, >60/Nd, Days Since, BB %B, MACD hist, Vol%
- Always-visible horizontal scrollbar (webkit + Firefox `scrollbarWidth: thin`)
- CSV export including all columns
- Stats bar: X fetched · Y shown · Zms · ↓ CSV button
- RSI rising today toggle (client-side post-filter on `rsi_change > 0`)

**RSI Divergence Page:**
- Pivot controls, recency bar, divergence type selector
- Dual range slider for bars between P1 & P2 (5–50)
- Max/min pivot RSI sliders
- RSI rising today toggle (server-side via `require_rsi_rising`)
- Results table with RSI NOW column

**Screen Page:**
- Dynamic filter builder: RSI + Bollinger Bands, all timeframes
- Sortable results table

---

## Current Known Issues
None.

---

---

### Phase 6 — AI Chat ✅

- `LLMChatAgent` — intent detection (SCREEN / QUOTE / FUNDAMENTALS / GENERAL) + dispatch
- NLP helpers: symbol extraction, universe detection, RSI threshold, BB condition, volume condition, LLM-assisted filter extraction (`_llm_extract_filters`)
- Chat history: last 20 messages as LLM context per turn
- `chat_sessions` + `chat_messages` DB tables fully wired
- REST: `POST /chat/sessions`, `GET /chat/sessions`, `POST /chat/sessions/{id}/messages`, `DELETE /chat/sessions/{id}`
- `ChatPanel.tsx` — session management, message history, typing indicator

---

## Next Recommended Task
**Phase 8 — Advanced Analysis**
- Additional indicators: EMA, SMA, ATR, ADX, Stochastic
- Candlestick pattern detection
- Alerts system


---

### TradingView screener integration ✅ (2026-10-02)
- Backend: `services/tv_screener_service.py`, `routes/tv_screener.py` (`/tv/markets|fields|presets|scan`), field catalog JSON in `app/data/tv_fields/` (generated by `scripts/generate_tv_fields.py`), vendored library source in `app/tradingview_screener/` (MIT, v3.2.2; only `requests` added as a dependency)
- Frontend: new "TradingView" tab (`components/TVScreenerPage.tsx`) — 80 markets, ~1,135 stock fields, 1m–1M timeframes, full operator set, presets, CSV export
- Field reference docs: `docs/tradingview_fields/`
- Tests: `backend/tests/tradingview_screener/` (library's own tests, imports rewritten; several hit the live TradingView API) and `backend/tests/test_tv_screener_service.py` (offline service tests). Run: `cd backend && PYTHONPATH=. .venv/bin/python3.12 -m pytest tests/test_tv_screener_service.py tests/tradingview_screener -q` → 53 passed
- Library README kept at `backend/app/tradingview_screener/README.md` (the README test executes its examples)
