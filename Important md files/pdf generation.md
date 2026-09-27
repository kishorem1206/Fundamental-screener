Absolutely. Below is the **MD file content** I would use as a specification for your Fundamental Screener's **Premium Equity Research Report + PDF Rendering Engine**.

````md
# Fundamental Screener — Premium Equity Research Report & PDF Engine

## Objective

The Fundamental Screener should not only screen stocks using financial ratios.

It should be capable of generating a professional, source-traceable equity research report for any listed company.

The generated report should combine:

- Financial fundamentals
- Market data
- Business and segment analysis
- Brand intelligence
- Competitor analysis
- Management commentary
- Concall intelligence
- Management guidance tracking
- Risks
- Growth drivers
- Valuation
- Price performance
- Source attribution
- Charts and visualizations

The final PDF should have a premium editorial / institutional equity-research appearance.

Reference design inspiration:

- Branded header
- Company name and report date
- Metric cards
- Business overview
- Brand/segment information
- Revenue and profitability data
- Competitor tables
- 1-year and 5-year price charts
- Rebased competitor performance charts
- Moat / growth / risk sections
- Key questions
- Long-term outlook
- Source ledger

---

# 1. High-Level Architecture

```text
                         FUNDAMENTAL SCREENER
                                  |
                +-----------------+-----------------+
                |                                   |
          SCREENING ENGINE                     RESEARCH ENGINE
                |                                   |
        Financial Metrics                    Company Research
        Ratios                               Annual Reports
        Growth                               Investor Presentations
        Valuation                            Concall Transcripts
        Quality                              NSE/BSE Filings
        Sector Metrics                       Company Website
                |                            Industry Data
                |                            News
                +-----------------+-----------------+
                                  |
                           DATA NORMALIZATION
                                  |
                         COMPANY KNOWLEDGE STORE
                                  |
                    +-------------+-------------+
                    |                           |
              DETERMINISTIC                 AI ANALYSIS
                ENGINE                         |
                    |                    EmbeddingGemma
                    |                           |
                    |                         Llama
                    |                           |
                    +-------------+-------------+
                                  |
                          ANALYSIS JSON
                                  |
                    +-------------+-------------+
                    |                           |
              WEB APPLICATION               PDF ENGINE
                    |                           |
              Interactive Report        HTML + CSS + SVG
                                              |
                                           Chromium
                                              |
                                             PDF
````

---

# 2. Core Design Principle

## Separate DATA from ANALYSIS from PRESENTATION

Never allow the PDF renderer to directly fetch financial data.

Never allow the LLM to calculate fundamental ratios when deterministic calculations are possible.

Never allow the LLM to invent a source.

The architecture should be:

```text
RAW DATA
   ↓
NORMALIZED DATA
   ↓
CALCULATED METRICS
   ↓
RESEARCH EVIDENCE
   ↓
AI INTERPRETATION
   ↓
ANALYSIS JSON
   ↓
WEB UI / PDF
```

This ensures that the same underlying analysis can power:

* Screener
* Company dashboard
* PDF report
* Stock comparison
* AI Q&A
* Alerts
* Historical tracking

---

# 3. Data Architecture

Create a normalized company entity.

```json
{
  "company_id": "JYOTHYLAB",
  "name": "Jyothy Labs Limited",
  "exchange": "NSE",
  "symbol": "JYOTHYLAB",
  "isin": "...",
  "sector": "FMCG",
  "industry": "Home Care"
}
```

---

# 4. Market Data

Store:

* Current price
* Previous close
* Market capitalization
* Enterprise value
* 52-week high
* 52-week low
* 1D return
* 1W return
* 1M return
* 3M return
* 6M return
* 1Y return
* 3Y CAGR
* 5Y CAGR
* 10Y CAGR
* Volume
* Average volume
* Beta
* Dividend yield

Historical prices:

```text
date
open
high
low
close
adjusted_close
volume
```

The chart engine should be able to generate:

```text
price_1m
price_3m
price_6m
price_1y
price_3y
price_5y
price_10y
```

---

# 5. Financial Data

Store at least 10 years where available.

## P&L

```text
Revenue
Other Income
EBITDA
EBIT
PBT
PAT
EPS
```

## Balance Sheet

```text
Equity
Reserves
Total Assets
Cash
Investments
Net Debt
Borrowings
Receivables
Inventory
Payables
Working Capital
```

## Cash Flow

```text
CFO
CFI
CFF
Capex
FCF
```

---

# 6. Calculated Fundamental Metrics

All calculations should happen using deterministic code.

## Growth

```text
Revenue Growth
EBITDA Growth
EBIT Growth
PAT Growth
EPS Growth
CFO Growth
FCF Growth
```

## CAGR

```text
3Y Revenue CAGR
5Y Revenue CAGR
10Y Revenue CAGR

3Y PAT CAGR
5Y PAT CAGR
10Y PAT CAGR
```

## Margins

```text
Gross Margin
EBITDA Margin
EBIT Margin
PAT Margin
CFO Margin
FCF Margin
```

## Returns

```text
ROE
ROCE
ROIC
ROA
```

## Balance Sheet

```text
Debt / Equity
Net Debt / EBITDA
Current Ratio
Interest Coverage
CFO / Debt
```

## Cash Quality

```text
CFO / PAT
FCF / PAT
FCF Conversion
```

## Working Capital

```text
DSO
DIO
DPO
Cash Conversion Cycle
```

---

# 7. Valuation Engine

Calculate:

```text
P/E
Forward P/E
PEG
EV / EBITDA
EV / EBIT
P/B
P/S
Dividend Yield
FCF Yield
EV / FCF
```

Historical valuation:

```text
5Y P/E range
5Y EV/EBITDA range
Current percentile
Historical median
Historical minimum
Historical maximum
```

Example:

```json
{
  "metric": "PE",
  "current": 25.8,
  "historical_median": 31.2,
  "percentile": 38,
  "interpretation": "Below historical median"
}
```

---

# 8. Company Business Intelligence

The company should have a structured business profile.

```text
Company
 |
 +-- Business Segments
 |
 +-- Brands
 |
 +-- Products
 |
 +-- Geography
 |
 +-- Customers
 |
 +-- Distribution
 |
 +-- Manufacturing
 |
 +-- Market Share
 |
 +-- Competitors
```

---

# 9. Brand Intelligence

Brand information should be a first-class data object.

```json
{
  "brand": "Ujala",
  "company": "Jyothy Labs",
  "category": "Fabric Care",
  "ownership": "Owned",
  "market_share": 84,
  "market_share_unit": "%",
  "revenue": null,
  "growth": null,
  "competitors": [
    "..."
  ],
  "source": "..."
}
```

For every brand, capture where possible:

* Brand name
* Category
* Sub-category
* Ownership
* Licensed / owned
* License expiry
* Market share
* Revenue
* Revenue growth
* Volume growth
* Pricing growth
* Geographic presence
* Distribution
* Competitors
* Brand strength
* Management commentary
* Risks

---

# 10. Brand Portfolio Visualization

The PDF should support a visual brand map.

Example:

```text
                    COMPANY

       +-------------+-------------+
       |             |             |
   FABRIC CARE   DISHWASHING   INSECTICIDES
       |             |             |
     UJALA          EXO           MAXO
     HENKO          PRIL*         
       |             |
    Category       Category
     Share          Share
```

Where possible, display:

```text
Brand
Category
Market Share
Revenue Contribution
Growth
Ownership
```

---

# 11. Segment Intelligence

Each segment should contain:

```json
{
  "segment": "Fabric Care",
  "revenue": 1346,
  "revenue_unit": "INR crore",
  "revenue_growth": 8.1,
  "volume_growth": 9.5,
  "profit": null,
  "profit_growth": null,
  "margin": null,
  "brands": [
    "Ujala",
    "Henko"
  ]
}
```

Calculate:

```text
Segment Revenue
Segment Revenue Growth
Segment Contribution %
Segment Profit
Segment Margin
Segment Growth
```

---

# 12. Segment Charts

Generate:

### Revenue Mix

Pie / stacked bar chart.

### Segment Revenue Trend

5Y / 10Y where available.

### Segment Growth

Bar chart.

### Segment Profitability

Bar / line chart.

---

# 13. Competitor Engine

Competitors should not simply be manually typed.

Create a company-category relationship.

```text
Company A
 |
 +-- Category 1
 |      |
 |      +-- Competitor B
 |      +-- Competitor C
 |
 +-- Category 2
        |
        +-- Competitor D
```

Store:

```text
Competitor
Symbol
Category
Market Cap
Revenue
Revenue Growth
EBITDA Margin
ROCE
ROE
P/E
EV/EBITDA
1Y Return
5Y CAGR
```

---

# 14. Competitor Report

Generate:

## Market Cap Comparison

## Revenue Growth Comparison

## EBITDA Margin Comparison

## ROCE Comparison

## P/E Comparison

## 1-Year Stock Performance

## 5-Year Stock Performance

---

# 15. Rebased Price Performance

Normalize all competitors to 100 at the beginning of the period.

```text
Starting value = 100
```

Example:

```text
Company A → 122
Company B → 96
Company C → 141
Company D → 83
```

This allows direct comparison independent of absolute stock price.

---

# 16. Research Source Architecture

Every important factual statement should have a source.

Source hierarchy:

## Tier 1 — Primary

```text
NSE
BSE
Company Investor Relations
Annual Reports
Financial Results
Investor Presentations
Concall Transcripts
Corporate Announcements
Regulatory Filings
```

## Tier 2 — High-quality secondary

```text
Reuters
Business Standard
Economic Times
Mint
Moneycontrol
Bloomberg
Financial research reports
```

## Tier 3 — Context / Industry

```text
Finshots
TradingView
Screener
Industry reports
PR Newswire
Other credible publications
```

Priority:

```text
Primary > Secondary > Context
```

---

# 17. Source Registry

Create a source registry.

```json
{
  "source_id": "SRC_001",
  "title": "FY26 Annual Report",
  "publisher": "Company",
  "source_type": "annual_report",
  "tier": 1,
  "date": "2026-05-20",
  "url": "...",
  "retrieved_at": "...",
  "document_id": "..."
}
```

---

# 18. Evidence Objects

Every important extracted claim should have an evidence object.

```json
{
  "claim": "Fabric Care revenue grew 8.1% in FY26",
  "value": 8.1,
  "unit": "%",
  "period": "FY26",
  "source_id": "SRC_001",
  "source_type": "investor_presentation",
  "confidence": "high",
  "evidence_text": "...",
  "page": 42
}
```

This makes the system auditable.

---

# 19. Concall Intelligence Engine

Concall transcripts should be treated differently from ordinary documents.

Pipeline:

```text
Concall PDF
    ↓
Text extraction
    ↓
Chunking
    ↓
EmbeddingGemma
    ↓
Vector database
    ↓
Semantic retrieval
    ↓
Llama
    ↓
Structured management intelligence
```

---

# 20. Concall Topics

Extract:

```text
Demand
Volume
Pricing
Revenue
Margins
Costs
Raw Materials
Capacity
Capex
Utilization
New Products
Market Share
Distribution
Competition
Geography
Hiring
Technology
M&A
Guidance
Risks
```

---

# 21. Management Guidance Extraction

For every concall, identify explicit guidance.

Example:

```json
{
  "quarter": "Q1 FY27",
  "topic": "Revenue Growth",
  "guidance": "Double digit growth",
  "direction": "positive",
  "confidence": "high",
  "source": "Q1 FY27 Concall"
}
```

Do not confuse:

```text
Management expectation
Analyst expectation
Historical performance
LLM inference
```

These must remain separate.

---

# 22. Guidance Tracking

Create a historical guidance table.

```text
Q1 FY26
   ↓
Q2 FY26
   ↓
Q3 FY26
   ↓
Q4 FY26
   ↓
Q1 FY27
```

For every guidance item:

```text
Original Guidance
Actual Result
Variance
Management Explanation
Status
```

Status:

```text
Delivered
Partially Delivered
Missed
Withdrawn
Still Pending
```

---

# 23. Guidance Quality Score

Calculate a deterministic management guidance score.

Example:

```text
Guidance Accuracy
Guidance Consistency
Conservatism
Frequency of Misses
Frequency of Upgrades
Frequency of Downgrades
```

Do not allow Llama to directly assign the score.

LLM can explain the evidence.

---

# 24. Management Tone Analysis

Llama can classify management commentary as:

```text
Positive
Neutral
Negative
Mixed
```

Across:

```text
Demand
Margins
Pricing
Volume
Capex
Guidance
Competition
Working Capital
Industry
```

Output:

```text
Demand        ↑ Positive
Margins       ↓ Negative
Volumes       ↑ Positive
Pricing       → Neutral
Capex         ↑ Positive
Guidance      → Stable
```

This should be evidence-backed.

---

# 25. Concall Change Detection

Compare latest concall with previous calls.

Detect:

```text
New positive commentary
New negative commentary
Guidance change
Tone change
New risk
Removed risk
New growth driver
Delayed project
Changed capex
Changed margin expectation
```

Example:

```text
Previous Quarter:
"Margins expected to remain stable"

Latest Quarter:
"Margins likely to remain under pressure"

CHANGE:
Negative
```

---

# 26. AI Research Architecture

Use different models for different jobs.

## EmbeddingGemma

Use for:

* Semantic retrieval
* Concall search
* Annual report retrieval
* Finding similar commentary
* Historical guidance retrieval
* Evidence retrieval

## Llama

Use for:

* Summarization
* Classification
* Management commentary interpretation
* Risk extraction
* Growth driver extraction
* Moat analysis
* Q&A generation
* Narrative generation

Do NOT use Llama for:

* Revenue calculation
* CAGR
* ROCE
* P/E
* Market cap
* Price return
* Financial ratios

These must be deterministic.

---

# 27. Fundamental Analysis Engine

Generate structured conclusions.

```text
Business Quality
Growth Quality
Profitability
Capital Efficiency
Balance Sheet
Cash Flow Quality
Management Quality
Competitive Position
Valuation
Risk
```

Each conclusion must contain:

```json
{
  "score": 8.2,
  "reason": "...",
  "evidence": [],
  "confidence": "high"
}
```

---

# 28. Explainable Scoring

Never create:

```text
Fundamental Score = 8.3
```

without explanation.

Instead:

```text
Fundamental Score = 8.3 / 10

Business Quality      8.7
Growth                7.8
Profitability         8.9
Balance Sheet         9.2
Cash Flow             8.5
Management            7.6
Valuation             6.2
Risk                  7.0
```

Every score should have underlying measurable factors.

---

# 29. Report Structure

The premium PDF should follow this structure.

---

# PAGE 1 — COMPANY SNAPSHOT

Header:

```text
[Brand Logo]

COMPANY NAME
Fundamental Analysis

As of [Date]
```

Metric cards:

```text
Price
Market Cap
P/E
52W Range
```

Then:

## Investment Snapshot

Short company description.

Then:

## 1-Year Price Chart

Display:

* 1Y price
* 52W high
* 52W low
* 1Y return

---

# PAGE 2 — BUSINESS & BRANDS

## Business Overview

2–4 paragraph concise description.

## Brand Portfolio

Visual brand cards.

For each major brand:

```text
Brand
Category
Market Share
Ownership
Growth
```

## Revenue Snapshot

```text
FY26 Revenue
Revenue Growth
EBITDA
EBITDA Margin
PAT
PAT Growth
```

---

# PAGE 3 — FINANCIAL PERFORMANCE

## Revenue

10Y revenue chart.

## EBITDA

10Y EBITDA chart.

## PAT

10Y PAT chart.

## EPS

10Y EPS chart.

---

# PAGE 4 — PROFITABILITY & CASH FLOW

Metrics:

```text
ROE
ROCE
ROIC
EBITDA Margin
PAT Margin
CFO/PAT
FCF
FCF Conversion
```

Charts:

```text
ROCE trend
ROE trend
EBITDA Margin trend
FCF trend
```

---

# PAGE 5 — SEGMENTS

## Segment Revenue

Chart.

## Segment Growth

Chart.

## Segment Profitability

Chart.

## Segment Commentary

For every segment:

```text
Revenue
Growth
Margin
Key Brands
Management Commentary
Risks
```

---

# PAGE 6 — COMPETITIVE LANDSCAPE

## Competitor Table

```text
Company
Market Cap
Revenue Growth
EBITDA Margin
ROCE
P/E
1Y Return
```

## Market Cap Comparison

Bar chart.

## P/E Comparison

Bar chart.

---

# PAGE 7 — STOCK PERFORMANCE

## 1-Year Rebased Performance

Company + competitors.

Starting value:

```text
₹100
```

## 5-Year Performance

Where data is available.

## Relative Performance

Explain:

```text
Company underperformed peers by X%
```

---

# PAGE 8 — MANAGEMENT & CONCALL INTELLIGENCE

## Latest Concall

```text
Demand       Positive
Volumes      Positive
Pricing      Neutral
Margins      Negative
Capex        Positive
Guidance     Stable
```

## Management Guidance

Table:

```text
Topic
Previous Guidance
Latest Guidance
Actual
Status
```

## What Changed?

Explain changes from previous quarter.

---

# PAGE 9 — MOAT & GROWTH DRIVERS

## Business Moat

Evidence-backed bullets.

Possible factors:

```text
Brand strength
Market share
Distribution
Cost advantage
Network effect
Switching costs
Intellectual property
Scale
Customer relationships
```

## Growth Drivers

Rank:

```text
High impact
Medium impact
Low impact
```

Each driver should contain:

```text
Driver
Evidence
Expected impact
Time horizon
Risk
```

---

# PAGE 10 — RISKS

## Key Risks

Rank by:

```text
Probability
Impact
Time Horizon
```

Example:

```text
Risk                     Probability    Impact
Margin pressure          High           High
Competition              Medium         High
Raw material inflation   Medium         Medium
Regulatory               Low            High
```

Each risk must have supporting evidence.

---

# PAGE 11 — KEY QUESTIONS

Generate questions that matter to the investment thesis.

Examples:

```text
Can the company replace lost revenue?
Can margins recover?
Is market share improving?
Is growth volume-led or price-led?
Is the moat strengthening?
Is management delivering its guidance?
Is valuation justified?
```

For every question:

```text
Question
Evidence For
Evidence Against
Current Answer
What To Monitor
Next Trigger
```

---

# PAGE 12 — VALUATION

## Current Valuation

```text
P/E
EV/EBITDA
P/B
FCF Yield
Dividend Yield
```

## Historical Valuation

5Y P/E chart.

## Peer Valuation

Comparison.

## Valuation Conclusion

```text
Cheap
Reasonable
Expensive
```

The conclusion must be based on deterministic valuation metrics.

---

# PAGE 13 — INVESTMENT DASHBOARD

Example:

```text
BUSINESS QUALITY       8.4 / 10
GROWTH                 7.6 / 10
PROFITABILITY          8.8 / 10
BALANCE SHEET          9.1 / 10
CASH FLOW              8.2 / 10
MANAGEMENT             7.5 / 10
COMPETITIVE POSITION   8.1 / 10
VALUATION              6.2 / 10
RISK                   6.8 / 10

--------------------------------

FUNDAMENTAL SCORE      7.9 / 10
```

Then:

## Bull Case

## Base Case

## Bear Case

---

# PAGE 14 — SOURCES & EVIDENCE

Do not merely provide a list of websites.

Create a source ledger.

```text
Source
Type
Date
Used For
Reliability
```

Example:

```text
FY26 Annual Report
Primary
May 2026
Financials
High

Q1 FY27 Concall
Primary
Aug 2026
Management Guidance
High

Industry Report
Secondary
Aug 2026
Market Share
Medium
```

---

# 30. PDF Design System

The report should have a consistent visual identity.

## Colors

Use a restrained palette:

```text
Primary: Dark Navy
Background: Off White
Accent: Gold / Brand Accent
Text: Dark Grey
Secondary Text: Muted Grey
Positive: Green
Negative: Red
Neutral: Grey
```

Do not use excessive colors.

---

# 31. Typography

Use:

## Heading Font

Elegant serif font.

## Body Font

Modern sans-serif.

Recommended approach:

```text
Headings:
Cormorant Garamond / Source Serif / similar

Body:
Inter / IBM Plex Sans / similar
```

Use a consistent hierarchy:

```text
H1
H2
H3
Body
Caption
Source
```

---

# 32. Header

Every page should contain:

```text
[Application Brand]

Company Name — Fundamental Analysis
Date
```

Example:

```text
Fundamental Research
Jyothy Labs Limited — Fundamental Analysis
14 Sep 2026
```

---

# 33. Footer

Every page:

```text
Fundamental Research | Company Name

Educational / Research Use
Page X
```

Include appropriate disclaimer.

---

# 34. Metric Cards

Use compact cards.

```text
+----------------+
| Market Cap     |
|                |
| ₹7,344 Cr      |
+----------------+
```

Metric card properties:

```text
Label
Value
Unit
Period
YoY Change
Source
```

---

# 35. Chart Engine

Charts should be generated independently from the PDF layout.

Chart types:

```text
Line
Bar
Stacked Bar
Pie
Area
Rebased Line
```

Required charts:

```text
Price 1Y
Price 5Y
Revenue 10Y
EBITDA 10Y
PAT 10Y
EPS 10Y
ROCE
ROE
Margins
FCF
Segment Revenue
Revenue Mix
Competitor Market Cap
Competitor P/E
Competitor Growth
Competitor Returns
Historical P/E
```

---

# 36. Chart Requirements

Charts should:

* Use vector SVG where possible
* Have clean axes
* Avoid unnecessary gridlines
* Use consistent typography
* Have clear units
* Include period
* Include source
* Never distort scale
* Never hide meaningful data
* Never use misleading axes

Example:

```text
Price performance
1 Sep 2025 → 14 Sep 2026

Source: NSE
```

---

# 37. PDF Rendering Architecture

Do not build the premium PDF entirely using low-level PDF drawing.

Recommended:

```text
Analysis JSON
     ↓
Jinja2
     ↓
HTML
     ↓
CSS
     ↓
SVG Charts
     ↓
Playwright / Chromium
     ↓
PDF
```

Benefits:

* Better typography
* Better spacing
* Better tables
* Better page breaks
* SVG support
* Responsive layouts
* Easy design changes
* Reusable components

---

# 38. Component-Based PDF Templates

Create reusable components.

```text
/components

metric-card.html
section-header.html
company-header.html
brand-card.html
segment-card.html
competitor-table.html
source-badge.html
risk-card.html
guidance-table.html
chart.html
footer.html
disclaimer.html
```

---

# 39. Report Template

```text
/templates

report.html

/sections

snapshot.html
business.html
brands.html
financials.html
segments.html
competitors.html
performance.html
concall.html
moat.html
risks.html
questions.html
valuation.html
dashboard.html
sources.html
```

---

# 40. Analysis JSON

The entire report should ultimately be represented as one structured object.

```json
{
  "company": {},
  "snapshot": {},
  "financials": {},
  "ratios": {},
  "valuation": {},
  "brands": [],
  "segments": [],
  "competitors": [],
  "market_performance": {},
  "management": {},
  "guidance": [],
  "concall_analysis": {},
  "moat": [],
  "growth_drivers": [],
  "risks": [],
  "key_questions": [],
  "investment_dashboard": {},
  "charts": [],
  "sources": []
}
```

The same JSON should power:

```text
Web Dashboard
PDF
AI Chat
Screening
Comparison
Alerts
```

---

# 41. Source Traceability

Every important number and qualitative claim should support:

```text
source_id
source_type
source_date
page / section
confidence
```

Example:

```json
{
  "claim": "EBITDA margin declined to 15.3%",
  "value": 15.3,
  "period": "FY26",
  "source_id": "FY26_AR",
  "page": 112,
  "confidence": "high"
}
```

---

# 42. Confidence System

Every extracted research item should have:

```text
High
Medium
Low
```

High confidence:

```text
Company filing
Annual report
Official presentation
Official concall
NSE/BSE
```

Medium:

```text
Reliable financial publication
Industry research
Credible third-party report
```

Low:

```text
Unverified web claim
Secondary aggregation
Weak source
```

Low-confidence information should never silently become a hard fact.

---

# 43. Conflict Resolution

When two sources disagree:

```text
Primary source wins.
```

Example:

```text
Source A:
Revenue ₹2,944 Cr

Source B:
Revenue ₹2,950 Cr

Company filing:
₹2,944 Cr

Final:
₹2,944 Cr

Source:
Company filing
```

Store the conflict rather than silently deleting it.

---

# 44. Data Freshness

Every data point should contain:

```text
as_of
reported_on
retrieved_at
period
```

Example:

```json
{
  "value": 199.36,
  "as_of": "2026-09-14",
  "retrieved_at": "2026-09-14T19:30:00",
  "period": "LIVE"
}
```

---

# 45. Report Versioning

Every generated report should contain:

```text
Report Date
Data Cutoff
Model Version
Analysis Version
Data Version
```

Example:

```text
Report:
14 Sep 2026

Financial Data:
FY26

Latest Results:
Q1 FY27

Market Data:
14 Sep 2026

Analysis Engine:
v1.4
```

---

# 46. Incremental Research

Do not regenerate everything from scratch every time.

Store:

```text
Company Research State
```

When a new result/concall arrives:

```text
Previous State
      ↓
New Filing
      ↓
Difference Detection
      ↓
Update Relevant Sections
      ↓
New Analysis JSON
      ↓
New Report
```

---

# 47. Research Change Log

Every company should have:

```text
What changed since last report?
```

Example:

```text
+ Revenue growth improved
+ Insecticide margins improved
- EBITDA margin declined
- New competitive pressure
- Management reduced guidance
```

This should be shown prominently.

---

# 48. Screener Integration

The premium report should be accessible directly from the screener.

Example:

```text
Search:
Jyothy Labs

[Fundamental Score 7.9]

Revenue CAGR      11.4%
ROCE              21.3%
Debt/Equity        0.08
FCF Yield          3.4%
P/E               25.8x

[Open Research Report]
```

---

# 49. Screening → Research Workflow

User workflow:

```text
Run Screener
    ↓
Find Candidate
    ↓
Open Company
    ↓
View Fundamental Dashboard
    ↓
Open Deep Research
    ↓
Read Concall Intelligence
    ↓
Read Risks
    ↓
Read Valuation
    ↓
Generate PDF
```

---

# 50. Future AI Query Layer

Once the research database is mature, users should be able to ask:

```text
Why did this stock fall?

What changed in the latest concall?

Is management becoming more optimistic?

Which segments are driving growth?

Is revenue growth volume-led?

Is the stock expensive relative to its own history?

What are the biggest risks?

Which competitors are gaining market share?

Has management delivered its previous guidance?

What changed compared with the previous quarter?
```

The answer should always be based on retrieved evidence.

---

# 51. Important Guardrails

The AI must NEVER:

* Invent revenue
* Invent market share
* Invent management guidance
* Invent a source
* Treat estimates as reported facts
* Mix standalone and consolidated financials
* Mix quarterly and annual figures
* Mix reported and adjusted numbers
* Calculate ratios using inconsistent periods
* Treat analyst estimates as company guidance
* Treat an article's opinion as company commentary

---

# 52. Fact Types

Every piece of information should be classified.

```text
REPORTED_FACT
CALCULATED_METRIC
MANAGEMENT_GUIDANCE
ANALYST_ESTIMATE
INDUSTRY_ESTIMATE
AI_INFERENCE
AI_OPINION
```

Example:

```text
Revenue = ₹2,944 Cr
Type = REPORTED_FACT

Revenue Growth = 3.5%
Type = CALCULATED_METRIC

"Revenue growth expected to accelerate"
Type = MANAGEMENT_GUIDANCE

"FY27 revenue may decline 6–8%"
Type = ANALYST_ESTIMATE
```

---

# 53. Report Language Rules

The report should clearly distinguish:

### Fact

"Revenue increased 3.5% YoY."

### Management commentary

"Management expects..."

### Analyst estimate

"Equirus estimates..."

### AI interpretation

"This suggests..."

Never present these as equivalent.

---

# 54. Premium Report Goal

The final report should feel like:

```text
Equity Research Report
        +
Company Intelligence Database
        +
Concall Tracker
        +
Fundamental Screener
```

rather than a generic AI-generated PDF.

---

# 55. Recommended Technology Stack

## Backend

```text
Python
FastAPI
PostgreSQL
Redis
```

## Data

```text
NSE/BSE
Financial APIs / structured sources
Company filings
Market data
```

## AI

```text
EmbeddingGemma
Llama
Vector Database
```

Possible vector databases:

```text
Qdrant
pgvector
Milvus
```

For your application, PostgreSQL + pgvector is a strong starting point if you want to keep infrastructure simple.

## Research

```text
PDF parser
Document chunker
Embedding pipeline
Retrieval pipeline
LLM extraction pipeline
```

## PDF

```text
Jinja2
HTML
CSS
SVG
Playwright / Chromium
```

## Charts

```text
Plotly
Matplotlib
SVG-based chart renderer
```

---

# 56. Suggested Agent Architecture

```text
                    ORCHESTRATOR
                         |
       +-----------------+-----------------+
       |                 |                 |
 Financial Agent    Market Agent      Research Agent
       |                 |                 |
       |                 |                 |
    P&L/BS/CF          Price          Web / Filings
       |                 |                 |
       +-----------------+-----------------+
                         |
                  Segment Agent
                         |
                   Brand Agent
                         |
                  Competitor Agent
                         |
                   Concall Agent
                         |
                  Guidance Agent
                         |
                    Risk Agent
                         |
                  Valuation Agent
                         |
                  Synthesis Agent
                         |
                    Report JSON
```

---

# 57. Most Important Principle for Agents

Agents should NOT independently write the final report.

Instead:

```text
Agents → Structured Evidence

Synthesis Engine → Structured Analysis

Report Engine → Presentation
```

This prevents inconsistent narratives.

---

# 58. Final Report Generation

```text
User clicks:

GENERATE RESEARCH REPORT
        ↓
Check data freshness
        ↓
Fetch missing data
        ↓
Run calculations
        ↓
Retrieve research evidence
        ↓
Run AI analysis
        ↓
Validate claims
        ↓
Create Analysis JSON
        ↓
Generate charts
        ↓
Render HTML
        ↓
Chromium PDF
        ↓
Validate PDF
        ↓
Publish report
```

---

# 59. Automated Validation Before PDF

Before publishing:

## Financial Validation

```text
Revenue values consistent?
Standalone/consolidated correct?
Periods correct?
Ratios correct?
```

## Source Validation

```text
Every major claim has source?
Source exists?
Source date correct?
```

## Chart Validation

```text
No missing points?
Correct units?
Correct period?
Correct company?
```

## Layout Validation

```text
No orphan headings
No clipped tables
No chart overflow
No blank pages
No broken fonts
No source cutoff
```

---

# 60. PDF Quality Target

The final PDF should satisfy:

```text
Professional
Readable
Source-traceable
Data-rich
Visually attractive
Consistent
Auditable
Repeatable
```

The report should look like a premium financial research publication rather than an automatically generated document.

---

# 61. MVP Implementation Order

Do NOT build everything at once.

## Phase 1

Build:

```text
Company Snapshot
Financials
Ratios
1Y Price Chart
5Y Price Chart
Competitor Table
Basic PDF
```

## Phase 2

Add:

```text
Segments
Brands
Revenue Mix
Competitor Charts
Valuation History
```

## Phase 3

Add:

```text
Concall ingestion
EmbeddingGemma
Llama
Management guidance
Guidance tracking
```

## Phase 4

Add:

```text
Moat
Growth Drivers
Risks
Key Questions
AI-generated narrative
```

## Phase 5

Add:

```text
Evidence graph
Claim validation
Historical research state
Change detection
Automated report updates
```

---

# 62. End State

The final Fundamental Screener should work like this:

```text
                    STOCK
                      |
          +-----------+-----------+
          |                       |
      SCREENING                RESEARCH
          |                       |
      Financials             Annual Reports
      Ratios                 Investor PPT
      Valuation              Concall
      Quality                NSE/BSE
          |                  Web Research
          |                       |
          +-----------+-----------+
                      |
                 AI + EVIDENCE
                      |
              COMPANY KNOWLEDGE
                      |
              FUNDAMENTAL ANALYSIS
                      |
              +-------+-------+
              |               |
           DASHBOARD         PDF
                              |
                    Premium Research Report
```

The key idea is:

> **One structured research engine → multiple presentation formats.**

The PDF is only one output of the Fundamental Screener.

---

# 63. Example Final Company Report

```text
JYOTHY LABS LIMITED
Fundamental Analysis
14 September 2026

────────────────────────────────────

PRICE                 ₹XXX
MARKET CAP            ₹X,XXX Cr
P/E                   XX.Xx
52W RANGE             ₹XXX – ₹XXX

[ 1 YEAR PRICE CHART ]

────────────────────────────────────

BUSINESS QUALITY                 8.4
GROWTH                           7.6
PROFITABILITY                    8.8
BALANCE SHEET                    9.1
CASH FLOW                        8.2
MANAGEMENT                       7.5
COMPETITIVE POSITION             8.1
VALUATION                        6.2

FUNDAMENTAL SCORE                7.9

────────────────────────────────────

BUSINESS

Company overview...

BRAND PORTFOLIO

Ujala | Henko | Exo | Maxo

SEGMENTS

Fabric Care
Dishwashing
Insecticides
Personal Care

FINANCIALS

Revenue
EBITDA
PAT
EPS
ROCE
ROE
FCF

COMPETITORS

HUL
Godrej Consumer
Dabur
...

MANAGEMENT INTELLIGENCE

Demand              ↑
Margins             ↓
Volumes             ↑
Guidance            →

KEY RISKS

1. ...
2. ...
3. ...

GROWTH DRIVERS

1. ...
2. ...
3. ...

VALUATION

Current vs historical vs peers

KEY QUESTIONS

1. ...
2. ...
3. ...

────────────────────────────────────

SOURCES & EVIDENCE

Primary sources
Secondary sources
Industry sources

────────────────────────────────────
```

---

# 64. Final Architecture Principle

The most important design decision is:

```text
             DO NOT BUILD A PDF GENERATOR.

             BUILD A RESEARCH ENGINE.

                       ↓

             RESEARCH ENGINE
                    |
              Analysis JSON
                    |
        +-----------+-----------+
        |           |           |
       PDF       Dashboard     AI Q&A
```

That architecture will allow the Fundamental Screener to eventually become a **full company intelligence platform**, where the beautiful PDF is simply one output.

```

This is the direction I'd lock in for the app. The **brand intelligence + source/evidence layer + concall/guidance engine + reusable chart engine + HTML/CSS PDF renderer** are the pieces that will differentiate it from a normal Screener clone. The reference report's brand/segment treatment, competitor analysis, 1-year rebased performance, moat/growth/risk analysis, and source list give us a very good target for the presentation layer. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}
```
