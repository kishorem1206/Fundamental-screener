# Account Change — Session Handoff Notes

**Why this file exists:** the user working on this project switched Claude
Code accounts mid-session (from `kishorekishore289@gmail.com` to
`kishore12600@gmail.com`) and asked for a summary of everything done under
the previous account, so work can continue seamlessly from the new one.
This file is that summary — read it top to bottom for full context, or
jump to the section you need.

**Date range covered:** one continuous working session, 2026-09-20.

---

## 1. Standing principles established this session

These are durable conventions, not one-off decisions — anyone continuing
this work should follow them:

1. **Screener.in is the primary source of truth** for all financial
   values; yfinance is the fallback; NSE/BSE annual-report and quarterly
   Investor Presentation extraction is used only for what neither
   Screener nor yfinance structurally have (physical volumes, capacity,
   per-tonne economics, etc.).
2. **Never fabricate a number.** Every extraction prompt in this codebase
   explicitly instructs "if ambiguous, return null rather than guessing" —
   and this was proven necessary multiple times live this session (see
   §6, the Cement quarterly bug).
3. **Standalone vs Consolidated must be tracked per data point**, never
   assumed uniform across a whole report.
4. **Parentheses in a financial figure mean negative** — `(1,234)` → `-1234`
   — every extraction prompt says this explicitly.
5. **A local-LLM fallback response must never be stored** — Groq's
   `gpt-oss-20b` is the primary model; a local Ollama `llama3.2:3b`
   fallback kicks in on rate-limit, and its failure mode is *silent digit
   transposition*, not honest nulls. Every extraction engine in this app
   checks `llm_client.last_used_fallback` and skips storage entirely if
   true, rather than storing a lower-confidence value.
6. **Prefer a company's own directly-reported figure over a derived one**,
   but never invent the derivation either — every ratio-computation block
   checks for a directly-extracted value first, falls back to computing it
   from other ledger data second, and never silently overwrites a REPORTED
   value with a CALCULATED one for the same metric/period.
7. **New extraction areas get validated against at least 2 real
   companies** before being wired to storage — and it's normal/expected
   for one to work cleanly and another to be a documented miss (different
   companies disclose differently). A miss is not a bug to keep chasing;
   it's an honest finding to document.

---

## 2. Annual Report Extraction Engine — formalized

`backend/app/ingestion/annual_report_ingestion.py` + `annual_report_locator.py`
already existed in skeleton form; this session declared it **THE canonical
Annual Report Extraction Engine**, added a module-docstring **Area
Registry** table (the single place to check "does an extraction area
already exist" before building a new one), and fixed two real bugs found
live:

- **TOC false-positive bug**: a report's own Table of Contents listing
  both "Standalone Financial Statements" and "Consolidated Financial
  Statements" as adjacent page-number entries was being misread as the
  real section boundary. Fixed by requiring `_STANDALONE_MARKERS`/
  `_CONSOLIDATED_MARKERS` to be narrowed to genuine heading-only phrases
  ("standalone balance sheet"/"consolidated balance sheet"), and by
  skipping any page where both markers co-occur (a strong TOC signal).
- **`locate_sections()` now returns per-area statement-type resolution**
  (`{area: "STANDALONE"|"CONSOLIDATED"|"UNKNOWN"}`), not a single
  document-wide assumption — different areas on the same report can
  genuinely resolve differently.

**Area Registry as of this session** (see the module docstring for the
authoritative, always-current version):

| Area | Sector | Status |
|---|---|---|
| `asset_quality`, `funding`, `capital` | Banking | WIRED (banking-only) |
| `other_liabilities` | universal | WIRED |
| `ppe` | universal | BUILT, NOT WIRED — silently wrong-year on live testing, more dangerous than a null |
| `raw_material`, `energy_cost`, `revenue_geography`, `rd_expenditure` | universal | WIRED, validated on Pidilite + Aarti Industries |
| `cement_operating_metrics` | Cement | WIRED, validated on UltraTech; documented miss on Ambuja (infographic-heavy annual report) |
| `paper_operating_metrics` | Forest Materials | WIRED, validated on TNPL; documented miss on JK Paper |
| `metals_operating_metrics` | Metals & Mining | WIRED, validated on JSW Steel (full incl. direct EBITDA/tonne) + Tata Steel; documented miss on Hindalco (scrambled chart text) |
| `automobile_operating_metrics` | Automobile | WIRED, validated on Maruti Suzuki + Bajaj Auto |

---

## 3. Quarterly Report Extraction Engine — Tier 1 (financial data, all stocks)

Built from scratch this session — genuinely new capability, not a
formalization of existing code:

- **`backend/app/ingestion/quarterly_results_client.py`** — ingests
  Screener's `quarterly_results()` (previously only 2-3 banking NPA
  fields were kept from it; now every quarter, every field, for every
  company). All metric keys are `qtr_`-prefixed to avoid a real collision
  risk: a Q4 quarter-end ISO date is textually identical to that year's
  fiscal-year-end date, so reusing the annual `pnl_` namespace would let a
  quarterly row silently overwrite an annual one for the same date.
- **`backend/app/calculations/quarterly_intelligence/`** — a new compute
  package: QoQ/YoY growth, margin-trend classification (reuses
  `pl_intelligence/margin_trends.py`'s existing classifier, not
  reimplemented), and 4 deterministic red-flag rules (sequential
  deceleration, margin inflection, other-income dependency, tax-rate
  anomaly). Pure arithmetic, no LLM cost.
- New orchestrator pipeline stage `quarterly_analysis`, new REST route
  `/api/quarterly-intelligence/{company_id}`, new frontend "Quarterly" tab.
- **Real bug found and fixed**: `metric_store.get_latest_period_value()`'s
  `max()`-over-periods picks `"TTM"` as "latest" (since `"T"` sorts after
  any digit character), silently mismatching a ratio's numerator and
  denominator to two different periods. Fixed with a new
  `_latest_fiscal_pnl_value()` helper (later generalized with an `n_prior`
  parameter for the Automobile ASP-growth calc — see §5) that explicitly
  excludes `"TTM"` before picking a period.

---

## 4. Sector-by-sector rollout (annual-report-sourced operating metrics)

Sectors built this session, in order, each following the same "read the MD
spec → check the Area Registry → gap-analysis → build only what's missing
→ validate against 2 real companies → wire into the sector's scored
metrics" methodology:

### Commodities → Chemicals
First sector done (`app/sectors/commodities_chemicals.py`, renamed from
`chemicals.py` to match the spec file's naming). 4 new metrics wired:
`raw_material_cost_pct`, `energy_cost_pct`, `export_revenue_pct`,
`rd_to_revenue_pct` — all now **universal** areas other sectors reuse for
free (see below).

### Commodities → Construction Materials (Cement)
`app/sectors/cement.py`. 5 metrics wired: `volume_growth_yoy`,
`realisation_per_tonne`, `cost_per_tonne`, `ebitda_per_tonne`,
`capacity_utilization`. Real find: UltraTech's MD&A has a clean
current+prior-year table with a directly-stated per-tonne cost/energy/
freight breakdown — but that specific 3-column narrative breakdown was
**dropped from extraction** after two live runs of identical text returned
the raw-material and freight figures *swapped* (a real, reproduced LLM
field-confusion risk, not a hypothetical one).

### Commodities → Forest Materials (Paper)
**New sector framework** (`app/sectors/commodities_forest_materials.py`) —
previously `'paper & paper products'` fell through to `GenericSector`.
Wired into `registry.py` and `classification_map.py`. 3 metrics free via
universal-area reuse (`raw_material_cost_pct`/`energy_cost_pct`/
`export_revenue_pct`), 4 more (`capacity_utilization`,
`realisation_per_tonne`, `ebitda_per_tonne`, `cost_per_tonne`) from a new
`paper_operating_metrics` area. Real accuracy improvement made here:
per-tonne ratios prefer **sales** volume over **production** volume (they
can differ in an inventory-drawdown year) — the Cement area had used
production volume, a small known imprecision left as-is there since it
wasn't worth revisiting.

### Commodities → Metals & Mining
`app/sectors/metals.py` (`MetalsSector` + `MiningSector`, already
existed). Real bug fixed: `ebitda_per_tonne`/`cost_per_tonne` were
modeled in **USD** — real Indian disclosures state these in **INR** (USD
is only how the global LME benchmark *price* is quoted, a different
concept) — corrected the unit and recalibrated thresholds. New capability:
JSW Steel's MD&A directly states EBITDA/tonne in narrative prose, so the
ratio-computation block now **prefers a directly-reported figure over the
derived one** when both are available, with a dedicated regression test
proving the reported value is never silently overwritten.

### Consumer Discretionary → Automobile and Auto Components
`app/sectors/automobile.py` + `auto_ancillaries.py` (already existed). 4
metrics wired (`volume_growth_yoy`, `asp_growth`, `market_share`,
`dealer_inventory_days`) from a new `automobile_operating_metrics` area.
Two free renames (`rd_to_revenue`→`rd_to_revenue_pct`,
`exports_to_revenue`→`export_revenue_pct`) to match the universal areas.
Real find: Bajaj Auto's MD&A directly discloses its own market share
sourced from SIAM data — overturning the original assumption that market
share would always need third-party industry data. `ev_penetration`/
`ev_revenue_contribution` and Ancillaries' `customer_concentration_top3`/
`ev_ready_revenue_pct` remain **documented gaps**, not forced.

### Cross-referencing (done before the sector rollout, applies to all 34 sectors)
All 21 sector analysis framework MD docs and all 25 Python sector
implementation files now open with a note pointing at the two engine
files and their Area Registries, so future sector work checks for
existing coverage before building something new.

---

## 5. Automobile ASP-growth fix — `_latest_fiscal_pnl_value(n_prior=...)`

Generalized the annual engine's TTM-exclusion helper with an `n_prior`
parameter (0 = latest fiscal period, 1 = the one before that, by *sort
order of periods that actually exist in the ledger* — not date
arithmetic on a possibly-fallback-derived period). Needed because ASP
growth requires the *prior* fiscal year's Screener revenue, and naively
subtracting one calendar year from an already-imprecise resolved period
would be fragile. All 4 existing callers keep their old default (`n_prior=0`)
behavior unchanged.

---

## 6. Quarterly Sector KPI Extraction Engine (built today, right before the account switch)

**Genuinely new document source**: NSE quarterly **Investor
Presentation** filings (via the same `corporate-announcements` API
`nse_concall_client.py` already used for earnings-call transcripts,
filtered to `desc == "Investor Presentation"` instead), not annual
reports. This closes a real gap the user flagged: "Only annual report?
Where recent quarterly analysis" — the sector-specific physical KPIs
(production volume, capacity utilization, EBITDA/tonne, units sold) had
only ever been sourced annually until now.

### New files
- **`backend/app/ingestion/nse_investor_presentation_client.py`** — fetch
  discovery + download. Handles two real failure modes found live:
  1. Some companies' NSE-attached PDF is just a cover letter linking to
     the real deck on their own website (JSW Steel's pattern) — resolved
     automatically by following a `.pdf` URL found in the sparse text
     (with a regex fix for PDFs that word-wrap the URL mid-word,
     inserting a literal newline into the link).
  2. Some companies' decks are pure-graphic/infographic slides with
     almost no extractable text (UltraTech Cement's pattern) — detected
     via a minimum-text-length heuristic and skipped cleanly (no crash,
     no wrong data — just no data).
- **`backend/app/ingestion/quarterly_operating_metrics_ingestion.py`** —
  the extraction engine itself. Per-sector prompts for Automobile, Cement,
  Metals/Mining, Paper. Every metric key is `qtr_`-prefixed and namespaced
  by sector (e.g. `qtr_automobile_units_sold`), with FINAL derived ratios
  (`qtr_ebitda_per_tonne`, `qtr_cost_per_tonne`, `qtr_realisation_per_tonne`,
  `qtr_volume_growth_yoy`) intentionally mirroring the annual engine's
  metric names — same vocabulary, different cadence, never mixed into
  annual sector scoring.
- New `metric_store.py` source: `"NSE_INVESTOR_PRESENTATION"` (0.95 base
  confidence, same tier as `NSE_ANNUAL_REPORT`/`BSE_EARNINGS_CALL` — real
  text-layer extraction, no OCR). **Was a live bug on first run** —
  forgot to register it in `VALID_SOURCES`, caught immediately by the
  test suite.
- New orchestrator stage `quarterly_sector_kpis`, weekly-cache-gated
  (`_QUARTERLY_SECTOR_KPI_TTL`, 7 days — this stage makes a real LLM call,
  unlike the pure-Screener quarterly stage, and a new presentation only
  lands ~4x/year).

### A real bug found and fixed live, mid-build (important for whoever continues this)
The first Cement extraction attempt targeted Ambuja Cements' "Consolidated
Highlights" page — a bar-chart-style strip showing Sales Volume/Cement
Cost/EBITDA as three side-by-side mini-charts. **A live LLM call on this
page returned `sales_volume=1,069`, off by an order of magnitude** — that
number is actually a *different* metric's prior-year value; the page's
raw extracted text is a genuinely scrambled sequence of 9 numbers with no
recoverable column mapping from text alone. **This was caught, not
shipped** — retargeted the locator at a different, proper row-based table
elsewhere in the same deck ("Quarter Ended / Particulars UoM / Volume MnT
... EBITDA (PMT)"), verified it's internally consistent (each row's own
stated YoY/QoQ % change matches its own numbers), and confirmed a second
live LLM call against it returns an exact match. The lesson generalized
into the "cement" prompt itself, which now explicitly warns against
bar-chart-style layouts and asks the model to sanity-check its own
extraction against the stated % change.

### Live validation status
- **Automobile** (Maruti Suzuki): primary-model LLM call, exact match to
  the real deck (682,724 / 527,861 YoY / 676,209 QoQ units).
- **Cement** (Ambuja Cements): primary-model LLM call, exact match after
  the fix above (17.1 / 18.4 YoY / 19.9 QoQ MnT, EBITDA/tonne 931).
- **Metals** (JSW Steel): structurally validated (locator, period
  parsing, external-link resolution all confirmed working) but the
  Groq daily token quota was exhausted before a primary-model
  confirmation could complete — the fallback-LLM guard correctly
  refused to store the degraded-model result instead.
- **Paper**: no real candidate company found — TNPL and JK Paper both
  file zero "Investor Presentation" filings in a 120-day window. The
  extraction area is built (in case a paper company files one later)
  but unvalidated live, same honest-gap treatment as everywhere else
  this session.

### Not yet done (explicit next step for whoever continues)
The new `qtr_*` sector KPIs are being extracted and stored in the ledger
with full provenance, but **not yet surfaced anywhere** — the
`quarterly_intelligence` dashboard/API built in §3 only shows the generic
financial QoQ/YoY data, not these new sector-specific physical KPIs.
Extending `compute_quarterly_intelligence()`'s output (and the frontend
Quarterly tab) to include them is the natural next piece of work, not yet
started.

---

## 7. A negative result worth knowing about: `markitdown` evaluation

The user asked whether Microsoft's `markitdown` (PDF→Markdown converter)
could reduce LLM token usage in the annual-report pipeline. Piloted and
**rejected** — tested on both a clean table (UltraTech's cement
production table) and a known-hard scrambled infographic (Ambuja's
manufacturing highlights page): `markitdown`'s table-detection heuristic
made both *worse*, not better, chopping real tables into fragments
interleaved with unrelated narrative text from neighboring columns. It
also has no page-range API, so it would require converting whole
documents rather than the targeted 2-3 pages this pipeline already
extracts. Uninstalled cleanly (never touched `pyproject.toml`/`uv.lock`).
**Don't re-litigate this without a new reason** — the finding was based
on real side-by-side comparison, not speculation.

---

## 8. Known external constraint: Groq daily token quota

This session did an unusually large amount of live LLM validation (many
real annual reports + investor presentations across 5+ companies), and
repeatedly exhausted Groq's `gpt-oss-20b` daily token cap (200,000
tokens/day on this account's tier). This is a **calendar-day** quota, not
a rolling window — once exhausted, waiting 10-20 minutes doesn't help;
it needs to reset on its own schedule. When continuing this work, expect
to hit this again if doing heavy live-validation in one sitting; the
fallback-LLM guard (§1, point 5) means this never produces wrong data,
just blocks *new* validation until the quota resets.

---

## 9. Test suite

383 tests passing as of this file's writing (was 297 at the start of the
major work described here). Every new extraction area got dedicated
regression tests before being considered done — see `backend/tests/
test_*_operating_metrics*.py` and `test_quarterly_operating_metrics_ingestion.py`
for the pattern to follow for any new area.

---

## 10. Quick file map for orientation

**New/significantly modified this session:**
```
backend/app/ingestion/
  annual_report_ingestion.py          — formalized as THE Annual Report Extraction Engine
  annual_report_locator.py            — TOC bug fix, new area terms for 4 sectors + quarterly variants
  quarterly_results_client.py         — NEW, Tier-1 quarterly financial data (all stocks)
  quarterly_operating_metrics_ingestion.py  — NEW, quarterly sector KPI engine (investor presentations)
  nse_investor_presentation_client.py — NEW, fetch client for investor presentations

backend/app/calculations/quarterly_intelligence/  — NEW package, QoQ/YoY + margin trend + flags

backend/app/sectors/
  commodities_chemicals.py            — renamed from chemicals.py, 4 metrics wired
  cement.py                           — 5 metrics wired, unit-corrected
  commodities_forest_materials.py     — NEW sector framework
  metals.py                           — unit fix (USD→INR), 3 metrics wired
  automobile.py / auto_ancillaries.py — 4 metrics wired, 2 free renames
  registry.py / classification_map.py — Forest Materials wired in

backend/app/pipeline/orchestrator.py  — 2 new stages: quarterly_analysis, quarterly_sector_kpis

backend/app/infrastructure/database/metric_store.py — new NSE_INVESTOR_PRESENTATION source

frontend/src/components/sections/QuarterlySection.tsx — NEW Quarterly tab

Important md files/Sector analysis framework/*.md  — all 21 files cross-referenced
backend/app/sectors/*.py (25 files)                — all cross-referenced
```


---

# Update 2026-09-20 (later session) — sectors, sources, surfaces

**Sector rollout continued** (each: MD spec -> framework -> live/hand-read validation -> tests): Consumer Durables, Consumer Services (Hotels & Restaurants, Retail), Media (investigated, nothing safe to wire), Realty, Textiles (new framework), Diversified (new framework), Oil & Gas (GRM), FMCG, Healthcare, Banks/NBFC ROE method.

**Quarterly Sector KPI engine now a SOURCE CASCADE** (`quarterly_operating_metrics_ingestion.py`): investor presentation -> NSE results press release -> earnings-call transcript. Sources `NSE_PRESS_RELEASE` (HIGH) / `NSE_CONCALL` (capped MEDIUM). Outcome-of-board-meeting filings were hand-checked on 8 hospitals: financial statements only, no operating KPIs, so NOT a layer (banks are the exception — their board-outcome results carry GNPA/NNPA/CRAR). Deck discovery also matches decks misfiled under other NSE categories (Bank of Baroda).

**Hand-verified data (source MANUAL, each row keeps filing URL + quote + corroboration)** — done because the Groq daily quota was exhausted; use as ground truth to grade the LLM path: 8 hospitals (occupancy, ARPOB, ALOS, ARPP, beds), 9 FMCG (volume growth, USG, price-mix, Nestle premium share), 9 banks x 10 ratios (HDFC Bank skipped: results filing is cover/image only). Traps found and recorded: Medanta prose ARPOB typo (70,224 vs table 70,244); SBI/Federal decks mix subsidiary figures with bank figures; AU board-outcome ROA is un-annualised; mentor's IDFC CRAR 15.60% is the MARCH figure (Jun-26 is 15.05%); Fortis/Narayana quote ARPOB per YEAR (converted /365, marked CALCULATED).

**Bank/NBFC ROE method** (mentor's `idfc-first-roe-simulator.html`): `app/calculations/bank_roe_engine.py`, route `/api/bank-roe/{id}`, tab `BankRoeSection.tsx`, scoring metrics `sustainable_growth_gap` + `pb_roe_premium_pct`. Parity-tested against his JS.

**Every surface** (a test now guards this — `tests/test_sector_kpi_surfaces.py`): Quarterly tab KPI cards show source/confidence/link; PDF has two new auto-numbered sections (`bankRoe`, `sectorKpis`; pdf-renderer/src/index.ts numbers sections in draw order); offline HTML export bundle includes `/quarterly-intelligence/` and `/bank-roe/`; quarterly figures feed sector SCORES via `ledger_bridge.QUARTERLY_FALLBACKS` (rates/levels only — never absolute flows like pre_sales_value). Adding a sector to `quarterly_sector_kpis._SECTOR_METRICS` now flows through all of these; a new UNIT must also get a formatter in QuarterlySection.tsx and `_KPI_UNIT_FORMATS` (tests fail otherwise).

**Open**: LLM path unvalidated live for Healthcare/FMCG-transcript/press-release layers (quota); FMCG transcript job still separate from the cascade; Godrej Consumer 2-Sep call (UVG 4%) has no stated period so not stored; HDFC Bank needs OCR of its results.

## Capital Goods / Industrials / Defence (2026-09-20)
- Quarterly engine: new area `capgoods_quarterly_metrics` + prompt `capgoods` (all three sector names share prefix `capgoods`). Stores `qtr_capgoods_*`: order_inflow, order_inflow_yoy_prior, order_backlog, order_backlog_yoy_prior, export_order_pct (INR Cr / %), plus derived order_inflow_growth_yoy (a stated % wins), order_backlog_growth_yoy, book_to_bill (same-document revenue), order_backlog_to_ttm_revenue (only with 4 consecutive Screener quarters).
- Framework: added `book_to_bill` (scored, 0.05) and `export_order_pct` (display only); `order_book_to_revenue`, `order_inflow_growth` now filled through `QUARTERLY_FALLBACKS`. Unit `x` gets a formatter in QuarterlySection.tsx and `_KPI_UNIT_FORMATS`.
- Hand-read ground truth (MANUAL rows, Q1 FY27): Triveni Turbine, ABB India, Thermax, Hitachi Energy India, Praj, CG Power (consolidated and standalone), GE Vernova T&D, BEL (transcript, MEDIUM).
- Traps: Hitachi Energy's +26.1% order growth excludes an HVDC base order (not stored); CG Power files standalone and consolidated side by side; Thermax TOESL moved to a rolling-12-month backlog method; units are crore/million/billion by issuer; GE Vernova T&D and Hitachi statement basis unlabelled (stored as CONSOLIDATED).
- Not disclosed comparably, left N/A: capacity utilisation, aftermarket revenue %, dealer metrics, book-to-bill for defence PSUs without a revenue line in the same document. HAL, Mazagon, BDL, Siemens, Cummins, Kirloskar, KEI, Polycab, GRSE, Cochin: no stated inflow/backlog in a usable table (Cochin transcript gives ~Rs 22,000 Cr backlog only in prose, not stored). LLM path unvalidated live (quota).
- Follow-up (same day, wider source sweep): added `aftermarket_order_pct` and `capacity_utilization` (company-wide single figure only). Year-end (FY26, period 2026-03-31) order books stored for HAL (254,538 Cr vs 189,302), BDL (26,176 vs 22,814), Mazagon (20,535), BEML (15,896 vs 14,610), BHEL (~2.4 lakh Cr, approximate) because their Q1 FY27 decks/calls are not yet filed. Q1 backlog from prose/transcripts (MEDIUM): KEI 4,292, GRSE 13,596, Cochin ~21,900 (deck, position date not stated). Siemens from the results note (orders 6,328, backlog 46,670). Deliberately NOT stored: Cummins utilisation "70-75%" (a range), Polycab's Rs 10,900 Cr (Bharat Net + RDSS only), Kirloskar overseas-only backlog and its corrected 5.4% order growth (entity unclear), CG Power's 100% (a single transformer plant's Reg-30 capacity filing), full-year inflows (HAL 97,028, BHEL ~75,000). Still not disclosed anywhere found: dealer economics for CG names, order margin/customer quality.

## Construction (2026-09-20)
- Construction (EPC) shares the Capital Goods order-book engine (`qtr_capgoods_*`, same locator/prompt; sector name "Construction" added to `_SECTOR_CONFIG`, `_SECTOR_METRICS`, KPI/PDF/HTML/score paths). New metric `international_backlog_pct` (display) and `export_order_pct` relabelled international for construction. Framework gained `book_to_bill` (0.05), `export_order_pct`, `international_backlog_pct`. Infrastructure (concessions) inherits the metrics but has no quarterly config.
- Routing fix: 'tractors' and 'construction vehicles' moved from Construction to Capital Goods (spec: Agricultural, Commercial & Construction Vehicles is a Capital Goods industry).
- Hand-read Q1 FY27 (MANUAL rows): L&T (inflow 1,08,014, backlog 7,78,954, international 56%/52%), Afcons, Ashoka, IRCON, JK Infra, Kalpataru, KNR, NCC, PNC, Power Mech, Engineers India, RVNL.
- Not stored, on purpose: KEC (backlog quoted with L1 positions; YTD inflow), KPIL YTD inflow (measured past quarter end), DBL (backlog dominated by 25-55-year mine-developer contracts), Power Mech's 55,398 incl. MDO, L&T's +5% (vs March, not YoY), NCC's July-inclusive 4,542. HG Infra deck is image-only; Techno Electric filed no usable material. Not captured anywhere comparable: govt/private split (only charts), retention money, billing vs collection, fixed-price share, cancellation rate, equipment utilisation.

## Information Technology (2026-09-20)
- Audit result: the IT framework had 6 unavailable metrics (CC growth, TCV, attrition, utilisation, revenue/employee, top-10 client %); only attrition/utilisation/TCV had a source (transcript LLM job); nothing reached the Quarterly tab/PDF/HTML and the release/fact-sheet documents were unused.
- Added IT to the quarterly cascade (`prompt it_services`, prefix `it`, area `it_quarterly_metrics`): `qtr_it_*` CC growth YoY/QoQ, USD revenue, headcount, LTM attrition, utilisation (incl. trainees), total and large-deal TCV, top-5/10 client %, North America/Europe/BFSI share, offshore effort, US$1M+ clients, derived revenue/employee (annualised). Bridge `QUARTERLY_FALLBACKS` feeds the scored metrics (annual/transcript value wins). New units USD Bn / USD Mn / USD k formatted in frontend and PDF.
- Hand-read Q1 FY27 (MANUAL): TCS, Infosys (full fact sheet), HCLTech, Tech Mahindra, Wipro (transcript, IT-services scope), Mphasis (net-new TCV only), Zensar, Persistent. Sanity check: derived HCL revenue/employee 65.2k vs company-stated 65.5k.
- Traps: HCL's "62.1% YoY CC" is Advanced AI only; TechM shows IT-segment headcount 74,689 beside company 146,760; Infosys reports utilisation both incl./excl. trainees; Infosys TCV is large deals only (stored as large_deal_tcv, not total); Persistent's top-5 table has 7 columns (latest first).
- Not disclosed comparably / not built: pricing and billing rates, subcontractor ratio, recurring-revenue %, deal pipeline, software ARR/NRR/CAC/LTV, hardware units/ASP/channel inventory, vertical mix beyond BFSI, service-line mix (AI/cloud %), employee pyramid. Coforge, LTIM, Tata Elxsi, KPIT, Mastek, Sonata, BSOFT, Cyient, Happiest Minds, OFSS: filings scanned or absent in window but not hand-verified this pass. LLM cascade path unvalidated live (quota).

## Services -> Services (2026-09-20)
- Gap found: no Services framework existed; 35 of the 79 "Services" stocks (Diversified Commercial Services, BPO/KPO, Trading & Distributors, Transport Related Services, Consulting) fell to Generic. Added `ServicesSector` (`app/sectors/services.py`; revenue/PAT CAGR, EBITDA margin, ROCE, receivable/WC days, D/E, FCF/PAT, P/E, EV/EBITDA scored; headcount, attrition, order-book cover display) and routed those NSE basic industries to it. Transport operators, ports/roads/airports stay on Logistics/Aviation/Infrastructure.
- Quarterly cascade: Services, Logistics, Aviation, Infrastructure share prompt `services` / prefix `svc` (headcount, attrition, utilisation, passengers, load factor, ASK, yield, CASK, CASK ex-fuel, cargo MT, TEU, shipments, TCE, orders, growth via shared `qtr_volume_growth_yoy`). Units Mn, Bn, USD/day formatted on frontend + PDF; QUARTERLY_FALLBACKS now accepts several keys per metric (attrition, utilisation).
- Hand-read Q1 FY27 (MANUAL): IndiGo (ASK, load factor, yield, CASK, CASK ex-fuel), GMR Airports (30.5 mn pax), CONCOR (1.4 mn TEU, +9%), Delhivery (322 mn shipments, +55.2% - inflated by Ecom Express), VRL (+9% volume), Gateway Distriparks (TEU), Quess (482,214 headcount), TeamLease (341,330), Awfis (76% occupancy).
- Traps: IndiGo's +2.9% is ASK capacity not traffic; Delhivery growth is acquisition-led; Quess release has a 469k sub-count next to 482k total; APSEZ states domestic (115.3 MMT) and international (22.8 MMT) separately with no total, so nothing stored.
- Not captured (no comparable disclosure found): toll/traffic for road InvITs, aeronautical vs non-aeronautical revenue, revenue/tonne, fleet-level economics for shipping (TCE only appears as a glossary line), SCI/GE Shipping utilisation, public-services contract risk, employee-cost ratios. Blue Dart, TCI, Mahindra Logistics, Allcargo, Redington, eClerx, Firstsource, CMS Info, Dredging Corp, Seamec fetched but no clean company-wide operational figure was verified. LLM cascade path unvalidated live (quota).

### Services follow-up: the "not captured" list, second source sweep (2026-09-20)
- **Road toll (new source type):** IRB files monthly "project-wise toll revenue" updates on NSE (category Updates). New `app/ingestion/nse_toll_disclosure_client.py` parses them deterministically (no LLM, no quota): monthly `mth_svc_toll_revenue` (+ year-ago), and `qtr_svc_toll_revenue` / `_yoy_prior` / `qtr_svc_toll_growth_yoy` once all three months exist. Source `NSE_COMPANY_DISCLOSURE` (registered, labelled). Wired into the Infrastructure branch of the cascade. Live on IRB: Q1 FY27 gross toll Rs 2,444 Cr vs 1,945 Cr (+25.65%; Apr 793.5, May 842.7, Jun 807.8). Gross across group + InvIT SPVs, some added mid-year, so growth is not like-for-like. Other road InvITs (IRB InvIT, Vertis, NHIT, Cube, Indus, RIIT) returned no filings from the corporate-announcements API under those symbols - InvITs sit on a different feed and are still uncovered.
- **Airports:** GAL aero yield per passenger Rs 445 and non-aero income per passenger Rs 691 (deck); absolute aero/non-aero revenue is only stated for Delhi (growth %), so not stored.
- **Logistics:** VRL tonnage 1,019 kt and revenue/tonne Rs 8,546 (+9% each); Blue Dart 364.43 kt and 96.15 mn shipments (transcript); Mahindra Logistics 21.9 mn sq ft warehousing.
- **Shipping:** GE Shipping own average earnings by category (crude 93,026 / product 45,471 / dry bulk 22,601 USD/day; LPG 41,528 not stored) and fleet 40 vessels / 3.24 mn dwt. The "Baltic/Suezmax" deck lines are market indices and are deliberately not stored as company earnings.
- **Employees / utilisation:** Firstsource 36,875 headcount, 33.1% TTM attrition; eClerx 22,499 headcount, 75.5% delivery utilisation; derived employee-cost % of revenue exists in the engine (needs both figures in one document; no company verified yet).
- **APSEZ:** only domestic cargo (115.3 MMT, +2.1%) is stated - stored, labelled domestic-only, MEDIUM. No group total exists to store.
- Still not found: TCI/Redington/Dredging Corp/CMS Info/Seamec operating figures (CMS's "Rs 2,000 Cr order book" is a target line, not stored); public-services contract risk (qualitative, no listed Public Services stocks in the DB); revenue per tonne for most logistics names; per-vessel fleet economics beyond category TCE.

## Telecommunication (2026-09-20)
- Audit: 4 unavailable Telecom metrics (ARPU, subscriber growth, data revenue %, service FCF margin) had no source and nothing reached the Quarterly tab/PDF/HTML. Only Telecom - Services routed to Telecom; **tower companies (Telecom - Infrastructure: Indus Towers, HFCL, GTL) were mis-routed to the roads/ports Infrastructure framework** - now mapped to Telecom.
- Quarterly cascade for Telecom (prompt `telecom`, prefix `tel`): ARPU, mobile customers and derived YoY growth, net adds, monthly churn, data GB/customer/month, 4G/5G customers (+company-stated share), home broadband, towers, co-locations, tenancy (stated, else colocations/towers), equipment order book/book-to-bill, derived EBITDA-capex margin (only when EBITDA and capex are both stated). New cascade layer **results filing (Outcome of Board Meeting)** for Telecom only, source `NSE_RESULTS_FILING`: operators put their operating-KPI tables there (Airtel). Locator gained `x_tolerance` (1.5 for this layer) because Airtel's filing text is letter-spaced ("3 7 6 ,5 0 8") at default tolerance.
- Hand-read Q1 FY27 (MANUAL): Bharti Airtel (India mobile: 376.5 mn customers +3.78%, ARPU Rs 264, churn 2.6%, 34.4 GB, 4G/5G 301.8 mn / 80.5% company-stated), Bharti Hexacom (ARPU 259, 28.98 mn, churn 2.3%, 36.2 GB), Vodafone Idea (ARPU 195, 193.1 mn, 130.1 mn 4G/5G), Indus Towers (267,611 towers, 432,250 co-locations, 1.62x), Tejas (order book Rs 1,529 Cr).
- New industry source: **TRAI monthly subscription report** (trai.gov.in press release 104/2026, June 2026): Vodafone Idea mobile share 15.50% (reported); Airtel 35.47% and Vi 12.51% of wireless broadband subscribers (calculated from TRAI's operator table / 1,039.78 mn; MEDIUM). Not automated - TRAI publishes operator shares mostly as chart labels, so only text-extractable figures were taken.
- Traps: Airtel reports India and Africa side by side (group 681 mn customers not used); ARPU in Rs vs US$; my derived 4G/5G share (80.15%) differed from the company's stated 80.5% (different denominator) so the derived version was removed; Vi's YoY subscriber base is not stated so no growth; HFCL's order-book chart was ambiguous and not stored.
- Not captured: Tata Communications, Route Mobile, RailTel, STL, ITI, Optiemus, MTNL/BSNL operating KPIs (no clean company-wide figure found in the filings fetched); network capex per operator; spectrum holdings/AGR dues (regulatory, qualitative); revenue/GB; 5G site counts as a comparable series; TRAI Airtel/Jio mobile market share (chart-only). LLM cascade path unvalidated live (quota).

### Telecom follow-up: the "not captured" list (2026-09-20)
- **Airtel Africa is now stored, not dropped**: India-mobile KPIs stay the headline (scored), and the Africa segment (constant currency) is stored beside them as `qtr_tel_africa_*` (customers 188.999 mn vs 169.389 mn -> derived +11.58%, matches company-stated 11.6%; ARPU US$2.7; churn 4.5%; 10.6 GB; data customers 87.3 mn; 41,300 towers; mobile-money 56.5 mn active) plus group customers 681 mn. The engine prompt takes `africa_*` and `group_customers_mn` for any operator with an overseas segment. Africa figures are display-only cards; they are never mixed into the India ARPU/customer numbers that feed scoring.
- **Vodafone Idea year-ago base found** in its 14 Aug 2025 results filing (197.7 mn) -> customer growth -2.33%. Also stored: revenue 11,689 / EBITDA 5,034 / capex 1,930 Cr (service-FCF margin 26.55%), deferred spectrum obligation Rs 130,299 Cr, AGR Rs 25,759 Cr (spectrum/AGR dues now covered from the results filing note).
- **Capex / service FCF**: Airtel 13,386 Cr (34.5%), Hexacom 382 Cr (39.6%), Vi (26.55%); Indus states no capex, so none.
- **Revenue per GB**: Airtel India mobile segment revenue Rs 29,929 Cr / 31.062 bn GB = Rs 9.64/GB (includes voice; the segment also carries network groups). New engine fields `mobile_revenue_cr`, `data_traffic_bn_gb`.
- **Data revenue share**: Tata Communications Data Services Rs 5,703.58 Cr of Rs 6,582.82 Cr = 86.6% (feeds the previously-N/A `data_revenue_pct`).
- **TRAI market shares automated** (`app/ingestion/trai_client.py`, source `TRAI_REPORT`): the operator table is a rotated page pdfplumber reads reversed, so text comes from poppler `pdftotext -layout` (skipped cleanly if not installed - deployment note). Shares = operator subscribers / TRAI total, accepted only if operator columns reconcile to the total and BSNL agrees with TRAI's printed 7.25%. June 2026: Airtel 37.96%, Jio 39.27% (unlisted), Vi 15.50%, BSNL 7.25%, MTNL 0.01%; last three monthly reports stored under `mth_` and quarter-end under `qtr_`. Wired into the Telecom cascade for BHARTIARTL, IDEA, MTNL. TRAI counts include M2M so they differ from company-reported bases.
- **HFCL** order book resolved by cross-footing the chart: Rs 26,665 Cr (Networks 17,339 + O&M 4,227 + Products 5,099 = Government 10,502 + Private 16,164). **ITI**: order book Rs 13,882.81 Cr from its going-concern note (MEDIUM: an incidental figure).
- Still not captured: STL (only a ">US$2 bn open order book" line in a transcript, no INR figure), Route Mobile (LTM revenue and concentration charts only; message volumes undisclosed in the deck), RailTel (transcript/deck are cover pages; only per-order-win filings exist), Optiemus (targets only), BSNL (unlisted; TRAI share stored on Airtel/Vi/MTNL only), Tata Comm/RailTel decks are image-only (need OCR). Not stored on purpose: Airtel's derived 4G/5G share (denominator mismatch). LLM cascade path unvalidated live (quota).

## Utilities -> Power (2026-09-20)
- Audit: 4 unavailable metrics (PLF, regulated/PPA %, T&D losses, DISCOM receivable days); no source for any, nothing reached the Quarterly tab/PDF/HTML.
- Quarterly cascade for Power / Utilities / Renewable Energy (prompt `power`, prefix `pow`): operational MW + year-ago -> derived capacity growth, thermal/renewable/pipeline MW, generation MU, thermal PLF, availability, renewable CUF, PPA share, tariff, transmission availability/ckm/MVA, distribution loss, AT&C, collection efficiency, trading volume, capex, derived EBITDA margin and EBITDA-capex margin (only when both stated). Scored bridge: `plf`, `td_losses`, `regulated_capacity_pct`; new display metrics availability, CUF, transmission availability, AT&C, collection efficiency, capacity growth. New units MW, MU, INR/kWh, ckm, MVA, Bn units formatted on frontend + PDF.
- **Renewable trap handled**: NSE files solar/wind developers (Adani Green, NTPC Green, ACME, KPI Green) and coal utilities under one "Power Generation" industry, so they all route to the Power framework whose PLF scale is thermal (65-88%). Thermal PLF and renewable CUF are separate keys and only PLF feeds the scored `plf`, so a ~25% CUF can never be scored as a 25% PLF (test-guarded). Pure-play routing by company is not possible with the current basic_industry-only classification.
- Hand-read Q1 FY27 (MANUAL): Adani Power (PLF 78% vs 67%, 31 BU generated), Adani Green (20,142 MW vs 15,816 MW, +27.35%), POWERGRID (availability 99.80%, 1,86,595 ckm, 6,34,516 MVA), JSW Energy (net generation 12.9 BU), PTC (25,783 MU traded), NLC India (gross generation 8,262.06 MU).
- Not stored on purpose: Torrent/CESC distribution losses (per licence area and FY26 annual, not company-wide quarterly), NTPC's 72.04% PLF (FY26 annual), JSW's installed-capacity chart (base vs current ambiguous), KPI Green/NTPC Green/ACME capacity (not stated as a clean operational figure in the fetched documents). Not found comparably: NTPC, Tata Power, NHPC, SJVN, CESC quarterly PLF/availability/generation (decks chart-scrambled or annual; NTPC group figures live in a separate operational-data release not fetched), DISCOM receivable days (annual-report note), fuel cost per unit, coal stock days, heat rate, PPA tenor/tariff by asset. Nuclear/hydro-specific disclosures absent. LLM cascade path unvalidated live (quota).

### Power follow-up: other sources (2026-09-20)
- **CEA (Central Electricity Authority) monthly Executive Summary** now a source (`app/ingestion/cea_client.py`, `CEA_REPORT`): all-India thermal PLF by ownership sector (Central / State / Private IPP / Private utility), table 10. Stored as a **benchmark, not the company's own PLF**: NTPC/NLC/SJVN -> Central, Adani Power/JSW/Reliance Power/Jaypee -> Private IPP, Tata Power/CESC/Torrent -> Private utility (coarse mapping, recorded in provenance). June 2026: Central 72.42%, Private IPP 78.03% (matches Adani Power's own stated 78%), Private utility 68.04%. Monthly rows plus the quarter-end month as the KPI-card value (labelled "quarter-end month"): the May 2026 report is not under a guessable file name, so a 3-month average is not reliable. Uses poppler `pdftotext` (skipped if absent), wired into the Power/Utilities cascade.
- **KPI read fix**: a regulator/industry series (CEA, TRAI market share) no longer decides whether a company's card shows CONSOLIDATED or STANDALONE figures - previously a consolidated benchmark row hid a standalone company's own metrics (found on CESC).
- **Newly captured**: NTPC group operational capacity 90.9 GW and 35.7 GW under construction (deck; the 72.04% PLF and 432 BU are FY26 annual and not stored); CESC standalone Q1 generation 1,668 MU, Kolkata distribution T&D loss 6.85% vs 7.08% (from its "Investor Update", filed under General Updates - a misfiled quarterly deck).
- **Checked, not usable**: CEA's DISCOM outstanding-dues table is stale (as of March 2024) and shows zeros (post late-payment-surcharge rules); PRAAPTI (praapti.in) is a JavaScript app with no static data; CEA daily coal-stock pages are not reachable as documents; NHPC's investor presentation (filed under Updates) is image-only (needs OCR); Tata Power's deck is segment financials, not operating data; SJVN/NHPC results carry no operating KPIs.
- **Still not captured**: DISCOM receivable days, coal stock days, heat rate, fuel cost per unit, PPA tenor/tariff by asset, NTPC/NHPC/SJVN/Tata Power quarterly PLF and generation (would need OCR of NHPC's deck or NTPC's operational-data release).

## Utilities -> Utilities (2026-09-20)
- **Framework fix**: the "Utilities" framework used to inherit Power's scale (PLF, T&D losses, DISCOM receivable days) - wrong for water/waste. New `app/sectors/other_utilities.py` (`UtilitiesSector`): growth, EBITDA margin, ROCE, receivable days, D/E, FCF/PAT, order-book cover and book-to-bill for water/waste contractors, plus display collection efficiency, waste processed (kt/quarter) and treatment capacity (MLD). Test-guarded: no PLF/T&D/DISCOM metrics.
- **Routing**: 'integrated power utilities' (Tata Power, Adani Power, Torrent, CESC, Reliance Infra) -> Power (the Power spec covers integrated utilities); 'gas transmission/marketing' (GAIL) moved from Power to Oil & Gas; water/waste stay Utilities. City-gas distribution (IGL, MGL, ATGL, Petronet) stays in Oil & Gas because that spec has its own gas-distribution chapter; the Utilities spec's gas-distribution items are extracted there.
- **Quarterly cascade**: Utilities (prompt `utilities`, prefix `util`: order inflow/backlog + derived growth/book-to-bill/backlog-to-TTM-revenue, waste, treatment MLD, customers, collection efficiency, network km) and Oil & Gas gained city-gas fields (`cgd_volume_mmscmd`, `_mmscm`, growth via the shared `qtr_volume_growth_yoy`, CNG stations, domestic PNG connections lakh, margin/SCM). New units tpd, MLD, km, MMSCMD, MMSCM, lakh, INR/SCM formatted on frontend + PDF.
- **Hand-read Q1 FY27 (MANUAL)**: WABAG (order book ~Rs 19,400 Cr excluding framework contracts, intake 3,400 Cr, book-to-bill 3.83), Ion Exchange (order book 2,473 Cr, call), EnviroInfra (3,693.8 Cr), Refex (1,635 Cr), EMS (2,328.91 Cr), Antony Waste (~850 kt processed, ~550 kt collected in the quarter, approximate), IGL (9.66 MMSCMD, +6%), MGL (4.766 MMSCMD, +7.01%), ATGL (303 MMSCM, +13%, 707 CNG stations).
- Traps: WABAG excludes framework contracts from its order book; Antony Waste gives quarterly tonnes (not per day) with '~'; ATGL states volume per quarter, MGL/IGL per day; MGL's pipeline (8,477 km) and cumulative 2.17 mn DPNG conversions are stated but conversions are not connections, so not stored.
- Not captured: water utility metrics proper (water supplied/billed, non-revenue water, per-consumer consumption) - no listed municipal water utility exists in the DB and contractors do not disclose them; waste contract tenure/tipping fees; gas procurement cost and realised margin per SCM (not disclosed in the fetched filings); CGD network utilisation; regulatory-asset/receivable quality; Petronet/GAIL operating data (regas utilisation, transmission volumes - Petronet's filing was an unreadable newspaper-style PDF); municipal receivable days (annual report). LLM cascade path unvalidated live (quota).

### Petronet LNG and GAIL: other sources (2026-09-20)
- **My earlier "unreadable" verdict was partly wrong**: only Petronet's *press-release* filing is a newspaper advertisement. Its earnings-call transcript reads fine with `pdftotext` (the earlier scan used pdfplumber and a too-loose grep), and GAIL's operating data sits in its results press release. Both are now read.
- **Petronet LNG (Q1 FY27, call)**: LNG processed 207 TBtu (220 a year ago), Dahej 192 TBtu; company utilisation 58% (76% a year ago), Dahej 65.6%, Kochi 23.27%. Caveat: Dahej nameplate rose from 17.5 to 22.5 MMTPA on 31 March 2026, so the drop is partly a bigger denominator.
- **GAIL (Q1 FY27 standalone, press release)**: gas transmission 122.36 MMSCMD, gas marketing 93.82 MMSCMD, LPG transmission 1,077 TMT, polymer 51 TMT, LHC 232 TMT, revenue Rs 38,982 Cr, EBITDA 6,948 Cr, capex 6,176 Cr (EBITDA-capex margin 1.98%). The release compares with Q4 FY26, not the year-ago quarter, so no YoY.
- **New regulator source - PPAC "Snapshot of India's Oil & Gas data"** (`app/ingestion/ppac_client.py`, source `PPAC_REPORT`, poppler `pdftotext`): Table 21 gives per-terminal capacity and FYTD utilisation (Dahej 22.5 MMTPA 68.21%, Kochi 5 MMTPA 24.26% -> Petronet capacity-weighted 60.22%, stored as monthly FYTD `mth_oilgas_regas_utilization_fytd_ppac`, a cross-check not a quarterly figure); Table 20 (PNGRB) gives common-carrier pipeline length/authorised capacity as on 31 Mar 2026 (GAIL 11,184 km, 240.1 MMSCMD; GSPL 2,894 km, 74.8 MMSCMD; GAIL's partially-commissioned 7,118 km not counted). Wired into the Oil & Gas cascade for PETRONET/GAIL/GSPL. PPAC also publishes LNG import volumes (India, Aug 2026 prorated 2,915 MMSCM), PNG connections/CNG stations by state, and CNG/PNG city prices - industry-level, not stored per company.
- **Engine additions** (Oil & Gas prompt): gas transmission/marketing MMSCMD, LPG transmission / petchem / LHC kt, LNG throughput TBtu, regas utilisation, regas capacity MMTPA, capex and derived EBITDA-capex margin. New units TBtu and MMTPA on frontend + PDF.
- **KPI read fix again**: PPAC pipeline rows (consolidated) were hiding GAIL's standalone figures; pipeline keys are now statement-agnostic like the CEA/TRAI series.
- **Still not captured**: GAIL year-ago comparisons and gas-marketing/transmission tariffs and realised margins, GAIL LPG/petchem spread; Petronet regas tariffs, term vs spot vs third-party volume split (described qualitatively on the call), Kochi/Dahej volumes in absolute terms beyond Dahej TBtu; GSPL/Gujarat Gas/other CGD PPAC-level connection counts per company (PPAC gives them by state only). LLM cascade path unvalidated live (quota).
