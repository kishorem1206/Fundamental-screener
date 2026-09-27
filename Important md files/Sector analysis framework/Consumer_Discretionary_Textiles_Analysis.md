# Consumer Discretionary — Textiles — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

## 1. Classification

**Macro Sector:** Consumer Discretionary  
**Sector Value:** Textiles  
**Industry:** Textiles & Apparels

```text
Consumer Discretionary
└── Textiles
    └── Textiles & Apparels
```

This framework is specifically for companies classified under **Consumer Discretionary → Textiles → Textiles & Apparels**. The source framework classifies the industry into spinning, weaving, processing, garments, home textiles, technical textiles, synthetic textiles, cotton textiles, integrated manufacturers, export-oriented businesses and domestic branded apparel. fileciteturn18file0L94-L120

---

# 2. Purpose

Build a sector-specific fundamental-analysis layer that explains:

```text
BUSINESS MODEL
      ↓
DEMAND
      ↓
VOLUME + PRICE + MIX
      ↓
UTILIZATION
      ↓
RAW-MATERIAL / INPUT COST
      ↓
SPREAD
      ↓
GROSS MARGIN
      ↓
EBITDA / EBIT
      ↓
WORKING CAPITAL
      ↓
CASH FLOW
      ↓
ROCE / ROIC
      ↓
COMPETITIVE POSITION
      ↓
CYCLE POSITION
      ↓
VALUATION
      ↓
CAUSAL ANALYSIS
      ↓
FUNDAMENTAL THESIS
```

The system must distinguish structural improvement from temporary textile-cycle benefits.

---

# 3. Industry Coverage

## 3.1 Spinning

Track:

- Installed spindle capacity
- Production volume
- Yarn production
- Yarn realization/kg
- Utilization
- Cotton/raw-material cost
- Yarn spread
- Export share
- Domestic share
- Product mix
- Power cost
- Labour cost

## 3.2 Weaving

Track:

- Loom capacity
- Fabric production
- Meterage
- Realization/meter
- Utilization
- Grey fabric vs value-added fabric
- Product mix
- Power consumption
- Labour intensity
- Export share

## 3.3 Processing

Track:

- Processing volume
- Meterage
- Dyeing/finishing capacity
- Utilization
- Realization/meter
- Chemical/dye cost
- Energy cost
- Water treatment cost
- Value-added product share
- Customer concentration

## 3.4 Garments / Apparel

Track:

- Garment units
- Pieces produced
- Pieces sold
- ASP
- Revenue per garment
- Capacity
- Utilization
- Domestic/export mix
- Brand/channel mix
- Customer concentration
- Order book
- Private-label vs own-brand mix

## 3.5 Home Textiles

Track:

- Towels
- Bed linen
- Rugs
- Furnishing textiles
- Volume
- Realization
- Export share
- Customer concentration
- Product mix
- Capacity utilization

## 3.6 Technical Textiles

Track:

- Product category
- Application
- Volume
- Realization
- Industrial/customer concentration
- Export share
- Capacity
- Utilization
- Certification requirements
- R&D intensity
- Value-added mix

## 3.7 Synthetic Textiles

Track:

- Polyester/nylon/other synthetic products
- Polymer/raw-material prices
- Volume
- Realization
- Spread
- Utilization
- Product mix
- Export share

## 3.8 Cotton Textiles

Track:

- Cotton consumption
- Cotton price
- Yarn/fabric realization
- Cotton-yarn spread
- Inventory position
- Utilization
- Export demand
- Domestic demand

## 3.9 Integrated Textile Manufacturers

Map the value chain:

```text
Cotton / Fibre
      ↓
Spinning
      ↓
Weaving
      ↓
Processing
      ↓
Garments / Home Textiles
      ↓
Brand / Export Customer
```

Measure how vertical integration affects:

- Margin stability
- Input-cost protection
- Working capital
- Utilization
- ROCE
- Product realization
- Supply-chain control

## 3.10 Export-Oriented Textile Companies

Track:

- Export revenue %
- Geography
- Customer concentration
- Currency exposure
- Hedging
- Freight
- Export incentives where applicable
- Order book
- Export realization
- Foreign-currency receivables
- Trade-policy exposure

## 3.11 Domestic Branded Apparel

Track:

- Brand count
- Stores
- Distribution reach
- Online share
- Wholesale/direct-to-consumer mix
- Same-store growth where disclosed
- ASP
- Units
- Gross margin
- Inventory ageing
- Markdown
- Brand positioning
- Market share

---

# 4. Business-Model Classification

Before analysis, classify each company using one or more tags:

```text
SPINNING
WEAVING
PROCESSING
GARMENTS
HOME_TEXTILES
TECHNICAL_TEXTILES
SYNTHETIC_TEXTILES
COTTON_TEXTILES
INTEGRATED
EXPORT_ORIENTED
DOMESTIC_BRANDED
ASSET_HEAVY
ASSET_LIGHT
B2B
B2C
PRIVATE_LABEL
OWN_BRAND
```

Also identify:

- Revenue model
- Customer type
- Geography
- Product mix
- Distribution model
- Export/domestic exposure
- Commodity exposure
- Value-added exposure
- Capacity intensity
- Working-capital intensity
- Capital intensity

Do not compare a commodity-oriented spinning company directly with a branded apparel company without adjusting the KPI set.

---

# 5. Common Financial Dataset

Collect annual, quarterly and TTM data wherever available.

## 5.1 P&L

Capture:

- Revenue
- Revenue growth
- Material/raw-material cost
- Employee cost
- Power & fuel
- Manufacturing expenses
- Freight
- Chemicals/dyes
- Subcontracting
- Selling expenses
- Administrative expenses
- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- Depreciation
- Interest
- PBT
- Tax
- PAT
- PAT margin
- EPS

## 5.2 Balance Sheet

Capture:

- Cash
- Inventory
- Trade receivables
- Trade payables
- Other current assets
- Working capital
- Gross fixed assets
- Net fixed assets
- CWIP
- Investments
- Total debt
- Net debt
- Equity
- Reserves
- Net worth

## 5.3 Cash Flow

Capture:

- CFO
- Capex
- CFI
- CFF
- FCF
- CFO/PAT
- FCF/PAT
- Debt raised
- Debt repayment
- Dividend
- Equity issuance

The ratio engine should preserve source inputs and distinguish AVAILABLE, CALCULABLE, PARTIAL, MISSING_INPUT, SOURCE_REQUIRED, NOT_APPLICABLE and INVALID rather than treating missing values as zero. fileciteturn18file1L223-L265

---

# 6. Core Textile Operating Metrics

## 6.1 Volume

Track:

- Production volume
- Sales volume
- Volume growth
- Units sold
- Kg sold
- Tonnes sold
- Meters sold
- Pieces sold

Where possible:

```text
Volume Growth = Current Volume / Prior Volume - 1
```

## 6.2 Realization

Track:

- Realization/kg
- Realization/tonne
- Realization/meter
- ASP/piece
- Revenue/unit

Separate:

```text
Volume Growth
Price / Realization Growth
Mix Growth
```

Do not interpret revenue growth as volume growth without evidence.

## 6.3 Capacity

Track:

- Installed capacity
- New capacity
- Capacity retired
- Production
- Utilization
- Utilization trend

```text
Utilization = Production / Available Capacity × 100
```

Analyze whether margin expansion is caused by:

- Better utilization
- Better realization
- Lower input cost
- Better mix
- Operating leverage

---

# 7. Demand Analysis

Analyze demand separately for:

### Domestic

- Consumption growth
- Rural/urban exposure
- Apparel demand
- Replacement cycle
- Fashion cycle
- Consumer income
- Channel inventory

### Export

- Major geographies
- Global textile demand
- Customer orders
- Export growth
- Currency
- Freight
- Trade restrictions
- Competitor-country capacity
- China/Bangladesh/Vietnam/Turkey/other relevant competitive exposure

### Apparel / Branded

Track:

- Footfall
- Units
- ASP
- Same-store growth where disclosed
- Channel inventory
- E-commerce
- Store additions
- Brand traction

---

# 8. Volume–Price–Mix Engine

For every period, decompose revenue:

```text
Revenue Growth
    ├── Volume
    ├── Realization
    └── Mix
```

Preferred analysis:

```text
Revenue Growth
= Volume Effect
+ Price Effect
+ Mix Effect
+ Acquisition / Other Effect
```

Where exact decomposition is unavailable, explicitly mark the component as estimated or unavailable.

Flag:

- Revenue growth driven only by price
- Volume contraction hidden by realization
- Margin improvement from temporary mix
- Export growth caused by currency rather than underlying demand

---

# 9. Raw-Material and Input-Cost Analysis

## 9.1 Key Inputs

Depending on business model:

- Cotton
- Polyester
- Viscose
- Yarn
- Fibre
- Dyes
- Chemicals
- Power
- Fuel
- Coal
- Natural gas
- Labour
- Freight
- Packaging

The reference framework explicitly identifies cotton/raw material, yarn, power, fuel, labour, freight, chemicals/dyes and subcontracting as key textile cost drivers. fileciteturn18file2L393-L405

## 9.2 Cost Ratios

Calculate:

```text
Material Cost / Revenue
Power & Fuel / Revenue
Employee Cost / Revenue
Freight / Revenue
Chemical Cost / Revenue
Subcontracting / Revenue
```

Analyze both absolute cost and cost intensity.

---

# 10. Textile Spread Analysis

This is a core sector-specific engine.

For commodity-oriented businesses calculate:

```text
Raw Material Price
        ↓
Yarn / Fabric Realization
        ↓
SPREAD
        ↓
Gross Margin
        ↓
EBITDA Margin
        ↓
CFO
```

Examples:

```text
Yarn Spread = Yarn Realization/kg - Fibre/Cotton Input Cost/kg

Fabric Spread = Fabric Realization/meter - Major Input Cost/meter

Garment Contribution = Garment ASP - Direct Material - Direct Conversion Cost
```

Use company-specific definitions where disclosed.

Flag earnings that depend on unusually high temporary spreads. The reference framework explicitly defines the textile cycle as:

**Raw-material price → Product realization → Spread → Utilization → Margin → Cash flow.** fileciteturn18file2L423-L431

---

# 11. Margin Analysis

Track:

- Gross margin
- EBITDA margin
- EBIT margin
- PAT margin
- Material cost %
- Employee cost %
- Power & fuel %
- Freight %
- Other operating cost %

Analyze:

```text
Margin Change
= Price
+ Volume
+ Mix
+ Raw Material
+ Energy
+ Labour
+ Operating Leverage
+ FX
+ Other
```

Flag:

- Margin expansion without volume support
- Margin expansion solely from commodity deflation
- Margin compression despite realization growth
- Rising employee cost intensity
- Rising power/fuel intensity
- High other-income dependence

---

# 12. Unit Economics

Where data permits, calculate:

### Spinning

- Revenue/kg
- EBITDA/kg
- EBITDA/tonne
- Power cost/kg
- Employee cost/kg

### Weaving

- Revenue/meter
- EBITDA/meter
- Power cost/meter

### Processing

- Revenue/meter
- EBITDA/meter
- Processing cost/meter

### Garments

- Revenue/piece
- Gross profit/piece
- EBITDA/piece
- Labour cost/piece

### Branded Apparel

- Revenue/store
- Revenue/sq ft
- EBITDA/store
- Gross margin
- Inventory/store

The reference framework specifically calls for EBITDA/tonne, EBITDA/kg, gross margin, EBITDA margin and EBIT margin. fileciteturn18file2L406-L412

---

# 13. Working Capital

Track:

- Inventory days
- Receivable days
- Payable days
- Cash Conversion Cycle
- Raw-material inventory
- Work-in-progress
- Finished goods inventory
- Export receivables
- Advances

Calculate:

```text
CCC = Inventory Days + Receivable Days - Payable Days
```

Investigate:

- Inventory build-up
- Finished-goods accumulation
- Slow-moving inventory
- Receivables increasing faster than sales
- Customer concentration
- Export receivable stress
- Payables stretching

The reference framework specifically identifies inventory days, receivable days, payable days, CCC, finished goods inventory and raw-material inventory. fileciteturn18file2L414-L422

---

# 14. Inventory Intelligence

Separate:

```text
Raw Material
WIP
Finished Goods
```

Analyze:

- Inventory days
- Inventory turnover
- Inventory growth vs sales growth
- Inventory growth vs volume
- Ageing
- Obsolescence
- Commodity inventory gains/losses
- Working capital locked in inventory

Flag:

```text
Inventory Growth > Revenue Growth
```

especially when accompanied by:

- Lower utilization
- Falling realizations
- Lower cash flow
- Margin pressure

---

# 15. Export Intelligence

For export-oriented businesses track:

- Export revenue
- Export share
- Export growth
- Geography
- Customer concentration
- Currency exposure
- Hedging
- Export receivables
- Freight
- Order book
- New customer additions
- Regulatory/trade exposure

Separate:

```text
Underlying Export Demand
vs
FX Translation Benefit
```

---

# 16. Capex and Capacity-Cycle Analysis

Track:

- Existing capacity
- New capacity
- Capex announced
- Capex spent
- CWIP
- Commissioning date
- Capacity addition
- Expected utilization
- Expected realization
- Funding source
- Expected ROCE

Calculate:

```text
Incremental Revenue / Incremental Capital
Incremental EBITDA / Incremental Capital
```

Flag:

- Capacity additions during weak demand
- Debt-funded expansion with weak cash generation
- Delayed commissioning
- Cost overruns
- Low post-commissioning utilization
- Poor incremental returns

---

# 17. Fixed-Asset Efficiency

Track:

- Asset turnover
- Fixed asset turnover
- Capacity utilization
- ROCE
- ROIC
- Incremental ROCE
- Capex intensity

Analyze:

```text
Capex
 ↓
Capacity
 ↓
Utilization
 ↓
Revenue
 ↓
EBITDA
 ↓
CFO
 ↓
ROCE
```

---

# 18. Cash Flow Analysis

Core metrics:

```text
CFO
FCF
CFO/PAT
FCF/PAT
Capex/Revenue
Capex/CFO
Net Debt/EBITDA
```

Analyze:

- PAT vs CFO
- CFO vs EBITDA
- Inventory-driven cash flow
- Receivable-driven cash flow
- Capex intensity
- Debt-funded capex
- Dividend sustainability

Flag:

- PAT growth without CFO growth
- Persistent negative FCF
- Rising debt during weak cash generation
- Working-capital-driven cash deterioration

---

# 19. Balance Sheet

Track:

- Debt
- Net debt
- Debt/equity
- Net debt/EBITDA
- Interest coverage
- Current ratio
- Working capital
- CWIP
- Contingent liabilities
- Guarantees
- Related-party balances

Key diagnostic:

```text
Growth Quality
=
Revenue Growth
+
EBITDA Growth
+
CFO Growth
+
Balance Sheet Sustainability
```

A high-growth company with rapidly increasing leverage should be analyzed differently from an internally funded grower.

---

# 20. ROCE / ROIC

Calculate:

```text
ROCE
ROIC
Incremental ROCE
Incremental ROIC
```

Decompose:

```text
ROIC
=
Operating Margin
×
Capital Turnover
```

Investigate whether returns are improving because of:

- Higher margins
- Better utilization
- Better asset turnover
- Lower working capital
- Temporary commodity spreads

---

# 21. Management and Capital Allocation

Evaluate:

- Capacity expansion discipline
- Capex discipline
- Debt management
- Dividend policy
- Buybacks
- Acquisitions
- Working-capital discipline
- Related-party transactions
- Promoter transactions
- Promoter pledge
- Capital raising
- Subsidiary investments
- Project execution

Ask:

> Is management converting the textile cycle into durable shareholder value, or merely benefiting from a temporary upcycle?

---

# 22. Concall Intelligence

Extract management statements on:

- Demand
- Volume
- Realizations
- Capacity utilization
- Cotton/raw-material outlook
- Yarn/fabric spread
- Export demand
- Domestic demand
- Order book
- Capex
- Capacity commissioning
- Margin outlook
- Working capital
- Inventory
- Debt
- FX
- Customer additions
- Product mix
- Guidance

Maintain:

```text
GUIDANCE
   ↓
ACTUAL
   ↓
VARIANCE
   ↓
MANAGEMENT EXPLANATION
```

Classify guidance as:

```text
POSITIVE
NEUTRAL
NEGATIVE
MIXED
UNCERTAIN
```

Do not infer management intent from tone alone. Store the actual statement, period, metric and source.

---

# 23. Competitive Advantage

Evaluate:

- Cost position
- Scale
- Integrated operations
- Product quality
- Customer relationships
- Certifications
- Export relationships
- Brand
- Distribution
- Design capability
- Technical know-how
- Manufacturing efficiency
- Capacity scale
- Switching costs
- Customer concentration risk

For commodity textile companies, distinguish:

```text
Structural Cost Advantage
vs
Temporary Commodity Advantage
```

---

# 24. Supply-Demand and Cycle Analysis

Textiles should be analyzed as a cycle-sensitive industry.

Track:

- Global capacity
- Domestic capacity
- New capacity additions
- Demand growth
- Export demand
- Inventory levels
- Utilization
- Raw-material prices
- Product realizations
- Spreads
- Freight
- Currency

Cycle model:

```text
Weak Demand
    ↓
Inventory Reduction
    ↓
Capacity Discipline
    ↓
Utilization Recovery
    ↓
Realization Improvement
    ↓
Spread Expansion
    ↓
Margin Expansion
    ↓
Capex / Capacity Additions
    ↓
Oversupply Risk
    ↓
Margin Normalization
```

The engine should identify where the company is within this cycle.

---

# 25. Growth Quality

Decompose growth into:

```text
Organic Growth
Volume Growth
Price Growth
Mix Growth
Capacity Growth
Market Share Growth
Export Growth
Acquisition Growth
```

Classify growth as:

- Structural
- Cyclical
- Capacity-led
- Price-led
- FX-led
- Acquisition-led
- Market-share-led

Do not treat cyclical price increases as equivalent to structural growth.

---

# 26. Peer Comparison

Peer selection must consider:

1. Same industry
2. Similar business model
3. Similar product mix
4. Similar geography
5. Similar capital intensity
6. Similar export exposure
7. Similar size

Compare:

- Revenue growth
- Volume growth
- Realization
- Utilization
- Gross margin
- EBITDA margin
- EBIT margin
- Inventory days
- Receivable days
- CCC
- ROCE
- ROIC
- CFO/PAT
- FCF/PAT
- Debt/equity
- Net debt/EBITDA
- Valuation

Avoid comparing branded apparel economics directly with commodity spinning economics.

---

# 27. Valuation

Keep valuation separate from business-quality analysis.

Potential metrics:

- P/E
- EV/EBITDA
- P/B
- EV/Sales
- FCF Yield
- Dividend Yield
- EV/Capacity where meaningful
- Market Cap/Installed Capacity where meaningful

For cyclical textile businesses, use normalized earnings.

```text
Normalized EBITDA
Normalized EBIT
Normalized PAT
```

Do not value a cyclical business purely on peak earnings.

---

# 28. Historical Valuation

Track:

- Current P/E
- 3Y median P/E
- 5Y median P/E
- 10Y median P/E
- Current EV/EBITDA
- Historical EV/EBITDA
- P/B history
- FCF yield history

Overlay valuation with:

- EBITDA margin
- Utilization
- Spread
- ROCE
- CFO
- Debt

The system should answer:

> Is the current valuation being supported by sustainable earnings or peak-cycle earnings?

---

# 29. Causal Analysis Engine

Every important change should produce a causal explanation.

Example:

```text
EBITDA Margin ↑
      ↓
Realization ↑
      ↓
Cotton Cost ↓
      ↓
Yarn Spread ↑
      ↓
Utilization ↑
      ↓
Operating Leverage ↑
```

Another example:

```text
CFO ↓
   ↓
Inventory ↑
   ↓
Finished Goods ↑
   ↓
Sales Growth ↓
   ↓
Utilization ↓
```

Every causal chain should identify:

- Metric
- Direction
- Magnitude
- Driver
- Supporting evidence
- Source
- Confidence

---

# 30. Positive Signals

Potential positive signals:

- Volume growth
- Sustainable realization improvement
- Utilization improvement
- Stable/improving spreads
- Lower material-cost intensity
- Better product mix
- Higher value-added share
- Export diversification
- Market-share gains
- Strong order book
- Healthy inventory
- Improving CFO
- Positive FCF
- Deleveraging
- High incremental ROCE
- Disciplined capex
- Capacity additions backed by demand

Signals must be evidence-based and should not be treated as guarantees.

---

# 31. Red Flags

Flag:

### Demand

- Volume decline
- Order-book deterioration
- Export slowdown
- Customer concentration

### Costs

- Raw-material inflation
- Power/fuel inflation
- Freight inflation
- Labour-cost pressure

### Operations

- Falling utilization
- Capacity under-absorption
- Project delays
- Cost overruns

### Working Capital

- Inventory build
- Receivable build
- Rising CCC
- Finished-goods accumulation

### Balance Sheet

- Rising leverage
- Weak interest coverage
- Debt-funded losses
- Frequent equity dilution

### Governance

- Related-party transactions
- Promoter pledge
- Aggressive accounting
- Unexplained auditor changes
- Contingent liabilities

### Cycle

- Peak spreads
- Peak margins
- Aggressive capacity expansion
- Industry oversupply

---

# 32. Scenario Analysis

Build:

## Bull Case

Assumptions:

- Strong demand
- Higher utilization
- Better realization
- Stable/strong spreads
- Lower input costs
- Better product mix
- Operating leverage

## Base Case

Assumptions:

- Normal demand
- Normal utilization
- Normal spreads
- Planned capacity additions
- Normal margins

## Bear Case

Assumptions:

- Demand slowdown
- Lower utilization
- Commodity inflation
- Spread compression
- Margin pressure
- Higher working capital
- Higher interest costs
- Export weakness

Calculate scenario impact on:

- Revenue
- EBITDA
- EBIT
- PAT
- CFO
- FCF
- ROCE
- ROIC
- Net debt
- Valuation

These scenario dimensions follow the broader Consumer Discretionary framework. fileciteturn18file3L531-L561

---

# 33. Scoring Architecture

Do not use a single generic score.

Suggested Textiles dimensions:

| Dimension | Suggested Weight |
|---|---:|
| Business Quality | 10% |
| Demand & Growth Quality | 15% |
| Volume / Realization / Mix | 10% |
| Cycle & Spread Position | 15% |
| Operating Quality | 10% |
| Cash Flow Quality | 10% |
| Balance Sheet | 10% |
| Capital Efficiency | 10% |
| Competitive Position | 5% |
| Management & Governance | 5% |

**Valuation should remain a separate decision-support layer**, rather than allowing cheap valuation to compensate for weak business quality.

Within textiles, weights may vary by business model:

- Spinning → spread, utilization, raw material and cycle
- Weaving → utilization, realization and product mix
- Processing → value addition, utilization and cost control
- Garments → volume, ASP, customers and execution
- Home textiles → export demand, utilization and customer concentration
- Technical textiles → value-added mix, growth and competitive differentiation
- Branded apparel → brand strength, store economics, inventory and demand

---

# 34. Metric Classification

Every metric must be tagged:

```text
CORE
SUPPORTING
DIAGNOSTIC
SECTOR_SPECIFIC
VALUATION
PRESENTATION
```

Core metrics should drive the fundamental assessment.

Diagnostic metrics should activate when a condition occurs.

Sector-specific metrics should not become universal missing-data failures. fileciteturn18file6L1248-L1288

---

# 35. Data Quality

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

Allowed data types:

```text
REPORTED
CALCULATED
ESTIMATED
MANAGEMENT-DISCLOSED
THIRD-PARTY
```

Confidence:

```text
HIGH
MEDIUM
LOW
```

Calculated metrics must retain their underlying inputs.

Example:

```text
EBITDA/kg
=
EBITDA / Production Volume
```

Store:

- EBITDA
- Production
- Period
- Formula
- Source of each input
- Confidence

The source framework explicitly requires metric lineage and warns against silently mixing reported, calculated and estimated values. fileciteturn18file3L598-L631

---

# 36. Source Hierarchy

Preferred order:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings / Concall Transcript
5. NSE/BSE filings
6. Regulatory filings
7. Company investor-relations website
8. Reliable financial databases
9. Third-party research

For textile operating metrics, prioritize company disclosures and exchange/regulatory filings. Third-party data must not silently override company-reported data. fileciteturn18file3L635-L651

For commodity/reference data, store the external source separately and preserve the date.

---

# 37. Agent Architecture

```text
Company Identification Agent
          ↓
Industry Classification Agent
          ↓
Financial Data Agent
          ↓
Textile KPI Agent
          ↓
Demand Agent
          ↓
Volume / Price / Mix Agent
          ↓
Raw Material & Spread Agent
          ↓
Capacity / Utilization Agent
          ↓
Working Capital Agent
          ↓
Capex / Asset Efficiency Agent
          ↓
Cash Flow Agent
          ↓
Management / Concall Agent
          ↓
Competitive Advantage Agent
          ↓
Peer Comparison Agent
          ↓
Cycle Analysis Agent
          ↓
Historical Valuation Agent
          ↓
Valuation Agent
          ↓
Causal Analysis Agent
          ↓
Red Flag Agent
          ↓
Scoring Agent
          ↓
Final Fundamental Analysis
```

The broader architecture follows the existing Consumer Discretionary framework's pipeline from company identification through classification, financial/KPI analysis, demand, working capital, capex, cash flow, management, competitive advantage, peers, valuation, red flags, causal analysis and final thesis. fileciteturn18file3L655-L691

---

# 38. Recommended Database Structure

## Company

```text
company_id
company_name
macro_sector
sector
industry
sub_industry
business_model
market_cap
market_status
```

## Textile Operating Metrics

```text
company_id
period
metric_id
metric_name
value
unit
business_model
source
confidence
```

Examples:

```text
production_volume
sales_volume
capacity
utilization
realization_per_kg
realization_per_meter
garment_asp
export_share
domestic_share
product_mix
order_book
```

## Raw Material

```text
company_id
period
input_name
input_price
unit
source
```

## Spread

```text
company_id
period
spread_name
spread_value
formula
input_metric_ids
confidence
```

## Guidance

```text
company_id
period
metric
guidance
actual
variance
management_explanation
source
sentiment
confidence
```

## Cycle

```text
company_id
period
cycle_indicator
value
cycle_phase
confidence
```

---

# 39. Data Coverage Dashboard

For every company display:

```text
Textile KPI Coverage
────────────────────────────
Production             ✓
Capacity               ✓
Utilization            ✓
Realization            ✓
Raw Material           ✓
Spread                 ?
Export Share           ✓
Order Book             ?
Inventory              ✓
CFO                    ✓
Capex                  ✓
ROCE                   ✓
Concall Guidance       ✓
```

Never convert missing data into zero.

Show:

- Available
- Calculable
- Partial
- Missing input
- Source required
- Not applicable
- Invalid

The ratio implementation framework explicitly recommends this coverage model and a source-gap report to identify which raw inputs/data agents are required to close gaps. fileciteturn18file1L223-L265

---

# 40. Final Screener Output

The final company report should contain:

## A. Business Snapshot

- Company
- Textile business model
- Products
- Geography
- Domestic/export mix
- Capacity
- Utilization

## B. Growth

- Revenue growth
- Volume growth
- Realization growth
- Mix
- Capacity growth
- Market-share indicators

## C. Textile Operating Dashboard

- Production
- Capacity
- Utilization
- Realization
- Raw-material cost
- Spread
- Export share
- Order book

## D. Profitability

- Gross margin
- EBITDA margin
- EBIT margin
- PAT margin
- EBITDA/kg or relevant unit economics

## E. Working Capital

- Inventory days
- Receivable days
- Payable days
- CCC

## F. Cash Flow

- CFO
- FCF
- CFO/PAT
- FCF/PAT

## G. Balance Sheet

- Debt
- Net debt
- D/E
- Net debt/EBITDA
- Interest coverage

## H. Returns

- ROCE
- ROIC
- Incremental ROCE

## I. Cycle Position

```text
Raw Material
Spread
Utilization
Margins
Capacity
Demand
```

## J. Management

- Guidance
- Capex
- Strategy
- Capital allocation
- Governance

## K. Peer Comparison

Compare only relevant textile peers.

## L. Valuation

Show:

- Current valuation
- Historical valuation
- Peer valuation
- Normalized earnings

## M. Causal Explanation

Answer:

> **WHY did earnings, margins, cash flow and returns change?**

## N. Risks

Show evidence-backed red flags.

## O. Data Confidence

Show:

```text
Overall Data Confidence
High / Medium / Low
```

and identify missing critical metrics.

---

# 41. Implementation Principles

1. **Do not treat all textile companies as identical.**
2. Classify business model before selecting KPIs.
3. Separate volume, price and mix.
4. Track capacity and utilization.
5. Track raw-material prices and spreads.
6. Separate cyclical earnings from structural earnings.
7. Track inventory carefully.
8. Separate accounting profit from cash generation.
9. Normalize earnings before valuing cyclical companies.
10. Preserve source lineage for every calculated metric.
11. Never treat missing data as zero.
12. Do not let valuation override business-quality analysis.
13. Use management guidance as a trackable dataset, not narrative text alone.
14. Explain changes causally rather than presenting isolated ratios.
15. Compare companies only with economically relevant peers.
16. Show data-confidence limitations whenever critical inputs are unavailable.

The broader ratio architecture also requires unique metric IDs, formulas, dependency lists, validity rules, source priority, coverage status and lineage for each metric. fileciteturn18file1L223-L265

---

# 42. Central Fundamental Question

The Textile analysis engine should ultimately answer:

> **Is this company's earnings growth being driven by sustainable demand, volume, pricing, product mix, competitive advantage and efficient capital deployment — or is it primarily the result of a temporary textile-cycle spread, favorable input prices or peak utilization?**

That question should connect the entire analysis:

```text
Demand
  ↓
Volume
  ↓
Realization
  ↓
Mix
  ↓
Utilization
  ↓
Raw Material
  ↓
Spread
  ↓
Margins
  ↓
Working Capital
  ↓
Cash Flow
  ↓
Capex
  ↓
ROCE / ROIC
  ↓
Balance Sheet
  ↓
Competitive Position
  ↓
Cycle Normalization
  ↓
Valuation
```
