# Consumer Discretionary → Automobile and Auto Components — Fundamental Analysis Framework

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
**Sector Value:** Automobile and Auto Components  
**Industries:** Auto Components; Automobiles

The source framework classifies Automobiles into passenger vehicles, two-wheelers, three-wheelers, commercial vehicles, tractors, electric vehicles and premium/luxury vehicles. Auto Components are classified into engines/powertrain, transmission, braking, electrical/electronics, tyres, castings/forgings, interiors, body systems, EV components and Tier-1/Tier-2 suppliers. The core sector drivers are volume, ASP, mix, market share, capacity, utilization, commodity costs, new launches, EV mix and export mix. fileciteturn22file0

The engine must move through:

**RAW DATA → NORMALIZATION → CALCULATED METRICS → TREND → PEER → CAUSAL ANALYSIS → RED FLAGS → SCORING → INVESTMENT THESIS**

> Implementation rule: classify the company and its business model first. An OEM, tyre manufacturer, EV-component supplier and diversified Tier-1 supplier do not have identical economics.

---

# 2. Business-Model Classification

## 2.1 Automobiles

Classify the company by:

- Passenger vehicles
- Two-wheelers
- Three-wheelers
- Commercial vehicles
- Tractors
- Electric vehicles
- Premium/luxury vehicles

Also classify:

- Domestic vs export
- Mass-market vs premium
- ICE vs EV
- OEM vs replacement exposure
- Product / platform concentration
- Vehicle segment exposure

### Core OEM drivers

- Units sold
- Domestic volume
- Export volume
- Segment volume
- Market share
- ASP
- Product mix
- Premium mix
- EV mix
- Capacity
- Utilization
- Dealer inventory
- New launches
- Model age
- Discounts
- Incentives
- Finance penetration

The source framework specifically identifies units sold, domestic/export/segment volume, market share and dealer inventory as volume metrics; ASP, premium mix, SUV/premium mix, EV mix, discounts, incentives and finance penetration as pricing/mix metrics. fileciteturn22file2

---

## 2.2 Auto Components

Classify the supplier by:

### Product

- Engines / powertrain
- Transmission
- Braking
- Electrical / electronics
- Tyres
- Castings / forgings
- Interiors
- Body systems
- EV components

### Customer

- OEM
- Aftermarket / replacement
- Export customer
- Domestic customer

### Supplier tier

- Tier-1
- Tier-2
- Other

### Technology

- ICE
- Hybrid
- EV
- EV-agnostic

### Geography

- India
- Export
- Region / country where disclosed

The source framework specifically requires supplier classification by product, customer, tier, geography, ICE/EV exposure and replacement/OEM exposure. fileciteturn22file3

---

# 3. Revenue Architecture

Decompose revenue before interpreting growth.

Track:

- Vehicle sales revenue
- Component revenue
- Replacement / aftermarket revenue
- Export revenue
- Domestic revenue
- Product-segment revenue
- Geography revenue
- OEM revenue
- Other operating revenue
- Other income

For OEMs separate:

**Volume × ASP / Mix → Revenue**

For component suppliers:

**Vehicle Production × Content / Vehicle → Supplier Revenue**

Where applicable, separately identify:

- Organic growth
- Acquisition-led growth
- Currency impact
- Price pass-through
- New program contribution
- New product contribution

---

# 4. Demand Analysis

Automobile demand is influenced by:

- Consumer income
- Employment
- Interest rates
- Financing availability
- Fuel prices
- Replacement cycle
- Urban demand
- Rural demand
- Infrastructure spending
- Freight activity
- Construction activity
- Agricultural income
- Fleet replacement
- Product launches
- Regulatory changes
- EV adoption

Track:

- Industry volume growth
- Company volume growth
- Segment growth
- Domestic demand
- Export demand
- Retail volume where available
- Wholesale volume
- Dealer inventory
- Waiting periods where disclosed
- Booking trends where disclosed

Important:

**Wholesale growth ≠ necessarily end-consumer demand.**

Where available, separate:

**Production → Dispatch → Dealer Inventory → Retail / Registration**

This helps identify channel loading.

---

# 5. Volume Analysis

Track:

- Units sold
- Domestic units
- Export units
- Segment units
- Monthly volume
- Quarterly volume
- Annual volume
- Volume growth
- Market share
- Product-level volume
- Model-level volume where available

Calculate:

- YoY volume growth
- QoQ volume growth where meaningful
- 3Y volume CAGR
- 5Y volume CAGR
- Domestic volume CAGR
- Export volume CAGR

For components track:

- Customer production
- Component volumes
- New program volumes
- Replacement volumes

The source framework explicitly emphasizes volume decomposition for automobiles and auto components. fileciteturn22file2

---

# 6. Market Share Analysis

Track:

- Overall market share
- Segment market share
- Product market share
- Domestic share
- Export share
- EV share
- Premium-segment share

Analyze:

**Company Volume Growth vs Industry Volume Growth**

Possible interpretation:

- Company growth > industry growth → potential share gain
- Company growth < industry growth → potential share loss

But confirm using reported market-share data where available.

For components also track:

- Customer share
- Content per vehicle
- Program wins
- New OEM relationships
- Customer additions

---

# 7. Pricing & ASP Analysis

Track:

- ASP
- Realization per vehicle
- Realization per component
- Price increases
- Discounts
- Incentives
- Finance schemes
- Premiumization
- Product mix
- Variant mix
- Geographic mix
- EV mix

Calculate:

**ASP = Revenue / Units**

where the revenue and unit definitions are sufficiently comparable.

Analyze:

**Revenue Growth = Volume Growth + Price Effect + Mix Effect + Currency + Acquisitions**

A company growing revenue primarily through price/mix should not automatically be treated as having the same demand strength as a company growing through volume. The source framework makes this distinction explicit. fileciteturn22file4

---

# 8. Product Mix Analysis

For OEMs track:

- Entry-level vs premium
- SUV / premium segment
- Sedan / hatchback where relevant
- Commercial vehicle categories
- Motorcycle / scooter mix
- Tractor mix
- EV mix
- Hybrid mix
- High-margin model mix

Analyze:

**Mix Shift → ASP → Gross Margin → EBITDA Margin**

Look for:

- Premiumization
- Higher-content products
- EV mix
- Product mix deterioration
- Dependence on one high-margin model

---

# 9. EV Transition Analysis

Classify exposure:

- ICE-heavy
- ICE + hybrid
- EV-ready
- EV-focused
- EV-component supplier
- EV-agnostic supplier

Track:

- EV volume
- EV mix
- EV revenue
- EV market share
- EV capacity
- EV models
- EV launches
- EV battery / powertrain exposure
- EV component content
- EV order book
- EV customer concentration

For component suppliers track:

- ICE revenue exposure
- EV revenue exposure
- Product substitution risk
- New EV programs
- EV content per vehicle
- Investment required for transition

Analyze:

**ICE Volume → EV Transition → Product Mix → Content / Vehicle → Revenue → Margin → Capex → ROIC**

Flag:

- High ICE exposure with limited transition plan
- Large EV capex without order visibility
- Technology transition causing stranded assets
- Customer concentration in a single EV platform

---

# 10. Capacity Analysis

Track:

- Installed capacity
- Capacity additions
- Plant count
- Plant location
- Capacity utilization
- New plants
- Expansion capex
- Capacity under construction
- CWIP

Calculate:

- Capacity utilization
- Revenue / capacity
- EBITDA / capacity
- Incremental revenue / incremental capacity where possible

Core chain:

**Capex → Capacity → Utilization → Revenue → EBIT → CFO → FCF → ROIC**

The source framework explicitly uses this capacity-to-ROIC chain and flags large capex without demand visibility and low utilization after expansion. fileciteturn22file3

---

# 11. Utilization & Operating Leverage

Track:

- Capacity utilization
- Fixed costs
- Variable costs
- Revenue growth
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
- Operating leverage

The common Consumer Discretionary framework specifically requires this analysis of operating leverage and its drivers. fileciteturn22file4

---

# 12. Dealer Inventory Analysis

For OEMs track where disclosed:

- Dealer inventory
- Inventory days
- Dispatches
- Retail sales
- Wholesale vs retail gap
- Discounts
- Incentives
- Waiting periods

Analyze:

**Production → Dispatch → Dealer Inventory → Retail**

Flag:

- Dispatch growth with rising dealer inventory
- High inventory combined with increasing discounts
- Weak retail demand hidden by wholesale growth
- Persistent inventory build

This is important because reported unit sales may not represent underlying end-customer demand.

---

# 13. Auto Component Economics

Track:

- Revenue / customer
- Customer concentration
- Revenue by geography
- OEM vs aftermarket
- EV share
- Capacity
- Utilization
- New programs
- Order book
- Content / vehicle

The source framework explicitly identifies these as core component metrics. fileciteturn22file3

### Core component causal chain

**Vehicle Production → Content / Vehicle → Supplier Revenue → Utilization → Margin → CFO**

Use this chain to explain changes in component-company performance.

---

# 14. Content per Vehicle

For component suppliers, track:

- Content / vehicle
- Product value / vehicle
- Number of components supplied
- New products per vehicle
- EV content / vehicle
- Customer platform penetration

Analyze:

**Vehicle Volume Growth + Content / Vehicle Growth → Supplier Revenue Growth**

This allows the engine to distinguish:

- Pure industry-volume growth
- Market-share gains
- Content expansion
- New program contribution
- Price pass-through

---

# 15. Customer Concentration

Track:

- Top customer %
- Top 5 customers %
- Revenue / customer
- OEM exposure
- Aftermarket exposure
- Export customer concentration
- Platform concentration

Assess:

- Bargaining power
- Switching risk
- Program duration
- Customer diversification
- Dependency on one OEM

Flag:

- Excessive customer concentration
- One customer driving most growth
- Major customer loss
- Customer price pressure
- New program dependence

The source framework specifically flags excessive customer concentration for component companies. fileciteturn22file3

---

# 16. Order Book & New Programs

For component suppliers track:

- Order book
- New business wins
- RFQs / nominations where disclosed
- New programs
- SOP dates
- Program duration
- Lifetime revenue opportunity where disclosed
- Customer additions
- EV program wins

Analyze:

**Order Win → SOP → Volume Ramp → Utilization → Revenue → Margin → Cash**

Do not treat announced order value as current revenue.

Track conversion:

**Order Book → Actual Revenue**

---

# 17. Commodity Cost Analysis

The source framework identifies:

- Steel
- Aluminium
- Rubber
- Precious metals
- Battery materials

as key automobile commodity sensitivities. fileciteturn22file3

Depending on the company, also track:

- Plastics
- Resins
- Copper
- Energy
- Freight
- Other major inputs

Analyze:

**Commodity Price → Input Cost → Gross Margin → EBITDA → CFO**

Determine:

- Pass-through mechanism
- Pass-through lag
- Contractual protection
- Pricing reset frequency
- Inventory impact
- Hedging where disclosed

Flag:

- Commodity inflation without price pass-through
- Margin compression from input inflation
- Margin expansion caused mainly by temporary commodity deflation

---

# 18. Gross Margin Analysis

Track:

- Material cost / revenue
- Employee cost / revenue
- Power / fuel
- Freight
- Warranty
- R&D
- Selling costs
- Other operating expenses

Analyze:

**ASP / Realization → Material Cost → Gross Margin → EBITDA**

For component suppliers especially analyze:

**Commodity Cost + Price Pass-through + Product Mix → Gross Margin**

Separate:

- Structural improvement
- Temporary commodity benefit
- Pricing
- Mix
- Productivity

---

# 19. EBITDA & EBIT Analysis

Track:

- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- Incremental EBITDA margin
- Incremental EBIT margin
- PAT margin

Explain changes through:

- Volume
- ASP
- Mix
- Utilization
- Commodity costs
- Productivity
- New plant costs
- Launch costs
- R&D
- Warranty costs
- Foreign exchange
- Operating leverage

Do not describe margin expansion as structural without evidence.

---

# 20. R&D & Product Development

Track:

- R&D expense
- R&D / revenue
- Capitalized development cost where disclosed
- New model launches
- New platforms
- EV development
- Battery / electronics development
- Technology investments
- Product pipeline

Assess:

- Innovation intensity
- Product competitiveness
- EV readiness
- Model replacement cycle
- R&D efficiency

Flag:

- Declining product competitiveness
- Underinvestment in technology transition
- High R&D spending without visible product pipeline
- Capitalization of development expenses that obscures economics

---

# 21. New Launch & Product-Cycle Analysis

For OEMs track:

- New launches
- Facelifts
- Model age
- New platforms
- Product refreshes
- Waiting periods
- Bookings
- Market share following launches

Analyze:

**Launch → Bookings → Deliveries → Volume → Market Share → ASP / Mix → Margin**

The source framework specifically lists product launches, model age, brand strength, dealer network and waiting periods as competitive metrics. fileciteturn22file3

---

# 22. Brand & Competitive Position

Assess:

- Brand recognition
- Pricing power
- Customer loyalty
- Distribution
- Product differentiation
- Product innovation
- Manufacturing efficiency
- Procurement advantage
- Dealer network
- Service network
- Content / technology advantage

For OEMs also assess:

- Product breadth
- Segment leadership
- Premium positioning
- EV competitiveness
- Export presence

For components assess:

- Engineering capability
- Customer qualification
- Switching costs
- Technology
- Program stickiness
- Scale
- Cost advantage

The source framework requires evidence such as stable/improving market share, sustained premium pricing, superior margins, high ROIC and distribution strength rather than labeling a moat merely because a company is large. fileciteturn22file3

---

# 23. Distribution & Dealer Network

Track:

- Dealer count
- Service centers
- Geographic reach
- Rural penetration
- Urban penetration
- Dealer productivity
- Dealer inventory
- Distribution expansion
- Export distribution

Assess:

- Market access
- Customer service
- Brand reach
- Distribution advantage
- Dealer economics

Flag:

- Weak dealer network
- Excess inventory
- Dealer financial stress
- Expansion without adequate productivity

---

# 24. Aftermarket & Replacement Economics

For applicable component and tyre businesses track:

- Aftermarket revenue
- OEM revenue
- Replacement volume
- Replacement realization
- Dealer/distributor network
- Product life
- Brand strength
- Gross margin
- Working capital

Analyze:

**Installed Base → Replacement Cycle → Aftermarket Demand → Realization → Margin → Cash**

Aftermarket exposure can be analyzed separately from OEM production cycles.

---

# 25. Export Analysis

Track:

- Export revenue
- Export volume
- Export share
- Geography
- Customer mix
- Currency exposure
- Export realization
- Export growth
- Local manufacturing footprint

Analyze:

**Export Volume + Realization + Currency → Export Revenue → Margin → CFO**

Flag:

- Excessive country concentration
- Currency-driven earnings
- Geopolitical / regulatory exposure
- Weak export demand masked by domestic performance

---

# 26. Working Capital

Track:

- Receivable days
- Inventory days
- Payable days
- Cash conversion cycle
- Dealer receivables
- Channel inventory
- Raw-material inventory
- Finished goods inventory

Analyze:

**Revenue Growth → Receivables Growth → Inventory Growth → CFO**

The source framework specifically highlights receivables, inventory, payables, dealer receivables, channel inventory and inventory ageing. fileciteturn22file3

Flag:

- Receivables growing faster than sales
- Inventory growing faster than sales
- Dealer receivable stress
- Persistent negative CFO
- Channel stuffing
- Inventory ageing

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
- EV capex
- Tooling / model-development investment

Evaluate:

**Capex → Capacity → Utilization → Revenue → EBIT → CFO → FCF → ROIC**

Flag:

- Large capex without demand visibility
- Low utilization after expansion
- Persistent negative FCF
- Repeated project delays
- Capitalized expenses

These are directly aligned with the source framework's capital-expenditure logic. fileciteturn22file3

---

# 28. Cash Flow Quality

Track:

- CFO
- Capex
- CFI
- CFF
- FCF
- CFO / PAT
- FCF / PAT
- FCF margin
- Cash conversion
- Dividend
- Buybacks
- Debt repayment
- Debt raised

Core chain:

**EBITDA → EBIT → PAT → CFO → Capex → FCF**

Analyze:

**Accounting Profit vs Cash Generation**

Flag:

- PAT rising while CFO falls
- Weak CFO/PAT
- Persistent negative FCF
- Heavy capex with poor utilization
- Working-capital absorption

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
- EV-transition funding
- Acquisition debt
- Lease obligations
- Refinancing risk

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

Investigate whether ROIC is driven by:

- Pricing
- Product mix
- Utilization
- Manufacturing efficiency
- Asset-light growth
- Market share
- High content / vehicle

Or weakened by:

- Excess capacity
- Large new plants
- EV-transition capex
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
- Debt reduction

Assess:

- Capacity allocation
- EV investment
- Acquisitions
- R&D
- Buybacks
- Dividends
- Debt reduction

Flag:

- Repeated acquisitions with weak returns
- Large capex before demand visibility
- Persistent dilution
- Weak disclosure
- Related-party concerns

---

# 32. Concall Intelligence

Extract management commentary on:

## Demand

- Industry demand
- Rural / urban demand
- Consumer financing
- Replacement cycle
- Commercial vehicle cycle
- Tractor demand
- Export demand

## Pricing

- ASP
- Discounts
- Incentives
- Price increases
- Commodity pass-through

## Product

- New launches
- Model refreshes
- EV launches
- Premiumization
- Product pipeline

## Capacity

- Capacity additions
- Utilization
- New plants
- Expansion timing

## Components

- New programs
- Order wins
- Customer additions
- Content / vehicle
- EV exposure

## Costs

- Steel
- Aluminium
- Rubber
- Precious metals
- Battery materials
- Energy
- Freight

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

Optimistic management commentary must not be treated as evidence by itself.

---

# 33. Industry Cycle Analysis

Automobiles and components are cyclical.

Analyze:

- Credit cycle
- Interest rates
- Consumer income
- Rural cycle
- Replacement cycle
- Commercial vehicle cycle
- Tractor cycle
- Export cycle
- Commodity cycle
- Inventory cycle
- Capacity cycle
- EV transition

Core cycle:

**Demand → Volume → Utilization → Margin → Cash Flow**

For commodity-sensitive suppliers:

**Commodity Price → Realization → Spread → Utilization → Margin → Cash Flow**

Distinguish:

**Structural growth**

from:

**Cyclical recovery**

from:

**Temporary commodity benefit**

---

# 34. Competitive Metrics

For Automobiles track:

- Market share
- Product launches
- Model age
- Brand strength
- Dealer network
- Waiting periods
- Export markets
- EV competitiveness

These metrics are explicitly identified in the source framework. fileciteturn22file3

For components additionally track:

- Customer concentration
- Content / vehicle
- New programs
- Order book
- EV share
- Engineering capability
- OEM / aftermarket mix

---

# 35. Peer Comparison

Compare companies by actual business model.

## OEM peers

Compare:

- Volume growth
- Market share
- ASP
- Product mix
- Premium mix
- EV mix
- Capacity utilization
- EBITDA margin
- EBIT margin
- CFO/PAT
- FCF margin
- ROIC
- Net debt
- Valuation

## Auto Component peers

Compare:

- Revenue growth
- Vehicle-volume exposure
- Content / vehicle
- Customer concentration
- OEM / aftermarket mix
- EV exposure
- Capacity utilization
- Order book
- EBITDA margin
- CFO/PAT
- FCF
- ROIC
- Net debt
- Valuation

## Tyre peers

Additionally compare:

- Replacement vs OEM
- Volume
- Realization
- Rubber cost sensitivity
- Brand
- Distribution
- Market share
- EBITDA / tonne where meaningful
- Cash generation

Do not compare an OEM's valuation or economics directly with a Tier-2 supplier merely because both belong to the same Sector Value.

---

# 36. Valuation Framework

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

For automobile companies valuation should be considered alongside:

- Volume growth
- Market share
- Product cycle
- EV transition
- Margins
- ROIC
- FCF
- Net cash / debt

For components:

- Customer concentration
- Growth visibility
- Order book
- EV exposure
- Content / vehicle
- ROIC
- FCF
- Valuation

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

# 37. Historical Valuation

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
- EBITDA margin
- ROIC
- FCF
- Net debt
- Product cycle
- EV exposure
- Industry cycle

A low historical multiple is not automatically cheap; valuation must be interpreted alongside business quality and cycle position.

---

# 38. Causal Analysis Engine

The system must explain **WHY** financial metrics changed.

## OEM Chain

**Industry Demand → Company Volume → Market Share → ASP / Mix → Revenue → Utilization → Margin → EBIT → PAT → CFO → FCF → ROIC**

## Pricing / Mix Chain

**Price Increase / Premiumization → ASP → Revenue → Gross Margin → EBITDA → CFO**

## Commodity Chain

**Steel / Aluminium / Rubber / Battery Materials → Input Cost → Gross Margin → EBITDA → CFO**

## Capacity Chain

**Capex → Capacity → Utilization → Fixed-Cost Absorption → EBITDA → CFO → FCF → ROIC**

## Auto Component Chain

**Vehicle Production → Content / Vehicle → Supplier Revenue → Utilization → Margin → CFO**

## EV Transition Chain

**EV Adoption → EV Volume → EV Mix → Content / Vehicle → Revenue → R&D / Capex → Margin → FCF → ROIC**

## Market Share Chain

**New Launch → Customer Acceptance → Volume → Market Share → Utilization → Margin → Cash**

The engine should identify where the chain breaks.

Example:

**Industry volume ↑ → Company volume ↓ → Market share ↓**

The system should investigate product competitiveness, model cycle, capacity, supply constraints, distribution or other disclosed factors before assigning a cause.

---

# 39. Red Flags

## Demand

- Company volume materially below industry growth
- Market-share decline
- Rising dealer inventory
- Weak retail demand hidden by dispatch growth
- High dependence on financing

## Pricing

- Revenue growth without volume growth
- Heavy discounting
- Incentive escalation
- ASP growth entirely due to mix
- Price increases without demand support

## Product

- Aging product portfolio
- Weak launch pipeline
- Model concentration
- EV transition risk
- Technology obsolescence

## Capacity

- Large capex without demand visibility
- Low utilization
- Capacity additions before order visibility
- Persistent CWIP
- Delayed projects

## Components

- Excessive customer concentration
- Weak order-book conversion
- Receivable build-up
- Commodity pass-through mismatch
- High capex before program visibility

These component-specific flags are directly identified in the source framework. fileciteturn22file3

## Margins

- EBITDA growth without CFO growth
- Margin expansion from temporary commodity deflation
- Weak gross margin
- Rising warranty / launch costs
- Capitalized expenses

## Cash Flow

- PAT rising while CFO falls
- Persistent negative FCF
- Inventory build
- Receivable build
- Capex exceeding sustainable cash generation

## Governance

- Promoter pledge
- Auditor qualification
- Auditor resignation
- Related-party concerns
- Repeated dilution
- Aggressive acquisitions

---

# 40. Positive Signals

Look for combinations such as:

- Company volume growth > industry growth
- Sustained market-share gains
- Strong new-product cycle
- Premiumization
- Higher ASP with healthy volume
- Improving utilization
- Operating leverage
- Stable / improving gross margin
- Strong EV transition
- Rising content / vehicle
- New customer additions
- Diversified customer base
- Strong order-book conversion
- Higher aftermarket share where economically attractive
- Strong CFO/PAT
- Rising FCF
- Improving ROIC
- Low leverage
- Strong brand / technology / distribution

A positive signal should be supported by multiple data points rather than a single quarter.

---

# 41. Scenario Analysis

Build Bull / Base / Bear scenarios.

## Bull

Potential assumptions:

- Industry volume growth
- Market-share gains
- ASP growth
- Premiumization
- Higher utilization
- Better product mix
- Lower commodity costs
- Strong EV growth
- Strong export growth
- New program ramp-up

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

- Normal industry volume
- Stable market share
- Normal ASP
- Normal utilization
- Stable commodity environment
- Planned capacity additions
- Expected product launches

## Bear

Potential assumptions:

- Demand slowdown
- Market-share loss
- Dealer inventory build
- Discounting
- Commodity inflation
- Lower utilization
- EV-transition pressure
- Export slowdown
- Higher interest costs
- Working-capital stress

Calculate the same financial outputs.

---

# 42. Scoring Architecture

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

Activate industry-specific metrics inside these categories.

### Business Quality

- Business model
- Product breadth
- Revenue diversification
- Customer diversification
- OEM / aftermarket mix

### Demand & Growth

- Volume
- Market share
- ASP
- Product mix
- EV growth
- Export growth
- Order-book growth

### Competitive Position

- Brand
- Distribution
- Technology
- Product pipeline
- Customer relationships
- Market share

### Operating Quality

- Utilization
- Gross margin
- EBITDA margin
- Incremental margins
- Commodity pass-through

### Cash Flow Quality

- CFO/PAT
- FCF
- Working-capital quality
- Capex discipline

### Balance Sheet

- Net debt
- Interest coverage
- Lease liabilities
- Funding needs

### Capital Efficiency

- ROCE
- ROIC
- Asset turnover

### Management & Governance

- Guidance quality
- Capital allocation
- EV-transition execution
- Disclosure quality

### Valuation

- P/E
- EV/EBITDA
- EV/Sales
- FCF yield
- Historical valuation
- Peer valuation

### Important

Do not produce a misleading final score when critical industry data is missing.

Show:

**Data Coverage + Confidence + Critical Missing Metrics**

---

# 43. Metric Classification

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
| Volume growth | SECTOR_SPECIFIC |
| Market share | SECTOR_SPECIFIC |
| ASP | SECTOR_SPECIFIC |
| Capacity utilization | SECTOR_SPECIFIC |
| EV mix | SECTOR_SPECIFIC |
| Content / vehicle | SECTOR_SPECIFIC |
| Dealer inventory | DIAGNOSTIC |
| Commodity sensitivity | DIAGNOSTIC |
| Order book | SECTOR_SPECIFIC |
| P/E | VALUATION |
| EV/EBITDA | VALUATION |
| Net debt / EBITDA | CORE |

---

# 44. Data Quality Framework

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
= Revenue attributable to vehicle sales / Vehicle units
```

or:

```text
Incremental EBITDA Margin
= Change in EBITDA / Change in Revenue
```

Store the inputs used in each calculation.

---

# 45. Source Hierarchy

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

For operating metrics such as:

- Volume
- Market share
- Capacity
- Utilization
- Order book
- EV mix
- Customer concentration

prefer primary company disclosures where available.

Third-party data must not silently override company-reported data.

---

# 46. Missing Data Logic

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

If dealer inventory is not disclosed:

```text
dealer_inventory = MISSING_INPUT
```

not:

```text
dealer_inventory = 0
```

---

# 47. Agent Architecture

Recommended pipeline:

```text
Company Identification
        ↓
Business Classification
        ↓
OEM / Component Classification
        ↓
Product / Customer / Geography Classification
        ↓
Financial Data
        ↓
Industry Volume
        ↓
Company Volume
        ↓
Market Share
        ↓
ASP / Price / Mix
        ↓
EV / ICE Exposure
        ↓
Capacity / Utilization
        ↓
Commodity Cost
        ↓
Customer / Order Book
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

# 48. Database Structure

Recommended metric table:

```text
company_id
sector
sector_value
industry
business_model
product_type
customer_type
tier
geography
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

Recommended industry operating-metric categories:

```text
VOLUME
MARKET_SHARE
ASP
PRODUCT_MIX
EV
CAPACITY
UTILIZATION
DEALER_INVENTORY
LAUNCHES
COMMODITIES
CUSTOMER
ORDER_BOOK
CONTENT_PER_VEHICLE
OEM
AFTERMARKET
EXPORT
MARGINS
WORKING_CAPITAL
CAPEX
CASH_FLOW
BALANCE_SHEET
ROIC
GOVERNANCE
VALUATION
```

---

# 49. Data Coverage Dashboard

The application should show:

**DATA COVERAGE**

Example:

```text
82% of tracked metrics available
```

Then:

```text
Critical data gaps:
- Dealer inventory
- Customer concentration
- Content / vehicle
- Capacity utilization
- EV-specific revenue
```

The dashboard must identify which missing metrics affect the analysis most.

---

# 50. Quarterly Monitoring System

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
- EV mix
- Capacity utilization
- Dealer inventory
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

# 51. Guidance Tracking

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
- EV launches
- New programs
- Order book
- Exports

---

# 52. Fundamental Thesis Generator

Generate the thesis from evidence:

```text
Business Model
+
Industry Demand
+
Company Volume
+
Market Share
+
ASP / Mix
+
EV Transition
+
Capacity / Utilization
+
Commodity Economics
+
Competitive Position
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

What reported/calculated data shows.

### Interpretation

What the evidence may imply.

### Uncertainty

What cannot yet be established.

### Monitoring triggers

What future data could confirm or invalidate the interpretation.

---

# 53. Final Screener Output

The report should answer:

## Business

- What does the company manufacture or supply?
- Is it an OEM or component company?
- Which product categories matter?
- Who are its customers?

## Demand

- Is industry demand growing?
- Is company volume growing?
- Is market share improving?
- Is demand structural or cyclical?

## Pricing & Mix

- Is ASP increasing?
- Is premiumization occurring?
- Is mix improving?
- Are discounts increasing?

## EV Transition

- What is the ICE / EV exposure?
- Is EV mix increasing?
- Is the company gaining EV programs?
- What investment is required?

## Capacity

- Is utilization improving?
- Is new capacity justified?
- Is operating leverage emerging?

## Components

- Is content / vehicle increasing?
- Is customer concentration manageable?
- Is the order book converting into revenue?
- Is aftermarket exposure improving?

## Costs

- How sensitive are margins to steel, aluminium, rubber, precious metals or battery materials?
- Is price pass-through adequate?

## Financials

- Is revenue growing?
- What is driving growth?
- Are margins improving?
- Is cash conversion strong?

## Capital Efficiency

- Is ROCE / ROIC improving?
- Is growth consuming excessive capital?

## Balance Sheet

- Is leverage manageable?
- Are capex commitments sustainable?

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

# 54. Implementation Principles

1. **Classify first, calculate second.**
2. **Separate OEM economics from component economics.**
3. **Separate industry volume from company volume.**
4. **Separate wholesale/dispatch data from end-consumer demand where possible.**
5. **Track market share, not just revenue growth.**
6. **Decompose growth into volume, price, mix, currency and acquisitions.**
7. **Track ASP together with volume.**
8. **Track premiumization and product mix.**
9. **Treat EV transition as a business-model and capital-allocation question, not only a volume metric.**
10. **Track capacity utilization and operating leverage.**
11. **For components, track content / vehicle and customer concentration.**
12. **Track commodity sensitivity and pass-through.**
13. **Separate structural margin improvement from temporary commodity benefits.**
14. **Separate accounting profit from cash generation.**
15. **Track capex → utilization → FCF → ROIC.**
16. **Track management guidance against subsequent results.**
17. **Compare companies by actual business model.**
18. **Never treat missing data as zero.**
19. **Retain metric lineage for every calculated value.**
20. **Explain WHY metrics changed, not merely whether they passed a threshold.**

---

# 55. Central Fundamental Question

The entire Automobile and Auto Components analysis should ultimately answer:

> **Can this company sustainably grow volume, market share and/or content per vehicle while maintaining pricing, competitive positioning and healthy utilization, converting operating growth into strong free cash flow and ROIC without requiring disproportionate capital investment or taking excessive technology, customer or cycle risk?**
