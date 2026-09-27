# Implementation Plan — AI Fundamental Analysis Platform

## Overview

A production-quality single-stock fundamental analysis platform built as a standalone app that shares the existing 750-stock PostgreSQL database with the Stock Screener.

- **Backend**: FastAPI (Python 3.12+) on port **3002**
- **Frontend**: React 18 + Vite + Tailwind on port **5174**
- **Database**: Shared PostgreSQL at `localhost:5433` (Docker)
- **LLM**: GPT-OSS 20B via Groq API

---

## Phase Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Done — reviewed and working |
| 🔶 | Partial — written but needs review/improvement |
| ❌ | Not done |
| 🔍 | In review |

---

## Phase 1 — Inspect Existing Database & Application
**Status: ✅ DONE**

**What was done:**
- Inspected the Stock Screener's PostgreSQL database
- Identified the `stocks` table schema (id, symbol, exchange, company_name, sector, industry, basic_industry, macro_sector, market_cap, market_cap_category, isin, is_active)
- Confirmed ~750 stocks across sectors
- Identified Docker-based PostgreSQL on port 5433 with credentials `screener:screener`
- Confirmed Redis on port 6379

**Key findings:**
- Stock IDs are formatted as `EXCHANGE:SYMBOL` (e.g., `NSE:TATAMOTORS`)
- Sectors include: Automobile, Banking, IT, Pharma, FMCG, etc.
- No existing FA (fundamental analysis) tables — we create them fresh

**Files:**
- `ARCHITECTURE.md` — system map
- `AGENTS.md` — agent definitions

---

## Phase 2 — Database Architecture & Migrations
**Status: ✅ DONE (Session 7)**

**What was done (original):**
- Alembic migration `0001_fundamental_schema.py` — `fa_analyses` + `fa_analysis_stages` tables with JSON blob storage + basic indexes

**What was added (Session 7 — migration `0002`):**
- `fa_analysis_seq` PostgreSQL sequence — replaces race-prone `COUNT+1` ID generation
- `fa_agent_runs` table — per-stage audit trail: `agent_name`, `duration_ms`, `token_count`, `model_used`, `input_summary`, `error`
- `model_version` + `prompt_version` + `cancelled_at` columns on `fa_analyses`
- Composite index `(stock_id, created_at DESC)` for "latest analysis per stock" queries
- `AgentRun` SQLAlchemy model in `models.py`
- `fundamental.py` ID generation uses `nextval('fa_analysis_seq')` — concurrent-safe
- `orchestrator.py` — `_log_agent_run()` helper; wired into Stage 2 (yfinance) and Stage 12 (AI) with duration + token count
- `llm/client.py` — `last_token_count` stored after each call

**Note:** JSON blob storage retained intentionally — normalizing into 20 tables adds complexity with no benefit at this scale (750 stocks, 1 analysis at a time). `fa_agent_runs` provides the audit trail without forcing full normalization.

---

## Phase 3 — Stock Universe Integration
**Status: ✅ DONE**

**What was done:**
- `Stock` SQLAlchemy model mirrors the existing `stocks` table (read-only, `extend_existing=True`)
- API endpoints: `GET /api/stocks/sectors`, `GET /api/stocks?sector=X`, `GET /api/stocks/{id}`
- Frontend populates dropdowns from the DB

**Files:**
- `backend/app/infrastructure/database/models.py`
- `backend/app/routes/stocks.py`

---

## Phase 4 — Financial Data Layer
**Status: ✅ DONE (Session 7)**

**What was done (original):**
- `yfinance_client.py` fetches IS/BS/CF/market data; NSE→.NS / BSE→.BO; Redis 24h cache

**What was added (Session 7):**
- **Expanded row-key variants** — every `_try_keys()` call now tries 4–6 alternative yfinance row names (e.g. "Total Revenue" / "Revenue" / "Net Revenue" / "Revenues") to survive yfinance API changes
- **`_merge_series()`** — merges overlapping series from multiple sources (e.g. D&A from both income stmt and CF stmt)
- **FCF fallback** — `_compute_fcf_from_ocf(ocf, capex)` computes FCF = OCF + CapEx (CapEx is negative in yfinance) when "Free Cash Flow" row is absent
- **Richer quarterly** — now extracts gross_profit, ebit, eps, ocf, capex per quarter; plus `ttm_revenue`, `ttm_net_income`, `ttm_ebitda`, `ttm_ocf` convenience fields (sum of 4 most-recent quarters)
- **`_diagnose()`** — returns `years_available`, `years_count`, `revenue_years`, `bs_years`, `cf_years`, `missing_fields`, `is_stale`, `latest_fy` in every result dict
- **Data quality scoring** (`scoring.py`) — `compute_data_quality()` now incorporates staleness penalty (−15 pts) and missing-field penalty (−5 pts each, max −20); also checks FCF and D/E availability
- **Engine** — `compute_all()` now returns `latest_fy`, `missing_fields`, `data_is_stale`, `fetched_at` from diagnostics
- **`types.ts`** — `Metrics` interface updated with new diagnostic fields

**Files:**
- `backend/app/data/yfinance_client.py` (full rewrite)
- `backend/app/calculations/scoring.py` (`compute_data_quality` enhanced)
- `backend/app/calculations/engine.py` (new diagnostic fields in return dict)
- `frontend/src/types.ts` (Metrics interface updated)

---

## Phase 5 — Deterministic Calculation Engine
**Status: ✅ DONE (Session 7)**

**What was done (original):**
- `MetricsCalculator` with CAGR, margins, ROE/ROCE/ROIC, FCF, debt ratios, valuation ratios, trend direction (linear regression + CV)

**What was added (Session 7):**
- **Bug fix:** `self._fd = data` — `compute_all()` was referencing `self._fd` without it being set, causing `AttributeError` at runtime
- **10Y CAGR:** `revenue_cagr_10y`, `pat_cagr_10y`, `eps_cagr_10y` (uses all available years up to 10)
- **Quick Ratio:** `(Cash + Receivables) / Current Liabilities` — liquidity measure excluding inventory
- **Cash Conversion Cycle:** `CCC = Inventory Days + Receivable Days - Payable Days`
- **Normalized EPS:** 3-year average diluted EPS (mid-cycle approximation)
- **PEG Ratio:** `Trailing P/E / EPS CAGR 3Y` — guards against negative PE/growth
- **Earnings Yield:** `100 / PE` — bond-comparable metric
- **EV/FCF:** `Enterprise Value / FCF` — capital-structure-neutral P/FCF
- **Implied P/E series:** Current price / historical EPS per year → `implied_pe_3y_avg`, `implied_pe_5y_avg`
- **`types.ts`** — all new fields added to `Metrics` interface

**Smoke-tested:** All 12 new metrics compute correctly on synthetic 5-year dataset.

**Files:**
- `backend/app/calculations/engine.py`
- `frontend/src/types.ts`

---

## Phase 6 — Universal Metrics
**Status: ✅ DONE (Session 7)**

**What was added (Session 7):**

**Cyclicality Analysis** (`cyclicality_analysis()`):
- `ebitda_margin_cv` — coefficient of variation of EBITDA margin; `is_cyclical = CV > 0.25`
- `ebitda_margin_peak/trough` — historical max/min EBITDA margin over full data
- `cycle_position` — 0–100 score (0=trough, 100=peak) for current margin vs history
- `roce_peak/trough/cycle_position` — same for ROCE

**Working Capital Cycle Trends** (`working_capital_trends()`):
- `inventory_days_trend`, `receivable_days_trend` — direction-flipped (falling days = IMPROVING)
- `payable_days_trend` — higher payables = better (more supplier credit, not flipped)
- `ccc_trend`, `wc_to_revenue_trend`
- `working_capital_latest`, `wc_to_revenue_latest` (NWC intensity %)

**ROIC Decomposition** (`roic_decomposition()`) — DuPont-style:
- `nopat_margin_latest/3y_avg` — NOPAT / Revenue (after-tax operating margin)
- `capital_turnover_latest/3y_avg` — Revenue / Invested Capital
- `nopat_margin_series`, `capital_turnover_series` — full year-by-year breakdown
- Verification: ROIC ≈ NOPAT Margin × Capital Turnover

All metrics smoke-tested on 7-year synthetic dataset; TypeScript clean.

**Files:** `backend/app/calculations/engine.py`, `frontend/src/types.ts`

---

## Phase 7 — Sector Framework Registry
**Status: ✅ DONE (all 34 sectors, Session 6)**

### Phase 7A: Financial Sector Separation (✅ DONE — Session 5)

**Problem solved:** BankingSector incorrectly included NBFCs and Insurance under one framework.

**What was done:**
- **`base.py`** — Enhanced `SectorMetric` with `thresholds`, `available_from_yfinance`, `na_message`, and `applicable_to` fields. Added `metric_status()` helper and `score_key_metric()` on `SectorFramework`. Added `_piecewise()` for piecewise-linear scoring.
- **`banking.py`** — Complete rewrite: bank-only aliases (no NBFC, no Insurance). 17 metrics: 6 available from yfinance (ROE, ROA, revenue CAGR, PAT CAGR, P/B, P/E), 11 marked `available_from_yfinance=False` (NIM, GNPA, NNPA, PCR, CASA, credit cost, CAR, slippage, cost-to-income). 10 red flags with bank-specific severity.
- **`nbfc.py`** — New file. Base `NBFCSector` with 18 metrics. NBFC-specific leverage thresholds (3-7x normal, not 8-12x banks). Sub-types: `HousingFinanceSector`, `MicrofinanceSector`, `GoldLoanSector` (inheritance-based overrides). Collection efficiency and credit cost as primary red flags.
- **`insurance.py`** — New file. 13 metrics covering GWP growth, combined ratio, loss ratio, expense ratio, solvency ratio, VNB margin, 13-month persistency. Correctly excludes CASA, deposit growth, NPA metrics. 7 red flags.
- **`registry.py`** — Complete rewrite. 2-pass matching (exact first, then alias-in-text). Accepts `sector`, `industry`, `basic_industry` for sub-type disambiguation (e.g. `NBFC + basic_industry="Housing Finance"` → `HousingFinanceSector`). "Financial Services" correctly routes to `Generic` (not bank/NBFC). Exposes `list_frameworks()`.
- **`scoring.py`** — Bank-specific scorers (`_bank_profitability_score`, `_bank_balance_sheet_score`, `_bank_valuation_score`). NBFC-specific scorers. `compute_scores()` dispatches based on `sector`. D/E red flag threshold: 2x industrial / 10x NBFC / 20x banks. Interest coverage threshold: 2x industrial / 1.2x financial.
- **`engine.py`** — Added `roa_series()`, `roa_latest()`, `roa_trend`. `compute_all()` now returns `roa`, `roa_series`, `roa_trend`.
- **`orchestrator.py`** — Stage 8: passes `industry` and `basic_industry` to `get_framework()`. Returns `framework_class`, `available_metric_names`, `unavailable_metric_names`, `sector_weights` in `sector_analysis`. Stage 12 (AI): sector-aware metric context (financial vs industrial). AI prompt includes sector-specific instructions preventing CASA/deposit-growth from appearing in NBFC analysis.

**Architecture achieved:**
```
Financial Services
├── Banks     → BankingSector     (ROE, ROA, NIM, GNPA, CASA, CAR)
├── NBFCs     → NBFCSector        (ROE, ROA, AUM, credit cost, collection efficiency)
│   ├── HousingFinanceSector
│   ├── MicrofinanceSector
│   └── GoldLoanSector
└── Insurance → InsuranceSector   (combined ratio, VNB, solvency, persistency)
```

**N/A handling implemented:**
- Metrics marked `available_from_yfinance=False` do not receive a score of 0 — the scoring engine normalises over available metrics only.
- Bank/NBFC sector scoring bypasses EBITDA margin, asset turnover, FCF/PAT (inapplicable for financial companies).
- `na_message` field tells frontend exactly WHY a metric is N/A.

### Phase 7B: Remaining Sectors (✅ DONE — Session 6)
All 34 sector frameworks now implemented (447 total metrics, 226 red flag rules):
- [x] Auto Ancillaries (`auto_ancillaries.py`, inherits `AutomobileSector`)
- [x] Chemicals / Specialty Chemicals (`chemicals.py` + `SpecialtyChemicalsSector`)
- [x] Metals & Mining (`metals.py` + `MiningSector`)
- [x] Cement (`cement.py`)
- [x] Oil & Gas (`oil_gas.py`)
- [x] Power / Utilities / Renewable Energy (`power.py` + `UtilitiesSector` + `RenewableEnergySector`)
- [x] Telecom (`telecom.py`)
- [x] Retail (`retail.py`)
- [x] Real Estate / Construction / Infrastructure (`real_estate.py`, `construction.py` + `InfrastructureSector`)
- [x] Capital Goods / Industrials / Defence (`capital_goods.py` + `IndustrialsSector` + `DefenceSector`)
- [x] Aviation / Hotels / Logistics / Media (`aviation.py`, `hotels.py`, `logistics.py`, `media.py`)
- [x] Electronics (`electronics.py`)
- [x] Consumer Durables (`consumer_durables.py`)

Also rewritten from stub to full spec: `automobile.py`, `it_services.py`, `pharma.py`, `fmcg.py`.
`registry.py` imports and registers all 34 frameworks in specificity order. `SECTOR_WEIGHTS` in `scoring.py` covers all 35 sector names.

**Files:**
- `backend/app/sectors/` (34 sector files + base, generic, registry)

---

## Phase 8 — Sector-Specific Metric Engines
**Status: ✅ DONE**

**What was done:**
- `_eval_condition(condition, metrics)` added to `base.py` — auto-parses `"metric op value"` strings (all operators: <, >, <=, >=, ==, !=). Base `_check_rule` now auto-evaluates these instead of returning False, eliminating the need to write boilerplate overrides for simple rules.
- `compute_sector_score(metrics, data)` added to `SectorFramework` — weight-normalised average of per-metric piecewise scores. Normalisation over available metrics means N/A fields don't penalise the score.
- Per-metric `score` (0–100) and `status` (EXCELLENT/GOOD/FAIR/POOR) added to every entry in `key_metrics_list` in the orchestrator Stage 8 output.
- `sector_score` field added to `sector_analysis` dict.
- `_compute_special_metric` override added to `ITServicesSector` — derives `revenue_per_employee` (USD k) from `company_info.employees` + latest income statement revenue.
- `SectorAnalysis`, `SectorMetric` interfaces updated in `frontend/src/types.ts`.
- `describe()` already existed in base for all frameworks.

---

## Phase 9 — Validation Agents
**Status: 🔶 PARTIAL**

**What was done:**
- `_validate_metrics()` in orchestrator: basic range checks (EBITDA margin 0-100%, D/E 0-20x, etc.)

**What needs improvement:**
- [ ] Missing-value detection per field
- [ ] Duplicate period detection
- [ ] Sudden unexplained change detection (>50% YoY change)
- [ ] Negative denominator detection
- [ ] Accounting anomaly detection
- [ ] Each metric gets VALID / WARNING / FAILED / NOT_APPLICABLE status with confidence score

---

## Phase 10 — MCP Tool Layer
**Status: ❌ NOT DONE**

The prompt specifies controlled data access through MCP tools. Agents should never touch the DB directly.

**Planned tools:**
- `get_company(stock_id)` → company profile
- `get_financial_history(stock_id)` → multi-year financials
- `get_income_statement(stock_id, year)` → annual IS
- `get_balance_sheet(stock_id, year)` → annual BS
- `get_cash_flow(stock_id, year)` → annual CF
- `get_sector_metrics(sector, metrics)` → sector thresholds
- `get_peer_group(stock_id)` → peer list
- `calculate_metric(name, inputs)` → deterministic calculation
- `validate_metric(name, value, context)` → validation
- `save_agent_result(analysis_id, agent, result)` → persist output

**Note:** MCP is a complex layer. For now, agents call helper functions directly. MCP can be a Phase 10 upgrade.

---

## Phase 11 — A2A Agent Orchestration
**Status: 🔶 PARTIAL**

**What was done:**
- Single `run_analysis_pipeline()` function with 13 sequential stages
- Each stage updates DB state before proceeding
- Non-critical stages (AI, PDF) don't abort the pipeline on failure

**What needs improvement:**
- [ ] Formal A2A message protocol (structured JSON messages between agents)
- [ ] Retry logic per agent (currently no retries)
- [ ] Timeout per agent
- [ ] Agent-run audit table
- [ ] Parallel IS/BS/CF validation (currently faked as instant pass-through)

---

## Phase 12 — Scoring Engine
**Status: 🔶 PARTIAL**

**What was done:**
- `compute_scores(metrics, sector)` with piecewise linear thresholds
- Universal weights + sector weight overrides
- `compute_data_quality()` and `compute_confidence()`

**What needs improvement:**
- [ ] Percentile ranking (vs sector peers)
- [ ] Score component breakdown with metric contributions
- [ ] Red flag scoring penalties
- [ ] Score explanation (what drove the score up/down)

---

## Phase 13 — Peer Comparison Engine
**Status: 🔶 PARTIAL**

**What was done:**
- `_find_peers()` finds up to 10 stocks from the same sector
- Returns peer list with basic info (company name, symbol, market cap)

**Critical gap:**
- Peers have NO financial metrics. The current design just lists peer names. Actual comparison (percentile ranking, sector median, peer ratio tables) requires separate analysis runs or market data API for each peer — this is the hardest part.
- [ ] Implement peer metric fetching (quick yfinance fetch per peer)
- [ ] Sector median calculation
- [ ] Percentile ranking for each metric

---

## Phase 14 — Risk & Catalyst Engine
**Status: 🔶 PARTIAL**

**What was done:**
- `_identify_universal_risks()`: 7 risk checks (leverage, interest coverage, ROCE, FCF, valuation)
- `_identify_catalysts()`: 5 catalyst checks (ROCE trend, FCF, revenue growth, deleveraging, margin expansion)
- Sector risks from framework `identify_risks()`

**What needs improvement:**
- [ ] More risk types (receivables spike, inventory spike, accounting anomalies)
- [ ] Data-quality risks (insufficient data, missing periods)
- [ ] Valuation risks vs historical averages
- [ ] Cyclicality risks
- [ ] Categorize catalysts: Structural / Cyclical / Company-specific

---

## Phase 15 — GPT-OSS 20B Analyst
**Status: 🔶 PARTIAL**

**What was done:**
- `_run_ai_analysis()` builds structured JSON context
- Sends to Groq API (openai SDK) with strict JSON schema
- Fallback defaults if LLM fails
- AI model is configurable via `.env`

**What needs improvement:**
- [ ] Richer context (valuation vs history, cyclicality, peer comparison)
- [ ] Token usage logging
- [ ] Prompt versioning
- [ ] Better fallback when partial data is available
- [ ] Section: "What does the company do?" (requires company description — yfinance provides `longBusinessSummary`)

---

## Phase 16-18 — Frontend
**Status: 🔶 PARTIAL**

**What was done:**
- Stock selector (sector → stock → analyze)
- Analysis progress screen (polls /status every 2s, shows 13 stages)
- Analysis dashboard (7 tabs: Overview, Financials, Scores, Sector, Peers, Risks, AI)
- All 7 section components written
- TrendChart (Recharts AreaChart)
- TypeScript clean (0 errors)

**What needs improvement:**
- [ ] Interactive chart controls (3Y/5Y/10Y toggle, Annual/Quarterly)
- [ ] Ratio table with 3Y avg / 5Y avg / Sector / Trend columns
- [ ] Better peer comparison table with percentile ranking
- [ ] Historical valuation chart
- [ ] Mobile responsiveness review
- [ ] Investor checklist (from AI analysis)
- [ ] Analysis history list improvements

---

## Phase 19 — PDF Report
**Status: 🔶 PARTIAL**

**What was done:**
- ReportLab-based PDF generation
- Cover page, Investment Snapshot, Score Breakdown, Key Metrics, Risks, AI Analysis, Disclaimer

**What needs improvement:**
- [ ] Separate pages per section as spec requires (13 pages)
- [ ] Charts embedded in PDF (ReportLab charts or matplotlib)
- [ ] Professional table formatting
- [ ] Sector analysis page
- [ ] Peer comparison page
- [ ] Investor checklist page
- [ ] Report versioning metadata (analysis_id, model, prompt_version, etc.)

---

## Phase 20 — Tests
**Status: ❌ NOT DONE**

**Planned:**
- [ ] Unit tests for every formula in `engine.py`
- [ ] Sector framework tests
- [ ] Validation agent tests
- [ ] API endpoint tests (pytest + httpx)
- [ ] Edge case tests (zero denominator, missing data, extreme values)

---

## Phase 21 — Performance Optimization
**Status: ❌ NOT DONE**

- [ ] Parallel IS/BS/CF validation
- [ ] DB connection pooling review
- [ ] Redis cache warm-up
- [ ] Background task concurrency limits

---

## Phase 22 — End-to-End Acceptance Test
**Status: ❌ NOT DONE**

**Acceptance criteria (from Section 66 of PROMPT.md):**
- Select Sector = Automobile
- Select an existing automobile stock
- Click Analyze
- Analysis ID created
- Pipeline completes all 13 stages
- Dashboard shows all sections
- PDF generated
- PDF viewable/downloadable
- Analysis saved in PostgreSQL

---

## Phase 23 — Banking Pilot: Provenance Ingestion, RAG & Report Renderer
**Status: 🔶 PARTIAL (Session 7, 2026-09-06/07) — see ARCHITECTURE.md "Banking Pilot" section for the full diagram**

Scoped to **Banks only**, deliberately not generalized to the other 33 sectors yet — proves the pattern on one sector before deciding whether/how to extend it. Plan file used for this work: `~/.claude/plans/fizzy-nibbling-lantern.md` (multiple sub-plans across the session).

### 23A: Provenance ledger (✅ DONE)
New `fa_metric_data_points` table (migration `0003`) — an append-only ledger for sector metrics yfinance can't supply. Every row carries `source`, `source_tier`, `reported_or_calculated`, `confidence`, `source_url/document/date`, `calculation_formula`. Conflicting values from different sources are never overwritten; `app/infrastructure/database/metric_store.py::get_authoritative_value()` resolves by lowest tier, tie-broken by most recent retrieval. Manual override + full history API: `app/routes/banking_data.py`.

### 23B: BSE quarterly-filing ingestion (✅ DONE)
`app/ingestion/bse_client.py` + `banking_ingestion.py`. NSE was Akamai-blocked from this dev environment when this was built (later found reachable again, see 23D) so BSE became the primary automated source. Resolves scrip code → BSE's structured results-snapshot API (CAR%) → locates the actual SEBI-format quarterly results PDF via BSE's announcements feed → **OCRs it** (`pdf_ocr.py`, pypdfium2 + Tesseract — the numbers pages are scanned images, only the cover letter has real text) → LLM-extracts (Groq `gpt-oss-20b`) → derives cost-to-income/credit-cost. Backfills ~5 years of quarterly filings per bank (`backfill_bank_history`), gated to run once per company (30-day Redis TTL) since it's slow.
Closes 6 of banking.md's 8 hardest metrics: CAR, GNPA, NNPA, ROA (+ derived cost-to-income, credit-cost).

### 23C: HTML/PDF report renderer (✅ DONE)
Spec: `backend/banking_stock_analysis_report.md` (51 sections, canonical). New `app/reporting/` package — Jinja2 template (`templates/banking_report.html.jinja`) implementing the navy/gold/glass dark design language, hand-rolled inline-SVG charts (`charts.py`, no JS lib so HTML and PDF render identically), `data_builder.py` (pure aggregation, no new "analysis" — groups already-scored metrics into 7 report categories). PDF export via Playwright/headless Chromium (`pdf_report_service.py`) — a true rendered snapshot, not a separate template. `orchestrator.py` stage 13 dispatches by sector: Banks → this renderer, everyone else → the original ReportLab PDF (`report_service.py`), untouched.

### 23D: NSE annual-report ingestion (✅ DONE)
Fills the 3 metrics BSE's quarterly filing genuinely doesn't disclose: **CASA ratio, Provision Coverage Ratio, slippage ratio** (+ CET1/Tier1 as a bonus). NSE reachability flipped from hard-blocked to fully reachable partway through the session (see ARCHITECTURE.md note) — `app/ingestion/nse_client.py` bootstraps via a cookie visit then hits `/api/annual-reports`. Annual reports have a **real text layer** (confirmed on HDFC's 678-page FY2025-26 report) — no OCR needed. `annual_report_locator.py` finds the relevant ~5-25 pages via densest-window keyword clustering (naive first-match picks up MD&A narrative instead of the real notes-to-accounts tables — had to fix this). `annual_report_ingestion.py` runs ~3 targeted LLM extraction calls per report. Batch driver `ingest_all_banks_annual_reports()` (bounded, resumable — one unbounded run would blow the LLM daily quota) exposed at `POST /api/banking/annual-reports/ingest-batch`.
**Verified on real data**: `casa_ratio = 34.1%` extracted from HDFC's actual annual report text, flowed through the full pipeline into the rendered report with correct provenance.

### 23E: Semantic retrieval (RAG) over annual reports (❌ REMOVED, 2026-09-10)
Was: a new `app/ingestion/embeddings/` package replacing exact-keyword page matching with semantic search, using a **locally installed qwen3-embedding model** (served via Ollama at `localhost:11434`, 4096-dim vectors), chunked with configurable before/after context windows, stored in a **pgvector**-backed table `fa_document_chunks` (migration `0004`), retrieved via cosine similarity as the **primary** path ahead of the keyword locator.

**Removed per explicit instruction**: "Completely disseminate the embedding type analysis. It isn't needed anymore. Since we got screener.in website, we can take most values from there for all analysis." It added a slow, NSE- and Ollama-availability-dependent indexing step that stalled the pipeline for minutes on every run (observed directly: a fresh HDFC analysis sat on the `sector_analysis` stage for 5+ minutes waiting on Ollama), and Screener.in scraping now covers most of what it was built to reach, more directly and reliably. Teardown: `app/ingestion/embeddings/` deleted entirely; `annual_report_ingestion.py` reverted to keyword-only retrieval (`annual_report_locator.py`), its module docstring documents why; `DocumentChunk` model removed from `models.py`; `fa_document_chunks` table dropped via migration `0008`; `pgvector` dependency removed from `pyproject.toml` (the shared Postgres image stays on `pgvector/pgvector:pg16` — reverting a shared instance wasn't worth the risk). Ollama is no longer used anywhere in this project. The 23D keyword-based path (`casa_ratio`, `provision_coverage_ratio`, `slippage_ratio`, `cet1_ratio`, `tier1_ratio`) is unaffected and remains the sole NSE annual-report extraction path.

### 23F: Screener.in as a data source (🔶 IN PROGRESS / not yet architecturally scoped)
`app/ingestion/screener_client.py` fetches standalone AND consolidated balance sheets from Screener.in via `openscreener`, tagged by `statement_type` — built, but **not yet wired into the main `sector_analysis` stage or `orchestrator.py`**. Separately, `scripts/classify_stocks_screener.py` backfilled `fa_stock_classification` (4-level NSE taxonomy for ~1610 stocks above ₹1000 Cr market cap) and migration `0007` loaded the official NSE Industry Classification Structure PDF into `fa_industry_taxonomy` — both done, both reference/classification data rather than analysis inputs. The broader pivot implied by the removal above — using Screener.in as a *preferred* source over BSE-OCR/NSE-annual-report for banking metrics generally, not just the 3 gaps those pipelines can't fill — has not been designed or implemented yet.

---

## Phase 24 — P&L, Balance Sheet & Cash Flow Intelligence Engines + Score Refinement
**Status: ✅ DONE (Session 9, 2026-09-15/16) — see `Important md files/ARCHITECTURE.md`'s "Three new intelligence engines" section for full technical detail**

User supplied three engine specs (`fundamental_pl_analysis_engine_spec.md`, `balance_sheet_analysis_engine_consolidated.md`, `cash_flow_analysis_engine_standalone.md`, all in `Important md files/`) and asked for all three built, folded into the existing overall score, and this documentation updated at the end — all three now done.

**What was built**, each a separate additive `app/calculations/<engine>_intelligence/` package (never touching the pre-existing `pnl_engine.py`/`engine.py`/`scoring.py` calculation paths):
- **P&L Intelligence** — sector-percentile margin, margin headroom, doubling velocity, Earnings Quality Index, Cost Structure Resilience, 5-component Master P&L Score (0-100), 8 diagnostic flags.
- **Balance Sheet Analysis** — Screener.in (net worth/leverage/archetype/common-size) blended with yfinance (working-capital ratios), 6-way archetype, 12-rule red-flag engine.
- **Cash Flow Analysis** — primary-sourced from a newly-discovered **undocumented Screener.in JSON API** (their "Schedule" popups' backing endpoint, found by reading Screener's own frontend JS) giving the full CFO/CFI/CFF line-item breakdown including GROSS debt raised/repaid, which yfinance structurally cannot provide. CFO reconciliation bridge, cash bridge, CFO/Operating-Profit conversion (new headline metric), volatility classification, 7 forensic patterns, 5 red flags, 6-way archetype. Coverage audit: 84% available/calculable for Maruti (vs. Balance Sheet's ~30-50%), confirming the richer source.

**Score integration (the explicit "add to overall score" ask)**: a new final orchestrator stage `score_refinement` (`app/calculations/score_refinement.py`) blends each engine's richer signals into the existing `profitability`/`balance_sheet`/`cash_flow` category scores — each blend a bounded (±10 pt) pull toward a 0-100 proxy score, `overall` recomputed via a newly-extracted `scoring.py::recompute_overall()` using the SAME unmodified weight dicts. Verified live on Maruti: 75.1 → 77.0, traceably and boundedly (full breakdown recorded in `scores["refinement"]`).

**Also wired**: LLM narrative sections (`cf_*`, mirroring the existing `bs_*`), a compute-on-read REST route (`/api/cash-flow-intelligence/{company_id}`), 9 new `cf_*` screener-filterable metric ids + 4 new `rules.yaml` filter sets (including a literal gross-debt-repayment screen, resolving a documented Balance Sheet Engine limitation), a new "Cash Flow" frontend tab, and a new PDF section (renumbering existing sections 07-14 to 08-15).

**Verification**: 286 backend tests passing (0 regressions), `tsc --noEmit` clean on `frontend/` and `pdf-renderer/`, live end-to-end run for Maruti across every surface — REST API, LLM context builder, a live-browser CDP screenshot of the new tab, and a regenerated PDF with the new section visually confirmed.

**Files**: `backend/app/calculations/{pl_intelligence,balance_sheet_intelligence,cash_flow_intelligence}/`, `backend/app/calculations/score_refinement.py`, `backend/app/calculations/scoring.py` (`recompute_overall`/`classify_overall_rating` extracted), `backend/app/pipeline/orchestrator.py` (stages 96-99), `backend/app/ingestion/screener_client.py` (`ingest_cash_flow_schedules`), `backend/app/interpretation/{master_object,context_builder}.py` + `prompts/sections.py`, `backend/app/routes/cash_flow_intelligence.py`, `backend/app/metrics/registry.py`, `backend/app/screening/rules.yaml`, `frontend/src/components/sections/CashFlowIntelligenceSection.tsx` + `AnalysisDashboard.tsx`/`api.ts`/`types.ts`, `backend/app/reporting/equity_report_mapper.py` + `pdf-renderer/src/{index,types}.ts`, `backend/tests/test_{cfi_*,score_refinement}.py`.

---

## Phase 25 — Statement-type resilience fixes + Screener.in as Primary Source of Truth
**Status: ✅ DONE (Session 9 continued, 2026-09-16) — see `Important md files/ARCHITECTURE.md`'s "Two real ingestion gaps" and "Screener.in as Primary Source of Truth" sections for full technical detail**

Two follow-up efforts triggered by a live user bug report and a subsequent explicit instruction, both closing out the same session as Phase 24.

**Bug-report follow-up**: user reported Tata Technologies' Cash Flow and P&L Intelligence tabs showing blank/missing data. Root cause: Screener CONSOLIDATED ingestion had never completed for this company (a real, occasional scrape-target gap, fixed by re-ingesting). But diagnosing it surfaced 3 real code bugs: (1) `cash_flow_intelligence`'s statement-type selection only checked top-level series, not schedule data, so it picked a statement_type with real top-level rows but zero schedule rows — fixed to prefer whichever type has BOTH; (2) `pl_intelligence`'s `compute_pl_intelligence()` had no STANDALONE fallback at all (hardcoded CONSOLIDATED) — fixed, and confirmed to also affect other companies (TCS, per an existing test fixture's own docstring); (3) fixing #1 surfaced `engine.py::calculate_cagr()` silently returning a Python `complex` number for a positive-start/negative-end series (legitimate for cash-flow data), crashing `round()` downstream — fixed by extending the function's existing zero/negative-base guard. Also added a genuine Screener-latest-period fallback to `balance_sheet_intelligence/working_capital.py` for Inventory Days/CCC when yfinance's series is entirely empty (Tata Technologies has no "Inventory" line on yfinance at all — a real business fact, not a bug — but Screener's `.ratios()` had the answer and wasn't being used). Added a Consolidated/Standalone toggle to all 3 intelligence tabs (`StatementTypeToggle.tsx`), and — per explicit instruction — made the PDF render CONSOLIDATED only, never a silent standalone substitute (new guard in each of `equity_report_mapper.py`'s 3 section mappers).

**Screener.in as Primary Source of Truth**: user's explicit instruction to make Screener primary for "all values," scoped (via a clarifying question) to include the core `engine.py::MetricsCalculator` — previously 100% yfinance, feeding the Overall Score, the base Financials tab, and all 34 sector frameworks. Rather than rewrite `MetricsCalculator` internally (high regression risk), built a new post-processing layer, `app/calculations/screener_metrics_override.py`, that overwrites specific `analysis.metrics` keys in place after `compute_metrics()` runs, reusing already-computed values from `pnl_engine.py`/`balance_sheet_intelligence` plus one new ingestion (Screener's `summary()` "top ratios" strip — P/E, book value, dividend yield, market cap — previously scraped and discarded). Every key with no Screener source stays untouched (yfinance remains the fallback); `scoring.py` and all 34 sector frameworks needed zero changes, since they read the same dict by the same key names regardless of source. Found and fixed a real pipeline-ordering bug during planning (the natural insertion point would have silently no-op'd, since Screener ingestion for a fresh company completes in a LATER stage than where metrics are first computed) and a 4th instance of the Rupees-vs-Crores unit-mismatch bug class during live verification (Screener's market cap is in Crores, but `metrics["market_cap"]` is a yfinance-native raw-Rupee figure everywhere else in the codebase — caught before shipping via the mandated before-merge live regression check, which showed the figure jumping by 7 orders of magnitude). Shipped incrementally across 4 milestones (P&L overrides → balance-sheet overrides → valuation overrides, ingestion first), each with its own live regression check against Maruti + Tata Technologies confirming `overall_score` moved plausibly (a few points, not tens) before the next milestone started.

**Verification**: 314 backend tests passing (up from 297), live regression checks for Maruti + Tata Technologies before each of the 4 milestones, full `pytest` suite green throughout.

**Files**: `backend/app/calculations/screener_metrics_override.py` (new), `backend/app/calculations/cash_flow_intelligence/__init__.py` (statement-type selection fix), `backend/app/calculations/pl_intelligence/__init__.py` (STANDALONE fallback), `backend/app/calculations/engine.py` (`calculate_cagr` negative-end guard), `backend/app/calculations/balance_sheet_intelligence/working_capital.py` (`single_period_fallback`), `backend/app/pipeline/orchestrator.py` (override insertion point), `backend/app/ingestion/screener_client.py` (`sr_*` summary-ratios ingestion), `backend/app/routes/{pl_intelligence,balance_sheet_intelligence,cash_flow_intelligence}.py` (`statement_type` query param), `backend/app/reporting/equity_report_mapper.py` (CONSOLIDATED-only PDF guards), `frontend/src/components/StatementTypeToggle.tsx` (new) + the 3 intelligence section components, `backend/tests/test_{screener_metrics_override,screener_summary_ratios_ingestion,engine_calculate_cagr,pl_intelligence_orchestrator}.py` + extensions to `test_cfi_coverage_orchestrator.py`/`test_bsi_leverage_roce_working_capital.py`.

---

## Phase 26 — "Download HTML": standalone, interactive replica of the live dashboard
**Status: ✅ DONE (Session 11, 2026-09-16)**

User asked for an HTML download alongside the existing PDF that has "the exact UI & UX experience" of the web app — all 15 tabs, all metrics, tab-switching and chart interactivity intact, not a re-implementation. Rather than hand-rolling a template (which the PDF and the dormant banking Jinja/Playwright path both already show drifts from the real UI over time), the design reuses the actual `frontend/src/` React code for both builds — the live app and the export are the same components, the only difference is where their data comes from.

**Mechanism**:
- `frontend/export.html` + `frontend/vite.export.config.ts` — a second Vite build entry (via new dependency `vite-plugin-singlefile`) that inlines all JS+CSS into one offline-capable file. Kept fully separate from `vite.config.ts` (whose `manualChunks` vendor-splitting is the opposite of what a singlefile build needs).
- `frontend/src/main.tsx` — one additive runtime branch: if `window.__EXPORT_ANALYSIS__` is a real object (set only by the backend-injected export file, always `undefined` in the normal app), mounts `AnalysisDashboard` directly with it instead of `<App/>`.
- `frontend/src/api.ts` — the single point of change making all 11 data-fetching section components (of 15 total tabs) work identically in both builds with zero edits to any of them: `req()` checks a `window.__EXPORT_BUNDLE__` path-keyed lookup first, falling through to the existing `fetch()` when absent.
- `backend/app/reporting/html_export_service.py` (new) — for a given analysis, calls the 13 backing route functions those 11 sections independently fetch (`premium`, `history-charts`, `company-summary`, 5×`yfinance/*`, `segments`, `brands`, `analyst-consensus`, `broker-reports`, `concall`, plus both `CONSOLIDATED`/`STANDALONE` variants of `pl-intelligence`/`balance-sheet-intelligence`/`cash-flow-intelligence`) directly in-process — no HTTP round-trip against itself — keyed by the exact path string `req()` looks up. Injects that bundle plus the main analysis JSON into the pre-built template (`app/reporting/templates/export_dashboard_template.html`, produced by the new `npm run build:export` script) via two placeholder-token string replacements, `<`-escaped against JSON-in-`<script>` breakage.
- `backend/app/services/full_analysis_service.py` (new) — extracted `_analysis_to_dict`/the `get_analysis` route's company_info patch logic out of `app/routes/fundamental.py` (and `app/mcp/server.py`, a second consumer found only when the test suite caught the broken import) into one shared `get_full_analysis_dict()`, so the export's top-level payload can never drift from what the live `GET /analyses/{id}` returns.
- Route: `GET /fundamental/analyses/{id}/report?format=html` (replacing a pre-existing dead branch that assumed a PDF had already been generated) — unlike the PDF, no separate "generate" step: the export is pure DB reads + string templating (~2.4s cold, confirmed live), so the route generates-and-caches to `reports_dir/{id}.html` on first request, then serves the cached file in ~12ms on subsequent ones.
- UI: a second "Download HTML" link next to "Download PDF" on the dashboard (`AnalysisDashboard.tsx`), always available (no PDF-style ready-gating needed).

**Verified live end-to-end** against the real `FA-2026-000080` (Coforge) analysis: generated via direct Python call, then via the actual HTTP route (both cold-generate and cached-hit paths), then opened the resulting standalone file in a browser (served statically, simulating `file://`) — confirmed all tabs render with real data, tab-switching works, the P&L Intelligence Consolidated/Standalone toggle correctly shows genuinely different embedded data (Master Score 81 vs 88), Cash Flow and Calendar tabs (both backed by independently-fetched, now-embedded data) render correctly, and zero console errors (meaning every `req()` embedded-lookup hit, none silently fell through to a failing live fetch). `tsc --noEmit` clean, full backend suite 322/322 passing.

**Known limitation, not fixed**: `index.html`/`export.html`'s Google Fonts `<link>` tags aren't self-hosted, so the offline file falls back to the CSS's own fallback font stack rather than pixel-identical typography — correct layout and content, just not the exact display font offline. Small, isolated follow-up if it matters (see Next Steps).

**Files**: `frontend/export.html`, `frontend/vite.export.config.ts`, `frontend/src/vite-env.d.ts` (all new); `frontend/src/main.tsx`, `frontend/src/api.ts`, `frontend/src/components/AnalysisDashboard.tsx`, `frontend/package.json` (modified); `backend/app/reporting/html_export_service.py`, `backend/app/services/full_analysis_service.py` (new); `backend/app/routes/fundamental.py`, `backend/app/mcp/server.py` (modified).

---

## Phase 27 — Pine Labs bug report: `single_statement_source` false positive, cache-TTL root cause, BSE annual-report fallback
**Status: ✅ DONE (2026-09-16)**

User reported Pine Labs' Cash Flow tab blank and ROCE/EBIT Margin showing "—" despite the Consolidated/Standalone handling (Phase 25/26-era fix) supposedly covering this. Investigation found the `single_statement_source` heuristic (built for GENUINELY standalone-only companies like Netweb Technologies) **can't distinguish that from a transient CONSOLIDATED ingestion failure** — it saw an empty CONSOLIDATED ledger for Pine Labs and confidently relabeled the incomplete STANDALONE data as "Consolidated," masking the gap instead of surfacing it. Confirmed live: Pine Labs' CONSOLIDATED P&L (8 years) and cash-flow schedules (7 years) genuinely exist on Screener — this is the third company this exact ingestion-gap pattern has hit (after Tata Technologies and Coforge).

**Root cause fixed, not just the symptom**: `orchestrator.py`'s ingestion cache-set was unconditional — a transient CONSOLIDATED-leg failure (network blip, rate limit) got the SAME 24h cache lock as a full success, so the gap persisted until someone manually noticed and re-ingested (as happened 3 times now). New `_has_consolidated_rows()` helper checks the actual returned rows; if CONSOLIDATED rows are absent, the cache TTL drops to 4h (`_CONSOLIDATED_GAP_RETRY_TTL`) instead of 24h, so this self-heals same-day. Applied to all three affected ingestion calls (`ingest_cash_flow_schedules`, `ingest_ratios`, `ingest_pnl_history`).

**BSE added as a secondary annual-report source, per explicit user request**: investigating a separate part of the same report (missing Accrued Expenses/Deferred Revenue), found Pine Labs has ZERO NSE annual-report coverage (only concall/earnings-call transcripts on file) — consistent with it being a very recently-listed company (NSE's annual-report filing requirement lags a fresh listing). User confirmed BSE has it. Found BSE's own undocumented Annual Report API (`api.bseindia.com/BseIndiaAPI/api/AnnualReport_New/w?scripcode=...`, same host `bse_client.py` already uses) by direct probing — confirmed live for Pine Labs (scrip 544606): real FY2025-26 report, 7MB PDF, same text-layer format as NSE's (no OCR needed). `annual_report_ingestion.py::ingest_annual_report()` now tries NSE first (unchanged behavior for the ~everyone-else case), falls back to BSE only when NSE genuinely has nothing (or errors) — `_fetch_nse_annual_report()`/`_fetch_bse_annual_report()` normalize both sources' differently-shaped filing rows into one common return contract, and the resulting `Document` row is correctly tagged `BSE_ANNUAL_REPORT` vs `NSE_ANNUAL_REPORT` for provenance. Verified live end-to-end: BSE PDF downloaded and stored (sha256-checksummed in MinIO, matching the NSE path's contract), locator correctly found the Other Liabilities note's pages (232-234) and ran extraction — came back with no `deferred_revenue`/`accrued_expenses` values for Pine Labs specifically, which is a legitimate "this company's note doesn't disclose these as separate lines" outcome (the extraction mechanism itself works; not every company's disclosure has every line item), not a bug in the new fallback path.

**Verification**: 331 backend tests (up from 325, +6 for the BSE-fallback decision logic), live-verified via a real fresh orchestrator pipeline run for Pine Labs (`FA-2026-000007`) with all 18 stages completing cleanly, and the same for the cache-TTL fix's target companies (re-confirmed Coforge/Tata Technologies/Pine Labs all now resolve to real CONSOLIDATED data). `tsc --noEmit` clean (Peer Positioning scatter chart also gained on-chart name+value labels in the same pass, a separate small UX ask from the same bug report).

**Files**: `backend/app/pipeline/orchestrator.py` (`_has_consolidated_rows`, `_CONSOLIDATED_GAP_RETRY_TTL`), `backend/app/ingestion/bse_client.py` (`find_latest_annual_report`/`download_annual_report`, new), `backend/app/ingestion/annual_report_ingestion.py` (`_fetch_nse_annual_report`/`_fetch_bse_annual_report`, `ingest_annual_report()` restructured), `backend/tests/test_annual_report_bse_fallback.py` (new), `frontend/src/components/charts/PeerScatterChart.tsx`.

---

## Session-by-Session Progress

| Session | What was done |
|---------|--------------|
| Session 1 | Wrote ALL backend + frontend code in one rushed pass (phases 2-19 partially) |
| Session 2 | Wrote section components, fixed TypeScript types, installed deps, saved docs |
| Session 3 | Created documentation files (PROMPT.md, IMPLEMENTATION_PLAN.md, ARCHITECTURE.md, AGENTS.md, HOW_TO_RUN.md). Fixed: duplicate `fcf_yield` in engine.py, EBITDA fallback in yfinance_client.py, sector_analysis structure, peers type mismatch |
| Session 4 | Phase-by-phase code review + bug fixes: calculation engine verified, LLM tested (works), build clean. Fixed: AI prompt aligned with AiSection fields (narrative fields + key_catalysts), risks/catalysts API null→[], scoring engine adds red_flags + sector_matched, CSS --bg-input variable added, PDF report updated with new AI fields, code splitting in vite.config.ts. |
| Session 5 | **Financial sector separation.** Rewrote banking.py (bank-only, 17 metrics), created nbfc.py (18 metrics + HFC/MFI/Gold sub-types), created insurance.py (13 metrics). Enhanced base.py with thresholds/applicable_to/na_message. Rewrote registry.py with 2-pass matching + industry/basic_industry disambiguation. Updated scoring.py with bank/NBFC-specific scorers and sector-aware D/E/IC red flag thresholds. Added ROA to engine.py. Updated orchestrator Stage 8 to pass industry+basic_industry to framework, return available/unavailable metric lists; Stage 12 AI is now sector-aware. |
| Session 6 | **Phase 7B: remaining 20+ sectors.** All 34 sector frameworks implemented (447 metrics, 226 red flags). Rewrote automobile/it_services/pharma/fmcg from stub to full spec; added 17 new sector files (auto_ancillaries, chemicals, metals, cement, oil_gas, power, telecom, retail, real_estate, construction, capital_goods, aviation, hotels, logistics, media, electronics, consumer_durables), several with subclass inheritance (Mining<Metals, HFC/MFI/Gold<NBFC, etc). registry.py and scoring.py updated to cover all 35 sector names. |
| Session 7 | **Banking pilot — provenance ingestion, HTML/PDF renderer, RAG.** See Phase 23 above for full detail. Built: `fa_metric_data_points` provenance ledger; BSE quarterly-filing OCR ingestion (closes CAR/GNPA/NNPA/ROA); premium HTML/PDF report renderer (`app/reporting/`, Jinja2 + inline SVG + Playwright) per new spec `banking_stock_analysis_report.md`; NSE annual-report ingestion (closes CASA/PCR/slippage, real text extraction, densest-window locator); semantic retrieval over annual reports via a locally-installed qwen3-embedding model (Ollama) + pgvector (`app/ingestion/embeddings/`) — switched the shared Postgres image to `pgvector/pgvector:pg16` for this. Also fixed several real bugs found along the way: `backend/.env` pointing at stale/wrong DB ports, a dead `ai_analysis` stage (broken import, silently no-op in every prior run), BSE's `AttachLive`/`AttachHis` stale-link and >365-day-window quirks, Groq's real token-per-day quota. RAG indexing verification was mid-run when the session was paused — see Phase 23E "what's left." |
| Session 8 | **Screener.in integration, NSE taxonomy, RAG removal.** Cloned/verified `openscreener` for Screener.in scraping (`screener_client.py`, standalone+consolidated balance sheets). Authenticated to Screener.in via a persistent WebKit profile (email/password — Google OAuth is blocked for automated browsers). Scraped all ~1625 stocks above ₹1000 Cr market cap from Screener.in; classified 1610 of them into NSE's full 4-level taxonomy into new table `fa_stock_classification` (`scripts/classify_stocks_screener.py`). Loaded NSE's official Industry Classification Structure PDF into new reference table `fa_industry_taxonomy` (migration `0007`, 197 rows, 12 macro sectors). Fixed a real production bug: `metric_store.get_latest_period_value()` was sorting by wall-clock `retrieved_at` instead of fiscal `period`, causing a stale period to surface as "latest" after a non-chronological backfill (surfaced as HDFC Bank showing Gross NPA 31173.32% / Net NPA 8091.74% in the live UI). **Per explicit instruction, completely removed the RAG/embedding system** (Phase 23E above) — `app/ingestion/embeddings/` deleted, `DocumentChunk` model + `fa_document_chunks` table dropped (migration `0008`), `pgvector` dependency removed, `annual_report_ingestion.py` reverted to keyword-only retrieval. Rationale: Screener.in scraping now reaches most of what the RAG system was built to reach, more directly and without the Ollama-availability-dependent stalls. |
| Session 9 | **P&L, Balance Sheet & Cash Flow Intelligence Engines + score refinement, then statement-type resilience fixes + Screener.in as Primary Source of Truth.** See Phase 24/25 above for full detail. Built all three engines as separate additive packages. For Cash Flow specifically: investigated the user's question ("can't we use screener as primary source?") and discovered Screener.in's undocumented cash-flow "schedules" JSON API — richer than yfinance, gives GROSS debt raised/repaid, made it the engine's primary source. Built `score_refinement.py` (the explicit "add to overall score" ask) — a new final orchestrator stage blending all three engines' signals into the existing category scores via a bounded proxy-score pull, `overall` recomputed from the same unmodified weight dicts. Wired LLM narrative sections, a REST route, screener-filter metric ids, a frontend tab, and a PDF section for the Cash Flow engine. Found and fixed 2 real bugs live-testing against Maruti's actual data: a missing `cf_` ledger-key prefix silently emptying every top-level cash-flow series, and a recurrence of the Rupees-vs-Crores unit-mismatch bug class (this time in the FCF yfinance cross-check). **Continued same session**: a live bug report on Tata Technologies (blank Cash Flow/P&L tabs) led to fixing 2 statement-type-fallback bugs, a `calculate_cagr` complex-number crash, and a working-capital single-period-fallback gap, plus a new Consolidated/Standalone frontend toggle and a CONSOLIDATED-only PDF guard. Then, per an explicit "make Screener primary for all values" instruction, built `screener_metrics_override.py` — a new post-processing layer making the CORE calculation engine (previously 100% yfinance) Screener-primary too, shipped incrementally across 4 milestones with a live regression check before each, catching a pipeline-ordering bug during planning and a 4th instance of the Rupees-vs-Crores bug during verification. Updated this file and `ARCHITECTURE.md` throughout to close out the session. |
| Session 10 | **Debt/Equity (and other "lower is better") trend-color bug fix.** User caught a real bug live: Debt/Equity falling (de-leveraging, a GOOD thing) was rendered as "Deteriorating" in red — `debt_trend` fed its raw value series straight into `trend_direction()`, which only knows value UP/DOWN, not business-good/bad. Added a module-level `flip_trend()` helper (`engine.py`, right after `trend_direction()`) and applied it to `debt_trend` and (refactored to reuse the same helper instead of a local duplicate) `working_capital_trends()`'s `inventory_days_trend`/`receivable_days_trend`/`ccc_trend` — `payable_days_trend` correctly stays unflipped since higher payables is the "good" direction there. Broad search confirmed no other unfixed occurrence of the bug pattern, and confirmed the frontend/PDF layers are all dumb metric-agnostic trend→color mappers (no double-flip risk). Added regression tests (`tests/test_engine_flip_trend.py`, 5 tests) — full suite now 322 passing (up from 317). Found and fixed one related frontend bug while checking for double-flip risk: `FinancialsSection.tsx`'s `trendArrow()` (Ratio Table arrows for Debt/Equity, Net Debt/EBITDA, Interest Coverage) only matched lowercase `"improving"`/`"declining"`, but the backend sends `IMPROVING`/`DETERIORATING`/`STRONGLY_IMPROVING`/`STRONGLY_DETERIORATING` — so everything except plain `IMPROVING` silently fell through to a neutral grey arrow; fixed to match the real enum. **Verified live against real data**: `FA-2026-000080` (COFORGE), computed before this fix landed, has D/E falling FY2025→FY2026 (0.1285→0.0752) stored as `STRONGLY_DETERIORATING`; re-running the CURRENT code against that same stored `financial_data` now correctly produces `STRONGLY_IMPROVING`. Confirms the fix is correct on a real company, not just synthetic test data — but also means **all analyses completed before this fix carry the stale/wrong `debt_trend` (and possibly `inventory_days_trend`/`receivable_days_trend`/`ccc_trend`) until re-analyzed** (see Next Steps). |
| Session 11 | **"Download HTML" — standalone interactive replica of the live dashboard.** See Phase 26 above for full detail. User wanted an HTML export alongside the PDF with "the exact UI & UX experience" of the web app; chose the highest-fidelity option offered (an interactive tabbed replica, not a static snapshot) when asked. Built by reusing the actual `frontend/src/` React app for a second, singlefile Vite build (`vite-plugin-singlefile`) fed pre-embedded JSON instead of live `fetch()` calls — one new branch point in `api.ts`'s `req()` keeps all 11 data-fetching section components unchanged. Backend aggregates the 13+6 (statement-type variants) endpoints those sections need directly in-process into one bundle, injects it into a pre-built template, and serves it via `GET .../report?format=html` — generated-and-cached on first request (~2.4s), ~12ms on cache hits, no subprocess. Along the way, extracted `_analysis_to_dict`/`get_analysis`'s patch logic into a new shared `full_analysis_service.py` to guarantee the export's top-level payload can't drift from the live JSON endpoint — this surfaced a second, previously-unknown consumer of the old private function (`app/mcp/server.py`), caught immediately by the existing test suite failing to collect. Verified live end-to-end against the real Coforge analysis: direct call, real HTTP route (both cold and cached paths), and a browser open of the resulting file with tab-switching, the P&L Consolidated/Standalone toggle showing genuinely different embedded scores (81 vs 88), and zero console errors across Overview/P&L Intelligence/Cash Flow/Calendar tabs. |
| Session 12 | **HTML export filename parity + Balance Sheet/Cash Flow data-coverage investigation.** Two follow-ups from the same download flow. (1) The `format=html` branch of `download_report` was returning `FileResponse` with no `Content-Disposition` header at all (the PDF branch always has one) — fixed to match the PDF's exact naming convention, `FA_{symbol}_{analysis_id}.html`. (2) User asked why Persistent Systems' Balance Sheet (45%, 31 metrics) and Cash Flow (32%, 25 metrics, CONSOLIDATED) Intelligence tabs showed such low data coverage. Investigated both with real queries against `fa_metric_data_points`, not guesses — two different root causes: **Balance Sheet's 45% ceiling is genuinely structural**, confirmed by directly querying Screener.in's own balance-sheet API for Persistent live — it has no `inventory` line at all (same class of gap as the already-documented Tata Technologies case), and the other listed gaps (aging buckets, debt maturity schedule, related-party loans, contingent liabilities, gross PPE, accrued-expenses/deferred-revenue split) all require annual-report footnote disclosures this app deliberately doesn't ingest (RAG removed, Session 8) — not a bug. **Cash Flow's 32% was a real, fixable ingestion gap**: `fa_metric_data_points` showed Persistent had `cf_sched_*` (the Screener.in cash-flow "Schedules" data, Phase 24's primary CF source) populated for STANDALONE only, zero CONSOLIDATED rows — confirmed live that Screener.in's CONSOLIDATED schedule data genuinely exists and is fetchable right now (traced the exact failure point: `Stock(consolidated=True).cash_flow()` and company-id resolution both succeed, the schedule fetch itself just never got called/completed during that analysis's original pipeline run). Backfilled directly (`ingest_cash_flow_schedules`) — coverage jumped 32%→84% (CONSOLIDATED) / →80% (STANDALONE), matching Maruti's own documented 84% benchmark exactly. A quick DB-wide audit found this exact one-sided-statement-type gap on 2 of the only 6 companies with any `cf_sched_*` data at all (Lenskart, Netweb) — not a systematic bug (Maruti has full symmetric coverage), just intermittent per-company ingestion misses. Backfilled Lenskart too (both `ingest_cash_flow` — the specific gap already flagged in Next Steps — and `ingest_cash_flow_schedules`), now 80% coverage instead of an empty result. **Netweb's case is different and NOT fixed**: traced to a genuine zero — Screener.in has no CONSOLIDATED financials for Netweb at all (across every metric type, not just cash-flow schedules), consistent with a small, recently-listed company with no subsidiaries to consolidate. Since `fa_metric_data_points` is append-only by design, all backfills just added new rows (old rows untouched) — no destructive changes. Compute-on-read routes mean the fix is live immediately for these 3 companies with zero redeploy or re-analysis needed. |
| Session 13 | **Financials tab visual redesign.** User: "the financials page looks odd." Root causes, found by walking the live page: (1) the bottom "metric group" cards used a 3-column grid with 5 cards, leaving an awkward half-empty trailing row; (2) heavy redundancy — ROCE/ROE/PAT Margin/Gross Margin/EBITDA Margin/FCF-PAT/Debt-Equity/Net-Debt-EBITDA/Interest Coverage were each shown twice (once in the Ratio Table with full current/3Y/5Y/sector/trend context, again as a bare current-value-only line in a group card two sections down); (3) inconsistent card chrome — the top 2 chart cards used the richer `ChartCard`/`card-rich` component while the 4 trend charts below them (PAT/ROCE/FCF/ROE) used plain ad hoc `<div className="card p-4">` markup with a different header style, and the metric-group cards used the same flatter `.card` too, so three different visual treatments appeared on one page. Fixed all three: converted the 4 trend charts to `ChartCard` for one consistent chart family; removed the redundant "Growth" group entirely (100% covered by the CAGR bar chart already at the top) and merged the remaining "Profitability" group's 2 unique metrics (EBIT Margin, ROIC — no 3Y/5Y-average backend fields exist for these, so they couldn't extend the Ratio Table itself) into a reorganized 3-card, redundancy-free grid: **Profitability & Returns**, **Balance Sheet & Efficiency**, **Valuation** — exactly 3 cards, no dangling row, each carrying only metrics not already shown elsewhere on the page. Restyled `MetricTable` to the same `card-rich` glass chrome as the chart cards, added a small colored accent dot per group (gold/sky/orange, matching each group's dominant chart color elsewhere on the page) so the three groups are visually distinct at a glance instead of three identical grey boxes. Also wired `inventory_days_trend`/`receivable_days_trend`/`payable_days_trend` — Session 10's `flip_trend` fix — into the Efficiency group's day-count rows as trend arrows, previously computed but never surfaced in this UI; verified live on Coforge that Receivable Days correctly shows a red down-arrow (slower collection = worse) while Payable Days shows a green up-arrow (more supplier credit = better, correctly NOT flipped). Verified end-to-end in the browser at both desktop and mobile widths (375px) — single-column stacking, ratio table's own horizontal scroll, no console errors — plus `tsc --noEmit` and a full `npm run build` both clean, and `npm run build:export` re-run to keep the HTML-export template (Phase 26) in sync per its own documented rebuild requirement. **Files**: `frontend/src/components/sections/FinancialsSection.tsx` only. |
| Session 14 | **Clean-slate reset, scoped in two rounds.** User: "Remove all the existing analysis documents. Want to start fresh." Given the DB is shared infrastructure and the ask was ambiguous (documents on disk? DB records? the separately-built Screener/BSE/NSE scraping ledger?), asked a clarifying question before touching anything destructive/irreversible. User's answer narrowed scope to disk files only, explicitly excluding DB records and the scraping ledger — deleted all 120 generated report documents (81 PDF/20 HTML/19 intermediate JSON, ~20MB) from `backend/reports/`. User then followed up wanting the DB analysis records cleared too ("still showing" in the Recently Analyzed list) — deleted all 83 `fa_analyses` rows (cascades to `fa_analysis_stages`/`fa_agent_runs` via existing `ON DELETE CASCADE` FKs, confirmed before running) and reset `fa_analysis_seq` to restart at 1. Throughout, left the 19,972-row `fa_metric_data_points` provenance ledger and `fa_stock_classification`/`fa_industry_taxonomy` reference tables untouched, per the user's explicit instruction — future analyses don't need to re-scrape. No code changes. |
| Session 15 | **"Key Points" paywall-text leak.** User spotted Screener.in's own unauthenticated-preview upsell copy ("Please upgrade to premium to read more key insights...") rendered on Netweb Technologies' Summary tab under a "Key Points" heading, as if it were real content. Traced the full path: `openscreener`'s `summary_parser.py` blindly takes `node_text()` of whatever sits in Screener's `commentary` div with no genuine-content check; `ingest_company_summary` (`app/ingestion/screener_client.py`) only overwrites this free-preview text when `_fetch_full_key_points()` (a Playwright login-and-scrape path, requires `SCREENER_EMAIL`/`SCREENER_PASSWORD`) succeeds — when that fails (no "Read More" section, a smaller company like Netweb) the paywall copy from the free preview was silently kept and persisted as if genuine. Fixed with a new `_is_key_points_paywall()` guard (matches `"upgrade to premium"`, case-insensitive) applied at both points `key_points` gets set in `ingest_company_summary`, so future ingestion runs store `None` instead of the boilerplate — `about` (a separate field) is unaffected, so the rest of the Summary tab still renders normally. Per the user's explicit instruction ("visible only if you can fetch, otherwise remove the section completely"), added the identical check frontend-side too (`SummarySection.tsx`) as a second, independent guard, and fixed the `hasSummary` computed flag so a paywall-only `key_points` with no `about` doesn't leave the tab looking blank instead of showing its proper "no summary available" empty state. **Backfilled 7 already-affected companies** (Maruti, Coforge, Ather Energy, Tata Motors, Ashok Leyland, Netweb, Tata Technologies — found via `key_points ILIKE '%upgrade to premium%'`, not assumed) by nulling the stored junk directly; verified live on Netweb and Coforge that the section is now gone entirely rather than showing an empty card. `tsc --noEmit` and full backend suite (322 passing) both clean; `npm run build:export` re-run to keep the HTML export template in sync. **Files**: `backend/app/ingestion/screener_client.py`, `frontend/src/components/sections/SummarySection.tsx`. |
| Session 16 | **Collapse Consolidated/Standalone when only one genuinely exists.** Follow-up to Session 15's Netweb investigation: user asked why P&L/Balance Sheet/Cash Flow Intelligence all showed "no consolidated data — try the other statement type" for Netweb and (per a live audit) Bandhan Bank, and whether Screener.in was malfunctioning. Confirmed live against Screener.in directly (not just the DB) that it genuinely has 0 consolidated rows for both companies — a real structural fact (no subsidiaries to consolidate), not a scraping bug. User's instruction: when there's no genuine second dataset, stop offering a Consolidated/Standalone choice that doesn't exist — treat the one real dataset as *the* consolidated view and hide the toggle; when both genuinely exist, change nothing. Added `single_statement_source: bool` to all 3 intelligence engines' (`app/calculations/{pl,balance_sheet,cash_flow}_intelligence/`) output — each now probes both statement types upfront using its own pre-existing "has data" signal (P&L: cascade truthy; Balance Sheet: `total_assets` truthy; Cash Flow: top-level `cfo` truthy), and when exactly one side has any data, always resolves to it and labels the output `"CONSOLIDATED"` regardless of what was explicitly requested — critically, the *internal* resolution still uses the real underlying type throughout (peer-percentile lookups, schedule/cascade fetches all stay correctly keyed), only the final output label changes. Genuine both-sided or neither-sided companies get zero behavior change. This one fix automatically repaired two other things with no code changes needed: the PDF's existing `!= "CONSOLIDATED"` guards (`equity_report_mapper.py`, 3 identical sites) were fully **omitting** these sections for Netweb/Bandhan — since the engines now honestly report "CONSOLIDATED", the guards simply started passing (verified live: fresh Netweb PDF regenerated, all 3 sections now present across 26 pages, confirmed via `pdftotext`) — and the HTML export inherited the fix the same way. Frontend: `StatementTypeToggle` (already a single `const toggle = ...` definition reused across every render branch in each of the 3 section components) now renders `null` when `single_statement_source` is true — one line per file. Along the way, discovered and backfilled two more real, unrelated ingestion gaps surfaced by testing: Netweb had zero `pnl_*` ledger rows under *either* statement type (P&L history was simply never ingested for it — `ingest_pnl_history`), and Bandhan Bank was missing top-level + schedule cash-flow data entirely (`ingest_cash_flow` + `ingest_cash_flow_schedules`) — backfilled all three live, closing what would otherwise have remained empty tabs even after the relabeling fix. Existing test `test_falls_back_to_standalone_when_consolidated_has_no_pnl_data` asserted the exact OLD behavior this change supersedes — rewritten (not just patched) to assert the new contract, plus a new test locking in that genuine both-sided companies are unaffected. Verified live in the browser: Netweb's Balance Sheet/P&L/Cash Flow tabs show real data with no toggle at all (confirmed the toggle correctly disappears after the brief loading-state flash); Coforge (a genuine both-source company) still shows a fully working toggle with real, different Consolidated (81) vs Standalone (88) P&L Master Scores. Full backend suite 323/323, `tsc --noEmit` clean, `npm run build:export` re-run. **Files**: `backend/app/calculations/{pl_intelligence,balance_sheet_intelligence,cash_flow_intelligence}/__init__.py`, `backend/app/reporting/equity_report_mapper.py` (comments only), `backend/tests/test_pl_intelligence_orchestrator.py`, `frontend/src/types.ts`, `frontend/src/components/sections/{PlIntelligenceSection,BalanceSheetIntelligenceSection,CashFlowIntelligenceSection}.tsx`. |
| Session 17 | **Generalized NSE annual-report extraction past banking-only: Gross PPE + Other Liabilities breakdown, via Groq (not local Llama).** User proposed a full "Annual Report / Filing Intelligence" architecture (NSE XBRL/MCA XBRL/BSE, embeddings + local Llama) to close the Balance Sheet Intelligence engine's remaining structural gaps. Corrected two premises before building anything: (1) most of "Level 1/2" already existed — Phase 23D's `annual_report_ingestion.py`/`annual_report_locator.py` (NSE PDF + keyword locator + LLM extraction) is exactly this pattern, just banking-only; (2) the proposed embeddings+local-Llama layer is what Session 8 already built and explicitly removed for stalling the pipeline. **Live-tested both before deciding**: downloaded TCS's real FY2025-26 annual report, ran the same real table through local `qwen3-embedding`+`llama3.2:3b` and through the already-integrated Groq `gpt-oss-20b`. Embedding retrieval was inconsistent (correctly ranked the PPE note top on one query, incorrectly ranked a Directors' Report above the real Related Party table on another). Local Llama scored 3/5 on a PPE table with 2 silently-wrong digits (`39277` vs `37277`) — the dangerous failure mode for an app whose whole design principle is "never fabricate a number." Groq scored 4/5 on the same table (clean explainable miss, not digit corruption) and 4/4 on a clean table. User confirmed: go with Groq, build it. **Generalized the existing pattern, not rebuilt it**: added `ppe`/`other_liabilities` keyword areas to `annual_report_locator.py` (already sector-agnostic, zero banking-specific logic) and two new prompts + metric mappings to `annual_report_ingestion.py`, explicitly instructing the sign convention the user flagged (parenthesized values are negative — false for contra-asset magnitudes like accumulated depreciation, which are requested as positive). Moved `orchestrator.py`'s `ingest_annual_report()` call out of the Banks-only block into the universal any-sector section (following an established precedent in the same file for exactly this kind of generalization) — bank-only areas simply find no matching pages for non-bank companies, at no extra cost. Wired the new `gross_ppe`/`accrued_expenses`/`deferred_revenue` metrics out of `coverage.py`'s permanent `_ALWAYS_ABSENT` bucket into real dependency-based AVAILABLE/MISSING_INPUT resolution (with a new `_ANNUAL_REPORT_SOURCED` reason-text dict distinguishing "not yet ingested" from the 6 still-genuinely-structural gaps), and fetches the 4 new ledger values into `compute_balance_sheet_intelligence()`'s `coverage_facts` + surfaces them in the `assets`/`liabilities` output dicts. **Found and fixed 2 more real bugs live-testing against TCS's actual report** (not synthetic fixtures): the locator's initial `other_liabilities` keyword list included generic terms ("deferred revenue", "accrued expenses") that were scattered across unrelated related-party disclosure pages and won the densest-window contest over the one page with the real note — tightened to the specific heading phrases only, confirmed live this now lands on the correct page. And the initial prompt let Groq relabel a bare "Others" line as the more-specific `accrued_expenses` field on a second run of the *identical* input (same number, different — wrong — field) since the schema invited it to fill every field; tightened the prompt to require an explicit synonym match, confirmed deterministic across 3 repeated runs afterward. **One gap knowingly NOT closed**: TCS's real PPE schedule page has its text stored in reverse character order in the PDF itself (confirmed: `pdfplumber` extracts "772,73" where Poppler's `pdftotext` correctly reads "37,277") — a genuine document-level rendering quirk, not an extraction-code bug. A per-line-reversal heuristic recovers it on this one page, but with only one confirmed example to calibrate a detector against, shipping an untested auto-correction risked silently corrupting some other, genuinely-normal page's text — left as an honestly-reported `MISSING_INPUT` gap (new reason text explaining why) rather than risk a wrong number. **Verified end-to-end on real data, not mocks**: `deferred_revenue=694` (INR crore) now correctly ingests, resolves to `AVAILABLE`, and surfaces in `liabilities.deferred_revenue` for TCS — `accrued_expenses`/`gross_ppe` correctly show the new honest `MISSING_INPUT` reasons instead of the old permanent `SOURCE_REQUIRED`. Full backend suite 325/325 (2 new coverage tests added), `tsc --noEmit` clean (frontend needed no changes — it already renders `assets`/`liabilities` and coverage gaps generically). |
| Session 18 | **Session 17 follow-up: Coforge backfill surfaced a second, more dangerous extraction bug — Gross PPE disabled, Other Liabilities hardened.** User reported Coforge's Balance Sheet coverage still showed 45% with `gross_ppe`/`accrued_expenses`/`deferred_revenue` still listed as gaps — the new pipeline only runs during a *fresh* analysis, and Coforge's existing one predates Session 17's build. Backfilling it live surfaced real, company-specific generalization gaps the single-company TCS validation hadn't caught: (1) Coforge's PPE/Other-Liabilities note headings use completely different phrasing than TCS's ("15 Other liabilities" vs "Other liabilities – Current"), so the locator's TCS-tuned keyword terms matched nothing; (2) once broadened, the densest-window selection (tuned for the original banking areas at window=20) let an isolated, correct 1-2 page note lose to a wider spread of thin, unrelated mentions — fixed with a new per-area `_AREA_PEAK_ONLY` selection (single highest-hit page + tight ±1 margin, bypassing windowing entirely) for these two areas, confirmed correct on both TCS and Coforge; (3) widening the char budget to compensate (40,000 chars) immediately hit a **hard, previously-undocumented constraint**: this Groq account has an 8,000-tokens-per-minute cap — explaining in hindsight why the original banking-only `_MAX_CHARS_PER_AREA=8000` was chosen — dialed back to a per-area 12,000-char override, safe under the cap once the peak-only selection stopped needing more anyway. **The more important finding**: even after all three fixes, a live production run of `ingest_annual_report()` for Coforge returned a fully-populated, plausible-looking Gross PPE result that was silently wrong — `gross_block_opening`/`closing` were correct (7894/8132) but `accumulated_depreciation_closing`/`net_carrying_amount` were the PRIOR year's closing figures (3693/4201) rather than the requested year's (4171/3961), traced to the same "table has two side-by-side year blocks with identically-labelled rows" confusion already documented for TCS's reversed-text case, just manifesting as wrong-year instead of wrong-digit this time — and this particular call had silently fallen back from Groq to local Llama mid-run after hitting the rate limit from the session's own repeated testing, reinforcing Session 17's own finding that the fallback model is measurably less reliable. Deleted the bad rows immediately. Given a metric that's SOMETIMES silently wrong is strictly worse than one that's honestly `MISSING_INPUT` always, **disabled Gross PPE from storage entirely** (removed its `_AREA_METRIC_FIELDS` entry — `ingest_annual_report()` no longer even attempts the LLM call for it, saving quota on a call that isn't trustworthy yet) while leaving the prompt/locator code in place as documented, inert groundwork for a future fix. **Other Liabilities (`deferred_revenue`) is now the one shipped, working win** — validated correct and reproducible on two real companies with genuinely different note formats: TCS (`694`) and Coforge (`158`, cross-checked by hand against the source table: Contract liabilities 158 + Statutory dues 1045 = the note's own disclosed split). Verified live via the actual running API (not a direct function call, which was found to under-report coverage by omitting the yfinance cross-source blend a real request includes): Coforge's Balance Sheet coverage moved from 45.2% → 48.4% for both Consolidated and Standalone, `deferred_revenue` reads `AVAILABLE` with value `158.0`, `accrued_expenses`/`gross_ppe` correctly show the new honest `MISSING_INPUT` reason instead of the old blanket `SOURCE_REQUIRED`. Full backend suite 325/325 throughout. **Files**: `backend/app/ingestion/annual_report_locator.py`, `backend/app/ingestion/annual_report_ingestion.py`. |

---

## Next Steps (Priority Order)

1. **Session 11 follow-up** → the HTML export's fonts aren't self-hosted (see Phase 26 "Known limitation") — opened offline it falls back to the CSS fallback stack instead of Fraunces/Inter; self-hosting both families as base64 `data:` URIs in `index.css` for the export build only would close this if pixel-exact offline typography matters
2. **Session 11 follow-up** → `npm run build:export` is a manual step with no enforcement (no CI, no git repo yet) — any future change to `AnalysisDashboard.tsx` or a section/chart component silently goes stale in the downloaded HTML until someone remembers to rebuild the template; worth a reminder mechanism (a pre-commit hook once a git repo exists, or at minimum a prominent note in `HOW_TO_RUN.md`) if this bites in practice
3. **Session 10 follow-up** → all analyses run before the `flip_trend` fix (2026-09-16, before ~14:28 local) have stale `debt_trend`/`inventory_days_trend`/`receivable_days_trend`/`ccc_trend` values in the DB (confirmed live on `FA-2026-000080` COFORGE) — decide whether to bulk re-run/re-analyze historical companies or just let it self-correct as each is naturally re-analyzed (bulk re-run costs Groq LLM quota per company, same constraint as the Phase 23 annual-report batch driver below)
4. **Phase 25 follow-up** → the deferred cash-flow-ratio overrides (`fcf_yield`/`fcf_margin`/`fcf_to_pat`/`cfo_to_pat`/`fcf_cagr_3y`) need new single-year ratio functions in `cash_flow_intelligence/conversion.py` (today only has a cumulative multi-year conversion ratio) before they can be wired into `screener_metrics_override.py`
5. **Phase 25 follow-up** → decide whether `_validate_metrics()` needs to also re-run after the Screener override (currently validates pre-override yfinance values only) — revisit if a real pipeline run ever surfaces a validation-range false positive (none has so far — see verification note below)
6. **Phase 24 follow-up** → run the Cash Flow Intelligence orchestrator stage (and re-verify P&L/Balance Sheet) across a volatile/negative-CFO company, not just Maruti/Tata Technologies, to confirm archetype/red-flag classification behaves sensibly outside the "healthy large-cap" case already tested
7. ~~**Phase 24 follow-up** → Lenskart's `cf_*` top-level ledger rows were never populated~~ **CLOSED, Session 12** — backfilled directly (`ingest_cash_flow` + `ingest_cash_flow_schedules`), Cash Flow Intelligence now computes 80% coverage (25 metrics) instead of degrading to empty. See Session 12 below.
8. **Phase 23** → decide whether to run `ingest_all_banks_annual_reports` batch driver across the other ~20 banks in the stocks table, respecting the Groq daily quota
9. **Phase 22** → end-to-end acceptance test: Automobile → Tata Motors → Analyze → all 13 stages → dashboard (still not formally done for a non-bank sector)
10. **Phase 13** → peer financial metrics for banks (peer comparison currently only has generic yfinance metrics, not banking-specific ones — peers were never run through the banking ingestion pipeline)
11. **Phase 20** → unit tests for the ORIGINAL calculation engine's own internals (`engine.py::MetricsCalculator`'s ~150 methods, `pnl_engine.py`'s helpers) — `screener_metrics_override.py` now has its own tests (Phase 25), and the 3 intelligence engines have 286+ tests, but the base yfinance-computation methods themselves still have none. `test_engine_flip_trend.py` (Session 10) is a first step but only covers `flip_trend`/`debt_trend`/`working_capital_trends`.
12. **Open question** → generalize the Phase 23 provenance-ledger pattern (now Screener.in + BSE/NSE, no RAG) to other sectors, or keep it banking-only

**Verified 2026-09-16** (closed the one Phase 25 follow-up that mattered most): ran two REAL, full, fresh orchestrator pipelines end-to-end via the actual `POST /api/fundamental/analyses` REST endpoint (`FA-2026-000076` Maruti, `FA-2026-000077` Tata Technologies) — not the direct-call re-simulation used during Phase 25's own implementation. All 18 stages completed with zero errors for both, `report_available: true`. Confirmed the corrected insertion point works end-to-end in the REAL pipeline, not just in isolation: `sector_analysis["key_metrics"]`/`sector_score` (built in the same stage, immediately after the override) show the Screener-sourced values, not the original yfinance ones (Maruti's `revenue_cagr_3y` key_metric reads 15.68 — the Screener figure — not yfinance's original 15.9; `pat_margin` reads 8.01 not 8.29). `analysis.metrics["_metric_sources"]` has all 22 expected keys for both companies. `score_refinement` (stage 99, runs after `scoring`) completed correctly on top of the overridden scores for both. Final `overall_score`: Maruti 75.20, Tata Technologies 62.60 — both consistent with the Phase 25 direct-call verification's own figures, confirming the two verification methods agree.

**Real regression found and fixed 2026-09-16 (same day)**: a live bug report on Coforge (Cash Flow/P&L tabs blank for CONSOLIDATED) revealed the Consolidated/Standalone toggle (added earlier this same session) had silently broken the auto-fallback it was meant to sit alongside — the 3 section components defaulted their toggle state to `"CONSOLIDATED"` and sent it explicitly on every request, which forced `allow_fallback=False` on the backend even for the FIRST, unclicked load. Fixed: toggle state now starts at `null` ("auto" — no `statement_type` query param sent, backend picks whichever has data), only becoming an explicit forced value once the user actually clicks a toggle button; the toggle's displayed selection reflects whichever statement_type the auto-resolved result actually used. Also found Coforge had the exact same STANDALONE-only ingestion gap as Tata Technologies (re-ingested to close it), and — since this same gap has now recurred on two unrelated companies — added the same `allow_fallback` pattern to `pnl_engine.py::compute_pnl_analysis()` itself (previously hardcoded `statement_type="CONSOLIDATED"` with zero fallback, unlike `pl_intelligence`'s own already-fixed version), so `screener_metrics_override.py`'s P&L overrides (CAGRs, PAT margin, ROE, interest coverage) no longer silently skip for any future company hitting this same transient scrape gap. 317 tests passing (up from 314), live-verified end-to-end for Coforge via a fresh real pipeline run (`FA-2026-000079`) — Cash Flow/P&L/Balance Sheet all correctly resolve to CONSOLIDATED with real data, `overall_score: 70.6`.
