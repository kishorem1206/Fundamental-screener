# MASTER IMPLEMENTATION PROMPT

# AI-Powered Single-Stock Fundamental Analysis & Research Platform

## 0. ROLE

You are a senior full-stack architect, Python engineer, PostgreSQL engineer, AI-agent engineer, MCP engineer, financial-data engineer, quantitative analyst, UI/UX designer, and QA engineer.

Build a production-quality **single-stock fundamental analysis platform** inside the existing application.

The existing application already contains approximately **750 stocks in PostgreSQL**, including sector/category information.

DO NOT replace, reset, truncate, delete, or recreate the existing database.

DO NOT break existing CRM/application functionality.

First inspect the existing project, database schema, APIs, frontend architecture, authentication, environment configuration, migrations, and existing stock tables.

Extend the existing system using backward-compatible migrations.

The primary purpose of this module is:

> Allow the user to select ONE sector and ONE stock from the existing PostgreSQL stock universe, perform a comprehensive fundamental analysis using deterministic financial calculations + specialized validation agents + sector-specific analysis + agent-to-agent communication + MCP tools + GPT-OSS 20B, assign transparent scores, identify risks/opportunities, and finally generate a professionally designed PDF equity-research report.

The system must analyze ONE stock at a time.

Do not build the initial UX around batch analysis of all 750 stocks.

The architecture should be capable of batch processing later, but the primary workflow is single-stock analysis.

---

# 1. FIRST TASK — INSPECT THE EXISTING APPLICATION

Before writing code:

1. Inspect repository structure.
2. Identify backend framework.
3. Identify frontend framework.
4. Identify PostgreSQL connection.
5. Identify ORM/query layer.
6. Identify existing Alembic/database migration system.
7. Inspect existing stock/company tables.
8. Inspect sector/category relationships.
9. Identify stock identifiers:

   * company ID
   * symbol
   * exchange
   * ISIN if available
   * sector
   * industry
10. Identify existing market-data tables/services.
11. Identify existing APIs.
12. Identify authentication/authorization.
13. Identify existing UI design system.
14. Identify existing charting library.
15. Identify existing background-job infrastructure.
16. Identify existing logging system.
17. Identify existing environment variables.
18. Identify existing AI/LLM integrations if any.

Create an internal implementation map before changing anything.

The existing 750-stock database must remain the source of truth for the stock-selection universe.

---

# 2. CORE USER EXPERIENCE

The user should see a dedicated module:

## Fundamental Research

Main screen:

```text
Fundamental Research

Select Sector
[ Automobile ▼ ]

Select Stock
[ Tata Motors ▼ ]

[ Start Fundamental Analysis ]
```

The stock dropdown must be dynamically populated from the existing PostgreSQL database.

The user must NOT manually type arbitrary stocks unless an optional search field is provided.

Sector selection should filter the stock list.

Example:

```text
Sector:
Automobile

Stocks:
Tata Motors
Mahindra & Mahindra
Maruti Suzuki
Eicher Motors
Hero MotoCorp
...
```

Only stocks existing in the database should be selectable.

After selecting the stock:

```text
Selected Company

Tata Motors
Automobile
NSE: TATAMOTORS

[ Analyze Stock ]
```

---

# 3. ANALYSIS LIFECYCLE

When the user clicks:

"Analyze Stock"

create a unique:

```text
analysis_id
```

The backend creates an analysis job.

Example:

```text
analysis_id:
FA-2026-000123
```

The analysis pipeline should be asynchronous.

Never keep the HTTP request open for the entire analysis.

Use:

```text
Frontend
    ↓
POST /fundamental-analysis
    ↓
Create analysis job
    ↓
Background worker
    ↓
Agent orchestration
    ↓
Validation
    ↓
Scoring
    ↓
AI interpretation
    ↓
Report generation
    ↓
Completed
```

---

# 4. ANALYSIS STATUS UI

While processing, show a beautiful progress screen.

Example:

```text
Analyzing Tata Motors

Overall Progress
████████████████░░░░░░ 78%

✓ Company identification
✓ Financial data collection
✓ Historical financial analysis
✓ Ratio calculations
✓ Balance-sheet validation
✓ Cash-flow validation
✓ Sector-specific analysis
✓ Peer comparison
◉ AI investment analysis
○ Risk analysis
○ Report generation
```

Show:

* current stage
* completed stages
* percentage
* elapsed time
* errors/warnings
* data quality
* validation status

Allow the user to leave the page and return later.

The analysis must persist in PostgreSQL.

---

# 5. ANALYSIS PIPELINE

Implement the following pipeline:

```text
                    ANALYSIS ORCHESTRATOR
                              │
                              ▼
                  Company Identification Agent
                              │
                              ▼
                    Data Collection Agent
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
       Income Statement   Balance Sheet    Cash Flow
           Agent             Agent           Agent
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                    Financial Calculation Engine
                              │
                              ▼
                    Universal Validation Agent
                              │
                              ▼
                    Sector Detection Agent
                              │
                              ▼
                    Sector Analysis Agent
                              │
                              ▼
                     Peer Comparison Agent
                              │
                              ▼
                       Risk Agent
                              │
                              ▼
                       Scoring Engine
                              │
                              ▼
                    Data Quality Agent
                              │
                              ▼
                     GPT-OSS 20B Analyst
                              │
                              ▼
                     Recommendation Engine
                              │
                              ▼
                     Report Generation Agent
                              │
                              ▼
                         PDF Report
```

---

# 6. DO NOT LET THE LLM CONTROL FINANCIAL CALCULATIONS

This is extremely important.

Financial calculations must be performed by deterministic Python code.

The LLM must NOT be the authoritative calculator.

Python calculates:

* CAGR
* margins
* ROE
* ROCE
* ROIC
* debt ratios
* liquidity ratios
* valuation ratios
* cash-flow ratios
* working-capital ratios
* sector scores
* percentile rankings
* normalized scores

The LLM receives the validated structured output and interprets it.

---

# 7. GPT-OSS 20B

Use:

```text
GPT-OSS 20B
```

as the primary reasoning/interpretation model.

Make the LLM provider configurable through environment variables.

Example:

```env
LLM_MODEL=gpt-oss-20b
LLM_BASE_URL=
LLM_API_KEY=
```

Do not hard-code the model endpoint.

Create an abstraction:

```python
LLMClient
```

so the model can later be changed without rewriting the application.

The LLM must receive structured JSON rather than raw database dumps.

---

# 8. MCP ARCHITECTURE

Implement an MCP tool layer.

Agents should access controlled data through MCP tools.

Create tools such as:

```text
get_company
get_sector
get_industry
get_financial_history
get_income_statement
get_balance_sheet
get_cash_flow
get_market_data
get_valuation_data
get_shareholding
get_sector_metrics
get_peer_group
calculate_metric
validate_metric
get_analysis_context
get_previous_analysis
save_agent_result
get_company_risks
generate_report_data
```

Each tool must have:

* strict input schema
* strict output schema
* authentication/authorization where appropriate
* logging
* error handling
* timeout
* validation

Never allow an LLM to execute arbitrary SQL.

---

# 9. AGENT-TO-AGENT COMMUNICATION

Create a structured A2A communication protocol.

Agents must communicate using structured messages.

Example:

```json
{
  "analysis_id": "FA-2026-000123",
  "company_id": 123,
  "agent": "financial_validation_agent",
  "message_type": "metric_validation",
  "payload": {
    "metric": "ROCE",
    "value": 24.71,
    "period": "FY2026",
    "status": "validated"
  },
  "confidence": 0.96,
  "timestamp": "..."
}
```

Do not rely on free-form text between agents for critical data.

---

# 10. AGENT DEFINITIONS

Implement separate agents.

## 10.1 Orchestrator Agent

Responsibilities:

* create analysis
* manage workflow
* invoke agents
* track dependencies
* retry failed agents
* handle timeouts
* aggregate outputs
* never fabricate missing data

---

## 10.2 Company Identification Agent

Validate:

* company
* symbol
* exchange
* sector
* industry
* company ID

---

## 10.3 Financial Data Agent

Collect:

### Income Statement

* Revenue
* Cost of goods/services
* Gross profit
* EBITDA
* EBIT
* PBT
* PAT
* EPS

### Balance Sheet

* Total assets
* Current assets
* Cash
* Inventory
* Receivables
* Equity
* Total debt
* Current liabilities
* Non-current liabilities

### Cash Flow

* CFO
* Capex
* CFI
* CFF
* FCF

Collect multiple years where available.

Prefer at least:

```text
5 years
```

and ideally:

```text
10 years
```

---

# 11. UNIVERSAL FUNDAMENTAL METRICS

Calculate all applicable metrics.

## Growth

* Revenue CAGR 3Y
* Revenue CAGR 5Y
* Revenue CAGR 10Y
* EBITDA CAGR
* EBIT CAGR
* PAT CAGR
* EPS CAGR
* FCF CAGR

## Profitability

* Gross margin
* EBITDA margin
* EBIT margin
* PAT margin
* ROE
* ROCE
* ROIC

## Cash Flow

* CFO
* FCF
* CFO/PAT
* FCF/PAT
* FCF margin
* FCF yield

## Balance Sheet

* Debt/equity
* Net debt
* Net debt/EBITDA
* Interest coverage
* Current ratio
* Quick ratio

## Efficiency

* Asset turnover
* Inventory days
* Receivable days
* Payable days
* Cash conversion cycle

## Valuation

* Market capitalization
* Enterprise value
* P/E
* EV/EBITDA
* EV/Sales
* P/B
* P/FCF
* FCF yield
* Dividend yield
* PEG

Where a ratio cannot be meaningfully calculated, return:

```text
NOT_APPLICABLE
```

rather than:

```text
0
```

Never fabricate missing values.

---

# 12. HISTORICAL TREND ANALYSIS

Do not analyze only the latest year.

Show:

* 3Y
* 5Y
* 10Y where available

For every important metric determine:

```text
improving
stable
deteriorating
volatile
insufficient_data
```

Examples:

```text
ROCE:
2022 16.2%
2023 18.4%
2024 21.1%
2025 23.8%
2026 25.4%

Trend:
STRONGLY IMPROVING
```

---

# 13. DATA VALIDATION AGENTS

Every important financial dataset must pass validation.

## Validation checks

Detect:

* missing values
* duplicate periods
* inconsistent units
* negative denominators
* impossible ratios
* sudden unexplained changes
* accounting anomalies
* restatements
* exceptional items
* acquisition distortions
* discontinued operations
* currency inconsistencies
* quarterly/annual inconsistencies

Each metric receives:

```text
VALID
WARNING
FAILED
NOT_APPLICABLE
```

and:

```text
confidence_score
```

---

# 14. SECTOR FRAMEWORK

Create a configurable sector registry.

Do NOT hard-code sector logic into individual agents.

Use configuration/database-driven definitions.

Structure:

```text
Sector
    ↓
Industry
    ↓
Metrics
    ↓
Weights
    ↓
Thresholds
    ↓
Validation Rules
    ↓
Red Flags
    ↓
Scoring Rules
```

Create initial frameworks for major sectors.

At minimum:

* Automobile
* Auto Ancillaries
* Banks
* NBFC
* Insurance
* IT Services
* Pharma
* Healthcare
* FMCG
* Consumer Durables
* Chemicals
* Specialty Chemicals
* Metals
* Mining
* Cement
* Oil & Gas
* Power
* Utilities
* Telecom
* Retail
* Real Estate
* Construction
* Infrastructure
* Capital Goods
* Industrials
* Defence
* Aviation
* Hotels
* Logistics
* Media
* Renewable Energy
* Electronics/Semiconductors

The framework must be extensible.

---

# 15. AUTOMOBILE FRAMEWORK

For automobile companies calculate and analyze:

### Growth

* vehicle volume growth
* revenue CAGR
* EPS CAGR
* export growth

### Market Position

* market share
* market-share trend
* segment share
* premium segment share

### Pricing

* ASP
* ASP growth
* price/mix growth

### Profitability

* gross margin
* EBITDA margin
* EBIT margin
* ROCE
* ROIC

### Capital Efficiency

* asset turnover
* capacity utilization
* capex/revenue

### Cash Flow

* CFO
* FCF
* FCF/PAT

### Balance Sheet

* debt/equity
* net debt/EBITDA
* interest coverage

### Working Capital

* inventory days
* receivable days
* payable days
* cash conversion cycle

### EV

* EV penetration
* EV volume growth
* EV market share
* EV revenue contribution
* EV margin where available
* battery localization
* EV R&D

### Other

* R&D/revenue
* exports/revenue
* commodity sensitivity
* dealer inventory
* premiumization

Automobile scoring should NOT be applied to banks or unrelated sectors.

---

# 16. BANKING FRAMEWORK

Implement separate banking logic including:

* loan growth
* deposit growth
* NIM
* ROA
* ROE
* GNPA
* NNPA
* PCR
* credit cost
* CASA
* capital adequacy
* slippage ratio
* provision coverage
* cost-to-income
* valuation
* book value
* P/B

---

# 17. NBFC FRAMEWORK

Include:

* AUM growth
* loan growth
* NIM
* ROA
* ROE
* GNPA
* NNPA
* credit cost
* collection efficiency
* capital adequacy
* borrowing cost
* asset-liability mismatch
* P/B
* P/E

---

# 18. IT SERVICES FRAMEWORK

Include:

* revenue growth
* constant-currency growth where available
* EBIT margin
* EBITDA margin
* employee growth
* revenue/employee
* utilization
* attrition
* deal wins
* order book
* client concentration
* FCF
* ROCE
* ROIC
* net cash/debt
* P/E
* EV/EBITDA

---

# 19. PHARMA FRAMEWORK

Include:

* revenue growth
* EBITDA margin
* R&D/revenue
* ANDA/product pipeline where available
* domestic/international mix
* regulated-market exposure
* ROCE
* FCF
* debt
* product concentration
* regulatory risk

---

# 20. FMCG FRAMEWORK

Include:

* volume growth
* revenue growth
* price/mix growth
* gross margin
* EBITDA margin
* ROCE
* ROIC
* distribution strength
* premiumization
* rural exposure
* working capital
* FCF
* valuation

---

# 21. SECTOR CONFIGURATION ENGINE

Every sector definition should contain:

```json
{
  "sector": "Automobile",
  "metrics": [
    {
      "name": "ROCE",
      "weight": 0.12,
      "importance": "high",
      "direction": "higher_is_better"
    }
  ],
  "red_flags": [],
  "thresholds": {},
  "peer_rules": {}
}
```

Allow this to be updated without changing Python source code.

---

# 22. SCORING ENGINE

Create transparent scoring.

Overall score:

```text
0–100
```

Suggested universal components:

```text
Growth                  15
Profitability           20
Cash Flow               15
Balance Sheet           15
Capital Efficiency      15
Valuation               10
Business Quality        10
```

However:

SECTOR-SPECIFIC WEIGHTS MUST OVERRIDE UNIVERSAL WEIGHTS where appropriate.

For example:

Automobile:

```text
Growth               15%
Profitability        20%
Cash Flow            15%
Balance Sheet        10%
Capital Efficiency   15%
Market Position      10%
EV Transition         5%
Valuation             5%
Business Quality      5%
```

Bank:

```text
Asset Quality
Profitability
Capital Adequacy
Growth
Deposit Franchise
Valuation
etc.
```

The final score must show component-level scores.

---

# 23. SCORE TRANSPARENCY

Never return only:

```text
Score = 84
```

Return:

```text
Overall Score: 84/100

Growth:              91
Profitability:       88
Cash Flow:           79
Balance Sheet:       94
Capital Efficiency:  87
Valuation:           72
Business Quality:    90
```

For each score show:

* metrics contributing to score
* metric values
* weight
* percentile
* score
* validation status

---

# 24. PEER ANALYSIS

Automatically create a peer group from the same sector/industry.

Use the existing database sector classification first.

Peer selection should consider:

* sector
* industry
* business model
* market cap
* geography
* product category

Compare:

* revenue growth
* EBITDA margin
* ROCE
* ROE
* FCF
* debt
* valuation
* sector-specific metrics

Show percentile ranking.

Example:

```text
ROCE
Company: 27.4%
Sector median: 18.1%
Percentile: 91st
```

---

# 25. RED-FLAG ENGINE

Create an independent risk engine.

Examples:

### Financial

* debt spike
* declining ROCE
* declining margins
* negative FCF
* weak cash conversion
* receivables spike
* inventory spike
* interest coverage deterioration

### Valuation

* excessive P/E
* excessive EV/EBITDA
* valuation far above peers
* growth expectations inconsistent with valuation

### Business

* market-share loss
* product concentration
* customer concentration
* geographic concentration
* regulatory exposure
* commodity exposure

### Data

* insufficient data
* conflicting financial statements
* low confidence
* missing historical periods

Each risk:

```json
{
  "severity": "HIGH",
  "category": "BALANCE_SHEET",
  "title": "...",
  "description": "...",
  "evidence": {},
  "confidence": 0.94
}
```

---

# 26. CATALYST ENGINE

Identify positive catalysts.

Examples:

* new product launch
* margin expansion
* capacity expansion
* deleveraging
* market-share gains
* EV adoption
* new geography
* pricing power
* operating leverage
* industry recovery
* restructuring
* improved capital allocation

Separate:

```text
Structural catalysts
Cyclical catalysts
Company-specific catalysts
```

---

# 27. CYCLICALITY ANALYSIS

For cyclical sectors, analyze historical cycles.

Determine:

* peak margin
* trough margin
* average margin
* peak ROCE
* trough ROCE
* revenue cycle
* earnings cycle
* FCF cycle

The AI must not assume current earnings are sustainable without considering cyclicality.

---

# 28. VALUATION ENGINE

Calculate:

* P/E
* EV/EBITDA
* EV/Sales
* P/B
* P/FCF
* FCF yield
* dividend yield
* PEG

Where historical data is available, compare current valuation against:

* 3-year average
* 5-year average
* historical range
* sector median
* peer median

Classify:

```text
CHEAP
ATTRACTIVE
FAIR
EXPENSIVE
VERY_EXPENSIVE
```

Do not use valuation multiples blindly for sectors where they are inappropriate.

---

# 29. NORMALIZED EARNINGS

For cyclical companies calculate normalized earnings where sufficient historical data exists.

Do not use a single peak-year PAT to calculate valuation.

Provide:

```text
Reported EPS
Normalized EPS
Current P/E
Normalized P/E
```

Clearly explain the methodology.

---

# 30. AI ANALYST — GPT-OSS 20B

Only call GPT-OSS 20B after all deterministic analysis is completed.

Input:

```text
company profile
validated financials
historical trends
calculated ratios
sector framework
peer comparison
valuation
red flags
catalysts
data-quality score
```

The AI must answer:

## Business

* What does the company do?
* How attractive is the industry?
* What are the competitive advantages?

## Growth

* Is growth strong?
* Is growth sustainable?
* What drives it?

## Profitability

* Are margins improving?
* Is ROCE improving?
* Is there operating leverage?

## Cash Flow

* Is profit converting into cash?
* Is FCF sustainable?

## Balance Sheet

* Is debt manageable?
* Is financial risk increasing?

## Competitive Position

* Market share
* pricing power
* product strength
* moat

## Valuation

* cheap/fair/expensive
* valuation vs peers
* valuation vs history
* assumptions implied by current valuation

## Risks

* financial
* business
* industry
* regulatory
* technological
* valuation

## Catalysts

* near-term
* medium-term
* structural

## Investment Thesis

Explain:

```text
Why an investor might consider this company
```

## Bear Case

Explain:

```text
What could make the investment thesis wrong
```

## What To Monitor

Provide 5–10 measurable indicators.

---

# 31. AI OUTPUT MUST BE STRUCTURED

Do not store only a paragraph.

Store structured JSON:

```json
{
  "rating": "STRONG",
  "conviction": "HIGH",
  "confidence": 0.89,
  "business_quality": 91,
  "growth_quality": 87,
  "financial_quality": 93,
  "valuation_view": "FAIR",
  "thesis": [],
  "risks": [],
  "catalysts": [],
  "monitoring_points": [],
  "bear_case": [],
  "bull_case": []
}
```

Then render this JSON into the UI and PDF.

---

# 32. AI GUARDRAILS

The AI must:

* never invent financial values
* never invent company facts
* never invent ratios
* never override validated calculations
* clearly distinguish facts from interpretation
* identify missing data
* mention uncertainty
* provide evidence for major conclusions

If data is unavailable:

```text
Data unavailable
```

not an invented estimate.

---

# 33. DATA QUALITY SCORE

Create:

```text
Data Quality Score: 0–100
```

Based on:

* completeness
* source quality
* historical depth
* validation success
* consistency
* freshness

Example:

```text
Data Quality: 94/100
```

Show this prominently.

---

# 34. CONFIDENCE SCORE

Create separate:

```text
Analysis Confidence: 0–100
```

This should depend on:

* data quality
* number of validated metrics
* sector framework coverage
* peer availability
* historical depth
* AI uncertainty

Never confuse:

```text
Fundamental Score
```

with:

```text
Confidence Score
```

---

# 35. FRONTEND — DESIGN

Create a premium financial-research interface.

Visual direction:

* dark professional research-terminal aesthetic
* excellent typography
* subtle gradients
* clean cards
* restrained animations
* high information density
* excellent spacing
* responsive layout
* desktop-first but mobile compatible

Avoid making it look like a generic admin dashboard.

Use:

```text
dark background
soft cards
high-contrast typography
subtle borders
clean charts
pill badges
progress indicators
```

---

# 36. MAIN FUNDAMENTAL RESEARCH PAGE

Create:

```text
Fundamental Research
```

Top section:

```text
Select Sector
[ Automobile ▼ ]

Select Stock
[ Tata Motors ▼ ]

[ Start Analysis ]
```

Below:

```text
Recent Analyses
```

Show:

* company
* sector
* date
* score
* rating
* confidence
* status
* report availability

---

# 37. ANALYSIS DASHBOARD

After completion:

```text
Tata Motors
Automobile

Fundamental Score
87 / 100

STRONG FUNDAMENTALS

Confidence
91%

Data Quality
95%
```

Then:

```text
Growth        91
Profitability 94
Cash Flow     82
Balance Sheet 90
Efficiency    87
Valuation     73
```

---

# 38. COMPANY PAGE SECTIONS

Use tabs/sections:

```text
Overview
Financials
Growth
Profitability
Cash Flow
Balance Sheet
Valuation
Sector Analysis
Peer Comparison
Risks
Catalysts
AI Analysis
Report
```

---

# 39. FINANCIAL CHARTS

Include interactive charts for:

### Revenue

5Y/10Y

### EBITDA

5Y/10Y

### PAT

5Y/10Y

### EPS

5Y/10Y

### FCF

5Y/10Y

### ROCE

5Y/10Y

### ROE

5Y/10Y

### Debt

5Y/10Y

Use clear trend visualization.

Allow:

```text
Annual
Quarterly
```

where data exists.

---

# 40. RATIO TABLE

Create a professional table:

```text
Metric             Current    3Y Avg   5Y Avg   Sector   Trend
ROCE               27.4%      22.1%    19.8%     18.2%    ↑
EBITDA Margin      15.2%      13.9%    12.7%     11.8%    ↑
Debt/Equity         0.21       0.31     0.42       0.56    ↓
FCF/PAT             91%        84%      79%        73%    ↑
```

---

# 41. SECTOR SCORECARD

Display only metrics relevant to the selected sector.

For Automobile:

```text
Market Share
Volume Growth
ASP Growth
EBITDA Margin
ROCE
FCF Conversion
Capacity Utilisation
EV Penetration
R&D/Revenue
Debt
```

For banks:

show banking metrics.

For IT:

show IT metrics.

Do not display irrelevant metrics.

---

# 42. PEER COMPARISON UI

Example:

```text
                 Company   Peer Median   Percentile

Revenue Growth    14.2%      10.1%          82
ROCE              27.4%      18.2%          91
EBITDA Margin     15.2%      12.7%          78
Debt/Equity        0.21       0.39           84
P/E               24.3x      21.8x          42
```

---

# 43. RED FLAGS UI

Use severity:

```text
HIGH
MEDIUM
LOW
```

Example:

```text
⚠ High Valuation

Current P/E is significantly above
the historical median.

Evidence:
Current P/E: 34x
5Y Median: 23x
Peer Median: 21x
```

---

# 44. AI INVESTMENT VIEW

Create a visually prominent card:

```text
AI FUNDAMENTAL VIEW

Rating:
STRONG

Conviction:
HIGH

Valuation:
FAIR

Fundamental Score:
87/100

Confidence:
91%
```

Then sections:

```text
Investment Thesis
Bull Case
Bear Case
Key Risks
Catalysts
What To Monitor
```

---

# 45. REPORT GENERATION

At the end of the analysis:

```text
[ Generate PDF Report ]
```

If the analysis already generated a report:

```text
[ View Report ]
[ Download Report ]
```

Generate a professionally designed PDF.

Use a proper PDF generation library.

Do not generate a screenshot of the webpage and call it a report.

---

# 46. PDF REPORT STRUCTURE

## Cover

```text
FUNDAMENTAL EQUITY RESEARCH

Tata Motors

Automobile

Analysis Date
```

---

## Page 2 — Investment Snapshot

Show:

```text
Fundamental Score
87/100

Confidence
91%

Data Quality
95%

AI Rating
STRONG

Valuation
FAIR
```

---

## Page 3 — Business Overview

* business description
* sector
* industry
* major segments
* competitive position

---

## Page 4 — Financial Performance

Charts:

* revenue
* EBITDA
* PAT
* EPS

---

## Page 5 — Profitability

* EBITDA margin
* EBIT margin
* ROE
* ROCE
* ROIC

---

## Page 6 — Cash Flow

* CFO
* FCF
* CFO/PAT
* FCF/PAT
* capex

---

## Page 7 — Balance Sheet

* debt
* cash
* net debt
* debt/equity
* interest coverage
* liquidity

---

## Page 8 — Valuation

* P/E
* EV/EBITDA
* P/B
* P/FCF
* FCF yield
* peer comparison
* historical valuation

---

## Page 9 — Sector Analysis

Show sector-specific metrics.

---

## Page 10 — Peer Comparison

Show company vs peers.

---

## Page 11 — Risks

High/medium/low risks.

---

## Page 12 — Catalysts

Structural/cyclical/company-specific catalysts.

---

## Page 13 — AI Analysis

GPT-OSS 20B:

* investment thesis
* bull case
* bear case
* valuation view
* key risks
* catalysts

---

## Final Page — Investor Checklist

```text
What is working?
What is deteriorating?
What is expensive?
What could surprise positively?
What could go wrong?
What should be monitored every quarter?
```

Include:

```text
This report is an analytical research output,
not a guarantee of future returns.
```

---

# 47. REPORT VERSIONING

Every report must have:

```text
analysis_id
company_id
generated_at
data_timestamp
calculation_version
sector_framework_version
llm_model
llm_prompt_version
```

This allows reproducibility.

---

# 48. DATABASE DESIGN

Extend PostgreSQL using migrations.

Do NOT alter existing stock records destructively.

Create tables logically equivalent to:

```text
fundamental_analyses
analysis_jobs
analysis_stages
financial_periods
income_statements
balance_sheets
cash_flows
financial_metrics
metric_definitions
sector_definitions
sector_metric_definitions
metric_validations
peer_groups
peer_comparisons
company_scores
score_components
risk_flags
catalysts
agent_runs
agent_messages
agent_validations
ai_analyses
analysis_reports
data_sources
```

Use foreign keys to existing company/stock records.

---

# 49. ANALYSIS TABLE

Example:

```text
fundamental_analyses

id
company_id
sector_id
status
overall_score
confidence_score
data_quality_score
ai_rating
valuation_rating
started_at
completed_at
created_at
updated_at
```

Statuses:

```text
QUEUED
RUNNING
VALIDATING
AI_ANALYSIS
REPORT_GENERATION
COMPLETED
FAILED
CANCELLED
```

---

# 50. AGENT RUN TABLE

Store every agent execution.

```text
agent_runs

id
analysis_id
agent_name
status
input_hash
output_json
confidence
started_at
completed_at
error
retry_count
```

This creates a complete audit trail.

---

# 51. METRIC VALIDATION TABLE

Store:

```text
analysis_id
metric_id
period
raw_value
calculated_value
validation_status
validation_message
confidence
source
calculation_version
```

---

# 52. API ENDPOINTS

Implement endpoints similar to:

```text
GET /api/fundamental/sectors

GET /api/fundamental/sectors/{sector_id}/stocks

GET /api/fundamental/stocks/{stock_id}

POST /api/fundamental/analyses

GET /api/fundamental/analyses/{analysis_id}

GET /api/fundamental/analyses/{analysis_id}/status

GET /api/fundamental/analyses/{analysis_id}/financials

GET /api/fundamental/analyses/{analysis_id}/metrics

GET /api/fundamental/analyses/{analysis_id}/scores

GET /api/fundamental/analyses/{analysis_id}/peers

GET /api/fundamental/analyses/{analysis_id}/risks

GET /api/fundamental/analyses/{analysis_id}/ai-analysis

POST /api/fundamental/analyses/{analysis_id}/generate-report

GET /api/fundamental/analyses/{analysis_id}/report
```

---

# 53. JOB SYSTEM

Analysis must be background-job based.

Implement:

```text
analysis_job
```

with stages.

Allow:

* retries
* timeout
* resume
* cancellation
* partial failure
* status tracking

If one agent fails, do not destroy the entire analysis.

Mark the affected stage:

```text
FAILED
```

and retry according to policy.

---

# 54. CACHING

Cache data that does not need to be repeatedly fetched.

Cache:

* company metadata
* historical financial statements
* sector definitions
* peer groups
* market data where appropriate

But store timestamps and source information.

---

# 55. OBSERVABILITY

Implement:

* structured logs
* agent execution logs
* analysis stage logs
* errors
* retries
* latency
* token usage where available
* LLM cost where available
* report-generation status

Create an internal debugging view if appropriate.

---

# 56. SECURITY

Never expose:

* API keys
* database credentials
* internal MCP credentials
* LLM credentials

to frontend.

Validate all user inputs.

Use parameterized queries/ORM.

LLM-generated content must never become executable SQL or code.

---

# 57. TESTING

Create extensive tests.

## Unit tests

Test:

* every financial formula
* CAGR
* ROCE
* ROE
* ROIC
* margins
* FCF
* debt ratios
* valuation ratios
* scoring
* percentile calculation

## Sector tests

Test each sector framework.

## Validation tests

Test:

* missing data
* invalid data
* zero denominator
* negative denominator
* extreme values
* conflicting data

## Agent tests

Test:

* successful execution
* timeout
* retry
* malformed response
* missing data
* invalid LLM JSON

## API tests

Test all endpoints.

## UI tests

Test:

```text
sector selection
stock filtering
analysis start
progress
completed analysis
report generation
```

---

# 58. FAILURE HANDLING

If data is unavailable:

```text
Data unavailable
```

If an agent fails:

```text
Validation agent failed
Retrying...
```

If AI fails:

The deterministic analysis must still remain available.

Show:

```text
Fundamental analysis completed.
AI interpretation unavailable.
```

Never block access to the calculated financial analysis because the LLM is unavailable.

---

# 59. SINGLE-STOCK WORKFLOW

The final workflow should feel extremely simple:

```text
1. Select Sector
        ↓
2. Select Stock
        ↓
3. Click Analyze
        ↓
4. Watch Analysis Progress
        ↓
5. Review Fundamental Dashboard
        ↓
6. Review Sector Analysis
        ↓
7. Review Peer Comparison
        ↓
8. Review Risks
        ↓
9. Review GPT-OSS 20B Analysis
        ↓
10. Generate PDF
        ↓
11. View / Download Report
```

---

# 60. IMPORTANT: EXISTING 750 STOCK DATABASE

The existing PostgreSQL stock universe is mandatory.

Do not create a second independent stock master.

Use the existing database relationship.

If existing data resembles:

```text
stocks
sectors
industries
```

reuse it.

If the existing schema has different names, adapt to it.

Create a compatibility/service layer rather than duplicating records.

---

# 61. NO DESTRUCTIVE MIGRATIONS

Absolutely prohibited:

```text
DROP DATABASE
DROP TABLE
TRUNCATE
DELETE existing stocks
recreate existing stock table
reset existing database
```

Use:

```text
ALTER
CREATE new tables
ADD columns where safe
CREATE indexes
CREATE foreign keys
```

through proper migrations.

---

# 62. PERFORMANCE

The application should support analysis of one company without blocking other application functionality.

Use:

```text
async API
background workers
database connection pooling
caching
parallel independent agents
```

Where safe, independent data-validation agents may execute concurrently.

However, dependencies must be respected.

Example:

```text
Data collection
      ↓
Calculation
      ↓
Validation
      ↓
Scoring
```

Do not run scoring before validation.

---

# 63. FINAL QUALITY REQUIREMENT

The application should feel like a professional equity research product.

Not:

```text
AI chatbot + random ratios
```

Instead:

```text
Financial Data
      +
Deterministic Quantitative Engine
      +
Sector Intelligence
      +
Validation Agents
      +
Peer Analysis
      +
Risk Engine
      +
GPT-OSS 20B
      +
Professional Research Report
```

Every important conclusion must be traceable back to financial data.

---

# 64. IMPLEMENTATION ORDER

Do NOT attempt everything in one uncontrolled change.

Implement in these phases:

## PHASE 1

Repository/database inspection.

## PHASE 2

Architecture and database migrations.

## PHASE 3

Existing-stock integration.

## PHASE 4

Financial data layer.

## PHASE 5

Deterministic calculation engine.

## PHASE 6

Universal metrics.

## PHASE 7

Sector framework.

## PHASE 8

Sector-specific metric engines.

## PHASE 9

Validation agents.

## PHASE 10

MCP tools.

## PHASE 11

A2A agent orchestration.

## PHASE 12

Scoring engine.

## PHASE 13

Peer engine.

## PHASE 14

Risk/catalyst engine.

## PHASE 15

GPT-OSS 20B analyst.

## PHASE 16

Frontend selection workflow.

## PHASE 17

Analysis progress dashboard.

## PHASE 18

Completed analysis dashboard.

## PHASE 19

PDF generation.

## PHASE 20

Testing.

## PHASE 21

Performance optimization.

## PHASE 22

End-to-end single-stock analysis.

---

# 65. AFTER EACH PHASE

After each phase:

1. Run tests.
2. Check database migrations.
3. Verify existing application still works.
4. Verify existing 750 stocks remain intact.
5. Verify API compatibility.
6. Fix errors before moving to the next phase.

Do not accumulate unresolved errors across phases.

---

# 66. ACCEPTANCE TEST

The final system is considered complete only when this exact workflow succeeds:

```text
Open Fundamental Research

↓

Select:
Sector = Automobile

↓

Select:
Stock = an existing automobile stock

↓

Click:
Analyze

↓

System creates analysis_id

↓

Background pipeline starts

↓

Financial data collected

↓

Ratios calculated

↓

Metrics validated

↓

Automobile-specific metrics calculated

↓

Peers identified

↓

Risks identified

↓

Score generated

↓

GPT-OSS 20B produces structured analysis

↓

Dashboard displays:

Overall Score
Confidence
Data Quality
Growth
Profitability
Cash Flow
Balance Sheet
Valuation
Sector Metrics
Peer Comparison
Risks
Catalysts
AI Thesis

↓

Click:
Generate PDF

↓

Professional PDF generated

↓

PDF can be viewed/downloaded

↓

Analysis remains saved in PostgreSQL
```

---

# 67. FINAL DELIVERABLE

Do not stop at backend functionality.

The final implementation must include:

* database
* migrations
* models
* services
* calculations
* sector framework
* agents
* A2A communication
* MCP tools
* validation
* scoring
* peer comparison
* risk engine
* GPT-OSS 20B integration
* APIs
* frontend
* progress tracking
* charts
* report generation
* tests
* documentation

The final result must be a polished, production-quality **single-stock fundamental research platform** integrated with the existing application and existing PostgreSQL stock universe.

Start by inspecting the existing project and database. Do not assume table names, framework names, or existing architecture. Adapt the implementation to the actual codebase.