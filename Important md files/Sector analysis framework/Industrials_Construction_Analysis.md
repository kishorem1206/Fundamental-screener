# Industrials → Construction — Fundamental Analysis Framework

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
**Macro Sector:** Industrials  
**Sector Value:** Construction

## Industry Covered

- Construction

### Construction Business Models / Segments

Classify the company into one or more of:

- EPC
- Infrastructure construction
- Roads
- Railways
- Metro
- Buildings
- Water
- Urban infrastructure
- Industrial construction
- Power construction
- Other specialized construction

---

# 1. PURPOSE

This standalone framework is for companies classified under **Industrials → Construction**.

Construction must be analysed separately from product-based Capital Goods because the economics are driven by project awards, order books, execution, billing, receivables, working capital, debt and cash conversion.

The core construction analytical chain is:

**Order Intake → Order Book → Execution → Billing → Receivables → CFO → FCF → Balance Sheet**

The engine must not judge a construction company using a single ratio such as P/E, EBITDA margin or debt/equity.

---

# 2. BUSINESS CLASSIFICATION

Capture:

- Industry
- Sub-industry
- Business model
- Project categories
- End markets
- Domestic/export mix
- Government/private exposure
- Project mix
- Recurring vs project revenue where applicable
- Order-driven model
- Customer concentration
- Geography concentration
- Execution footprint
- Equipment fleet where relevant
- Working-capital intensity
- Capital intensity
- Competitive advantages
- Regulatory exposure

The classification engine must identify the construction sub-industry before applying specialized KPIs.

---

# 3. COMMON FINANCIAL ANALYSIS

## 3.1 Growth

Track:

- Revenue growth YoY
- Revenue CAGR 3Y
- Revenue CAGR 5Y
- Revenue CAGR 10Y
- EBITDA growth
- EBIT growth
- PAT growth
- EPS CAGR
- Order intake growth
- Order-book growth
- Book-to-bill
- Execution growth

## 3.2 Profitability

Track:

- Gross margin
- EBITDA margin
- EBIT margin
- PAT margin
- Project margin
- Segment margin
- ROE
- ROCE
- ROIC
- Asset turnover
- Capital turnover

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

## 3.4 Working Capital

Track:

- Receivable days
- Inventory days
- Payable days
- Cash conversion cycle
- Contract assets
- Contract liabilities
- Unbilled revenue
- Retention money
- Advances
- Working capital/revenue

## 3.5 Balance Sheet

Track:

- Gross debt
- Net debt
- Net cash
- Debt/equity
- Interest coverage
- Current ratio
- Lease liabilities
- Bank guarantees
- Performance guarantees
- Contingent liabilities
- Capital commitments
- Debt maturity
- Interest cost
- Project advances

---

# 4. CONSTRUCTION ORDER BOOK ENGINE

Track:

- Order intake
- Order intake growth
- Order book
- Order-book growth
- Book-to-bill
- Order-book/revenue
- New orders
- Order cancellations
- L1 orders where disclosed
- Bidding pipeline
- Project awards
- Project mix

## 4.1 Core Formulas

### Order Intake Growth

`Current Period Order Intake / Previous Comparable Period - 1`

### Book-to-Bill

`Order Intake / Revenue`

### Order Book Coverage

`Closing Order Book / TTM Revenue`

### Order Execution

`Revenue from Orders / Opening Order Book`

Use only where reliable data exists.

---

# 5. ORDER BOOK QUALITY

A large order book must not automatically be treated as high-quality growth.

Track:

- Government vs private
- Fixed-price vs cost-plus
- Domestic vs export
- Short-duration vs long-duration
- Margin profile
- Working-capital profile
- Client quality
- Execution complexity
- Project type
- Customer concentration
- Order cancellation risk
- Contractual escalation clauses
- Payment terms
- Advance requirements
- Retention terms

The report must never say simply:

`Order Book is strong`

without explaining:

- Size
- Growth
- Coverage
- Quality
- Margin
- Customer
- Working-capital profile
- Execution period
- Cancellation risk

A large order book with weak cash conversion or low margins should not be treated as high-quality growth.

---

# 6. CONSTRUCTION EXECUTION ENGINE

Track:

- Revenue growth
- Execution rate
- Project completion
- Project milestones
- Cost overruns
- Project delays
- Claims
- Liquidated damages
- Escalation clauses
- Project cancellations
- Billing
- Unbilled revenue
- Contract assets

Causal chain:

`Order Intake → Order Book → Execution → Billing → Revenue`

## 6.1 Execution Quality

Compare:

`Opening Order Book → Planned Execution → Actual Execution → Closing Order Book`

Identify:

- Faster-than-expected execution
- On-schedule execution
- Delayed execution
- Repeated delays
- Order-book build-up without revenue conversion

### Key Warning Pattern

`Order Book ↑↑ → Revenue →`

Possible issue:

**Weak execution.**

---

# 7. PROJECT ECONOMICS

For major projects, where data is available, capture:

- Contract value
- Order date
- Expected completion date
- Actual completion status
- Revenue recognized
- Remaining order value
- Project margin
- Cost incurred
- Expected cost
- Cost overruns
- Billing status
- Receivables
- Contract assets
- Advances
- Retention money
- Claims
- Liquidated damages
- Escalation mechanism
- Funding/payment profile

The engine should distinguish between:

**Awarded order → Executing order → Billed revenue → Collected cash**

These are not interchangeable.

---

# 8. CONSTRUCTION WORKING CAPITAL ENGINE

Working capital is a critical part of construction analysis.

Track:

- Receivable days
- Contract assets
- Unbilled revenue
- Retention money
- Advances
- Payables
- Contract liabilities
- Inventory
- Working-capital/revenue
- CFO

Important causal chain:

`Revenue ↑ → Receivables/Contract Assets ↑ → CFO ↓`

Flag if growth consistently consumes disproportionate cash.

## 8.1 Cash Conversion

Calculate:

`CFO/PAT`

`CFO/EBITDA`

`FCF/PAT`

`Working Capital / Revenue`

Track these across multiple years rather than relying on one quarter.

---

# 9. BILLING & COLLECTION ANALYSIS

Separate:

**Accounting Revenue**

from:

**Billing**

and:

**Cash Collection**

Track:

- Revenue recognized
- Amount billed
- Unbilled revenue
- Receivables
- Contract assets
- Advances
- Retention money
- Cash collected
- Collection period

Core chain:

`Execution → Billing → Receivables → Collection → CFO`

A company can report revenue growth while simultaneously experiencing weak cash conversion.

---

# 10. CONSTRUCTION MARGIN ANALYSIS

Track:

- Gross margin
- EBITDA margin
- EBIT margin
- Project margin
- Segment margin
- Employee cost
- Material cost
- Subcontracting cost
- Finance cost

Analyse:

`Revenue Growth → Project Mix → Cost Inflation → Margin`

Look for:

- Margin expansion from better project mix
- Margin pressure from fixed-price contracts
- One-off project gains/losses
- Claims income
- Exceptional items
- Material-cost inflation
- Subcontracting-cost changes
- Finance-cost pressure

Separate sustainable operating margins from one-off gains.

---

# 11. COST STRUCTURE

Track major project costs:

- Materials
- Employee costs
- Subcontracting
- Equipment/fleet costs
- Fuel/energy
- Freight/logistics
- Finance cost
- Other project costs

Where possible, identify:

`Material Cost → Project Cost → Gross Margin`

and:

`Project Mix → Cost Structure → EBITDA Margin`

For fixed-price projects, explicitly assess the ability to pass through cost inflation.

---

# 12. CONTRACT STRUCTURE & RISK

Classify contracts by:

- Fixed-price
- Cost-plus
- EPC
- Turnkey
- Long-duration
- Short-duration
- Government
- Private
- Domestic
- Export

Track:

- Escalation clauses
- Payment milestones
- Advance payments
- Retention
- Performance guarantees
- Penalties
- Liquidated damages
- Claims provisions
- Cancellation provisions
- Dispute/arbitration exposure

Contract structure should feed directly into the margin and cash-flow analysis.

---

# 13. BALANCE SHEET ANALYSIS

Track:

- Gross debt
- Net debt
- Net working capital
- Current assets
- Current liabilities
- Bank guarantees
- Performance guarantees
- Contingent liabilities
- Debt maturity
- Interest cost
- Project advances

Important distinction:

`Accounting Profit`

vs

`Cash Available to Shareholders`

Construction analysis must connect:

`Working Capital → Debt → Interest → FCF`

Flag situations where reported growth requires increasing leverage or working-capital funding.

---

# 14. EQUIPMENT & ASSET UTILIZATION

Where applicable, track:

- Equipment fleet
- Fleet age
- Utilization
- Equipment capex
- Equipment depreciation
- Revenue/equipment
- Asset turnover
- ROCE

For asset-heavy contractors:

`Equipment Utilization → Revenue → Fixed-cost absorption → Margin`

Analyse whether equipment additions are supported by project demand.

---

# 15. CUSTOMER & PROJECT CONCENTRATION

Track:

- Top 1 customer %
- Top 5 customer %
- Government %
- Export customer %
- Repeat customer %
- New customer %
- Customer retention
- Largest project %
- Top 5 project concentration where available

Flag:

`Top Customer ↑ + Revenue Dependence ↑`

especially if contract renewal or project-award risk is material.

---

# 16. GOVERNMENT VS PRIVATE EXPOSURE

Break order book and revenue by:

- Government
- Public-sector entities
- Private sector
- Domestic
- Export

For government/project exposure, capture:

- Awarding authority
- Project type
- Contract status
- Execution schedule
- Payment profile
- Regulatory dependencies
- Cancellation/change-order risk

For government/project awards, prefer the official awarding authority or company filing as the source.

---

# 17. MANAGEMENT & GOVERNANCE

Track evidence for:

### Positive Signals

- Consistent capital allocation
- Disciplined bidding
- Transparent order disclosures
- Realistic guidance
- Stable promoter ownership
- Low/no promoter pledge
- Strong compliance
- Sensible acquisitions
- Sustainable dividend/buyback policy
- Consistent project execution
- Transparent disclosure of delays/claims

### Red Flags

- Aggressive order-book claims
- Repeated project delays
- Unexplained margin spikes
- Large related-party transactions
- Frequent acquisitions without returns
- Auditor qualifications
- Auditor changes
- Promoter pledge
- Excessive dilution
- Contingent liability expansion
- Working-capital deterioration
- Repeated cost overruns
- Weak disclosure around project claims

Record:

`Evidence → Date → Source → Severity → Status`

---

# 18. CAPITAL ALLOCATION

Track:

- Maintenance capex
- Expansion capex
- Acquisitions
- Dividends
- Buybacks
- Debt repayment
- Equity issuance
- Equipment purchases

Analyse:

`FCF → Reinvestment → Growth → ROIC`

For construction:

`Working Capital → Debt → Interest → FCF`

Determine whether growth is being funded through:

- Internal cash generation
- Customer advances
- Working-capital stretch
- Debt
- Equity issuance

---

# 19. EARNINGS QUALITY

Check:

- PAT vs CFO
- EBITDA vs CFO
- Receivables
- Inventory
- Contract assets
- Unbilled revenue
- Other income
- Exceptional items
- Capitalized expenses
- Claims income
- FX gains/losses
- Subsidies/grants where applicable

Flag:

`PAT ↑ + CFO ↓`

`Revenue ↑ + Receivables ↑↑`

`Revenue ↑ + Contract Assets ↑↑`

`Order Book ↑ + Revenue →`

`Revenue ↑ + ROCE ↓`

---

# 20. CYCLE ANALYSIS

Construction companies must be evaluated through the cycle.

Track:

- Industry demand
- Government capex
- Infrastructure spending
- Private capex
- Interest rates
- Credit availability
- Commodity prices
- Labour costs
- Construction activity
- Export demand where relevant

Determine whether current growth is:

- Structural
- Cyclical
- Market-share driven
- Price-driven
- Capacity/equipment-driven
- Acquisition-driven

Do not extrapolate peak-cycle margins indefinitely.

---

# 21. COMPETITIVE ADVANTAGE

Evaluate evidence for:

- Brand
- Technology
- Project execution capability
- Project reliability
- Distribution/network
- Installed equipment base
- Certifications
- Switching costs
- Customer relationships
- Manufacturing/procurement scale where relevant
- Procurement advantage
- Cost advantage
- Export capability
- IP where relevant
- Execution track record
- Aftermarket/service capability where relevant

Score evidence, not reputation alone.

---

# 22. PEER COMPARISON

Peers must have comparable business models and project exposure.

Compare:

- Order intake
- Order book
- Order-book growth
- Book-to-bill
- Order-book/revenue
- Revenue growth
- Execution
- EBITDA margin
- EBIT margin
- ROCE
- ROIC
- Net debt
- Working-capital days
- CFO/PAT
- CFO/EBITDA
- FCF
- P/E
- EV/EBITDA

Avoid comparing companies with materially different project mixes without adjusting the interpretation.

---

# 23. VALUATION ENGINE

Use where appropriate:

- P/E
- EV/EBITDA
- EV/EBIT
- EV/Revenue
- FCF yield
- Price/Book where relevant
- PEG
- ROCE
- ROIC

For cyclical companies:

**Normalize earnings across the cycle.**

Do not value a company solely on peak-year earnings.

## Historical Valuation

Calculate where data permits:

- Current P/E vs 3Y median
- Current P/E vs 5Y median
- Current P/E vs 10Y median
- Current EV/EBITDA vs history
- Current FCF yield vs history
- Current EV/Revenue vs history
- Current P/B vs history
- Historical high multiple
- Historical low multiple
- Current percentile
- Relevant cycle position

Historical average is context, not automatic fair value.

---

# 24. CAUSAL ANALYSIS ENGINE

The final report must explain:

**WHAT → CHANGED → WHY → IMPACT → RISK → WHAT TO MONITOR**

## Construction Causal Chain

```text
Awards ↑
→ Order Book ↑
→ Execution ↑
→ Billing ↑
→ Receivables ↑
→ CFO
→ Debt
→ Interest
→ FCF
→ ROCE
```

The engine must identify where the chain is breaking.

Examples:

```text
Order Book ↑
→ Execution →
→ Revenue →
```

Potential issue: execution bottleneck.

```text
Revenue ↑
→ Receivables/Contract Assets ↑↑
→ CFO ↓
```

Potential issue: working-capital-funded growth.

```text
Revenue ↑
→ EBITDA ↑
→ CFO ↓
```

Potential issue: low-quality earnings/cash conversion.

```text
Revenue ↑
→ Margin ↓
→ ROCE ↓
```

Potential issue: growth is destroying incremental economics.

---

# 25. POSITIVE SIGNAL ENGINE

Potential evidence-based signals:

- Order intake growth
- Order-book growth
- Book-to-bill > 1 sustained over time
- Improving execution
- Strong project pipeline
- Stable/improving project margins
- Strong cash conversion
- Falling leverage
- Improving ROCE
- Diversified customer base
- Strong repeat orders
- Successful project completion
- Successful capacity/equipment commissioning

The system must verify whether each signal is sustainable.

---

# 26. RED-FLAG ENGINE

## Orders

- Order book without execution
- High cancellation
- Low-quality orders
- Low-margin orders
- Excessive customer/project concentration

## Execution

- Project delays
- Cost overruns
- Weak billing
- Low conversion of awarded orders
- Repeated milestone slippage
- Claims/disputes

## Financial

- Revenue growth without CFO
- Rising receivables
- Rising contract assets
- Rising debt
- Falling ROCE
- Persistent negative FCF

## Operations

- Cost inflation
- Equipment underutilization
- Capacity/equipment ahead of demand
- Weak project margins

## Governance

- Related-party concerns
- Promoter pledge
- Auditor issues
- Excessive dilution
- Contingent-liability expansion

---

# 27. BAD GROWTH PATTERNS

### Pattern 1

`Order Book ↑↑ → Revenue →`

Possible issue:

Weak execution.

### Pattern 2

`Revenue ↑↑ → Receivables ↑↑ → CFO ↓`

Possible issue:

Working-capital-funded growth.

### Pattern 3

`Revenue ↑ → Contract Assets ↑↑ → CFO ↓`

Possible issue:

Accounting revenue growing ahead of cash realization.

### Pattern 4

`Revenue ↑ → EBITDA ↑ → CFO ↓`

Possible issue:

Low-quality earnings/cash conversion.

### Pattern 5

`Revenue ↑ → Margin ↓ → ROCE ↓`

Possible issue:

Growth is destroying incremental economics.

### Pattern 6

`Order Book ↑ → Debt ↑ → Interest ↑ → FCF ↓`

Possible issue:

Growth increasingly dependent on external funding.

---

# 28. DATA QUALITY

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

---

# 29. SOURCE PRIORITY

Use:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. Company filings
6. NSE/BSE filings
7. Government/sector agencies
8. Regulatory filings
9. Reliable financial databases
10. Third-party research

For government/project awards, prefer the official awarding authority or company filing.

---

# 30. MANAGEMENT GUIDANCE ENGINE

Extract:

- Revenue guidance
- Margin guidance
- Order-intake guidance
- Order-book guidance
- Capex guidance
- Equipment/capacity guidance
- Utilization guidance
- Project completion guidance
- Export guidance

Track:

`Guidance → Actual`

Classify:

- Delivered
- Missed
- Exceeded
- Revised

Do not treat management guidance as reported fact.

---

# 31. SCORING ARCHITECTURE

Base weights:

| Dimension | Weight |
|---|---:|
| Business Quality | 15% |
| Growth | 20% |
| Operating Quality | 20% |
| Financial Quality | 20% |
| Competitive Advantage | 10% |
| Valuation | 15% |

For Construction, give meaningful weight to:

- Order-book quality
- Execution
- Working capital
- Balance sheet
- Cash conversion
- ROCE

Industry-specific weights may be redistributed where necessary.

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

# 32. FINAL OUTPUT FORMAT

```text
Company:
Macro Sector:
Sector Value:
Industry:
Sub-Industry:
Business Model:

BUSINESS QUALITY       XX/100
GROWTH                 XX/100
OPERATING QUALITY      XX/100
FINANCIAL QUALITY      XX/100
COMPETITIVE ADVANTAGE  XX/100
VALUATION              XX/100

OVERALL SCORE          XX/100

DATA CONFIDENCE:
PRIMARY SOURCES:

BUSINESS OVERVIEW
-

ORDER BOOK
- Order intake:
- Order-book growth:
- Book-to-bill:
- Order-book/revenue:
- Order quality:
- Execution visibility:

PROJECT ECONOMICS
- Major projects:
- Project margins:
- Cost overruns:
- Delays:
- Claims:
- Billing:

OPERATING KPIs
- Execution rate:
- Equipment/fleet:
- Utilization:
- Project completion:

GROWTH ENGINE
- Revenue CAGR:
- Latest growth:
- Main growth driver:

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
- Inventory days:
- Payable days:
- Contract assets:
- Contract liabilities:
- Unbilled revenue:
- Cash conversion cycle:

BALANCE SHEET
- Debt:
- Net debt/cash:
- Interest coverage:
- Guarantees:
- Contingent liabilities:

COMPETITIVE ADVANTAGE
-

CAPITAL ALLOCATION
-

MANAGEMENT / GOVERNANCE
-

CYCLE POSITION
-

VALUATION
- P/E:
- EV/EBITDA:
- EV/EBIT:
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

# 33. CORE IMPLEMENTATION PRINCIPLE

The Industrials → Construction engine should not simply ask:

`Is revenue growing?`

It should determine:

**Are new projects being awarded?**

→ **Is the order book growing?**

→ **Is the order book high quality?**

→ **Are projects being executed on schedule?**

→ **Is execution converting into billing and revenue?**

→ **Are receivables and contract assets under control?**

→ **Is growth converting into CFO and FCF?**

→ **Is debt remaining manageable?**

→ **Is incremental capital generating attractive returns?**

The core analytical pipeline is:

**RAW DATA → NORMALIZATION → INDUSTRY KPIs → TRENDS → ORDER/EXECUTION ANALYSIS → WORKING CAPITAL → CASH FLOW → BALANCE SHEET → PEER COMPARISON → VALUATION → RED FLAGS → SCORING → FINAL THESIS**

---

## Construction Agent Architecture

```text
Company Identification
        ↓
Industrials Classification
        ↓
Construction Classification
        ↓
Sub-Industry / Project Type
        ↓
Business Model
        ↓
Financial Data
        ↓
Order Intake
        ↓
Order Book
        ↓
Order Quality
        ↓
Project Execution
        ↓
Billing / Revenue Recognition
        ↓
Receivables / Contract Assets
        ↓
Working Capital
        ↓
CFO / FCF
        ↓
Debt / Guarantees / Balance Sheet
        ↓
Project Margin Analysis
        ↓
Equipment / Asset Utilization
        ↓
ROCE / ROIC
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

## Core Fundamental Question

**Does this construction company have a durable and high-quality order book, the execution capability to convert awards into profitable revenue, disciplined working-capital management, sustainable cash generation, a manageable balance sheet and attractive returns on capital, while its current valuation is supported by normalized long-term earnings power?**
