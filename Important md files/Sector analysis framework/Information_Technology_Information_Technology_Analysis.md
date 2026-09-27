# Information Technology → Information Technology — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

**Version:** 1.0  
**Primary Market:** India  
**Macro Sector:** Information Technology  
**Sector Value:** Information Technology

## Industries Covered

1. IT - Software
2. IT - Hardware
3. IT - Services

---

# 1. PURPOSE

This standalone framework is for companies classified under **Information Technology → Information Technology**.

The engine must classify the company first and then apply the relevant industry module.

IT businesses should be analysed through the complete chain:

**Demand → Bookings → Deal Wins → Backlog → Revenue → Utilization → Pricing → Margin → Cash Flow → ROIC**

The engine must distinguish sustainable growth from growth caused by acquisitions, currency, temporary demand, one-time contracts, or cost actions.

Do not judge an IT company using a single ratio such as P/E, EBITDA margin, revenue growth or employee growth.

---

# 2. BUSINESS CLASSIFICATION

Capture:

- Industry
- Sub-industry
- Business model
- Product/service categories
- End markets
- Customer geography
- Domestic/export mix
- BFSI / healthcare / retail / manufacturing / telecom / technology / other vertical exposure
- Onshore/offshore mix
- Recurring vs project revenue
- Subscription vs transaction revenue
- Managed services vs project services
- Product vs services mix
- Cloud / digital / AI / data / cybersecurity exposure where disclosed
- Customer concentration
- Geography concentration
- Employee base
- Delivery centres
- Utilization
- Competitive advantages
- Regulatory exposure
- Capital intensity
- Working-capital intensity

---

# 3. COMMON FINANCIAL ANALYSIS

## 3.1 Growth

Track:

- Revenue growth YoY
- Revenue CAGR 3Y
- Revenue CAGR 5Y
- Revenue CAGR 10Y
- Constant-currency growth where disclosed
- Reported-currency growth
- EBITDA growth
- EBIT growth
- PAT growth
- EPS CAGR
- Organic growth
- Acquisition-led growth
- Deal-win growth
- Bookings growth
- Order intake growth
- Revenue visibility / backlog where disclosed

Separate:

`Reported Growth = Organic Growth + Acquisition Impact + Currency Impact + Other Effects`

Do not treat reported growth as organic growth unless supported by data.

## 3.2 Profitability

Track:

- Gross margin where meaningful
- EBITDA margin
- EBIT margin
- PAT margin
- ROE
- ROCE
- ROIC
- Operating leverage
- Revenue/employee
- Profit/employee

## 3.3 Cash Flow

Track:

- CFO
- CFO/PAT
- CFO/EBITDA
- FCF
- FCF/PAT
- FCF margin
- Capex
- Maintenance capex
- Growth capex
- Cash conversion

For asset-light IT services, sustained cash conversion is particularly important.

## 3.4 Working Capital

Track:

- Receivable days
- Unbilled revenue
- Contract assets
- Payable days
- Contract liabilities / deferred revenue
- Cash conversion cycle where meaningful
- Working capital/revenue

Core chain:

`Revenue → Billing → Receivables/Unbilled Revenue → Collections → CFO`

## 3.5 Balance Sheet

Track:

- Gross debt
- Net debt
- Net cash
- Debt/equity
- Interest coverage
- Current ratio
- Lease liabilities
- Goodwill
- Intangible assets
- Contingent liabilities
- Capital commitments

---

# 4. IT SERVICES

IT Services includes businesses providing software development, consulting, systems integration, managed services, outsourcing, cloud services, digital transformation and related technology services.

## 4.1 Revenue Drivers

Track:

- Revenue growth
- Constant-currency growth
- Organic growth
- Client additions
- Client mining
- Large-deal wins
- Bookings
- Deal pipeline
- Backlog / executable order book where disclosed
- Renewal rate
- Cross-sell
- Upsell
- Pricing
- Volume
- Geography
- Industry vertical
- Service-line mix
- Digital/cloud/AI mix where disclosed

Break growth into:

`Volume + Pricing + Mix + Currency + Acquisitions`

## 4.2 Deal & Booking Engine

Track:

- Total bookings
- New bookings
- Large-deal TCV
- Large-deal ACV
- Book-to-bill where applicable
- Deal count
- Average deal size
- Renewal bookings
- New-client bookings
- Existing-client expansion
- Pipeline
- Deal conversion
- Cancellation / deferral where disclosed

Do not treat a large TCV announcement as equivalent to near-term revenue.

Classify deals by:

- New logo vs existing client
- Short-term vs multi-year
- Project vs managed service
- Fixed-price vs time-and-materials
- High-margin vs low-margin
- Domestic vs international
- Strategic vs tactical

## 4.3 Client Metrics

Track:

- Number of active clients
- New clients
- Client retention
- Top 1 client %
- Top 5 client %
- Top 10 client %
- Revenue from large clients
- $1M+ / $5M+ / $10M+ client counts where disclosed
- Client mining
- Revenue per client

Analyse:

`Client Additions → Revenue Diversification → Concentration Risk`

## 4.4 Geography

Track:

- North America
- Europe
- India
- Asia-Pacific
- Other geographies

Analyse:

- Geography growth
- Geography mix
- Currency exposure
- Regional demand
- Local hiring
- Onshore/offshore delivery

Do not infer geographic growth drivers without evidence.

## 4.5 Vertical Mix

Track exposure to:

- BFSI
- Healthcare
- Retail
- Manufacturing
- Telecom
- Energy
- Technology
- Public sector
- Other disclosed verticals

Analyse whether growth is:

- Broad-based
- Concentrated in one vertical
- Driven by a temporary cycle
- Supported by structural spending

## 4.6 Service-Line Mix

Track:

- Application services
- Infrastructure / managed services
- Cloud
- Data & analytics
- AI
- Cybersecurity
- Engineering services
- Consulting
- Digital services
- Other disclosed categories

Analyse:

`Service Mix → Pricing → Gross Margin → EBIT Margin`

---

# 5. IT SERVICES OPERATING METRICS

Track:

- Employee count
- Employee growth
- Attrition
- Voluntary attrition where disclosed
- Utilization
- Billable employees
- Non-billable employees
- Subcontractor ratio
- Onshore/offshore mix
- Revenue/employee
- EBIT/employee
- Hiring
- Lateral hiring
- Campus hiring
- Training

## Utilization

Analyse:

`Employees → Billable Capacity → Utilization → Revenue → Margin`

Do not assume employee growth automatically creates revenue growth.

## Attrition

Analyse:

- Overall attrition
- Voluntary attrition
- Critical-skill attrition
- Senior-level attrition where disclosed
- Replacement hiring
- Wage inflation
- Productivity impact

---

# 6. IT SERVICES PRICING & MARGIN ENGINE

Track:

- Billing rates
- Pricing changes
- Wage inflation
- Subcontractor costs
- Travel costs
- Onshore/offshore mix
- Utilization
- Employee pyramid
- Service mix
- Currency
- Other operating costs

Causal chain:

`Pricing + Utilization + Mix + Employee Cost + Subcontracting + Currency → EBIT Margin`

Separate:

**Structural margin improvement**

from:

**Temporary margin improvement**

Examples of temporary drivers may include unusually favourable currency or one-time cost actions.

---

# 7. RECURRING REVENUE & VISIBILITY

Track where disclosed:

- Recurring revenue %
- Managed services revenue
- Subscription revenue
- Annual recurring revenue
- Contracted revenue
- Backlog
- Renewal rates
- Multi-year contracts

Analyse:

`Contract Duration → Renewal → Recurring Revenue → Revenue Visibility → Cash Flow`

Recurring revenue should be evaluated for:

- Renewal risk
- Pricing
- Customer concentration
- Contract profitability
- Churn

---

# 8. IT SOFTWARE / PRODUCTS

For product-oriented software companies, track:

- ARR
- Subscription revenue
- License revenue
- Maintenance revenue
- Customer count
- Paying customers
- Net revenue retention where disclosed
- Gross retention / churn
- ARPU
- Revenue/customer
- New bookings
- Deferred revenue
- RPO where disclosed
- Implementation revenue
- Recurring vs non-recurring revenue

## Unit Economics

Track where data supports:

- CAC
- LTV
- CAC payback
- Gross margin
- Contribution margin
- Revenue/user
- Revenue/customer
- Churn
- Net retention

Do not calculate LTV or CAC from unsupported assumptions.

---

# 9. IT HARDWARE

For IT hardware businesses, track:

- Unit volumes
- ASP
- Revenue/unit
- Product mix
- Market share
- Installed base
- Replacement cycle
- Distribution
- Dealer/channel inventory
- Inventory turns
- Warranty cost
- Service revenue
- Recurring revenue
- Component costs
- Import exposure
- Export exposure
- Capacity
- Utilization

Break revenue growth into:

`Volume + Price + Mix + Currency`

Analyse:

`Component Cost → ASP/Pass-through → Gross Margin → EBITDA`

Track key input/component exposure where disclosed.

---

# 10. SOFTWARE PRODUCT LIFECYCLE

Track:

`R&D → Product Launch → Customer Acquisition → Adoption → ARR/Revenue → Retention → Expansion → Cash Flow`

Capture:

- R&D/revenue
- R&D growth
- Product releases
- Product adoption
- New customers
- Existing customer expansion
- Churn
- Pricing
- Product concentration
- Technology obsolescence
- IP/patents where relevant

Evaluate whether R&D is producing commercial outcomes rather than treating R&D spending itself as an advantage.

---

# 11. DIGITAL / CLOUD / AI EXPOSURE

Where disclosed, capture:

- Cloud revenue
- AI revenue
- AI-related bookings
- GenAI revenue
- Digital revenue
- Data/analytics revenue
- Cybersecurity revenue
- Automation revenue
- AI/cloud deal pipeline
- AI/cloud client adoption
- AI-led productivity impact

Classify claims as:

- Reported revenue
- Management-disclosed
- Bookings
- Pipeline
- Estimated

Do not convert a pipeline or management commentary into reported revenue.

---

# 12. COMPETITIVE ADVANTAGE

Evaluate evidence for:

- Brand
- Technology
- IP
- Domain expertise
- Switching costs
- Customer relationships
- Installed base
- Distribution
- Delivery capability
- Talent
- Scale
- Certifications
- Product reliability
- Ecosystem partnerships
- Recurring revenue
- Data/network effects where demonstrable

Score evidence, not reputation alone.

---

# 13. CUSTOMER CONCENTRATION

Track:

- Top 1 customer %
- Top 5 customer %
- Top 10 customer %
- Largest contract
- Largest vertical
- Largest geography
- Repeat customer %
- New customer %
- Client retention

Flag:

`Top Customer ↑ + Revenue Dependence ↑`

especially when contract renewal or pricing risk is material.

---

# 14. MANAGEMENT & GOVERNANCE

Track evidence for:

### Positive Signals

- Consistent capital allocation
- Transparent deal disclosures
- Realistic guidance
- Consistent delivery against guidance
- Sensible acquisitions
- Strong compliance
- Stable promoter ownership where relevant
- Low/no promoter pledge where relevant
- Sustainable dividend/buyback policy
- Disciplined hiring and capacity planning

### Red Flags

- Aggressive booking claims
- Repeated guidance misses
- Unexplained margin spikes
- Large related-party transactions
- Frequent acquisitions without returns
- Auditor qualifications
- Auditor changes
- Promoter pledge
- Excessive dilution
- Goodwill impairment
- Deteriorating cash conversion
- Persistent unexplained revenue divergence from cash flow

Record:

`Evidence → Date → Source → Severity → Status`

---

# 15. CAPITAL ALLOCATION

Track:

- Maintenance capex
- Growth capex
- Acquisitions
- Dividends
- Buybacks
- Debt repayment
- Equity issuance
- R&D
- Investments

Analyse:

`FCF → Reinvestment → Growth → ROIC`

For acquisitions:

`Purchase Price → Revenue Synergy → Margin → Integration → ROIC`

Do not assume acquisition synergies are realized until supported by results.

---

# 16. EARNINGS QUALITY

Check:

- PAT vs CFO
- EBITDA vs CFO
- Receivables
- Unbilled revenue
- Contract assets
- Deferred revenue / contract liabilities
- Other income
- Exceptional items
- Capitalized software/development costs
- Stock-based compensation
- Acquisition-related costs
- FX gains/losses
- Goodwill
- Impairments

Flag:

`PAT ↑ + CFO ↓`

`Revenue ↑ + Receivables/Unbilled Revenue ↑↑`

`Bookings ↑ + Revenue →`

`Revenue ↑ + ROIC ↓`

`Adjusted Profit ↑ + Cash Flow →`

The engine must clearly distinguish reported accounting metrics from management-adjusted metrics.

---

# 17. CURRENCY ANALYSIS

For export-heavy IT companies, track:

- USD exposure
- EUR exposure
- GBP exposure
- Other material currencies
- Reported growth
- Constant-currency growth
- Currency translation impact
- Hedging policy where disclosed

Causal chain:

`Currency Movement → Reported Revenue → Margin → PAT → Cash Flow`

Do not interpret currency-driven reported growth as underlying demand growth.

---

# 18. ACQUISITION ANALYSIS

Track:

- Acquisition date
- Purchase price
- Revenue acquired
- EBITDA acquired
- Geography
- Service/product capability
- Customer base
- Goodwill
- Intangible assets
- Integration cost
- Synergy guidance
- Actual synergy
- Organic growth after acquisition

Separate:

`Organic Growth`

from:

`Acquired Growth`

Analyse:

`Acquisition → Revenue → Margin → Cash Flow → ROIC`

Flag repeated acquisitions where returns are not demonstrated.

---

# 19. CYCLE & DEMAND ANALYSIS

Track:

- Global IT spending
- Enterprise technology budgets where disclosed
- Client discretionary spending
- Cost-optimization cycle
- Cloud migration cycle
- Digital transformation cycle
- AI spending
- BFSI/retail/manufacturing demand
- Interest rates
- Currency
- Recession risk indicators where relevant

Determine whether current growth is:

- Structural
- Cyclical
- Market-share driven
- Price-driven
- Currency-driven
- Acquisition-driven
- Productivity-driven
- Mix-driven

Do not extrapolate temporary demand spikes indefinitely.

---

# 20. PEER COMPARISON

Peers must have comparable business models.

For IT Services compare:

- Revenue growth
- Constant-currency growth
- Organic growth
- Deal wins/bookings
- Book-to-bill where meaningful
- Large-deal TCV/ACV
- EBIT margin
- Utilization
- Attrition
- Employee growth
- Revenue/employee
- CFO/PAT
- FCF
- ROIC
- Net cash/debt
- P/E
- EV/EBITDA

For Software compare:

- ARR growth
- Subscription growth
- Net retention
- Churn
- Gross margin
- CAC
- LTV where reliable
- FCF
- Revenue/customer
- P/S
- P/E where profitable

For Hardware compare:

- Volume growth
- Market share
- ASP
- Revenue/unit
- Gross margin
- Inventory turns
- Working capital
- ROCE
- P/E
- EV/EBITDA

---

# 21. VALUATION ENGINE

Use where appropriate:

- P/E
- EV/EBITDA
- EV/EBIT
- EV/Revenue
- P/S
- FCF yield
- PEG
- Price/Book where relevant
- ROIC

For high-growth software businesses, evaluate valuation alongside:

- ARR growth
- Revenue growth
- Gross margin
- Retention
- Cash generation
- Unit economics

For cyclical IT services, normalize earnings where necessary.

Do not value a company solely on revenue growth.

## Historical Valuation

Calculate where data permits:

- Current P/E vs 3Y median
- Current P/E vs 5Y median
- Current P/E vs 10Y median
- Current EV/EBITDA vs history
- Current EV/Revenue vs history
- Current FCF yield vs history
- Current P/S vs history
- Historical high multiple
- Historical low multiple
- Current percentile
- Relevant demand-cycle position

Historical average is context, not automatic fair value.

---

# 22. CAUSAL ANALYSIS ENGINE

The final report must explain:

**WHAT → CHANGED → WHY → IMPACT → RISK → WHAT TO MONITOR**

## IT Services Causal Chain

```text
Client Demand ↑
→ Deal Wins / Bookings ↑
→ Backlog / Revenue Visibility ↑
→ Revenue ↑
→ Utilization ↑
→ Pricing / Mix
→ EBIT Margin
→ CFO ↑
→ FCF ↑
→ ROIC ↑
```

## Software Product Causal Chain

```text
Product Investment
→ Customer Acquisition
→ Adoption
→ ARR ↑
→ Retention / Expansion
→ Revenue ↑
→ Gross Margin
→ Operating Leverage
→ FCF
→ ROIC
```

## Hardware Causal Chain

```text
Industry Demand
→ Unit Volume
→ Market Share
→ ASP / Mix
→ Revenue
→ Component Cost
→ Gross Margin
→ EBITDA
→ CFO
→ ROCE
```

---

# 23. POSITIVE SIGNAL ENGINE

Potential evidence-based signals:

- Sustained organic revenue growth
- Constant-currency growth
- Strong deal wins
- Improving bookings
- Book-to-bill > 1 sustained where meaningful
- Improving revenue visibility
- Stable/improving EBIT margin
- Improving utilization
- Strong cash conversion
- Rising recurring revenue
- Strong client retention
- Diversified customer base
- Market-share gains
- Successful product launches
- Improving ARR/NRR for software businesses
- Strong FCF
- Falling leverage
- Improving ROIC

The system must verify whether each signal is sustainable.

---

# 24. RED-FLAG ENGINE

## Demand / Revenue

- Revenue growth driven mainly by acquisitions
- Revenue growth driven mainly by currency
- Weak organic growth
- Concentrated client growth
- Repeated deal deferrals

## Bookings

- Large bookings without revenue conversion
- Pipeline presented as bookings
- TCV treated as immediate revenue
- High cancellation/deferral

## Operations

- Falling utilization
- Rising attrition
- Employee growth ahead of demand
- Margin pressure
- Excessive subcontracting
- Weak productivity

## Financial

- Revenue growth without CFO
- Rising receivables
- Rising unbilled revenue
- Persistent negative FCF
- Falling ROIC
- Rising debt
- Large goodwill/intangibles

## Governance

- Related-party concerns
- Promoter pledge where relevant
- Auditor issues
- Excessive dilution
- Repeated acquisition write-downs

---

# 25. BAD GROWTH PATTERNS

### Pattern 1

`Bookings ↑↑ → Revenue →`

Possible issue:

Weak conversion or execution.

### Pattern 2

`Revenue ↑↑ → Receivables/Unbilled Revenue ↑↑ → CFO ↓`

Possible issue:

Weak cash conversion.

### Pattern 3

`Employee Count ↑↑ → Revenue →`

Possible issue:

Underutilization or weak demand.

### Pattern 4

`Revenue ↑ → EBIT Margin ↓ → ROIC ↓`

Possible issue:

Growth is destroying incremental economics.

### Pattern 5

`Reported Growth ↑ → Constant-Currency Growth →`

Possible issue:

Currency-driven growth.

### Pattern 6

`Reported Growth ↑ → Organic Growth →`

Possible issue:

Acquisition-driven growth.

### Pattern 7

`AI/Cloud Pipeline ↑ → Reported Revenue →`

Possible issue:

Pipeline being treated as realized revenue.

---

# 26. DATA QUALITY

Every metric must contain:

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

Data types:

- REPORTED
- CALCULATED
- ESTIMATED
- MANAGEMENT_DISCLOSED
- THIRD_PARTY

If unavailable:

`NOT_AVAILABLE`

Never silently substitute another metric.

If sources conflict:

1. Identify discrepancy
2. Prefer primary filing
3. Preserve relevant alternative value
4. Record reason

Do not manufacture:

- Market share
- Pipeline conversion
- ARR
- CAC
- LTV
- Client retention
- AI revenue
- Deal value conversion
- Product adoption
- Technology advantage

unless supported by data.

---

# 27. SOURCE PRIORITY

Use:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. Company filings
6. NSE/BSE filings
7. Regulatory filings
8. Company investor-relations disclosures
9. Reliable financial databases
10. Third-party research

For major contracts/deal awards, prefer the company filing or primary counterparty disclosure.

Management commentary must remain classified as **MANAGEMENT_DISCLOSED**, not REPORTED.

---

# 28. MANAGEMENT GUIDANCE ENGINE

Extract:

- Revenue guidance
- Constant-currency guidance
- Margin guidance
- Booking guidance
- Deal-win guidance
- Utilization guidance
- Attrition guidance
- Hiring guidance
- Capex guidance
- Acquisition guidance
- AI/cloud revenue guidance
- Product/ARR guidance where applicable

Track:

`Guidance → Actual`

Classify:

- Delivered
- Missed
- Exceeded
- Revised

Do not treat management guidance as reported fact.

---

# 29. SCORING ARCHITECTURE

Base weights:

| Dimension | Weight |
|---|---:|
| Business Quality | 15% |
| Growth Quality | 20% |
| Operating Quality | 20% |
| Financial Quality | 20% |
| Competitive Advantage | 10% |
| Valuation | 15% |

Industry-specific weights may be redistributed.

### IT Services

Give meaningful weight to:

- Organic growth
- Deal/bookings quality
- Revenue visibility
- Utilization
- Pricing
- Margin sustainability
- Cash conversion
- Client concentration
- ROIC

### Software

Give meaningful weight to:

- ARR/revenue growth
- Retention
- Churn
- Product economics
- Gross margin
- Unit economics
- FCF
- Competitive advantage

### Hardware

Give meaningful weight to:

- Unit volume
- Market share
- ASP
- Product mix
- Gross margin
- Inventory
- Working capital
- ROCE

Every score must retain:

```text
score
evidence
reason
period
source
confidence
```

---

# 30. FINAL OUTPUT FORMAT

```text
Company:
Macro Sector:
Sector Value:
Industry:
Sub-Industry:
Business Model:

BUSINESS QUALITY       XX/100
GROWTH QUALITY         XX/100
OPERATING QUALITY      XX/100
FINANCIAL QUALITY      XX/100
COMPETITIVE ADVANTAGE  XX/100
VALUATION              XX/100

OVERALL SCORE          XX/100

DATA CONFIDENCE:
PRIMARY SOURCES:

BUSINESS OVERVIEW
-

GROWTH ENGINE
- Revenue CAGR:
- Latest growth:
- Organic growth:
- Constant-currency growth:
- Acquisition contribution:
- Currency contribution:
- Main growth driver:

DEAL / BOOKING ENGINE
- Bookings:
- Deal wins:
- Large-deal TCV/ACV:
- Book-to-bill:
- Pipeline:
- Backlog/revenue visibility:
- Conversion:

CLIENT METRICS
- Active clients:
- New clients:
- Client retention:
- Top customer:
- Top 5 concentration:
- Large-client count:

OPERATING KPIs
- Employees:
- Employee growth:
- Utilization:
- Attrition:
- Revenue/employee:
- Onshore/offshore:
- Subcontractor ratio:

SERVICE / PRODUCT MIX
- Service/product mix:
- Recurring revenue:
- Cloud:
- AI:
- Digital:
- Other key mix:

PROFITABILITY
- Gross margin:
- EBITDA margin:
- EBIT margin:
- ROCE:
- ROIC:

CASH FLOW
- CFO:
- CFO/PAT:
- CFO/EBITDA:
- FCF:
- FCF/PAT:

WORKING CAPITAL
- Receivable days:
- Unbilled revenue:
- Contract assets:
- Contract liabilities:
- Cash conversion cycle:

BALANCE SHEET
- Debt:
- Net debt/cash:
- Interest coverage:
- Goodwill:
- Intangibles:
- Contingent liabilities:

COMPETITIVE ADVANTAGE
-

CAPITAL ALLOCATION
-

MANAGEMENT / GOVERNANCE
-

CYCLE / DEMAND POSITION
-

VALUATION
- P/E:
- EV/EBITDA:
- EV/Revenue:
- P/S:
- FCF yield:
- Historical valuation:
- Peer valuation:

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
3.

CAUSAL ANALYSIS
WHAT CHANGED:
WHY:
IMPACT:
RISK:
WHAT TO MONITOR:

BULL CASE
-

BEAR CASE
-

WHAT WOULD BREAK THE THESIS
-

NEXT QUARTER METRICS
1.
2.
3.
4.
5.

DATA GAPS
1.
2.
3.
```

---

# 31. AGENT ARCHITECTURE

```text
Company Identification
        ↓
Information Technology Classification
        ↓
Industry Classification
        ↓
Business Model
        ↓
Financial Data
        ↓
Revenue Growth Decomposition
        ↓
Organic / Acquisition / Currency Analysis
        ↓
Bookings / Deal-Win Analysis
        ↓
Client Analysis
        ↓
Geography Analysis
        ↓
Vertical Analysis
        ↓
Service / Product Mix
        ↓
Employee / Utilization / Attrition
        ↓
Pricing / Margin Analysis
        ↓
Recurring Revenue / ARR / Backlog
        ↓
Cloud / AI / Digital Analysis
        ↓
Working Capital
        ↓
Cash Flow
        ↓
Balance Sheet
        ↓
ROIC
        ↓
Capital Allocation
        ↓
Management / Concall / Guidance
        ↓
Governance
        ↓
Peer Comparison
        ↓
Normalization
        ↓
Valuation
        ↓
Red Flags
        ↓
Causal Analysis
        ↓
Scoring
        ↓
Investment Thesis
```

---

# 32. CORE IMPLEMENTATION PRINCIPLE

The Information Technology engine should not simply ask:

`Is revenue growing?`

It should determine:

**Is underlying technology demand growing?**

→ **Are bookings and deal wins increasing?**

→ **Are those bookings converting into revenue?**

→ **Is growth organic or acquisition/currency driven?**

→ **Are clients being retained and expanded?**

→ **Is utilization healthy?**

→ **Is pricing supporting margins?**

→ **Are margins sustainable?**

→ **Is growth converting into cash?**

→ **Is incremental capital generating attractive returns?**

The core analytical pipeline is:

**RAW DATA → NORMALIZATION → INDUSTRY KPIs → GROWTH DECOMPOSITION → BOOKINGS/DEAL ANALYSIS → CLIENT/GEOGRAPHY/SERVICE MIX → OPERATING METRICS → CASH FLOW → PEER COMPARISON → VALUATION → RED FLAGS → SCORING → FINAL THESIS**

---

## Core Fundamental Question

**Does this Information Technology company have durable technology demand, strong customer economics, sustainable organic growth, high-quality bookings/revenue visibility, defensible products or services, efficient delivery economics, strong cash conversion and attractive returns on capital, while its current valuation is supported by normalized long-term earnings and cash-flow power?**
