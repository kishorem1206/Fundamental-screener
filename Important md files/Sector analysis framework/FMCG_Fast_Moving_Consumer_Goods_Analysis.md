# FMCG → Fast Moving Consumer Goods — Fundamental Analysis Framework

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
> - **Macro Sector:** FMCG
> - **Sector Value:** Fast Moving Consumer Goods
> - **Industries:** Personal Products; Beverages; Household Products; Agricultural Food & Other Products; Cigarettes & Tobacco Products; Food Products; Diversified FMCG

This is the standalone implementation framework for the **FMCG → Fast Moving Consumer Goods** sector value. It covers all seven industries in this classification and is designed for the Fundamental Analysis Screener.

# 2. FMCG Business-Model Classification

Every company should first be classified by category and business model.

## 2.1 Personal Products

Examples of categories:

- Beauty
- Skin care
- Hair care
- Oral care
- Personal hygiene
- Grooming
- Cosmetics

Track:

- Category growth
- Volume growth
- Price/mix
- Premium products
- Brand contribution
- Distribution
- Market share
- Gross margin
- Advertising intensity

---

## 2.2 Beverages

Classify:

- Packaged foods/beverages
- Soft drinks
- Bottled water
- Tea
- Coffee
- Juices
- Dairy beverages
- Alcoholic beverages only where classified within the relevant company/industry dataset

Track:

- Volume
- Realization
- Pack sizes
- Rural/urban mix
- Channel mix
- Distribution
- Input costs
- Seasonality
- Capacity
- Brand/category share

---

## 2.3 Household Products

Track:

- Detergents
- Home cleaning
- Surface care
- Dishwashing
- Household consumables
- Other recurring-use products

Key metrics:

- Volume growth
- Price/mix
- Market share
- Distribution
- Product penetration
- Gross margin
- Promotional intensity
- Raw-material sensitivity

---

## 2.4 Agricultural Food & Other Products

Classify according to actual business:

- Edible oils
- Staples
- Grains
- Spices
- Agricultural products
- Commodity-linked food products

These businesses require greater emphasis on:

- Commodity prices
- Procurement economics
- Inventory
- Working capital
- Realization
- Gross margin
- Hedging
- Processing spread

---

## 2.5 Cigarettes & Tobacco Products

Track:

- Volume
- Realization
- Price increases
- Product mix
- Premiumization
- Market share
- Tax impact
- Excise/GST effects
- Illicit/unorganized market exposure
- Gross margin
- Cash generation

Do not treat cigarette volume, pricing and tax changes as interchangeable drivers.

---

## 2.6 Food Products

Classify:

- Packaged foods
- Biscuits
- Snacks
- Ready-to-eat
- Dairy/food products
- Staples
- Processed foods
- Premium food categories

Track:

- Volume
- Price/mix
- Category growth
- Market share
- Distribution
- Premiumization
- Raw-material costs
- Gross margin
- New-product contribution

---

## 2.7 Diversified FMCG

For diversified companies, analyze each major category separately.

Track:

- Segment revenue
- Segment EBITDA
- Segment EBIT
- Growth
- Margin
- Market share
- Capital employed
- ROCE/ROIC
- Capex
- Working capital

Use segment-level analysis before consolidated conclusions.

---

# 3. Common Financial Dataset

Collect annual, quarterly and TTM data.

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
- P/E
- EV/EBITDA
- P/B
- EV/Sales
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
- Finance cost
- Depreciation
- Tax rate
- Exceptional items

Always separate:

**Core operating revenue → operating profit → other income → exceptional items → PAT**

---

# 4. Revenue Growth Decomposition

For FMCG companies, revenue growth should be decomposed into:

**Volume + Price + Mix + Distribution + Acquisitions + Currency**

Where available calculate:

### Volume Growth

Change in underlying units sold.

### Price Growth

Growth attributable to price increases.

### Mix Growth

Contribution from:

- Premium products
- Pack-size changes
- Category mix
- Geography
- Channel mix

### Distribution Growth

Contribution from:

- New outlets
- Rural expansion
- Modern trade
- E-commerce
- Quick commerce
- Direct distribution

A company reporting 10% revenue growth with 1% volume growth and 9% price/mix growth should not be interpreted the same way as a company delivering 8–10% volume growth.

---

# 5. Volume Analysis

Track:

- Volume growth YoY
- Volume growth QoQ
- 3Y volume CAGR
- 5Y volume CAGR where available
- Category volume growth
- Company volume growth
- Market volume growth
- Rural volume
- Urban volume
- Modern trade
- General trade
- E-commerce
- Quick commerce

Compare:

**Company Volume Growth vs Category Growth**

and:

**Company Volume Growth vs Market/Peer Growth**

Persistent market-share gains are more informative than one-quarter volume growth.

---

# 6. Price/Mix Analysis

Track:

- Pricing growth
- Realization growth
- Premiumization
- Product mix
- Pack-size mix
- Channel mix
- Geography mix

Separate:

**Healthy pricing power**

from:

**Commodity inflation pass-through**

and:

**Temporary price increases during inflation.**

Monitor whether volume remains resilient after price increases.

---

# 7. Market Share Analysis

Where reliable data is available track:

- Current market share
- Market-share change
- Category leadership
- Regional share
- Premium segment share
- Rural share
- Modern-trade share

Analyze:

**Distribution → Availability → Trial → Repeat Purchase → Market Share**

Market-share gains should be supported by evidence rather than inferred from revenue growth alone.

---

# 8. Distribution Analysis

Track:

- Total outlets
- Direct outlets
- Rural outlets
- Urban outlets
- Distributors
- Stockists
- Retail reach
- Numeric distribution
- Weighted distribution
- E-commerce presence
- Quick-commerce presence

Calculate where possible:

- Revenue/outlet
- Volume/outlet
- Revenue/distributor
- Outlet productivity
- Distribution growth

For FMCG businesses, distribution can be a structural competitive advantage.

---

# 9. Brand & Competitive Advantage

Assess:

- Brand awareness
- Brand strength
- Category leadership
- Pricing power
- Consumer loyalty
- Repeat purchase
- Product differentiation
- Distribution reach
- Advertising efficiency
- Innovation pipeline
- Premiumization ability

Do not treat brand value as a qualitative assumption only. Seek evidence through:

- Market share
- Pricing resilience
- Volume retention
- Gross margin
- Advertising efficiency
- Category growth
- Consumer/product data where available

---

# 10. Gross Margin Analysis

Gross margin is a critical FMCG metric.

Track:

- Gross profit
- Gross margin
- Gross-margin change
- Raw-material inflation
- Pricing recovery
- Mix
- Premiumization

Analyze:

**Input Cost → Pricing → Mix → Gross Margin**

Identify whether margin expansion comes from:

- Lower commodity costs
- Price increases
- Premiumization
- Product mix
- Manufacturing efficiency
- Temporary input deflation

---

# 11. Raw-Material Cost Analysis

Identify major inputs by company/category.

Examples:

- Palm oil
- Crude-linked inputs
- Milk
- Wheat
- Sugar
- Coffee
- Tea
- Packaging materials
- Paper
- Plastic
- Aluminium
- Cocoa
- Agri commodities

Track:

- Benchmark price
- Company procurement price where available
- Lag effect
- Hedging
- Inventory
- Cost pass-through

Analyze:

**Commodity Price → Input Cost → Gross Margin → Pricing → Volume → EBITDA**

---

# 12. EBITDA & Operating Margin

Track:

- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- Margin expansion/contraction
- A&P spend
- Employee cost
- Distribution cost
- Freight
- Manufacturing cost

Decompose margin changes:

**Gross Margin Change + Operating Leverage + A&P + Employee Cost + Distribution Cost + Other Costs**

Avoid concluding that margin expansion is structural until the underlying drivers are identified.

---

# 13. Advertising & Promotion Analysis

Track:

- Advertising & promotion expense
- A&P/revenue
- Brand investment
- Promotional discounts
- Trade schemes
- Sales incentives

Analyze:

**A&P Spend → Brand Demand → Volume Growth → Market Share → Revenue → Profit**

Important distinction:

- Underinvestment may improve short-term margins but weaken brands.
- Excessive spending may suppress short-term margins without producing adequate growth.

Look for evidence of advertising efficiency through volume, market share and category growth.

---

# 14. Pricing Power

Assess pricing power through:

- Ability to increase prices
- Volume retention after price increases
- Gross-margin resilience
- Premiumization
- Brand strength
- Market-share stability
- Competitor response

A useful causal test:

**Price Increase → Volume Change → Market Share → Gross Margin → EBITDA**

Pricing power should not be inferred from a single quarter.

---

# 15. Premiumization

Track:

- Premium category growth
- Premium SKU mix
- Premium revenue %
- ASP
- Gross-margin contribution
- Urban/rural premiumization
- New premium launches

Analyze:

**Income/Consumer Shift → Premium Mix → ASP → Gross Margin → EBIT**

Premiumization can improve economics even when volume growth is moderate.

---

# 16. Rural vs Urban Analysis

Track:

- Rural revenue/volume
- Urban revenue/volume
- Rural growth
- Urban growth
- Rural distribution
- Rural penetration
- Wage/income environment where relevant

Compare:

**Rural Growth vs Urban Growth**

and:

**Company Rural Growth vs Category Rural Growth**

Do not assume rural recovery solely from macro indicators.

---

# 17. Channel Analysis

Separate:

- General trade
- Modern trade
- E-commerce
- Quick commerce
- Institutional/B2B
- Direct-to-consumer

Track:

- Channel growth
- Channel margin
- Trade discounts
- Customer concentration
- Fulfillment cost
- Returns
- Promotional intensity

Important:

Rapid digital-channel growth may increase revenue while changing gross margin, fulfillment costs and customer economics.

---

# 18. New Product & Innovation Analysis

Track:

- New launches
- New-product revenue %
- Innovation pipeline
- Category extensions
- Premium products
- Product discontinuations
- Launch success
- Cannibalization

Evaluate:

**R&D/Innovation → Launch → Distribution → Adoption → Revenue → Margin**

Do not count every launch as a growth driver.

---

# 19. Working Capital Analysis

Track:

- Receivable days
- Inventory days
- Payable days
- Cash conversion cycle
- Inventory growth
- Distributor inventory
- Finished goods inventory
- Raw-material inventory

Calculate:

**CCC = Receivable Days + Inventory Days − Payable Days**

Analyze:

**Revenue Growth → Inventory → Receivables → Payables → CFO**

Red flags:

- Inventory growing faster than sales
- Receivables growing faster than revenue
- Persistent working-capital deterioration
- Distributor/channel stuffing indicators
- CFO lagging PAT

---

# 20. Cash Flow Quality

Track:

- CFO
- EBITDA
- PAT
- CFO/PAT
- CFO/EBITDA
- FCF
- FCF margin
- FCF/PAT
- FCF yield

Separate:

- Sustainable operating cash flow
- Working-capital release
- One-off tax effects
- Asset sales
- Exceptional receipts

Core relationship:

**EBITDA → CFO → Capex → FCF**

A high-quality FMCG company should demonstrate durable conversion of accounting earnings into cash over time.

---

# 21. Capex & Manufacturing Economics

Track:

- Maintenance capex
- Growth capex
- Capacity additions
- Plant utilization
- Capex/revenue
- Capex/depreciation
- New manufacturing facilities
- Automation
- Contract manufacturing

Analyze:

**Capex → Capacity → Utilization → Volume → Revenue → EBITDA → FCF → ROIC**

For major projects track:

- Initial cost
- Revised cost
- Planned capacity
- Start date
- Actual commissioning
- Utilization
- Expected returns

---

# 22. Asset-Light vs Asset-Heavy Model

Classify manufacturing model:

- Owned manufacturing
- Contract manufacturing
- Hybrid

Compare:

- Fixed assets
- Asset turnover
- ROCE
- Gross margin
- Supply-chain control
- Capex requirements
- Working capital

Asset-light businesses may have lower capital requirements, but the engine must assess whether outsourcing creates dependency or quality/supply risks.

---

# 23. Return Ratios

Track:

- ROE
- ROCE
- ROIC
- ROA
- Asset turnover
- Incremental ROIC
- Incremental ROCE

Analyze:

**Revenue Growth → EBIT → Capital Employed → ROIC**

A strong FMCG business should ideally combine:

- Brand strength
- Growth
- High margins
- High asset turns
- Strong cash conversion
- High returns on incremental capital

---

# 24. Balance Sheet Analysis

Track:

- Cash
- Investments
- Gross debt
- Net debt
- Net debt/EBITDA
- Debt/equity
- Interest coverage
- Lease liabilities
- Goodwill
- Intangibles
- Contingent liabilities

Assess:

- Acquisition leverage
- Dividend sustainability
- Buyback capacity
- Down-cycle resilience
- Liquidity

---

# 25. Acquisition Analysis

For acquisitions track:

- Purchase price
- Revenue acquired
- EBITDA acquired
- EBITDA margin
- Valuation multiple
- Funding
- Debt impact
- Goodwill
- Intangibles
- Synergy assumptions
- Actual synergy
- Post-acquisition growth
- ROIC

Analyze:

**Acquisition → Revenue → Synergy → EBITDA → Cash Flow → ROIC**

Flag acquisitions that grow revenue but reduce returns on capital.

---

# 26. Management & Capital Allocation

Track:

- Dividend payout
- Buybacks
- Acquisitions
- Capex
- Debt repayment
- Cash accumulation
- Minority investments
- New categories

Evaluate management's history of:

- Reinvestment
- Brand investment
- Pricing
- Acquisitions
- Cost discipline
- Shareholder returns

Analyze:

**FCF → Reinvestment / Dividend / Buyback / Acquisition → Incremental Return**

---

# 27. Concall & Management Guidance Analysis

Extract:

- Volume guidance
- Pricing outlook
- Commodity-cost outlook
- Gross-margin outlook
- Rural demand
- Urban demand
- Distribution expansion
- Market-share commentary
- A&P plans
- New-product launches
- Capex guidance
- Acquisition plans

Track:

**Guidance → Actual → Variance → Management Explanation**

Classify guidance as:

- MET
- EXCEEDED
- MISSED
- REVISED

Do not treat management guidance as reported fact.

---

# 28. Governance & Integrity

Track:

- Promoter holding
- Promoter pledge
- Promoter buying/selling
- Share dilution
- Related-party transactions
- Auditor changes
- Auditor qualifications
- Regulatory actions
- Executive remuneration
- Subsidiary transactions
- Contingent liabilities

Look for:

- Persistent related-party transactions
- Unexplained receivables
- Aggressive accounting
- Frequent exceptional items
- Unusual acquisitions
- Excessive dilution

---

# 29. Competitive Structure

Assess:

- Number of major competitors
- Category concentration
- Private-label pressure
- Organized vs unorganized market
- Distribution barriers
- Brand barriers
- Switching costs
- Regulatory barriers

For each major category identify:

- Market leader
- Challenger
- Premium leader
- Value player
- Emerging brands

Do not infer market leadership without reliable evidence.

---

# 30. Category Growth

Track:

- Industry/category growth
- Company growth
- Market-share change
- Volume growth
- Pricing
- Premiumization

Decompose:

**Category Growth + Market Share Gain = Company Volume Opportunity**

A company growing because the whole category is growing has different economics from one taking share in a stagnant category.

---

# 31. Seasonality

Track:

- Quarterly revenue
- Quarterly volume
- Quarterly margin
- Seasonal categories
- Festival demand
- Weather sensitivity
- Agricultural cycles

Compare:

- YoY
- QoQ where meaningful
- 3Y seasonal averages

Do not interpret sequential changes without considering seasonality.

---

# 32. Commodity-Cycle Analysis

For commodity-sensitive FMCG categories:

Track:

- Input commodity price
- Historical average
- Current percentile
- Company pricing
- Gross margin
- Inventory effects

Classify:

- Input inflation
- Peak inflation
- Normalization
- Deflation

Analyze:

**Commodity Cycle → Input Cost → Pricing → Volume → Gross Margin → EBITDA → CFO**

Normalize earnings before assigning long-term valuation.

---

# 33. Valuation Framework

Use multiple methods.

## P/E

Track:

- Current P/E
- Historical median
- Historical percentile
- Forward P/E where reliable
- EPS growth

## EV/EBITDA

Useful for comparing businesses with different:

- Capital structures
- Depreciation
- Acquisition histories

## EV/Sales

Use selectively for:

- Low-margin businesses
- Early-stage categories
- Companies where earnings are temporarily depressed

## FCF Yield

Calculate:

**FCF Yield = FCF / Market Capitalization**

## PEG

Use only when:

- Growth is reasonably sustainable
- Earnings quality is strong
- Growth assumptions are credible

Do not blindly apply PEG to cyclical or commodity-driven earnings.

---

# 34. Brand/Quality Premium in Valuation

Where a company has:

- Strong brands
- Market leadership
- High ROIC
- Durable cash flow
- Pricing power
- Low leverage

the market may assign a premium valuation.

The engine should not automatically justify that premium.

Instead compare:

**Valuation Premium → Growth Premium → ROIC Premium → Cash-Flow Quality → Competitive Advantage**

---

# 35. Historical Valuation

Track:

- Historical P/E
- Historical EV/EBITDA
- Historical P/S
- Historical FCF yield
- Historical valuation percentile

Compare current valuation with:

1. Own history
2. Relevant peers
3. Growth rate
4. ROIC
5. Margin
6. Cash conversion
7. Market-share trajectory
8. Category growth
9. Normalized earnings

No universal hard-coded P/E threshold should be used.

---

# 36. Normalized Earnings

Adjust for:

- Commodity inflation/deflation
- Temporary gross-margin spikes
- Inventory effects
- Exceptional items
- One-off tax impacts
- Acquisition effects

Calculate:

- Normalized revenue
- Normalized gross margin
- Normalized EBITDA
- Normalized EBIT
- Normalized PAT
- Normalized CFO
- Normalized FCF

All normalized values must be labelled:

**ESTIMATED**

---

# 37. Causal Analysis Chains

## Core FMCG

**Category Demand → Volume → Price/Mix → Revenue → Gross Margin → EBITDA → CFO → FCF → ROIC**

## Brand-Led Growth

**Brand Strength → Distribution → Market Share → Volume → Pricing → Gross Margin → EBITDA → FCF**

## Commodity-Sensitive FMCG

**Input Commodity → Cost/Unit → Pricing → Volume → Gross Margin → EBITDA → CFO**

## Premiumization

**Consumer Shift → Premium Mix → ASP → Gross Margin → EBIT → FCF**

## Distribution Expansion

**Outlet Addition → Availability → Volume → Revenue → Operating Leverage → EBITDA → FCF**

## New Product

**Innovation → Launch → Distribution → Adoption → Volume → Revenue → Margin → ROIC**

The final analysis should identify the actual growth and profit engine rather than merely listing ratios.

---

# 38. Red-Flag Engine

## Growth

- Revenue growth entirely price-led
- Weak/negative volume growth
- Market-share loss
- Growth below category for prolonged periods
- Excessive acquisition dependence

## Margin

- Margin expansion caused only by temporary input deflation
- Price increases without volume resilience
- Aggressive cost cutting
- Underinvestment in brands
- Rising trade promotions

## Working Capital

- Inventory growth > sales growth
- Receivables growth > sales growth
- CFO consistently below PAT
- Channel stuffing indicators

## Balance Sheet

- Acquisition-driven leverage
- High goodwill
- Weak interest coverage
- Debt-funded shareholder distributions

## Governance

- Promoter pledge
- Frequent dilution
- Related-party concerns
- Auditor qualifications
- Frequent exceptional items

## Valuation

- Premium multiple without corresponding growth/ROIC
- Peak-margin earnings capitalized at normal multiples
- FCF yield inconsistent with business quality

---

# 39. Positive-Signal Engine

Look for:

- Consistent volume growth
- Market-share gains
- Strong distribution expansion
- Pricing power
- Premiumization
- High gross margins
- Stable/improving EBITDA margins
- Strong CFO conversion
- High ROIC
- Low leverage
- Strong brands
- Category leadership
- Successful innovation
- Disciplined capital allocation
- Sustainable FCF

Every positive signal should be backed by measurable evidence.

---

# 40. Scenario Analysis

## Bull Case

Assume:

- Strong category growth
- Volume growth
- Market-share gains
- Pricing power
- Premiumization
- Favorable input costs
- Margin expansion

## Base Case

Assume:

- Normal category growth
- Normal volume
- Stable market share
- Normalized gross margin
- Normal A&P
- Normal working capital

## Bear Case

Assume:

- Weak demand
- Volume decline
- Commodity inflation
- Limited pricing power
- Market-share loss
- Margin compression
- Higher working capital

Calculate impact on:

- Revenue
- Gross profit
- EBITDA
- PAT
- CFO
- FCF
- ROIC
- EPS
- Valuation

---

# 41. Scoring Architecture

Suggested base weighting:

| Dimension | Weight |
|---|---:|
| Brand / Competitive Advantage | 15% |
| Volume & Market Share | 15% |
| Revenue Quality / Growth | 10% |
| Gross Margin / Pricing Power | 10% |
| Operating Quality | 10% |
| Cash Flow Quality | 15% |
| Balance Sheet | 10% |
| ROIC / Capital Efficiency | 5% |
| Management & Governance | 5% |
| Valuation | 5% |

Weights can be adjusted by industry.

Examples:

- Personal Products → brand, pricing and premiumization
- Beverages → volume, distribution and seasonality
- Food → volume, commodity costs and gross margin
- Tobacco → pricing, volume, taxation and cash flow
- Agricultural food → commodity procurement, spreads and working capital
- Diversified FMCG → segment economics and capital allocation

Do not generate a high-confidence score when critical operating or category data is unavailable.

---

# 42. Data Quality Framework

Every metric should carry:

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

Examples:

- Revenue from annual report → REPORTED
- Revenue CAGR → CALCULATED
- Normalized EBITDA → ESTIMATED
- Management volume guidance → MANAGEMENT-DISCLOSED
- Market-share estimate from external research → THIRD-PARTY

Never manufacture missing category, volume or market-share data.

---

# 43. Source Hierarchy

Preferred sources:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. NSE/BSE filings
6. Company investor-relations disclosures
7. Regulatory filings
8. Official industry/category data
9. Reliable financial databases
10. Third-party research

Source-specific metrics should retain their provenance.

---

# 44. Agent Architecture

Recommended pipeline:

```text
Company Identification Agent
        ↓
Industry / Category Classification Agent
        ↓
Business Model Agent
        ↓
Financial Data Agent
        ↓
Revenue Decomposition Agent
        ↓
Volume & Price/Mix Agent
        ↓
Market Share Agent
        ↓
Distribution Agent
        ↓
Brand / Competitive Advantage Agent
        ↓
Commodity Input Agent
        ↓
Gross Margin Agent
        ↓
Operating Margin Agent
        ↓
Working Capital Agent
        ↓
Cash Flow Agent
        ↓
Capex Agent
        ↓
ROIC Agent
        ↓
Management / Concall Agent
        ↓
Governance Agent
        ↓
Peer Comparison Agent
        ↓
Valuation Agent
        ↓
Normalization Agent
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

# 45. Recommended Database Structure

## Company

- company_id
- company_name
- sector
- industry
- sub_industry
- business_model
- category
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

## FMCG Operating Metric

- company_id
- metric_name
- value
- period
- unit
- category
- segment
- geography
- channel
- source
- confidence

## Category Data

- category
- market_size
- category_growth
- company_market_share
- market_share_change
- period
- source
- confidence

## Input Commodity

- commodity
- benchmark
- price
- date
- unit
- source

## Distribution

- company_id
- outlet_type
- outlet_count
- period
- geography
- productivity
- source

## Product / Brand

- company_id
- brand
- category
- premium/value
- revenue
- growth
- market_share
- source

## Guidance

- company_id
- guidance_date
- metric
- guidance_value
- period
- actual_value
- variance
- explanation

## Valuation

- company_id
- valuation_method
- metric
- normalized_value
- multiple
- current_value
- historical_median
- peer_median
- percentile
- confidence

---

# 46. Final Screener Output

## 1. Company Snapshot

- Business
- FMCG category
- Market cap
- Revenue
- EBITDA
- PAT
- ROIC
- Net debt
- FCF

## 2. Category Exposure

Show:

- Major categories
- Revenue contribution
- Growth
- Market share
- Competitive position

## 3. Growth Quality

- Revenue growth
- Volume growth
- Price growth
- Mix
- Market-share change
- Distribution growth

## 4. Brand & Competitive Advantage

- Brand strength
- Pricing power
- Distribution
- Premiumization
- Category leadership

## 5. Margin Quality

- Gross margin
- EBITDA margin
- EBIT margin
- Input-cost impact
- Pricing impact
- Mix impact
- A&P

## 6. Cash Quality

- CFO
- FCF
- CFO/PAT
- Working capital
- Capex

## 7. Balance Sheet

- Net debt
- Net debt/EBITDA
- Interest coverage
- Liquidity
- Goodwill/intangibles

## 8. Capital Efficiency

- ROE
- ROCE
- ROIC
- Incremental ROIC
- Asset turnover

## 9. Management

- Guidance
- Capital allocation
- Acquisitions
- Concall observations
- Governance

## 10. Valuation

- P/E
- EV/EBITDA
- FCF yield
- Historical valuation
- Peer valuation
- Normalized valuation

## 11. Causal Analysis

Explain:

**Demand → Volume → Price/Mix → Revenue → Gross Margin → EBITDA → CFO → FCF → ROIC**

## 12. Red Flags

For each:

- Issue
- Severity
- Evidence
- Source
- Potential impact

## 13. Positive Signals

Evidence-backed strengths.

## 14. Investment Thesis

Produce:

- Business thesis
- Category thesis
- Volume thesis
- Pricing thesis
- Brand/distribution thesis
- Margin thesis
- Cash-flow thesis
- Capital-efficiency thesis
- Valuation thesis
- Bull case
- Bear case
- Key risks
- Thesis-break conditions
- Next-quarter metrics to monitor

---

# 47. Implementation Principles

1. Classify the company by category before applying ratios.
2. Separate volume from price.
3. Separate price from mix.
4. Track market-share movement.
5. Track distribution and outlet productivity.
6. Identify major raw-material exposures.
7. Analyze gross-margin movement through input costs and pricing.
8. Separate temporary commodity benefits from structural margin improvement.
9. Track A&P and brand investment.
10. Analyze working capital carefully.
11. Prioritize CFO and FCF over accounting PAT alone.
12. Measure ROIC and incremental ROIC.
13. Analyze acquisitions separately from organic growth.
14. Track management guidance against actual outcomes.
15. Normalize earnings where commodity/input cycles distort margins.
16. Compare valuation with company history and relevant peers.
17. Do not use a universal P/E or PEG threshold.
18. Preserve source provenance for every material metric.
19. Clearly label reported, calculated, estimated and management-disclosed data.
20. Do not manufacture unavailable market-share, volume or category data.
21. Make the final thesis traceable to underlying operating evidence and cash generation.

---

# 48. Sector-Level Fundamental Question

The final FMCG engine should answer:

> **Is this FMCG company gaining durable consumer demand through volume, pricing, mix, brands and distribution, while converting that growth into sustainable margins, cash flow and high returns on capital, and is the current valuation supported by normalized long-term earnings power?**

The analysis should distinguish **real growth from inflation-led growth, temporary margin benefits from structural profitability, and accounting earnings from sustainable cash generation**.

