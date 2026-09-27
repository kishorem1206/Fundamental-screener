# Consumer Discretionary → Consumer Durables — Fundamental Analysis Framework

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

This is a standalone, implementation-ready framework for companies classified under:

**Macro Sector:** Consumer Discretionary  
**Sector Value:** Consumer Durables  
**Industry:** Consumer Durables

The source framework classifies this industry into:

- Consumer electronics
- Appliances
- Air conditioners
- Refrigerators
- Washing machines
- Small appliances
- Electrical consumer products
- Premium electronics

Its core drivers are:

- Units
- ASP
- Product mix
- Distribution
- Market share
- Replacement cycle
- Seasonality
- Commodity costs
- Channel inventory

It also specifically requires capacity and utilization analysis and separation of channel inventory from end-consumer demand where data is available. fileciteturn23file1 fileciteturn23file0

The analysis engine should move through:

**RAW DATA → NORMALIZATION → CALCULATED METRICS → TREND → PEER → CAUSAL ANALYSIS → RED FLAGS → SCORING → INVESTMENT THESIS**

> Core principle: a Consumer Durables company should not be analyzed using revenue and margin alone. The engine must connect units, ASP, mix, market share, distribution, replacement demand, seasonality, input costs, channel inventory, capacity utilization and cash generation.

---

# 2. Business-Model Classification

Before calculating ratios, classify the company.

## 2.1 Consumer Electronics

Examples of analytical categories:

- Televisions
- Audio products
- Personal electronics
- Smart devices
- Digital consumer products
- Premium electronics

Track:

- Units
- ASP
- Product mix
- Premium mix
- Market share
- Distribution
- E-commerce share
- Replacement cycle
- Inventory

---

## 2.2 Appliances

Classify by:

- Air conditioners
- Refrigerators
- Washing machines
- Small appliances
- Other household appliances

Track:

- Units
- ASP
- Product mix
- Premium mix
- Market share
- Distribution
- Replacement demand
- Capacity
- Utilization
- Seasonality

---

## 2.3 Electrical Consumer Products

Classify:

- Consumer electrical products
- Household electrical products
- Other consumer-facing electrical categories

Track:

- Units / volume
- ASP
- Product mix
- Market share
- Distribution reach
- Dealer / retailer network
- Replacement demand
- Input-cost sensitivity

---

## 2.4 Premium Electronics

Track separately:

- Premium product share
- Premium ASP
- Premium mix
- Gross margin
- Brand strength
- Product innovation
- Market share
- Customer profile
- Replacement cycle

Analyze:

**Premiumization → ASP → Gross Margin → EBITDA → Cash**

---

# 3. Revenue Architecture

Decompose revenue before interpreting growth.

Track:

- Product revenue
- Category revenue
- Domestic revenue
- Export revenue
- E-commerce revenue
- Offline channel revenue
- Premium product revenue
- Aftermarket / service revenue where applicable
- Other operating revenue
- Other income

Separate:

**Core operating revenue vs other income**

and:

**Organic growth vs acquisition-led growth**

Where possible, decompose:

**Revenue Growth = Volume Growth + Price Effect + Mix Effect + New Product Contribution + Acquisitions + Currency**

The source framework explicitly requires volume/price/mix decomposition for Consumer Discretionary businesses, including Consumer Durables. fileciteturn23file4

---

# 4. Demand Engine

Consumer Durables demand can be driven by:

- Replacement cycle
- New household formation
- Income growth
- Employment
- Consumer confidence
- Financing availability
- Interest rates
- Urban demand
- Rural demand
- Housing activity
- Seasonality
- Product innovation
- Premiumization
- Energy efficiency
- Technology upgrades

Track:

- Industry volume growth
- Company volume growth
- Replacement demand
- New-user demand
- Premium demand
- Rural vs urban demand
- Financing availability
- Seasonal demand

Core chain:

**Consumer Demand → Units → Revenue → Utilization → Operating Leverage → Margin → Profit → Cash**

This demand-to-cash chain follows the common Consumer Discretionary framework. fileciteturn23file4

---

# 5. Unit Volume Analysis

Track:

- Units sold
- Domestic units
- Export units
- Category volume
- Product-level volume
- Quarterly volume
- Annual volume
- Volume growth

Calculate:

- YoY volume growth
- QoQ volume growth where meaningful
- 3Y volume CAGR
- 5Y volume CAGR
- TTM volume growth

Compare:

**Company Volume Growth vs Industry Volume Growth**

This helps identify potential market-share changes.

Do not use revenue growth as a substitute for volume growth when unit data is available.

---

# 6. ASP Analysis

Track:

- ASP
- Realization
- Product-level ASP
- Category ASP
- Premium ASP
- Entry-level ASP
- Price increases
- Discounts
- Promotions

Calculate:

**ASP = Relevant Revenue / Relevant Units**

where the revenue and unit definitions are comparable.

Analyze:

**Volume + ASP → Revenue**

Then explain whether ASP changes arise from:

- Actual price increases
- Premiumization
- Product mix
- Geographic mix
- Currency
- Product launches

A revenue increase caused mainly by price/mix should be distinguished from genuine unit-demand growth. fileciteturn23file4

---

# 7. Product Mix Analysis

Track:

- Entry-level products
- Mid-range products
- Premium products
- Product category mix
- Smart / connected products where applicable
- Energy-efficient products
- New vs mature products
- High-margin vs low-margin products

Calculate where data permits:

- Premium mix %
- Premium ASP
- Revenue contribution by category
- Margin by category

Analyze:

**Mix Shift → ASP → Gross Margin → EBITDA**

Positive mix changes should be distinguished from broad-based volume growth.

---

# 8. Premiumization

Track:

- Premium revenue
- Premium units
- Premium ASP
- Premium mix
- Premium market share
- Premium gross margin where available

Analyze:

**Income Growth → Premium Demand → Premium Mix → ASP → Margin**

Investigate whether premiumization is:

- Structural
- Temporary
- Promotion-driven
- Product-launch-driven

Do not assume premiumization automatically improves cash returns if customer acquisition, marketing or product-development costs rise materially.

---

# 9. Market Share

Track:

- Overall market share
- Category market share
- Product market share
- Premium market share
- Geographic market share
- Online share
- Offline share

Analyze:

**Company Volume Growth vs Industry Volume Growth → Market Share**

Track:

- Share gains
- Share losses
- New entrants
- Competitive pricing
- Product launches
- Distribution expansion

Require reported market-share data where available rather than relying solely on inferred market share.

---

# 10. Distribution Analysis

Track:

- Dealer count
- Distributor count
- Retail outlets
- Geographic reach
- Modern retail
- General trade
- E-commerce
- Online sales
- Offline sales
- Omnichannel penetration
- Service network
- Rural distribution

Calculate where possible:

- Revenue / dealer
- Revenue / outlet
- Revenue / distribution point
- Online revenue share
- Digital penetration

Assess:

- Distribution reach
- Channel productivity
- Dealer economics
- Geographic expansion
- E-commerce dependence

---

# 11. Channel Inventory Analysis

This is a critical module.

Track where available:

- Manufacturer inventory
- Distributor inventory
- Dealer inventory
- Retail inventory
- Channel inventory days
- Sell-in
- Sell-through
- Retail sales

Core chain:

**Production → Sell-in → Channel Inventory → Sell-through / End Consumer Demand**

The source framework explicitly requires channel inventory to be separated from end-consumer demand where data is available and flags revenue growth caused by channel loading rather than sell-through. fileciteturn23file0

Flag:

- Dispatch growth + rising dealer inventory
- Revenue growth + weak sell-through
- Heavy promotional activity
- Sudden inventory accumulation
- Channel loading before quarter-end
- Inventory correction after a strong quarter

---

# 12. Replacement Cycle

Consumer Durables often have a meaningful replacement component.

Track:

- Installed base where available
- Average product life
- Replacement demand
- New-user demand
- Replacement cycle
- Upgrade cycle
- Product obsolescence
- Technology transition

Analyze:

**Installed Base → Product Age → Replacement Cycle → Units → Revenue**

For electronics, also assess:

- Technology upgrades
- New features
- Product refreshes
- Smart / connected product adoption

---

# 13. Seasonality Analysis

The source framework specifically identifies:

- Summer
- Festive
- Monsoon
- Winter
- Regional cycles

as important seasonality factors for Consumer Durables. fileciteturn23file0

## Summer

Potentially relevant to:

- Air conditioners
- Cooling products
- Refrigeration

Track:

- Weather sensitivity
- Pre-season inventory
- Peak-season volume
- ASP
- Channel inventory

## Festive

Track:

- Festive sales
- Promotions
- Premiumization
- Financing
- E-commerce events
- Inventory build

## Monsoon

Track:

- Regional demand
- Product-category sensitivity
- Distribution disruption
- Rural demand

## Winter

Track category-specific seasonality.

## Regional cycles

Compare:

- North
- South
- East
- West
- Rural
- Urban

Do not annualize a seasonally strong quarter without adjusting for the business cycle.

---

# 14. Weather Sensitivity

For weather-sensitive categories such as air conditioners and cooling products, track:

- Temperature
- Heat-wave intensity where relevant
- Season length
- Cooling-degree demand where available
- Pre-season demand
- Peak-season demand
- Inventory before season

Analyze:

**Weather → Consumer Demand → Units → ASP / Mix → Revenue → Utilization → Margin**

Separate:

**Structural category penetration**

from:

**Unusually favorable weather**

---

# 15. Capacity Analysis

Track:

- Installed capacity
- Capacity additions
- Plant count
- Production capacity
- Capacity utilization
- New factories
- Expansion capex
- CWIP

Calculate:

- Capacity utilization
- Revenue / capacity
- EBITDA / capacity
- Incremental revenue / capacity

Core chain:

**Capex → Capacity → Utilization → Revenue → EBIT → CFO → FCF → ROIC**

The source framework specifically identifies capacity and utilization as Consumer Durables metrics. fileciteturn23file3

---

# 16. Operating Leverage

Track:

- Capacity
- Capacity utilization
- Fixed-cost base
- Revenue
- EBITDA margin
- EBIT margin
- Incremental EBITDA margin
- Incremental EBIT margin

Calculate:

**Incremental EBITDA Margin = Change in EBITDA / Change in Revenue**

**Incremental EBIT Margin = Change in EBIT / Change in Revenue**

Determine whether margin improvement comes from:

- Volume recovery
- Higher utilization
- Premiumization
- Product mix
- Pricing
- Cost reduction
- Commodity deflation
- Temporary operating leverage

The common framework explicitly requires this attribution rather than assuming margin improvement is structural. fileciteturn23file4

---

# 17. Input-Cost Analysis

The source framework identifies these Consumer Durables input costs:

- Copper
- Aluminium
- Steel
- Plastics
- Electronics/components

fileciteturn23file0

Depending on the company, also track:

- Freight
- Packaging
- Energy
- Other major components

Analyze:

**Input Prices → Material Cost → Gross Margin → EBITDA → CFO**

Track:

- Input cost / revenue
- Commodity sensitivity
- Price pass-through
- Pass-through lag
- Procurement efficiency
- Hedging where disclosed

---

# 18. Commodity Pass-Through

Assess:

- Price increases
- Vendor contracts
- Cost-plus arrangements where disclosed
- Pass-through lag
- Competitive pricing
- Inventory effect

Analyze:

**Commodity Inflation → Price Action → ASP → Volume → Gross Margin**

Flag:

- Input inflation without price increases
- Price increases causing volume deterioration
- Margin expansion caused by temporary commodity deflation

---

# 19. Gross Margin

Track:

- Material cost / revenue
- Component cost / revenue
- Employee cost / revenue
- Freight / revenue
- Warranty cost
- Advertising / revenue
- Selling cost
- Other operating expenses

Analyze:

**ASP / Mix → Input Cost → Gross Margin → EBITDA**

Separate margin changes caused by:

- Pricing
- Volume
- Mix
- Commodity costs
- Productivity
- Currency
- Warranty
- Launch costs

---

# 20. Warranty & After-Sales Economics

Where disclosed, track:

- Warranty expense
- Warranty provisions
- Warranty claims
- Service revenue
- Spare-parts revenue
- Installation revenue
- Extended warranty
- Service network
- Return rates
- Product quality indicators

Analyze:

**Units Sold → Installed Base → Warranty / Service Cost → Customer Retention → Brand → Cash**

Flag:

- Rising warranty provisions
- Repeated product quality issues
- Warranty costs rising faster than revenue
- Large provisions without adequate explanation

---

# 21. Product Innovation & Launches

Track:

- New products
- New categories
- Product refreshes
- Launch frequency
- Premium launches
- Smart / connected products
- Energy-efficient products
- Product development
- R&D expenditure

Analyze:

**R&D / Product Investment → Launch → Market Acceptance → Volume → ASP → Margin**

Flag:

- Weak product pipeline
- Aging portfolio
- Heavy launch spending without adoption
- Technology obsolescence

---

# 22. Brand & Competitive Advantage

Assess:

- Brand recognition
- Pricing power
- Customer loyalty
- Distribution
- Product differentiation
- Product innovation
- Scale
- Procurement advantage
- Manufacturing efficiency
- Service network

The source framework states that competitive advantage should be supported by evidence such as stable/improving market share, sustained premium pricing, superior margins, high ROIC and distribution expansion. fileciteturn23file3

Do not label a moat merely because the company is large.

---

# 23. E-Commerce & Omnichannel Analysis

Track:

- Online revenue
- Online share
- E-commerce volume
- Online ASP
- Offline ASP
- Marketplace dependence
- Direct-to-consumer sales
- Website sales
- Omnichannel sales
- Digital marketing cost

Analyze:

**Digital Penetration → Customer Reach → Conversion → Revenue → Distribution Cost → Margin**

Compare:

- Online vs offline economics
- Discounting
- Returns
- Customer acquisition
- Channel conflict
- Marketplace fees

---

# 24. Financing & Affordability

Track:

- Consumer financing penetration
- EMI availability
- Interest rates
- Loan affordability
- Promotional financing
- Dealer financing
- Credit conditions

Analyze:

**Financing Availability → Affordability → Units → Revenue**

Pay attention to:

- Interest-rate sensitivity
- Consumer income
- Credit tightening
- Financing promotions

---

# 25. Working Capital

Track:

- Receivable days
- Inventory days
- Payable days
- Cash conversion cycle
- Dealer receivables
- Distributor receivables
- Channel inventory
- Inventory ageing
- Raw-material inventory
- Finished goods inventory

Core chain:

**Revenue Growth → Receivables Growth → Inventory Growth → CFO**

The source framework specifically flags receivables growing faster than sales, inventory growing faster than sales and channel stuffing indicators. fileciteturn23file3

Flag:

- Inventory buildup
- Slow-moving products
- Dealer receivable stress
- Excess finished goods
- Channel loading

---

# 26. Inventory Quality

Track:

- Inventory days
- Inventory turns
- Raw-material inventory
- Work-in-progress
- Finished goods
- Obsolete inventory
- Inventory ageing
- Provisions for obsolete inventory

Analyze:

**Inventory → Sell-through → Discounting → Gross Margin → CFO**

Flag:

- Inventory growth > sales growth
- Ageing inventory
- Rising markdowns
- Obsolescence risk
- Inventory correction following weak demand

---

# 27. Capex Analysis

Track:

- Gross capex
- Maintenance capex
- Growth capex
- Capacity additions
- Capex / revenue
- Capex / depreciation
- CWIP
- Asset turnover
- New plant capex
- Product-development capex

Evaluate:

**Capex → Capacity → Utilization → Revenue → EBIT → CFO → FCF → ROIC**

Flag:

- Large capex without demand visibility
- Low utilization after expansion
- Persistent negative FCF
- Project delays
- Capitalized expenses

The source framework explicitly uses this capex-to-ROIC chain. fileciteturn23file3

---

# 28. Cash Flow Quality

Track:

- CFO
- Capex
- CFI
- CFF
- FCF
- CFO/PAT
- FCF/PAT
- FCF margin
- Cash conversion
- Dividends
- Buybacks
- Debt repayment
- Debt raised

Core chain:

**EBITDA → EBIT → PAT → CFO → Capex → FCF**

Assess:

**Accounting Profit vs Cash Generation**

Flag:

- PAT rising while CFO falls
- Weak CFO/PAT
- Persistent negative FCF
- Working-capital absorption
- Heavy capex without corresponding growth

---

# 29. Balance Sheet & Funding

Track:

- Cash
- Investments
- Gross debt
- Net debt
- Equity
- Net worth
- Goodwill
- Intangible assets
- Receivables
- Inventory
- Payables
- CWIP
- PPE
- Lease liabilities

Calculate:

- Net debt / EBITDA
- Debt / equity
- Interest coverage
- Net debt / CFO
- Asset turnover
- ROCE
- ROIC

Assess:

- Leverage
- Funding requirements
- Acquisition debt
- Lease obligations
- Working-capital funding

---

# 30. ROCE / ROIC

Calculate:

- ROCE
- ROIC
- ROA
- Asset turnover
- Capital turnover

Decompose:

**ROCE = Operating Margin × Capital Turnover**

Investigate whether returns are driven by:

- Strong brand
- Premiumization
- High utilization
- Asset-light growth
- Strong distribution
- Procurement advantage

Or weakened by:

- Excess capacity
- Large inventories
- Heavy capex
- Low utilization
- Acquisitions
- Working-capital intensity

---

# 31. Management & Capital Allocation

Track:

- Promoter holding
- Promoter pledge
- Promoter buying / selling
- Institutional ownership
- Dilution
- ESOP dilution
- Related-party transactions
- Auditor changes
- Auditor qualifications
- Auditor resignations
- Regulatory actions
- Contingent liabilities
- Management remuneration
- Acquisitions
- Dividends
- Buybacks
- Capex plans

Assess capital allocation toward:

- Capacity
- Product development
- Distribution
- Technology
- Acquisitions
- Debt reduction
- Dividends
- Buybacks

Flag:

- Repeated acquisitions with weak returns
- Excessive capacity expansion
- Persistent dilution
- Weak disclosure
- Related-party concerns

---

# 32. Concall Intelligence

Extract management commentary on:

## Demand

- Consumer demand
- Replacement demand
- Rural demand
- Urban demand
- Financing conditions
- Seasonal outlook

## Volume

- Unit growth
- Category growth
- Market share
- Retail sell-through

## Pricing

- Price increases
- Discounts
- Promotions
- ASP
- Premiumization

## Distribution

- Dealer additions
- Retail expansion
- E-commerce
- Omnichannel strategy

## Inventory

- Channel inventory
- Dealer inventory
- Sell-through
- Inventory normalization

## Costs

- Copper
- Aluminium
- Steel
- Plastics
- Electronics/components
- Freight
- Energy

## Capacity

- New plants
- Capacity utilization
- Expansion
- Capex

## Product

- New launches
- Premium products
- Product pipeline
- Technology
- Energy efficiency

## Guidance

Track:

**Guidance → Subsequent Result → Variance → Management Explanation**

Classify:

- Positive guidance
- Neutral guidance
- Cautious guidance
- Negative guidance
- Quantified guidance
- Qualitative commentary

Do not treat management optimism as evidence without subsequent operating or financial confirmation.

---

# 33. Industry Cycle Analysis

Analyze:

- Replacement cycle
- Income cycle
- Credit cycle
- Interest rates
- Housing cycle
- Consumer confidence
- Weather
- Commodity cycle
- Inventory cycle
- Festive cycle
- Technology cycle

Distinguish:

**Structural category growth**

from:

**Cyclical recovery**

from:

**Seasonal strength**

from:

**Temporary commodity benefit**

---

# 34. Peer Comparison

Compare companies by actual product category and business model.

## Appliance peers

Compare:

- Volume growth
- ASP
- Market share
- Premium mix
- Distribution
- Capacity utilization
- Commodity sensitivity
- EBITDA margin
- CFO/PAT
- FCF
- ROIC
- Valuation

## Consumer Electronics peers

Compare:

- Units
- ASP
- Product mix
- Premiumization
- Market share
- E-commerce share
- Inventory
- Gross margin
- EBITDA
- FCF
- ROIC

## Electrical Consumer Product peers

Compare:

- Volume
- ASP
- Distribution
- Market share
- Input costs
- Working capital
- Margins
- ROIC
- FCF

Do not compare companies solely because they are classified under Consumer Durables.

---

# 35. Valuation Framework

Track:

- P/E
- EV/EBITDA
- EV/Sales
- P/B where meaningful
- DCF
- FCF yield
- Historical valuation
- Peer valuation
- Growth-adjusted valuation

Interpret valuation alongside:

- Volume growth
- Market share
- ASP
- Premiumization
- Margin
- ROIC
- FCF
- Balance-sheet strength
- Industry cycle

Output:

- Current valuation
- Historical valuation
- Peer valuation
- Growth-adjusted valuation
- Margin-adjusted valuation
- Cash-flow-adjusted valuation
- Margin of safety

Do not hard-code one universal multiple.

---

# 36. Historical Valuation

Track:

- Historical P/E
- Historical EV/EBITDA
- Historical EV/Sales
- Historical P/B where meaningful
- Historical FCF yield

Compare against:

- Revenue growth
- Volume growth
- Market share
- ASP
- EBITDA margin
- ROIC
- FCF
- Net debt
- Industry cycle

A lower historical multiple should not automatically be interpreted as undervaluation without considering the underlying business conditions.

---

# 37. Causal Analysis Engine

The system must explain **WHY** financial metrics changed.

## Core Consumer Durables Chain

**Consumer Demand → Units → ASP / Mix → Revenue → Capacity Utilization → Margin → EBIT → PAT → CFO → FCF → ROIC**

## Market Share Chain

**Product / Brand / Distribution → Company Volume → Industry Volume → Market Share → Revenue → Utilization → Margin**

## Premiumization Chain

**Income / Preferences → Premium Demand → Premium Mix → ASP → Gross Margin → EBITDA**

## Input-Cost Chain

**Copper / Aluminium / Steel / Plastics / Electronics → Material Cost → Gross Margin → EBITDA → CFO**

## Inventory Chain

**Production → Sell-in → Channel Inventory → Sell-through → Revenue Quality → Working Capital → CFO**

## Seasonality Chain

**Weather / Festive / Regional Cycle → Demand → Units → Inventory → Revenue → Utilization → Margin**

## Capacity Chain

**Capex → Capacity → Utilization → Revenue → EBIT → CFO → FCF → ROIC**

The engine should identify where the chain breaks.

Example:

**Revenue ↑ → Units flat → ASP ↑ → Inventory ↑ → CFO ↓**

Possible investigation:

- Price increase
- Premiumization
- Channel loading
- Weak sell-through
- Working-capital stress

Do not assign a cause unless supported by reported data, calculated evidence or management disclosure.

---

# 38. Red Flags

## Demand

- Unit growth materially below industry growth
- Market-share decline
- Weak replacement demand
- Weak retail sell-through
- Demand dependent on financing incentives

## Pricing

- Revenue growth without volume growth
- Heavy discounting
- ASP growth caused only by premium mix
- Price increases causing demand deterioration

## Product

- Aging product portfolio
- Weak launch pipeline
- Technology obsolescence
- Falling premium share
- Product concentration

## Distribution

- Weak dealer productivity
- Distribution expansion without sales productivity
- Excessive marketplace dependence
- Channel conflict

## Inventory

- Channel inventory rising
- Dealer inventory rising
- Inventory growth > sales growth
- Inventory ageing
- High discounting to clear inventory
- Channel loading

## Costs

- Input inflation without pass-through
- Margin expansion from temporary commodity deflation
- Rising warranty costs
- Rising component costs

## Capacity

- Large capex without demand visibility
- Low utilization
- Persistent CWIP
- Project delays
- Excess capacity

## Cash Flow

- PAT rising while CFO falls
- Weak CFO/PAT
- Persistent negative FCF
- Working-capital absorption

## Governance

- Promoter pledge
- Auditor qualification
- Auditor resignation
- Related-party concerns
- Repeated dilution
- Aggressive acquisitions

---

# 39. Positive Signals

Look for combinations such as:

- Unit growth > industry growth
- Sustained market-share gains
- Healthy ASP growth
- Premiumization
- Strong new-product cycle
- Improving distribution
- Higher e-commerce penetration with healthy economics
- Healthy sell-through
- Controlled channel inventory
- Improving utilization
- Operating leverage
- Stable/improving gross margin
- Successful price increases
- Strong brand
- Strong replacement demand
- Improving CFO/PAT
- Rising FCF
- Improving ROIC
- Low leverage

A positive signal should be supported by multiple data points rather than one quarter.

---

# 40. Scenario Analysis

Build Bull / Base / Bear scenarios.

## Bull

Potential assumptions:

- Strong unit growth
- Market-share gains
- ASP growth
- Premiumization
- Higher utilization
- Strong festive / seasonal demand
- Favorable replacement cycle
- Lower input costs
- Strong product launches
- Healthy channel inventory

Calculate:

- Revenue
- EBITDA
- EBIT
- PAT
- CFO
- FCF
- ROIC
- Net debt
- Valuation

## Base

Potential assumptions:

- Normal category growth
- Stable market share
- Normal ASP growth
- Normal utilization
- Normal seasonality
- Stable commodity environment
- Planned capex

## Bear

Potential assumptions:

- Demand slowdown
- Market-share loss
- Dealer/channel inventory build
- Discounting
- Commodity inflation
- Lower utilization
- Weak product cycle
- Higher financing costs
- Working-capital stress

Calculate the same financial outputs.

---

# 41. Scoring Architecture

Use the common Consumer Discretionary framework as the starting architecture:

| Category | Base Weight |
|---|---:|
| Business Quality | 15% |
| Demand & Growth | 15% |
| Competitive Position | 10% |
| Operating Quality | 15% |
| Cash Flow Quality | 15% |
| Balance Sheet | 10% |
| Capital Efficiency | 10% |
| Management & Governance | 5% |
| Valuation | 5% |

Activate Consumer Durables-specific metrics inside each category.

### Business Quality

- Category attractiveness
- Brand
- Product portfolio
- Revenue diversification
- Replacement exposure

### Demand & Growth

- Unit growth
- Market growth
- Market share
- ASP
- Premiumization
- Replacement demand

### Competitive Position

- Brand
- Distribution
- Product innovation
- Market share
- Service network

### Operating Quality

- Utilization
- Gross margin
- EBITDA margin
- Incremental margin
- Commodity pass-through

### Cash Flow Quality

- CFO/PAT
- FCF
- Inventory quality
- Working-capital management

### Balance Sheet

- Net debt
- Interest coverage
- Working-capital funding

### Capital Efficiency

- ROCE
- ROIC
- Asset turnover

### Management & Governance

- Guidance quality
- Capital allocation
- Product strategy
- Disclosure quality

### Valuation

- P/E
- EV/EBITDA
- EV/Sales
- FCF yield
- Historical valuation
- Peer valuation

**Important:** do not produce a misleading final score when critical industry data is missing. Show data coverage and confidence.

---

# 42. Metric Classification

Every metric should be tagged:

- CORE
- SUPPORTING
- DIAGNOSTIC
- SECTOR_SPECIFIC
- VALUATION
- PRESENTATION

Examples:

| Metric | Classification |
|---|---|
| Revenue growth | CORE |
| EBITDA margin | CORE |
| CFO/PAT | CORE |
| FCF margin | CORE |
| ROIC | CORE |
| Unit growth | SECTOR_SPECIFIC |
| ASP | SECTOR_SPECIFIC |
| Market share | SECTOR_SPECIFIC |
| Premium mix | SECTOR_SPECIFIC |
| Capacity utilization | SECTOR_SPECIFIC |
| Channel inventory | DIAGNOSTIC |
| Inventory days | CORE |
| Replacement cycle | SECTOR_SPECIFIC |
| Commodity sensitivity | DIAGNOSTIC |
| P/E | VALUATION |
| EV/EBITDA | VALUATION |
| Net debt / EBITDA | CORE |

---

# 43. Data Quality Framework

Every metric must store:

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
- MANAGEMENT-DISCLOSED
- THIRD-PARTY

Confidence:

- HIGH
- MEDIUM
- LOW

Calculated metrics must retain input lineage.

Example:

```text
ASP
= Relevant Revenue / Relevant Units
```

Store both revenue and units used.

For:

```text
Incremental EBITDA Margin
= Change in EBITDA / Change in Revenue
```

store both periods used in the calculation.

---

# 44. Source Hierarchy

Use:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings / Concall Transcript
5. NSE/BSE filings
6. Regulatory filings
7. Company website / Investor Relations
8. Reliable financial databases
9. Third-party research

For:

- Units
- Market share
- Distribution
- Channel inventory
- Capacity
- Utilization
- Product mix
- Commodity sensitivity

prefer primary company disclosures where available.

Third-party data must not silently override company-reported data.

---

# 45. Missing Data Logic

Never convert missing values into zero.

Allowed states:

- AVAILABLE
- CALCULABLE
- PARTIAL
- MISSING_INPUT
- SOURCE_REQUIRED
- NOT_APPLICABLE
- INVALID

Example:

If channel inventory is not disclosed:

```text
channel_inventory = MISSING_INPUT
```

not:

```text
channel_inventory = 0
```

The scoring system must reduce confidence rather than manufacture a value.

---

# 46. Agent Architecture

Recommended pipeline:

```text
Company Identification
        ↓
Business Classification
        ↓
Product Category Classification
        ↓
Domestic / Export Classification
        ↓
Financial Data
        ↓
Industry Demand
        ↓
Company Units
        ↓
Market Share
        ↓
ASP / Price / Mix
        ↓
Premiumization
        ↓
Distribution
        ↓
Replacement Cycle
        ↓
Seasonality
        ↓
Channel Inventory
        ↓
Capacity / Utilization
        ↓
Commodity Costs
        ↓
Margins
        ↓
Working Capital
        ↓
Capex
        ↓
Cash Flow
        ↓
Balance Sheet
        ↓
ROIC
        ↓
Management / Concall
        ↓
Competitive Advantage
        ↓
Industry Cycle
        ↓
Peer Comparison
        ↓
Valuation
        ↓
Red Flag Detection
        ↓
Causal Analysis
        ↓
Scoring
        ↓
Investment Thesis
```

Each module should return:

```text
metric
value
trend
source
confidence
interpretation
causal_link
red_flags
positive_signals
```

---

# 47. Database Structure

Recommended metric table:

```text
company_id
sector
sector_value
industry
business_model
product_category
geography
channel
metric_name
metric_category
period
value
unit
source
source_date
data_type
confidence
calculation_formula
input_metrics
```

Recommended operating-metric categories:

```text
UNITS
ASP
PRODUCT_MIX
PREMIUMIZATION
MARKET_SHARE
DISTRIBUTION
DEALERS
RETAIL_OUTLETS
E_COMMERCE
REPLACEMENT
SEASONALITY
WEATHER
CHANNEL_INVENTORY
CAPACITY
UTILIZATION
INPUT_COSTS
MARGINS
WARRANTY
WORKING_CAPITAL
INVENTORY
CAPEX
CASH_FLOW
BALANCE_SHEET
ROIC
GOVERNANCE
VALUATION
```

---

# 48. Data Coverage Dashboard

The application should show:

**DATA COVERAGE**

Example:

```text
81% of tracked metrics available
```

Then:

```text
Critical data gaps:
- Channel inventory
- Market share
- Category-level volume
- Premium mix
- Capacity utilization
```

Also show:

```text
High-confidence metrics
Medium-confidence metrics
Low-confidence metrics
```

Critical missing metrics should be highlighted before the final score.

---

# 49. Quarterly Monitoring System

For every quarter compare:

```text
Current Quarter
vs Previous Quarter
vs Same Quarter Last Year
vs TTM
vs 3Y Trend
```

Track:

- Industry volume
- Company volume
- Market share
- ASP
- Product mix
- Premium mix
- Distribution
- E-commerce share
- Channel inventory
- Inventory days
- Capacity utilization
- Commodity costs
- Revenue
- EBITDA
- EBIT
- PAT
- CFO
- FCF
- ROIC
- Net debt

Generate:

**What changed? → Why did it change? → Is it temporary or structural? → What should be monitored next?**

---

# 50. Guidance Tracking

Maintain:

| Date | Metric | Management Guidance | Actual | Variance | Explanation | Status |
|---|---|---|---|---|---|---|

Possible statuses:

- ACHIEVED
- PARTIALLY_ACHIEVED
- MISSED
- AHEAD_OF_GUIDANCE
- NOT_TESTABLE_YET

Track guidance for:

- Volume
- Market share
- ASP
- Margins
- Commodity costs
- Capex
- Capacity
- Product launches
- Distribution
- Premiumization

---

# 51. Fundamental Thesis Generator

Generate the thesis from evidence:

```text
Business Model
+
Category / Product Position
+
Industry Demand
+
Units
+
Market Share
+
ASP / Mix
+
Premiumization
+
Distribution
+
Replacement Cycle
+
Seasonality
+
Channel Inventory
+
Capacity / Utilization
+
Commodity Economics
+
Margins
+
Cash Flow
+
Capital Efficiency
+
Balance Sheet
+
Management
+
Valuation
+
Risks
=
Fundamental Thesis
```

The thesis must distinguish:

### Evidence

What reported / calculated data shows.

### Interpretation

What the evidence may imply.

### Uncertainty

What cannot yet be established.

### Monitoring triggers

What future data could confirm or invalidate the interpretation.

---

# 52. Final Screener Output

The report should answer:

## Business

- What consumer category does the company operate in?
- What products drive revenue?
- Is the business mass-market or premium?
- What is the replacement exposure?

## Demand

- Is industry demand growing?
- Are company units growing?
- Is demand structural, cyclical or seasonal?

## Market Share

- Is the company gaining or losing share?
- Which categories are driving the change?

## Pricing & Mix

- Is ASP increasing?
- Is premiumization occurring?
- Is product mix improving?

## Distribution

- Is distribution expanding?
- Is dealer productivity improving?
- Is e-commerce changing the economics?

## Inventory

- Is sell-through healthy?
- Is channel inventory under control?
- Is revenue supported by end-consumer demand?

## Capacity

- Is utilization improving?
- Is new capacity justified?
- Is operating leverage emerging?

## Costs

- How sensitive is the company to copper, aluminium, steel, plastics and electronics/components?
- Is pass-through adequate?

## Financials

- Is revenue growing?
- What is driving the growth?
- Are margins improving?
- Is cash conversion strong?

## Capital Efficiency

- Is ROCE / ROIC improving?
- Is growth consuming excessive capital?

## Balance Sheet

- Is leverage manageable?
- Is working-capital funding under control?

## Management

- What is management guiding?
- Did prior guidance translate into results?
- Is capital allocation disciplined?

## Valuation

- How does valuation compare with history and peers?
- Does valuation reflect growth, margins and cash generation?

## Risks

- What could break the thesis?
- Which metrics should be monitored every quarter?

---

# 53. Implementation Principles

1. **Classify first, calculate second.**
2. **Analyze units before relying on revenue growth.**
3. **Separate volume, price and mix.**
4. **Track market share against industry growth.**
5. **Track premiumization separately from volume growth.**
6. **Separate sell-in from sell-through where possible.**
7. **Treat channel inventory as a critical diagnostic.**
8. **Track replacement demand separately from new-user demand.**
9. **Adjust for summer, festive, monsoon, winter and regional seasonality.**
10. **Track capacity utilization and operating leverage.**
11. **Track copper, aluminium, steel, plastics and electronics/components sensitivity.**
12. **Separate structural margin improvement from temporary commodity benefits.**
13. **Track distribution productivity, not just distribution count.**
14. **Separate accounting profit from cash generation.**
15. **Track capex → utilization → FCF → ROIC.**
16. **Track management guidance against subsequent results.**
17. **Compare companies by product/category economics, not only sector classification.**
18. **Never treat missing data as zero.**
19. **Retain metric lineage for every calculated value.**
20. **Explain WHY metrics changed, not merely whether they passed a threshold.**

---

# 54. Central Fundamental Question

The entire Consumer Durables analysis should ultimately answer:

> **Can this company sustainably grow units, market share and/or ASP through strong brands, products and distribution while maintaining healthy channel inventory, managing input costs and capacity utilization, and converting growth into durable free cash flow and ROIC across the consumer and replacement cycle?**
