# Consumer Discretionary — Consumer Services — Fundamental Analysis Framework

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
**Sector Value:** Consumer Services  
**Industries:** Other Consumer Services; Leisure Services; Retailing

```text
Consumer Discretionary
└── Consumer Services
    ├── Other Consumer Services
    ├── Leisure Services
    └── Retailing
```

The source classification explicitly places Education, Beauty/Wellness, Food Services, Consumer-facing Platforms and Repair/Service Networks under Other Consumer Services; Hotels, Travel, Tourism, Restaurants, Leisure/Recreation and Hospitality Platforms under Leisure Services; and Offline Retail, Online/E-commerce, Omnichannel, Specialty Retail, Department Stores, Grocery, Fashion/Lifestyle and Jewellery Retailing under Retailing. fileciteturn19file0L123-L165

---

# 2. Purpose

This framework is designed for a sector-specific fundamental-analysis engine covering all three industries.

Core flow:

```text
BUSINESS MODEL
      ↓
CUSTOMER DEMAND
      ↓
CUSTOMERS / FOOTFALL / TRANSACTIONS
      ↓
UTILIZATION / PRODUCTIVITY
      ↓
REVENUE PER CUSTOMER / TICKET / SQ FT / ROOM
      ↓
REVENUE
      ↓
UNIT ECONOMICS
      ↓
MARGIN
      ↓
WORKING CAPITAL / CAPEX
      ↓
CASH FLOW
      ↓
ROCE / ROIC
      ↓
COMPETITIVE ADVANTAGE
      ↓
MANAGEMENT / GUIDANCE
      ↓
PEER COMPARISON
      ↓
VALUATION
      ↓
CAUSAL ANALYSIS
```

The analysis must distinguish fundamentally different service economics. A retailer, hotel, education company and platform business should not receive the same KPI set merely because all are classified as Consumer Services.

---

# 3. Industry Coverage

## 3.1 Other Consumer Services

Cover:

- Education
- Beauty/wellness
- Food services
- Consumer-facing platforms
- Repair/service networks
- Healthcare-adjacent consumer services where classified here

Core metrics:

- Customers
- Transactions
- Active users
- ARPU
- Take rate
- Locations
- Utilization
- Retention
- Repeat purchase
- Customer acquisition cost
- Lifetime value
- Revenue/customer

The source framework defines the platform model as:

```text
GMV → Take Rate → Revenue → Contribution Margin → Cash Burn/Generation
```

and service businesses as:

```text
Customers → Utilization → Revenue/customer → Employee productivity → Margin → Cash
```

fileciteturn19file3L709-L732

---

## 3.2 Leisure Services

Cover:

- Hotels
- Travel
- Tourism
- Restaurants
- Leisure/recreation
- Hospitality platforms

Core metrics:

- Customers
- Bookings
- Occupancy
- ADR
- RevPAR
- Transactions
- Average ticket
- Room inventory
- Same-property growth
- Revenue/property
- F&B revenue
- Ancillary revenue
- Domestic/international mix

For hotels:

```text
Demand → Occupancy → ADR → RevPAR → Revenue → EBITDA → CFO
```

The source framework defines:

```text
RevPAR = Occupancy × ADR
```

and also requires evaluation of owned vs leased properties, asset-light vs asset-heavy models, renovation capex, seasonality and destination concentration. fileciteturn19file2L567-L597

---

## 3.3 Retailing

Cover:

- Offline retail
- Online/e-commerce
- Omnichannel
- Specialty retail
- Department stores
- Grocery
- Fashion/lifestyle
- Jewellery retail

Core metrics:

- Store count
- New stores
- Closures
- Store area
- Sales/sq ft
- Same-store sales growth
- Footfall
- Conversion rate
- Transactions
- Average transaction value
- Online sales
- Digital penetration

The source framework also requires inventory days, inventory turns, stock ageing, markdown percentage, shrinkage and working capital/store. fileciteturn19file2L523-L563

---

# 4. Business-Model Classification

Before analysis, classify the company.

## 4.1 Other Consumer Services

```text
EDUCATION
BEAUTY_WELLNESS
FOOD_SERVICE
CONSUMER_PLATFORM
REPAIR_SERVICE
OTHER_SERVICE
```

Additional classification:

```text
B2C
B2B2C
PLATFORM
ASSET_LIGHT
ASSET_HEAVY
SUBSCRIPTION
TRANSACTIONAL
FRANCHISE
OWNED_LOCATIONS
MARKETPLACE
```

## 4.2 Leisure Services

```text
HOTEL
TRAVEL
TOURISM
RESTAURANT
LEISURE_RECREATION
HOSPITALITY_PLATFORM
```

Additional:

```text
OWNED
LEASED
MANAGED
FRANCHISED
ASSET_LIGHT
ASSET_HEAVY
PREMIUM
MASS_MARKET
DOMESTIC
INTERNATIONAL
```

## 4.3 Retailing

```text
OFFLINE
ONLINE
OMNICHANNEL
SPECIALTY
DEPARTMENT_STORE
GROCERY
FASHION_LIFESTYLE
JEWELLERY
```

Additional:

```text
OWNED_STORE
FRANCHISE
MARKETPLACE
INVENTORY_LED
ASSET_LIGHT
ASSET_HEAVY
PREMIUM
VALUE
```

---

# 5. Common Financial Dataset

Collect annual, quarterly and TTM data wherever available.

## 5.1 P&L

Capture:

- Revenue
- Revenue growth
- Cost of goods/services
- Employee cost
- Rent/lease cost
- Advertising/marketing
- Distribution cost
- Other operating expenses
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
- Receivables
- Payables
- Other current assets
- Fixed assets
- Right-of-use assets
- CWIP
- Investments
- Debt
- Lease liabilities
- Net debt
- Equity
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
- Lease payments where material
- Debt raised
- Debt repayment
- Dividend

---

# 6. Customer-Demand Engine

Demand is the starting point for Consumer Services.

Track:

- Customer count
- New customers
- Active customers
- Repeat customers
- Transactions
- Bookings
- Footfall
- Conversion
- Average ticket
- ARPU
- Customer retention
- Churn

Analyze:

```text
Market Demand
     ↓
Customer Acquisition
     ↓
Active Customers
     ↓
Transactions
     ↓
Average Ticket / ARPU
     ↓
Revenue
```

Separate:

```text
New Customer Growth
vs
Existing Customer Growth
```

and:

```text
Customer Growth
vs
Revenue Growth
```

Flag revenue growth driven primarily by price increases when customer activity is weakening.

---

# 7. Volume–Price–Mix Analysis

For service businesses:

```text
Revenue Growth
=
Customer Growth
+
Transaction Growth
+
Price / ARPU Growth
+
Mix
```

For retail:

```text
Revenue
=
Footfall
×
Conversion
×
Average Transaction Value
```

For hotels:

```text
Room Revenue
=
Available Rooms
×
Occupancy
×
ADR
```

For platforms:

```text
Revenue
=
GMV
×
Take Rate
```

Use company-disclosed definitions where available.

---

# 8. Unit Economics

Unit economics must be selected according to the business model.

## 8.1 Other Consumer Services

Calculate where data permits:

- Revenue/customer
- Revenue/location
- Revenue/employee
- EBITDA/customer
- EBITDA/location
- CAC
- LTV
- LTV/CAC
- Retention
- Repeat purchase rate

For platforms:

- GMV/user
- Revenue/user
- Take rate
- Contribution margin/user
- CAC
- LTV
- Cash burn/user

## 8.2 Hotels

Calculate:

- Revenue/room
- EBITDA/room
- Revenue/property
- EBITDA/property
- RevPAR
- ADR
- Occupancy

## 8.3 Restaurants

Calculate:

- Revenue/store
- Revenue/seat
- Revenue/sq ft
- Transactions/store
- Average ticket
- EBITDA/store
- Store-level EBITDA margin
- New-store payback where disclosed

## 8.4 Retail

Calculate:

- Revenue/store
- EBITDA/store
- Revenue/sq ft
- EBITDA/sq ft
- Sales/store
- Sales/mature store
- New-store productivity
- Store payback where disclosed

The source framework specifically identifies revenue/store, EBITDA/store, revenue/sq ft, EBITDA/sq ft, store payback, new-store productivity and mature-store productivity for retailing. fileciteturn19file2L540-L550

---

# 9. Location and Capacity Analysis

For location-driven businesses track:

- Number of locations
- New locations
- Closures
- Location age
- Location size
- Utilization
- Revenue/location
- EBITDA/location
- Mature-location productivity

Analyze:

```text
Location Additions
      ↓
New Capacity
      ↓
Ramp-up
      ↓
Mature Productivity
      ↓
Revenue
      ↓
EBITDA
      ↓
Cash Payback
```

Flag:

- Rapid expansion
- Falling mature-store productivity
- Low utilization
- Poor new-unit economics
- Expansion funded by excessive debt

---

# 10. Retail Inventory Intelligence

For retail businesses track:

- Inventory
- Inventory days
- Inventory turns
- Stock ageing
- Slow-moving inventory
- Markdown %
- Shrinkage
- Working capital/store
- Inventory/store
- Inventory growth vs sales growth

Separate:

```text
Inventory Build
vs
Underlying Consumer Demand
```

Flag:

```text
Inventory Growth > Revenue Growth
```

particularly when combined with:

- Falling footfall
- Falling same-store growth
- Rising markdowns
- Margin compression
- Weak CFO

The source framework specifically flags aggressive store expansion without sufficient mature-store productivity. fileciteturn19file2L552-L563

---

# 11. Hotel / Leisure Intelligence

For hotels track:

- Occupancy
- ADR
- RevPAR
- Room count
- Room additions
- Same-property growth
- New-property contribution
- F&B revenue
- Ancillary revenue
- Domestic/international mix

Analyze:

```text
Demand
 ↓
Occupancy
 ↓
ADR
 ↓
RevPAR
 ↓
Revenue
 ↓
EBITDA
 ↓
CFO
 ↓
ROIC
```

Also evaluate:

- Owned vs leased
- Managed vs owned
- Asset-light vs asset-heavy
- Lease obligations
- Renovation capex
- Seasonality
- Destination concentration

---

# 12. Platform Economics

For platform businesses track:

- GMV
- Active users
- Transactions
- Take rate
- Revenue
- Contribution margin
- CAC
- LTV
- Retention
- Churn
- Burn
- Cash generation

Core chain:

```text
Users
 ↓
Transactions
 ↓
GMV
 ↓
Take Rate
 ↓
Revenue
 ↓
Contribution Margin
 ↓
EBITDA
 ↓
CFO
 ↓
FCF
```

Separate:

```text
GMV Growth
vs
Revenue Growth
vs
Profit Growth
```

Flag:

- GMV growth without monetization improvement
- Falling take rate
- Rising CAC
- Falling retention
- Increasing cash burn
- Growth requiring disproportionate incentives

---

# 13. Service Productivity

Track:

- Revenue/employee
- EBITDA/employee
- Customers/employee
- Employees/location
- Utilization
- Employee cost/revenue

Analyze:

```text
Customers
 ↓
Utilization
 ↓
Employee Productivity
 ↓
Revenue
 ↓
Margin
```

Flag:

- Employee costs rising faster than revenue
- Falling revenue/employee
- Low utilization
- Excess capacity
- Productivity deterioration

---

# 14. Pricing and Monetization

Track:

- ASP
- ARPU
- Average ticket
- Take rate
- Subscription price
- Revenue/customer
- Revenue/room
- Revenue/sq ft
- Revenue/location

Separate:

```text
Price Increase
vs
Volume / Customer Growth
```

Evaluate pricing power through:

- Retention after price increases
- Volume response
- Competitor pricing
- Customer mix
- Premiumization
- Revenue/customer trend

---

# 15. Margin Analysis

Track:

- Gross margin
- EBITDA margin
- EBIT margin
- PAT margin
- Employee cost %
- Rent %
- Marketing %
- Distribution %
- COGS %
- Other operating costs %

Analyze:

```text
Revenue Growth
 ↓
Operating Leverage
 ↓
EBITDA Margin
 ↓
EBIT
 ↓
PAT
```

Identify whether margin expansion comes from:

- Pricing
- Volume
- Mix
- Utilization
- Operating leverage
- Cost control
- Lower input costs
- Temporary factors

---

# 16. Working Capital

Track:

- Inventory days
- Receivable days
- Payable days
- Cash conversion cycle
- Working capital/revenue
- Working capital/location

For platform/service businesses also track:

- Customer advances
- Merchant payables
- Deferred revenue
- Contract liabilities

Calculate:

```text
CCC = Inventory Days + Receivable Days - Payable Days
```

Flag:

- Inventory build
- Receivables growing faster than revenue
- Payable stretching
- Deteriorating CCC
- Customer advances masking weak underlying cash conversion

---

# 17. Capex and Expansion

Track:

- New stores
- New hotels
- New locations
- New facilities
- Renovation capex
- Technology capex
- Maintenance capex
- Growth capex
- Capex/store
- Capex/room
- Capex/location
- Capital employed/location

Analyze:

```text
Capital Invested
 ↓
New Capacity
 ↓
Ramp-up
 ↓
Revenue
 ↓
EBITDA
 ↓
CFO
 ↓
Payback
 ↓
ROCE / ROIC
```

Flag expansion where:

- Unit economics deteriorate
- Mature units are slowing
- Cash generation cannot fund expansion
- Debt rises materially
- New capacity is added ahead of demand

---

# 18. Cash Flow Quality

Track:

- CFO
- FCF
- CFO/PAT
- FCF/PAT
- Capex/CFO
- FCF margin
- Lease-adjusted cash flow where material

Analyze:

```text
PAT
 ↓
CFO
 ↓
Capex
 ↓
FCF
```

Flag:

- PAT growth without CFO growth
- Persistent negative FCF
- Heavy growth capex
- Working-capital-driven cash deterioration
- Debt-funded expansion
- Capitalized expenses distorting operating economics

---

# 19. Balance Sheet and Funding

Track:

- Debt
- Net debt
- Debt/equity
- Net debt/EBITDA
- Interest coverage
- Current ratio
- Lease liabilities
- Fixed assets
- ROCE
- ROIC

For asset-light businesses separately assess:

- Lease liabilities
- Deferred revenue
- Merchant/customer funds
- Contract liabilities
- Restricted cash where material

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

For location-led businesses:

```text
Unit Economics
+
Capital per Unit
+
Unit Productivity
=
Incremental Return
```

Determine whether returns improve through:

- Higher utilization
- Higher pricing
- Better mix
- Higher productivity
- Lower capital intensity
- Operating leverage

---

# 21. Competitive Advantage

Assess:

- Brand
- Customer loyalty
- Distribution
- Location network
- Network effects
- Technology
- Data
- Customer acquisition efficiency
- Switching costs
- Scale
- Supplier relationships
- Procurement advantage
- Content/service quality
- Market share
- Customer retention

For platforms:

```text
Users
→ Engagement
→ Network Effects
→ More Supply/Demand
→ Better Unit Economics
```

For retail:

```text
Brand
→ Footfall
→ Conversion
→ Scale
→ Procurement
→ Better Economics
```

For hotels:

```text
Brand
→ Occupancy
→ Pricing
→ RevPAR
→ Cash Generation
```

---

# 22. Management and Capital Allocation

Track:

- Store/location expansion
- Hotel expansion
- Acquisitions
- Franchise strategy
- Capex
- Technology investment
- Debt
- Dividends
- Buybacks
- Equity issuance
- Related-party transactions
- Promoter transactions
- Executive remuneration
- Auditor changes
- Regulatory actions
- Contingent liabilities

The source framework requires tracking promoter holding/pledge, promoter transactions, dilution, related-party transactions, auditor changes, regulatory actions, remuneration, capital allocation, acquisitions, buybacks and dividends. fileciteturn20file0L15-L35

---

# 23. Concall Intelligence

Extract:

- Demand commentary
- Pricing
- Volume outlook
- Margin guidance
- Capex
- Expansion
- New locations
- New products
- Market share
- Competition
- Consumer behavior
- Commodity/input outlook
- Customer acquisition
- Retention
- Management risks

Track:

```text
GUIDANCE
   ↓
SUBSEQUENT RESULT
   ↓
VARIANCE
   ↓
EXPLANATION
```

Do not treat optimistic commentary as evidence without subsequent operating confirmation. fileciteturn20file0L36-L59

---

# 24. Demand and Cycle Analysis

Consumer Services are sensitive to:

- Consumer income
- Affordability
- Interest rates
- Employment
- Tourism
- Seasonality
- Consumer confidence
- Urban/rural demand
- Festival periods
- Weather
- Travel cycles
- Discretionary spending

Analyze:

```text
Macro Conditions
      ↓
Consumer Demand
      ↓
Footfall / Customers
      ↓
Transactions
      ↓
ASP / ARPU
      ↓
Revenue
      ↓
Utilization
      ↓
Margin
      ↓
Cash Flow
```

Identify whether growth is:

- Structural
- Cyclical
- New-capacity-led
- Price-led
- Market-share-led
- Acquisition-led

---

# 25. Peer Comparison

Select peers based on:

1. Same industry
2. Similar business model
3. Similar customer segment
4. Similar geography
5. Similar capital intensity
6. Similar scale

## Other Consumer Services

Compare:

- Customer growth
- Active users
- Transactions
- ARPU
- Take rate
- Retention
- CAC
- LTV
- Revenue/customer
- Revenue/employee
- EBITDA margin
- CFO/PAT
- FCF

## Leisure

Compare:

- Occupancy
- ADR
- RevPAR
- Revenue/room
- EBITDA/room
- Room additions
- Same-property growth
- Asset intensity
- ROCE
- ROIC

## Retail

Compare:

- Store count
- Store growth
- Sales/sq ft
- Same-store sales growth
- Footfall
- Conversion
- Average ticket
- Inventory turns
- Markdown
- EBITDA/store
- EBITDA margin
- ROCE
- ROIC

The source framework explicitly says peer selection must be based on business model rather than broad sector classification alone. fileciteturn20file0L63-L82

---

# 26. Valuation

Keep valuation separate from business-quality analysis.

Potential methods:

- P/E
- EV/EBITDA
- EV/Sales
- P/B where relevant
- FCF Yield
- DCF
- Asset-based valuation where appropriate

Use the valuation method appropriate to the economics.

### Other Consumer Services

Potentially:

- P/E
- EV/EBITDA
- EV/Sales
- DCF
- FCF yield

### Hotels / Leisure

Potentially:

- EV/EBITDA
- P/E
- EV/room
- EV/property
- NAV/asset-based methods where appropriate

### Retail

Potentially:

- P/E
- EV/EBITDA
- EV/Sales
- FCF yield

### Platforms

Potentially:

- EV/Sales
- EV/GMV
- P/E once profitable
- FCF yield
- DCF

Never apply one universal multiple across all Consumer Services.

---

# 27. Historical Valuation

Track:

- Current P/E
- 3Y/5Y/10Y P/E
- Current EV/EBITDA
- Historical EV/EBITDA
- EV/Sales
- FCF yield
- P/B where relevant

Compare valuation against:

- Historical growth
- Current growth
- Margin
- ROIC
- Cash generation
- Balance-sheet quality
- Unit economics

The source framework recommends comparing current valuation with company history, comparable peers, current growth, profitability, ROIC and balance-sheet quality. fileciteturn20file0L184-L201

---

# 28. Causal Analysis Engine

The final output must explain **WHY** financial performance changed.

## General Consumer Services

```text
Consumer Demand
→ Customers / Footfall
→ Transactions
→ ASP / ARPU
→ Revenue
→ Utilization
→ Margin
→ EBIT
→ PAT
→ CFO
→ FCF
→ ROIC
```

## Retail

```text
Footfall
→ Conversion
→ Transactions
→ Average Ticket
→ Revenue/store
→ Same-store Growth
→ Store EBITDA
→ CFO
```

## Hotels

```text
Demand
→ Occupancy
→ ADR
→ RevPAR
→ Revenue
→ EBITDA
→ CFO
→ ROIC
```

## Platforms

```text
Users
→ Transactions
→ GMV
→ Take Rate
→ Revenue
→ Contribution Margin
→ EBITDA
→ CFO
→ FCF
```

The source framework explicitly defines these causal chains and requires the system to identify where the chain is breaking. fileciteturn20file0L205-L239

---

# 29. Red-Flag Engine

## Growth

Flag:

- Revenue growth without customer/volume growth
- Price-led growth with weak demand
- Acquisition-led growth
- Channel loading
- Declining market share
- Growth concentrated in one product/location

## Unit Economics

Flag:

- Falling revenue/customer
- Falling revenue/store
- Falling revenue/room
- Falling revenue/employee
- Rising CAC
- Falling LTV
- Falling take rate

## Retail

Flag:

- Inventory build-up
- Rising markdown
- Falling same-store growth
- Falling mature-store productivity
- Aggressive store additions
- Shrinkage increase

## Hotels

Flag:

- Falling occupancy
- ADR weakness
- RevPAR decline
- High lease burden
- Excessive renovation capex
- Destination concentration

## Cash Flow

Flag:

- PAT rising while CFO falls
- Persistent negative FCF
- Receivables rising
- Inventory rising
- Heavy growth capex
- Debt-funded expansion

The broader source framework similarly flags revenue growth without volume, price-led growth with weak demand, falling market share, inventory build-up and PAT/CFO divergence. fileciteturn20file0L243-L269

---

# 30. Positive Signals

Potential positive signals:

- Customer growth
- Transaction growth
- Healthy retention
- Rising ARPU
- Stable/improving take rate
- Higher utilization
- Same-store growth
- Strong mature-unit productivity
- Improving revenue/employee
- Better unit economics
- Stable/improving margins
- Healthy inventory
- Positive CFO
- Positive FCF
- High incremental ROCE
- Disciplined expansion
- Deleveraging
- Market-share gains
- Strong brand/distribution

These are analytical signals, not guarantees of future performance.

---

# 31. Scenario Analysis

## Bull Case

Assumptions:

- Strong consumer demand
- Customer growth
- Higher utilization
- Better pricing
- Improved mix
- Strong same-store growth
- New units ramp successfully
- Operating leverage

## Base Case

Assumptions:

- Normal demand
- Stable customer growth
- Normal utilization
- Planned expansion
- Normal margins
- Normal working capital

## Bear Case

Assumptions:

- Consumer slowdown
- Lower footfall/customers
- Lower utilization
- Pricing pressure
- Higher employee/rent costs
- Inventory build
- Higher marketing/customer-acquisition costs
- Weak cash generation

Calculate impact on:

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

---

# 32. Scoring Architecture

Do not use one generic score across all Consumer Services businesses.

Suggested dimensions:

| Dimension | Suggested Weight |
|---|---:|
| Business Quality | 15% |
| Demand & Growth Quality | 15% |
| Unit Economics / Operating Quality | 15% |
| Competitive Position | 10% |
| Cash Flow Quality | 15% |
| Balance Sheet | 10% |
| Capital Efficiency | 10% |
| Management & Governance | 10% |

**Valuation remains a separate decision-support layer.**

Industry-specific emphasis:

- Other Consumer Services → customer growth, retention, CAC/LTV, unit economics
- Platforms → GMV, take rate, contribution margin, retention, cash burn
- Hotels → occupancy, ADR, RevPAR, asset efficiency
- Restaurants → same-store growth, ticket size, store economics
- Retail → SSSG, sales/sq ft, inventory and store productivity

The broader Consumer Discretionary framework also specifies that weights should be adjusted by industry and that the system should display a data-confidence limitation when critical data is missing. fileciteturn19file3L565-L594

---

# 33. Metric Classification

Every metric must have a role:

```text
CORE
SUPPORTING
DIAGNOSTIC
SECTOR_SPECIFIC
VALUATION
PRESENTATION
```

Examples:

### Core

- Revenue growth
- Customer growth
- Utilization
- Unit economics
- EBITDA margin
- CFO
- ROCE

### Supporting

- Market share
- Digital penetration
- Employee productivity
- Location growth

### Diagnostic

- Inventory build
- CAC increase
- Take-rate compression
- Mature-store productivity decline

### Sector Specific

- RevPAR
- SSSG
- Sales/sq ft
- CAC/LTV
- Take rate

Sector-specific ratios should not be treated as universal missing-data failures.

---

# 34. Data Quality

Every metric must carry:

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

Allowed:

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

Calculated metrics must preserve source inputs.

Example:

```text
Revenue/store
=
Revenue / Average Store Count
```

Store:

- Revenue
- Average store count
- Period
- Formula
- Source
- Confidence

The source framework requires this metric lineage and confidence structure. fileciteturn19file3L598-L631

---

# 35. Source Hierarchy

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

For operating KPIs, prioritize company disclosures and exchange/regulatory filings.

Third-party data must not silently override company-reported data. fileciteturn19file3L635-L651

---

# 36. Agent Architecture

```text
Company Identification Agent
          ↓
Industry Classification Agent
          ↓
Business Model Agent
          ↓
Financial Data Agent
          ↓
Consumer Services KPI Agent
          ↓
Demand / Customer Agent
          ↓
Volume / Price / Mix Agent
          ↓
Unit Economics Agent
          ↓
Location / Capacity Agent
          ↓
Inventory Agent
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
Cycle / Demand Agent
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

The KPI agent should dynamically select metrics according to the business model rather than running every Consumer Services metric on every company.

---

# 37. Recommended Database Structure

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

## Consumer Services KPI

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
customer_count
active_users
transactions
arpu
take_rate
locations
utilization
retention
repeat_purchase
cac
ltv
revenue_per_customer
revenue_per_store
revenue_per_sqft
occupancy
adr
revpar
room_count
footfall
conversion_rate
average_ticket
same_store_sales_growth
inventory_turns
markdown_percentage
```

## Location

```text
company_id
period
location_type
location_count
new_locations
closures
average_area
revenue_per_location
ebitda_per_location
mature_productivity
```

## Platform Economics

```text
company_id
period
gmv
active_users
transactions
take_rate
revenue
contribution_margin
cac
ltv
cash_burn
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

## Unit Economics

```text
company_id
period
unit_type
metric
value
formula
source
confidence
```

---

# 38. Data Coverage Dashboard

Display business-model-specific coverage.

Example:

```text
Consumer Services KPI Coverage
────────────────────────────────
Customer Growth          ✓
Transactions             ✓
ARPU                     ✓
Utilization              ✓
Locations                ✓
Unit Economics           ✓
Retention                ?
CAC                      ?
LTV                      ?
Working Capital          ✓
CFO                      ✓
FCF                      ✓
ROCE                     ✓
Concall Guidance         ✓
```

For hotels:

```text
Occupancy                ✓
ADR                      ✓
RevPAR                   ✓
Room Count               ✓
Room Additions           ✓
Same-property Growth     ?
```

For retail:

```text
Store Count              ✓
SSSG                     ✓
Footfall                 ?
Sales/sq ft              ✓
Inventory Turns          ✓
Markdown                 ?
```

Missing data must never be converted to zero.

Use:

```text
AVAILABLE
CALCULABLE
PARTIAL
MISSING_INPUT
SOURCE_REQUIRED
NOT_APPLICABLE
INVALID
```

---

# 39. Final Screener Output

## A. Business Snapshot

- Company
- Industry
- Business model
- Customer type
- Geography
- Revenue model
- Asset intensity

## B. Demand Dashboard

- Customers
- Transactions
- Footfall
- Bookings
- Retention
- ARPU/ASP

## C. Operating Dashboard

### Other Consumer Services

- Active users
- Utilization
- Revenue/customer
- CAC
- LTV
- Take rate

### Leisure

- Occupancy
- ADR
- RevPAR
- Room count
- Revenue/room

### Retail

- Store count
- SSSG
- Footfall
- Conversion
- Average ticket
- Sales/sq ft
- Inventory turns

## D. Growth

- Revenue
- Customer/volume
- Price
- Mix
- New units
- Same-unit growth

## E. Profitability

- Gross margin
- EBITDA margin
- EBIT margin
- PAT margin
- Unit EBITDA

## F. Working Capital

- Inventory
- Receivables
- Payables
- CCC

## G. Cash Flow

- CFO
- FCF
- CFO/PAT
- FCF/PAT

## H. Balance Sheet

- Debt
- Net debt
- Lease liabilities
- Net debt/EBITDA
- Interest coverage

## I. Capital Efficiency

- ROCE
- ROIC
- Incremental ROCE

## J. Competitive Position

- Brand
- Distribution
- Market share
- Network effects
- Customer retention

## K. Management

- Guidance
- Capex
- Expansion
- Capital allocation
- Governance

## L. Peer Comparison

Use only economically relevant peers.

## M. Valuation

- Current valuation
- Historical valuation
- Peer valuation
- Growth/margin context
- FCF context

## N. Causal Analysis

Answer:

> **WHY did revenue, unit economics, margins, cash flow and returns change?**

## O. Risks

Evidence-backed red flags.

## P. Data Confidence

Display:

```text
Overall Data Confidence
HIGH / MEDIUM / LOW
```

and identify critical missing inputs.

---

# 40. Implementation Principles

1. Classify the business model before KPI selection.
2. Do not treat all Consumer Services businesses identically.
3. Separate customers, transactions and pricing.
4. Track unit economics.
5. Track mature-unit productivity separately from new-unit growth.
6. Separate end-consumer demand from channel/location expansion.
7. Track inventory carefully for retail.
8. Track occupancy/ADR/RevPAR for hotels.
9. Track GMV/take rate/unit economics for platforms.
10. Track CAC/LTV/retention where applicable.
11. Separate accounting profit from cash generation.
12. Track capex and incremental returns.
13. Include lease liabilities where economically material.
14. Preserve source lineage for every calculated metric.
15. Never treat missing data as zero.
16. Do not allow valuation to compensate for weak operating fundamentals.
17. Track management guidance longitudinally.
18. Explain changes through causal chains.
19. Compare companies using relevant business-model peers.
20. Display data-confidence limitations.

---

# 41. Central Fundamental Question

The Consumer Services analysis engine should ultimately answer:

> **Is this company creating durable value through customer growth, retention, pricing power, utilization, unit economics, competitive advantage and efficient capital deployment — or is reported growth being driven mainly by temporary demand, aggressive expansion, pricing, acquisitions or accounting effects?**

The complete causal chain is:

```text
CONSUMER DEMAND
      ↓
CUSTOMERS / FOOTFALL
      ↓
TRANSACTIONS
      ↓
ASP / ARPU / TAKE RATE
      ↓
REVENUE
      ↓
UTILIZATION
      ↓
UNIT ECONOMICS
      ↓
MARGIN
      ↓
WORKING CAPITAL
      ↓
CFO
      ↓
CAPEX
      ↓
FCF
      ↓
ROCE / ROIC
      ↓
COMPETITIVE ADVANTAGE
      ↓
SUSTAINABILITY OF GROWTH
      ↓
VALUATION
```
