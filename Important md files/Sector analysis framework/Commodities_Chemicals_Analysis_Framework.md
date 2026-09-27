# Chemicals — Fundamental Analysis Framework

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
**Sector:** Chemicals  
**Industries in this sector:**  
- Chemicals & Petrochemicals
- Fertilizers & Agrochemicals

**Classification source:** User-provided `Main sector divisions(1).csv` and `Sectoral classification(1).csv`.

---

## 1. Purpose

This is a standalone fundamental-analysis framework for companies classified as:

> **Commodities → Chemicals**

The framework covers both major industry groups under the sector:

1. **Chemicals & Petrochemicals**
2. **Fertilizers & Agrochemicals**

The engine must first identify the company's precise business model and product exposure before applying industry-specific metrics.

Core analytical chain:

```text
RAW MATERIAL / FEEDSTOCK
        ↓
CAPACITY
        ↓
UTILIZATION
        ↓
PRODUCTION / VOLUME
        ↓
REALIZATION / PRODUCT PRICE
        ↓
SPREAD / UNIT ECONOMICS
        ↓
INPUT COST
        ↓
EBITDA / UNIT
        ↓
CFO
        ↓
CAPEX
        ↓
FCF
        ↓
ROCE / ROIC
        ↓
BALANCE SHEET
        ↓
VALUATION
```

For chemicals, **product spreads, feedstock costs, capacity additions, utilization, product mix and global supply-demand** are often more informative than generic financial ratios alone.

---

# 2. Industry Mapping

## 2.1 Chemicals & Petrochemicals

Analyze companies across relevant chemical categories such as:

- Basic chemicals
- Specialty chemicals
- Performance chemicals
- Petrochemicals
- Intermediates
- Resins
- Polymers
- Solvents
- Industrial chemicals
- Electronic / advanced chemicals
- Custom manufacturing
- Contract manufacturing
- Chemical derivatives

The system must identify the actual products rather than assuming that every chemical company has the same economics.

Track:

- Product portfolio
- End markets
- Capacity
- Production
- Utilization
- Realization
- Product spreads
- Raw-material exposure
- Energy intensity
- Export exposure
- Customer concentration
- Geography
- Import competition
- New capacity

### Core causal chain

```text
END-MARKET DEMAND
↓
PRODUCT DEMAND
↓
VOLUME
↓
UTILIZATION
↓
PRODUCT PRICE
↓
RAW MATERIAL / FEEDSTOCK
↓
SPREAD
↓
EBITDA / UNIT
↓
CFO
↓
FCF
```

---

## 2.2 Fertilizers & Agrochemicals

Analyze companies across:

- Fertilizers
- Crop protection
- Agrochemicals
- Herbicides
- Insecticides
- Fungicides
- Plant-growth products
- Fertilizer intermediates
- Specialty agricultural inputs

Track:

- Product volumes
- Capacity
- Utilization
- Realization
- Raw materials
- Natural gas / energy exposure
- Phosphate / potash / ammonia exposure where applicable
- Channel inventory
- Dealer network
- Crop-cycle demand
- Monsoon dependence
- Export exposure
- Regulatory approvals
- Product registrations
- Molecule exposure

For fertilizers, distinguish:

```text
COMMODITY FERTILIZER
vs
SPECIALTY / VALUE-ADDED FERTILIZER
```

For agrochemicals, distinguish:

```text
DOMESTIC FORMULATION
vs
TECHNICAL / ACTIVE INGREDIENT
vs
EXPORT
vs
CONTRACT / CUSTOM MANUFACTURING
```

---

# 3. Business Model Classification

Before calculating sector metrics, classify each company.

Required fields:

```text
macro_sector
sector
industry
business_model
chemical_category
product_category
end_market
feedstock
raw_material
integrated_model
manufacturing_model
domestic_export_mix
geography
customer_type
customer_concentration
capacity
capacity_utilization
asset_intensity
capital_intensity
```

Possible business models:

```text
COMMODITY CHEMICAL
SPECIALTY CHEMICAL
PERFORMANCE CHEMICAL
PETROCHEMICAL
INTERMEDIATE
CONTRACT MANUFACTURING
CUSTOM MANUFACTURING
EXPORT ORIENTED
DOMESTIC FORMULATION
FERTILIZER
AGROCHEMICAL
TECHNICAL / ACTIVE INGREDIENT
DOWNSTREAM VALUE-ADDED
DIVERSIFIED CHEMICAL
```

---

# 4. Product Economics

The engine must create a product-level view wherever data is available.

For each major product:

```text
product
revenue
volume
realization
capacity
production
utilization
raw_material
raw_material_cost
energy_cost
selling_price
gross_margin
EBITDA
EBITDA_per_unit
geography
end_market
```

Calculate:

```text
Realization / Unit =
Product Revenue / Product Volume
```

and:

```text
EBITDA / Unit =
Product EBITDA / Product Volume
```

Where product-level EBITDA is unavailable, calculate company-level unit economics cautiously and mark the calculation as `CALCULATED`.

---

# 5. Capacity & Utilization

Track:

- Installed capacity
- Production capacity
- Actual production
- Sales volume
- Capacity additions
- Capacity under construction
- Planned capacity
- Brownfield expansion
- Greenfield expansion
- Acquired capacity
- Capacity utilization

Calculate:

```text
Capacity Utilization =
Production / Installed Capacity
```

and:

```text
Capacity Growth =
Future Capacity / Current Capacity - 1
```

Analyze:

- Is capacity being added faster than demand?
- Is utilization improving?
- Is the company operating below economic utilization?
- Is the new capacity replacing old capacity or adding incremental supply?
- Is industry capacity also expanding?

---

# 6. Volume Analysis

Track:

- Production volume
- Sales volume
- Export volume
- Domestic volume
- Product-level volume
- Volume growth
- Volume mix

Calculate:

```text
Volume Growth =
Current Volume / Prior Period Volume - 1
```

Separate:

```text
VOLUME GROWTH
vs
PRICE GROWTH
vs
MIX GROWTH
vs
CURRENCY EFFECT
```

A chemical company's revenue growth should not automatically be interpreted as demand growth.

---

# 7. Pricing & Realization

Track:

- Average selling price
- Realization per unit
- Product price
- Export realization
- Domestic realization
- Price increases
- Discounts
- Premium products
- Contract pricing
- Spot pricing

Calculate:

```text
Realization Growth =
Current Realization / Prior Realization - 1
```

Determine whether realization changes are caused by:

- Industry price movements
- Feedstock movements
- Product mix
- Geography
- Currency
- Customer mix
- Pricing power
- Temporary shortages

Important distinction:

> **Higher chemical prices are not automatically evidence of structural pricing power.**

---

# 8. Chemical Spread Analysis

For many chemical businesses, the spread between selling price and key input cost is a core economic metric.

Track:

- Product price
- Feedstock price
- Key raw-material price
- Energy price
- Freight
- Conversion cost

Calculate where data permits:

```text
Product Spread =
Product Realization - Key Feedstock / Raw Material Cost
```

For relevant businesses:

```text
Gross Spread / Unit
EBITDA / Unit
```

Track spread:

- Current
- 1Y
- 3Y
- 5Y
- Historical peak
- Historical trough

Analyze:

> Is margin expansion coming from sustainable efficiency or an unusually favorable spread?

---

# 9. Raw Material & Feedstock Analysis

Track major input exposure:

- Crude-linked feedstocks
- Natural gas
- Naphtha
- Benzene
- Toluene
- Propylene
- Ethylene
- Coal
- Power
- Minerals
- Phosphoric acid
- Ammonia
- Other company-specific inputs

For each major input:

```text
input
supplier
price
volume
cost
price sensitivity
domestic/imported
currency exposure
```

Calculate:

```text
Raw Material Cost / Revenue
```

and where meaningful:

```text
Raw Material Cost / Unit
```

Analyze pass-through:

```text
INPUT COST CHANGE
→
SELLING PRICE CHANGE
→
SPREAD CHANGE
→
MARGIN CHANGE
```

---

# 10. Energy Economics

Track:

- Electricity consumption
- Fuel consumption
- Natural gas
- Coal
- Steam
- Captive power
- Renewable power
- Energy efficiency

Calculate:

```text
Energy Cost / Revenue
Energy Cost / Unit
```

Flag:

```text
HIGH_ENERGY_INTENSITY
ENERGY_COST_PRESSURE
IMPORT_DEPENDENCE
LOW_PASS_THROUGH
```

For energy-intensive chemical plants, analyze whether the company has a structural cost advantage.

---

# 11. Specialty Chemical Analysis

Specialty chemicals require additional analysis beyond commodity spreads.

Track:

- Product complexity
- Number of products
- Customer qualification
- Product approval
- Qualification duration
- Customer stickiness
- Customization
- R&D
- IP
- Process know-how
- New product launches
- Export share
- Global customers

Classify revenue as:

```text
COMMODITY
SEMI-SPECIALTY
SPECIALTY
HIGHLY_CUSTOMIZED
```

Analyze:

> Is the company's margin protected by technical capability, customer qualification and switching costs, or merely by temporary supply-demand conditions?

---

# 12. Contract / Custom Manufacturing

For custom and contract manufacturers track:

- Customer count
- Customer concentration
- Products under development
- Products commercialized
- Qualification pipeline
- Development-to-commercial conversion
- Customer approvals
- Contract duration
- Repeat business
- Revenue from existing customers
- New customer revenue

Calculate where possible:

```text
Repeat Revenue %
=
Revenue from Existing Customers / Total Revenue
```

Flag:

- One-customer dependency
- Delayed approvals
- High R&D spending without commercialization
- Large pipeline without revenue conversion

---

# 13. Export & Geography

Track:

- Domestic revenue
- Export revenue
- Export %
- Geographic revenue
- Currency exposure
- Destination concentration
- Freight exposure
- Trade restrictions
- Tariffs
- Anti-dumping actions

Calculate:

```text
Export Revenue %
=
Export Revenue / Total Revenue
```

Analyze:

```text
EXPORT GROWTH
vs
GLOBAL DEMAND
vs
DOMESTIC DEMAND
vs
CURRENCY
```

Flag excessive dependence on one geography.

---

# 14. Customer Concentration

Track:

- Top customer %
- Top 5 customers %
- Industry concentration
- Geography concentration
- Related-party customers

Flag:

```text
HIGH_CUSTOMER_CONCENTRATION
SINGLE_CUSTOMER_DEPENDENCY
CUSTOMER_LOSS_RISK
```

For specialty chemicals, high customer concentration can be acceptable only if supported by long-term relationships and qualification barriers; the engine should report the evidence rather than assume it.

---

# 15. Demand & End-Market Analysis

Map revenue to end markets:

```text
AUTOMOTIVE
PHARMACEUTICAL
AGRICULTURE
CONSTRUCTION
TEXTILES
ELECTRONICS
CONSUMER
PACKAGING
INDUSTRIAL
ENERGY
OTHER
```

Track:

- End-market growth
- Revenue exposure
- Volume growth
- Customer demand
- Inventory cycle

Analyze:

> Is growth driven by a structurally growing end market or temporary inventory restocking?

---

# 16. Fertilizer-Specific Analysis

For fertilizer businesses track:

- Product type
- Nutrient content
- Production volume
- Sales volume
- Realization
- Subsidy exposure
- Subsidy receivables
- Raw-material costs
- Natural gas exposure
- Phosphate / potash exposure
- Government policy
- Import dependence
- Working capital

Separate:

```text
SUBSIDY-DRIVEN ECONOMICS
vs
MARKET-PRICE-DRIVEN ECONOMICS
```

Analyze:

- Subsidy receivable cycle
- Working-capital impact
- Government policy dependence
- Nutrient mix
- Input-price volatility

Do not treat reported revenue growth as equivalent to underlying demand growth when subsidy mechanics materially affect reported economics.

---

# 17. Agrochemical-Specific Analysis

Track:

- Crop protection volumes
- Molecule portfolio
- Active ingredients
- Formulations
- Product registrations
- Domestic vs export
- Crop exposure
- Geography
- Monsoon sensitivity
- Channel inventory
- Dealer inventory
- New product launches

Analyze:

```text
FARMER DEMAND
↓
CHANNEL INVENTORY
↓
PRODUCT SALES
↓
VOLUME
↓
REALIZATION
↓
MARGIN
```

Flag:

- Channel destocking
- Excess inventory
- Regulatory restrictions
- Molecule concentration
- Commodity generic exposure
- Weak new-product pipeline

---

# 18. Inventory Analysis

Track:

- Raw-material inventory
- Work-in-progress
- Finished goods
- Inventory days
- Inventory growth
- Inventory/revenue

Calculate:

```text
Inventory Days
```

Analyze:

```text
Inventory Growth
vs
Revenue Growth
vs
Volume Growth
```

Flag:

```text
INVENTORY_BUILD
CHANNEL_DESTOCKING
COMMODITY_PRICE_INVENTORY_LOSS_RISK
```

---

# 19. Working Capital

Track:

- Receivables
- Inventory
- Payables
- Subsidy receivables
- Working capital
- Cash conversion cycle

Calculate:

```text
CCC =
Inventory Days + Receivable Days - Payable Days
```

For fertilizer companies, separately track:

```text
SUBSIDY RECEIVABLE DAYS
```

For export-oriented chemical companies track:

- Export receivables
- Letter of credit exposure
- Currency timing

---

# 20. Margin Analysis

Track:

- Gross margin
- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- PAT
- PAT margin
- EBITDA/unit

Build margin bridge:

```text
REALIZATION
+
VOLUME / MIX
-
RAW MATERIAL
-
ENERGY
-
FREIGHT
-
EMPLOYEE COST
-
OTHER OPERATING COST
=
EBITDA
```

Classify margin improvement as:

```text
PRICE-LED
SPREAD-LED
VOLUME-LED
MIX-LED
COST-LED
OPERATING-LEVERAGE-LED
CURRENCY-LED
```

---

# 21. P&L Analysis

Track:

- Revenue
- Revenue growth
- Gross profit
- EBITDA
- EBIT
- PAT
- EPS
- Other income
- Interest
- Tax

Use:

- YoY
- QoQ
- TTM
- 3Y CAGR
- 5Y CAGR
- 10Y CAGR

Separate:

```text
CORE OPERATING PROFIT
vs
OTHER INCOME
```

Do not treat gains from investments, asset sales or exceptional items as recurring chemical operating earnings.

---

# 22. Cash Flow

Track:

- CFO
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

Analyze whether strong accounting margins translate into cash.

Flag:

```text
PROFIT_CASH_FLOW_MISMATCH
WEAK_CFO_CONVERSION
NEGATIVE_FCF
```

---

# 23. Capital Expenditure

Track:

- Maintenance capex
- Growth capex
- Capacity expansion
- New plants
- Debottlenecking
- R&D capex
- Environmental capex

Calculate:

```text
Capex / Revenue
Capex / EBITDA
Capex / New Capacity
```

Analyze:

- Project cost
- Project timeline
- Expected capacity
- Expected utilization
- Funding
- Expected return

For new capacity:

```text
Incremental ROCE =
Incremental EBIT / Incremental Capital Employed
```

where sufficient data exists.

---

# 24. Capacity-Cycle Analysis

Chemicals can experience severe supply-demand cycles.

Track:

```text
INDUSTRY CAPACITY GROWTH
vs
INDUSTRY DEMAND GROWTH
```

Flag:

```text
SUPPLY GLUT
CAPACITY OVERBUILD
UTILIZATION DECLINE
PRICE PRESSURE
MARGIN COMPRESSION
```

For specialty chemicals, assess whether barriers to entry limit supply additions.

---

# 25. Global Supply-Chain Analysis

Track:

- China capacity
- Global capacity
- Import competition
- Export demand
- Freight
- Trade restrictions
- Geopolitical changes
- Supply disruptions
- Global inventory

Analyze whether company growth is driven by:

- China+1
- Global outsourcing
- Capacity relocation
- Temporary supply disruption
- Structural demand

Do not assume China+1 benefits are permanent without evidence of customer qualification and sustained order growth.

---

# 26. Currency Analysis

Track:

- Export revenue
- Import costs
- USD exposure
- Foreign-currency debt
- Hedging
- Net FX exposure

Calculate:

```text
Net FX Exposure =
Foreign Currency Revenue - Foreign Currency Costs
```

Analyze:

```text
FX
+
REALIZATION
+
INPUT COST
=
MARGIN IMPACT
```

---

# 27. Balance Sheet

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

Stress-test leverage using normalized rather than peak-cycle EBITDA.

---

# 28. ROCE / ROIC

Track:

- ROE
- ROCE
- ROIC
- Asset turnover
- Capital employed
- Incremental ROCE

Analyze:

```text
ROIC
vs
Cost of Capital
```

and:

```text
Incremental ROCE
vs
Historical ROCE
```

For capacity-heavy commodity chemicals, high returns during peak spreads must be normalized across the cycle.

---

# 29. R&D & Innovation

For specialty chemicals and agrochemicals track:

- R&D expenditure
- R&D/revenue
- New molecules
- New products
- Patents where relevant
- Customer approvals
- Commercial launches
- Revenue from new products

Calculate where available:

```text
New Product Revenue %
```

Analyze:

```text
R&D
→
Qualification
→
Commercialization
→
Revenue
→
Margin
```

Flag:

- High R&D with weak commercialization
- Pipeline without customer approvals
- Declining innovation output

---

# 30. Regulatory & Environmental Risk

Track:

- Environmental approvals
- Pollution-control compliance
- Product registrations
- Agrochemical registrations
- Government regulation
- Export restrictions
- Hazardous-material compliance
- Litigation
- Plant shutdowns
- Regulatory notices

For agrochemicals and fertilizers, regulatory approval can directly affect product availability and economics.

Flag:

```text
REGULATORY_RISK
ENVIRONMENTAL_RISK
PRODUCT_REGISTRATION_RISK
PLANT_COMPLIANCE_RISK
```

---

# 31. Management & Capital Allocation

Analyze:

- Capacity expansion
- Acquisition strategy
- R&D allocation
- Debt management
- Dividends
- Buybacks
- Related-party transactions
- Promoter holding
- Promoter pledge
- Dilution
- Auditor history
- Contingent liabilities

Management questions:

- Does management expand near cycle peaks?
- Are projects completed on time?
- Does capex generate acceptable incremental returns?
- Are acquisitions strategically justified?
- Does management maintain balance-sheet discipline?

---

# 32. Concall / Management Guidance Analysis

Extract:

- Demand outlook
- Volume guidance
- Capacity guidance
- Margin guidance
- Capex guidance
- New product guidance
- Customer commentary
- Pricing commentary
- Raw-material commentary
- Export commentary
- Regulatory commentary

Classify statements as:

```text
POSITIVE
NEUTRAL
NEGATIVE
UNCERTAIN
```

Track management statements against subsequent reported results.

The system should compare:

```text
GUIDANCE
vs
ACTUAL
```

and calculate historical guidance reliability.

Do not treat management guidance as fact until supported by reported data.

---

# 33. Competitive Advantage

Assess evidence for:

- Cost leadership
- Feedstock advantage
- Scale
- Technology
- Process know-how
- Product qualification
- Customer relationships
- IP
- Distribution
- Brand
- Geographic advantage
- Integration
- Regulatory barriers

Separate:

```text
STRUCTURAL ADVANTAGE
vs
TEMPORARY SUPPLY SHORTAGE
```

---

# 34. Peer Comparison

Select peers based on:

- Industry
- Product
- End market
- Geography
- Business model
- Commodity/specialty exposure

Compare:

### Operating

- Capacity
- Utilization
- Volume growth
- Realization
- Spread
- EBITDA/unit

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

Do not compare a commodity chemical producer with a high-value specialty chemical company without adjusting for business model.

---

# 35. Valuation

Use:

- P/E
- EV/EBITDA
- EV/EBIT
- P/B
- EV/Sales
- FCF yield

For cyclical chemicals, compare valuation against:

- Historical multiple
- Peer multiple
- Normalized EBITDA
- Mid-cycle earnings
- Current spread
- Capacity cycle
- Utilization

For asset-heavy businesses, consider:

- Replacement cost
- Asset value
- NAV where appropriate

Do not hard-code a universal valuation threshold.

The system should answer:

> Is the current valuation based on sustainable earnings or peak chemical-cycle economics?

---

# 36. Historical Cycle Analysis

Maintain at least:

- 5Y history
- 10Y history where available

Track:

```text
PRODUCT PRICE
RAW MATERIAL PRICE
SPREAD
VOLUME
CAPACITY
UTILIZATION
EBITDA / UNIT
EBITDA
CFO
FCF
ROCE
NET DEBT
CAPEX
```

Identify:

```text
PEAK SPREAD
NORMALIZED SPREAD
TROUGH SPREAD
```

Then determine whether current earnings are:

```text
DEPRESSED
NORMALIZED
ELEVATED
```

---

# 37. Growth Quality

Classify growth as:

### Volume-led

More units sold.

### Capacity-led

New capacity contributes.

### Price-led

Product prices rise.

### Spread-led

Input costs fall faster than selling prices.

### Mix-led

Higher-value products increase.

### Market-share-led

Company grows faster than the market.

### Acquisition-led

Growth comes from acquired businesses.

### Currency-led

FX contributes materially.

### New-product-led

New products drive incremental revenue.

The final analysis must identify the dominant growth engine.

---

# 38. Positive Signals

Examples:

```text
VOLUME_GROWTH
UTILIZATION_IMPROVEMENT
SUSTAINABLE_SPREAD
COST_ADVANTAGE
PRODUCT_PREMIUMIZATION
SPECIALTY_MIX_IMPROVEMENT
NEW_PRODUCT_COMMERCIALIZATION
CUSTOMER_QUALIFICATION
STRONG_CFO_CONVERSION
POSITIVE_FCF
LOWER_NET_DEBT
HIGH_INCREMENTAL_ROCE
DISCIPLINED_CAPEX
STRONG_BALANCE_SHEET
```

These are analytical signals, not automatic investment conclusions.

---

# 39. Red Flags

Flag:

```text
COMMODITY_PRICE_PEAK_DEPENDENCY
SPREAD_COMPRESSION
CAPACITY_OVERBUILD
LOW_UTILIZATION
HIGH_RAW_MATERIAL_EXPOSURE
HIGH_ENERGY_INTENSITY
CUSTOMER_CONCENTRATION
GEOGRAPHIC_CONCENTRATION
EXPORT_DEPENDENCY
CHANNEL_DESTOCKING
INVENTORY_BUILD
WEAK_CFO_CONVERSION
NEGATIVE_FCF
HIGH_NET_DEBT
AGGRESSIVE_CAPEX
LOW_INCREMENTAL_ROCE
REGULATORY_RISK
ENVIRONMENTAL_RISK
PRODUCT_REGISTRATION_RISK
RELATED_PARTY_RISK
ACQUISITION_DEPENDENCY
PEAK_MARGIN_VALUATION
```

---

# 40. Scenario Analysis

Build three scenarios.

## Down Cycle

Assumptions:

- Lower product prices
- Lower utilization
- Higher feedstock costs
- Lower spreads
- Lower EBITDA/unit

Output:

- Revenue
- EBITDA
- PAT
- CFO
- FCF
- Net debt
- ROCE

## Base / Mid Cycle

Use normalized:

- Product prices
- Feedstock costs
- Spreads
- Volume
- Utilization
- Margins

## Up Cycle

Assumptions:

- Strong demand
- Higher utilization
- Better realization
- Strong spreads
- Operating leverage

Clearly separate scenario assumptions from reported data.

---

# 41. Causal Analysis Engine

The final analysis should follow:

```text
END-MARKET DEMAND
        ↓
PRODUCT DEMAND
        ↓
SALES VOLUME
        ↓
CAPACITY UTILIZATION
        ↓
REALIZATION
        ↓
RAW MATERIAL / FEEDSTOCK
        ↓
SPREAD
        ↓
EBITDA / UNIT
        ↓
EBITDA
        ↓
CFO
        ↓
CAPEX
        ↓
FCF
        ↓
NET DEBT / CASH
        ↓
ROCE / ROIC
        ↓
VALUATION
```

For specialty chemicals:

```text
CUSTOMER DEMAND
↓
QUALIFICATION
↓
COMMERCIALIZATION
↓
VOLUME
↓
MIX
↓
REALIZATION
↓
MARGIN
↓
CASH FLOW
```

For fertilizers:

```text
CROP DEMAND
↓
FERTILIZER DEMAND
↓
VOLUME
↓
REALIZATION / SUBSIDY
↓
INPUT COST
↓
MARGIN
↓
SUBSIDY RECEIVABLE
↓
CFO
↓
FCF
```

For agrochemicals:

```text
CROP CYCLE
↓
FARMER DEMAND
↓
CHANNEL INVENTORY
↓
PRODUCT SALES
↓
VOLUME
↓
REALIZATION
↓
MARGIN
↓
CASH FLOW
```

---

# 42. Scoring Architecture

Maintain separate dimensions:

```text
BUSINESS QUALITY
PRODUCT QUALITY
DEMAND QUALITY
COST COMPETITIVENESS
SPREAD QUALITY
CAPACITY QUALITY
GROWTH
OPERATING QUALITY
CASH FLOW QUALITY
BALANCE SHEET
CAPITAL EFFICIENCY
COMPETITIVE ADVANTAGE
MANAGEMENT / GOVERNANCE
VALUATION
RISK
```

Each dimension must retain:

- Metric
- Value
- Trend
- Peer comparison
- Interpretation
- Data confidence

Do not collapse the entire analysis into an opaque single score.

---

# 43. Data Quality

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

Allowed data types:

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
6. Regulatory filings
7. Company operational disclosures
8. Reliable financial databases
9. Third-party datasets

Never silently convert an estimate or management statement into reported data.

---

# 44. Agent Architecture

Recommended pipeline:

```text
COMPANY IDENTIFICATION
        ↓
MACRO SECTOR / SECTOR / INDUSTRY CLASSIFICATION
        ↓
BUSINESS MODEL CLASSIFICATION
        ↓
RAW FINANCIAL DATA
        ↓
PRODUCT / SEGMENT DATA
        ↓
CAPACITY / PRODUCTION DATA
        ↓
COMMODITY / INPUT PRICE DATA
        ↓
REALIZATION ENGINE
        ↓
SPREAD / UNIT ECONOMICS ENGINE
        ↓
DEMAND / END-MARKET ENGINE
        ↓
P&L ANALYSIS
        ↓
BALANCE SHEET ANALYSIS
        ↓
CASH FLOW ANALYSIS
        ↓
ROCE / ROIC ENGINE
        ↓
R&D / PRODUCT PIPELINE ENGINE
        ↓
MANAGEMENT / CONCALL ENGINE
        ↓
INDUSTRY SUPPLY-DEMAND ENGINE
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

# 45. Database Structure

Recommended tables:

```text
companies
company_classification
industry_mapping
products
product_metrics
end_market_metrics
capacity_metrics
production_metrics
utilization_metrics
realization_metrics
commodity_prices
raw_material_prices
energy_metrics
spread_metrics
regional_metrics
customer_metrics
export_metrics
segment_metrics
financial_statements
working_capital_metrics
cash_flow_metrics
balance_sheet_metrics
capex_metrics
r_and_d_metrics
product_pipeline
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

# 46. Final Screener Output

For every Chemicals company, generate:

## Classification

- Macro Sector: Commodities
- Sector: Chemicals
- Industry
- Business model
- Product category
- End markets
- Geography
- Domestic/export mix

## Business Quality

- Product portfolio
- Commodity vs specialty exposure
- Customer concentration
- Competitive advantage
- Integration
- R&D
- Product pipeline

## Demand

- End-market growth
- Volume growth
- Market-share indicators
- Export demand
- Channel inventory

## Operating

- Capacity
- Utilization
- Production
- Sales volume
- Realization
- Spread
- Cost/unit
- EBITDA/unit

## Financial Quality

- Revenue growth
- EBITDA growth
- EBITDA margin
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
- Incremental ROCE

## Cycle Position

- Product price
- Feedstock price
- Spread
- Historical spread
- Current utilization
- Capacity additions
- Supply-demand position

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

- Capex
- Acquisitions
- Guidance
- R&D
- Capital allocation
- Governance
- Concall signals

## Risks

- Commodity cycle
- Spread compression
- Raw materials
- Energy
- Regulation
- Environment
- Customer concentration
- Export dependence
- Capacity additions
- Leverage

## Final Analytical Output

```text
BUSINESS QUALITY
PRODUCT QUALITY
DEMAND QUALITY
COST POSITION
SPREAD QUALITY
GROWTH ENGINE
OPERATING ENGINE
CASH ENGINE
BALANCE SHEET
CAPITAL EFFICIENCY
COMPETITIVE ADVANTAGE
CYCLE POSITION
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

# 47. Implementation Principles

The engine must follow:

```text
RAW DATA
→ VERIFIED DATA
→ CLASSIFICATION
→ PRODUCT MAPPING
→ NORMALIZATION
→ DEMAND ANALYSIS
→ VOLUME ANALYSIS
→ CAPACITY / UTILIZATION
→ REALIZATION
→ INPUT COST
→ SPREAD
→ UNIT ECONOMICS
→ FINANCIAL ANALYSIS
→ CASH FLOW
→ ROCE / ROIC
→ SUPPLY-DEMAND
→ PEER COMPARISON
→ CYCLE ANALYSIS
→ MANAGEMENT / CONCALL
→ RED FLAGS
→ SCENARIOS
→ VALUATION
→ FINAL FUNDAMENTAL THESIS
```

The core rule is:

> **Never confuse a favorable chemical-cycle spread with durable business quality.**

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
RAW MATERIAL
vs
ENERGY
vs
SPREAD
vs
CASH FLOW
vs
CAPITAL ALLOCATION
```

## Central Fundamental Question

> **Can the company generate attractive returns and free cash flow through a normalized chemical cycle, supported by sustainable product economics, cost advantages, competitive barriers and disciplined capital allocation?**
