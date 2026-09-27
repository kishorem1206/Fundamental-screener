# Services → Services — Fundamental Analysis Framework

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
**Macro Sector:** Services  
**Sector Value:** Services

## Industries Covered

1. Commercial Services & Supplies
2. Public Services
3. Transport Infrastructure
4. Engineering Services
5. Transport Services

---

# 1. PURPOSE

This standalone framework covers **Services → Services** and evaluates companies through their actual economic drivers rather than applying generic manufacturing or financial-sector ratios.

Core philosophy:

**BUSINESS MODEL → DEMAND → VOLUME / CONTRACTS → PRICING → CAPACITY / UTILIZATION → UNIT ECONOMICS → MARGINS → CASH FLOW → ROIC → VALUATION → RISK**

The engine must distinguish:

- Asset-light services
- Asset-heavy services
- Contract-driven services
- Transaction-driven services
- Infrastructure-linked services
- Government/public services
- Engineering/project businesses
- Transport operators

---

# 2. INDUSTRY COVERAGE

## 2.1 Commercial Services & Supplies

Possible businesses:

- Facility management
- Security services
- Staffing / recruitment
- Business support services
- Professional support services
- Waste management
- Cleaning services
- Testing / inspection
- Distribution support
- Other outsourced commercial services

Primary drivers:

- Contract wins
- Client retention
- Revenue per employee
- Volume
- Pricing
- Wage inflation
- Utilization
- Contract duration
- Renewal rate
- Working capital
- Cash conversion

## 2.2 Public Services

Economics may be linked to:

- Government contracts
- Public infrastructure
- Public-service delivery
- Regulated service arrangements
- Long-term concessions
- Public-sector customers

Primary drivers:

- Government spending
- Contract awards
- Concession terms
- Regulatory framework
- Tariffs
- Volume
- Collection efficiency
- Receivables
- Execution
- Contract renewals

**Important:** Separate government customer exposure from government-regulated economics.

## 2.3 Transport Infrastructure

Includes:

- Roads
- Airports
- Ports
- Rail-linked infrastructure
- Logistics infrastructure
- Terminals
- Warehousing infrastructure
- Toll / concession assets
- Other transport infrastructure

Primary drivers:

- Traffic / throughput
- Capacity
- Utilization
- Tariff
- Concession period
- New capacity
- Cargo / passenger volumes
- Contract structure
- Capex
- Debt
- Asset turnover

## 2.4 Engineering Services

Includes:

- Engineering consultancy
- Design engineering
- EPC-related engineering services
- Project management
- Technical services
- Engineering outsourcing
- Infrastructure engineering
- Industrial engineering

Primary drivers:

- Order inflow
- Order book
- Book-to-bill
- Execution
- Billing
- Project margins
- Employee productivity
- Utilization
- Working capital
- Project concentration

## 2.5 Transport Services

Includes:

- Road transport
- Rail-linked services
- Shipping
- Logistics
- Freight
- Passenger transport
- Aviation-related services
- Courier / express
- Warehousing-linked transportation
- Multimodal transport

Primary drivers:

- Volume
- Distance
- Yield
- Freight rates
- Load factor
- Fleet utilization
- Capacity
- Fuel
- Maintenance
- Network density
- Working capital

---

# 3. BUSINESS MODEL CLASSIFICATION

Before screening, classify every company.

Required fields:

- Main sector
- Industry
- Sub-industry
- Business model
- Revenue model
- Asset intensity
- Capital intensity
- Contract model
- Customer type
- Geography
- Pricing model
- Volume driver
- Capacity model
- Recurring revenue %
- Contract duration
- Government exposure

Revenue models may include:

- Recurring contracts
- Long-term contracts
- Project contracts
- Transaction fees
- Usage-based fees
- Toll / concession revenue
- Freight charges
- Passenger revenue
- Subscription
- Commission
- Consulting fees
- Engineering fees
- EPC / milestone billing
- Management fees

Do not apply the same ratio set to every Services company.

---

# 4. DATA PERIODS & DATA MODEL

Support:

- Annual
- Quarterly
- TTM
- Monthly operating statistics where available
- Contract period
- Concession period
- Management guidance period

Every metric should retain:

```text
metric_name
value
period
unit
source
source_date
data_type
confidence
company
industry
```

Allowed data types:

- REPORTED
- CALCULATED
- ESTIMATED
- MANAGEMENT_DISCLOSED
- THIRD_PARTY

---

# 5. CORE FINANCIAL METRICS

## Growth

- Revenue growth YoY
- Revenue CAGR 3Y
- Revenue CAGR 5Y
- Revenue CAGR 10Y
- EBITDA growth
- EBIT growth
- PAT growth
- EPS growth
- CFO growth
- FCF growth

## Profitability

- Gross margin where meaningful
- EBITDA margin
- EBIT margin
- PAT margin
- ROE
- ROCE
- ROIC
- Asset turnover

## Cash Flow

- CFO
- CFO/PAT
- CFO/EBITDA
- FCF
- FCF margin
- FCF conversion
- Capex
- Working-capital impact

## Balance Sheet

- Debt
- Cash
- Net debt
- Net debt/EBITDA
- Interest cost
- Lease liabilities
- Receivables
- Payables
- Inventory
- Contract assets
- Contract liabilities

---

# 6. COMMERCIAL SERVICES ANALYSIS

## 6.1 Contract Quality

Track:

- Number of contracts
- Contract value
- Average contract size
- Contract duration
- Renewal rate
- Retention rate
- New contracts
- Lost contracts
- Cross-sell
- Upsell
- Customer concentration

Formula:

```text
Contract Renewal Rate =
Renewed Contracts / Contracts Due for Renewal
```

Analyse:

- Recurring vs one-time revenue
- Customer switching costs
- Contract visibility
- Competitive intensity
- Pricing reset mechanism

## 6.2 Unit Economics

Track:

- Employees
- Billable employees
- Revenue/employee
- EBITDA/employee
- Client/site count
- Revenue/site
- Contract value/site
- Utilization
- Wage cost
- Subcontracting cost

For labor-intensive businesses:

```text
Revenue
↓
Employee Count
↓
Revenue / Employee
↓
Wage Cost
↓
Gross Margin
↓
EBITDA
```

Watch for wage inflation exceeding contractual price increases.

## 6.3 Working Capital

Track:

- Receivables
- DSO
- Payables
- DPO
- Contract assets
- Contract liabilities
- Security deposits
- Advance payments
- Cash conversion cycle

Red flag:

**Revenue and reported profit grow while receivables grow materially faster.**

Also investigate businesses where strong customer advances do not translate into the expected cash benefit.

---

# 7. PUBLIC SERVICES ANALYSIS

Track:

- Government revenue %
- Government customer concentration
- Contract awards
- Contract duration
- Renewal probability
- Tariff
- Subsidy
- Receivables from government entities
- Regulatory changes
- Payment cycle
- Collection efficiency

Separate:

- Contracted revenue
- Approved revenue
- Regulated revenue
- Subsidized revenue
- Uncontracted opportunity

Do not treat announced government spending as company revenue.

## Public-Service Contract Risk

Analyse:

- Change-in-law provisions
- Escalation clauses
- Termination clauses
- Penalties
- Service-level requirements
- Performance guarantees
- Minimum volume guarantees
- Concession rights
- Renegotiation history

Causal chain:

```text
Contract Award
↓
Execution
↓
Billing
↓
Collection
↓
Renewal
```

---

# 8. TRANSPORT INFRASTRUCTURE ANALYSIS

## 8.1 Capacity

Track:

- Installed capacity
- Current throughput
- Capacity utilization
- Expansion capacity
- Expansion capex
- Asset age
- Asset availability

Formula:

```text
Capacity Utilization =
Actual Throughput / Available Capacity
```

## 8.2 Roads

Track:

- Traffic volume
- Vehicle count
- Toll transactions
- Average daily traffic
- Toll revenue
- Toll rate
- Commercial vehicle mix

## 8.3 Airports

Track:

- Passenger traffic
- Aircraft movements
- Domestic passengers
- International passengers
- Aeronautical revenue
- Non-aeronautical revenue

## 8.4 Ports

Track:

- Cargo volume
- TEUs
- Bulk cargo
- Container throughput
- Revenue/ton
- Revenue/TEU
- Capacity utilization

## 8.5 Warehousing / Logistics Infrastructure

Track:

- Area
- Occupancy
- Throughput
- Revenue/sq ft
- Revenue/unit
- Rental yield

## 8.6 Tariff & Pricing

Track:

- Tariff
- Tariff growth
- Escalation mechanism
- Regulated tariff
- Market-linked pricing
- Volume discounts
- Revenue per unit

Decompose:

```text
Revenue Growth =
Volume Growth
+
Price / Tariff Growth
+
Mix
```

Determine whether growth is volume-led or price-led.

## 8.7 Concession Analysis

Track:

- Concession period
- Remaining concession life
- Initial concession date
- Revenue-sharing mechanism
- Minimum guarantee
- Traffic assumptions
- Actual traffic
- Capex obligations
- O&M obligations
- Termination provisions
- Renewal / extension terms

A high current cash flow may not have the same economic value if the concession has a short remaining life.

## 8.8 Infrastructure Capex & Returns

Track:

- Maintenance capex
- Growth capex
- Expansion capex
- Replacement capex
- Capex/revenue
- Capex/CFO
- Asset turnover
- ROCE
- ROIC

Separate maintenance capex from growth capex.

Calculate FCF after economically necessary maintenance capex where reliable data permits.

---

# 9. ENGINEERING SERVICES ANALYSIS

## 9.1 Order Book

Track:

- Order inflow
- Order book
- Order-book growth
- Book-to-bill
- Order execution
- Order cancellations
- Order deferrals
- New customers
- Repeat customers

Formula:

```text
Book-to-Bill =
New Order Intake / Revenue
```

```text
Order Book Coverage =
Order Book / Annualized Revenue
```

Interpret coverage in the context of project duration and execution capacity.

## 9.2 Project Economics

Track:

- Project size
- Project duration
- Milestones
- Billing schedule
- Cost-to-complete
- Estimated project margin
- Actual project margin
- Claims
- Variations
- Liquidated damages
- Penalties
- Delays

Watch for:

- Margin deterioration
- Cost overruns
- Delayed billing
- Receivable buildup
- Contract assets
- Aggressive revenue recognition

## 9.3 Engineering Employee Economics

Track:

- Employee count
- Engineering employees
- Billable employees
- Utilization
- Revenue/employee
- EBIT/employee
- Employee cost/revenue
- Attrition
- Hiring

Causal chain:

**Order-book growth → hiring → utilization → revenue → margin**

Hiring significantly ahead of order conversion can reduce near-term profitability.

---

# 10. TRANSPORT SERVICES ANALYSIS

## 10.1 Volume

Depending on business model:

- Tonnes transported
- Ton-km
- Passenger-km
- Shipments
- Parcels
- Trips
- Vehicle movements
- TEUs
- Load factor
- Occupancy
- Fleet utilization

## 10.2 Pricing / Yield

Track:

- Revenue per tonne
- Revenue per ton-km
- Revenue per passenger
- Revenue per shipment
- Revenue per vehicle
- Freight yield
- Passenger yield
- Average ticket price
- Fuel surcharge
- Contract rates
- Spot rates

Formula:

```text
Revenue = Volume × Yield
```

Decompose growth into:

- Volume
- Pricing
- Mix
- Fuel surcharge
- FX where applicable

## 10.3 Fleet Economics

For asset-heavy transport businesses track:

- Fleet size
- Fleet age
- Fleet utilization
- Vehicle availability
- Trips/vehicle
- Revenue/vehicle
- Maintenance cost/vehicle
- Fuel cost/vehicle
- Replacement cycle
- Capex/vehicle

Causal chain:

```text
Fleet
↓
Utilization
↓
Trips / Capacity
↓
Revenue
↓
Fuel + Maintenance
↓
EBITDA
↓
FCF
```

## 10.4 Fuel & Input Costs

Track where relevant:

- Fuel cost
- Fuel/revenue
- Fuel/vehicle
- Fuel/tonne
- Electricity
- Maintenance
- Tyres
- Personnel
- Toll costs
- Port charges
- Airport charges

Analyse pass-through mechanisms.

Key question:

**Can the company pass input-cost inflation to customers quickly enough?**

## 10.5 Logistics Network Economics

Track:

- Shipment density
- Network utilization
- Hub utilization
- Average distance
- First-mile cost
- Last-mile cost
- Sorting cost
- Delivery success rate
- Revenue/shipment
- Cost/shipment
- Customer density

Potential network advantage:

```text
Higher Density
↓
Lower Unit Cost
↓
Better Pricing / Margin
↓
More Customers
↓
Higher Density
```

---

# 11. MARGIN ANALYSIS

Track:

- Gross margin
- EBITDA margin
- EBIT margin
- PAT margin
- Contribution margin
- Margin volatility

Analyse:

- Volume operating leverage
- Pricing
- Mix
- Employee costs
- Fuel
- Subcontracting
- Maintenance
- Depreciation
- Finance cost

Separate:

**Structural margin improvement**

from:

**Temporary cost savings**

## Operating Leverage

### Asset-heavy

```text
Revenue Growth
↓
Asset Utilization
↓
Fixed Cost Absorption
↓
EBITDA Margin
↓
EBIT
```

### Asset-light

```text
Revenue Growth
↓
Employee Productivity
↓
Operating Leverage
↓
EBIT Margin
```

Identify when incremental revenue begins producing higher margins.

---

# 12. CASH FLOW ANALYSIS

Track:

- CFO
- CFO/PAT
- CFO/EBITDA
- FCF
- FCF margin
- Capex
- Working capital
- Receivables
- Contract assets
- Advances
- Maintenance capex

Formula:

```text
FCF = CFO - Capex
```

For infrastructure and transport companies distinguish:

- Maintenance capex
- Expansion capex
- Regulatory capex
- Contractual capex

---

# 13. BALANCE SHEET ANALYSIS

Track:

- Cash
- Debt
- Net debt
- Net debt/EBITDA
- Interest coverage
- Lease liabilities
- Receivables
- Contract assets
- Inventory
- Goodwill
- Intangibles
- CWIP
- Fixed assets

For asset-heavy services, lease liabilities can materially affect economic leverage.

---

# 14. RETURN ON CAPITAL

Track:

- ROE
- ROCE
- ROIC
- Asset turnover
- Capital turnover
- Incremental ROIC

Causal chain:

```text
Revenue
↓
EBIT
↓
NOPAT
↓
Capital Employed
↓
ROIC
```

Do not compare asset-light and asset-heavy businesses without considering capital intensity.

---

# 15. COMPETITIVE ADVANTAGE

Evaluate evidence for:

- Brand
- Scale
- Distribution
- Technology
- Route density
- Infrastructure ownership
- Regulatory barriers
- Cost advantage
- Operating expertise
- Customer relationships
- Network density
- Location advantage
- Long-term contracts
- Concessions

Evidence should support the claimed advantage.

---

# 16. CUSTOMER CONCENTRATION

Track:

- Largest customer %
- Top 5 customers %
- Top 10 customers %
- Government customer %
- Contract renewal rate
- Customer additions
- Customer losses
- Revenue concentration

Assess whether concentration creates:

- Pricing risk
- Renewal risk
- Credit risk
- Margin risk

---

# 17. MANAGEMENT & GOVERNANCE

Track:

- Promoter holding where applicable
- Promoter buying/selling
- Pledge
- Dilution
- Related-party transactions
- Auditor changes
- Auditor qualifications
- Management remuneration
- Regulatory actions
- Litigation
- Capital allocation
- Acquisitions
- Dividends
- Buybacks
- Debt-funded expansion

For concession businesses additionally track:

- Related-party concession transactions
- Contract amendments
- Government interactions
- Regulatory compliance

---

# 18. CAPITAL ALLOCATION

Analyse:

- Organic capex
- Maintenance capex
- Expansion capex
- Acquisitions
- Debt repayment
- Dividends
- Buybacks
- Asset sales

For infrastructure:

**Is incremental capex producing adequate incremental traffic, throughput, revenue and ROIC?**

For asset-light services:

**Is capital being reinvested into scalable growth or low-return expansion?**

---

# 19. MANAGEMENT GUIDANCE & CONCALL ANALYSIS

Extract:

- Revenue guidance
- Margin guidance
- Order inflow guidance
- Order-book execution
- Traffic / volume guidance
- Capacity expansion
- Capex guidance
- Pricing commentary
- Wage commentary
- Fuel commentary
- Contract renewals
- Government spending
- Regulatory changes
- Demand outlook
- Working-capital expectations

Compare:

```text
Previous Guidance
vs
Actual Outcome
```

Track management guidance credibility over time.

---

# 20. CONTRACT & ORDER-BOOK QUALITY

Do not evaluate order book only by size.

Analyse:

- Customer quality
- Contract duration
- Margin
- Execution complexity
- Payment terms
- Advance received
- Retention money
- Penalties
- Escalation clauses
- Cancellation clauses
- Working-capital requirement

A large low-margin or working-capital-heavy order book may have lower economic quality than its headline size suggests.

---

# 21. CYCLICALITY

Identify exposure to:

- Economic cycle
- Infrastructure cycle
- Government capex cycle
- Freight cycle
- Fuel cycle
- Construction cycle
- Consumer demand
- Industrial activity

Track:

- Revenue during upcycle
- Revenue during downcycle
- Margin peak
- Margin trough
- Cash flow through cycle
- Debt through cycle
- Capacity additions through cycle

Avoid extrapolating peak-cycle margins indefinitely.

---

# 22. BAD GROWTH PATTERNS

Flag:

### 1. Order-book growth without execution

Orders increase but revenue conversion remains weak.

### 2. Revenue growth without cash

PAT rises while CFO deteriorates.

### 3. Volume growth without profitability

Volumes rise but pricing/mix causes margin compression.

### 4. Capacity-led growth without utilization

Heavy capex occurs before demand is proven.

### 5. Government-order dependence

Growth depends disproportionately on government awards.

### 6. Receivable-led growth

Receivables rise much faster than revenue.

### 7. Contract-quality deterioration

Large contracts come with weak margins or unfavorable payment terms.

### 8. Debt-funded expansion

Debt rises materially before asset utilization stabilizes.

### 9. Acquisition-led growth

Reported growth depends heavily on acquisitions.

### 10. Temporary margin expansion

Margins improve because of unusually low fuel, wage, subcontracting or other costs.

---

# 23. CAUSAL ANALYSIS ENGINE

## Commercial Services

```text
Customer Demand
↓
Contract Wins
↓
Employees / Capacity
↓
Utilization
↓
Revenue / Employee
↓
Revenue
↓
EBITDA Margin
↓
CFO
↓
FCF
↓
ROIC
```

## Public Services

```text
Government / Public Demand
↓
Contract / Regulatory Award
↓
Execution
↓
Billing
↓
Collection
↓
Revenue
↓
Margin
↓
CFO
↓
ROIC
```

## Transport Infrastructure

```text
Economic Activity
↓
Traffic / Throughput
↓
Capacity Utilization
↓
Volume
↓
Tariff
↓
Revenue
↓
Operating Leverage
↓
EBITDA
↓
CFO
↓
FCF
↓
ROIC
```

## Engineering Services

```text
Demand
↓
Order Inflow
↓
Order Book
↓
Execution
↓
Revenue
↓
Project Margin
↓
Working Capital
↓
CFO
↓
FCF
↓
ROIC
```

## Transport Services

```text
Demand
↓
Volume
↓
Load Factor / Utilization
↓
Yield
↓
Revenue
↓
Fuel + Operating Costs
↓
EBITDA
↓
Capex
↓
FCF
↓
ROIC
```

---

# 24. PEER COMPARISON

Compare companies **within the same business model**.

## Commercial Services

- Revenue growth
- Contract growth
- Retention
- Revenue/employee
- EBITDA margin
- DSO
- CFO/PAT
- FCF margin
- ROIC
- Valuation

## Public Services

- Contract revenue
- Government exposure
- Receivable days
- EBITDA margin
- Cash conversion
- Debt
- ROCE
- Contract duration
- Valuation

## Transport Infrastructure

- Traffic / throughput growth
- Capacity utilization
- Revenue/unit
- EBITDA margin
- Capex
- Debt
- Asset turnover
- ROCE
- ROIC
- FCF yield
- Valuation

## Engineering Services

- Order inflow
- Order-book growth
- Book-to-bill
- Execution
- Project margins
- Working capital
- CFO
- ROCE
- Valuation

## Transport Services

- Volume growth
- Yield
- Load factor
- Fleet utilization
- Fuel/revenue
- EBITDA margin
- Debt
- FCF
- ROCE
- Valuation

Do not compare fundamentally different asset and contract models in one undifferentiated ranking.

---

# 25. HISTORICAL TREND ANALYSIS

Minimum:

- 3Y
- 5Y
- 10Y where available

Track:

- Revenue
- EBITDA
- EBIT
- PAT
- EPS
- CFO
- FCF
- ROCE
- ROIC
- Margins
- Debt
- Working capital
- Capex
- Volume
- Utilization
- Order book
- Contract wins
- Customer concentration

Identify:

- Structural growth
- Cyclical growth
- Inflection
- Deceleration
- Recovery
- Margin normalization

---

# 26. VALUATION FRAMEWORK

Valuation must reflect the business model.

## Commercial Services

- P/E
- EV/EBITDA
- EV/EBIT
- FCF yield
- Historical multiples

## Public Services

- P/E
- EV/EBITDA
- FCF yield
- ROCE-adjusted valuation

## Transport Infrastructure

- EV/EBITDA
- EV/EBIT
- P/E
- Asset-value approaches where appropriate
- FCF yield
- Historical multiples

## Engineering Services

- P/E
- EV/EBITDA
- EV/EBIT
- FCF yield
- Growth-adjusted valuation

## Transport Services

- P/E
- EV/EBITDA
- EV/EBIT
- EV/Sales where appropriate
- FCF yield
- Asset-adjusted valuation

Always compare:

- Current valuation
- Historical valuation
- Peer valuation
- Growth
- ROIC
- Cash conversion
- Balance-sheet risk
- Earnings durability

---

# 27. RISK ANALYSIS

## Business Risks

- Demand slowdown
- Customer concentration
- Contract loss
- Pricing pressure
- Technology disruption
- Competition
- Government dependence
- Regulatory change

## Infrastructure Risks

- Traffic shortfall
- Construction delays
- Concession risk
- Tariff restrictions
- Cost overruns
- Large capex requirements
- Refinancing risk

## Transport Risks

- Fuel prices
- Freight rates
- Volume slowdown
- Fleet utilization
- Maintenance
- Regulatory restrictions
- Capacity additions

## Engineering Risks

- Cost overruns
- Project delays
- Claims
- Penalties
- Working-capital stress
- Aggressive revenue recognition
- Order cancellations

## Financial Risks

- Excess leverage
- Weak CFO
- Rising receivables
- High capex
- Low ROIC
- Lease liabilities
- Refinancing requirements

---

# 28. POSITIVE SIGNAL ENGINE

Potential evidence-backed positive signals:

- Sustainable revenue growth
- Strong recurring contracts
- High renewal rates
- Rising order inflow
- Strong order-book coverage
- Healthy book-to-bill
- Rising utilization
- Pricing power
- Improving unit economics
- Stable/improving margins
- Strong CFO conversion
- Strong FCF
- High ROCE / ROIC
- Improving asset utilization
- Declining leverage
- High-quality customers
- Long-duration contracts
- Favorable concession economics
- Successful capacity expansion
- Consistent guidance delivery

These must be supported by data rather than automatically treated as positive.

---

# 29. RED-FLAG ENGINE

Flag when supported by evidence:

- Order book falling
- Order book not converting into revenue
- Order cancellations
- Margin deterioration
- Receivables rising faster than revenue
- CFO/PAT deterioration
- High working-capital requirements
- Debt-funded capex
- Low asset utilization
- Excess capacity
- Contract concentration
- Government receivable buildup
- Concession expiry approaching
- Traffic below assumptions
- Fuel inflation without pass-through
- Aggressive revenue recognition
- Project cost overruns
- Auditor qualifications
- Related-party concerns
- Excessive dilution
- Repeated acquisitions
- Repeated guidance misses

---

# 30. SCORING ARCHITECTURE

Suggested dimensions:

| Dimension | Indicative Weight |
|---|---:|
| Business Quality | 15% |
| Growth Quality | 15% |
| Operating Quality | 15% |
| Financial Quality | 15% |
| Competitive Advantage | 10% |
| Management & Governance | 10% |
| Cash Flow Quality | 10% |
| Valuation | 10% |

Weights should be configurable by industry.

### Commercial Services

Emphasize:

- Contract retention
- Revenue/employee
- Pricing
- Cash conversion

### Public Services

Emphasize:

- Contract quality
- Receivables
- Regulatory risk
- Cash conversion

### Transport Infrastructure

Emphasize:

- Volume
- Capacity
- Tariff
- Concession life
- Debt
- ROIC

### Engineering Services

Emphasize:

- Order inflow
- Order-book conversion
- Project margin
- Working capital

### Transport Services

Emphasize:

- Volume
- Yield
- Load factor
- Fleet utilization
- Fuel
- FCF

A valuation score should not hide severe operating, balance-sheet or governance risks.

Every score should retain:

```text
score
evidence
reason
period
source
confidence
```

---

# 31. DATA QUALITY & CONFIDENCE

Every metric must retain its source.

Required:

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

Confidence:

- HIGH
- MEDIUM
- LOW

Source priority:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. NSE / BSE filings
6. Regulatory filings
7. Company disclosures
8. Reliable financial databases
9. Third-party research

If sources conflict:

1. Prefer primary source.
2. Preserve the conflicting value where material.
3. Flag the discrepancy.
4. Do not silently overwrite.

---

# 32. MANAGEMENT / CONCALL INTELLIGENCE

Parse management commentary for:

- Demand
- Contract wins
- Order inflow
- Order-book conversion
- Volume
- Pricing
- Wage costs
- Fuel costs
- Capex
- Capacity
- Utilization
- Working capital
- Government spending
- Regulatory changes
- Competitive intensity

Use LLMs to extract statements and compare them over time.

Store:

```text
statement
speaker
date
quarter
topic
direction
source
confidence
```

Separate:

**Management expectation**

from:

**Reported operating evidence.**

---

# 33. AGENT ARCHITECTURE

```text
Company Profile Agent
        ↓
Financial Data Agent
        ↓
Business Model Agent
        ↓
Operating Metrics Agent
        ↓
Contract / Order Book Agent
        ↓
Management / Concall Agent
        ↓
Services Analysis Agent
        ↓
Causal Analysis Agent
        ↓
Peer Comparison Agent
        ↓
Valuation Agent
        ↓
Risk / Red Flag Agent
        ↓
Scoring Agent
        ↓
Final Investment Analysis
```

The calculation layer should remain deterministic.

The LLM should interpret evidence rather than generate numeric truth.

---

# 34. FINAL SCREENER OUTPUT

Every Services company report should contain:

## 1. Company Overview

- Business
- Industry
- Revenue model
- Asset intensity
- Customer profile
- Geography

## 2. Business Quality

- Business model
- Contract quality
- Competitive advantage
- Customer concentration

## 3. Growth Engine

- Revenue growth
- Volume growth
- Order inflow
- Order-book growth
- Capacity growth
- Pricing

## 4. Operating Engine

- Utilization
- Productivity
- Pricing
- Unit economics
- Capacity
- Margin

## 5. Financial Engine

- Revenue
- EBITDA
- EBIT
- PAT
- CFO
- FCF
- ROIC

## 6. Balance Sheet

- Debt
- Net debt
- Lease liabilities
- Working capital
- Capex
- Asset intensity

## 7. Management

- Guidance
- Execution credibility
- Governance
- Capital allocation
- Concall evidence

## 8. Valuation

- Current valuation
- Historical valuation
- Peer valuation
- Growth-adjusted valuation

## 9. Red Flags

Evidence-backed concerns.

## 10. Positive Signals

Evidence-backed strengths.

## 11. Peer Position

Use the correct business-model peer group.

## 12. Investment Thesis

Summarize:

- Demand engine
- Contract/order-book engine
- Operating engine
- Cash engine
- Capital efficiency
- Valuation
- Key risks

## 13. Bull Case

Evidence-based potential business drivers.

## 14. Bear Case

Evidence-based downside drivers.

## 15. Thesis Break Conditions

Define measurable conditions that would invalidate the thesis.

Examples:

- Order inflow deterioration
- Poor order-book conversion
- Persistent utilization decline
- Margin compression
- Receivable deterioration
- CFO/FCF deterioration
- Traffic/volume weakness
- Capacity underutilization
- Excess leverage
- Contract loss

## 16. Next-Quarter Watchlist

Track the operating drivers most relevant to the company:

- Revenue
- Volume
- Pricing
- Order inflow
- Order book
- Book-to-bill
- Utilization
- Capacity
- Margins
- Working capital
- CFO
- FCF
- Debt
- Management guidance
- Contract renewals
- Regulatory developments

---

# 35. CORE IMPLEMENTATION RULE

The Services analysis engine must answer:

> **What creates demand, how does that demand convert into contracts/volume, how efficiently does the company execute, how much capital is required, how much cash is ultimately generated, and what is the market already pricing in?**

Central causal model:

```text
BUSINESS MODEL
      ↓
DEMAND
      ↓
CONTRACTS / ORDERS / VOLUME
      ↓
CAPACITY / UTILIZATION
      ↓
PRICING / YIELD
      ↓
REVENUE
      ↓
MARGINS
      ↓
CFO
      ↓
FCF
      ↓
ROIC
      ↓
VALUATION
      ↓
RISK / THESIS BREAK
```

The framework must always distinguish **asset-light services, contract-driven services, engineering/project businesses, infrastructure assets and transport operators** because their economics, capital requirements and valuation drivers are materially different.
