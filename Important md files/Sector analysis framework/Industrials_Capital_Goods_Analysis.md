# Industrials → Capital Goods — Fundamental Analysis Framework

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
**Sector Value:** Capital Goods

## Industries Covered

1. Industrial Manufacturing
2. Industrial Products
3. Aerospace & Defense
4. Agricultural, Commercial & Construction Vehicles
5. Electrical Equipment

---

# 1. PURPOSE

This standalone framework is for companies classified under **Industrials → Capital Goods**.

The engine must classify the company first and then apply the relevant industry module.

Capital Goods businesses are often cyclical, order-driven and/or capital-intensive. The core analytical chain is:

**Orders → Order Book → Execution → Revenue → Utilization → Margin → Cash Flow → ROCE/ROIC**

The screener must not judge a capital-goods company using a single ratio such as P/E, EBITDA margin or debt/equity.

---

# 2. BUSINESS CLASSIFICATION

Capture:

- Industry
- Sub-industry
- Business model
- Product/service categories
- End markets
- Domestic/export mix
- Government/private exposure
- Project/product mix
- Recurring vs project revenue
- Aftermarket/service revenue
- Order-driven vs capacity-driven model
- Customer concentration
- Geography concentration
- Manufacturing footprint
- Installed capacity
- Capacity utilization
- Competitive advantages
- Regulatory exposure
- Capital intensity
- Working-capital intensity

The classification engine must identify the relevant Capital Goods industry before applying specialized KPIs.

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
- ROE
- ROCE
- ROIC
- Asset turnover
- Capital turnover

## 3.3 Cash Flow

Track:

- CFO
- CFO/PAT
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
- Contingent liabilities
- Guarantees
- Capital commitments

---

# 4. INDUSTRIAL MANUFACTURING

Examples:

- Industrial machinery
- Engineering equipment
- Process equipment
- Factory equipment
- Material-handling equipment
- Industrial systems

## 4.1 Revenue Drivers

Track:

- New equipment sales
- Replacement demand
- Service revenue
- Spare parts
- Aftermarket
- Export revenue
- Domestic revenue
- Product mix

Calculate:

`Aftermarket Revenue %`

`Recurring/Service Revenue %`

## 4.2 Orders

Track:

- Order intake
- Order intake growth
- Order book
- Order-book growth
- Book-to-bill
- Order-book/revenue
- Cancellation rate
- Order execution period

Formulas:

`Book-to-Bill = Order Intake / Revenue`

`Order Book Coverage = Closing Order Book / TTM Revenue`

Do not interpret a high order book as automatically positive. Assess order quality, margins, execution risk and customer concentration.

## 4.3 Manufacturing Economics

Track:

- Capacity
- Capacity utilization
- Plant additions
- Revenue/capacity
- Revenue/employee
- Manufacturing yield
- Scrap/rejection
- Raw-material cost
- Employee cost
- Freight
- Energy cost

Causal chain:

`Capacity → Utilization → Revenue → Operating Leverage → EBIT Margin`

## 4.4 Red Flags

- Order book rising while execution falls
- Order cancellations
- Margin deterioration
- Capacity added ahead of demand
- Customer concentration
- Rising receivables
- Working-capital absorption
- Low ROCE despite high capex
- Commodity input inflation without pricing power

---

# 5. INDUSTRIAL PRODUCTS

Track:

- Product categories
- Market share
- Installed base
- Product lifecycle
- Replacement cycle
- Distribution network
- Channel inventory
- Dealer count
- Dealer productivity
- Aftermarket
- Export mix

## 5.1 Pricing Power

Analyse:

`ASP Growth vs Volume Growth`

Separate:

- Price
- Volume
- Mix
- Currency

Track gross margin and EBIT margin through input-cost cycles.

## 5.2 Competitive Advantage

Evaluate evidence for:

- Brand
- Technology
- Distribution
- Switching cost
- Installed base
- Certification
- Product reliability
- Customer relationships

---

# 6. AEROSPACE & DEFENSE

Additional analysis:

- Government orders
- Defence orders
- Export orders
- Order backlog
- Program visibility
- Platform participation
- Indigenous content
- Technology/IP
- Certifications
- Development projects
- Production programs
- R&D
- Customer concentration
- Government dependence
- Execution timelines

## 6.1 Order Book Quality

Classify:

- Development order
- Prototype
- Production contract
- Long-term program
- Maintenance/service contract

A large development pipeline must not be treated as equivalent to contracted production revenue.

## 6.2 Revenue Visibility

Track:

- Order book
- Order-book/revenue
- Multi-year contracts
- Execution schedule
- Milestones
- Program delays
- Cancellations

## 6.3 R&D

Track:

- R&D/revenue
- R&D growth
- New technologies
- Product approvals
- Successful commercialization
- IP/patents
- Customer qualification

Causal chain:

`R&D → Qualification → Contract → Production → Revenue → Margin → ROIC`

## 6.4 Red Flags

- Delayed programs
- Order cancellations
- High government/customer concentration
- Cost overruns
- Low conversion of announced orders
- Large receivables
- Working-capital stress
- Regulatory/export restrictions
- Capex without contracted demand

---

# 7. AGRICULTURAL, COMMERCIAL & CONSTRUCTION VEHICLES

Track:

- Unit volumes
- Market share
- Industry volumes
- ASP
- Revenue/unit
- Product mix
- Domestic/export
- Dealer network
- Dealer inventory
- Replacement demand
- Financing availability
- Commodity/agriculture cycle
- Construction/infrastructure cycle

## 7.1 Volume Analysis

Break revenue growth into:

`Volume + Price + Mix + Currency`

Compare company volume growth with industry volume growth.

Interpret:

`Company Volume Growth - Industry Growth`

as an indicator of relative market-share movement, subject to product/geography mix.

## 7.2 Dealer Economics

Track:

- Dealer count
- Dealer additions
- Dealer productivity
- Inventory
- Channel financing
- Dealer receivables
- Dealer concentration

## 7.3 Red Flags

- Revenue growth driven only by price
- Market-share loss
- Rising dealer inventory
- Heavy discounting
- Margin pressure
- Commodity/input-cost pressure
- Weak replacement demand
- High financing dependence

---

# 8. ELECTRICAL EQUIPMENT

Examples:

- Switchgear
- Transformers
- Cables
- Motors
- Electrical systems
- Power equipment
- Industrial electrical products

Track:

- Order intake
- Order book
- Capacity
- Utilization
- Product mix
- Transmission/distribution exposure
- Industrial exposure
- Renewable exposure
- Building/infrastructure exposure
- Export exposure

## 8.1 Input Cost

Track:

- Copper
- Aluminium
- Steel
- Other key materials

Analyse:

`Input Cost → Price Pass-through → Gross Margin → EBITDA Margin`

## 8.2 Order Quality

Track:

- Order size
- Customer
- Project
- Margin
- Execution period
- Cancellation risk
- Government/private mix

---

# 9. CAPITAL GOODS COMMON ORDER-BOOK ENGINE

For every order-driven company, calculate:

## Order Intake Growth

`Current Period Order Intake / Previous Comparable Period - 1`

## Book-to-Bill

`Order Intake / Revenue`

## Order Book Coverage

`Closing Order Book / TTM Revenue`

## Order Execution

`Revenue from Orders / Opening Order Book`

Use only where reliable data exists.

## Order Quality

Classify orders by:

- High-margin vs low-margin
- Domestic vs export
- Government vs private
- Short-cycle vs long-cycle
- Product vs project
- Repeat vs new customer

The report must never say simply:

`Order Book is strong`

without explaining:

- Size
- Growth
- Coverage
- Quality
- Margin
- Customer
- Execution period

---

# 10. CAPACITY & UTILIZATION ENGINE

Track:

- Installed capacity
- Production
- Capacity utilization
- New capacity
- Capex
- Asset turnover
- Revenue/capacity
- ROCE

Causal chain:

`Capex → Capacity → Utilization → Revenue → Margin → ROCE`

Flag:

`Capex ↑↑ + Utilization → + ROCE ↓`

as potential overcapacity/capital-allocation risk.

---

# 11. PRICING POWER ENGINE

For industrial businesses:

`Revenue Growth = Volume Growth + Price Growth + Mix Growth + Currency`

Analyse:

- ASP
- Realization
- Input costs
- Price pass-through
- Gross margin
- EBIT margin

Positive evidence includes:

- Stable/improving margins despite input inflation
- Price increases retained
- Mix improvement
- Market-share gains

---

# 12. COMMON INDUSTRIAL COMPETITIVE ADVANTAGE

Evaluate:

- Brand
- Technology
- Product reliability
- Distribution
- Installed base
- Certifications
- Switching costs
- Customer relationships
- Manufacturing scale
- Procurement advantage
- Cost advantage
- Export capability
- IP
- Aftermarket network

Score evidence, not reputation alone.

---

# 13. CUSTOMER CONCENTRATION

Track:

- Top 1 customer %
- Top 5 customer %
- Government %
- Export customer %
- Repeat customer %
- New customer %
- Customer retention

Flag:

`Top Customer ↑ + Revenue Dependence ↑`

especially if contract renewal risk is material.

---

# 14. MANAGEMENT & GOVERNANCE

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

Record:

`Evidence → Date → Source → Severity → Status`

---

# 15. CAPITAL ALLOCATION

Track:

- Maintenance capex
- Expansion capex
- Acquisitions
- Dividends
- Buybacks
- Debt repayment
- Equity issuance
- R&D

Analyse:

`FCF → Reinvestment → Growth → ROIC`

For Capital Goods:

`Capex → Capacity → Utilization → ROCE`

---

# 16. EARNINGS QUALITY

Check:

- PAT vs CFO
- EBITDA vs CFO
- Receivables
- Inventory
- Contract assets
- Other income
- Exceptional items
- Capitalized expenses
- Claims income where applicable
- FX gains/losses
- Subsidies/grants where applicable

Flag:

`PAT ↑ + CFO ↓`

`Revenue ↑ + Receivables ↑↑`

`Order Book ↑ + Revenue →`

`Revenue ↑ + ROCE ↓`

---

# 17. CYCLE ANALYSIS

Capital Goods companies must be evaluated through the cycle.

Track:

- Industry demand
- Capacity additions
- Utilization
- Commodity prices
- Interest rates
- Government capex
- Infrastructure spending
- Private capex
- Export demand
- Credit availability

Determine whether current growth is:

- Structural
- Cyclical
- Market-share driven
- Price-driven
- Capacity-driven
- Acquisition-driven

Do not extrapolate peak-cycle margins indefinitely.

---

# 18. PEER COMPARISON

Peers must have comparable business models.

For Capital Goods, compare:

- Revenue growth
- Order intake
- Order-book growth
- Book-to-bill
- Order-book/revenue
- EBITDA margin
- EBIT margin
- ROCE
- ROIC
- CFO/PAT
- FCF
- Debt
- P/E
- EV/EBITDA

For Vehicles, compare:

- Volume growth
- Market share
- ASP
- Revenue growth
- EBITDA margin
- ROCE
- Dealer inventory
- P/E
- EV/EBITDA

---

# 19. VALUATION ENGINE

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

# 20. CAUSAL ANALYSIS ENGINE

The final report must explain:

**WHAT → CHANGED → WHY → IMPACT → RISK → WHAT TO MONITOR**

## Capital Goods Causal Chain

```text
Demand ↑
→ Orders ↑
→ Order Book ↑
→ Execution ↑
→ Revenue ↑
→ Utilization ↑
→ Margin ↑
→ CFO ↑
→ ROCE ↑
```

## Vehicles Causal Chain

```text
Industry Volume
→ Company Volume
→ Market Share
→ ASP/Mix
→ Revenue
→ Gross Margin
→ EBITDA
→ CFO
→ ROCE
```

---

# 21. POSITIVE SIGNAL ENGINE

Potential evidence-based signals:

- Order intake growth
- Order-book growth
- Book-to-bill > 1 sustained over time
- Improving execution
- Rising utilization
- Stable/improving margins
- Pricing power
- Market-share gains
- Strong cash conversion
- Falling leverage
- Improving ROCE
- Strong aftermarket
- Increasing recurring revenue
- Diversified customer base
- Strong export growth
- Successful capacity commissioning

The system must verify whether each signal is sustainable.

---

# 22. RED-FLAG ENGINE

## Orders

- Order book without execution
- High cancellation
- Low-quality orders
- Low-margin orders

## Financial

- Revenue growth without CFO
- Rising receivables
- Rising debt
- Falling ROCE
- Persistent negative FCF

## Operations

- Falling utilization
- Capacity ahead of demand
- Cost overruns
- Project delays
- Input inflation

## Governance

- Related-party concerns
- Promoter pledge
- Auditor issues
- Excessive dilution

---

# 23. BAD GROWTH PATTERNS

### Pattern 1

`Order Book ↑↑ → Revenue →`

Possible issue: weak execution.

### Pattern 2

`Revenue ↑↑ → Receivables ↑↑ → CFO ↓`

Possible issue: working-capital-funded growth.

### Pattern 3

`Capex ↑↑ → Utilization → → ROCE ↓`

Possible issue: capacity added ahead of demand.

### Pattern 4

`Revenue ↑ → EBITDA ↑ → CFO ↓`

Possible issue: low-quality earnings/cash conversion.

### Pattern 5

`Industry Growth ↑ → Company Growth →`

Possible issue: potential market-share loss.

### Pattern 6

`Revenue ↑ → Margin ↓ → ROCE ↓`

Possible issue: growth is destroying incremental economics.

---

# 24. DATA QUALITY

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

# 25. SOURCE PRIORITY

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

# 26. MANAGEMENT GUIDANCE ENGINE

Extract:

- Revenue guidance
- Margin guidance
- Order-intake guidance
- Order-book guidance
- Capex guidance
- Capacity guidance
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

# 27. SCORING ARCHITECTURE

Base weights:

| Dimension | Weight |
|---|---:|
| Business Quality | 15% |
| Growth | 20% |
| Operating Quality | 20% |
| Financial Quality | 20% |
| Competitive Advantage | 10% |
| Valuation | 15% |

For Capital Goods, give meaningful weight to:

- Order quality
- Execution
- Capacity utilization
- Margin
- ROCE
- Cash conversion

Industry-specific weights may be redistributed when required by the sub-industry.

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

# 28. FINAL OUTPUT FORMAT

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

OPERATING KPIs
- Capacity:
- Utilization:
- Volume:
- ASP:
- Market share:

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
- FCF:
- FCF/PAT:

WORKING CAPITAL
- Receivable days:
- Inventory days:
- Payable days:
- Contract assets:
- Cash conversion cycle:

BALANCE SHEET
- Debt:
- Net debt/cash:
- Interest coverage:
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

# 29. CORE IMPLEMENTATION PRINCIPLE

The Industrials → Capital Goods engine should not simply ask:

`Is revenue growing?`

It should determine:

**Is demand growing?**

→ **Are orders increasing?**

→ **Is the order book high quality?**

→ **Are orders being executed?**

→ **Is capacity being utilized?**

→ **Are margins sustainable?**

→ **Is growth converting into cash?**

→ **Is incremental capital generating attractive returns?**

The core analytical pipeline is:

**RAW DATA → NORMALIZATION → INDUSTRY KPIs → TRENDS → ORDER/EXECUTION ANALYSIS → CASH FLOW → PEER COMPARISON → VALUATION → RED FLAGS → SCORING → FINAL THESIS**

---

## Implementation Notes for the Screener

The Capital Goods module should dynamically activate industry-specific metrics:

| Industry | Priority Analytical Metrics |
|---|---|
| Industrial Manufacturing | Order intake, order book, book-to-bill, execution, capacity utilization, aftermarket, manufacturing economics, ROCE |
| Industrial Products | Product mix, market share, installed base, replacement cycle, ASP vs volume, distribution, dealer productivity, aftermarket |
| Aerospace & Defense | Government/defence/export orders, backlog quality, program visibility, platform participation, certifications, R&D, commercialization, execution |
| Agricultural, Commercial & Construction Vehicles | Unit volumes, industry volumes, market share, ASP, revenue/unit, product mix, dealer inventory, financing, cycle |
| Electrical Equipment | Order intake, order book, capacity, utilization, product mix, T&D/industrial/renewable exposure, copper/aluminium/steel costs, pass-through |

The report generator should preserve metric provenance and distinguish reported data from calculated, estimated, management-disclosed and third-party data.
