# Architecture — AI Fundamental Analysis Platform

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                         │
│              http://localhost:5174                           │
│                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│   │ Stock        │  │ Analysis     │  │ Analysis        │  │
│   │ Selector     │  │ Progress     │  │ Dashboard       │  │
│   │              │  │ (polling)    │  │ (7 tabs)        │  │
│   └──────────────┘  └──────────────┘  └─────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS (proxied by Vite dev server)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                         │
│                   http://localhost:3002                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │
│  │ /api/stocks │  │ /api/fund.. │  │ /api/fundamental/  │  │
│  │ sectors     │  │ analyses    │  │ analyses/{id}/     │  │
│  │ stocks list │  │ POST/GET    │  │ status, report     │  │
│  └─────────────┘  └──────┬──────┘  └────────────────────┘  │
│                           │                                  │
│                    BackgroundTask                            │
│                           │                                  │
│              ┌────────────▼─────────────┐                   │
│              │   Analysis Orchestrator   │                   │
│              │   (pipeline/orchestrator) │                   │
│              │                           │                   │
│              │  Stage 1: Company ID      │                   │
│              │  Stage 2: Data Collect    │                   │
│              │  Stage 3-5: IS/BS/CF      │                   │
│              │  Stage 6: Ratio Calc      │                   │
│              │  Stage 7: Validation      │                   │
│              │  Stage 8: Sector Analysis │                   │
│              │  Stage 9: Peer Compare    │                   │
│              │  Stage 10: Risks          │                   │
│              │  Stage 11: Scoring        │                   │
│              │  Stage 12: AI Analysis    │                   │
│              │  Stage 13: PDF Report     │                   │
│              └────────────┬─────────────┘                   │
│                           │                                  │
│         ┌─────────────────┼──────────────────┐              │
│         ▼                 ▼                  ▼              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Calculation │  │ Sector       │  │ LLM Client       │   │
│  │ Engine      │  │ Framework    │  │ (Groq / GPT-OSS) │   │
│  │ engine.py   │  │ Registry     │  │ llm/client.py    │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Report Service                       │   │
│  │                  (ReportLab PDF)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
  ┌───────────────────┐  ┌──────────────┐  ┌──────────────┐
  │    PostgreSQL     │  │    Redis     │  │   Groq API   │
  │  localhost:5433   │  │ localhost:   │  │ api.groq.com │
  │                   │  │    6379      │  │              │
  │  stocks (750 R/O) │  │ yfinance     │  │ GPT-OSS 20B  │
  │  fa_analyses      │  │ cache (24h)  │  │              │
  │  fa_analysis_     │  │              │  │              │
  │  stages           │  │              │  │              │
  └───────────────────┘  └──────────────┘  └──────────────┘
                  │
          yfinance (external)
          finance.yahoo.com
```

---

## Directory Structure

```
Fundamental screener/
├── PROMPT.md                      ← Original specification (67 sections)
├── IMPLEMENTATION_PLAN.md         ← This phase plan (see Phase 23 for the banking pilot)
├── ARCHITECTURE.md                ← This file
├── AGENTS.md                      ← Agent definitions
├── HOW_TO_RUN.md                  ← Setup and run guide
│
├── backend/
│   ├── .env                       ← Environment variables (secrets)
│   ├── pyproject.toml             ← Python dependencies (uv)
│   ├── alembic.ini                ← Alembic config
│   ├── sector_frameworks/
│   │   └── banking.md             ← canonical banking metric/framework spec
│   ├── banking_stock_analysis_report.md   ← canonical report-rendering spec
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 0001_fundamental_schema.py     ← DB migration
│   │       ├── 0003_metric_data_points.py     ← banking provenance ledger
│   │       ├── 0007_industry_taxonomy.py      ← NSE Industry Classification Structure reference data
│   │       └── 0008_drop_document_chunks.py   ← removes the pgvector RAG table (see "RAG removal" note below)
│   └── app/
│       ├── main.py                ← FastAPI app entry point
│       ├── config.py              ← Pydantic settings from .env
│       ├── logger.py              ← structlog config
│       ├── calculations/
│       │   ├── engine.py          ← MetricsCalculator (all ratios)
│       │   └── scoring.py         ← compute_scores(), data quality
│       ├── data/
│       │   └── yfinance_client.py ← fetch_financial_data()
│       ├── ingestion/              ← banking-pilot data sources, see "Banking Pilot Architecture" below
│       │   ├── bse_client.py, banking_ingestion.py      ← BSE quarterly filings
│       │   ├── nse_client.py, annual_report_ingestion.py, annual_report_locator.py  ← NSE annual reports
│       │   ├── screener_client.py ← Screener.in scraping (openscreener) — standalone + consolidated balance sheets
│       │   └── pdf_ocr.py         ← Tesseract OCR for BSE's scanned filings
│       ├── infrastructure/
│       │   ├── database/
│       │   │   ├── client.py      ← get_db(), get_engine()
│       │   │   ├── models.py      ← Stock (R/O), FundamentalAnalysis, AnalysisStage, MetricDataPoint
│       │   │   └── metric_store.py ← provenance ledger read/write + conflict resolution
│       │   └── redis/
│       │       └── client.py      ← cache_get/set_json()
│       ├── llm/
│       │   └── client.py          ← LLMClient (openai SDK → Groq)
│       ├── pipeline/
│       │   └── orchestrator.py    ← run_analysis_pipeline() — 13 stages
│       ├── reporting/              ← banking HTML/PDF report renderer, see below
│       │   ├── templates/banking_report.html.jinja
│       │   ├── charts.py, data_builder.py
│       │   └── html_report_service.py, pdf_report_service.py
│       ├── routes/
│       │   ├── health.py          ← GET /health
│       │   ├── stocks.py          ← GET /api/stocks/*
│       │   ├── fundamental.py     ← POST/GET /api/fundamental/analyses/*
│       │   └── banking_data.py    ← manual metric entry, provenance history, annual-report batch trigger
│       ├── sectors/
│       │   ├── base.py            ← SectorFramework base class
│       │   ├── registry.py        ← get_framework(sector_name)
│       │   ├── banking_data_bridge.py  ← bridges provenance ledger into BankingSector
│       │   ├── framework_loader.py     ← loads sector_frameworks/*.md into AI prompts
│       │   ├── automobile.py, banking.py, it_services.py, pharma.py, fmcg.py, generic.py, ...
│       │   └── (34 sector files total — see IMPLEMENTATION_PLAN.md Phase 7)
│       └── services/
│           └── report_service.py  ← generate_pdf_report() (ReportLab — non-bank sectors only)
│
└── frontend/
    ├── package.json
    ├── vite.config.ts             ← Port 5174, proxy /api → localhost:3002
    ├── tsconfig.json              ← ES2022 target
    ├── tailwind.config.js
    └── src/
        ├── main.tsx
        ├── App.tsx                ← AppView: home | progress | result
        ├── api.ts                 ← All API calls
        ├── types.ts               ← TypeScript interfaces
        ├── index.css              ← Dark terminal CSS variables
        └── components/
            ├── StockSelector.tsx      ← Sector → stock → analyze
            ├── AnalysisProgress.tsx   ← 13-stage progress view
            ├── AnalysisDashboard.tsx  ← Tabbed result view
            ├── TrendChart.tsx         ← Recharts AreaChart
            └── sections/
                ├── OverviewSection.tsx
                ├── FinancialsSection.tsx
                ├── ScoresSection.tsx
                ├── SectorSection.tsx
                ├── PeerSection.tsx
                ├── RisksSection.tsx
                └── AiSection.tsx
```

---

## Data Flow

### Starting an Analysis

```
User clicks "Analyze Stock"
        ↓
POST /api/fundamental/analyses { stock_id }
        ↓
Backend creates FundamentalAnalysis record (status=QUEUED)
        ↓
FastAPI BackgroundTask launches run_analysis_pipeline(analysis_id, stock_id)
        ↓
Returns { analysis_id } immediately to frontend
        ↓
Frontend navigates to progress screen
        ↓
Frontend polls GET /api/fundamental/analyses/{id}/status every 2 seconds
```

### Pipeline Execution

```
Stage 1: Company Identification
  - Query stocks table for stock_id
  - Store company_info JSON in fa_analyses
  - Mark stage COMPLETED

Stage 2: Financial Data Collection
  - Call fetch_financial_data(exchange, symbol)
  - Check Redis cache first (24h TTL)
  - If miss: fetch from yfinance (finance.yahoo.com)
  - Store in cache + db
  - Mark stage COMPLETED (or FAILED if no data)

Stages 3-5: IS/BS/CF Analysis
  - Currently: instant pass-through (mark COMPLETED)
  - Future: validation agents per statement

Stage 6: Ratio Calculations
  - MetricsCalculator.compute_all() on financial_data
  - Returns dict of 50+ metrics + trend series
  - Store in fa_analyses.metrics JSON

Stage 7: Metric Validation
  - Range checks on key ratios
  - Returns {metric: {status, value, confidence}}

Stage 8: Sector Analysis
  - Detect sector from company_info
  - get_framework(sector) → SectorFramework
  - Banks only: run BSE + NSE ingestion (Redis-gated, ~once/day and
    ~once/year respectively) then inject the resolved provenance-ledger
    values via banking_data_bridge before scoring — see "Banking Pilot
    Architecture" below
  - extract_sector_metrics() → sector-specific values
  - identify_risks() → sector red flags

Stage 9: Peer Comparison
  - Query stocks table for same sector
  - Returns peer list (basic info only for now)

Stage 10: Risk Analysis
  - Universal risk flags (leverage, ROCE, FCF, valuation)
  - Combine with sector risks

Stage 11: Scoring
  - compute_scores(metrics, sector) → 6 category scores + overall
  - compute_data_quality() → 0-100
  - compute_confidence() → 0-100

Stage 12: AI Analysis (non-critical)
  - Build structured JSON context
  - POST to Groq API (GPT-OSS 20B)
  - Parse JSON response
  - Falls back gracefully if LLM fails

Stage 13: Report Generation (non-critical)
  - Banks: HTML (Jinja2 + inline SVG) then PDF-from-HTML via Playwright —
    see "Banking Pilot Architecture" below
  - Everyone else: ReportLab PDF (unchanged)
  - Saves to ./reports/{analysis_id}.{html,pdf,json}
  - Falls back gracefully if generation fails
```

---

## Key Design Decisions

### 1. LLM Never Calculates
All financial ratios are computed by deterministic Python code.
The LLM only receives pre-calculated numbers and provides qualitative interpretation.

### 2. Non-Critical Stage Failures Don't Block
AI analysis (Stage 12) and PDF generation (Stage 13) can fail without failing the whole pipeline. The fundamental analysis result remains complete.

### 3. Shared PostgreSQL, Separate Tables
The FA platform shares the DB but only creates `fa_*` tables. The existing `stocks` table is accessed read-only.

### 4. Frontend Polling, Not WebSockets
The frontend polls `/status` every 2 seconds. Simple and reliable. WebSockets can be added later.

### 5. JSON Blobs vs Normalized Schema
The current implementation stores complex data as JSONB columns (metrics, scores, sector_analysis, etc.). A fully normalized schema (separate tables per financial statement period) is specified in the prompt but not yet implemented.

---

## Banking Pilot Architecture (Session 7, 2026-09-06/07)

A parallel, **Banks-only** architecture layered on top of the generic pipeline above — see
`IMPLEMENTATION_PLAN.md` Phase 23 for the session-by-session build log and what's left. The
generic pipeline (yfinance → deterministic metrics → generic scoring → ReportLab PDF) is
untouched for every other sector; banks get extra stages that fill in what yfinance can't
supply, plus a completely different report renderer.

```
                    Stage 8 (sector_analysis), Banks only
                                    │
        ┌───────────────────────────┼────────────────────────────┐
        ▼                           ▼                             ▼
┌───────────────────┐   ┌───────────────────────┐   ┌─────────────────────────┐
│ BSE quarterly      │   │ NSE annual report      │   │ Screener.in scraping    │
│ filing ingestion    │   │ ingestion               │   │                         │
│                     │   │                         │   │ screener_client.py      │
│ bse_client.py       │   │ nse_client.py           │   │ (openscreener)          │
│ banking_ingestion.py│   │ annual_report_           │   │                         │
│                     │   │  ingestion.py            │   │ Standalone + consol-    │
│ Scanned PDF → OCR   │   │ Real text layer,        │   │ idated balance sheets,  │
│ (pypdfium2+Tesseract)│   │ no OCR needed           │   │ market cap, PEG, etc.   │
│ → Groq LLM extract  │   │ locator.py: densest-    │   │                         │
│                     │   │  window keyword search  │   │                         │
│ Closes: CAR, GNPA,  │   │ → Groq LLM extract       │   │ Not yet wired into      │
│ NNPA, ROA, cost-to- │   │                         │   │ the sector_analysis     │
│ income, credit-cost │   │ Closes: CASA, PCR,      │   │ stage — see "Things     │
│                     │   │ slippage, CET1, Tier1   │   │ worth knowing" below    │
└──────────┬──────────┘   └───────────┬─────────────┘   └────────────┬────────────┘
           │                          │                               │
           └──────────────┬───────────┴───────────────────────────────┘
                           ▼
              fa_metric_data_points (provenance ledger)
              — append-only, never overwritten. Every row: source,
                source_tier, reported_or_calculated, confidence,
                source_url/document/date. Conflicts resolved at read
                time (lowest tier wins, ties broken by recency) via
                metric_store.get_authoritative_value().
                           │
                           ▼
              banking_data_bridge.py — injects resolved values into
              financial_data["_banking_authoritative_metrics"] before
              BankingSector.extract_sector_metrics() runs. Only HIGH/
              MEDIUM confidence values feed the score; LOW-confidence
              (single-quarter OCR approximations) stay visible via the
              provenance API but excluded from compute_sector_score().
                           │
                           ▼
              sector_analysis JSON (same shape as every other sector,
              stored on fa_analyses — this is what the report renderer
              and frontend actually read)
                           │
                           ▼
              Stage 13 (report_generation), Banks only:
              app/reporting/ — Jinja2 + inline-SVG charts + Playwright
              → {analysis_id}.html + {analysis_id}.pdf + {analysis_id}.json
              (everyone else keeps the original ReportLab PDF)
```

### New tables
- **`fa_metric_data_points`** (migration `0003`) — the provenance ledger above.
- **`fa_stock_classification`** (migration `0006`) — every stock's 4-level Screener.in/NSE classification (macro sector → sector → industry → basic industry), backfilled for ~1610 stocks above ₹1000 Cr market cap via `scripts/classify_stocks_screener.py`.
- **`fa_industry_taxonomy`** (migration `0007`) — NSE's official Industry Classification Structure reference data (the taxonomy itself, with definitions — not any company's placement within it).

### New directories
```
backend/
├── sector_frameworks/
│   └── banking.md              ← canonical banking metric/framework spec (moved from repo root)
├── banking_stock_analysis_report.md   ← canonical report-rendering spec (51 sections)
├── app/
│   ├── ingestion/
│   │   ├── bse_client.py / banking_ingestion.py        ← 23B
│   │   ├── nse_client.py / annual_report_ingestion.py  ← 23D
│   │   ├── annual_report_locator.py                    ← 23D (keyword-based page location)
│   │   ├── pdf_ocr.py                                  ← 23B (Tesseract OCR)
│   │   └── screener_client.py                          ← Screener.in scraping (openscreener)
│   ├── reporting/                                      ← 23C
│   │   ├── templates/banking_report.html.jinja
│   │   ├── charts.py, data_builder.py
│   │   ├── html_report_service.py, pdf_report_service.py
│   └── sectors/
│       ├── banking_data_bridge.py                      ← bridges ledger → sector framework
│       └── framework_loader.py                         ← loads sector_frameworks/*.md into AI prompts
```

### Things worth knowing before touching this again
- **NSE reachability is not stable.** It was hard Akamai-blocked (403 on everything) earlier in this project's life, then found fully reachable later the same session. Treat it as flaky, not permanently up or permanently down — every call degrades gracefully (log + skip) rather than assuming access.
- **BSE's `AttachLive` vs `AttachHis` paths**: a filing's PDF lives at `AttachLive` only while it's the single most-recent filing for that scrip; older filings move to `AttachHis`. A stale `AttachLive` link doesn't 404 — it returns HTTP 200 with an HTML error page, so always check the response actually starts with `%PDF`, not just the status code.
- **BSE's announcements API silently drops any date range over ~365 days** — no error, just zero rows. Backfilling years of history means walking backward in ≤360-day windows, not one wide query.
- **Groq's `gpt-oss-20b` spends real "reasoning" tokens even in JSON mode** — a `max_tokens` set too low doesn't truncate gracefully, it fails extraction outright with an opaque empty-body 400. There's also a genuine **daily** token cap (200,000/day on this account), separate from the per-minute limit, that got hit repeatedly during this session's testing.
- **Semantic retrieval (RAG) over annual reports was built, then removed (2026-09-10).** A qwen3-embedding-via-local-Ollama + pgvector pipeline (`app/ingestion/embeddings/`, table `fa_document_chunks`) briefly served as the primary retrieval path ahead of the keyword locator. It was torn out because it added a slow, NSE- and Ollama-availability-dependent indexing step that stalled the pipeline for minutes on every run, and Screener.in scraping now covers most of what it was built to reach, more directly and reliably. `annual_report_ingestion.py` is back to keyword-only retrieval (`annual_report_locator.py`); the `fa_document_chunks` table was dropped (migration `0008`); `pgvector` was removed from `pyproject.toml` (the Postgres image stays on `pgvector/pgvector:pg16` since it's shared with Stock Screener and reverting it isn't worth the risk). Ollama is no longer used anywhere in this project.
- **Screener.in is the likely direction for future data sourcing** — per explicit direction, "most values" going forward should come from Screener.in rather than the BSE-OCR/NSE-annual-report pipelines where possible. `screener_client.py` exists (fetches standalone + consolidated balance sheets) but is not yet wired into the main `sector_analysis` stage — that integration is unscoped as of this note.

---

## Architecture v2 upgrade (2026-09-11 onward)

A staged migration toward `Architecture v2 chatgpt.md`'s (repo root) target platform — metric registry, MCP interface layer, declarative screening, governance/integrity data, historical valuation, source-status tracking, object storage, sector generalization. See the session's plan file for the full staged roadmap and rationale; summarized here are the sources and mechanisms worth knowing about before touching this again.

### Sector-agnostic sources built across this upgrade
- **NSE shareholding pattern** (`app/ingestion/shareholding_client.py`) — promoter/public/pledge % history, any listed company. Powers `shareholding` + `governance_events` (deterministic flags: `PROMOTER_HOLDING_DECLINE`, `PLEDGE_PRESENT`/`PLEDGE_INCREASE`, always evidence-backed).
- **Historical valuation** (`app/ingestion/valuation_history_client.py`) — real historical P/E and P/B per fiscal year, EPS/book-value taken per-field from whichever source has it (Screener.in's `profit_loss()`/`balance_sheet()` first, ~11 years deep; yfinance's annual financials filling gaps, only ~4-5 years deep for Indian stocks — confirmed by direct probe). Genuinely different from `engine.py`'s pre-existing `implied_pe_series()`, which only divides *current* price by historical EPS.
- **Screener.in company summary** (`screener_client.py::ingest_company_summary`) — the `about` description and `key_points` (which for many companies is a real revenue-mix breakdown in prose, e.g. TCS: "BFSI: 31.9%, Consumer Business: 15.4%..."). Stored in `company_summary`, injected into both report renderers' company-overview section (ReportLab `report_service.py` and the banking HTML/PDF `data_builder.py`/`banking_report.html.jinja`).
- **BSE earnings-call transcript** (`app/ingestion/earnings_call_client.py`) — sector-agnostic adapter: any company can file one as a Regulation 30 disclosure on BSE, alongside (not part of) the standard financial-results filing. Real text layer, no OCR — confirmed live on Infosys's Q1 FY27 transcript (exact attrition/utilization/TCV figures in prepared remarks and Q&A). The *adapter* (find/download/durably-store via the `documents` table) is sector-agnostic and runs for every company; the *extraction* is sector-specific and so far only built for IT-services operational KPIs (`attrition_rate`, `utilization_rate`, `deal_wins_tcv` — the three metrics `it_services.py` had declared since the sector framework was written but had zero data source for until now). Other sectors can add their own extraction schema against the same transcript later (e.g. a bank's management commentary on asset-quality outlook) without touching the adapter.
  - **Locator lesson learned**: don't assume KPIs cluster in the first N pages or even in document order among keyword-hit pages — confirmed wrong on Infosys's real transcript (a Q&A-heavy 48-page document where "attrition" isn't in the first 15 pages at all, and "utilization" first appears past character 25,000 of a naive hit-page concatenation). Fixed by ranking hit *pages* by keyword *density* first, then re-sorting the top pages back into reading order — puts the CFO's number-dense recap ahead of a journalist's single passing mention. `_MAX_CHARS` also had to go to 16,000 (vs `banking_ingestion.py`'s 8,000) since even density-ranked transcript text runs longer than one disclosure area's worth of annual-report text.
  - **Generic ledger bridge** (`app/sectors/ledger_bridge.py`) — the other half of making this actually show up. `BankingSector`/`NBFCSector` each have their own `_compute_special_metric` override reading a bridge dict; rather than write another one-off per-sector override for IT, this generalizes the mechanism: `financial_data["_ledger_metrics"]` holds whatever the ledger has for a sector's declared non-yfinance metrics, checked automatically. **Real bug found while wiring this**: `orchestrator.py`'s stage-8 loop that builds the actually-*displayed* `key_metrics` list calls `framework._compute_special_metric()` **directly**, bypassing `SectorFramework.extract_sector_metrics()` (where the ledger-bridge check was first added) entirely — a real `deal_wins_tcv` value on file (HIGH confidence, $3.6bn) still showed N/A until the direct call site itself was fixed to check the bridge too.
- **Source status registry** (`app/sources/registry.py`) — RBI/SEBI/MCA were probed live and found genuinely blocked (RBI: 403 + broken SSL on DBIE; SEBI: search POST trips a WAF; MCA: CAPTCHA-gated, deliberately not bypassed). Rather than build fragile adapters or silently omit them, every known source's reachability (`ACTIVE`/`PARTIAL`/`BLOCKED`/`RESTRICTED`) is recorded with dated notes — `GET /api/sources`, MCP tool `list_data_sources`.
- **Object storage** (`app/infrastructure/storage/minio_client.py`, `documents` table) — MinIO added to the shared `docker-compose.yml`. Closed a real gap: BSE filing PDFs previously only existed in Redis with a 24h TTL and were unrecoverable after that; now every raw source document (BSE filings, NSE annual reports, BSE transcripts) is durably stored with a sha256, queryable via `GET /api/documents/{company_id}`.
- **Third-party analyst consensus** (`analyst_consensus` table) — deliberately **not** part of the `fa_metric_data_points` fact ledger and **never** blended into this platform's own `compute_scores()`/AI rating; every read carries an explicit disclaimer. Architecturally unusual: the backend has no direct HTTP path to the source (IndMoney, only reachable via an MCP connector inside a Claude session) — rows are agent-fetched then `POST`ed in, not pulled by an autonomous backend job like every other source here.

### A second real, pre-existing scoring bug found generalizing to NBFCs
`orchestrator.py` was calling `compute_scores(metrics, sector=sector)` with the **raw, unresolved DB sector string** ("Financial Services" for both banks and NBFCs) instead of `framework.sector_name`. `scoring.py`'s `SECTOR_WEIGHTS` lookup (keyed by the resolved framework name) therefore always missed and silently fell back to `UNIVERSAL_WEIGHTS` — for **every** financial-sector analysis run this entire project, not just NBFCs. Confirmed on real re-runs: Bajaj Finance corrected from 46.2 (WEAK, with false "High Debt-to-Equity"/"Poor Cash Generation" red flags) to 79.4 (GOOD, zero false flags); HDFC Bank corrected from 70.0 (GOOD) to 63.7 (FAIR), now correctly surfacing a real "Low ROE (7.7%)" flag. Fixed at the single call site (`compute_scores(metrics, sector=framework.sector_name)`).

### A real sector-routing bug found the same way
`app/sectors/registry.py`'s alias matching used a naive substring check (`alias in text`), which let `"IT Services"` accidentally match inside `"Credit Services"` — literally "cred**IT SERVICES**" — silently routing NBFCs classified under that real NSE industry tag (15 active stocks, e.g. Bajaj Finance) to the IT framework. Fixed with word-boundary regex matching (`\bit services\b`); `"Credit Services"` also added as a proper `NBFCSector` alias.

### A recurring data-quality bug: implausible OCR values silently outranking correct ones
BSE OCR+LLM extraction misread a percentage by orders of magnitude on three separate occasions (HDFC Bank: 31,173%; Bandhan Bank: 85,922%; Federal Bank: 428,234% — all should have been ~1-2%). Because a garbage value still lands at tier=1, it silently **outranked** a correct tier=2 Screener value in `get_authoritative_value()` — tier is checked before confidence, so even flagging a bad value to LOW confidence (the original one-off fix) doesn't stop it from surfacing in anything that iterates full history rather than just "latest." Fixed at the single chokepoint, `metric_store.insert_metric_value()`: any `%`-unit value with `abs(value) > 1000` is now rejected outright (never inserted, just logged) — the bound is deliberately generous so it only ever catches genuine scale/misread errors, never a legitimate extreme ratio. All ~11 call sites across the ingestion layer updated to handle the new possible `None` return. The 6 existing bad rows were deleted from the ledger (not just re-flagged — they were never real data).

### Yahoo Finance extended fundamental data + local LLM fallback (2026-09-13)
A systematic audit of yfinance's full `Ticker` API surface found a large amount of fundamental data available but unused. Added, all sourced from `app/ingestion/yfinance_extended_client.py` (one module, fully autonomous — no agent-fetch step, unlike `analyst_consensus`'s IndMoney row) and wired into every analysis run regardless of sector:
- **Analyst targets/ratings, own source** — `analyst_consensus` (migration 0012) already supported multiple sources side by side; found and fixed a real bug where the API/MCP tool only ever returned `.first()`, silently dropping whichever source lost the race. Now returns `by_source: {"INDMONEY": {...}, "YAHOO_FINANCE": {...}}`, each with its own disclaimer naming its provider — never merged into one number.
- **`forward_estimates`** — consensus EPS/revenue estimates and growth estimates by period; nothing like this existed before.
- **`insider_activity`** — dated, named insider transactions (distinct from Stage 3's NSE shareholding-pattern aggregate %).
- **`corporate_actions`** — dividend/split history.
- **`company_news`** — recent headlines with source attribution.
- **`earnings_calendar`** — next earnings date + expected EPS/revenue range.
- **`company_summary.governance_risk`** — audit/board/compensation/shareholder-rights/overall risk scores (sparse for Indian stocks in practice — came back empty for Infosys).
- Extra `.info` ratios (`payout_ratio`, `five_yr_avg_div_yield`, `held_pct_insiders`, `held_pct_institutions`, `week52_change`) added to the existing `market` dict. Margins/ROE/ROA/D-E deliberately **not** pulled from `.info` even though Yahoo has them — this app computes those itself from raw statements for consistency. TTM financials were already covered (`ttm_revenue` etc., derived from quarterly data) — no gap there.

**Local Ollama fallback for the LLM client** (`app/llm/client.py`) — Groq's rate limit was hit repeatedly throughout this project, sometimes stalling a pipeline stage for minutes (the SDK's own retry-with-backoff on 429 compounding across several calls). `llm_client.chat()` now catches `openai.RateLimitError` specifically (not any failure — a malformed prompt should still surface as a real error) and falls over to a local Ollama instance (`llama3.2:3b`, confirmed already installed and running) via its OpenAI-compatible endpoint. The primary client's `max_retries` was also dropped to 1 so a stuck call fails over quickly instead of waiting through Groq's full backoff sequence. `last_used_fallback` is exposed (same opt-in pattern as the pre-existing `last_token_count`) for any caller that wants to track when a weaker model served a request — nothing currently downgrades confidence based on it, a natural next step if fallback usage turns out to be frequent.

### Governance/shareholding data wired into the pipeline + Screener supplementary source (2026-09-13)
Stage 3's governance/integrity layer (`shareholding_client.py` — NSE promoter %/public %/pledge %, deterministic event detection) was fully built earlier in this project but never actually called from `orchestrator.py`, so it only had real data for the 2 companies tested manually (Adani Enterprises, HDFC Bank) and nothing for any other analyzed stock — found while auditing what promoter-holdings data the app actually surfaces. Now wired into the same "any sector, fully autonomous" block as the Yahoo Finance extended ingestion, gated by its own 60-day Redis cache key (`shareholding:{stock_id}`), so it runs for every stock on every future analysis.

Also checked whether Screener.in's own shareholding section (`openscreener`'s `Stock.shareholding_quarterly()`/`shareholding_yearly()`) could extend or replace the NSE source. Live-tested on ADANIENT: Screener gives promoter/FII/DII/public % and shareholder count with materially deeper history than NSE's current window (11 years yearly back to Mar 2017 vs NSE's 2022-on; 12+ quarters), plus an FII/DII split NSE's summary API doesn't provide. But Screener has **no pledge % field at all** — confirmed absent from every returned row, and grepping openscreener's entire source tree for "pledg" returned zero hits. Pledge tracking, the single most governance-critical figure, stays exclusively NSE-sourced. Added as a fully separate table (`shareholding_screener`, migration 0016) and ingestion module (`app/ingestion/screener_shareholding_client.py`) so it can never silently blend with or outrank the pledge-bearing NSE row for the same period — same "never blend sources" discipline as `analyst_consensus`. New read paths: `GET /api/governance/{company_id}/shareholding` (NSE, has pledge), `GET /api/governance/{company_id}/shareholding-screener` (Screener, quarterly+yearly, explicit disclaimer that it has no pledge field), MCP tools `get_shareholding` and `get_shareholding_trend_screener`.

No frontend UI surfaces any of this yet (neither NSE nor Screener shareholding data) — still an open gap.

### Dhan + Kite MCP connected, current price, and today's data surfaced in both PDF reports (2026-09-13)
User connected Dhan (`https://mcp.dhan.co/mcp`) and Kite (Zerodha) MCP servers globally (`~/.claude.json`). Audited both: pure brokerage APIs (live quotes/depth, option chain with Greeks for Dhan, historical OHLCV, portfolio/orders/GTT) — **no fundamentals at all**, and critically, **neither is callable from backend code**: their OAuth sessions are scoped to the Claude Code MCP client that authenticated them, not exposed as a reusable API key/token this FastAPI process can call. So "current price" still had to be sourced from what the backend can actually reach.

**`app/ingestion/live_price.py`** (new) — fetches a fresh quote via yfinance's `fast_info` (a single lightweight call, not the full `.info`/statements fetch `fetch_financial_data` already does). Wired into three places, each fetching independently fresh rather than reusing a stale snapshot:
- `orchestrator.py` Stage 1 — stores on `company_info.current_price`, reaching the analysis API and frontend.
- `report_service.py` (generic ReportLab PDF, all non-bank sectors) — refetched at PDF-generation time.
- `data_builder.py` (banking HTML/PDF report context) — same, replacing the old one-time yfinance snapshot that `company.price` used.

Frontend (`AnalysisDashboard.tsx`, `types.ts`) now renders price + change % + as-of time under the company header.

**Real bug found and fixed while adding this**: `report_service.py`'s `title` `ParagraphStyle` used `TEXT_PRIMARY` (`#f1f5f9`, near-white) — clearly designed for a dark canvas background the cover page never actually paints, so the company name was nearly invisible on the real (white) page. The new price line inherited the same broken convention. Both switched to `DARK_NAVY`. Separately, ReportLab's base Helvetica font has no ₹ glyph at all — it rendered as a black box; switched to `Rs. ` text (confirmed via a rendered-page screenshot, not just text extraction, since `pdftotext` alone would have missed the glyph and shown a spacing bug as an actual line overlap on top of it).

**"Everything discussed today" added to both PDF report paths** (previously scattered across REST/MCP only): Ownership & Governance section (NSE shareholding + pledge %, Screener supplementary trend, deterministic governance flags) and Market Intelligence section (analyst consensus by source — still never blended, forward estimates, earnings calendar, corporate actions, recent news) — both sections only render when data exists for that company, never a fabricated empty table. Verified on real generated PDFs (HDFC Bank via the banking Jinja report, TCS via the generic ReportLab report), not just import-level checks.

**Data-quality issue found and fixed**: TCS's rendered "Recent News" section showed headlines about an unrelated company ("Rezolve AI / RZLV") — yfinance's `.news` endpoint has no reliable per-item ticker linkage for Indian stocks (`relatedTickers`/`finance.stockTickers` both came back `None` on every item), so it silently leaks Yahoo's generic market-news feed. Fixed with a deterministic keyword-relevance filter in `ingest_company_news()` — an item is kept only if the company's symbol (word-boundary match) or its suffix-stripped name appears in the title/summary. Found and fixed a real bug in the suffix-stripping regex itself along the way (`\bltd\.?\b` failed to match a trailing "Ltd." because the optional period consumed the word-boundary anchor) before the filter worked correctly. Verified: 9 of 10 TCS items correctly dropped, the 1 genuinely on-topic item kept; re-verified on HDFC Bank with denser coverage to confirm the filter isn't overly strict.

### Llama Report Interpretation Architecture — local-Llama-primary modular narrative pipeline (2026-09-13)
User provided `Sector md files/Summary.md`: existing agents supply verified facts, a **local** Llama model interprets/writes narrative via small modular prompts (not one monolithic call), and a renderer turns a generic Report Blueprint JSON into the PDF — explicitly never an LLM that invents numbers. User confirmed local Llama as **primary** for this pipeline (not just the existing rate-limit fallback), accepting `llama3.2:3b`'s weaker quality for zero rate limits/cost/privacy. Planned as a 4-stage rollout (plan file: staged, additive, `_run_ai_analysis`/`ai_analysis` left completely untouched so nothing regresses if the new pipeline underperforms) and built end-to-end this session:

- **Stage L0 — `app/interpretation/master_object.py` + `context_builder.py`**: assembles Summary.md's §6 object entirely from data that already exists (company_info, metrics, sector_analysis, CompanySummary prose, Shareholding/GovernanceEvent, AnalystConsensus/ForwardEstimate/CorporateAction/CompanyNews — all added earlier today). Genuinely unavailable sections (order book, capacity, capex, structured business segments) are left explicitly `not_available: true`, never fabricated — confirmed by grepping all 34 sector files that these are declared metric IDs with no ingestion behind them anywhere in the app. `context_builder.build_context()` slices the object per report section so each modular prompt gets only what it needs.

- **Stage L1 — local-Llama-primary client + modular prompts**: `app/llm/client.py`'s `LLMClient` gained a `primary` constructor param — `local_llm_client = LLMClient(primary="local")` runs Ollama primary/Groq fallback (any exception fails over, not just `RateLimitError`, since Ollama has no rate-limit concept), alongside the untouched Groq-primary `llm_client`. `app/interpretation/prompts/sections.py` defines 10 short, independent prompts (company snapshot, business model, growth drivers, financial/balance-sheet/cash-flow/valuation interpretation, risk analysis, sector positioning, final conclusion), each carrying Summary.md §17's strict rules. `llama_interpreter.py` calls each independently (one failing never blocks the rest) and assembles the §9 blueprint shape. New `report_blueprint` JSON column (migration 0017), populated by a new orchestrator stage between `ai_analysis` and `report_generation`.
  - **Real reliability finding**: llama3.2:3b would sometimes just echo one raw input dict back verbatim instead of following the schema when a context carried the full unslimmed sector `key_metrics` list (~8 bulky objects with weight/description/na_message noise). Fixed by trimming that list to 5 fields per metric and dropping unavailable ones in `context_builder.py` — went from 8/10 to 10/10 sections reliably generating.

- **Stage L2 — `blueprint_validator.py`**: regex-extracts numeric tokens from generated text, cross-checks each against every number actually present in the master object (recursively, including numbers embedded in prose like `business.about`), drops any section carrying an unrecognized number. **Genuinely caught real hallucinations during testing**: the model reported HDFC Bank analyst targets as ₹58.00/₹94.49 when the real figures were ₹978.00/₹994.49 (dropped digits) — correctly stripped before reaching any report. Also caught the model inventing an unsupported "interest coverage ≈ 78.4x" calculation from unrelated balance-sheet fields it was never asked to compute.
  - **Two real bugs found in the validator itself**, both via false positives on entirely correct generated text: (1) an ISO date like "2023-03-31" was scanned as three numbers via the hyphens (2023, **-3**, **-31**) and correctly-but-wrongly failed grounding — fixed by stripping ISO dates before scanning. (2) A bare number range like "800-1400" (no space) parsed the second number as **-1400** for the same reason — fixed by adding a negative lookbehind so a hyphen directly between two digit runs is never read as a sign, only a separator.
  - **One real semantic bug the validator can't catch by design** (it only checks number grounding, not label correctness): the model cited HDFC's `promoter_pct` (25.59%, real and grounded) as if it were `pledge_pct` (actually `null` for every period on record) — both numbers are real, just mislabeled, so no ungrounded-number check catches it. Fixed with a more explicit prompt instruction (never substitute one field for the other; if `pledge_pct` is null/zero, say so explicitly) — verified fixed across 3 independent regenerations.

- **Stage L3 — rendered into both existing PDF paths**, reusing each report's existing card/table/flag styling rather than building a new renderer: `report_service.py` (ReportLab, all non-bank sectors) gained a "Business & Interpretation" section walking `report_blueprint.sections`; `data_builder.py` + `banking_report.html.jinja` gained the equivalent, positioned as new section "01C" right after Company Overview. **Real Jinja2 bug found**: `{% for item in s.items %}` silently resolved to the dict's built-in `.items()` method (not the `"items"` key) because Jinja2 falls back from failed subscript/attribute access to `getattr` — `s['items']` alone didn't fix it either (`KeyError` on sections without that key triggered the same fallback); only `s.get('items')` sidesteps it correctly. Both PDF paths' disclaimers updated to attribute the new section to the local model explicitly, distinct from the existing Groq-based "AI Fundamental Analysis" section.

Verified end-to-end on two real companies across both sectors and both renderers (HDFC Bank via the banking/Jinja path, TCS via the generic ReportLab path) — screenshotted, not just text-extracted. A real fresh pipeline run (`FA-2026-000032`) confirmed the new `report_blueprint` orchestrator stage integrates correctly between `ai_analysis` and `report_generation`, ~25-35s per company for all 10 local-model calls combined.

Stage L4 (real structured order-book/capacity/capex ingestion from investor presentations, matching Summary.md's own Waaree Energies example) is explicitly deferred, not started — flagged as valuable future work once this pipeline has run in production for a while.

### Three new intelligence engines: P&L, Balance Sheet, Cash Flow — plus score refinement (2026-09-15/16)

User supplied three full engine specs (`Important md files/fundamental_pl_analysis_engine_spec.md`, `balance_sheet_analysis_engine_consolidated.md`, `cash_flow_analysis_engine_standalone.md`), each a large, section-numbered spec of the same shape as `banking_stock_analysis_report.md`. All three were built as separate, additive `app/calculations/<engine>_intelligence/` packages — never touching the pre-existing `pnl_engine.py`/`scoring.py`/`engine.py` calculation paths, per the established "Stage 0 boundary" discipline from earlier sessions (see `pl_intelligence`/`pnl_analysis` distinction above). Each package follows the same internal shape: a single `snapshot.py` DB-reading entry point, every other module a pure function over already-fetched dicts, a `canonical_fields.py` documenting a `STRUCTURALLY_ABSENT` dict of genuinely-unavailable spec items (with a reason string, never a fabricated estimate), a `coverage.py` dependency-graph audit, an `archetype.py`/`red_flags.py` pair that always returns every rule ID (never silently omits one), and a `persistence.py` dual-writing a screenable subset into the existing `fa_metric_data_points` ledger for screener-filter support.

**P&L Intelligence** (`app/calculations/pl_intelligence/`) — margin percentile vs. sector peers, margin headroom to peer-peak, doubling-velocity (revenue vs. PAT), Earnings Quality Index, Cost Structure Resilience, a 5-component weighted Master P&L Score (`M1`-`M5`, `compute_master_score()` in `scoring.py`), 8 rule-based diagnostic flags. `master_pl_score` is 0-100, `classification` one of `PREMIUM_QUALITY_GROWTH_EFFICIENCY_LEADER`/`STABLE_COMPOUNDER_MARGIN_EXPANSION_CANDIDATE`/`HIGH_OVERHEAD_NON_CORE_TRAP_STAGNANT_PERFORMER`.

**Balance Sheet Analysis** (`app/calculations/balance_sheet_intelligence/`) — blends Screener.in (net worth/leverage/archetype/common-size, ~30-50% of the spec's full taxonomy genuinely available) with the existing yfinance-sourced `analysis.metrics` for working-capital ratios (DSO/DIO/DPO/CCC/Current/Quick/Cash Ratio) Screener's condensed balance sheet can't separate out — same "never silently blend, always cross-check" discipline as every other cross-source module in this codebase. 6-way archetype (`STRONG`/`TRANSFORMING`/`MIDDLE`/`WEAK`/`NOT_APPLICABLE` for banks), 12-rule red-flag engine.

**Cash Flow Analysis** (`app/calculations/cash_flow_intelligence/`) — the newest of the three, and the one with the most interesting data-source finding. User asked directly: *"can't we use screener website as primary source of data for all metrics? Are yahoo finance data reliable enough?"* — investigated rather than answered from assumption, and found Screener.in's own "Schedule" expand buttons on its cash-flow table call a **public, undocumented JSON API** (`GET /api/company/{companyId}/schedules/?parent={row}&section=cash-flow[&consolidated=]`, found by reading Screener's own frontend JS bundles, not from any API doc) returning the FULL line-item breakdown behind each of CFO/CFI/CFF — **gross** debt raised/repaid separately (spec §25's own requirement, something yfinance structurally cannot give, only a net issuance figure), receivables/inventory/payables/taxes-paid cash impact, capex/asset-sales/investment-purchases-and-sales/interest-received/dividends-received, already in Crores, ~12 years of history, per statement type. Confirmed live on Maruti and Lenskart. Made **Screener the primary source for this engine**, yfinance kept only as an explicit cross-check (`snapshot.py::yfinance_cross_check()`) — a deliberate, narrow exception to "each package is self-contained": it imports `balance_sheet_intelligence.snapshot.yfinance_value_in_crores()` directly (a generic, already-battle-tested period-format-bridging + Rupees-to-Crores unit-conversion utility, not package-specific business logic). New ingestion: `screener_client.py::ingest_cash_flow_schedules()`, writing `cf_sched_{op,inv,fin}_*` ledger rows alongside the pre-existing `cf_*` top-level totals. Result: this engine's coverage audit reads **84%** available/calculable for Maruti — meaningfully higher than the Balance Sheet engine's ~30-50%, exactly as the richer Screener source predicted. CFO reconciliation bridge (Operating Profit → ± Working Capital → − Taxes → CFO, cross-checked against Screener's own reported CFO), cash bridge (Opening + CFO + CFI + CFF = Closing), CFO/Operating-Profit conversion (the spec's own mandatory headline metric, genuinely new — never computed anywhere in this app before), CFO volatility classification, 7 forensic combination patterns, 5 red-flag rules, 6-way archetype (`CASH_COMPOUNDER`/`CASH_HARVEST`/`GROWTH_REINVESTMENT`/`ASSET_LIQUIDATION_SUPPORTED`/`WORKING_CAPITAL_TRAP`/`DEBT_FUNDED_BUSINESS`/`MIXED`).
**Two real bugs found live-testing against Maruti's actual data**: (1) `build_top_level_series()` was reading ledger keys without the `cf_` prefix `ingest_cash_flow()` actually writes under, so every top-level CFO/CFI/CFF/Net/FCF series silently read empty despite real rows existing — fixed, then verified `computed_cfo` exactly matched `reported_cfo` (19100.0 = 19100.0). (2) The FCF yfinance cross-check used `value_at_fiscal_year()` instead of `yfinance_value_in_crores()` for an absolute-Rupee-figure comparison — same Rupees-vs-Crores unit-mismatch bug class documented in `balance_sheet_intelligence/snapshot.py`'s own docstring from an earlier session, recurring here because a second, independent cross-check call site made the same mistake; caught it producing a 994,094,028% divergence reading (8754 Cr vs. 87,023,000,000 raw Rupees) before the fix.

**Score refinement — the explicit "add these new metrics to the overall score" ask**: rather than reorder the pipeline to compute all three intelligence engines before the existing "scoring" stage (would touch 12 already-tuned stages for no real benefit), a new final orchestrator stage `score_refinement` (after `cash_flow_intelligence_scoring`, both new, at progress 98/99) re-reads `analysis.scores` plus the three engines' already-computed results and blends them into the `profitability`/`balance_sheet`/`cash_flow` category scores via `app/calculations/score_refinement.py`'s `refine_*()` functions — each blend a BOUNDED pull (±10 points max) of the base category score toward a 0-100 "proxy score" derived from that engine's own archetype/conversion-band/volatility/red-flag signals (an engine with no usable signal for a company leaves that category's base score untouched, never pulled toward an arbitrary 50). `overall` is then recomputed via `scoring.py::recompute_overall()` (newly extracted out of `compute_scores()`'s own inline calculation for shared reuse) using the exact same, **unmodified** weight dict `compute_scores()` already chose (`UNIVERSAL_WEIGHTS` or one of the 39 `SECTOR_WEIGHTS` entries — 40 weight dicts total as of 2026-09-23, after adding 4 previously-missing sector entries and a separate valuation-weight-reduction pass; none of them were touched by score_refinement itself). `analysis.scores`/`analysis.overall_score` are overwritten in place with the refined values, plus a new `scores["refinement"]` sub-dict recording every category's base/proxy/adjustment for traceability. **Verified live on Maruti**: overall moved 75.1 → 77.0 (profitability +10.0 capped, balance_sheet +0.7, cash_flow −2.2), each within bound and fully traceable.

**Wired everywhere else the two earlier engines already were**: `master_object.py` (all three now populate the interpretation object), `prompts/sections.py`/`context_builder.py` (5 new `cf_*` LLM narrative sections, mirroring the 5 existing `bs_*`), `app/routes/cash_flow_intelligence.py` (compute-on-read REST surface, `/api/cash-flow-intelligence/{company_id}` + `/coverage`/`/red-flags`/`/archetype`/`/reconciliation` sub-paths, same route-ordering discipline as `balance_sheet_intelligence.py` — specific sub-paths registered before the greedy `{company_id:path}` catch-all), `app/metrics/registry.py` (9 new `cf_*` metric ids) + `app/screening/rules.yaml` (4 new `cf_*` screener filter sets, including a literal gross-debt-repayment screen — resolved from a documented Balance Sheet Engine limitation now that Screener's schedules carry both gross figures separately), a new "Cash Flow" frontend tab (`CashFlowIntelligenceSection.tsx`, modeled on `BalanceSheetIntelligenceSection.tsx`), and a new PDF section ("07 — Cash flow analysis", `equity_report_mapper.py::_cash_flow_intelligence()` + `pdf-renderer/src/index.ts`, reusing the existing `drawWaterfallChart`/`drawMetricGrid`/`drawBulletGroup`/`drawTable` primitives — no new PDF primitive needed; sections 07-14 renumbered +1 from the insertion point).

All three engines' work this session: 286 backend tests (up from the pre-existing suite), `tsc --noEmit` clean on both `frontend/` and `pdf-renderer/`, live-verified end-to-end for Maruti — REST routes, LLM context-builder sections, a live-browser CDP screenshot of the new frontend tab, and a regenerated PDF (`reports/FA-2026-000070.pdf`) with the new section visually confirmed correct.

### Two real ingestion gaps found investigating a user bug report (2026-09-16)

User reported Tata Technologies' Cash Flow tab showing almost all values blank, and separately P&L Intelligence showing "no data." Root cause for both, same class: **Screener ingestion had genuinely never completed for this company's CONSOLIDATED statement type** — confirmed live: `cf_sched_*` (cash-flow schedules) and `pnl_*` (P&L) ledger rows existed for STANDALONE only, zero CONSOLIDATED rows, while the corresponding CONSOLIDATED data demonstrably exists live on Screener.in (probed directly via `openscreener`/the undocumented schedules API — both returned real, complete data on retry). Re-running `ingest_cash_flow_schedules()`/`ingest_pnl_history()` for the company closed the gap immediately (416 rows landed). This is the documented, accepted failure mode of an undocumented, occasionally-rate-limited scrape target — but it exposed two REAL code bugs beyond the missing data itself:

1. **`cash_flow_intelligence/__init__.py`'s statement-type selection only checked whether the TOP-LEVEL `cf_*` series existed**, not whether the SCHEDULE data (`cf_sched_*`) existed under that same statement_type — so it picked CONSOLIDATED (top-level rows existed there) while all schedule-dependent output (CFO bridge, working capital, investing/financing breakdown, conversion) silently read blank, despite real schedule data sitting right there under STANDALONE. Fixed: prefer whichever statement_type has BOTH top-level AND schedule data, falling back to top-level-only (the old behavior) only if neither has schedule coverage.
2. **`pl_intelligence/__init__.py::compute_pl_intelligence()` had no fallback at all** — hardcoded `statement_type="CONSOLIDATED"` with no retry, so a company with STANDALONE-only `pnl_*` data (confirmed to affect more than just Tata Technologies — `test_pnl_engine_existing.py`'s own fixture-choice docstring already flagged TCS as having this exact shape) silently returned an empty result. Fixed: added `allow_fallback: bool = True` (default) that retries the other statement_type when the requested one has no cascade data.

Fixing bug #1 surfaced a THIRD, unrelated bug in `engine.py::calculate_cagr()`: a positive-start/negative-end series (legitimate for cash-flow figures, which can cross zero) made `(end/start) ** (1/years)` raise a fractional power of a negative number — Python doesn't raise here, it silently returns a `complex` number, which then crashed `round()` downstream ("type complex doesn't define __round__") inside `historical_trends.py`. Fixed by extending the function's existing negative/zero-base guard to also cover a negative end value.

Also fixed a genuine data-availability gap in `balance_sheet_intelligence/working_capital.py`: Tata Technologies (an IT-services company with literally no "Inventory" line on yfinance's balance sheet at all — confirmed via direct probe, not a parsing bug) had `inventory_days_series`/`ccc_series` come back entirely empty from yfinance. Screener's `.ratios()` endpoint DOES carry a real value for the latest period (`inventory_days: 0`, a genuine "no inventory" business fact) but the code only used it for cross-check divergence flagging, never as a fallback. Added `single_period_fallback` — when a yfinance SERIES is entirely empty (not just missing the latest point) but Screener has a value, that single point now backfills the flat `*_latest` field, flagged so it's never confused with a full multi-year trend; CCC is re-derived from DIO+DSO-DPO when its 3 inputs become available from either source.

Also added a **Consolidated/Standalone toggle** (`StatementTypeToggle.tsx`, shared across the P&L/Balance Sheet/Cash Flow tabs) — all three `compute_*_intelligence()` functions now accept an explicit `statement_type` override with NO fallback when forced (a user who deliberately picks STANDALONE should see "not available" rather than being silently redirected to CONSOLIDATED), wired through new `?statement_type=` query params on all three REST routes. Per an explicit user instruction, the **PDF deliberately has no such toggle** — it always renders CONSOLIDATED only, via a guard added to each of the three PDF mapper functions in `equity_report_mapper.py` (`if result.get("statement_type") != "CONSOLIDATED": return None` — omits the section entirely rather than silently rendering standalone-sourced numbers unlabeled as if consolidated).

### Screener.in as Primary Source of Truth for `analysis.metrics` (2026-09-16)

User's explicit instruction: *"Make sure Screener website is our primary source for all values. If any value is not available, then we can use yahoo finance and other sources."* Scoped via a clarifying question: the three intelligence engines above were already Screener-primary, but the CORE calculation engine (`engine.py::MetricsCalculator`, feeding the Overall Score, the base Financials tab, and all 34 `app/sectors/*.py` frameworks) was 100% yfinance-based with zero Screener involvement. User chose the maximal scope — rewrite the core engine's sourcing too — explicitly incremental, with live regression checks before merging each step, given the blast radius (every company's `overall_score`, not just a new, separately-displayed section).

**Design**: rather than rewriting `MetricsCalculator` internally (~150 keys, high regression risk to an already-tuned system read by `scoring.py` and all 34 sector frameworks, both confirmed to read `analysis.metrics` by exact key name with no translation layer, and by the frontend's hand-maintained, non-codegen'd `Metrics` TypeScript interface — a renamed key would silently break the UI), a new post-processing layer, `app/calculations/screener_metrics_override.py::apply_screener_primary_overrides()`, overwrites specific `metrics` dict keys IN PLACE after `compute_metrics()` has already run — reusing (never recomputing) `pnl_engine.py`'s and `balance_sheet_intelligence`'s already-computed Screener-sourced values, plus one new ingestion. Every key with no genuine Screener source is left completely untouched, so the original yfinance value silently remains the fallback — "primary source, fallback to yfinance" with zero extra code for the fallback half. **`scoring.py` and all 34 sector frameworks needed zero code changes** — they read the same dict by the same keys regardless of which function last wrote them.

**Critical pipeline-ordering finding**: traced the actual stage order and found the natural-seeming insertion point (right after `compute_metrics()` runs, at the "ratio_calculations" stage) would silently no-op — every Screener ingestion call this override depends on runs later, inside the "sector_analysis" stage's try block. Correct insertion point: inside "sector_analysis," right after the existing `inject_ledger_bridge(...)` call and before `sector_risks`/`key_metrics_list`/`sector_score` are built from `metrics` — since `metrics` is a plain dict reference threaded through the rest of the function, overriding it there means `sector_score`, `key_metrics_list`, `compute_scores()` (the "scoring" stage), and peer comparison all automatically see the overridden values with no other code changes. `analysis.metrics` is re-persisted immediately after the override so the later `pl_intelligence_scoring`/`balance_sheet_intelligence_scoring`/`cash_flow_intelligence_scoring` stages (which re-read it from the DB) don't see stale pre-override values.

**What's overridden** (verified exact formula/key mapping against live code before implementing): `revenue_cagr_3y/5y/10y`, `pat_cagr_3y/5y/10y`, `eps_cagr_3y/5y/10y` (from `pnl_engine.py`'s CAGR windows — same `calculate_cagr()` function both sides already share, a pure source-swap with zero formula difference; only 3y/5y/10y overridden, `pnl_engine.py`'s 7y window has no `engine.py` counterpart key to overwrite), `pat_margin`, `roe`, `interest_coverage` (from `pnl_engine.py` — formulas genuinely differ from `engine.py`'s originals, e.g. ROE uses AVERAGE equity not closing equity; overridden outright anyway, trusting Screener's own number, per the literal reading of "primary source of truth" — not reverse-engineered to match the old formula, which would just invent a third, novel number), `roce`, `debt_to_equity`, `net_debt_to_ebitda` (from `balance_sheet_intelligence`'s `leverage.py`/`roce.py`), `inventory_days`, `receivable_days` (Screener's `.ratios()` latest-period value only — the multi-year `*_series` stay yfinance-sourced for trend, since Screener's ratios endpoint is confirmed latest-period-only), and — found by re-checking a sub-agent's draft against the live code rather than trusting it — `ebitda_margin`/`ebit_margin` (discovered `pl_intelligence/cascade.py` already treats Screener's own "Operating Profit" line as EBITDA and derives EBIT from it, already reused by the leverage/ROCE calls above; wiring these two margins in was then nearly free).

**New ingestion**: `screener_client.py::ingest_company_summary()` extended to also persist `Stock.summary()`'s previously-discarded "top ratios" strip (`sr_*`-prefixed ledger keys: `sr_market_cap`, `sr_pe_ratio`, `sr_book_value`, `sr_dividend_yield`, `sr_current_price`, `sr_face_value`, plus `sr_roce_percent`/`sr_roe_percent` for cross-check only) — reusing the single `summary()` call already made for `about`/`key_points`, not a second scrape. These are snapshot-dated (today's date), not fiscal-year-dated, since P/E and market cap move daily. Feeds `pe_ratio`, `market_cap`, `dividend_yield`, and a derived `pb_ratio` (`sr_current_price / sr_book_value`, anchored to one Screener snapshot rather than mixing Screener book value with yfinance's live price).

**A fourth instance of the Rupees-vs-Crores unit-mismatch bug class, caught before shipping**: the live regression check (run deliberately before merging, per this rollout's own stated policy) showed `market_cap` jumping from ~3.85 trillion to ~386,860 after the valuation override — `sr_market_cap` is ingested in Crores (matching every other `sr_*`/`pnl_*`/`bs_*` ledger row), but `metrics["market_cap"]` is a yfinance-native RAW-RUPEE figure everywhere else in this codebase (confirmed via `AnalysisDashboard.tsx`'s explicit `mc / 1e7` display conversion and `master_object.py`'s `company_info.get("market_cap") or metrics.get("market_cap")` fallback, which only makes sense if both sides share units). Shipping the Crore figure unconverted would have displayed a market cap off by 7 orders of magnitude (e.g. "₹0 Cr" for a real ₹3.86-lakh-Cr company). Fixed: `×1e7` before writing into `metrics["market_cap"]`, same fix pattern as the −364-billion-Capital-Employed and 994,094,028%-FCF-divergence bugs from earlier sessions — this is now the fourth confirmed instance of the same bug class, all caught by the same discipline (live-check real numbers against a known-good reference before trusting a cross-source blend, never just unit-test the arithmetic in isolation).

**Explicitly documented as staying yfinance-only** (no Screener source exists anywhere in this codebase for these, `SCREENER_NOT_AVAILABLE` dict in `screener_metrics_override.py`, mirroring `STRUCTURALLY_ABSENT`'s style): gross margin (no COGS breakdown on Screener), ROA, ROIC + DuPont decomposition, asset turnover, cyclicality analysis, Piotroski F-Score, forward P/E, EV/EBITDA, EV/Sales, PEG ratio, earnings yield, EV/FCF, P/FCF, current/quick/cash ratio (Screener's `.ratios()` structurally has none of these three), implied P/E series, normalized EPS, and the FCF-based ratios (`fcf_yield`/`fcf_margin`/`fcf_to_pat`/`cfo_to_pat`/`fcf_cagr_3y` — `cash_flow_intelligence` has Screener-sourced FCF/CFO but no single-year ratio matching these keys' exact shape yet, deferred as a follow-up).

**Verification discipline**: unit tests for every new function (21 across ingestion + the override module), a live regression check for Maruti + Tata Technologies **before merging each of the 4 implementation milestones** (not just once at the end) — diffing every touched `metrics` key and confirming `overall_score` moved plausibly (a few points, not tens: Maruti 75.1→74.1, Tata Technologies 63.1→63.1 across all four milestones combined) — plus the full `pytest` suite (314 passing) after each step. One live check produced a genuinely positive, unplanned finding: Maruti's yfinance data only spans ~5 years, so its CAGR windows had silently collapsed to an identical value across 3y/5y/10y before the override (a pre-existing, previously-unnoticed data-depth artifact) — Screener's 12-year P&L history now gives genuinely differentiated windows.

Deferred, not in this rollout: cash-flow-ratio overrides (`fcf_yield` etc. — needs new single-year ratio functions `cash_flow_intelligence/conversion.py` doesn't have yet), and revisiting whether `_validate_metrics()` (which currently runs before this override, validating pre-override yfinance values) needs to also run after — not moved preemptively since no live check surfaced a validation-range false positive.

---

## Environment Variables

```env
# backend/.env
API_PORT=3002
DATABASE_URL=postgresql://screener:screener@localhost:5434/screener
REDIS_URL=redis://localhost:6380
LLM_MODEL=openai/gpt-oss-20b
LLM_API_KEY=gsk_...
LLM_API_BASE_URL=https://api.groq.com/openai/v1
REPORTS_DIR=./reports
```

**Note:** ports were originally 5433/6379 but moved to 5434/6380 at some point to avoid a
collision with an unrelated project's containers (`crmplatform-*`) squatting the old ports.
`backend/.env` had drifted and silently pointed at the wrong (unrelated) database for a
while — fixed 2026-09-06. If DB connections ever fail with a password-auth error, check
`docker ps` port mappings against `.env` before assuming credentials are wrong.

---

## Ports

| Service | Port | Notes |
|---------|------|-------|
| FastAPI backend | 3002 | This app |
| Vite frontend | 5174 | This app |
| PostgreSQL | 5434 | Shared with Stock Screener — `pgvector/pgvector:pg16` image (kept even after the RAG removal below, since reverting a shared instance isn't worth the risk) |
| Redis | 6380 | Shared with Stock Screener |
| Stock Screener backend | 3001 | Separate app, do not touch |
| Stock Screener frontend | 5173 | Separate app, do not touch |
