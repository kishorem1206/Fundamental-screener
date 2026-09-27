# Metals & Mining — Fundamental Analysis Framework

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
**Sector:** Metals & Mining  
**Parent Macro Sector:** Commodities

## 1. Purpose

This framework is a standalone analysis engine for companies classified under **Metals & Mining**.

The sector includes:

- Minerals & Mining
- Non - Ferrous Metals
- Metals & Minerals Trading
- Diversified Metals
- Ferrous Metals

The engine must analyze metals and mining businesses through their actual economic drivers rather than relying only on generic financial ratios.

Core philosophy:

> **RESERVES / RESOURCES → CAPACITY → PRODUCTION → VOLUME → REALIZATION / METAL PRICE → COST CURVE → EBITDA → CASH FLOW → CAPEX → ROCE / ROIC → BALANCE SHEET → VALUATION**

A metals company should be understood as a combination of:

- Commodity exposure
- Resource quality
- Production capacity
- Volume growth
- Realization / benchmark price
- Cost position
- Energy and input costs
- Operating leverage
- Capital intensity
- Balance-sheet leverage
- Free cash flow
- Commodity-cycle position

Do not treat a temporary commodity-price spike as structural earnings growth.

---

# 2. Industry Coverage

## 2.1 Minerals & Mining

Analyze companies engaged in extraction and processing of mineral resources.

Track:

- Mineral type
- Reserves
- Resources
- Mine life
- Production capacity
- Actual production
- Dispatch / sales volume
- Grade
- Recovery
- Stripping ratio where relevant
- Realization
- Benchmark commodity price
- Cost per unit
- Royalties
- Mining rights
- Exploration expenditure
- New mine development
- Expansion projects
- Regulatory permissions

Primary economic chain:

> **Resource → Mine Capacity → Production → Grade / Recovery → Realization → Cash Cost → EBITDA → FCF**

---

## 2.2 Ferrous Metals

Includes businesses exposed primarily to:

- Iron ore
- Steel
- Pig iron
- Long products
- Flat products
- Stainless / alloy steel where classified accordingly

Track:

- Crude steel capacity
- Finished steel capacity
- Production
- Sales volume
- Capacity utilization
- Realization per tonne
- EBITDA per tonne
- Coking coal consumption
- Iron ore integration
- Scrap consumption
- Energy cost
- Freight cost
- Product mix
- Domestic vs export sales

Core formula:

```text
EBITDA / Tonne =
EBITDA / Sales Volume
```

Analyze EBITDA/tonne across the commodity cycle rather than using only the latest quarter.

---

## 2.3 Non - Ferrous Metals

Includes exposure to metals such as:

- Aluminium
- Copper
- Zinc
- Lead
- Nickel
- Other non-ferrous metals where applicable

Track:

- Metal production
- Sales volume
- Capacity
- Capacity utilization
- Metal realization
- LME-linked pricing
- Domestic premium
- Treatment / refining charges
- Power cost
- Raw-material cost
- By-product contribution
- Integrated vs non-integrated production

Key causal chain:

> **LME / Benchmark Price → Realization → Revenue → Unit Margin → EBITDA → CFO → FCF**

---

## 2.4 Metals & Minerals Trading

Trading businesses must be analyzed differently from integrated miners and manufacturers.

Track:

- Trading volume
- Average selling price
- Average purchase price
- Trading margin
- Inventory
- Inventory turnover
- Working capital
- Supplier concentration
- Customer concentration
- Credit terms
- Commodity exposure
- Hedging
- Counterparty risk
- Geographic exposure

Key metric:

```text
Trading Margin =
Trading Revenue - Cost of Goods Sold
```

Also track:

```text
Trading Margin / Tonne
Trading Margin %
```

Do not compare trading margins directly with integrated metal producers without adjusting for business model.

---

## 2.5 Diversified Metals

For diversified metal groups, analyze each major business separately.

Required segmentation:

- Commodity
- Geography
- Production
- Capacity
- Revenue
- EBITDA
- EBITDA/tonne
- Capex
- ROCE / ROIC
- Net debt

Calculate:

```text
Segment EBITDA Contribution %
=
Segment EBITDA / Consolidated EBITDA
```

The engine must identify whether earnings are:

- Diversified across commodities
- Dominated by one commodity
- Dominated by one geography
- Dependent on one large asset

---

# 3. Business Model Classification

Every company must be classified before analysis.

Required fields:

```text
macro_sector
sector
industry
sub_industry
business_model
commodity
product
integrated_model
mining_exposure
manufacturing_exposure
trading_exposure
domestic_export_mix
geography
asset_intensity
capital_intensity
capacity
capacity_utilization
production_volume
recurring_revenue_percent
customer_concentration
```

Business models may include:

- Integrated mining
- Mining-only
- Mining + processing
- Integrated steel
- Aluminium production
- Copper production
- Zinc / lead production
- Metal manufacturing
- Metal trading
- Mineral trading
- Recycling
- Diversified metals
- Export-oriented producer
- Domestic producer

---

# 4. Data Periods

Maintain:

### Annual

- Current FY
- 3Y history
- 5Y history
- 10Y history

### Quarterly

- Latest quarter
- Previous quarter
- YoY quarter
- 8-quarter history
- 12-quarter history where available

### TTM

```text
TTM = Latest Four Reported Quarters
```

### Operating Periods

Where available:

- Monthly production
- Monthly dispatch
- Commodity price
- LME price
- Domestic benchmark price
- Capacity utilization
- Realization

Every metric must retain:

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
sector
industry
commodity
```

Allowed data types:

- REPORTED
- CALCULATED
- ESTIMATED
- MANAGEMENT_DISCLOSED
- THIRD_PARTY

---

# 5. Commodity Price Analysis

Commodity price is one of the most important external drivers.

Track:

- Current benchmark price
- 1Y average
- 3Y average
- 5Y average
- 10Y average where available
- Current vs historical average
- High / low
- Price volatility
- Domestic premium / discount
- Export realization
- Currency effect

Calculate:

```text
Price Premium / Discount =
Company Realization / Benchmark Price - 1
```

Analyze:

- Is the company benefiting from high commodity prices?
- Is the current price above its long-term cycle average?
- Is earnings growth primarily price-driven?
- Is volume also increasing?
- Is realization improving because of product mix?
- How sensitive is EBITDA to commodity prices?

---

# 6. Production & Volume Analysis

Track:

- Installed capacity
- Production
- Sales volume
- Dispatch
- Capacity utilization
- Production growth
- Sales growth
- Production-to-capacity ratio
- Expansion capacity
- Commissioning timeline

Calculate:

```text
Capacity Utilization =
Actual Production / Installed Capacity
```

and:

```text
Production Growth %
=
Current Production / Prior Production - 1
```

Separate:

- Volume growth
- Price growth
- Mix growth

Revenue growth should be decomposed into:

```text
Revenue Growth
=
Volume Effect
+
Price Effect
+
Mix Effect
+
Currency Effect
```

---

# 7. Realization Analysis

Track:

- Revenue per tonne
- Average selling price
- Realization per unit
- Benchmark commodity price
- Domestic premium
- Export realization
- Product mix

Calculate:

```text
Realization / Tonne =
Metal Revenue / Sales Volume
```

Analyze whether realization changes are caused by:

- Commodity prices
- Product mix
- Geography
- Customer mix
- Premium products
- Currency

Do not interpret realization growth automatically as pricing power.

---

# 8. Cost Curve Analysis

Cost position is critical for cyclical commodity businesses.

Track:

- Raw material cost
- Energy cost
- Power cost
- Fuel cost
- Employee cost
- Freight
- Royalty
- Mining cost
- Conversion cost
- Maintenance cost
- Other operating costs

Calculate where possible:

```text
Cash Cost / Tonne
Conversion Cost / Tonne
Energy Cost / Tonne
Raw Material Cost / Tonne
EBITDA / Tonne
```

Analyze the company against:

- Historical cost position
- Peer cost position
- Industry cost curve

Important question:

> Does the company remain economically viable when commodity prices normalize?

---

# 9. Margin Analysis

Track:

- Gross margin
- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- PAT
- PAT margin
- EBITDA/tonne
- EBIT/tonne

Analyze:

```text
EBITDA Change
=
Volume Effect
+
Realization Effect
+
Raw Material Effect
+
Energy Effect
+
Operating Leverage
+
Other Effects
```

Separate:

- Structural margin improvement
- Commodity-price-driven margin improvement
- Cost-driven improvement
- Mix-driven improvement
- One-time benefit

---

# 10. Operating Leverage

Metals businesses can exhibit significant operating leverage.

Analyze:

- Capacity utilization
- Fixed cost base
- Production growth
- Revenue growth
- EBITDA growth

Flag situations where:

```text
Revenue Growth < EBITDA Growth
```

and determine whether this is caused by:

- Operating leverage
- Commodity-price increase
- Cost reduction
- Product mix

Also flag the reverse situation:

```text
Revenue Growth > EBITDA Growth
```

when caused by:

- Cost inflation
- Weak realization
- Lower utilization
- Adverse mix

---

# 11. Reserves, Resources & Mine Life

For mining companies, assess:

- Proven reserves
- Probable reserves
- Measured resources
- Indicated resources
- Inferred resources
- Mine life
- Annual production
- Reserve replacement
- Exploration success
- Ore grade
- Recovery rate

Calculate where possible:

```text
Reserve Life =
Recoverable Reserves / Current Annual Production
```

Do not treat resources as equivalent to economically mineable reserves.

Flag:

- Short reserve life
- Declining grades
- Poor reserve replacement
- Regulatory uncertainty
- Dependence on one mine

---

# 12. Capacity Expansion

Track:

- Existing capacity
- Capacity additions
- Expansion capex
- Project cost
- Project timeline
- Commissioning date
- Expected utilization
- Expected EBITDA contribution

Calculate:

```text
Capacity Growth %
=
Future Capacity / Current Capacity - 1
```

Analyze whether expansion is:

- Demand-backed
- Commodity-cycle-driven
- Strategically integrated
- Acquisition-led
- Debt-funded

Flag aggressive expansion during unusually high commodity prices.

---

# 13. Capital Expenditure

Track:

- Total capex
- Maintenance capex
- Growth capex
- Expansion capex
- Sustaining mining capex
- Environmental capex
- Exploration capex
- Capex/revenue
- Capex/depreciation

Calculate:

```text
Capex / Revenue
Capex / EBITDA
FCF after Growth Capex
```

Separate:

```text
Maintenance Capex
vs
Growth Capex
```

A company generating high EBITDA but requiring continuous heavy capex should not be treated as equivalent to an asset-light business.

---

# 14. Working Capital

Track:

- Inventory
- Receivables
- Payables
- Inventory days
- Receivable days
- Payable days
- Cash conversion cycle
- Working capital/revenue

Calculate:

```text
CCC =
Inventory Days + Receivable Days - Payable Days
```

For trading businesses, inventory and working capital deserve additional emphasis.

Flag:

- Inventory buildup without volume growth
- Receivables growing faster than revenue
- Falling payable days
- Cash trapped in working capital
- Large commodity inventory losses

---

# 15. Cash Flow Analysis

Track:

- CFO
- EBITDA
- CFO/EBITDA
- CFO/PAT
- Capex
- FCF
- FCF margin
- FCF/PAT
- FCF after growth capex
- Dividend
- Buybacks
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

Analyze cash flow across the commodity cycle.

Important question:

> Does reported accounting profit translate into cash through a normalized commodity cycle?

---

# 16. Balance Sheet

Track:

- Gross debt
- Net debt
- Cash
- Net debt/EBITDA
- Debt/equity
- Interest cost
- Interest coverage
- Lease liabilities
- Contingent liabilities
- Guarantees
- Capital commitments

Calculate:

```text
Net Debt =
Gross Debt - Cash & Cash Equivalents
```

and:

```text
Net Debt / EBITDA
```

Analyze leverage at:

- Current commodity price
- Normalized commodity price
- Down-cycle EBITDA

A balance sheet that appears strong at peak-cycle EBITDA may become highly leveraged when commodity prices normalize.

---

# 17. Return on Capital

Track:

- ROE
- ROCE
- ROIC
- Asset turnover
- Fixed asset turnover
- Capital turnover

ROCE/ROIC should be evaluated across the cycle.

Analyze:

```text
ROIC
vs
Cost of Capital
```

and:

```text
ROCE Trend
vs
Commodity Cycle
```

Flag companies where high ROCE is mainly caused by temporarily elevated commodity prices.

---

# 18. Integration Analysis

For integrated metal businesses, identify:

- Captive mines
- Captive power
- Processing
- Smelting
- Refining
- Logistics
- Downstream products

Estimate where data permits:

```text
Integrated Cost Advantage
=
Peer Cost / Tonne - Company Cost / Tonne
```

Do not assume integration automatically creates superior economics.

Test whether integration actually results in:

- Lower costs
- Better utilization
- Better margins
- Lower supply risk
- Higher ROIC

---

# 19. Commodity Sensitivity

Estimate earnings sensitivity to commodity prices.

Where sufficient data exists:

```text
EBITDA Sensitivity =
Change in EBITDA / Change in Commodity Price
```

Track sensitivity to:

- Metal prices
- Energy prices
- Coking coal
- Iron ore
- Freight
- USD/INR

Classify exposure as:

- High
- Medium
- Low

These are exposure classifications, not investment ratings.

---

# 20. Currency Analysis

Track:

- Export revenue
- Import costs
- USD exposure
- Foreign currency debt
- Hedging
- Net FX exposure

Analyze:

```text
Net FX Exposure =
Foreign Currency Revenue - Foreign Currency Costs
```

Flag companies where:

- Revenue is USD-linked but costs are domestic
- Raw materials are USD-linked
- Debt is foreign-currency denominated
- FX gains materially affect reported profit

---

# 21. Management & Capital Allocation

Analyze:

- Expansion discipline
- Acquisition history
- Dividends
- Buybacks
- Debt reduction
- Capital allocation
- Related-party transactions
- Promoter holding
- Promoter pledge
- Dilution
- Auditor history
- Contingent liabilities
- Regulatory matters

Key questions:

- Does management expand capacity near cycle peaks?
- Are acquisitions value-accretive?
- Does management return excess cash?
- Does leverage rise aggressively during expansion?
- Are related-party transactions material?

---

# 22. Competitive Advantage

Assess evidence for:

- Low-cost assets
- High-grade reserves
- Long mine life
- Integrated operations
- Scale
- Logistics advantage
- Captive resources
- Technology
- Product specialization
- Customer relationships
- Geographic advantage
- Cost leadership

Separate:

```text
Structural Advantage
vs
Temporary Commodity Advantage
```

High margins during a commodity boom are not by themselves evidence of a durable moat.

---

# 23. Peer Comparison

Peers should be selected based on business model and commodity exposure.

Compare:

### Operating

- Production
- Capacity
- Utilization
- Realization
- EBITDA/tonne
- Cash cost/tonne
- Cost curve position

### Financial

- Revenue growth
- EBITDA growth
- EBITDA margin
- ROCE
- ROIC
- CFO conversion
- FCF

### Balance Sheet

- Net debt
- Net debt/EBITDA
- Interest coverage
- Capex intensity

### Valuation

- P/E
- EV/EBITDA
- P/B
- EV/Sales
- FCF yield
- Historical multiples

Do not compare a metal trader directly with an integrated producer without adjusting for business model.

---

# 24. Valuation

Valuation must account for cyclicality.

Use:

- P/E
- EV/EBITDA
- EV/EBIT
- P/B
- EV/Sales
- FCF yield
- EV/tonne where meaningful
- NAV / asset valuation where meaningful
- Replacement cost where relevant

For cyclical companies, use:

```text
Normalized Earnings
```

rather than simply:

```text
Current Peak Earnings
```

Analyze valuation against:

- Own historical multiple
- Peer multiple
- Normalized EBITDA
- Mid-cycle earnings
- Commodity-cycle position

Do not hard-code a universal P/E or EV/EBITDA threshold.

---

# 25. Historical Cycle Analysis

Maintain at least a 5–10 year history where data is available.

Track:

- Commodity price
- Revenue
- EBITDA
- EBITDA/tonne
- PAT
- CFO
- FCF
- ROCE
- Net debt
- Capex
- Production
- Capacity utilization

Identify:

- Peak cycle
- Trough cycle
- Mid-cycle
- Current position

The engine should answer:

> Is the company currently being valued on peak, mid-cycle or depressed earnings?

---

# 26. Growth Quality

Classify growth as:

### Volume-led

Production and sales volumes are increasing.

### Price-led

Commodity prices are driving revenue.

### Capacity-led

New capacity is driving growth.

### Mix-led

Higher-value products are increasing realization.

### Acquisition-led

Growth is primarily inorganic.

### Currency-led

FX movements materially affect reported growth.

### Cost-led

Profit growth is primarily driven by cost reduction.

The system should identify the dominant growth driver.

---

# 27. Positive Signals

Examples:

- Production growth with stable/improving cost position
- Capacity expansion with strong project economics
- Long reserve life
- Low-cost resource base
- Rising utilization
- Strong EBITDA/tonne
- Improving ROCE
- Strong CFO conversion
- FCF generation across the cycle
- Falling net debt
- Disciplined capex
- Successful downstream integration
- Strong balance sheet through the down-cycle

These are signals for analysis, not automatic investment conclusions.

---

# 28. Red Flags

Flag:

```text
COMMODITY_PEAK_DEPENDENCY
HIGH_COST_PRODUCER
SHORT_RESERVE_LIFE
DECLINING_ORE_GRADE
LOW_CAPACITY_UTILIZATION
AGGRESSIVE_CYCLE_PEAK_CAPEX
HIGH_NET_DEBT
HIGH_INTEREST_BURDEN
WEAK_CFO_CONVERSION
NEGATIVE_FCF
WORKING_CAPITAL_BUILD
INVENTORY_BUILD
CUSTOMER_CONCENTRATION
SUPPLIER_CONCENTRATION
REGULATORY_RISK
ENVIRONMENTAL_RISK
MINING_LICENSE_RISK
RELATED_PARTY_RISK
ACQUISITION_DEPENDENCY
ACCOUNTING_PROFIT_CASH_FLOW_MISMATCH
PEAK_MARGIN_VALUATION
```

---

# 29. Scenario Analysis

Build at least three scenarios:

## Down Cycle

Assumptions:

- Lower commodity prices
- Lower realization
- Lower utilization
- Normalized margins
- Higher relative leverage

Output:

- Revenue
- EBITDA
- PAT
- CFO
- FCF
- Net debt
- ROCE

## Base / Mid Cycle

Use normalized commodity prices and sustainable operating assumptions.

## Up Cycle

Assumptions:

- Higher commodity prices
- Higher utilization
- Strong realization
- Operating leverage

The engine must clearly distinguish scenario assumptions from reported data.

---

# 30. Causal Analysis Engine

The final analysis should follow:

```text
COMMODITY PRICE
      ↓
REALIZATION
      ↓
SALES VOLUME
      ↓
REVENUE
      ↓
UNIT COST
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

For mining:

```text
RESERVES
↓
MINE LIFE
↓
PRODUCTION
↓
GRADE / RECOVERY
↓
COST
↓
REALIZATION
↓
EBITDA
↓
FCF
```

For trading:

```text
VOLUME
↓
SPREAD / TRADING MARGIN
↓
WORKING CAPITAL
↓
CFO
↓
FCF
```

---

# 31. Scoring Architecture

Do not create one arbitrary score from dozens of ratios.

Maintain separate dimensions:

```text
BUSINESS QUALITY
COMMODITY / ASSET QUALITY
COST COMPETITIVENESS
GROWTH
OPERATING QUALITY
CASH FLOW QUALITY
BALANCE SHEET
CAPITAL EFFICIENCY
MANAGEMENT / GOVERNANCE
VALUATION
RISK
```

Each dimension should retain:

- Metric
- Value
- Historical trend
- Peer comparison
- Data confidence
- Interpretation

Valuation should remain separate from business-quality assessment.

---

# 32. Data Quality

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
calculation_method
```

Confidence levels:

```text
HIGH
MEDIUM
LOW
```

Prioritize:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings / Concall Transcript
5. NSE / BSE filings
6. Regulatory filings
7. Company operational disclosures
8. Reliable financial databases
9. Third-party datasets

The system must not silently convert estimated commodity prices or management guidance into reported facts.

---

# 33. Agent Architecture

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
OPERATING DATA
        ↓
COMMODITY PRICE DATA
        ↓
PRODUCTION / CAPACITY ENGINE
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

# 34. Database Structure

Recommended tables:

```text
companies
company_classification
industry_mapping
commodity_prices
production_metrics
capacity_metrics
reserve_resource_metrics
realization_metrics
unit_cost_metrics
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

Every observation should preserve:

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

# 35. Final Screener Output

For every Metals & Mining company, generate:

## Company Snapshot

- Company
- Industry
- Commodity exposure
- Business model
- Market capitalization
- Geography
- Integrated / non-integrated

## Asset Quality

- Reserves
- Resources
- Mine life
- Grade
- Production
- Capacity

## Operating Quality

- Capacity utilization
- Realization
- Cost/tonne
- EBITDA/tonne
- Production growth

## Financial Quality

- Revenue growth
- EBITDA growth
- EBIT
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
- Asset turnover

## Commodity Cycle

- Current commodity price
- Historical average
- Cycle position
- Price sensitivity

## Valuation

- P/E
- EV/EBITDA
- P/B
- FCF yield
- Historical valuation
- Peer valuation
- Normalized earnings valuation

## Management

- Capital allocation
- Expansion
- Acquisitions
- Governance
- Concall signals

## Risks

- Commodity
- Cost
- Leverage
- Regulatory
- Environmental
- Reserve
- Execution

## Final Analytical Output

```text
BUSINESS QUALITY
ASSET QUALITY
COST POSITION
GROWTH ENGINE
OPERATING ENGINE
CASH ENGINE
BALANCE SHEET
CAPITAL EFFICIENCY
COMMODITY CYCLE POSITION
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

# 36. Implementation Principles

The Metals & Mining engine must follow:

```text
RAW DATA
→ VERIFIED DATA
→ NORMALIZATION
→ CALCULATED METRICS
→ UNIT ECONOMICS
→ TREND ANALYSIS
→ COMMODITY CYCLE ANALYSIS
→ PEER COMPARISON
→ CAUSAL ANALYSIS
→ RED FLAGS
→ SCENARIOS
→ VALUATION
→ FINAL FUNDAMENTAL THESIS
```

The most important implementation rule is:

> **Do not confuse commodity-cycle earnings with structural business quality.**

The engine should always distinguish:

```text
PRICE
vs
VOLUME
vs
MIX
vs
COST
vs
CAPACITY
vs
CAPITAL ALLOCATION
```

The central fundamental question for Metals & Mining is:

> **If commodity prices normalize, does the company's asset quality, cost position, balance sheet and cash generation still support an attractive long-term economic business?**
