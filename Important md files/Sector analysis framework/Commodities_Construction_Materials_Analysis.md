# Construction Materials — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

**Macro Sector:** Commodities  
**Sector:** Construction Materials  
**Industries in this sector:**
- Cement & Cement Products
- Other Construction Materials

**Classification hierarchy:**

```text
Commodities
└── Construction Materials
    ├── Cement & Cement Products
    └── Other Construction Materials
```


**Version:** 1.0  
**Primary Market:** India  
**Sector:** Construction Materials  
**Parent Macro Sector:** Commodities

## 1. Purpose

This framework is a standalone fundamental-analysis engine for companies classified under **Construction Materials**.

Industries covered:

- Cement & Cement Products
- Other Construction Materials

Core philosophy:

> **DEMAND → VOLUME → CAPACITY → UTILIZATION → REALIZATION / PRICE → INPUT COST → EBITDA / UNIT → CASH FLOW → CAPEX → ROCE / ROIC → BALANCE SHEET → VALUATION**

Construction-material businesses must be analyzed through their physical volumes, regional demand, pricing, capacity utilization, input costs, freight economics and capital intensity—not through generic financial ratios alone.

---

# 2. Industry Coverage

## 2.1 Cement & Cement Products

Analyze:

- Cement production
- Cement sales
- Clinker production
- Clinker capacity
- Grinding capacity
- Installed capacity
- Capacity utilization
- Realization per tonne
- EBITDA per tonne
- Fuel cost
- Power cost
- Freight
- Raw-material cost
- Petcoke / coal exposure
- Alternative fuels
- Waste heat recovery
- Blended cement
- Trade / non-trade mix
- Regional exposure
- Integrated vs grinding-only model

Primary causal chain:

```text
CEMENT DEMAND
↓
VOLUME
↓
CAPACITY UTILIZATION
↓
REALIZATION / PRICE
↓
FUEL + POWER + FREIGHT COST
↓
EBITDA / TONNE
↓
EBITDA
↓
CFO
↓
CAPEX
↓
FCF
↓
ROCE
```

---

## 2.2 Other Construction Materials

Depending on the company, classify exposure to:

- Building products
- Pipes
- Tiles
- Ceramics
- Sanitaryware
- Glass
- Roofing materials
- Insulation
- Construction chemicals
- Flooring
- Bricks / blocks
- Aggregates
- Ready-mix concrete
- Other construction inputs

The engine must identify the company's specific product economics before applying industry metrics.

Track:

- Volume
- Capacity
- Utilization
- Average selling price
- Realization
- Product mix
- Raw-material costs
- Energy costs
- Freight
- Dealer/distributor network
- Housing vs infrastructure exposure
- Replacement vs new-construction demand

---

# 3. Business Model Classification

Every company must first be classified.

Required fields:

```text
macro_sector
sector
industry
business_model
product_category
integrated_model
manufacturing_model
domestic_export_mix
geography
regional_exposure
capacity
capacity_utilization
distribution_model
customer_type
end_market
asset_intensity
capital_intensity
```

Business models may include:

- Integrated cement producer
- Grinding-only cement producer
- Cement products manufacturer
- Building-material manufacturer
- Consumer-facing building-products company
- Infrastructure-material supplier
- B2B construction-material supplier
- Dealer/distributor-led business
- Project-oriented supplier
- Export-oriented producer

---

# 4. Demand Analysis

Construction-material demand is highly dependent on:

- Housing
- Infrastructure
- Roads
- Urbanization
- Commercial construction
- Industrial construction
- Real-estate activity
- Government capex
- Rural construction
- Repair / renovation

Classify demand into:

```text
Residential
Infrastructure
Commercial
Industrial
Government
Renovation / Replacement
```

Analyze:

- Demand growth
- Regional demand
- New construction vs replacement
- Public vs private demand
- End-market concentration

The engine should separate:

```text
Demand Growth
vs
Company Volume Growth
```

A company growing faster than the market may be gaining share, expanding geographically or adding capacity.

---

# 5. Volume Analysis

Track:

- Production volume
- Sales volume
- Dispatch volume
- Installed capacity
- Capacity additions
- Capacity utilization
- Volume growth

Calculate:

```text
Capacity Utilization =
Actual Production / Installed Capacity
```

and:

```text
Volume Growth =
Current Volume / Prior Period Volume - 1
```

For cement, separately track where available:

- Clinker volume
- Cement volume
- Trade volume
- Non-trade volume

Analyze:

> Is growth coming from demand, market-share gains, capacity additions or inventory movement?

---

# 6. Pricing & Realization

Track:

- Average selling price
- Realization per tonne
- Regional realization
- Trade realization
- Non-trade realization
- Premium product contribution
- Price increases
- Discounts

Calculate:

```text
Realization / Tonne =
Revenue from Product / Sales Volume
```

Analyze:

```text
Revenue Growth
=
Volume Effect
+
Price Effect
+
Mix Effect
```

Do not automatically classify higher realization as pricing power.

Determine whether it comes from:

- Industry price increase
- Regional mix
- Product mix
- Premium products
- Lower discounts
- Customer mix
- Currency

---

# 7. Capacity Analysis

Track:

- Existing capacity
- Capacity additions
- Capacity under construction
- Planned capacity
- Brownfield expansion
- Greenfield expansion
- Acquisition-led capacity
- Grinding capacity
- Clinker capacity

Calculate:

```text
Capacity Growth %
=
Future Capacity / Current Capacity - 1
```

Analyze:

- Demand support
- Project economics
- Utilization potential
- Expansion geography
- Funding
- Commissioning schedule

Flag:

- Large capacity additions ahead of demand
- Low utilization after expansion
- Debt-funded expansion
- High-cost greenfield projects

---

# 8. Cement-Specific Clinker Analysis

For cement companies, track:

- Clinker capacity
- Clinker production
- Clinker utilization
- Clinker-to-cement ratio
- Purchased clinker
- Captive clinker
- Grinding capacity

A company with stronger clinker integration may have a different cost structure from a grinding-only operator.

Analyze:

```text
Clinker Integration
=
Captive Clinker Availability / Cement Requirement
```

where data permits.

---

# 9. Cement Cost Structure

Track cost per tonne:

- Limestone
- Coal
- Petcoke
- Power
- Freight
- Packaging
- Employee cost
- Maintenance
- Other operating costs

Key metrics:

```text
Cost / Tonne
Power Cost / Tonne
Fuel Cost / Tonne
Freight Cost / Tonne
EBITDA / Tonne
```

For cement, analyze the following bridge:

```text
Realization / Tonne
-
Raw Material Cost / Tonne
-
Fuel Cost / Tonne
-
Power Cost / Tonne
-
Freight / Tonne
-
Other Costs / Tonne
=
EBITDA / Tonne
```

---

# 10. Energy Analysis

Energy is a major cost driver.

Track:

- Power consumption per tonne
- Fuel consumption per tonne
- Coal
- Petcoke
- Alternative fuels
- Renewable power
- Captive power
- Waste heat recovery
- Power purchase cost

Calculate where possible:

```text
Energy Cost / Tonne
```

Analyze sensitivity to:

- Coal prices
- Petcoke prices
- Electricity prices
- Renewable share
- Fuel mix

Flag:

- Rising energy cost without realization improvement
- High dependence on imported fuel
- Poor energy efficiency
- High exposure to volatile power prices

---

# 11. Freight & Logistics

Freight can materially determine regional competitiveness.

Track:

- Freight cost
- Freight/tonne
- Lead distance
- Rail vs road mix
- Logistics infrastructure
- Plant location
- Market location
- Depot network
- Captive logistics

Calculate:

```text
Freight Cost / Tonne
```

Analyze the relationship between:

```text
Plant Location
+
Logistics Network
+
Regional Realization
=
Market Competitiveness
```

For cement, evaluate the geographic radius within which the plant can compete economically.

---

# 12. Regional Analysis

Construction materials are often regional businesses.

Track by geography:

- Revenue
- Volume
- Realization
- EBITDA
- Capacity
- Utilization
- Market share where available

Required regions may include:

```text
North
South
East
West
Central
Northeast
Export
```

The engine should identify:

- Strongest region
- Weakest region
- Expansion regions
- Regional pricing differences
- Regional cost advantages

Do not treat a national average as representative if regional exposure is concentrated.

---

# 13. Product Mix

Track:

- Standard products
- Premium products
- Value-added products
- Blended cement
- Specialty products
- Higher-margin construction materials

Calculate:

```text
Premium Product Revenue %
=
Premium Product Revenue / Total Revenue
```

Analyze whether margin improvement comes from:

- Premiumization
- Price increases
- Cost reduction
- Volume
- Regional mix

---

# 14. Distribution & Market Structure

Track:

- Dealer count
- Distributor count
- Retail channel
- Institutional sales
- Direct sales
- Trade sales
- Non-trade sales
- Dealer concentration
- Geographic distribution

For consumer-oriented construction materials, analyze:

- Brand strength
- Dealer network
- Retail reach
- Dealer productivity
- Channel incentives
- Inventory levels

Flag:

- Excessive channel inventory
- Aggressive dealer incentives
- Receivable buildup
- Customer concentration

---

# 15. Margin Analysis

Track:

- Gross margin
- EBITDA
- EBITDA margin
- EBITDA/tonne
- EBIT
- EBIT margin
- PAT
- PAT margin

For cement:

```text
EBITDA / Tonne
```

is a core operating metric.

Analyze margin changes through:

```text
Realization
+
Volume
+
Fuel
+
Power
+
Freight
+
Raw Materials
+
Mix
+
Operating Leverage
```

Separate:

- Structural margin improvement
- Temporary input-cost benefit
- Industry-wide price increase
- Product-mix improvement
- One-time benefit

---

# 16. Working Capital

Track:

- Inventory
- Receivables
- Payables
- Inventory days
- Receivable days
- Payable days
- Cash conversion cycle

Calculate:

```text
CCC =
Inventory Days + Receivable Days - Payable Days
```

Analyze:

- Dealer receivables
- Institutional receivables
- Inventory buildup
- Channel inventory
- Working-capital intensity

Flag:

```text
RECEIVABLES_GROWING_FASTER_THAN_REVENUE
INVENTORY_BUILD
WEAK_CASH_CONVERSION
CHANNEL_STOCK_BUILD
```

---

# 17. Capex

Track:

- Maintenance capex
- Expansion capex
- Greenfield capex
- Brownfield capex
- Capacity addition capex
- Environmental capex
- Energy-efficiency capex

Calculate:

```text
Capex / Revenue
Capex / EBITDA
Capex / Tonne of New Capacity
```

Analyze:

- Cost per tonne of capacity addition
- Expected utilization
- Funding
- Project timeline
- Return on incremental capital

For expansion:

```text
Incremental ROCE =
Incremental Operating Profit / Incremental Capital Employed
```

where sufficient data exists.

---

# 18. Cash Flow

Track:

- CFO
- EBITDA
- CFO/EBITDA
- CFO/PAT
- Capex
- FCF
- FCF margin
- Dividend
- Buyback
- Debt repayment

Calculate:

```text
FCF = CFO - Capex
```

and:

```text
CFO Conversion =
CFO / EBITDA
```

Analyze FCF across the cycle.

Important question:

> Does the company convert its reported EBITDA into cash after working capital and sustaining capital expenditure?

---

# 19. Balance Sheet

Track:

- Gross debt
- Cash
- Net debt
- Net debt/EBITDA
- Debt/equity
- Interest coverage
- Lease liabilities
- Contingent liabilities
- Capital commitments

Calculate:

```text
Net Debt =
Gross Debt - Cash
```

and:

```text
Net Debt / EBITDA
```

Evaluate leverage using normalized EBITDA, not only current-cycle EBITDA.

---

# 20. ROCE / ROIC

Track:

- ROE
- ROCE
- ROIC
- Asset turnover
- Fixed asset turnover
- Capital employed
- Incremental ROCE

Construction materials are generally capital-intensive, so evaluate:

```text
ROCE
vs
Cost of Capital
```

and:

```text
Incremental ROCE
vs
Historical ROCE
```

Flag:

- Large capex with weak incremental returns
- Rising capital employed without proportional EBIT growth
- High ROCE caused mainly by temporary price increases

---

# 21. Competitive Advantage

Assess evidence for:

- Low-cost plants
- Strong limestone reserves
- Geographic advantage
- Logistics advantage
- Scale
- Brand
- Dealer network
- Premium products
- Distribution reach
- Energy efficiency
- Waste heat recovery
- Renewable energy
- Vertical integration

Separate:

```text
STRUCTURAL ADVANTAGE
vs
TEMPORARY INDUSTRY CONDITIONS
```

---

# 22. Industry Capacity & Supply Analysis

Track where available:

- Industry capacity
- Company capacity
- Capacity additions
- Industry utilization
- Regional oversupply
- Regional shortage
- Consolidation
- New entrants

Analyze:

```text
Industry Capacity Growth
vs
Industry Demand Growth
```

If capacity growth consistently exceeds demand growth, flag potential:

```text
OVER_CAPACITY_RISK
PRICING_PRESSURE
UTILIZATION_PRESSURE
```

---

# 23. Housing & Infrastructure Cycle

Analyze exposure to:

### Housing

- Residential construction
- Urban housing
- Rural housing
- Real-estate cycle
- Mortgage growth where relevant

### Infrastructure

- Roads
- Railways
- Airports
- Ports
- Power
- Industrial infrastructure
- Government capex

Separate:

```text
Government-led demand
vs
Private-sector demand
```

This helps determine whether growth is cyclical, policy-driven or structurally supported.

---

# 24. Management & Capital Allocation

Analyze:

- Capacity expansion discipline
- Acquisition strategy
- Debt management
- Dividends
- Buybacks
- Related-party transactions
- Promoter holding
- Promoter pledge
- Dilution
- Auditor history
- Contingent liabilities
- Project execution
- Management guidance

Key questions:

- Does management add capacity ahead of demand?
- Are acquisitions integrated effectively?
- Is capital allocated toward high-return regions?
- Does management maintain balance-sheet discipline?

---

# 25. Peer Comparison

Peers should be selected based on:

- Product
- Geography
- Capacity
- Business model
- End-market exposure

Compare:

### Operating

- Capacity
- Utilization
- Volume growth
- Realization
- EBITDA/tonne
- Cost/tonne

### Financial

- Revenue CAGR
- EBITDA growth
- EBITDA margin
- CFO conversion
- FCF

### Capital Efficiency

- ROCE
- ROIC
- Incremental ROCE

### Balance Sheet

- Net debt
- Net debt/EBITDA
- Interest coverage

### Valuation

- P/E
- EV/EBITDA
- EV/EBIT
- P/B
- FCF yield
- Historical multiples

---

# 26. Valuation

Use:

- P/E
- EV/EBITDA
- EV/EBIT
- P/B
- EV/Sales
- FCF yield

For cement and cyclical construction materials, compare valuation against:

- Historical multiple
- Peer multiple
- Normalized EBITDA
- Mid-cycle earnings
- Current utilization
- Current realization
- Current input costs

Do not hard-code a universal valuation threshold.

The system should answer:

> Is the current valuation based on sustainable earnings or unusually favorable operating conditions?

---

# 27. Historical Cycle Analysis

Maintain:

- 5Y history minimum where available
- 10Y history preferred

Track:

```text
Demand
Volume
Capacity
Utilization
Realization
Fuel Cost
Power Cost
Freight
EBITDA / Tonne
EBITDA
CFO
FCF
ROCE
Net Debt
```

Classify the current operating environment as:

```text
DEMAND WEAK
NORMAL
STRONG
```

and:

```text
MARGIN DEPRESSED
NORMALIZED
ELEVATED
```

Do not treat the latest quarter in isolation.

---

# 28. Growth Quality

Classify growth as:

### Volume-led

Sales volumes are increasing.

### Capacity-led

New capacity is driving growth.

### Price-led

Industry prices are increasing.

### Mix-led

Premium products or favorable geography increase realization.

### Market-share-led

Company volume grows faster than industry demand.

### Acquisition-led

Growth is driven by acquired capacity.

The final analysis should identify the dominant growth driver.

---

# 29. Positive Signals

Examples:

- Volume growth with strong utilization
- Sustainable realization improvement
- Improving cost/tonne
- Lower fuel and power intensity
- Strong regional positioning
- Increasing premium mix
- Strong CFO conversion
- FCF generation
- Falling net debt
- High incremental ROCE
- Disciplined capacity expansion
- Strong distribution network
- Structural cost advantage

These are analytical signals, not automatic investment conclusions.

---

# 30. Red Flags

Flag:

```text
OVER_CAPACITY_RISK
LOW_UTILIZATION
PRICE_PRESSURE
HIGH_FUEL_COST
HIGH_POWER_COST
HIGH_FREIGHT_COST
REGIONAL_CONCENTRATION
AGGRESSIVE_CAPACITY_EXPANSION
HIGH_NET_DEBT
WEAK_CFO_CONVERSION
NEGATIVE_FCF
WORKING_CAPITAL_BUILD
CHANNEL_INVENTORY_BUILD
LOW_INCREMENTAL_ROCE
ACQUISITION_DEPENDENCY
PROJECT_EXECUTION_RISK
REGULATORY_RISK
ENVIRONMENTAL_RISK
RELATED_PARTY_RISK
PEAK_MARGIN_VALUATION
```

---

# 31. Scenario Analysis

Build three scenarios.

## Down Cycle

Assume:

- Lower construction demand
- Lower utilization
- Lower realization
- Higher input costs
- Lower EBITDA/tonne

Output:

- Revenue
- EBITDA
- PAT
- CFO
- FCF
- Net debt
- ROCE

## Base / Normalized Cycle

Use normalized:

- Demand
- Volume
- Realization
- Input costs
- Utilization
- EBITDA/tonne

## Up Cycle

Assume:

- Strong demand
- Higher utilization
- Better realization
- Stable/favorable input costs
- Operating leverage

Clearly label all scenario assumptions as assumptions rather than reported data.

---

# 32. Causal Analysis Engine

The final engine should follow:

```text
CONSTRUCTION DEMAND
↓
INDUSTRY VOLUME
↓
COMPANY VOLUME
↓
CAPACITY UTILIZATION
↓
REALIZATION
↓
INPUT COST
↓
EBITDA / TONNE
↓
EBITDA
↓
CFO
↓
CAPEX
↓
FCF
↓
DEBT / CASH
↓
ROCE / ROIC
↓
VALUATION
```

For cement:

```text
CLINKER
↓
GRINDING
↓
CEMENT VOLUME
↓
REALIZATION
↓
FUEL + POWER + FREIGHT
↓
EBITDA / TONNE
↓
FCF
```

---

# 33. Scoring Architecture

Maintain separate dimensions:

```text
DEMAND QUALITY
ASSET / CAPACITY QUALITY
COST COMPETITIVENESS
GROWTH
OPERATING QUALITY
CASH FLOW QUALITY
BALANCE SHEET
CAPITAL EFFICIENCY
COMPETITIVE POSITION
MANAGEMENT / GOVERNANCE
VALUATION
RISK
```

Each dimension should retain:

- Metric
- Value
- Trend
- Peer comparison
- Interpretation
- Data confidence

Do not collapse all metrics into an opaque single score.

---

# 34. Data Quality

Every metric must preserve:

```text
metric_name
value
period
unit
source
source_date
data_type
confidence
calculation_method
```

Data types:

```text
REPORTED
CALCULATED
ESTIMATED
MANAGEMENT_DISCLOSED
THIRD_PARTY
```

Confidence:

```text
HIGH
MEDIUM
LOW
```

Source priority:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings / Concall Transcript
5. NSE / BSE filings
6. Company operational disclosures
7. Regulatory sources
8. Reliable financial databases
9. Third-party datasets

Never convert management guidance into reported performance.

---

# 35. Agent Architecture

Recommended pipeline:

```text
COMPANY IDENTIFICATION
        ↓
SECTOR / INDUSTRY CLASSIFICATION
        ↓
BUSINESS MODEL CLASSIFICATION
        ↓
RAW FINANCIAL DATA
        ↓
DEMAND DATA
        ↓
CAPACITY / PRODUCTION DATA
        ↓
REALIZATION ENGINE
        ↓
INPUT COST ENGINE
        ↓
UNIT ECONOMICS ENGINE
        ↓
P&L ANALYSIS
        ↓
BALANCE SHEET ANALYSIS
        ↓
CASH FLOW ANALYSIS
        ↓
ROCE / ROIC ENGINE
        ↓
MANAGEMENT / CONCALL ENGINE
        ↓
INDUSTRY CAPACITY ANALYSIS
        ↓
PEER COMPARISON
        ↓
HISTORICAL CYCLE ANALYSIS
        ↓
VALUATION ENGINE
        ↓
RED FLAG ENGINE
        ↓
SCENARIO ENGINE
        ↓
FINAL FUNDAMENTAL ANALYSIS
```

---

# 36. Database Structure

Recommended tables:

```text
companies
company_classification
industry_mapping
demand_metrics
industry_capacity
company_capacity
production_metrics
sales_volume_metrics
realization_metrics
input_cost_metrics
energy_metrics
freight_metrics
regional_metrics
product_mix_metrics
segment_metrics
financial_statements
working_capital_metrics
cash_flow_metrics
balance_sheet_metrics
capex_metrics
management_guidance
concall_metrics
peer_metrics
valuation_metrics
risk_flags
scenario_assumptions
analysis_results
data_quality
```

Each observation should preserve:

```text
company_id
metric_id
period
value
unit
source
source_date
data_type
confidence
```

---

# 37. Final Screener Output

For every Construction Materials company, generate:

## Company Snapshot

- Company
- Industry
- Product category
- Business model
- Geography
- Market capitalization

## Demand

- End-market exposure
- Housing exposure
- Infrastructure exposure
- Demand trend
- Regional demand

## Operating

- Capacity
- Utilization
- Production
- Sales volume
- Volume growth
- Realization
- Cost/tonne
- EBITDA/tonne

## Cost Structure

- Fuel
- Power
- Freight
- Raw materials
- Other costs

## Financial Quality

- Revenue growth
- EBITDA growth
- EBITDA margin
- PAT
- CFO
- FCF

## Balance Sheet

- Gross debt
- Net debt
- Net debt/EBITDA
- Interest coverage

## Capital Efficiency

- ROCE
- ROIC
- Incremental ROCE

## Competitive Position

- Geographic advantage
- Cost position
- Brand
- Distribution
- Product mix
- Scale

## Capacity Cycle

- Industry capacity
- Company capacity
- Capacity additions
- Utilization
- Supply-demand balance

## Valuation

- P/E
- EV/EBITDA
- EV/EBIT
- P/B
- FCF yield
- Historical valuation
- Peer valuation
- Normalized valuation

## Management

- Capital allocation
- Expansion
- Acquisitions
- Governance
- Concall signals

## Risks

- Demand
- Pricing
- Input costs
- Freight
- Capacity
- Leverage
- Execution
- Regulation
- Environment

## Final Analytical Output

```text
DEMAND QUALITY
ASSET / CAPACITY QUALITY
COST POSITION
GROWTH ENGINE
OPERATING ENGINE
CASH ENGINE
BALANCE SHEET
CAPITAL EFFICIENCY
COMPETITIVE POSITION
INDUSTRY CYCLE POSITION
VALUATION
KEY POSITIVES
KEY CONCERNS
RED FLAGS
DATA CONFIDENCE
BULL CASE
BASE CASE
BEAR CASE
THESIS
THESIS BREAK CONDITIONS
NEXT QUARTER METRICS TO WATCH
```

---

# 38. Implementation Principles

The engine must follow:

```text
RAW DATA
→ VERIFIED DATA
→ NORMALIZATION
→ DEMAND ANALYSIS
→ VOLUME ANALYSIS
→ CAPACITY / UTILIZATION
→ REALIZATION ANALYSIS
→ INPUT COST ANALYSIS
→ UNIT ECONOMICS
→ FINANCIAL ANALYSIS
→ CASH FLOW
→ ROCE / ROIC
→ INDUSTRY SUPPLY-DEMAND
→ PEER COMPARISON
→ CYCLE ANALYSIS
→ RED FLAGS
→ SCENARIOS
→ VALUATION
→ FINAL FUNDAMENTAL THESIS
```

The central implementation rule is:

> **Do not confuse construction-material price increases with structural demand growth or durable pricing power.**

Always separate:

```text
DEMAND
vs
VOLUME
vs
CAPACITY
vs
UTILIZATION
vs
PRICE
vs
MIX
vs
INPUT COST
vs
FREIGHT
vs
CAPITAL ALLOCATION
```

The central fundamental question for Construction Materials is:

> **Can the company sustain attractive unit economics and returns on capital through a normalized construction cycle while expanding capacity without destroying shareholder value?**
