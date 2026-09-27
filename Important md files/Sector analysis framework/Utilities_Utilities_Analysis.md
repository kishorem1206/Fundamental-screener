# Utilities → Utilities — Fundamental Analysis Framework

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

This standalone framework covers **Utilities → Utilities**, corresponding to the **Other Utilities** classification.

It is designed for businesses that may include:

- Water utilities
- Gas distribution utilities
- Waste management utilities
- Municipal utilities
- Other regulated infrastructure utilities

These businesses should be analyzed as regulated, infrastructure-heavy and often capital-intensive businesses. Generic profitability ratios are not sufficient.

The core economic relationship is:

> **CUSTOMERS / DEMAND → VOLUME / CONSUMPTION → NETWORK UTILIZATION → TARIFF → REVENUE → OPERATING COST → EBITDA → CAPEX → DEBT → CFO → FCF → ROIC**

The framework must adapt to the company's actual utility model and distinguish regulated, contracted and other revenue structures before applying financial ratios or valuation metrics.

---

# 2. Industry Coverage

## 2.1 Water Utilities

Analyze businesses involved in:

- Water supply
- Water distribution
- Water treatment
- Wastewater treatment
- Water infrastructure
- Other regulated water services

Primary drivers:

- Customer base
- Water volume
- Consumption
- Tariff
- Network utilization
- Distribution losses
- Collection efficiency
- Operating cost
- Capex
- Receivables
- Regulation
- Debt
- FCF
- Regulatory returns

---

## 2.2 Gas Distribution Utilities

Analyze businesses involved in:

- Gas distribution
- City gas distribution
- Pipeline-linked distribution infrastructure
- Other regulated gas distribution services

Primary drivers:

- Customer base
- Connections
- Gas volume
- Consumption/customer
- Industrial/commercial/residential mix
- Gas tariff
- Distribution margin
- Network utilization
- Input gas cost
- Operating cost
- Capex
- Receivables
- Regulation
- Debt
- FCF

---

## 2.3 Waste Management Utilities

Analyze businesses involved in:

- Municipal waste services
- Waste collection
- Waste treatment
- Waste processing
- Waste disposal
- Waste-to-value infrastructure where applicable

Primary drivers:

- Customer/service base
- Waste volume
- Collection volume
- Processing volume
- Contract tenure
- Service fees
- Tipping fees
- Recovery/recycling economics
- Operating cost
- Capex
- Contract renewal
- Receivables
- Regulation
- FCF

---

## 2.4 Municipal & Other Regulated Utilities

Depending on classification, analyze:

- Municipal utilities
- Other regulated infrastructure utilities
- Long-term concession utilities
- Network-based essential services

Primary drivers:

- Customer base
- Volume
- Consumption
- Tariff
- Regulation
- Network utilization
- Distribution losses
- Capex
- Operating cost
- Receivables
- Debt
- FCF
- Regulatory returns

---

# 3. Business Model Classification

Classify every company before screening.

Required fields:

```text
Sector
Industry
Sub-industry
Utility type
Regulated / merchant / contracted
Customer type
Geography
Asset intensity
Capital intensity
Tariff mechanism
Contract duration
Regulatory framework
Network model
Volume model
Recurring revenue
```

### Revenue Models

Track the applicable model:

- Regulated tariff
- Cost-plus tariff
- Usage-based tariff
- Connection charges
- Capacity charges
- Service fees
- Contracted service revenue
- Concession revenue
- Gas tariff
- Water tariff
- Waste service fees
- Municipal contract payments
- Other regulated infrastructure revenue

### Core Classification Questions

1. Who is the customer?
2. What physical service is delivered?
3. What is the measurable volume?
4. How is the customer charged?
5. Is pricing regulated, contracted or market-based?
6. What infrastructure is required?
7. Who bears input-cost risk?
8. Who bears volume risk?
9. How long is the contract/concession?
10. How quickly does accounting revenue convert into cash?

---

# 4. Data Periods & Data Quality

Support:

- Annual
- Quarterly
- TTM
- Monthly volume
- Monthly consumption
- Monthly customer additions
- Tariff periods
- Regulatory periods
- Contract/concession periods

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
6. Relevant sector regulator
7. Relevant ministry / government authority
8. Company disclosures
9. Reliable financial databases
10. Third-party research

When sources conflict:

1. Prefer the primary source.
2. Preserve material discrepancies.
3. Flag unresolved differences.
4. Never silently overwrite.

---

# 5. Customer Economics

Track:

- Customer count
- Customer additions
- Customer mix
- Consumption/customer
- Revenue/customer
- Tariff/customer
- Collection rate
- Churn where relevant

Analyze customer categories separately where material:

- Residential
- Commercial
- Industrial
- Government
- Municipal
- Institutional

### Core Revenue Formula

For volume-based utilities:

```text
Revenue =
Customers × Consumption × Tariff
```

For service-contract models:

```text
Revenue =
Contracted Volume × Service Fee
```

or where appropriate:

```text
Revenue =
Customers / Contracts × Applicable Service Charge
```

Analyze:

- Customer growth
- Volume growth
- Consumption/customer
- Tariff movement
- Customer mix
- Collection
- Revenue/customer

### Important Distinction

Revenue growth can come from:

- More customers
- Higher consumption
- Higher tariff
- Better customer mix
- New contracts
- Regulatory adjustments

The engine must identify which factor actually caused growth.

---

# 6. Volume & Consumption Analysis

Track:

- Total volume
- Volume growth
- Volume/customer
- Consumption/customer
- Industrial volume
- Commercial volume
- Residential volume
- Government/municipal volume
- Peak demand where relevant
- Seasonal volume

Analyze:

```text
Customer Growth
vs
Volume Growth
vs
Revenue Growth
```

Identify whether volume growth is:

- Structural
- Cyclical
- Weather-driven
- Industrial-cycle driven
- Policy-driven
- Contract-driven

### Unit Economics

Calculate where data permits:

```text
Revenue / Unit Volume
Operating Cost / Unit Volume
EBITDA / Unit Volume
CFO / Unit Volume
```

For network businesses also track:

```text
Volume / Network Asset
Revenue / Network Asset
```

---

# 7. Tariff & Pricing Analysis

Track:

- Approved tariff
- Realized tariff
- Average tariff
- Customer-segment tariff
- Tariff escalation
- Regulatory adjustments
- Pass-through mechanism
- Connection charges
- Service fees

Decompose:

```text
Revenue =
Volume × Realized Tariff
```

Analyze:

- Tariff increases
- Tariff reductions
- Regulatory true-ups
- Pass-through
- Competitive pressure
- Customer affordability
- Contract repricing

### Core Question

> Is revenue growth being driven by sustainable volume/customer expansion or primarily by tariff increases?

---

# 8. Regulation Analysis

Track applicable regulators and authorities.

Depending on the utility, this may include:

- Sector regulators
- State regulators
- Municipal authorities
- Local authorities
- Environmental regulators
- Government departments

Track:

- Tariff orders
- Allowed returns
- Cost-plus mechanisms
- Regulatory assets
- Regulatory liabilities
- True-ups
- Subsidies
- Environmental rules
- Service standards
- Licensing
- Concession terms
- Open-access requirements where applicable

For every material event store:

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

# 9. Regulatory Asset & Receivable Analysis

Track:

- Regulatory assets
- Regulatory liabilities
- Government receivables
- Regulatory receivables
- Subsidy receivables
- Carrying cost
- Recovery period
- Approved recovery
- Pending approval

Investigate:

> Profit recognized today but cash recovery occurring much later.

Do not automatically treat regulatory assets as equivalent to cash.

### Receivable Quality

Analyze:

- Receivables/revenue
- DSO
- Government receivables
- Regulatory receivables
- Collection history
- Ageing
- Provisioning
- Cash conversion

---

# 10. Network & Infrastructure Analysis

Track where applicable:

- Network length
- Pipeline length
- Distribution network
- Treatment capacity
- Processing capacity
- Storage capacity
- Connections
- Installed capacity
- Network utilization
- Asset availability
- Distribution losses
- Capacity additions

Analyze:

- Capacity growth
- Volume growth
- Utilization
- Availability
- Asset productivity
- Network expansion
- Maintenance requirements

### Critical Rule

> Do not treat infrastructure expansion as value creation unless volume, utilization, tariffs, cash flow and returns support the investment.

---

# 11. Distribution Loss Analysis

For network utilities track:

- Technical losses
- Commercial losses
- Distribution losses
- Billing efficiency
- Collection efficiency
- Leakage where applicable

Where the framework permits:

```text
Distribution Loss =
Technical Loss + Commercial Loss
```

Analyze:

- Loss reduction
- Billing improvement
- Collection improvement
- Tariff recovery
- Network efficiency

### Why It Matters

A utility may increase its network and customer base while losing economic value through:

- Physical leakage
- Unbilled consumption
- Poor collections
- Subsidy dependence
- Weak tariff recovery

---

# 12. Gas Distribution Analysis

For gas-distribution businesses track:

- PNG connections
- CNG stations/connections where applicable
- Industrial customers
- Commercial customers
- Residential customers
- Gas volume
- Volume/customer
- Network length
- Network utilization
- Gas procurement cost
- Realized gas margin
- Tariff
- Capex

Analyze:

```text
Customers
↓
Gas Volume
↓
Network Utilization
↓
Realized Margin
↓
Revenue
↓
Operating Cost
↓
EBITDA
↓
CFO
↓
FCF
```

Track exposure to:

- Gas procurement cost
- Volume growth
- Customer mix
- Alternative fuels
- Network expansion
- Regulatory changes

---

# 13. Water Utility Analysis

Track:

- Customers/connections
- Water supplied
- Water billed
- Water consumption
- Per-capita/consumer consumption where relevant
- Network length
- Treatment capacity
- Distribution losses
- Non-revenue water where disclosed
- Collection efficiency
- Tariff
- Revenue/customer
- Capex

Analyze:

```text
Water Supplied
↓
Water Delivered
↓
Water Billed
↓
Tariff
↓
Revenue
↓
Collection
↓
CFO
↓
FCF
```

Investigate the gap between:

- Water produced/supplied
- Water delivered
- Water billed
- Cash collected

---

# 14. Waste Utility Analysis

Track:

- Waste volume collected
- Waste volume processed
- Processing capacity
- Collection coverage
- Contracted volume
- Service fee
- Tipping fee
- Recovery/recycling revenue
- Contract duration
- Contract renewals
- Operating cost
- Capex

Analyze:

```text
Waste Volume
↓
Collection
↓
Processing
↓
Service Fee / Recovery Value
↓
Revenue
↓
Operating Cost
↓
EBITDA
↓
Capex
↓
CFO
↓
FCF
```

### Contract Quality

Assess:

- Contract tenure
- Counterparty
- Minimum volume
- Pricing mechanism
- Escalation
- Renewal
- Termination
- Payment history

---

# 15. Input Cost Analysis

Track relevant costs:

- Gas
- Electricity purchased
- Water
- Chemicals
- Fuel
- Maintenance
- Employee cost
- Transportation
- Treatment cost
- Waste processing cost
- Network maintenance
- Other operating inputs

Analyze:

- Input cost/unit
- Input cost/revenue
- Cost inflation
- Pass-through mechanism
- Contractual protection
- Operating efficiency

### Key Question

> Can the utility pass input-cost inflation through tariffs or contracts?

---

# 16. EBITDA & Margin Analysis

Track:

- Revenue
- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- PAT
- PAT margin
- EBITDA/customer
- EBITDA/unit volume
- EBITDA/asset

Analyze margin drivers:

- Customer growth
- Volume
- Tariff
- Input costs
- Network utilization
- Fixed-cost absorption
- Regulatory adjustments
- Contract mix

The analysis should explain **why margins changed**, not simply report the ratio.

---

# 17. Capex & Capital Intensity

Track:

- Maintenance capex
- Growth capex
- Network expansion
- Capacity expansion
- Treatment infrastructure
- Pipeline/network capex
- Modernization capex
- Environmental capex

Calculate:

```text
Capex / Revenue
Capex / EBITDA
Capex / Customer
Capex / Unit Capacity
```

Separate:

```text
Maintenance Capex
vs
Growth Capex
```

Assess:

> Expected incremental customers / volume / revenue / EBITDA / FCF from incremental capex.

### Capital Allocation Chain

```text
Incremental Capex
↓
Incremental Network / Capacity
↓
Incremental Customers / Volume
↓
Incremental Revenue
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

# 18. Project & Contract Execution

For new projects, concessions or contracts track:

- Project/contract size
- Contract value
- Project cost
- Planned completion
- Actual completion
- Cost overruns
- Time overruns
- Financing
- EPC contractor
- Regulatory approvals
- Land requirements
- Network connectivity
- Customer/offtake status
- Contract status

### Red Flag

> Project cost or completion time repeatedly exceeds initial assumptions.

For concessions/contracts also track:

- Award date
- Start date
- Tenure
- Revenue mechanism
- Escalation
- Renewal
- Termination
- Counterparty
- Payment security

---

# 19. Balance Sheet Analysis

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
- Customer/volume stability

---

# 20. Cash Flow Analysis

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
Debt Reduction / Reinvestment
```

### Cash Conversion Test

A strong utility analysis must determine whether:

- Accounting revenue becomes receivables or cash
- EBITDA becomes CFO
- CFO remains after maintenance capex
- Growth capex is funded sustainably
- FCF supports debt reduction or reinvestment

---

# 21. Working Capital

Track:

- Trade receivables
- Government receivables
- Regulatory receivables
- Subsidy receivables
- Inventory where relevant
- Payables
- Contract assets
- Contract liabilities
- DSO
- DPO
- Cash Conversion Cycle

Calculate:

```text
DSO
DPO
Cash Conversion Cycle
```

Special focus:

> Government and regulatory receivables can make reported profit materially different from actual cash generation.

Flag:

- Receivables rising faster than revenue
- Collection deterioration
- Ageing receivables
- Regulatory recovery delays
- CFO deterioration
- Profit growth without cash growth

---

# 22. Customer & Counterparty Quality

Track:

- Government customers
- Municipal customers
- Industrial customers
- Commercial customers
- Residential customers
- State entities
- Corporate customers
- Counterparty concentration
- Payment history

Analyze:

- Counterparty creditworthiness
- Payment delays
- Security mechanisms
- Collection risk
- Contract quality
- Customer concentration

---

# 23. Competitive Advantage

Evaluate according to utility type.

## Water

- Network density
- Treatment infrastructure
- Customer base
- Cost efficiency
- Regulatory position
- Long-duration contracts
- Collection infrastructure

## Gas Distribution

- Network footprint
- Customer connections
- Network utilization
- Geographic exclusivity where applicable
- Procurement capability
- Cost position
- Customer density

## Waste

- Contract portfolio
- Processing infrastructure
- Collection network
- Operating efficiency
- Municipal relationships
- Contract tenure
- Execution capability

## Other Regulated Infrastructure

- Network scale
- Customer density
- Asset quality
- Regulatory position
- Contract/concession durability
- Execution capability

### Core Rule

> Do not infer a moat solely from asset size or network length.

---

# 24. Management & Governance

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
- Contract selection
- Debt management
- Regulatory strategy
- Asset monetization

---

# 25. Management Guidance & Concall Analysis

Extract:

- Customer growth guidance
- Volume guidance
- Tariff expectations
- Network expansion
- Capex guidance
- Project commissioning
- Contract wins
- Contract renewals
- Debt reduction
- FCF expectations
- Regulatory developments
- Demand outlook
- Margin outlook
- Input-cost expectations

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
- Volume commentary
- Tariff commentary
- Customer additions
- Input costs
- Capex
- Project execution
- Contract pipeline
- Debt
- Regulatory developments
- Collections / receivables
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

# 26. Regulatory Asset & Contract Durability

For regulated or contracted utilities assess:

- Tariff durability
- Contract duration
- Escalation
- Cost pass-through
- Allowed returns
- Regulatory review frequency
- Repricing risk
- Renewal risk
- Termination risk
- Counterparty quality

Separate:

> Structural recurring revenue

from:

> Temporary regulatory or contractual revenue.

---

# 27. Return on Capital

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

### Incremental Return Test

```text
Incremental Revenue
+
Incremental EBITDA
+
Incremental FCF
+
Incremental ROIC
```

should be assessed against:

```text
Incremental Capital Deployed
```

---

# 28. Cyclicality

Identify exposure to:

- Customer demand cycle
- Industrial cycle
- Weather
- Commodity/input-cost cycle
- Interest-rate cycle
- Capex cycle
- Construction/property cycle where relevant
- Regulatory cycle

Track through the cycle:

- Peak volume
- Trough volume
- Peak utilization
- Trough utilization
- Tariff changes
- Input costs
- Debt
- FCF

Do not treat temporary volume, pricing or margin spikes as normalized economics without evidence.

---

# 29. Bad Growth Patterns

Flag:

### 1. Customer growth without volume

Customer base rises while consumption remains weak.

### 2. Volume growth without cash

Revenue rises but receivables and working capital absorb cash.

### 3. Tariff-led growth without volume

Growth depends mainly on tariff increases.

### 4. Network expansion without utilization

Infrastructure expands while asset productivity remains weak.

### 5. EBITDA growth without FCF

Cash is absorbed by capex, working capital or interest.

### 6. Debt-funded expansion without adequate returns

Leverage rises faster than sustainable cash flow.

### 7. Regulatory-profit growth without cash

Profit rises through regulatory assets/receivables without timely recovery.

### 8. Receivable-led growth

Government/regulatory receivables rise faster than revenue.

### 9. Contract growth without execution

Contract awards increase but execution, commissioning or collections lag.

### 10. Capacity growth without demand

Installed/treatment/network capacity rises without corresponding customer or volume growth.

### 11. Underutilized assets

Large infrastructure base produces persistently weak returns.

### 12. Input-cost inflation without pass-through

Operating costs rise faster than tariffs/contracts can absorb.

---

# 30. Causal Analysis Engine

## Generic Utility

```text
Customer Demand
↓
Customers / Connections
↓
Consumption / Volume
↓
Network Utilization
↓
Tariff / Service Fee
↓
Revenue
↓
Operating Cost
↓
EBITDA
↓
Working Capital + Capex + Interest
↓
CFO
↓
FCF
↓
ROIC
```

## Water

```text
Customers
↓
Water Supplied
↓
Water Delivered
↓
Water Billed
↓
Tariff
↓
Revenue
↓
Collection
↓
CFO
↓
FCF
↓
ROIC
```

## Gas Distribution

```text
Connections
↓
Gas Volume
↓
Network Utilization
↓
Realized Margin
↓
Revenue
↓
Operating Cost
↓
EBITDA
↓
CFO
↓
FCF
↓
ROIC
```

## Waste

```text
Waste Volume
↓
Collection
↓
Processing
↓
Service Fee / Recovery Value
↓
Revenue
↓
Operating Cost
↓
EBITDA
↓
Capex + Working Capital
↓
CFO
↓
FCF
↓
ROIC
```

---

# 31. Peer Comparison

Compare companies within the correct utility model.

## Water

- Customer base
- Volume
- Volume/customer
- Tariff
- Revenue/customer
- Network utilization
- Distribution losses
- Collection efficiency
- EBITDA margin
- Capex
- FCF
- Debt
- ROCE
- ROIC
- Valuation

## Gas Distribution

- Connections
- Gas volume
- Volume/customer
- Network length
- Network utilization
- Realized margin
- EBITDA
- Capex
- Debt
- FCF
- ROIC
- Valuation

## Waste

- Waste volume
- Collection volume
- Processing capacity
- Utilization
- Contracted volume
- Service fee
- Contract tenure
- EBITDA margin
- Capex
- Receivables
- FCF
- ROIC
- Valuation

## Other Regulated Utilities

- Customers
- Volume
- Tariff
- Network utilization
- Losses
- Collection efficiency
- Revenue/customer
- EBITDA
- Receivables
- FCF
- Debt
- ROIC
- Valuation

### Normalization Rule

Do not compare fundamentally different utility models without normalizing:

- Regulation
- Contract structure
- Asset intensity
- Growth stage
- Capital intensity
- Leverage
- Cash-flow profile

---

# 32. Historical Trend Analysis

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
- Customers
- Volume
- Consumption
- Tariff
- Network capacity
- Network utilization
- Receivables
- Regulatory assets

Identify:

- Structural growth
- Cyclical recovery
- Customer inflection
- Volume inflection
- Utilization inflection
- Tariff-driven growth
- Balance-sheet improvement
- Regulatory changes

---

# 33. Valuation Framework

Valuation should reflect utility type, regulation, capital intensity and cash-flow durability.

## Regulated Utilities

Use:

- P/E
- P/B where appropriate
- EV/EBITDA
- FCF yield
- ROE vs allowed ROE
- Historical multiples

## Network Utilities

Use:

- P/E
- EV/EBITDA
- P/B
- EV/network or asset base where appropriate
- FCF yield

Interpret asset-based metrics with:

- Asset age
- Utilization
- Tariff
- Regulatory return
- Capex requirements
- Cash generation

## Contracted Utilities

Use:

- P/E
- EV/EBITDA
- FCF yield
- DCF
- Historical multiples
- Contract/project valuation where appropriate

Interpret with:

- Contract tenure
- Escalation
- Counterparty
- Renewal risk
- Capex
- Debt
- FCF

Always compare:

- Current valuation
- Historical valuation
- Peer valuation
- Growth
- ROIC
- Cash flow
- Leverage
- Contract/regulatory durability

No universal valuation threshold should be applied across all Other Utilities businesses.

---

# 34. Risk Analysis

## Business Risks

- Demand weakness
- Volume decline
- Tariff pressure
- Customer affordability
- Network underutilization
- Input-cost inflation
- Contract loss
- Contract renewal risk

## Regulatory Risks

- Tariff revisions
- Regulatory asset recovery
- Policy changes
- Subsidy changes
- Licensing changes
- Environmental requirements
- Service-level requirements

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
- Infrastructure delays
- Regulatory approvals
- Contractor delays
- Customer/offtake delays

## Environmental Risks

- Water availability
- Pollution requirements
- Waste-treatment compliance
- Environmental permissions
- Carbon-related regulation
- Remediation liabilities

---

# 35. Positive Signals

Potential evidence-backed positives:

- Rising customer base
- Sustainable volume growth
- Improving network utilization
- Sustainable tariff improvement
- Strong recurring revenue
- Long-duration contracts
- Improving collection efficiency
- Falling distribution losses
- Strong capex execution
- Projects commissioned on time
- Strong FCF
- Debt reduction
- High ROIC
- Strong customer retention
- High-quality counterparties
- Favorable regulatory outcomes
- Improving asset productivity
- Strong contract pipeline

All positives must be supported by reported evidence.

---

# 36. Red Flags

Flag when supported by evidence:

- Falling volume
- Customer growth without consumption
- Network expansion without utilization
- Tariff growth without volume
- Input-cost escalation without pass-through
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
- Contract-renewal weakness

---

# 37. Scoring Architecture

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

### Water

Emphasize:

- Customer growth
- Volume
- Utilization
- Tariff
- Collection
- Capex
- FCF
- Regulatory returns

### Gas Distribution

Emphasize:

- Connections
- Volume
- Network utilization
- Margin
- Procurement economics
- Capex
- FCF
- Leverage

### Waste

Emphasize:

- Contract quality
- Volume
- Utilization
- Service fee
- Execution
- Capex
- Receivables
- FCF

### Other Regulated Utilities

Emphasize:

- Customer/volume growth
- Utilization
- Tariff
- Regulatory support
- Collections
- Capex
- FCF
- ROIC

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

# 38. Required Data Layer

## Customer

Store:

- Customer count
- Customer additions
- Customer mix
- Consumption/customer
- Revenue/customer
- Collection rate

## Volume

Store:

- Total volume
- Volume growth
- Volume/customer
- Segment volume
- Capacity
- Utilization

## Tariff

Store:

- Approved tariff
- Realized tariff
- Tariff escalation
- Regulatory adjustments
- Pass-through

## Network / Infrastructure

Store:

- Network length
- Capacity
- Utilization
- Connections
- Availability
- Distribution losses
- Capex

## Financial

Store:

- Revenue
- EBITDA
- PAT
- CFO
- FCF
- Debt
- Interest
- Receivables
- Working capital
- ROCE
- ROIC

## Contract / Regulatory

Store:

- Contract
- Counterparty
- Tenure
- Tariff/service fee
- Escalation
- Renewal
- Regulatory event
- Regulatory asset/liability

---

# 39. Agent Architecture

Recommended pipeline:

```text
Company Profile Agent
        ↓
Financial Data Agent
        ↓
Business Model Agent
        ↓
Customer / Volume Agent
        ↓
Network / Capacity Agent
        ↓
Tariff / Contract Agent
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

# 40. Final Screener Output

Every **Utilities → Utilities** company report should contain:

## 1. Company Overview

- Utility type
- Water / gas / waste / municipal / other
- Regulated / contracted / other
- Customer profile
- Geography
- Asset/network model

## 2. Business Quality

- Asset quality
- Contract quality
- Regulatory position
- Competitive advantage

## 3. Growth Engine

- Customers
- Volume
- Consumption
- Network/capacity
- Tariff
- Project/contract pipeline

## 4. Operating Engine

- Utilization
- Volume/customer
- Network efficiency
- Distribution losses
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
- Receivables
- Regulatory assets/liabilities

## 7. Regulatory

- Tariff orders
- Regulatory assets
- Allowed returns
- Policy developments
- Licensing/concession developments
- Environmental requirements

## 8. Management

- Guidance
- Project/contract execution
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
- Customer engine
- Volume engine
- Network/asset engine
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

- Customer decline
- Volume deterioration
- Utilization deterioration
- Tariff deterioration
- Input-cost shock
- Contract disruption
- Project delays
- Capex overruns
- Receivable deterioration
- Regulatory deterioration
- Excess leverage
- FCF deterioration

## 17. Next-Quarter Watchlist

Track:

- Customer additions
- Volume
- Consumption
- Utilization
- Tariff
- Input costs
- Network expansion
- Receivables
- Capex
- Project/contract commissioning
- EBITDA margin
- CFO
- FCF
- Debt
- Regulatory developments
- Management guidance

---

# 41. Core Implementation Rule

The **Utilities → Utilities** analysis engine must answer:

> **What drives customers and demand, how much useful service is delivered through the infrastructure, how is that service monetized, what operating and regulatory costs determine profitability, how much capital is required, and how much sustainable cash flow remains after maintaining and expanding the asset base?**

The core causal model is:

```text
CUSTOMERS / DEMAND
        ↓
VOLUME / CONSUMPTION
        ↓
NETWORK UTILIZATION
        ↓
TARIFF / SERVICE FEE
        ↓
REVENUE
        ↓
OPERATING COST
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

### Final Utilities → Utilities Principle

Always separate:

- Water vs gas distribution vs waste vs other regulated utilities
- Regulated vs contracted vs other economics
- Customer growth vs volume growth
- Volume growth vs tariff growth
- Network expansion vs utilization
- EBITDA growth vs cash-flow growth
- Accounting profit vs collectible cash
- Contract awards vs actual execution
- Capex vs incremental returns
- Asset scale vs economic advantage

**Customer growth alone is not value creation. Volume growth alone is not cash generation. Infrastructure expansion alone is not a return. The final analysis must connect customers, volume, utilization, tariff, operating costs, regulation, capital intensity, cash flow, leverage and ROIC.**
