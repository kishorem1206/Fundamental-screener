# Agents — AI Fundamental Analysis Platform

## What is an "Agent" in this system?

Each stage of the analysis pipeline is implemented as an **agent** — a focused unit of work with:
- A clear input (data from previous stages)
- A specific responsibility
- A structured output (JSON stored in PostgreSQL)
- A status (PENDING → RUNNING → COMPLETED / FAILED)

Agents communicate by reading/writing to the `fa_analyses` and `fa_analysis_stages` tables. They don't call each other directly — the **Orchestrator** calls them in sequence.

---

## Agent List

### 1. Orchestrator Agent
**File:** `backend/app/pipeline/orchestrator.py`  
**Function:** `run_analysis_pipeline(analysis_id, stock_id)`

The Orchestrator is the conductor. It:
- Runs as a FastAPI `BackgroundTask` (async, non-blocking)
- Calls each agent stage in order
- Updates `fa_analyses.current_stage` and `overall_progress` after each stage
- Updates `fa_analysis_stages` with each stage's status, progress, message, result
- On critical failure (Stage 1 or 2): marks analysis FAILED and stops
- On non-critical failure (Stage 12 AI, Stage 13 PDF): logs and continues

**Inputs:** analysis_id (UUID), stock_id (EXCHANGE:SYMBOL)  
**Output:** Updates fa_analyses record to COMPLETED with all JSON fields populated

---

### 2. Company Identification Agent
**Stage:** 1  
**Location:** Inside `run_analysis_pipeline()`, Stage 1 block

**What it does:**
- Queries the `stocks` table for the given `stock_id`
- Validates the stock exists
- Extracts company metadata: name, sector, industry, exchange, symbol, market cap, ISIN
- Derives `exchange` and `symbol` from `stock_id` format (`NSE:TATAMOTORS` → `NSE`, `TATAMOTORS`)

**Input:**
```json
{ "stock_id": "NSE:TATAMOTORS" }
```

**Output stored in `fa_analyses.company_info`:**
```json
{
  "stock_id": "NSE:TATAMOTORS",
  "symbol": "TATAMOTORS",
  "exchange": "NSE",
  "company_name": "Tata Motors Limited",
  "sector": "Automobile",
  "industry": "Automobile",
  "basic_industry": "Passenger Cars",
  "macro_sector": "Consumer Discretionary",
  "market_cap": 235000000000,
  "market_cap_category": "LARGE_CAP",
  "isin": "INE155A01022"
}
```

**Failure behavior:** CRITICAL — pipeline stops. Without a valid company, nothing else can proceed.

---

### 3. Financial Data Collection Agent
**Stage:** 2  
**File:** `backend/app/data/yfinance_client.py`  
**Function:** `fetch_financial_data(exchange, symbol)`

**What it does:**
- Maps exchange to yfinance suffix: NSE → `.NS`, BSE → `.BO`
- Calls `yfinance.Ticker(f"{symbol}.NS")`
- Fetches: annual income statement, annual balance sheet, annual cash flow, quarterly financials, market data, company info
- Tries multiple column name variants (yfinance uses inconsistent names across versions)
- Checks Redis cache first (24h TTL key: `fin:{exchange}:{symbol}`)
- If cache miss: fetches from Yahoo Finance and caches result

**Output stored in `fa_analyses.financial_data`:**
```json
{
  "income": {
    "Total Revenue": { "2022": 261000000000, "2023": 349000000000, ... },
    "EBITDA": { "2022": 28000000000, ... },
    "Net Income": { "2022": 14000000000, ... },
    "Basic EPS": { "2022": 3.6, ... }
  },
  "balance": {
    "Total Assets": { "2022": 320000000000, ... },
    "Total Debt": { "2022": 120000000000, ... },
    "Total Equity Gross Minority Interest": { "2022": 85000000000, ... }
  },
  "cash_flow": {
    "Operating Cash Flow": { "2022": 30000000000, ... },
    "Capital Expenditure": { "2022": -18000000000, ... }
  },
  "market": {
    "market_cap": 235000000000,
    "enterprise_value": 340000000000,
    "pe_ratio": 18.5,
    "pb_ratio": 2.8,
    "dividend_yield": 0.02
  },
  "company_info": {
    "longBusinessSummary": "Tata Motors is an...",
    "longName": "Tata Motors Limited"
  }
}
```

**Failure behavior:** CRITICAL — if no income/balance/CF data at all, pipeline stops.

---

### 4-6. IS / BS / CF Analysis Agents
**Stages:** 3, 4, 5  
**Current status:** Pass-through (instant COMPLETED)

**Planned behavior:**
- Parse and validate each financial statement independently
- Detect: missing rows, duplicate periods, unit inconsistencies, restatements
- Return per-row validation status

**Why currently minimal:** The heavy validation is done by the Metric Validation Agent (Stage 7). These stages exist to allow future parallel validation of each statement.

---

### 7. Ratio Calculation Engine
**Stage:** 6  
**File:** `backend/app/calculations/engine.py`  
**Class:** `MetricsCalculator`  
**Function:** `compute_metrics(financial_data)` → calls `MetricsCalculator(financial_data).compute_all()`

**What it does:**
Computes all universal financial ratios from the raw financial data.

**Growth metrics:**
- Revenue CAGR (3Y, 5Y)
- EBITDA CAGR (3Y)
- PAT CAGR (3Y, 5Y)
- EPS CAGR (3Y)
- FCF CAGR (3Y)

**Trend analysis (for each metric series):**
- Linear regression → direction
- Returns: STRONGLY_IMPROVING / IMPROVING / STABLE / DETERIORATING / STRONGLY_DETERIORATING / VOLATILE / INSUFFICIENT_DATA

**Profitability:**
- Gross margin, EBITDA margin, EBIT margin, PAT margin
- ROE, ROCE (EBIT / Capital Employed), ROIC (NOPAT / Invested Capital)

**Cash flow:**
- FCF = OCF + CapEx (CapEx is negative in yfinance)
- CFO/PAT, FCF/PAT, FCF margin, FCF yield

**Balance sheet:**
- D/E, Net Debt, Net Debt/EBITDA, Interest Coverage, Current Ratio

**Efficiency:**
- Asset Turnover, Inventory Days, Receivable Days, Payable Days, CapEx/Revenue

**Valuation:**
- P/E, Forward P/E, P/B, EV/EBITDA, EV/Sales, FCF Yield, Dividend Yield

**Output stored in `fa_analyses.metrics`:** ~50 metric fields + trend strings + year-keyed series dicts

**Important:** CapEx from yfinance is stored as a **negative** number.
Therefore: `FCF = OCF + CapEx` (NOT `OCF - CapEx`).

---

### 8. Metric Validation Agent
**Stage:** 7  
**Location:** `_validate_metrics()` in orchestrator.py

**What it does:**
- Range-checks key metrics for obviously wrong values
- Returns VALID / WARNING for each metric

**Checks:**
- EBITDA margin: must be 0–100%
- PAT margin: must be -50% to 100%
- ROE: must be -200% to 200%
- ROCE: must be -100% to 200%
- D/E: must be 0–20x
- Current Ratio: must be 0–20x
- Interest Coverage: must be -10x to 100x

**Output stored in `fa_analyses.metric_validations`:**
```json
{
  "ebitda_margin": { "status": "VALID", "value": 14.2, "confidence": 0.9 },
  "debt_to_equity": { "status": "WARNING", "value": 25.3, "message": "Value outside normal range" }
}
```

---

### 9. Sector Detection & Analysis Agent
**Stage:** 8  
**File:** `backend/app/sectors/registry.py`  
**Function:** `get_framework(sector_name)` → `SectorFramework`

**What it does:**
- Maps company sector name to a sector framework class
- `AutomobileSector`, `BankingSector`, `ITServicesSector`, `PharmaSector`, `FMCGSector`, `GenericSector`
- Calls `framework.extract_sector_metrics(metrics, financial_data)`
- Calls `framework.identify_risks(metrics, financial_data)`

**Sector alias examples:**
- "Automobile", "Auto" → AutomobileSector
- "Banking", "Banks", "Financial Services" → BankingSector
- "IT", "Technology", "Software" → ITServicesSector
- "Healthcare", "Pharma", "Pharmaceuticals" → PharmaSector
- "FMCG", "Consumer Staples" → FMCGSector
- Anything else → GenericSector

**Output stored in `fa_analyses.sector_analysis`:**
```json
{
  "sector_name": "Automobile",
  "sector_matched": true,
  "framework": "...",
  "sector_metrics": { "ebitda_margin": 14.2, "roce": 18.5, ... },
  "sector_risks": [{ "severity": "MEDIUM", "category": "...", ... }]
}
```

---

### 10. Peer Comparison Agent
**Stage:** 9  
**Location:** `_find_peers()` in orchestrator.py

**What it does:**
- Queries `stocks` table for other active stocks in the same sector
- Picks up to 10 peers
- Returns peer list with basic info

**Current limitation:** Peers have no financial metrics. Only name, symbol, market cap from the DB. Actual ratio comparison (ROCE, margins, etc.) would require a separate yfinance fetch per peer.

**Output stored in `fa_analyses.peers`:**
```json
{
  "sector": "Automobile",
  "peer_count": 8,
  "peers": [
    { "stock_id": "NSE:MARUTI", "company_name": "Maruti Suzuki", "symbol": "MARUTI", "market_cap": 3800000000000 },
    ...
  ],
  "company_metrics": { "ebitda_margin": 14.2, "roce": 18.5, ... },
  "note": "Peer metric values require separate analysis runs per peer company"
}
```

---

### 11. Risk Analysis Agent
**Stage:** 10  
**Location:** `_identify_universal_risks()` and `_identify_catalysts()` in orchestrator.py

**Universal risk checks:**
- High D/E (>2.0x) → HIGH severity
- Weak interest coverage (<2.0x) → HIGH/MEDIUM
- Low ROCE (<8%) → MEDIUM
- Declining ROCE trend → MEDIUM
- Negative FCF → MEDIUM
- Low cash conversion FCF/PAT (<30%) → LOW
- Very high P/E (>50x) → MEDIUM

**Catalyst checks:**
- Improving ROCE trend
- Strong FCF (FCF/PAT >80%)
- Strong revenue growth (>15% CAGR)
- Deleveraging (D/E trend improving)
- Margin expansion (EBITDA trend improving)

**Output stored in `fa_analyses.risks` and `fa_analyses.catalysts`** (arrays of risk/catalyst objects)

---

### 12. Scoring Engine
**Stage:** 11  
**File:** `backend/app/calculations/scoring.py`  
**Functions:** `compute_scores()`, `compute_data_quality()`, `compute_confidence()`

**What it does:**
- Maps each metric to a 0-100 score using piecewise linear thresholds
- Weights 6 categories: Growth, Profitability, Cash Flow, Balance Sheet, Efficiency, Valuation
- Sector weight overrides for 39 sector_names (`UNIVERSAL_WEIGHTS` default + `SECTOR_WEIGHTS` per-sector, `backend/app/calculations/scoring.py`)
- Computes weighted average as `overall` score (0-100)
- Classifies: POOR (<35) / WEAK (35-50) / FAIR (50-65) / GOOD (65-80) / STRONG (≥80) — see `classify_overall_rating()`
- `compute_data_quality()`: based on metric completeness and historical depth
- `compute_confidence()`: based on data quality + metric count + sector match

**Valuation weight is deliberately small (2026-09-23)**: cut to ~40% of its
previous value across every one of the 39 weight dicts (universal default
0.14 → 0.06; ranges 0.02–0.10 depending on sector, was 0.06–0.25) — explicit
product decision: a stock trading expensive BECAUSE it's genuinely
high-quality shouldn't have its `overall` quality score dragged down much
by that market-set price. `valuation_view` (CHEAP/ATTRACTIVE/FAIR/EXPENSIVE/
VERY_EXPENSIVE, in `scores`) remains the dedicated "is this cheap or
expensive" signal, kept fully independent of `overall`. Freed weight was
redistributed proportionally across the other 5 categories, not handed to
any one of them — every dict still sums to exactly 1.00. The SAME numbers
are mirrored in each `SectorFramework` subclass's own `SECTOR_WEIGHTS`
class attribute (`backend/app/sectors/*.py`) — that copy only feeds the
display-only `sector_analysis.sector_weights` API field, but must be kept
in sync by hand whenever `scoring.py`'s weights change, or the UI's
"sector weights" panel will show different numbers than what the `overall`
score actually used.

**Output stored in `fa_analyses.scores`:**
```json
{
  "overall": 74.3,
  "growth": 81.0,
  "profitability": 78.5,
  "cash_flow": 69.0,
  "balance_sheet": 72.0,
  "efficiency": 65.0,
  "valuation": 58.0,
  "overall_rating": "GOOD",
  "valuation_view": "EXPENSIVE",
  "sector_matched": true,
  "red_flags": ["High Debt-to-Equity", "Low Cash Conversion"],
  "weights": { "growth": 0.25, "profitability": 0.21, "cash_flow": 0.19, "balance_sheet": 0.19, "efficiency": 0.10, "valuation": 0.06 }
}
```

---

### 13. AI Analyst Agent (GPT-OSS 20B)
**Stage:** 12  
**File:** `backend/app/llm/client.py` + orchestrator.py `_run_ai_analysis()`  
**Model:** GPT-OSS 20B via Groq (`https://api.groq.com/openai/v1`)

**What it does:**
- Builds compact structured JSON context from all preceding stage outputs
- Sends to LLM with a strict system prompt: "You are a professional equity research analyst. You ONLY interpret pre-calculated data. Never invent financial values."
- Requests response in an exact JSON schema
- Falls back to default values if LLM fails (pipeline doesn't stop)

**Context sent to LLM:**
```json
{
  "company": { "name": "Tata Motors", "sector": "Automobile", "industry": "Automobile" },
  "scores": { "overall": 74.3, "growth": 81.0, ... },
  "key_metrics": { "revenue_cagr_3y": 12.4, "ebitda_margin": 14.2, ... },
  "trends": { "roce_trend": "IMPROVING", "ebitda_margin_trend": "STABLE", ... },
  "sector_framework": "Automobile",
  "risks_count": 3,
  "high_risks": [...],
  "catalysts": [...]
}
```

**Output stored in `fa_analyses.ai_analysis`:**
```json
{
  "rating": "GOOD",
  "conviction": "MEDIUM",
  "confidence": 0.78,
  "valuation_view": "FAIR",
  "investment_thesis": ["..."],
  "bull_case": ["...", "..."],
  "bear_case": ["...", "..."],
  "key_risks": ["...", "..."],
  "catalysts": ["...", "..."],
  "monitoring_points": ["...", "...", "..."],
  "competitive_position": "...",
  "industry_attractiveness": "...",
  "valuation_commentary": "..."
}
```

**Non-critical:** If LLM fails, this stage is marked FAILED but the pipeline continues.

---

### 14. Report Generation Agent
**Stage:** 13  
**File:** `backend/app/services/report_service.py`  
**Function:** `generate_pdf_report(analysis_id, db)`  
**Library:** ReportLab

**What it does:**
- Loads full analysis data from PostgreSQL
- Generates a multi-page PDF equity research report
- Saves to `./reports/{analysis_id}.pdf`
- Updates `fa_analyses.report_path`

**Current PDF sections:**
1. Cover page (company name, sector, date)
2. Investment Snapshot (score, confidence, AI rating)
3. Score Breakdown (bar chart per category)
4. Key Financial Metrics (metric table)
5. Risk Factors (severity-colored list)
6. Catalysts
7. AI Analysis (thesis, bull/bear case)
8. Disclaimer

**Non-critical:** If PDF fails, stage is marked FAILED but the analysis result is fully accessible in the UI.

---

## Agent Communication Protocol

Currently agents communicate by:
1. Reading from `fa_analyses` record (in-memory Python dict)
2. Writing to `fa_analyses` JSONB columns
3. Writing stage status to `fa_analysis_stages`

The **planned** A2A protocol (Phase 11) would use structured messages:
```json
{
  "analysis_id": "FA-2026-000123",
  "from_agent": "financial_data_agent",
  "to_agent": "calculation_engine",
  "message_type": "DATA_READY",
  "payload": { "income": {...}, "balance": {...} },
  "confidence": 0.96,
  "timestamp": "2026-08-29T14:30:00Z"
}
```

This is not yet implemented — agents pass data through the DB JSONB columns.

---

## How to Add a New Sector Framework

1. Create `backend/app/sectors/my_sector.py`:

```python
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag

class MySector(SectorFramework):
    sector_name = "My Sector"
    
    def extract_sector_metrics(self, metrics: dict, financial_data: dict) -> dict:
        return {
            "ebitda_margin": metrics.get("ebitda_margin"),
            "roce": metrics.get("roce"),
            # ... sector-specific metrics
        }
    
    def identify_risks(self, metrics: dict, financial_data: dict) -> list[dict]:
        risks = []
        # ... sector-specific risk checks
        return risks
    
    def describe(self) -> str:
        return "My Sector Framework v1"
```

2. Register in `backend/app/sectors/registry.py`:
```python
from app.sectors.my_sector import MySector

SECTOR_MAP = {
    "My Sector": MySector,
    "MySector Alias": MySector,
    ...
}
```

---

## Scoring Weight Override for a New Sector

In `backend/app/calculations/scoring.py`, add to `SECTOR_WEIGHTS` — AND mirror
the identical dict in the new sector's own `SectorFramework` subclass's
`SECTOR_WEIGHTS` class attribute under `backend/app/sectors/`, or the
display-only `sector_analysis.sector_weights` API field will show different
numbers than what actually computed `overall`. Keep `valuation` low (0.02–0.10
across every existing sector, see §12 above) unless the sector has a specific,
documented reason to weigh it more (e.g. Fintech at 0.10, the current
maximum, because P/E is unreliable for pre-profit fintechs) — every dict
must still sum to exactly 1.00:

```python
SECTOR_WEIGHTS = {
    ...
    "My Sector": {
        "growth":         0.22,
        "profitability":  0.27,
        "cash_flow":      0.19,
        "balance_sheet":  0.19,
        "efficiency":     0.08,
        "valuation":      0.05,
    },
}
```
