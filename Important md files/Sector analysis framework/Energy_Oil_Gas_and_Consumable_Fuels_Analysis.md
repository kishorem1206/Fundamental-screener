# Energy → Oil, Gas & Consumable Fuels — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

> **Classification**
> - **Macro Sector:** Energy
> - **Sector Value:** Oil, Gas & Consumable Fuels
> - **Industries:** Consumable Fuels; Petroleum Products; Oil; Gas

This is the standalone implementation framework for the **Energy → Oil, Gas & Consumable Fuels** sector value. It covers all four industries in this classification and retains the sector-specific operating, financial, cycle, valuation, data-quality, and agent architecture required by the Fundamental Analysis Screener.

# 2. Core Analytical Philosophy

Energy businesses can be highly sensitive to:

- Crude oil prices
- Natural gas prices
- Product cracks
- Refining margins
- Production volumes
- Reserves
- Government policy
- Subsidies
- Taxes
- Currency
- Freight
- Interest rates
- Environmental regulation
- Capital intensity

Therefore, the engine must first classify the business before applying financial metrics.

For every company identify:

1. Value-chain position
2. Primary energy commodity
3. Upstream/midstream/downstream exposure
4. Domestic/export exposure
5. Regulated vs market-linked pricing
6. Production capacity
7. Reserves/resources
8. Utilization
9. Realized price
10. Input/feedstock cost
11. Unit economics
12. Commodity-price sensitivity
13. Capital intensity
14. Working-capital intensity
15. Balance-sheet strength
16. Competitive advantage
17. Management quality
18. Capital allocation
19. Normalized earnings
20. Current position in the energy cycle

---

# 3. Business-Model Classification

## 3.1 Consumable Fuels

Classify:

- Coal mining
- Thermal coal
- Coking coal
- Lignite
- Biomass/alternative fuels
- Fuel distribution
- Integrated fuel businesses

Track:

- Production
- Sales
- Realization
- Cost/tonne
- Reserves
- Mine life
- Quality/grade
- Logistics
- Domestic/export exposure

---

## 3.2 Petroleum Products

Classify:

- Refining
- Marketing
- Integrated refining & marketing
- Lubricants
- Petrochemical-linked refining
- Fuel retail
- Aviation fuel
- Specialty petroleum products

Track:

- Refinery throughput
- GRM
- Product cracks
- Utilization
- Domestic sales
- Export sales
- Retail outlets
- Marketing margins
- Product mix

---

## 3.3 Oil

Classify:

- Exploration & production
- Integrated oil company
- Crude producer
- Oilfield services where classified within the group
- Oil transportation/storage where applicable

Track:

- Production
- Reserves
- Reserve replacement
- Realized crude price
- Lifting cost
- Finding & development cost
- Recovery rate
- Production decline
- Reserve life

---

## 3.4 Gas

Classify:

- Natural gas production
- Gas transmission
- Gas distribution
- LNG
- Gas marketing
- Integrated gas company

Track:

- Gas production
- Sales volume
- Realization
- LNG volumes
- Transmission volume
- Pipeline utilization
- Distribution volume
- Customer mix
- Contracted vs spot exposure

---

# 4. Common Financial Dataset

Collect annual, quarterly and TTM data wherever available.

## Market Data

- Market capitalization
- Enterprise value
- Share price
- Shares outstanding
- Free float
- Promoter holding
- Promoter pledge
- Institutional ownership
- Dividend yield
- Historical P/E
- Historical EV/EBITDA
- Historical P/B
- Historical EV/Sales
- FCF yield

## Income Statement

- Revenue
- Revenue growth
- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- PBT
- PAT
- EPS
- EPS growth
- Other income
- Exceptional items
- Finance cost
- Depreciation
- Tax rate

Always separate:

**Core operating revenue vs other income**

and:

**Recurring operating earnings vs exceptional/cycle-driven gains.**

## Balance Sheet

- Cash
- Investments
- Gross debt
- Net debt
- Equity
- Net worth
- Goodwill
- Intangibles
- Receivables
- Inventory
- Payables
- PPE
- CWIP
- Lease liabilities
- Provisions
- Contingent liabilities

## Cash Flow

- CFO
- Capex
- CFI
- CFF
- Free cash flow
- CFO/PAT
- FCF/PAT
- FCF margin
- Dividends
- Buybacks
- Debt repayment
- Debt raised

---

# 5. Energy Price & Cycle Analysis

Track relevant benchmark prices:

- Brent crude
- WTI where relevant
- Natural gas
- LNG
- Coal
- Relevant petroleum products
- Fuel prices
- Electricity/input prices where relevant

For each benchmark calculate:

- Current price
- 1Y change
- 3Y average
- 5Y average
- 10Y average where available
- Historical percentile
- Peak
- Trough
- Normalized/mid-cycle price

Classify:

- Downcycle
- Recovery
- Mid-cycle
- Late-cycle
- Peak
- Correction

Do not value an energy company solely on peak-cycle earnings.

---

# 6. Price-Volume-Mix Analysis

Decompose revenue growth into:

**Volume + Realization/Price + Product Mix + Currency + Acquisitions**

Track:

- Production volume
- Sales volume
- Throughput
- Realized price
- ASP
- Product mix
- Export mix
- Domestic mix

Where possible calculate:

**Realized Price = Relevant Revenue / Relevant Volume**

Compare company realization with the appropriate benchmark.

---

# 7. Unit Economics

Every energy sub-industry should have unit economics.

Examples:

### Upstream

- Realized price/barrel
- Lifting cost/barrel
- Finding cost
- EBITDA/barrel

### Refining

- GRM/barrel
- Conversion cost/barrel
- Operating cost/barrel

### Coal

- Realization/tonne
- Cost/tonne
- EBITDA/tonne

### Gas

- Realization/MMBtu or appropriate unit
- Transmission tariff
- Distribution margin
- EBITDA/unit

Core relationship:

**Realization − Cash Cost = Unit Contribution**

---

# 8. Industry Framework — Oil Exploration & Production

## Production

Track:

- Crude production
- Gas production
- Daily production
- Production growth
- Production decline
- Working interest
- Field contribution

## Reserves

Track:

- Proven reserves
- Probable reserves
- Resources
- Reserve replacement ratio
- Reserve life
- Production/reserves
- Reserve additions

Calculate:

**Reserve Life = Reserves / Annual Production**

## Economics

Track:

- Realized crude price
- Lifting cost
- Royalty
- Taxes
- Finding & development cost
- Development capex
- EBITDA/barrel
- FCF/barrel

Analyze:

**Oil Price → Realization → Production → Lifting Cost → EBITDA → CFO → Development Capex → FCF**

## Key Risks

- Production decline
- Reserve depletion
- Exploration failure
- Regulatory restrictions
- Higher development cost
- Commodity-price decline
- Project delays

---

# 9. Industry Framework — Refining

## Core Metrics

Track:

- Refinery throughput
- Capacity
- Utilization
- GRM
- Product yield
- Product cracks
- Crude mix
- Complexity
- Nelson complexity where available
- Energy intensity

## Refining Margin

Analyze:

**Product Basket Value − Crude Cost − Operating Cost = Refining Margin**

Track:

- GRM/barrel
- Benchmark GRM
- Company GRM
- Historical GRM

Determine whether superior margins are caused by:

- Better complexity
- Feedstock advantage
- Product mix
- Temporary cracks
- Location/logistics
- Operational efficiency

## Integration

Assess:

- Upstream crude integration
- Petrochemical integration
- Marketing network
- Storage
- Logistics

---

# 10. Industry Framework — Petroleum Marketing

Track:

- Sales volume
- Retail outlets
- Throughput/outlet
- Market share
- Dealer network
- Product mix
- Retail/industrial sales
- Aviation fuel
- Lubricants
- Marketing margin
- Inventory gains/losses

Separate:

**Core marketing margin vs inventory valuation effects**

Analyze:

**Sales Volume → Marketing Margin → EBITDA → CFO**

Flag reported profit increases caused primarily by inventory gains.

---

# 11. Industry Framework — Coal & Consumable Fuels

Track:

- Production
- Sales
- Dispatch
- Realization/tonne
- Grade
- Quality
- Capacity
- Mine life
- Stripping ratio where relevant
- Cash cost/tonne
- Logistics cost
- Freight

Analyze:

**Benchmark Coal Price → Realization → Volume → Cost/tonne → EBITDA/tonne → CFO → FCF**

For mining businesses also track:

- Reserves
- Resources
- Depletion
- New mines
- Mine approvals
- Rehabilitation obligations

---

# 12. Industry Framework — Natural Gas

Track:

- Production
- Sales volume
- Realization
- LNG imports
- Pipeline throughput
- Capacity
- Utilization
- Transmission volume
- Distribution volume

Separate:

- Long-term contracted gas
- Spot gas
- Domestic gas
- Imported gas
- Regulated gas
- Market-linked gas

Analyze:

**Gas Price → Volume → Realization → Transmission/Distribution Margin → EBITDA → CFO**

---

# 13. Industry Framework — Gas Transmission

Track:

- Pipeline length
- Transmission capacity
- Utilization
- Volume transported
- Tariff
- Contract duration
- Customer concentration
- Regulated return where applicable
- Expansion capex

Analyze:

**Capacity → Utilization → Volume → Tariff → Revenue → EBITDA → CFO → ROIC**

Key risks:

- Underutilization
- Competing pipelines
- Regulatory tariff changes
- Large expansion capex
- Customer concentration

---

# 14. Industry Framework — Gas Distribution

Track:

- Volume
- Customer connections
- Industrial customers
- Commercial customers
- Domestic customers
- CNG volume
- PNG volume
- Distribution network
- CNG stations
- Market share

Calculate:

- Volume/customer
- Revenue/unit
- EBITDA/unit
- Customer additions
- Network utilization

Analyze:

**Customer Addition → Volume → Margin/unit → EBITDA → CFO → ROIC**

---

# 15. Industry Framework — LNG

Track:

- LNG volumes
- Regasification capacity
- Utilization
- Contracted capacity
- Spot exposure
- LNG realization
- Gasification tariff
- Shipping/logistics
- Storage

Separate:

- Long-term contracted volumes
- Spot volumes
- Trading activity

Flag earnings dependent on volatile spot-market spreads.

---

# 16. Industry Framework — Integrated Energy Companies

For vertically integrated companies, analyze each layer separately:

**Upstream → Refining → Petrochemicals → Marketing → Gas → Renewables/Other Energy**

Measure:

- Segment revenue
- Segment EBITDA
- Segment EBIT
- Capital employed
- Capex
- ROCE
- FCF

Then analyze portfolio-level integration benefits:

- Feedstock security
- Logistics
- Product placement
- Marketing
- Shared infrastructure
- Working-capital benefits

Do not automatically assume integration creates value; quantify the benefit where possible.

---

# 17. Petrochemical Exposure

Where an energy company has significant petrochemical operations, track:

- Production
- Sales volume
- Realization
- Feedstock cost
- Product spreads
- Capacity
- Utilization
- EBITDA/tonne
- Polymer/aromatic margins where relevant

Analyze:

**Feedstock → Petrochemical Price → Spread → Volume → EBITDA → FCF**

Separate petrochemical-cycle effects from core energy economics.

---

# 18. Working Capital Analysis

Track:

- Receivable days
- Inventory days
- Payable days
- Cash conversion cycle
- Crude inventory
- Product inventory
- Trading inventory
- Subsidy/regulated receivables
- Dealer receivables

Important:

Commodity-price increases can inflate inventory and receivables without representing volume growth.

Analyze:

**Energy Price → Inventory Value → Working Capital → Borrowing → Interest → CFO**

Flag:

- Inventory buildup
- Receivables rising faster than sales
- Persistent negative CFO
- Working-capital debt
- Large regulated/subsidy receivables
- Trading-related working-capital spikes

---

# 19. Capex Analysis

Track:

- Maintenance capex
- Growth capex
- Exploration capex
- Development capex
- Refinery capex
- Pipeline capex
- LNG capex
- Distribution network capex
- Capex/revenue
- Capex/depreciation
- CWIP

Evaluate:

**Capex → Capacity → Utilization → Volume → Revenue → EBITDA → CFO → FCF → ROIC**

For major projects track:

- Initial cost
- Revised cost
- Start date
- Revised completion date
- Expected capacity
- Expected utilization
- Expected return
- Actual post-completion economics

Flag cost overruns and repeated delays.

---

# 20. Cash Flow Quality

Calculate:

- CFO/PAT
- CFO/EBITDA
- FCF/PAT
- FCF margin
- FCF yield
- Cash conversion
- Maintenance-capex-adjusted FCF

Separate:

- Sustainable CFO
- Working-capital release
- Inventory gains
- Asset sales
- Subsidy receipts
- One-off receipts

For cyclical energy businesses calculate **normalized FCF across the cycle**.

---

# 21. Normalized Earnings

Estimate where appropriate:

- Normalized crude price
- Normalized gas price
- Normalized GRM
- Normalized coal price
- Normalized production
- Normalized utilization
- Normalized EBITDA
- Normalized EBIT
- Normalized PAT
- Normalized CFO
- Normalized FCF

Use:

- Historical averages
- Mid-cycle benchmarks
- Peer economics
- Structural cost changes

All normalized metrics must be clearly labeled:

**ESTIMATED**

Never present them as reported financial figures.

---

# 22. Balance Sheet Analysis

Track:

- Gross debt
- Net debt
- Net debt/EBITDA
- Debt/equity
- Interest coverage
- Short-term debt
- Working-capital borrowing
- Lease liabilities
- Debt maturity
- Cash
- Liquidity
- Guarantees
- Contingent liabilities

Stress-test:

- Lower oil price
- Lower gas price
- Lower GRM
- Lower utilization
- Higher capex
- Higher working capital
- Higher interest cost

The balance sheet must be evaluated for **down-cycle resilience**.

---

# 23. Return Ratios

Track:

- ROE
- ROCE
- ROIC
- ROA
- Incremental ROIC
- Asset turnover
- Capital turnover

For energy companies compare returns across the cycle.

Important:

**Peak-cycle ROCE is not necessarily structural ROCE.**

Analyze:

**Commodity Price → Margin → EBIT → Capital Employed → ROIC**

---

# 24. Competitive Advantage

Assess:

- Resource ownership
- Reserve quality
- Low-cost production
- Refinery complexity
- Feedstock advantage
- Logistics
- Pipeline network
- Distribution network
- Retail footprint
- Brand
- Scale
- Long-term contracts
- Customer relationships
- Geographic advantage
- Technology

For upstream businesses, cost position and reserves may be more important than brand.

For downstream businesses, network scale, complexity and logistics may be more important.

---

# 25. Management & Governance

Track:

- Promoter holding
- Promoter pledge
- Promoter buying/selling
- Share dilution
- Related-party transactions
- Auditor changes
- Auditor qualifications
- Regulatory actions
- Environmental issues
- Executive remuneration
- Acquisitions
- Divestments
- Dividends
- Buybacks
- Capital allocation

## Concall Analysis

Extract:

- Demand outlook
- Crude-price assumptions
- Gas-price assumptions
- Production guidance
- GRM outlook
- Marketing margin
- Capacity utilization
- Capex guidance
- Project completion
- Exploration results
- Reserve additions
- Regulatory changes
- Energy-transition investments

Track:

**Guidance → Actual → Variance → Explanation**

---

# 26. Energy Transition Analysis

For companies exposed to conventional energy, track:

- Renewable investments
- Solar/wind capacity
- Battery/storage exposure
- EV infrastructure
- Green hydrogen
- Biofuels
- Gas transition
- Carbon intensity
- Emissions
- Transition capex

Do not assume transition investments automatically create value.

Evaluate:

- Capital invested
- Expected return
- Competitive position
- Commercial viability
- Scale
- Cash-flow impact
- Funding requirement

Analyze:

**Transition Capex → Capacity → Utilization → Revenue → EBITDA → FCF → ROIC**

---

# 27. Peer Comparison

Select peers based on:

- Value-chain position
- Commodity exposure
- Geography
- Integration
- Regulation
- Cost curve
- Scale

Compare:

- Production growth
- Realization
- Unit cost
- EBITDA/unit
- Margin
- ROCE
- ROIC
- CFO/PAT
- FCF margin
- Net debt
- Capacity
- Utilization
- Valuation

Industry-specific metrics must take precedence over generic ratios.

---

# 28. Valuation Framework

## Upstream

Use:

- EV/EBITDA
- EV/boe
- NAV/resource-based valuation
- DCF
- FCF yield

Normalize commodity prices and production assumptions.

## Refining

Use:

- EV/EBITDA
- EV/throughput
- P/E
- FCF yield

Consider normalized GRM.

## Marketing

Use:

- P/E
- EV/EBITDA
- EV/sales selectively
- FCF yield

Consider outlet/network economics.

## Gas Infrastructure

Use:

- EV/EBITDA
- DCF
- EV/capacity
- EV/volume where meaningful

## Coal/Mining

Use:

- EV/EBITDA
- EV/production
- NAV/resource-based valuation
- Normalized FCF

## Integrated Energy

Use:

- SOTP
- DCF
- Segment EV/EBITDA
- Asset-based valuation where relevant

Do not apply one multiple across the entire company without considering segment economics.

---

# 29. Historical Valuation

Track:

- Historical P/E percentile
- Historical EV/EBITDA percentile
- Historical P/B percentile
- Historical FCF yield
- Historical EV/throughput where relevant

Compare current valuation with:

1. Company's own history
2. Peer valuation
3. Commodity-cycle position
4. Normalized earnings
5. ROIC
6. Balance-sheet quality
7. Growth and reinvestment needs

Do not hard-code a universal valuation threshold.

---

# 30. Causal Analysis Engine

## Upstream

**Oil/Gas Price → Realization → Production → Unit Cost → EBITDA → CFO → Development Capex → FCF → ROIC**

## Refining

**Crude Price → Product Cracks → GRM → Throughput → EBITDA → CFO → Capex → FCF**

## Marketing

**Fuel Volume → Market Share → Marketing Margin → EBITDA → CFO**

## Coal

**Coal Price → Realization → Volume → Cost/tonne → EBITDA → CFO → FCF**

## Gas Transmission

**Capacity → Utilization → Volume → Tariff → Revenue → EBITDA → CFO → ROIC**

## Integrated Energy

**Upstream + Refining + Marketing + Gas → Consolidated Margin → CFO → Capex → FCF → Capital Allocation → ROIC**

The engine should identify exactly where the chain is strengthening or weakening.

---

# 31. Red-Flag Engine

## Commodity/Cycle Risks

- Peak-cycle earnings treated as sustainable
- Unrealistic oil/gas assumptions
- Temporary GRM expansion
- Inventory gains mistaken for structural profit
- High-cost production
- Falling production
- Reserve depletion

## Operating Risks

- Low utilization
- Production decline
- Rising unit costs
- Project delays
- Capacity additions without demand visibility

## Cash-Flow Risks

- PAT rising while CFO falls
- Persistent negative FCF
- Working-capital buildup
- Large subsidy/regulated receivables
- Debt-funded dividends
- Asset-sale-dependent cash generation

## Balance-Sheet Risks

- High net debt
- Short-term debt dependence
- Refinancing risk
- High interest burden
- Large project debt
- Weak liquidity entering a downturn

## Governance Risks

- Promoter pledge
- Frequent dilution
- Related-party transactions
- Auditor resignation
- Qualified audit opinion
- Aggressive acquisitions
- Unexplained guarantees

## Transition Risks

- Large transition capex with weak returns
- Stranded-asset risk
- Regulatory exposure
- Carbon-cost exposure
- Uncompetitive new-energy projects

---

# 32. Positive-Signal Engine

Look for:

- Low-cost production
- Strong reserve life
- Rising production
- Stable/improving unit economics
- Structural refining advantage
- Strong network utilization
- Long-term contracted volumes
- Strong balance sheet
- Positive normalized FCF
- Declining leverage
- High ROIC
- Disciplined capex
- Successful project execution
- Diversified energy exposure

Signals should be supported by operating and financial evidence.

---

# 33. Scenario Analysis

## Bull Case

Assume:

- Strong commodity prices
- Strong production
- Higher utilization
- Favorable spreads
- Stable input costs
- Strong cash generation

## Base Case

Assume:

- Mid-cycle commodity prices
- Normal production
- Normal utilization
- Normalized margins
- Planned capex

## Bear Case

Assume:

- Lower oil/gas/coal prices
- Lower GRM
- Lower utilization
- Higher input costs
- Higher working capital
- Higher capex
- Higher interest costs

Calculate impact on:

- Revenue
- EBITDA
- EBIT
- PAT
- CFO
- FCF
- ROIC
- Net debt
- Valuation

For highly cyclical businesses, include a balance-sheet survival test.

---

# 34. Scoring Architecture

Suggested dimensions:

| Dimension | Suggested Weight |
|---|---:|
| Asset / Business Quality | 10% |
| Cost Position / Unit Economics | 15% |
| Growth & Production | 10% |
| Cycle Position | 10% |
| Operating Quality | 10% |
| Cash Flow Quality | 15% |
| Balance Sheet | 15% |
| Capital Efficiency | 5% |
| Management & Governance | 5% |
| Valuation | 5% |

Weights should be adjusted by sub-industry.

Examples:

- Oil E&P → reserves, production and lifting cost
- Refining → GRM, throughput and complexity
- Marketing → volume, network and margin
- Gas → volume, contracts and utilization
- Coal → reserves, realization and cost
- Integrated energy → segment economics and capital allocation

Do not produce high-confidence scoring if critical commodity, operating or balance-sheet data is missing.

---

# 35. Data Quality Framework

Every metric must carry:

- metric_name
- value
- period
- unit
- source
- source_date
- data_type
- confidence

Allowed data types:

- REPORTED
- CALCULATED
- ESTIMATED
- MANAGEMENT-DISCLOSED
- THIRD-PARTY

Confidence:

- HIGH
- MEDIUM
- LOW

Normalized commodity prices, normalized margins and normalized earnings must be explicitly tagged:

**ESTIMATED**

Preserve the inputs and formulas used to derive calculated metrics.

---

# 36. Source Hierarchy

Preferred source order:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. NSE/BSE filings
6. Regulatory filings
7. Company investor-relations disclosures
8. Official commodity/benchmark sources
9. Reliable financial databases
10. Third-party research

Company-reported production, sales, reserves, capacity and segment data should be preserved alongside external benchmark data.

---

# 37. Agent Architecture

Recommended pipeline:

```text
Company Identification Agent
        ↓
Business Classification Agent
        ↓
Energy Value-Chain Agent
        ↓
Financial Data Agent
        ↓
Production / Volume Agent
        ↓
Commodity Price Agent
        ↓
Unit Economics Agent
        ↓
Cost-Curve Agent
        ↓
Capacity & Utilization Agent
        ↓
Reserve / Resource Agent
        ↓
Working Capital Agent
        ↓
Capex & Project Agent
        ↓
Cash Flow Agent
        ↓
Cycle / Normalization Agent
        ↓
Energy Transition Agent
        ↓
Management / Concall Agent
        ↓
Competitive Advantage Agent
        ↓
Peer Comparison Agent
        ↓
Valuation Agent
        ↓
Red Flag Agent
        ↓
Causal Analysis Agent
        ↓
Scoring Agent
        ↓
Investment Thesis Agent
```

---

# 38. Recommended Database Structure

## Company

- company_id
- company_name
- sector
- industry
- sub_industry
- business_model
- value_chain_position
- commodity_exposure
- market_cap

## Financial Metric

- company_id
- metric_name
- value
- period
- unit
- source
- source_date
- data_type
- confidence

## Energy Operating Metric

- company_id
- metric_name
- value
- period
- unit
- segment
- commodity
- source
- confidence

## Commodity Benchmark

- commodity
- benchmark
- price
- date
- unit
- source

## Reserve / Resource

- company_id
- asset
- commodity
- reserves
- resources
- production
- reserve_life
- source
- confidence

## Project

- company_id
- project_name
- capex
- planned_capacity
- completion_date
- revised_cost
- revised_completion
- utilization
- expected_return
- actual_return

## Guidance

- company_id
- guidance_date
- metric
- guidance_value
- period
- actual_value
- variance
- management_explanation

## Valuation

- company_id
- valuation_method
- normalized_metric
- multiple
- current_value
- historical_median
- peer_median
- percentile
- confidence

---

# 39. Final Screener Output

## 1. Company Snapshot

- Business
- Value-chain position
- Energy exposure
- Market cap
- Revenue
- EBITDA
- PAT
- ROIC
- Net debt
- FCF

## 2. Energy Exposure

- Oil
- Gas
- Coal
- Refining
- Marketing
- Infrastructure
- Other energy businesses

## 3. Operating Quality

- Production
- Volume
- Realization
- Capacity
- Utilization
- Unit cost
- Unit EBITDA

## 4. Cycle Analysis

- Benchmark price
- Historical position
- Current margin
- Normalized margin
- Normalized earnings

## 5. Cash Quality

- CFO
- FCF
- CFO/PAT
- Working capital
- Maintenance capex

## 6. Balance Sheet

- Net debt
- Net debt/EBITDA
- Interest coverage
- Liquidity
- Down-cycle stress

## 7. Capital Efficiency

- ROE
- ROCE
- ROIC
- Asset turnover
- Incremental ROIC

## 8. Management

- Guidance
- Capital allocation
- Project execution
- Concall observations
- Governance

## 9. Energy Transition

- Transition investments
- Capex
- Capacity
- Commercial progress
- Expected economics
- Risks

## 10. Valuation

- P/E
- EV/EBITDA
- Normalized EV/EBITDA
- FCF yield
- NAV/SOTP where relevant
- Historical valuation
- Peer valuation

## 11. Peer Position

Compare relevant industry peers using operating and financial metrics.

## 12. Causal Analysis

Explain:

**Commodity/energy price → volume → realization → unit economics → profit → cash → capex → ROIC**

## 13. Red Flags

List material concerns with:

- Severity
- Evidence
- Source
- Potential impact

## 14. Positive Signals

List evidence-backed strengths.

## 15. Investment Thesis

Produce:

- Business thesis
- Energy-cycle thesis
- Production/volume thesis
- Unit-economics thesis
- Cash-flow thesis
- Capital-efficiency thesis
- Valuation thesis
- Energy-transition thesis
- Bull case
- Bear case
- Key risks
- Thesis-break conditions
- Next-quarter metrics to monitor

---

# 40. Implementation Principles

1. Always classify the company's position in the energy value chain.
2. Separate upstream, midstream and downstream economics.
3. Separate volume from price.
4. Track benchmark prices and company realizations.
5. Track unit economics and cost curves.
6. Normalize cyclical earnings.
7. Separate inventory gains from recurring operating profit.
8. Analyze reserves and reserve life for resource businesses.
9. Analyze utilization for infrastructure and processing businesses.
10. Evaluate capex against expected returns.
11. Stress-test the balance sheet through a downturn.
12. Track working-capital effects of commodity-price movements.
13. Separate conventional-energy economics from transition investments.
14. Compare ROIC across the cycle.
15. Preserve source provenance for every metric.
16. Explicitly label estimated/normalized values.
17. Do not apply one valuation multiple to all energy business models.
18. Make the final thesis traceable to operating evidence and cash generation.

---

# 41. Sector-Level Fundamental Question

The final engine should answer:

> **Is this Energy company structurally competitive through its resource quality, cost position, operating efficiency, value-chain position, balance-sheet resilience and capital allocation, and is its current valuation supported by normalized mid-cycle cash generation?**

The analysis must clearly distinguish **commodity-cycle effects, regulated economics, temporary spreads and structural competitive advantages**, while preserving the provenance and confidence of every material data point.
