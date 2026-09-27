# Utilities → Power — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

## 1. Purpose

This standalone framework covers the **Utilities → Power** sector value.

It is designed for companies involved in:

- Power generation
- Power transmission
- Power distribution
- Integrated utilities
- Renewable power
- Thermal power
- Hydro power
- Nuclear power
- Power trading
- Renewable platforms
- Power infrastructure

Power businesses must be analyzed as regulated, infrastructure-heavy and often capital-intensive businesses. Generic profitability ratios are not sufficient.

The core economic chain is:

> **DEMAND → CAPACITY → UTILIZATION → TARIFF → REVENUE → FUEL / INPUT COST → EBITDA → CAPEX → DEBT → CFO → FCF → ROIC**

The engine must always distinguish **regulated, contracted and merchant economics**, and separate **generation, transmission, distribution and renewable models** before applying ratios or valuation metrics.

---

## 2. Power Business Model Classification

Before analysis, classify each company by:

- Power utility type
- Generation / transmission / distribution / integrated
- Regulated / merchant
- Contracted / spot exposure
- Renewable / thermal / hydro / nuclear / other
- Customer type
- Geography
- Asset intensity
- Capital intensity
- Tariff mechanism
- Contract duration
- Regulatory framework

### Revenue Models

- Regulated tariff
- Cost-plus tariff
- Availability-based tariff
- Power purchase agreement
- Merchant power
- Transmission charges
- Distribution charges
- Capacity charges
- Usage-based tariff
- Connection charges
- Renewable power purchase agreement

---

## 3. Data Periods & Data Quality

Support:

- Annual
- Quarterly
- TTM
- Monthly generation
- Monthly demand
- Monthly PLF
- Monthly transmission/distribution data
- Tariff periods
- Regulatory periods
- PPA/concession periods

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

Confidence:

- HIGH
- MEDIUM
- LOW

### Source Priority

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. NSE / BSE filings
6. CERC
7. SERC
8. Ministry of Power
9. MNRE
10. CEA
11. Other relevant regulators
12. Company disclosures
13. Reliable financial databases
14. Third-party research

When sources conflict:

1. Prefer the primary source.
2. Preserve material discrepancies.
3. Flag unresolved differences.
4. Never silently overwrite.

---

# 4. Power Demand Analysis

Track:

- Electricity demand
- Peak demand
- Demand growth
- Industrial demand
- Commercial demand
- Residential demand
- Agricultural demand
- Data-center demand
- EV-related demand where relevant

Analyze:

```text
Demand Growth
vs
Generation Growth
vs
Capacity Growth
```

Identify whether demand is:

- Structural
- Cyclical
- Weather-driven
- Industrial-cycle driven
- Policy-driven

### Core Questions

- Is demand growth translating into generation growth?
- Is generation growth being met by existing capacity or new capacity?
- Is peak-demand growth creating tighter utilization?
- Is demand growth broad-based or concentrated in a particular customer segment?
- Is the demand driver structural or temporary?

---

# 5. Power Generation Analysis

Track:

- Installed capacity
- Capacity additions
- Generation
- Plant Load Factor (PLF)
- Availability
- Capacity utilization
- Heat rate
- Auxiliary consumption
- Plant efficiency
- Renewable capacity
- Thermal capacity
- Hydro capacity
- Nuclear capacity

Calculate:

```text
PLF =
Actual Generation / Maximum Possible Generation
```

Analyze:

- Capacity growth
- Generation growth
- Utilization
- Availability
- Efficiency
- Generation per MW
- Change in PLF over time

### Critical Rule

> Do not treat capacity additions as value creation unless demand, utilization and returns support the investment.

---

# 6. Tariff & Monetization Analysis

Track:

- Average tariff
- Realized tariff
- PPA tariff
- Merchant tariff
- Transmission tariff
- Distribution tariff
- Renewable tariff
- Tariff escalation
- Fuel pass-through
- Regulatory adjustment

Decompose revenue:

```text
Revenue =
Volume × Realized Tariff
```

Analyze:

- Tariff increases
- Tariff reductions
- Fuel pass-through
- Regulatory true-ups
- Competitive tariff pressure
- Contracted versus merchant realization

### Key Question

Is revenue growth coming from:

1. Higher generation/volume?
2. Higher tariff?
3. Better mix?
4. Regulatory adjustment?
5. Merchant pricing?

Separate genuine operating growth from tariff-driven or regulatory-driven growth.

---

# 7. Power Purchase Agreement Analysis

Track:

- PPA capacity
- PPA tenure
- PPA tariff
- Fixed charges
- Variable charges
- Escalation
- Minimum offtake
- Availability requirements
- Counterparty
- Payment security
- Contract expiry

Assess:

- Revenue visibility
- Margin visibility
- Counterparty quality
- Repricing risk
- Renewal risk
- Offtake certainty

Always separate:

> **Contracted generation**

from:

> **Merchant generation**

### PPA Quality Analysis

For each material PPA, capture:

```text
PPA
├── Capacity
├── Tenure
├── Tariff
├── Escalation
├── Fixed / Variable component
├── Offtake obligation
├── Counterparty
├── Payment security
├── Expiry
├── Renewal / repricing risk
└── Expected cash-flow contribution
```

---

# 8. Merchant Power Analysis

Track:

- Merchant capacity
- Merchant generation
- Merchant tariff
- Spot power prices
- Peak/off-peak prices
- Power exchange prices
- Merchant EBITDA contribution

Calculate:

```text
Merchant Revenue =
Merchant Volume × Merchant Price
```

Analyze:

- Merchant revenue contribution
- Merchant EBITDA contribution
- Exposure to spot prices
- Peak versus off-peak realization
- Historical merchant-price cycle

### Important Rule

Merchant earnings can be significantly more cyclical than regulated or contracted earnings.

> Do not extrapolate peak merchant tariffs indefinitely.

---

# 9. Thermal Power Analysis

Track:

- Coal consumption
- Gas consumption
- Fuel cost/unit
- Heat rate
- Plant Load Factor
- Availability
- Auxiliary consumption
- Transportation cost
- Fuel inventory
- Fuel quality

Calculate:

```text
Fuel Cost / Unit of Generation
```

Analyze:

- Fuel efficiency
- Fuel availability
- Imported vs domestic fuel
- Fuel pass-through
- Transportation constraints
- Heat-rate improvement/deterioration
- Auxiliary consumption

### Core Question

Can the company pass fuel-cost inflation through tariffs or contracts?

---

# 10. Renewable Power Analysis

Track:

- Solar capacity
- Wind capacity
- Hybrid capacity
- Renewable generation
- Capacity utilization
- CUF
- PPA tariff
- PPA duration
- Module costs
- Turbine costs
- Storage
- Curtailment
- Grid connectivity

Calculate:

```text
CUF =
Actual Generation / Theoretical Maximum Generation
```

Analyze:

- Generation versus contracted expectations
- Curtailment
- Degradation
- Equipment performance
- Merchant exposure
- Financing cost
- Grid connectivity
- Storage economics

Separate:

> **Capacity addition**

from:

> **Generation and cash-flow contribution**

A growing renewable MW base is not sufficient without generation, contracted economics, cash flow and returns.

---

# 11. Hydro Power Analysis

Track:

- Installed hydro capacity
- Generation
- Reservoir levels
- Water availability
- PLF
- Tariff
- Seasonal generation
- Project life
- Renovation/modernization capex

Analyze:

- Hydrology risk
- Seasonal variability
- Long-term generation assumptions
- Maintenance requirements
- Generation volatility

---

# 12. Transmission Analysis

For transmission businesses track:

- Transmission capacity
- Network length
- Lines
- Substations
- Availability
- Transmission charges
- Regulated asset base
- New projects
- Capex
- Project commissioning

Key operating metric:

```text
Transmission Availability %
```

Analyze:

- Asset availability
- Network utilization
- Regulatory return
- Regulated asset-base growth
- Capex pipeline
- Commissioning delays

### Transmission Causal Chain

```text
Power Demand
↓
Transmission Requirement
↓
Network Utilization
↓
Availability
↓
Regulated Revenue
↓
Operating Cost
↓
EBITDA
↓
Capex + Interest
↓
CFO
↓
FCF
↓
ROIC
```

Do not compare transmission economics directly with merchant generation without normalization.

---

# 13. Distribution Analysis

Track:

- Customers
- Units sold
- Distribution losses
- AT&C losses
- Collection efficiency
- Billing efficiency
- Tariff
- Average cost of supply
- Average revenue realization
- Subsidy
- Receivables

Calculate:

```text
AT&C Loss =
Technical Loss + Commercial Loss
```

Analyze:

- Loss reduction
- Billing improvement
- Collection improvement
- Tariff recovery
- Subsidy dependence
- Receivable buildup

### Distribution Causal Chain

```text
Customer Demand
↓
Units Sold
↓
Tariff
↓
Billing
↓
Collection
↓
Revenue
↓
AT&C Losses
↓
Operating Margin
↓
CFO
↓
FCF
↓
ROIC
```

---

# 14. Fuel & Input Cost Analysis

Track:

- Coal
- Gas
- Oil
- Biomass
- Electricity purchased
- Water
- Chemicals
- Maintenance
- Employee cost
- Transmission charges
- Distribution costs

Analyze:

- Input cost/unit
- Fuel cost/revenue
- Pass-through mechanism
- Input price volatility

### Key Question

> Can the utility pass input-cost inflation through tariffs or contracts?

---

# 15. EBITDA & Margin Analysis

Track:

- Revenue
- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- PAT
- PAT margin
- EBITDA/MWh
- EBITDA/customer
- EBITDA/asset

Analyze margin drivers:

- Tariff
- Volume
- Fuel
- Utilization
- Fixed-cost absorption
- Regulatory adjustments

The analysis should explain **why margins changed**, not merely report the ratio.

---

# 16. Capex & Capital Intensity

Track:

- Maintenance capex
- Growth capex
- Capacity expansion
- Transmission capex
- Distribution capex
- Renewable capex
- Modernization capex
- Environmental capex

Calculate:

```text
Capex / Revenue
Capex / EBITDA
Capex / MW
```

Separate:

```text
Maintenance Capex
vs
Growth Capex
```

Assess:

> Expected incremental generation/revenue/EBITDA/FCF from incremental capex.

### Capital Allocation Test

```text
Incremental Capex
↓
Incremental Capacity
↓
Incremental Generation / Revenue
↓
Incremental EBITDA
↓
Incremental CFO
↓
Incremental FCF
↓
Incremental ROIC
```

---

# 17. Project Execution Analysis

For new utility projects track:

- Project size
- Project cost
- Planned commissioning
- Actual commissioning
- Cost overruns
- Time overruns
- Financing
- EPC contractor
- PPA status
- Grid connectivity
- Land acquisition
- Regulatory approvals

### Red Flag

> Project cost or completion time repeatedly exceeds initial assumptions.

Compare announced project pipeline with actual commissioning and cash-flow contribution.

---

# 18. Balance Sheet Analysis

Track:

- Gross debt
- Net debt
- Net debt/EBITDA
- Interest expense
- Interest coverage
- Debt maturity
- Refinancing requirements
- Lease liabilities
- Project debt
- Cash
- Restricted cash

Calculate:

```text
Net Debt = Debt - Cash
```

Assess leverage against:

- Contracted cash flows
- Regulated returns
- Asset life
- Interest cost
- Capex pipeline

For highly capital-intensive utilities, analyze debt together with future capex obligations rather than looking only at the current debt ratio.

---

# 19. Cash Flow Analysis

Track:

- CFO
- CFO/PAT
- CFO/EBITDA
- Capex
- FCF
- FCF margin
- Interest paid
- Debt repayment
- Working capital

Calculate:

```text
FCF = CFO - Economically Relevant Capex
```

Distinguish:

- Maintenance FCF
- Growth FCF
- Project-level cash flow

Analyze:

```text
EBITDA
↓
CFO
↓
FCF
↓
Debt Reduction
```

A utility can report strong EBITDA while generating weak FCF because of capex, working capital or interest requirements.

---

# 20. Working Capital & Receivables

Track:

- Trade receivables
- Government receivables
- Regulatory receivables
- Fuel inventory
- Payables
- Contract assets
- Subsidy receivables
- DSO
- DPO
- Cash Conversion Cycle

Calculate:

```text
DSO
DPO
Cash Conversion Cycle
```

### Special Focus

> Regulatory and government receivables can make reported profit materially different from actual cash generation.

Flag:

- Receivables growing faster than revenue
- Government/regulatory receivable concentration
- Collection delays
- Regulatory assets without timely recovery
- CFO deterioration despite accounting-profit growth

---

# 21. Regulatory Analysis

Track relevant authorities, including where applicable:

- CERC
- SERCs
- Ministry of Power
- Ministry of New and Renewable Energy
- Central Electricity Authority
- State electricity regulators
- Environmental regulators

Track:

- Tariff orders
- Regulatory assets
- Regulatory liabilities
- Allowed ROE
- Cost-plus returns
- True-ups
- Subsidies
- Environmental rules
- Renewable obligations
- Open-access rules
- Grid rules
- Transmission charges

For each regulatory event store:

```text
date
regulator
event
affected_company
financial_impact
operational_impact
source
confidence
```

Separate:

> **Confirmed regulatory decision**

from:

> **Proposed policy**

---

# 22. Regulatory Asset Analysis

Track:

- Regulatory assets
- Regulatory liabilities
- Carrying cost
- Recovery period
- Approved recovery
- Pending approval

Investigate:

> Profit recognized today but cash recovery occurring much later.

Do not automatically treat regulatory assets as equivalent to cash.

---

# 23. Renewable Obligation & Policy Analysis

Where relevant track:

- Renewable purchase obligations
- Renewable energy certificates
- Green energy requirements
- Renewable auctions
- Tariff ceilings
- Storage policy
- Open access
- Carbon-related regulations

Assess impact on:

- Demand
- Capex
- Tariffs
- Competitive position
- Project economics

---

# 24. Competitive Advantage

Evaluate by business model.

### Power Generation

- Low-cost generation
- Fuel access
- PPA portfolio
- Project locations
- Scale
- Asset quality
- Operating efficiency

### Transmission

- Network scale
- Strategic corridors
- Regulated asset base
- Execution capabilities
- Project pipeline

### Distribution

- Customer density
- Network efficiency
- Loss reduction
- Collection infrastructure
- Regulatory relationship

### Renewable

- Low-cost financing
- Project pipeline
- Land
- Grid access
- PPA relationships
- Execution
- Operating performance

### Core Rule

> Do not infer a moat solely from installed capacity.

---

# 25. Customer & Counterparty Quality

Track:

- Government customers
- State utilities
- Industrial customers
- Commercial customers
- Distribution companies
- Corporate PPAs
- Counterparty concentration
- Receivable quality
- Payment history

Analyze:

- Counterparty creditworthiness
- Payment delays
- Security mechanisms
- Collection risk
- Offtake quality

For PPAs specifically track:

- Counterparty
- Tariff
- Tenure
- Escalation
- Payment record
- Security
- Offtake
- Termination
- Renegotiation

Flag:

- Weak counterparties
- Delayed payments
- PPA disputes
- Tariff renegotiation

---

# 26. Management & Governance

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

For utilities additionally assess:

- Capex discipline
- Project selection
- Debt management
- Regulatory strategy
- Asset monetization

---

# 27. Management Guidance & Concall Analysis

Extract:

- Capacity addition guidance
- Generation guidance
- PLF guidance
- Tariff expectations
- Fuel availability
- Capex guidance
- Project commissioning
- Renewable pipeline
- Debt reduction
- FCF expectations
- Regulatory developments
- Demand outlook

Compare:

```text
Previous Guidance
vs
Actual Outcome
```

Track management credibility across periods.

### Concall NLP Layer

Use the LLM / embedding infrastructure to extract:

- Demand commentary
- Power-price commentary
- Tariff commentary
- Fuel availability
- Capex
- Project execution
- Debt
- Regulatory developments
- Renewable opportunities
- Collection / receivables
- Margin outlook
- Risks

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

Compare historical management statements with subsequent reported outcomes.

---

# 28. Capital Allocation

Analyze:

- Maintenance capex
- Expansion capex
- Renewable investment
- Acquisitions
- Debt repayment
- Dividends
- Buybacks
- Asset sales
- Infrastructure monetization

Key question:

> Does incremental capital earn returns above the cost of capital over the economic life of the asset?

---

# 29. Return on Capital

Track:

- ROE
- ROCE
- ROIC
- Asset turnover
- Capital turnover
- Incremental ROIC

Analyze:

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

For regulated businesses compare returns with:

- Allowed return
- Cost of capital
- Actual financing cost
- Asset utilization

---

# 30. Cyclicality

Identify exposure to:

- Power demand cycle
- Merchant power price cycle
- Fuel cycle
- Industrial cycle
- Interest-rate cycle
- Capex cycle
- Renewable equipment cycle
- Hydrology
- Weather

Track:

- Peak generation
- Trough generation
- Peak PLF
- Trough PLF
- Peak merchant tariff
- Trough merchant tariff
- Debt through cycle
- FCF through cycle

> Do not extrapolate peak merchant earnings as normalized earnings.

---

# 31. Bad Growth Patterns

Flag evidence of:

### 1. Capacity growth without utilization

Installed MW rises while generation/PLF remains weak.

### 2. EBITDA growth without FCF

Cash is absorbed by capex, working capital or interest.

### 3. Debt-funded expansion without adequate returns

Leverage rises faster than sustainable cash flow.

### 4. Regulatory-profit growth without cash

Profit rises mainly through regulatory assets/receivables.

### 5. Merchant-price dependence

Earnings rely on unusually high spot power prices.

### 6. Project growth without execution

Capex announcements increase but commissioning is delayed.

### 7. Renewable capacity without generation

Capacity grows but CUF/generation underperforms.

### 8. Receivable-led growth

Government/regulatory receivables rise faster than revenue.

### 9. Tariff-led growth without volume

Reported growth depends primarily on tariff increases.

### 10. Underutilized assets

Large asset base produces persistently weak returns.

---

# 32. Causal Analysis Engine

## Generation

```text
Electricity Demand
↓
Power Requirement
↓
Generation
↓
PLF / Utilization
↓
Realized Tariff
↓
Revenue
↓
Fuel + Operating Cost
↓
EBITDA
↓
Interest + Capex
↓
CFO
↓
FCF
↓
ROIC
```

## Transmission

```text
Power Demand
↓
Transmission Requirement
↓
Network Utilization
↓
Availability
↓
Regulated Revenue
↓
Operating Cost
↓
EBITDA
↓
Capex + Interest
↓
CFO
↓
FCF
↓
ROIC
```

## Distribution

```text
Customer Demand
↓
Units Sold
↓
Tariff
↓
Billing
↓
Collection
↓
Revenue
↓
AT&C Losses
↓
Operating Margin
↓
CFO
↓
FCF
↓
ROIC
```

## Renewable

```text
Capacity
↓
CUF
↓
Generation
↓
PPA / Merchant Tariff
↓
Revenue
↓
Operating Cost
↓
EBITDA
↓
Debt Service + Capex
↓
FCF
↓
ROIC
```

---

# 33. Peer Comparison

Compare companies within the correct power utility model.

## Generation

- Installed capacity
- Generation
- PLF
- Tariff
- EBITDA/MWh
- Fuel cost/MWh
- EBITDA margin
- Debt
- Net debt/EBITDA
- Capex
- FCF
- ROCE
- ROIC
- Valuation

## Transmission

- Network capacity
- Availability
- Regulated asset base
- Revenue
- EBITDA margin
- Capex
- Debt
- ROCE
- ROIC
- Valuation

## Distribution

- Customer base
- Units sold
- AT&C losses
- Collection efficiency
- Tariff
- Revenue/customer
- Receivables
- EBITDA
- FCF
- ROIC

## Renewable

- Capacity
- Generation
- CUF
- PPA tariff
- EBITDA
- Debt
- Capex
- FCF
- ROIC
- Valuation

### Normalization Rule

Do not compare regulated transmission economics directly with merchant generation economics without normalization.

---

# 34. Historical Trend Analysis

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
- Capex
- Installed capacity
- Generation
- PLF/CUF
- Tariff
- Customers
- Receivables
- Regulatory assets

Identify:

- Structural growth
- Cyclical recovery
- Capacity inflection
- Utilization inflection
- Tariff-driven growth
- Balance-sheet improvement
- Regulatory changes

---

# 35. Valuation Framework

Valuation must reflect utility type and capital intensity.

## Regulated Utilities

Use:

- P/E
- P/B where appropriate
- EV/EBITDA
- FCF yield
- ROE vs allowed ROE
- Historical multiples

## Generation

Use:

- EV/EBITDA
- P/E
- EV/MW
- FCF yield
- Asset-based valuation where appropriate

Interpret EV/MW with:

- Plant age
- PLF
- Tariff
- Fuel economics
- Contracted vs merchant exposure

## Transmission

Use:

- P/E
- EV/EBITDA
- P/B
- EV/regulatory asset base
- FCF yield

## Renewable

Use:

- EV/EBITDA
- P/E
- EV/MW
- FCF yield
- Project-level DCF
- Asset value

Always compare:

- Current valuation
- Historical valuation
- Peer valuation
- Growth
- ROIC
- Cash flow
- Leverage
- Contract/regulatory durability

No single valuation multiple should be used without understanding the underlying utility model.

---

# 36. Risk Analysis

## Business Risks

- Demand weakness
- Tariff pressure
- Merchant price decline
- Fuel availability
- Fuel price inflation
- Capacity underutilization
- Technology changes

## Regulatory Risks

- Tariff revisions
- Regulatory asset recovery
- Policy changes
- Renewable obligations
- Environmental requirements
- Subsidy changes
- Open-access changes

## Financial Risks

- High leverage
- Refinancing
- Interest-rate increases
- Weak FCF
- High capex
- Receivable buildup

## Project Risks

- Cost overruns
- Time overruns
- Land delays
- Grid connectivity
- PPA delays
- Equipment delays
- Regulatory approvals

## Environmental Risks

- Emission regulations
- Water availability
- Carbon costs
- Environmental permissions
- Stranded-asset risk

---

# 37. Positive Signals

Potential evidence-backed positives:

- Rising demand
- Improving PLF/CUF
- Sustainable tariff improvement
- Strong contracted revenue
- Long-duration PPAs
- High network availability
- Falling AT&C losses
- Improving collections
- Strong capex execution
- Capacity commissioned on time
- Strong FCF
- Debt reduction
- High ROIC
- Low-cost generation
- Strong renewable project pipeline
- Improving asset utilization
- Favorable regulatory outcomes
- Strong counterparty quality

All positives must be supported by reported evidence.

---

# 38. Red Flags

Flag when supported by evidence:

- Falling PLF/CUF
- Capacity additions without demand
- Merchant price dependence
- Fuel cost escalation without pass-through
- PPA disputes
- Weak counterparties
- Rising receivables
- Rising regulatory assets
- Poor collections
- Project delays
- Cost overruns
- High leverage
- Refinancing risk
- FCF deterioration
- Capex without returns
- Environmental liabilities
- Auditor qualifications
- Related-party concerns
- Repeated guidance misses

---

# 39. Scoring Architecture

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

Weights should be configurable by utility type.

### Generation

Emphasize:

- PLF
- Tariff
- Fuel economics
- PPA quality
- FCF
- Leverage

### Transmission

Emphasize:

- Availability
- Regulatory asset base
- Project execution
- Regulated returns
- Debt

### Distribution

Emphasize:

- AT&C losses
- Collection efficiency
- Tariff recovery
- Receivables
- Regulatory support

### Renewable

Emphasize:

- CUF
- PPA quality
- Project execution
- Capex
- Debt
- FCF

A valuation score must not conceal severe leverage, regulatory, execution or cash-flow risks.

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

# 40. Required Data Layer

## Power Generation

Store:

- Installed MW
- Generation
- PLF
- Availability
- Tariff
- PPA
- Fuel
- Heat rate
- Auxiliary consumption
- Capex
- Debt

## Transmission

Store:

- Transmission capacity
- Network length
- Availability
- Regulated asset base
- Tariff
- Capex
- Projects
- Debt

## Distribution

Store:

- Customers
- Units sold
- Tariff
- AT&C losses
- Collection efficiency
- Subsidies
- Receivables

## Renewable

Store:

- Capacity
- Generation
- CUF
- PPA
- Tariff
- Curtailment
- Capex
- Debt

---

# 41. Agent Architecture

Recommended pipeline:

```text
Company Profile Agent
        ↓
Financial Data Agent
        ↓
Business Model Agent
        ↓
Operating Metrics Agent
        ↓
Generation / Network Agent
        ↓
Tariff / PPA Agent
        ↓
Regulatory Agent
        ↓
Project Execution Agent
        ↓
Management / Concall Agent
        ↓
Utilities Analysis Agent
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

The numeric calculation layer must remain deterministic.

The LLM should interpret evidence and explain causal relationships.

---

# 42. Final Screener Output

Every Power company report should contain:

## 1. Company Overview

- Utility type
- Generation/transmission/distribution
- Regulated/merchant
- Renewable/thermal/hydro
- Customer profile
- Geography

## 2. Business Quality

- Asset quality
- Contract quality
- Regulatory position
- Competitive advantage

## 3. Growth Engine

- Demand
- Capacity
- Generation
- Customers
- Tariff
- Project pipeline

## 4. Operating Engine

- PLF/CUF
- Availability
- Utilization
- Fuel efficiency
- Losses
- Collection efficiency
- Unit economics

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
- Interest coverage
- Lease liabilities
- Regulatory liabilities
- Receivables

## 7. Regulatory

- Tariff orders
- Regulatory assets
- Allowed returns
- Policy developments
- Renewable requirements

## 8. Management

- Guidance
- Project execution
- Capital allocation
- Concall evidence

## 9. Valuation

- Current valuation
- Historical valuation
- Peer valuation
- Asset/project valuation where appropriate

## 10. Red Flags

Evidence-backed concerns.

## 11. Positive Signals

Evidence-backed strengths.

## 12. Peer Position

Use the correct utility-model peer group.

## 13. Investment Thesis

Summarize:

- Demand engine
- Capacity/asset engine
- Monetization engine
- Operating engine
- Cash engine
- Capital efficiency
- Balance sheet
- Valuation
- Key risks

## 14. Bull Case

Evidence-based potential drivers.

## 15. Bear Case

Evidence-based downside drivers.

## 16. Thesis Break Conditions

Examples:

- PLF/CUF deterioration
- Tariff deterioration
- Weak demand
- Fuel-cost shock
- PPA disruption
- Project delays
- Capex overruns
- Receivable deterioration
- Regulatory deterioration
- Excess leverage
- FCF deterioration

## 17. Next-Quarter Watchlist

Track:

- Demand
- Generation
- PLF/CUF
- Tariff
- Fuel cost
- Availability
- Receivables
- Capex
- Project commissioning
- EBITDA margin
- CFO
- FCF
- Debt
- Regulatory developments
- Management guidance

---

# 43. Core Implementation Rule

The Power analysis engine must answer:

> **What drives electricity demand, how much useful output is produced from the asset base, how is that output monetized, what fuel/input and regulatory costs determine profitability, how much capital is required, and how much sustainable cash flow remains after maintaining and expanding the asset base?**

The core causal model is:

```text
DEMAND
   ↓
CAPACITY
   ↓
UTILIZATION / PLF / CUF
   ↓
GENERATION / VOLUME
   ↓
TARIFF / PRICE
   ↓
REVENUE
   ↓
FUEL + OPERATING COST
   ↓
EBITDA
   ↓
CAPEX + WORKING CAPITAL + INTEREST
   ↓
CFO
   ↓
FCF
   ↓
DEBT REDUCTION / REINVESTMENT
   ↓
ROIC
   ↓
VALUATION
   ↓
REGULATORY / OPERATING RISK
   ↓
THESIS BREAK
```

### Final Power-Sector Principle

Always separate:

- Regulated vs contracted vs merchant economics
- Generation vs transmission vs distribution
- Thermal vs hydro vs renewable vs nuclear
- Capacity growth vs actual generation
- Generation growth vs monetization
- EBITDA growth vs cash-flow growth
- Project announcements vs commissioned assets
- Accounting profit vs collectible cash
- Capital expenditure vs incremental returns

**Capacity alone is not value creation. Revenue alone is not cash generation. EBITDA alone is not economic return. The final analysis must connect demand, utilization, tariff, costs, capital intensity, cash flow, leverage and ROIC.**
