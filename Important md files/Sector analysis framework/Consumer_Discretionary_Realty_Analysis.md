# Consumer Discretionary → Realty — Fundamental Analysis Framework

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
**Macro Sector:** Consumer Discretionary  
**Sector:** Realty  
**Industry:** Realty  

## Classification Hierarchy

```text
Consumer Discretionary
└── Realty
    └── Realty
```

> This is a **sector-value level framework**. It is designed specifically for companies classified as **Consumer Discretionary → Realty → Realty**, rather than applying a generic financial-ratio framework.

---

# 1. OBJECTIVE

Analyse a real-estate company as a combination of:

1. Land bank / project pipeline
2. Development capability
3. Launch pipeline
4. Pre-sales / bookings
5. Collections
6. Inventory monetisation
7. Realisations / pricing
8. Project execution
9. Construction cost
10. Cash-flow generation
11. Leverage
12. Capital allocation
13. Regulatory / approval risk
14. Competitive position
15. Valuation
16. Management quality and governance
17. Cycle positioning

The engine MUST NOT evaluate a real-estate company using generic P/E, ROE and revenue-growth ratios alone.

Real estate is fundamentally a:

```text
LAND / DEVELOPMENT RIGHTS
        +
LOCATION
        +
PROJECT PIPELINE
        +
LAUNCHES
        +
PRE-SALES
        +
COLLECTIONS
        +
EXECUTION
        +
MARGINS
        +
CASH FLOW
        +
BALANCE SHEET
        +
CAPITAL ALLOCATION
```

The analytical engine must therefore connect operating metrics to reported financial statements.

---

# 2. COMPANY CLASSIFICATION

## 2.1 Business Model

Classify the company into one or more of:

- Residential developer
- Commercial developer
- Office / IT park developer
- Retail / mall developer
- Mixed-use developer
- Industrial / logistics real estate
- Hospitality-linked real estate
- Plotted development
- Township development
- Redevelopment
- Rental / annuity-led real estate
- Development management
- Joint-venture / JDA-led developer
- Asset-light developer
- Integrated developer
- REIT / REIT-like rental platform, where applicable

Record:

```text
Business_Model
Revenue_Model
Development_Model
Asset_Model
Geographic_Focus
```

## 2.2 Development Structure

Capture whether projects are held through:

- Wholly owned subsidiaries
- Joint ventures
- Joint development agreements (JDA)
- Development management agreements
- SPVs
- Partnerships
- Landowner-sharing arrangements

A company with a large project pipeline does NOT necessarily own all the economic value represented by that pipeline.

The engine must distinguish:

```text
Gross Project Value
        ↓
Developer Economic Share
        ↓
Net Revenue / Cash Flow Potential
```

---

# 3. DATA PERIODS

Maintain:

### Annual

- Current FY
- 3Y history
- 5Y history
- 10Y history where available

### Quarterly

- Latest quarter
- Previous quarter
- YoY quarter
- 8-quarter history
- 12-quarter history where available

### TTM

```text
TTM = latest four reported quarters
```

For real estate, also maintain project-level lifecycle history because accounting revenue may not align with bookings.

---

# 4. REAL-ESTATE OPERATING DATA LAYER

The operating-data layer is more important than a simple P&L snapshot.

Capture:

```text
Launches
New Area Launched
Bookings / Pre-sales
Booking Value
Booking Volume
Average Selling Price
Collections
Construction Area
Area Delivered
Area Under Construction
Unsold Inventory
Completed Inventory
Project Pipeline
Gross Development Value
Developer Share
Land Cost
Construction Cost
Project-Level Debt
Net Debt
```

Where available, capture quarterly and annual values.

---

# 5. BUSINESS QUALITY

## 5.1 Geographic Position

Track:

- City
- Micro-market
- Project location
- Residential vs commercial exposure
- Tier 1 / Tier 2 / other market exposure
- Local market concentration

Calculate:

```text
Top_City_Revenue_%
Top_City_Bookings_%
Top_City_GDV_%
```

High concentration is not automatically negative. The engine should determine whether concentration is supported by strong market position and execution history.

---

# 6. LAND BANK AND DEVELOPMENT PIPELINE

Land is a core strategic asset but reported book value can be misleading.

Capture:

- Owned land
- Development rights
- Development potential
- Remaining saleable area
- Remaining developable area
- Project-wise GDV
- Project-wise developer share
- Acquisition cost
- Carrying value
- Land acquisition date
- Approval status
- Construction status
- Launch status

Calculate where possible:

```text
Land_Bank_Value
Remaining_Saleable_Area
GDV_per_Sqft
Land_Cost_per_Sqft
Embedded_Land_Value
```

### Pipeline Quality

Classify projects as:

```text
Land Identified
↓
Land Acquired / Rights Secured
↓
Approvals
↓
Launch Ready
↓
Launched
↓
Under Construction
↓
Completed
↓
Sold
```

A large pipeline with weak approvals or unclear economic ownership must not receive the same treatment as launch-ready inventory.

---

# 7. PROJECT-LEVEL ECONOMICS

For every material project, capture:

- Project name
- City / micro-market
- Product type
- Launch date
- Expected completion
- Saleable area
- Launched area
- Sold area
- Unsold area
- Booking value
- Collections
- Average selling price
- Estimated project cost
- Construction cost
- Land cost
- Other project costs
- Developer share
- JV/JDA partner share
- Estimated project margin
- Current project status

Calculate:

```text
Sales_Realisation_per_Sqft
Cost_per_Sqft
Project_Gross_Margin
Project_Contribution_Margin
Sales_Velocity
Collection_Efficiency
```

---

# 8. PRE-SALES / BOOKINGS

Pre-sales are one of the most important leading indicators.

Track:

- Quarterly bookings
- Annual bookings
- Booking value
- Booking volume
- Pre-sales growth
- Booking value / launch value
- Booking value / inventory
- Sales velocity
- New launches contribution
- Existing-project contribution

Calculate:

```text
PreSales_Growth
PreSales_CAGR_3Y
PreSales_CAGR_5Y
Sales_Velocity
Bookings_to_Completion
```

### Sales Velocity

Where area data exists:

```text
Sales_Velocity =
Area Sold / Area Available for Sale
```

Track the trend rather than relying on one quarter.

---

# 9. COLLECTIONS

Bookings are not cash.

Track:

- Customer collections
- Collections growth
- Collections / bookings
- Collections / reported revenue
- Receivables
- Customer advances
- Cancellation levels where disclosed

Calculate:

```text
Collection_Efficiency =
Collections / Bookings
```

Flag:

```text
BOOKINGS_UP + COLLECTIONS_FLAT
```

and

```text
REVENUE_UP + RECEIVABLES_UP_SHARPLY
```

These may indicate weaker cash conversion.

---

# 10. PRICE / REALISATION ANALYSIS

Track:

- Average selling price
- Price per sq ft
- Project-level realisation
- City-level realisation
- Product-level realisation
- Launch price
- Current price
- Premium / discount to local market where reliable

Separate:

```text
Price Growth
+
Volume Growth
+
Mix Change
```

A rise in booking value may come from:

- Higher prices
- More area sold
- Premium project launches
- Larger unit sizes
- Geographic mix

The engine should identify the actual driver.

---

# 11. VOLUME / AREA ANALYSIS

Track:

- Area launched
- Area sold
- Area booked
- Area constructed
- Area delivered
- Area remaining

Calculate:

```text
Volume_Growth
Area_Sold_Growth
Launch_Growth
Inventory_Turnover
```

Use both value and area metrics.

```text
Booking_Value ↑
Area_Sold →
ASP ↑
```

means price/mix-led growth.

```text
Booking_Value ↑
Area_Sold ↑
ASP →
```

means volume-led growth.

---

# 12. INVENTORY ANALYSIS

Track:

- Completed inventory
- Under-construction inventory
- Unsold inventory
- Inventory ageing
- Inventory by project
- Inventory by city
- Inventory as % of launched area

Flag:

```text
RISING_UNSOLD_INVENTORY
RISING_COMPLETED_INVENTORY
SLOWING_SALES_VELOCITY
```

The engine should distinguish healthy newly launched inventory from aged inventory.

---

# 13. PROJECT EXECUTION

Track:

- Construction progress
- Construction spend
- Completion timelines
- Delivery volume
- Possession timelines
- Project delays
- Cost overruns
- Approval delays

Calculate:

```text
Execution_Progress
Cost_Progress
Schedule_Variance
Cost_Variance
```

Flag:

```text
COST_PROGRESS >> PHYSICAL_PROGRESS
```

or:

```text
TIME_OVERRUN + COST_OVERRUN
```

---

# 14. CONSTRUCTION COST ANALYSIS

Track:

- Construction cost / sq ft
- Cement
- Steel
- Labour
- MEP
- Contractor costs
- Finishing costs
- Infrastructure costs
- Interest / finance cost
- Other project expenses

Analyse:

```text
Construction_Cost_Growth
Construction_Cost_per_Sqft
Gross_Margin_Trend
```

Separate commodity-driven cost inflation from execution inefficiency.

---

# 15. P&L ANALYSIS

Track:

- Revenue
- Revenue growth
- Gross profit where meaningful
- EBITDA
- EBITDA margin
- EBIT
- PBT
- PAT
- EPS
- Other income
- Finance cost
- Exceptional items

For real estate, reconcile reported revenue with:

```text
Bookings
Collections
Project Completion
Percentage-of-Completion / Revenue Recognition
Inventory
```

Do not interpret a single-quarter revenue spike without understanding project recognition.

---

# 16. REVENUE QUALITY

Classify revenue into:

- Residential sales
- Commercial sales
- Rental income
- Development management fees
- Joint venture income
- Other operating income
- Other income

Calculate:

```text
Core_RealEstate_Revenue_%
Recurring_Rental_Revenue_%
Development_Revenue_%
Other_Income_%
```

Separate operating income from treasury / investment income.

---

# 17. MARGIN ANALYSIS

Track:

- Gross margin
- EBITDA margin
- EBIT margin
- Project-level margin
- Segment margin
- Margin trend
- Margin vs booking realisation
- Margin vs construction cost

Causal chain:

```text
ASP
↓
Revenue / Sqft
↓
Cost / Sqft
↓
Project Gross Margin
↓
Corporate Overheads
↓
EBITDA
↓
PAT
```

Flag:

```text
ASP ↑ + COST ↑↑ + MARGIN ↓
```

and:

```text
REVENUE ↑ + EBITDA ↑ + CFO ↓
```

---

# 18. WORKING CAPITAL

Track:

- Trade receivables
- Customer advances
- Inventory
- Contract assets
- Contract liabilities
- Payables
- Other current assets
- Other current liabilities

Calculate where meaningful:

```text
Inventory_Days
Receivable_Days
Payable_Days
Working_Capital_to_Revenue
```

Real estate requires special interpretation because customer advances can be a source of project funding.

Analyse:

```text
Customer_Advances
+
Collections
+
Project_Inventory
+
Receivables
```

together rather than independently.

---

# 19. CASH FLOW

Track:

- CFO
- CFO / PAT
- CFO / EBITDA
- Capex
- Land acquisition
- Project investment
- Investing cash flow
- Financing cash flow
- FCF
- Debt raised
- Debt repayment

Calculate:

```text
CFO_PAT
FCF_PAT
FCF_Revenue
Cash_Generation_per_Booking
```

### Critical Real-Estate Reconciliation

```text
Bookings
    ↓
Collections
    ↓
Project Spending
    ↓
Operating Cash Flow
    ↓
Free Cash Flow
```

Flag:

```text
BOOKINGS ↑↑
COLLECTIONS ↑
CFO ↓
DEBT ↑
```

as a cash-conversion warning requiring investigation.

---

# 20. CAPEX AND LAND ACQUISITION

Separate:

- Maintenance capex
- Construction capex
- Land acquisition
- Development rights
- Investments in JVs
- Strategic acquisitions

Calculate:

```text
Growth_Capex / Revenue
Land_Acquisition / CFO
Capex / Depreciation
```

A developer can report strong earnings while consuming significant cash through land and project investments.

---

# 21. BALANCE SHEET

Track:

- Gross debt
- Net debt
- Cash
- Investments
- Inventory
- Land
- Receivables
- Customer advances
- Payables
- Net worth
- Minority interest
- JV exposure

Calculate:

```text
Net_Debt
Net_Debt_to_EBITDA
Debt_to_Net_Worth
Net_Debt_to_Operating_Cash_Flow
Interest_Coverage
```

Also track:

```text
Project_Level_Debt
Corporate_Level_Debt
JV_Debt
```

because consolidated debt can hide the location of leverage.

---

# 22. LEVERAGE AND DEBT QUALITY

Analyse:

- Debt maturity
- Interest rate
- Secured vs unsecured debt
- Project-level financing
- Corporate debt
- Refinancing requirements
- Debt repayment schedule
- Interest burden
- Debt-funded land acquisition

Flag:

```text
DEBT ↑ + CASH FLOW ↓
DEBT ↑ + PRE-SALES ↓
DEBT ↑ + INVENTORY ↑
```

as a high-priority investigation pattern.

---

# 23. ROCE / ROIC / CAPITAL EFFICIENCY

Track:

- ROCE
- ROIC
- ROE
- Incremental ROCE
- Incremental ROIC

But interpret these with the development cycle.

A project-heavy developer may have temporarily depressed accounting returns before monetisation.

Therefore calculate:

```text
Reported_ROCE
Reported_ROIC
Incremental_ROIC
Project_Return_Profile
```

where sufficient data exists.

---

# 24. DEMAND ANALYSIS

Track demand drivers:

- Housing demand
- Affordability
- Mortgage rates
- Employment
- Income growth
- Urbanisation
- Population growth
- Infrastructure development
- Commercial leasing demand
- Office absorption
- Retail consumption

Separate:

```text
Structural Demand
vs
Cyclical Demand
```

Do not assume national housing trends apply equally to every micro-market.

---

# 25. AFFORDABILITY

For residential developers track:

- Average ticket size
- Home loan rates
- EMI burden
- Household income
- Property price / income
- Down-payment requirements

Where data exists:

```text
Affordability_Index
```

Track changes over time.

---

# 26. INTEREST-RATE SENSITIVITY

Model:

```text
Mortgage Rates ↑
        ↓
EMI ↑
        ↓
Affordability ↓
        ↓
Booking Velocity ↓
        ↓
Pre-sales ↓
```

Also analyse the opposite scenario.

For developers with high debt:

```text
Interest Rates ↑
        ↓
Finance Cost ↑
        ↓
Cash Flow ↓
        ↓
Project Returns ↓
```

---

# 27. SUPPLY ANALYSIS

Track market:

- New launches
- New supply
- Unsold inventory
- Absorption
- Inventory months
- Competing projects
- Developer market share

Calculate where available:

```text
Supply_Growth
Absorption_Growth
Inventory_Months
Market_Share
```

Interpret:

```text
Supply ↑↑ + Absorption →
```

as potential pricing / inventory pressure.

---

# 28. COMPETITIVE POSITION

Track:

- Market share
- Brand strength
- Project locations
- Land access
- Execution track record
- Pricing power
- Sales velocity
- Customer trust
- Delivery record
- Balance-sheet strength

Possible competitive advantages:

- Scarce land
- Superior locations
- Brand
- Execution capability
- Customer trust
- Distribution network
- Access to capital
- Local market knowledge
- Redevelopment relationships

Competitive advantage must be supported by observable evidence.

---

# 29. MANAGEMENT AND CAPITAL ALLOCATION

Analyse:

- Land acquisitions
- Project launches
- Debt strategy
- Dividends
- Buybacks
- Equity issuance
- Dilution
- Joint ventures
- Related-party transactions
- Promoter transactions
- Acquisition strategy
- Asset monetisation
- Capital recycling

Track:

```text
Capital_Allocation_History
Debt_Discipline
Dilution_History
Project_Returns
```

---

# 30. MANAGEMENT / CONCALL INTELLIGENCE

Parse annual reports, investor presentations, exchange filings and earnings calls.

Extract:

### Management Guidance

- Booking guidance
- Sales growth
- Launch pipeline
- New project additions
- Collection guidance
- Margin commentary
- Completion guidance
- Debt reduction
- Cash-flow expectations
- Land acquisition plans

### Forward-Looking Statements

Store:

```text
Guidance_Date
Metric
Guidance
Time_Horizon
Actual_Result
Variance
Management_Explanation
```

Calculate:

```text
Guidance_Accuracy
Guidance_Raise_Count
Guidance_Cut_Count
Execution_vs_Guidance
```

Do not treat management guidance as fact until actual results validate it.

---

# 31. PROMOTER / GOVERNANCE ANALYSIS

Track:

- Promoter holding
- Promoter pledge
- Promoter buying
- Promoter selling
- Related-party transactions
- Auditor changes
- Auditor qualifications
- Subsidiary complexity
- Contingent liabilities
- Regulatory actions
- Litigation disclosures
- Preferential issues
- Warrants
- Equity dilution

Flag:

```text
RISING_PLEDGE
PERSISTENT_PROMOTER_SELLING
AUDITOR_RESIGNATION
QUALIFIED_AUDIT
LARGE_RELATED_PARTY_TRANSACTIONS
RAPID_DILUTION
UNEXPLAINED_SUBSIDIARY_COMPLEXITY
```

---

# 32. PEER COMPARISON

Compare relevant real-estate peers on:

```text
Pre-sales Growth
Bookings
Sales Velocity
Collections Growth
Revenue CAGR
EBITDA Margin
Project Margin
Inventory
Inventory Turnover
Net Debt
Net Debt / EBITDA
CFO / PAT
FCF / PAT
ROCE
ROIC
Market Share
Launch Pipeline
GDV
Developer Share of GDV
P/E
P/B
EV/EBITDA
EV/Revenue
FCF Yield
```

Use peer median and percentiles where sufficient data exists.

Do not compare companies without adjusting for:

- Business model
- Geography
- Project mix
- Development cycle
- Accounting model
- JV/JDA structure

---

# 33. VALUATION FRAMEWORK

Real estate should not rely on P/E alone.

Use multiple methods.

## 33.1 Earnings Valuation

- P/E
- EV/EBITDA
- EV/Revenue

Compare:

```text
Current
vs
Historical
vs
Peers
```

## 33.2 NAV / RNAV

Where sufficient project-level information exists:

```text
Gross Asset Value
- Net Debt
= Equity Value
```

For development businesses:

```text
Estimated Project NAV
+
Land / Investment Asset Value
-
Net Debt
-
Other Adjustments
=
Estimated Equity NAV
```

Compare:

```text
Market Capitalisation / NAV
```

or:

```text
Price / NAV
```

## 33.3 Embedded Value

Estimate:

```text
Current Projects
+
Future Project Pipeline
+
Land Bank / Development Rights
-
Net Debt
```

Apply conservative assumptions and clearly label estimates.

---

# 34. HISTORICAL VALUATION

Track:

- Historical P/E
- Historical EV/EBITDA
- Historical P/B
- Historical P/NAV
- Historical EV/Revenue

Also compare valuation against:

```text
Growth
Margin
ROIC
Pre-sales
Cash Flow
Net Debt
Project Pipeline
```

A lower multiple is not automatically attractive if business quality or future cash generation has deteriorated.

---

# 35. CYCLE ANALYSIS

Classify the real-estate cycle using:

```text
Demand
+
Mortgage Rates
+
Affordability
+
New Supply
+
Absorption
+
Inventory
+
Pricing
+
Construction Costs
+
Developer Leverage
```

Possible state:

```text
EARLY RECOVERY
RECOVERY
EXPANSION
PEAK
SLOWDOWN
CORRECTION
```

Cycle classification should be evidence-based and recorded with supporting metrics.

---

# 36. GROWTH QUALITY

Separate:

### Healthy growth

```text
Pre-sales ↑
Collections ↑
Area Sold ↑
ASP stable/up
Debt controlled
CFO improving
```

### Lower-quality growth

```text
Revenue ↑
Debt ↑↑
Inventory ↑
Receivables ↑
CFO weak
```

### Acquisition / land-led growth

```text
Pipeline ↑
Land spend ↑
Debt ↑
Current earnings →
```

The engine should explain the source and sustainability of growth.

---

# 37. CAUSAL ANALYSIS ENGINE

The system must answer:

### If revenue increased:

```text
Was it:
Price?
Volume?
Project mix?
New launch?
Project completion?
Acquisition?
```

### If margin increased:

```text
ASP ↑?
Construction cost ↓?
Land cost advantage?
Project mix?
Operating leverage?
Other income?
```

### If cash flow deteriorated:

```text
Inventory ↑?
Land acquisition?
Construction spend?
Receivables ↑?
Collections ↓?
Debt servicing?
JV investment?
```

### If debt increased:

```text
Land acquisition?
Project construction?
Working capital?
Acquisition?
Dividend?
Buyback?
```

The final analysis must explain **why** the metric changed.

---

# 38. POSITIVE SIGNALS

Potential positive signals:

- Sustained pre-sales growth
- Strong sales velocity
- Collections tracking bookings
- Rising ASP without severe volume loss
- Healthy project margins
- Strong execution
- Falling inventory
- Launch pipeline with strong absorption
- Debt reduction
- Improving CFO
- Strong FCF
- High incremental ROIC
- Successful asset monetisation
- Strong brand / market share
- Disciplined capital allocation

Signals must be supported by data.

---

# 39. RED FLAGS

High-priority investigation flags:

- Bookings rising but collections weak
- Revenue rising while CFO deteriorates
- Debt rising rapidly
- Debt-funded land acquisition
- Rising unsold inventory
- Rising completed inventory
- Falling sales velocity
- Large project delays
- Construction cost overruns
- Margin compression despite price increases
- Aggressive accounting / revenue recognition concerns
- Large related-party transactions
- Rising promoter pledge
- Persistent promoter selling
- Frequent equity dilution
- Auditor resignation
- Qualified audit opinion
- Large contingent liabilities
- Excessive JV complexity
- Weak project-level transparency

---

# 40. SCENARIO ANALYSIS

The engine should produce:

## Bull Case

Potential combination:

```text
Pre-sales ↑
ASP ↑
Collections ↑
Launches ↑
Execution strong
Margins ↑
Debt ↓
CFO ↑
```

## Base Case

```text
Moderate bookings
Stable ASP
Normal execution
Stable margins
Controlled debt
```

## Bear Case

Potential combination:

```text
Mortgage rates ↑
Demand ↓
Sales velocity ↓
Inventory ↑
ASP pressure
Construction cost ↑
Collections ↓
Debt ↑
CFO ↓
```

Scenarios must show assumptions rather than produce unsupported price targets.

---

# 41. REAL-ESTATE-SPECIFIC SCORE ARCHITECTURE

Do not hide the analysis inside one opaque score.

Recommended dimensions:

```text
Business / Location Quality
Development Pipeline Quality
Pre-sales & Demand
Execution Quality
Margin Quality
Cash Flow Quality
Balance Sheet Quality
Capital Efficiency
Management / Governance
Competitive Advantage
Valuation
Data Confidence
```

Example weighting:

```text
Business / Location Quality       10%
Pipeline Quality                  10%
Demand / Pre-sales                15%
Execution Quality                 10%
Margin Quality                    10%
Cash Flow Quality                 15%
Balance Sheet Quality             10%
Capital Efficiency                 5%
Management / Governance            5%
Competitive Advantage              5%
Valuation                         15%
```

Weights must remain configurable.

Do not let valuation override fundamental deterioration automatically.

---

# 42. DATA QUALITY

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

Data types:

```text
REPORTED
CALCULATED
ESTIMATED
MANAGEMENT_DISCLOSED
THIRD_PARTY
```

Never silently mix reported and estimated project values.

For estimated NAV:

```text
ESTIMATED
```

must be explicitly shown.

---

# 43. SOURCE PRIORITY

Use:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings / Concall Transcript
5. Company Exchange Filings
6. NSE / BSE filings
7. Regulatory filings
8. Company investor-relations website
9. Reliable financial databases
10. Third-party sources

For project-level metrics, prioritize company disclosures.

If sources conflict:

```text
Identify discrepancy
        ↓
Prefer primary filing
        ↓
Record alternative value if material
        ↓
Do not silently overwrite
```

---

# 44. AGENT ARCHITECTURE

Recommended pipeline:

```text
Company Data
     ↓
Classification Agent
     ↓
Financial Statement Agent
     ↓
Project / Real Estate KPI Agent
     ↓
Pre-sales & Collections Agent
     ↓
Land / Pipeline Agent
     ↓
Execution Agent
     ↓
Cash Flow Agent
     ↓
Balance Sheet Agent
     ↓
Management / Concall Agent
     ↓
Governance / Risk Agent
     ↓
Peer Comparison Agent
     ↓
Valuation Agent
     ↓
Causal Analysis Agent
     ↓
Scoring Agent
     ↓
Final Fundamental Report
```

---

# 45. DATABASE STRUCTURE

Recommended entities:

```text
companies
sectors
industries

realty_projects
project_locations
project_status
project_area
project_cost
project_sales
project_collections

land_bank
development_rights
jv_projects
jda_projects

quarterly_financials
annual_financials
cash_flow
balance_sheet

debt
debt_maturity

management_guidance
concall_transcripts
guidance_accuracy

peer_metrics
valuation_history

red_flags
causal_events
analysis_scores
data_quality
```

## Project-level schema

```text
company_id
project_id
project_name
city
micro_market
project_type
ownership_type
developer_share
total_saleable_area
launched_area
sold_area
unsold_area
booking_value
collections
asp_per_sqft
estimated_cost
construction_progress
completion_date
status
source
period
confidence
```

---

# 46. FINAL SCREENER OUTPUT

The final output should contain:

```text
Company:
Macro Sector: Consumer Discretionary
Sector: Realty
Industry: Realty

Business Model:

BUSINESS / LOCATION QUALITY       XX/100
PIPELINE QUALITY                  XX/100
DEMAND / PRE-SALES                XX/100
EXECUTION QUALITY                 XX/100
MARGIN QUALITY                    XX/100
CASH FLOW QUALITY                 XX/100
BALANCE SHEET QUALITY             XX/100
CAPITAL EFFICIENCY                XX/100
MANAGEMENT / GOVERNANCE           XX/100
COMPETITIVE ADVANTAGE             XX/100
VALUATION                         XX/100

DATA CONFIDENCE:

KEY POSITIVES
1.
2.
3.
4.
5.

KEY CONCERNS
1.
2.
3.
4.
5.

RED FLAGS
1.
2.
3.

DEMAND ENGINE
- Pre-sales:
- Area Sold:
- ASP:
- Sales Velocity:
- Collections:

PROJECT ENGINE
- Launch Pipeline:
- GDV:
- Developer Share:
- Execution:
- Inventory:

CASH ENGINE
- CFO:
- FCF:
- CFO/PAT:
- Debt:

CAPITAL EFFICIENCY
- ROCE:
- ROIC:
- Incremental ROIC:

VALUATION
- P/E:
- EV/EBITDA:
- P/NAV:
- Historical Position:
- Peer Position:

MANAGEMENT / GUIDANCE
- Guidance:
- Actual:
- Variance:
- Guidance Accuracy:

INVESTMENT THESIS

BULL CASE

BASE CASE

BEAR CASE

WHAT WOULD BREAK THE THESIS

METRICS TO MONITOR NEXT QUARTER
```

---

# 47. IMPLEMENTATION PRINCIPLE

Do NOT build the Realty screener as:

```text
IF ROE > X
AND PE < Y
AND Revenue Growth > Z
THEN PASS
```

Instead:

```text
RAW DATA
   ↓
NORMALIZATION
   ↓
PROJECT / OPERATING METRICS
   ↓
FINANCIAL METRICS
   ↓
TREND ANALYSIS
   ↓
PEER COMPARISON
   ↓
CAUSAL ANALYSIS
   ↓
RED FLAGS
   ↓
SCORING
   ↓
VALUATION
   ↓
INVESTMENT THESIS
```

The engine must answer:

> **Why did the company's operating and financial metrics change?**

> **Is the change driven by price, volume, project mix, launches, execution, cost, leverage or accounting recognition?**

> **Is the change sustainable?**

> **How does the company compare with relevant real-estate peers?**

> **Does the current valuation reflect the quality and future cash-generation potential of the development pipeline?**

---

# 48. CORE FUNDAMENTAL QUESTION

For a Realty company, the central question is:

> **Can the developer convert its land/development pipeline into sustained pre-sales, collections and free cash flow at attractive project-level returns, while maintaining execution discipline and a healthy balance sheet across the real-estate cycle?**

The backbone of the Realty screener should therefore be:

```text
LAND / DEVELOPMENT RIGHTS
          ↓
PROJECT PIPELINE
          ↓
LAUNCHES
          ↓
PRE-SALES
          ↓
COLLECTIONS
          ↓
EXECUTION
          ↓
REVENUE / MARGINS
          ↓
CASH FLOW
          ↓
DEBT
          ↓
ROIC
          ↓
VALUATION
```
