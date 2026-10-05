# How to Run — AI Fundamental Analysis Platform

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | Latest | https://docker.com |
| Python | 3.12+ | via pyenv or homebrew |
| uv | Latest | `brew install uv` |
| Node.js | 18+ | via nvm or homebrew |
| npm | 9+ | comes with Node |

---

## Step 1 — Start Docker (Shared DB + Redis)

The PostgreSQL database and Redis are shared with the Stock Screener app.  
**Do NOT start a separate Postgres** — use the shared one.

```bash
cd "/Users/kishore/Downloads/My personal apps/Stock screener/containers"
docker compose up -d
```

Verify it's running:
```bash
docker ps
# Should see: screener-postgres (port 5434) and screener-redis (port 6380)
```

Check postgres is accepting connections:
```bash
pg_isready -h localhost -p 5434 -U screener
# Should print: localhost:5434 - accepting connections
```

---

## Step 2 — Install Backend Dependencies

```bash
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/backend"
uv sync
```

This creates `.venv` and installs all packages from `pyproject.toml`.

---

## Step 2b — Install PDF Renderer Dependencies

**Run only once** (or when `pdf-renderer/package.json` changes). PDF report
generation runs as a Node subprocess, not in Python:

```bash
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/pdf-renderer"
npm install
```

---

## Step 3 — Run Database Migration

**Run only once** (or when migration files change):

```bash
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/backend"
uv run alembic upgrade head
```

This creates two tables in the shared database:
- `fa_analyses` — stores each analysis run
- `fa_analysis_stages` — stores stage-by-stage progress

**Verify the tables were created:**
```bash
psql -h localhost -p 5434 -U screener -d screener -c "\dt fa_*"
```
Should show `fa_analyses` and `fa_analysis_stages`.

---

## Step 4 — Start the Backend

```bash
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/backend"
uv run uvicorn app.main:app --port 3002 --reload
```

Check it's running:
```bash
curl http://localhost:3002/health
# Should return: {"status": "ok", ...}
```

Check the stocks API works:
```bash
curl "http://localhost:3002/api/stocks/sectors"
# Should return a list of sectors from the DB
```

---

## Step 5 — Install Frontend Dependencies

```bash
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/frontend"
npm install
```

---

## Step 6 — Start the Frontend

```bash
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/frontend"
npm run dev
```

Open: **http://localhost:5174**

---

## Step 7 — Run an Analysis

1. Open http://localhost:5174
2. Select a sector (e.g., "Automobile")
3. Select a stock (e.g., "Tata Motors")
4. Click "Analyze Stock"
5. Watch the 13-stage progress screen
6. When complete (3-5 minutes), review the dashboard
7. Click "Generate PDF Report" or "Download HTML" (the latter is a standalone, interactive replica of this dashboard — same tabs, same charts — that works fully offline once downloaded)

---

## Step 7b — Rebuild the HTML export template (only after frontend changes)

The "Download HTML" button serves a pre-built, self-contained copy of the React app (`backend/app/reporting/templates/export_dashboard_template.html`) with each analysis's data injected at request time. This template is **not** rebuilt automatically — there's no CI or git hook here yet — so if you change `AnalysisDashboard.tsx` or any tab/section/chart component, re-run:

```bash
cd "frontend"
npm run build:export
```

Skipping this after a UI change means the downloaded HTML silently keeps serving the *old* UI against fresh data.

---

## Recent IPOs

Tracks every NSE IPO (from NSE's own `/api/public-past-issues` + `/api/all-upcoming-issues` endpoints — see `backend/app/ingestion/nse_ipo_client.py`), and promotes mainboard (EQ/BE) listings into the stocks universe with a Yahoo-only quick score. SME-board, debt/NCDs, InvITs and REITs are stored in `fa_ipo_issues` for reference but never promoted — they don't fit this app's equity-scoring model.

**Run it manually:**
```bash
cd backend && .venv/bin/python -m scripts.update_ipo_universe
```

**Weekly automatic run (macOS `launchd`):** a job is installed at `~/Library/LaunchAgents/com.fundamentalscreener.ipo-update.plist`, firing every Monday 8am. It only runs while your Mac is on, and needs Docker (Postgres/Redis) already up — if either is asleep/off at trigger time, that week's run just fails silently; the next Monday's run catches up since the whole pipeline is idempotent. Logs land in `backend/cache/ipo_update.log`.

```bash
# check it's loaded
launchctl list | grep fundamentalscreener

# reload after editing the plist
launchctl unload ~/Library/LaunchAgents/com.fundamentalscreener.ipo-update.plist
launchctl load ~/Library/LaunchAgents/com.fundamentalscreener.ipo-update.plist

# remove it entirely
launchctl unload ~/Library/LaunchAgents/com.fundamentalscreener.ipo-update.plist
rm ~/Library/LaunchAgents/com.fundamentalscreener.ipo-update.plist
```

---

## API Routes — Intelligence Engines

Three additive analysis engines (`Important md files/ARCHITECTURE.md`'s "Three new
intelligence engines" section) each expose a compute-on-read REST surface, all mounted
in `app/main.py`. Base analysis fields (`overall_score`, `scores`, etc.) already reflect
these engines automatically — the routes below are for reading an engine's full detail
directly, without needing a whole analysis payload:

```bash
# P&L Intelligence
curl "http://localhost:3002/api/pl-intelligence/NSE:MARUTI"

# Balance Sheet Analysis Engine
curl "http://localhost:3002/api/balance-sheet-intelligence/NSE:MARUTI"
curl "http://localhost:3002/api/balance-sheet-intelligence/NSE:MARUTI/coverage"
curl "http://localhost:3002/api/balance-sheet-intelligence/NSE:MARUTI/red-flags"
curl "http://localhost:3002/api/balance-sheet-intelligence/NSE:MARUTI/archetype"

# Cash Flow Analysis Engine
curl "http://localhost:3002/api/cash-flow-intelligence/NSE:MARUTI"
curl "http://localhost:3002/api/cash-flow-intelligence/NSE:MARUTI/coverage"
curl "http://localhost:3002/api/cash-flow-intelligence/NSE:MARUTI/red-flags"
curl "http://localhost:3002/api/cash-flow-intelligence/NSE:MARUTI/archetype"
curl "http://localhost:3002/api/cash-flow-intelligence/NSE:MARUTI/reconciliation"
```

Each returns `period: null` gracefully (not an error) if that company has no data yet
for the relevant source — re-run the company's analysis to trigger ingestion first.

---

## Configuration

### Backend `.env` file

```bash
cat "/Users/kishore/Downloads/My personal apps/Fundamental screener/backend/.env"
```

Key variables:
```env
API_PORT=3002
DATABASE_URL=postgresql://screener:screener@localhost:5434/screener
REDIS_URL=redis://localhost:6380
LLM_MODEL=openai/gpt-oss-20b
LLM_API_KEY=gsk_...           # Groq API key
LLM_API_BASE_URL=https://api.groq.com/openai/v1
REPORTS_DIR=./reports
```

---

## Troubleshooting

### "Connection refused" on port 5434
Docker is not running. Start Docker Desktop, then:
```bash
cd "Stock screener/containers" && docker compose up -d
```

### "alembic: command not found"
Run with `uv run`:
```bash
uv run alembic upgrade head
```

### "No module named app"
Make sure you're in the `backend/` directory when running uvicorn.

### yfinance returns no data
- Check internet connection
- The stock might be delisted or use a different symbol suffix
- Try manually: `python3 -c "import yfinance as yf; t = yf.Ticker('TATAMOTORS.NS'); print(t.financials)"`

### AI stage fails / LLM error
- Check the Groq API key in `.env`
- The analysis still completes — AI is non-critical
- Check backend logs for the error message

### Frontend shows "API error" on sectors
- Backend is not running. Start it: `uv run uvicorn app.main:app --port 3002 --reload`
- Or Vite proxy is misconfigured. Check `vite.config.ts` — proxy should point to `http://localhost:3002`

---

## Running Tests

```bash
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/backend"
.venv/bin/python3 -m pytest tests/ -v
```

286 tests as of Phase 24 (Session 9) — covering the three intelligence engines
(`pl_intelligence`/`balance_sheet_intelligence`/`cash_flow_intelligence`) and
`score_refinement.py` in depth. The ORIGINAL calculation engine (`engine.py`/
`pnl_engine.py`/`scoring.py`'s pre-existing functions) still has no dedicated test
coverage — see Phase 20 in IMPLEMENTATION_PLAN.md.

---

## Useful Database Queries

```sql
-- Connect
psql -h localhost -p 5434 -U screener -d screener

-- See all analyses
SELECT id, stock_id, status, overall_score, created_at FROM fa_analyses ORDER BY created_at DESC;

-- See stages for an analysis
SELECT stage_name, status, progress, message FROM fa_analysis_stages 
WHERE analysis_id = '<id>' ORDER BY id;

-- Count stocks by sector
SELECT sector, COUNT(*) FROM stocks WHERE is_active GROUP BY sector ORDER BY count DESC;

-- See auto stocks
SELECT id, company_name, symbol FROM stocks WHERE sector = 'Automobile' AND is_active LIMIT 10;
```

---

## Ports Reference

| Service | URL |
|---------|-----|
| This app — frontend | http://localhost:5174 |
| This app — backend | http://localhost:3002 |
| This app — API docs | http://localhost:3002/docs |
| Stock Screener — frontend | http://localhost:5173 |
| Stock Screener — backend | http://localhost:3001 |
| PostgreSQL | localhost:5434 |
| Redis | localhost:6380 |

---

## Quick Restart (all services)

```bash
# Terminal 1 — Docker (if not running)
cd "/Users/kishore/Downloads/My personal apps/Stock screener/containers"
docker compose up -d

# Terminal 2 — Backend
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/backend"
uv run uvicorn app.main:app --port 3002 --reload

# Terminal 3 — Frontend
cd "/Users/kishore/Downloads/My personal apps/Fundamental screener/frontend"
npm run dev
```

---

## Technical screener (merged from the Stock screener app)

The technical screener now runs inside this backend — there is no second
server to start. Its routes are under `/api/technical`:

```bash
curl -s http://localhost:3002/api/technical/health
curl -s http://localhost:3002/api/technical/universes
curl -s -X POST http://localhost:3002/api/technical/macd/scan -H 'content-type: application/json' -d '{"universe_id":"NIFTY_50"}'
```

Code: `backend/app/technical/`. Tests: `backend/tests/technical/`.
Docker services: `containers/docker-compose.yml` in this repo (same containers and volumes as before).
Old-to-new path map: `Important md files/Technical screener/MERGED_INTO_FUNDAMENTAL_SCREENER.md`.

---

## Price store (daily prices for stocks and indices)

Relative strength, drawdown, volatility and the technical score read stored
daily history from two tables instead of calling Yahoo on every request.

| Table | What | Source |
|---|---|---|
| `index_bars_daily` | Every NSE index: open, high, low, close, volume, turnover, P/E, P/B, dividend yield | NSE daily index file `nsearchives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv` |
| `price_bars_daily` | Every active stock: open, high, low, close, adjusted close, volume | Yahoo Finance daily history (adjusted for splits, bonuses and dividends) |

```bash
cd backend
.venv/bin/python -m app.prices.runner              # daily update: only the new days
.venv/bin/python -m app.prices.runner --years 3    # first fill, or a full re-read
.venv/bin/python -m app.prices.runner --check      # compare stored closes with NSE's official bhavcopy
```

The daily update re-reads a stock's whole history when Yahoo has restated it
(split, bonus or dividend). Run it after the market closes; NSE publishes the
day's files in the evening.

API: `/api/prices/status`, `/api/prices/check`, `/api/prices/indices`,
`/api/prices/index/{name}`, `/api/prices/stock/{symbol}`.

Which index each stock is measured against: `backend/app/prices/benchmarks.py`.
Index constituents (33 indices) are loaded by the technical screener's Nifty
ingestion: `curl -X POST "http://localhost:3002/api/technical/admin/nifty/ingest?dry_run=false"`.
