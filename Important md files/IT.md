# IT Sector Fundamental Screener Specification

**Version:** 1.0
**Sector:** Information Technology / IT Services
**Primary Market:** India
**Purpose:** Fundamental analysis and ranking of listed IT companies
**Output:** Business Quality + Growth + Operating Quality + Financial Quality + Valuation + Risk

---

## 1. OBJECTIVE

Analyse an IT company as a combination of:

1. Business quality
2. Revenue growth
3. Revenue mix
4. Client quality
5. Deal pipeline
6. Employee economics
7. Operating efficiency
8. Margin quality
9. Cash-flow quality
10. Balance-sheet strength
11. Capital efficiency
12. Competitive advantage
13. Valuation
14. Risks and red flags

The system MUST NOT evaluate an IT company using generic financial ratios alone.

IT services are primarily a:

> **People + Utilization + Pricing + Client Demand + Deal Pipeline + Delivery Model + Currency**

business.

Therefore, financial metrics MUST be combined with operational KPIs.

---

# 2. COMPANY CLASSIFICATION

First classify the company.

## 2.1 Business Model

Possible classifications:

* IT Services
* Digital Transformation
* Cloud Services
* Cybersecurity
* Data & Analytics
* AI / GenAI
* Engineering R&D / ER&D
* Product Engineering
* BPM
* Consulting
* SaaS
* Software Products
* Infrastructure Services
* Managed Services
* Hybrid

A company MAY have multiple classifications.

## 2.2 Revenue Model

Identify:

* Recurring revenue
* Project revenue
* Managed services
* Time & material
* Fixed-price projects
* Subscription
* Transaction-based
* License revenue
* Consulting revenue

Calculate where possible:

`Recurring Revenue %`

Higher recurring revenue generally improves predictability.

---

# 3. DATA PERIODS

The engine MUST maintain:

### Annual

* Current FY
* 3Y history
* 5Y history
* 10Y history

### Quarterly

* Latest quarter
* Previous quarter
* YoY quarter
* 8-quarter history
* 12-quarter history where available

### TTM

Calculate:

`TTM = latest four reported quarters`

Use TTM for current valuation and profitability where appropriate.

---

# 4. BUSINESS QUALITY

## 4.1 Business Understanding

Capture:

* Primary services
* Key verticals
* Geographic exposure
* Customer profile
* Delivery model
* Recurring vs discretionary revenue
* Product/IP contribution

Flag:

`BUSINESS_MODEL_COMPLEXITY`

---

## 4.2 Revenue Mix

Track:

### Service Mix

* Traditional IT
* Digital
* Cloud
* Data
* AI
* Cybersecurity
* Consulting
* Engineering
* BPM
* Infrastructure
* Other

Calculate:

`Higher_Value_Service_Revenue_%`

Possible proxy:

`Digital + Cloud + Data/AI + Cybersecurity + Consulting / Total Revenue`

DO NOT treat this as universally comparable across companies because company definitions differ.

---

## 4.3 Geographic Mix

Track:

* North America %
* Europe %
* India %
* APAC %
* Rest of World %

Calculate:

`Top_Geography_Revenue_%`

Flag excessive geographic concentration.

---

## 4.4 Industry Vertical Mix

Track:

* BFSI
* Healthcare
* Retail
* Manufacturing
* Communications
* Technology
* Energy
* Public Sector
* Travel
* Others

Calculate:

`Top_3_Vertical_Concentration`

High concentration = higher cyclical/concentration risk.

---

# 5. REVENUE GROWTH

## 5.1 Core Metrics

Calculate:

* Revenue CAGR 3Y
* Revenue CAGR 5Y
* Revenue CAGR 10Y
* Revenue YoY
* Revenue QoQ
* TTM Revenue Growth

Formulas:

`Revenue_CAGR_3Y = (Revenue_t / Revenue_t-3)^(1/3) - 1`

`Revenue_CAGR_5Y = (Revenue_t / Revenue_t-5)^(1/5) - 1`

---

## 5.2 Constant Currency Growth

Capture:

`CC_Revenue_Growth`

Compare:

`Reported_Revenue_Growth`

vs

`Constant_Currency_Growth`

Interpretation:

* CC growth ≈ reported growth → operational growth
* Large difference → currency impact

---

## 5.3 Organic Growth

Where acquisition information is available:

`Organic_Revenue_Growth`

Compare:

`Reported Growth vs Organic Growth`

Flag:

`ACQUISITION_DEPENDENT_GROWTH`

if reported growth materially exceeds organic growth.

---

# 6. DEAL PIPELINE

Deal wins are a leading indicator and MUST be analysed separately from reported revenue.

## 6.1 Metrics

Capture:

* TCV
* TCV YoY growth
* Large deal TCV
* Number of large deals
* Bookings
* Order intake
* Book-to-bill
* Deal pipeline
* Deal conversion where available

## 6.2 Derived Metrics

`TCV_to_Revenue = TCV / TTM Revenue`

`TCV_Growth = TCV_t / TCV_t-1 - 1`

`Book_to_Bill = New_Bookings / Revenue`

Interpretation:

* > 1: pipeline replenishment generally positive
* ≈1: broadly stable
* <1: potential future growth pressure

DO NOT use a universal threshold because contract duration and accounting recognition differ between companies.

---

# 7. EMPLOYEE ECONOMICS

Employee economics is a CORE IT-SECTOR module.

## 7.1 Headcount

Track:

* Total employees
* Employee additions
* Employee growth YoY
* Employee growth QoQ
* Freshers
* Lateral hires
* Contractors
* Offshore employees
* Onsite employees

---

## 7.2 Attrition

Track:

* Total attrition
* Voluntary attrition
* Quarterly attrition
* Annual attrition
* Attrition trend

Calculate:

`Attrition_Trend`

Interpret in conjunction with:

* Utilization
* Headcount
* Revenue growth
* Hiring
* Margin

DO NOT automatically score lower attrition as positive.

---

## 7.3 Utilization

Track:

* Overall utilization
* Utilization excluding trainees
* Billable utilization
* Onsite utilization
* Offshore utilization

Calculate:

`Utilization_Change = Current Utilization - Previous Period Utilization`

---

## 7.4 Revenue Per Employee

Calculate:

`Revenue_Per_Employee = TTM Revenue / Average Employee Count`

Also calculate:

`Revenue_Per_Billable_Employee`

where data is available.

---

## 7.5 Employee Productivity

Calculate:

`Revenue_Growth - Employee_Growth`

Interpretation:

### Positive

Revenue growth > employee growth

Potential:

* Productivity improvement
* Utilization improvement
* Pricing improvement
* Automation benefit
* Better mix

### Negative

Employee growth > revenue growth

Potential:

* Hiring ahead of demand
* Utilization pressure
* Margin pressure

Investigate before scoring.

---

# 8. PRICING POWER

Track where disclosed:

* Billing rate changes
* Pricing increases
* Realization
* Revenue per employee
* Revenue per billable employee
* Offshore mix
* Onsite mix
* Fixed-price vs T&M

Analyze:

`Revenue Growth`

against:

`Headcount Growth`

and:

`Revenue / Employee Growth`

Positive pattern:

`Revenue ↑ > Headcount ↑`

Strongest pattern:

`Revenue ↑ + Revenue/Employee ↑ + Margin ↑`

---

# 9. MARGIN ANALYSIS

## 9.1 Primary Metrics

Track:

* Gross Margin
* EBITDA Margin
* EBIT Margin
* PAT Margin

For IT services, give greatest importance to:

`EBIT Margin`

and

`EBIT Margin Trend`

---

## 9.2 Historical Margin

Calculate:

* Current EBIT Margin
* 3Y average EBIT Margin
* 5Y average EBIT Margin
* 10Y average EBIT Margin
* Best historical EBIT Margin
* Worst historical EBIT Margin
* Margin volatility

---

## 9.3 Margin Change

Calculate:

`Current EBIT Margin - 5Y Average EBIT Margin`

and:

`Current EBIT Margin - Previous Year EBIT Margin`

---

## 9.4 Margin Volatility

Calculate:

`Quarterly EBIT Margin Standard Deviation`

Lower volatility generally indicates higher earnings predictability.

---

# 10. MARGIN BRIDGE

Whenever possible, explain margin movement through:

```text
Revenue Growth
        +
Utilization
        +
Pricing
        +
Employee Cost
        +
Subcontractor Cost
        +
Onsite/Offshore Mix
        +
Currency
        +
SG&A
        =
EBIT Margin Change
```

The system MUST avoid simplistic conclusions such as:

> "Margin increased = business quality improved."

For example:

`Layoffs → Employee Cost ↓ → EBIT Margin ↑`

may improve short-term profitability while simultaneously indicating weak demand.

---

# 11. COST STRUCTURE

Track:

* Employee cost
* Employee cost / Revenue
* Subcontractor cost
* Subcontractor cost / Revenue
* SG&A / Revenue
* Other operating expenses / Revenue

Calculate:

`Employee_Cost_Ratio = Employee Cost / Revenue`

`Subcontractor_Ratio = Subcontractor Cost / Revenue`

Track 3Y/5Y trends.

---

# 12. CLIENT QUALITY

## 12.1 Customer Concentration

Track:

* Top client %
* Top 5 clients %
* Top 10 clients %

Flag:

`CUSTOMER_CONCENTRATION_RISK`

---

## 12.2 Large Client Base

Capture number of clients above disclosed thresholds:

* $1M
* $5M
* $10M
* $20M
* $50M
* $100M

Use company-specific disclosure units where applicable.

---

## 12.3 Client Growth

Track:

* New clients
* Lost clients
* Growing clients
* Declining clients
* Client additions
* Client retention

Calculate:

`Client_Base_Growth`

and:

`Large_Client_Growth`

---

# 13. CASH FLOW QUALITY

Cash flow is a HIGH-PRIORITY module.

## 13.1 Metrics

Track:

* CFO
* FCF
* CFO / PAT
* FCF / PAT
* CFO / EBITDA
* FCF / EBITDA
* FCF Margin

---

## 13.2 Cash Conversion

Calculate:

`CFO_PAT = CFO / PAT`

`FCF_PAT = FCF / PAT`

`FCF_EBITDA = FCF / EBITDA`

Calculate for:

* Current FY
* 3Y average
* 5Y average

---

## 13.3 Interpretation

Strong pattern:

`PAT ↑ + CFO ↑ + FCF ↑`

Warning:

`PAT ↑↑ + CFO stagnant/declining`

Major warning:

`PAT consistently > CFO`

Investigate:

* Receivables
* Other working capital
* Exceptional items
* Non-cash income
* Accounting adjustments

---

# 14. WORKING CAPITAL

IT companies typically have limited inventory, therefore receivables deserve significant attention.

Track:

* Debtor Days / DSO
* Trade Receivables
* Receivables / Revenue
* Other Receivables
* Payable Days
* Working Capital Days

---

## 14.1 Receivables Growth Test

Compare:

`Revenue Growth`

against:

`Receivables Growth`

Warning:

`Receivables Growth >> Revenue Growth`

Flag:

`RECEIVABLES_OUTGROWING_REVENUE`

---

## 14.2 DSO Trend

Track:

* Current DSO
* 3Y average
* 5Y average
* YoY change

Rising DSO = potential cash collection risk.

---

# 15. BALANCE SHEET

Track:

* Total Debt
* Net Debt
* Cash
* Liquid Investments
* Debt/Equity
* Net Debt/EBITDA
* Interest Coverage
* Current Ratio

---

## 15.1 Net Cash

Calculate:

`Net_Cash = Cash + Liquid Investments - Total Debt`

Calculate:

`Net_Cash / Revenue`

and:

`Net_Cash / Market Cap`

where relevant.

---

## 15.2 Goodwill

Track:

* Goodwill
* Goodwill / Total Assets
* Goodwill Growth
* Goodwill / Equity

High goodwill growth + acquisition-led growth = investigate.

---

# 16. CAPITAL EFFICIENCY

Prioritize:

1. ROIC
2. ROCE
3. ROE

Track:

* Current ROIC
* 3Y average ROIC
* 5Y average ROIC
* 10Y average ROIC
* ROIC trend

---

## 16.1 Incremental ROIC

Where sufficient data exists:

`Incremental_ROIC = Change in NOPAT / Change in Invested Capital`

Use cautiously because accounting definitions can vary.

---

# 17. CAPEX INTENSITY

Track:

* Capex
* Capex / Revenue
* Capex / EBITDA
* Capex / CFO

Calculate:

`FCF_After_Capex`

IT businesses with structurally low capital intensity generally deserve higher asset-light quality scores.

---

# 18. ACQUISITION ANALYSIS

Track:

* Acquisition spend
* Number of acquisitions
* Goodwill created
* Intangible assets
* Revenue acquired
* Organic revenue growth
* Reported revenue growth

Flag:

`ACQUISITION_DEPENDENT_GROWTH`

if acquisition contribution is material.

Also monitor:

`Goodwill Growth > Organic Growth`

as a potential investigation trigger.

---

# 19. CURRENCY ANALYSIS

Track:

* USD revenue %
* EUR revenue %
* GBP revenue %
* Other currency exposure
* Foreign currency expenses
* Forex gain/loss
* Hedging impact

Calculate:

`Foreign_Currency_Revenue / Total Revenue`

Compare:

`Constant Currency Growth`

vs

`Reported Growth`

Do not treat FX-driven growth as organic operational improvement.

---

# 20. COMPETITIVE ADVANTAGE

Create a structured qualitative score.

Potential positive indicators:

* Large enterprise client base
* High client retention
* High switching costs
* Strong domain expertise
* Proprietary IP
* Strong delivery capability
* Global delivery network
* Strong brand
* High employee productivity
* Persistent premium margins
* Persistent high ROIC
* Strong deal-win capability

Potential negative indicators:

* Commodity services
* Pricing pressure
* Low differentiation
* Customer concentration
* High employee dependency without pricing power
* Weak client retention
* Declining realization

---

# 21. FINANCIAL QUALITY SCORE

Score from 0–100.

Suggested weighting:

```text
Cash Flow Quality          25%
Capital Efficiency         25%
Balance Sheet              20%
Margin Quality              20%
Working Capital             10%
```

---

# 22. GROWTH SCORE

Score from 0–100.

Suggested weighting:

```text
Revenue CAGR                25%
Organic Growth              20%
Constant Currency Growth    15%
TCV / Deal Growth           20%
EPS / PAT Growth             20%
```

---

# 23. OPERATING QUALITY SCORE

Score from 0–100.

Suggested weighting:

```text
Utilization                 20%
Revenue / Employee          20%
Revenue vs Headcount        15%
Attrition                   10%
Margin Trend                20%
Client Quality              15%
```

---

# 24. BUSINESS QUALITY SCORE

Score from 0–100.

Suggested weighting:

```text
Business Model              15%
Revenue Diversification     15%
Client Quality              20%
Service Mix                 15%
Competitive Advantage       20%
Recurring Revenue           15%
```

---

# 25. VALUATION SCORE

Valuation MUST be evaluated independently from business quality.

Track:

* P/E
* EV/EBIT
* EV/EBITDA
* FCF Yield
* PEG
* P/B where useful

---

## 25.1 Historical Valuation

Calculate:

`Current P/E / 5Y Median P/E`

`Current P/E / 10Y Median P/E`

`Current EV/EBIT / Historical Median`

`Current FCF Yield vs Historical FCF Yield`

---

## 25.2 Peer Valuation

Compare against:

* Direct IT services peers
* Similar growth companies
* Similar margin companies
* Similar business models

DO NOT compare SaaS companies directly with traditional IT services using a simple P/E comparison.

---

# 26. VALUATION + GROWTH

Calculate:

`PEG = P/E / Expected EPS Growth`

Also evaluate:

`P/E vs EPS CAGR`

`EV/EBIT vs EBIT Growth`

Use PEG only as a supporting metric, not as the sole valuation decision.

---

# 27. RED FLAG ENGINE

The system MUST actively search for:

### Growth

* Revenue growth slowing
* Organic growth declining
* TCV declining
* Book-to-bill deteriorating

### Employee

* Attrition increasing
* Utilization declining
* Headcount growing faster than revenue
* Revenue/employee declining

### Margin

* EBIT margin compression
* Margin volatility increasing
* Margin improvement caused primarily by layoffs

### Client

* Customer concentration increasing
* Major client loss
* Large-client additions declining

### Cash Flow

* CFO/PAT declining
* FCF/PAT declining
* PAT growing while CFO declines

### Working Capital

* DSO rising
* Receivables growing faster than revenue

### Balance Sheet

* Debt increasing
* Net cash declining
* Goodwill increasing rapidly

### Acquisition

* Organic growth weak
* Reported growth acquisition-led

### Currency

* Large FX dependence
* Reported growth materially above CC growth

---

# 28. POSITIVE SIGNAL ENGINE

Flag:

### Growth

* Revenue CAGR improving
* CC growth accelerating
* TCV accelerating
* Book-to-bill >1
* Organic growth strong

### Operations

* Utilization improving
* Revenue/employee increasing
* Headcount discipline
* Attrition improving

### Margins

* EBIT margin expanding
* Margin above historical average
* Margin expansion accompanied by revenue growth

### Cash

* CFO/PAT >100% consistently
* FCF/PAT >100%
* Strong FCF margin

### Capital Efficiency

* ROIC consistently high
* ROIC improving

### Balance Sheet

* Net cash
* Low debt
* Strong interest coverage

---

# 29. CAUSAL ANALYSIS ENGINE

The system SHOULD analyse relationships rather than individual ratios.

Core IT causal chain:

```text
Client Demand
      ↓
Deal Wins / TCV
      ↓
Revenue Growth
      ↓
Utilization
      ↓
Revenue / Employee
      ↓
EBIT Margin
      ↓
EBIT
      ↓
CFO
      ↓
FCF
      ↓
ROIC
```

Example positive pattern:

```text
TCV ↑
Revenue ↑
Utilization ↑
Revenue/Employee ↑
EBIT Margin ↑
CFO ↑
FCF ↑
ROIC ↑
```

This is a high-quality growth pattern.

---

# 30. BAD GROWTH PATTERNS

## Pattern A — Cost-Cutting Growth

```text
Revenue →
Headcount ↓
Employee Cost ↓
EBIT Margin ↑
```

Flag:

`MARGIN_IMPROVEMENT_WITHOUT_DEMAND_GROWTH`

---

## Pattern B — Accounting Growth

```text
PAT ↑
CFO ↓
Receivables ↑↑
DSO ↑
```

Flag:

`EARNINGS_CASH_FLOW_DIVERGENCE`

---

## Pattern C — Acquisition Growth

```text
Reported Revenue ↑↑
Organic Revenue →
Goodwill ↑↑
```

Flag:

`ACQUISITION_DEPENDENT_GROWTH`

---

## Pattern D — Hiring Ahead of Demand

```text
Headcount ↑↑
Revenue ↑
Utilization ↓
EBIT Margin ↓
```

Flag:

`CAPACITY_UNDERUTILIZATION`

---

# 31. PEER COMPARISON

Every company MUST be compared with relevant peers.

Compare:

```text
Revenue CAGR
CC Growth
Organic Growth
EBIT Margin
Margin Trend
TCV Growth
Utilization
Attrition
Revenue/Employee
CFO/PAT
FCF/PAT
ROIC
Net Cash
P/E
EV/EBIT
FCF Yield
```

Calculate:

`Peer Percentile`

for each metric where sufficient peer data exists.

Prefer:

* Median
* Percentile
* Best-in-class
* Worst-in-class

over simple sector averages when outliers are significant.

---

# 32. SCORING MODEL

Final score:

```text
Business Quality          15%
Growth                    20%
Operating Quality         20%
Financial Quality         20%
Competitive Advantage     10%
Valuation                 15%
```

Total:

`100`

---

# 33. QUALITY CLASSIFICATION

## 85–100

`EXCEPTIONAL`

Strong business + strong financials + strong operating metrics.

## 75–84

`HIGH QUALITY`

Fundamentally strong.

## 65–74

`GOOD`

Acceptable fundamentals with some weaknesses.

## 50–64

`AVERAGE`

Mixed signals.

## 35–49

`WEAK`

Multiple fundamental concerns.

## <35

`POOR`

Significant structural concerns.

---

# 34. VALUATION CLASSIFICATION

Valuation should be independent.

Possible outputs:

```text
DEEPLY ATTRACTIVE
ATTRACTIVE
FAIR
EXPENSIVE
VERY EXPENSIVE
```

Classification MUST consider:

* Historical valuation
* Peer valuation
* Growth
* Margin quality
* ROIC
* Cash generation
* Business quality

---

# 35. FINAL OUTPUT FORMAT

The screener MUST return:

```text
Company:
Sector:
Business Model:

BUSINESS QUALITY        XX/100
GROWTH                  XX/100
OPERATING QUALITY       XX/100
FINANCIAL QUALITY       XX/100
COMPETITIVE ADVANTAGE   XX/100
VALUATION               XX/100

OVERALL SCORE           XX/100

QUALITY:
VALUATION:
CONFIDENCE:

KEY POSITIVES
1.
2.
3.
4.
5.

KEY CONCERNS
1.
2.
3.
4.
5.

RED FLAGS
1.
2.

GROWTH ENGINE
- Revenue:
- Organic Growth:
- CC Growth:
- TCV:
- Book-to-Bill:

OPERATING ENGINE
- Utilization:
- Attrition:
- Revenue/Employee:
- Employee Cost/Revenue:
- EBIT Margin:

CASH ENGINE
- CFO:
- FCF:
- CFO/PAT:
- FCF/PAT:
- DSO:

CAPITAL EFFICIENCY
- ROIC:
- ROCE:
- ROE:

BALANCE SHEET
- Debt:
- Net Cash:
- Net Debt/EBITDA:

VALUATION
- P/E:
- Historical P/E:
- EV/EBIT:
- FCF Yield:
- PEG:

PEER POSITION
- Revenue Growth Percentile:
- Margin Percentile:
- ROIC Percentile:
- Valuation Percentile:

INVESTMENT THESIS

BULL CASE

BEAR CASE

WHAT WOULD BREAK THE THESIS

METRICS TO MONITOR NEXT QUARTER
```

---

# 36. DATA QUALITY RULES

The engine MUST distinguish:

`REPORTED`

`CALCULATED`

`ESTIMATED`

`MANAGEMENT-DISCLOSED`

`THIRD-PARTY`

Never silently mix them.

Every metric should contain:

```text
metric_name
value
period
unit
source
source_date
data_type
confidence
```

Example:

```json
{
  "metric": "revenue_growth",
  "value": 12.4,
  "unit": "percent",
  "period": "FY2026",
  "source": "annual_report",
  "data_type": "calculated",
  "confidence": "high"
}
```

---

# 37. SOURCE PRIORITY

Use this hierarchy:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. Company filings
6. Exchange filings
7. Regulatory filings
8. Reliable financial databases
9. Third-party data

For critical metrics, prefer primary company disclosures.

If two sources conflict:

* Identify the discrepancy
* Prefer primary filing
* Record both values if necessary
* Do NOT silently overwrite

---

# 38. MCP DATA REQUIREMENTS

The IT analysis agent should request data from specialized tools rather than one giant data fetch.

Recommended MCP tools:

```text
financial_statements()
quarterly_results()
annual_reports()
investor_presentations()

revenue_metrics()
segment_revenue()
geographic_revenue()

headcount_metrics()
attrition_metrics()
utilization_metrics()
employee_cost_metrics()

deal_wins()
tcv_metrics()
bookings_metrics()

client_metrics()
customer_concentration()

cash_flow_metrics()
working_capital_metrics()

balance_sheet_metrics()

valuation_metrics()
historical_valuation()

peer_metrics()

management_guidance()
earnings_call_metrics()
```

---

# 39. AGENT ARCHITECTURE

Recommended flow:

```text
                    COMPANY
                       │
                       ▼
              ┌────────────────┐
              │ Company Profile │
              └───────┬────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
 Financial       Operating       Business
   Agent           Agent          Agent
       │              │              │
       └──────────────┼──────────────┘
                      ▼
              IT Analysis Agent
                      │
                      ▼
              Causal Analysis
                      │
                      ▼
              Peer Comparison
                      │
                      ▼
              Valuation Agent
                      │
                      ▼
              Risk / Red Flag Agent
                      │
                      ▼
              Final Screener
```

---

# 40. IMPORTANT IMPLEMENTATION PRINCIPLE

Do NOT build the screener as:

```text
IF ROE > X
AND PE < Y
AND Revenue Growth > Z
THEN BUY
```

Instead build:

```text
RAW DATA
   ↓
NORMALIZATION
   ↓
CALCULATED METRICS
   ↓
TREND ANALYSIS
   ↓
PEER COMPARISON
   ↓
CAUSAL ANALYSIS
   ↓
RED FLAGS
   ↓
SCORING
   ↓
INVESTMENT THESIS
```

The engine's job is not merely to identify whether a ratio is "good".

It should answer:

> **WHY did the metric change?**

> **Is the change sustainable?**

> **Is the change better or worse than peers?**

> **Does it improve or weaken future earnings power?**

> **Is the market already pricing it in?**

---

# 41. CORE INVESTMENT LOGIC

The highest-quality IT companies generally demonstrate a combination of:

```text
Strong Organic Growth
        +
Healthy TCV / Deal Pipeline
        +
High Utilization
        +
Increasing Revenue/Employee
        +
Stable/Improving EBIT Margin
        +
Strong Cash Conversion
        +
High ROIC
        +
Strong Balance Sheet
        +
Diversified Clients
        +Run this
Reasonable Valuation
```

The strongest signal is NOT any single ratio.

It is the **consistency of the entire chain**:

```text
DEMAND
  ↓
DEALS
  ↓
REVENUE
  ↓
PRODUCTIVITY
  ↓
MARGINS
  ↓
CASH
  ↓
ROIC
```

This chain should form the backbone of the IT sector screener.
