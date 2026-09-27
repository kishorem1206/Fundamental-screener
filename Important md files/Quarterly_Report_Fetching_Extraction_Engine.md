# Fundamental Screener — Recent Quarterly Report Fetching & Extraction Engine
## Master Document-Parsing Book for Current-Quarter / Latest-Results Analysis


# 1. PURPOSE AND ARCHITECTURE

This is the **upstream current-results extraction book**. It feeds the existing sector-specific engines with the latest quarter's reported financials, operating KPIs, balance-sheet movements, segment data and management guidance.

```text
LATEST RESULTS PACKAGE
→ CLASSIFY DOCUMENT
→ LOCATE RESULTS / NOTES / SEGMENTS
→ IDENTIFY PERIOD COLUMNS
→ IDENTIFY STANDALONE / CONSOLIDATED
→ EXTRACT
→ NORMALIZE
→ VALIDATE
→ STORE LINEAGE
→ COMMON DATA LAYER
→ SECTOR ENGINE
```

The annual engine gives the long-term baseline. This engine answers: **what changed recently?**

# 2. ACCEPTED QUARTERLY DOCUMENTS

Recognize:

- Financial Results
- Quarterly Results
- Unaudited Financial Results
- Limited Review Results
- Audited Q4 Results
- Results for quarter ended...
- Results for quarter and half year ended...
- Results for quarter and nine months ended...
- Results with notes
- Segment results
- Investor presentation
- Shareholder letter
- Earnings release

For accounting totals, prefer official financial results and attached notes. Use presentations and management commentary for operating KPIs and explanations.

# 3. PERIOD CONTROL

Every record requires:

```text
period_start
period_end
duration_months
period_type
```

Use:

```text
CURRENT_QUARTER
PREVIOUS_QUARTER
PREVIOUS_YEAR_QUARTER
CURRENT_YTD
PREVIOUS_YEAR_YTD
FULL_YEAR
TTM_CALCULATED
```

Never mix Q1 with 6M, Q4 with FY, or a current quarter with a prior-year quarter.

# 4. Q4 SPECIAL HANDLING

Q4 packages may contain:

- current Q4
- prior Q4
- current FY
- prior FY

Extract all separately.

Do not automatically derive Q4 as `FY - 9M` when an explicit Q4 figure exists.

# 5. SIGN, BLANK AND UNIT NORMALIZATION

Parentheses are negative:

```text
(250) → -250
```

Blank/dash/N/A are not zero.

Store raw and normalized values.

Capture units such as:

- ₹ lakh/crore/million/billion
- foreign currencies
- tonnes/MT
- MW/GW
- GWh/TWh
- units
- subscribers
- customers
- km
- barrels/litres

Never silently convert currencies.

# 6. STANDALONE VS CONSOLIDATED

Every value:

```text
report_scope = STANDALONE | CONSOLIDATED
```

Extract both where available.

# 7. QUARTERLY P&L

Extract:

- revenue from operations
- other income
- total income
- materials/purchases
- inventory change
- employee costs
- power/fuel
- other operating expenses
- finance costs
- depreciation/amortization
- EBITDA if reported
- EBIT if reported
- exceptional items
- PBT
- tax
- PAT
- PAT attributable to owners
- NCI
- OCI
- total comprehensive income
- basic/diluted EPS

Keep operating revenue and other income separate.

# 8. BALANCE SHEET

Extract quarter-end:

- PPE
- ROU assets
- CWIP
- goodwill/intangibles
- investments
- inventory
- receivables
- contract assets
- cash
- bank balances
- other current assets
- equity/reserves
- debt
- lease liabilities
- payables
- contract liabilities
- provisions
- tax liabilities
- other liabilities

Validate:

```text
Assets ≈ Equity + Liabilities
```

# 9. CASH FLOW

Quarterly reports frequently provide **YTD cash flow**.

Extract:

### CFO
PBT, non-cash adjustments, working-capital changes, tax paid, CFO.

### CFI
PPE/intangible purchases, investments, acquisitions, asset sales and other investing flows.

### CFF
Debt raised/repaid, leases, equity, buybacks, dividends and other financing flows.

Also extract opening cash, closing cash and FX effects.

# 10. SINGLE-QUARTER CASH FLOW FROM YTD

If:

```text
Q1 CFO = reported
6M CFO = reported
```

then:

```text
Q2 CFO = 6M CFO - Q1 CFO
```

This must be stored as:

```text
data_type = CALCULATED
formula = current_YTD - previous_YTD
```

Never label the derived Q2 figure as reported.

# 11. SEGMENT RESULTS

Extract every material segment:

- reported segment name
- revenue
- external revenue
- inter-segment revenue
- segment result/EBIT
- margin
- assets
- liabilities
- capex
- depreciation
- operating KPIs

Segment totals may differ from consolidated revenue because of eliminations. Do not force reconciliation without checking the segment note.

# 12. NOTES AND HIDDEN QUARTERLY DATA

Search notes for:

- revenue disaggregation
- segment information
- debt
- PPE/CWIP
- inventory
- receivables/payables
- tax
- exceptional items
- related parties
- contingent liabilities
- acquisitions/disposals
- impairment
- leases
- fair value
- FX
- investments

# 13. WORKING CAPITAL

Extract:

- inventory
- receivables
- payables
- contract assets/liabilities
- customer advances
- supplier advances
- other current assets/liabilities
- ageing where disclosed

Calculate only when source inputs exist:

```text
Inventory Days
Receivable Days
Payable Days
CCC
```

# 14. DEBT / CASH

Extract:

- gross debt
- current/non-current debt
- working-capital borrowings
- bonds/debentures
- term loans
- lease liabilities
- maturity
- interest rate
- security
- covenants
- refinancing
- cash
- liquid investments

If calculating net debt, preserve the exact formula and components.

# 15. MANAGEMENT GUIDANCE

Search results presentations, shareholder letters, MD&A-style updates and concall materials for:

- revenue/growth guidance
- margin guidance
- volume guidance
- price guidance
- capex guidance
- capacity guidance
- utilization guidance
- order-book guidance
- launch guidance
- debt reduction
- cash-flow expectations

Store as:

```text
data_type = MANAGEMENT_DISCLOSED
```

Never treat guidance as reported actuals.

# 16. GUIDANCE TRACKER

Build:

```text
PREVIOUS GUIDANCE
→ CURRENT ACTUAL
→ VARIANCE
→ MANAGEMENT EXPLANATION
→ UPDATED GUIDANCE
```

Statuses:

```text
MET
EXCEEDED
MISSED
REVISED
NOT_COMPARABLE
```

# 17. RECENT-QUARTER DIAGNOSTIC INPUTS

Preserve the inputs needed to calculate:

### Growth
- revenue YoY/QoQ
- volume growth
- price/mix
- segment growth

### Profitability
- gross margin
- EBITDA/margin
- EBIT/margin
- PAT/margin

### Cash
- CFO
- CFO/PAT
- FCF
- capex
- working capital

### Balance sheet
- debt
- cash
- net debt
- receivables
- inventory
- payables

### Operating KPIs
- capacity
- utilization
- volume
- ASP
- orders/order book
- subscribers/ARPU
- AUM/NIM/asset quality
- beds/occupancy
- production/generation
- tariff
- etc.

# 18. QUARTERLY SECTOR KPI DICTIONARY

### Metals & Mining
Production, sales/shipment, realization, commodity price, capacity, utilization, cost/tonne, EBITDA/tonne, ore grade, recovery, downstream output, export/domestic mix, energy, freight, capex.

### Construction Materials
Cement/clinker/RMC volume, capacity, utilization, realization, regional prices, fuel/power, freight, raw material, dealer inventory, market share, capacity additions.

### Chemicals
Production, sales, realization, product mix, capacity/utilization, raw-material cost, energy, freight, export/domestic, customer concentration, specialty share, new products, registrations, R&D.

### Fertilizers & Agrochemicals
Volume, mix, realization, subsidy, subsidy receivables, raw materials, crop demand, monsoon, channel inventory, exports, registrations, molecules, capacity/utilization.

### Forest Materials
Paper/pulp/jute volume, realization, capacity/utilization, pulp/wood/waste-paper cost, energy, freight, export demand, mix.

### Realty
Bookings/pre-sales, collections, launches, area sold/launched, realization/sq ft, inventory, construction progress/cost, land bank, JDA, customer advances, project debt, rental occupancy/income.

### Textiles & Apparels
Yarn/fabric/garment volume, ASP, capacity/utilization, cotton/fibre cost, energy, export/domestic demand, brand/store metrics, inventory, customer concentration.

### Consumer Services
Customers, active users, orders/transactions, GMV, revenue, take rate, ARPU, churn/retention, store count, footfall, same-store growth, service-provider count, utilization.

### Media/Entertainment/Publication
Subscribers, audience, engagement, ad/subscription revenue, ARPU, content cost/amortization, circulation, ad rates, screens, occupancy, ticket volume, digital/OTT metrics.

### Automobiles/Auto Components
Production, dispatch/retail volume, model mix, ASP, market share, EV/ICE, exports, capacity/utilization, order book, launches, commodity cost, warranty, R&D, customer concentration.

### Consumer Durables
Units, ASP, volume, premium mix, distribution/stores/dealers, channel inventory, raw-material cost, launches, market share, capacity/utilization, service network.

### Diversified
Every material segment's revenue, growth, EBIT, margin, assets, capex, operating KPIs, subsidiary/JV/associate contribution, acquisitions/disposals, corporate overhead, debt/cash.

### Oil/Gas/Consumable Fuels
Production, refinery throughput, GRM, crude intake, gas/LNG volume, pipeline utilization, retail fuel volume, marketing margin, realization, oil/gas price, inventory effects, fuel cost, capex, reserves, capacity, regulation.

### FMCG
Volume/value/price growth, mix, gross margin, premiumization, market share, rural/urban, trade-channel mix, e-commerce/quick commerce, launches, advertising, channel inventory, raw-material costs, capacity/utilization.

### Financial Services
**Banks:** deposits, advances, CASA, NIM, GNPA/NNPA, slippages, credit cost, provisions, CRAR/CET1, PPOP, cost/income, fee income, loan mix.  
**Insurance:** GWP/NBP/APE/VNB, VNB margin, persistency, claims/combined ratio, solvency, embedded value, AUM.  
**Capital markets:** AUM, clients, trading volumes, market share, brokerage/advisory.  
**NBFC:** AUM, disbursements, yield, cost of funds, spread/NIM, GNPA/NNPA, collections, credit cost, capital adequacy.  
**Fintech:** users, transactions, TPV/GMV, take rate, revenue, contribution margin, CAC, retention, AUM/origination.

### Healthcare
**Hospitals:** beds, occupancy, ARPOB, IPD/OPD, ALOS, payer/specialty mix, new beds, capex.  
**Pharma:** product sales, geography, volume/price, launches, approvals, pipeline, R&D, API, capacity/utilization, regulatory observations.  
**Equipment:** installed base, units, ASP, consumables, service revenue, orders/order book, utilization, R&D.

### Capital Goods
Order inflow/book, book-to-bill, order-book/revenue, capacity/utilization, production, ASP, project execution, cancellations, customer concentration, government/private, exports, R&D, equipment utilization.

### Construction
Order inflow/book, book-to-bill, execution, project revenue/margin, contract type, government/private mix, material/subcontracting/labour cost, equipment utilization, retention, advances, claims, guarantees, working capital.

### Information Technology
**Services:** revenue/CC growth, volume, pricing, utilization, attrition, headcount, offshore/onsite, billing rates, large deals/TCV/bookings, top clients, revenue/employee, AI/cloud/digital mix, margin.  
**Software:** ARR, recurring revenue, customers, NRR, churn, ACV, R&D.  
**Hardware:** units, ASP, production, capacity/utilization, inventory, component costs.

### Services
Customers, transactions, revenue, pricing, utilization, capacity, market share, contracts, order book, pipeline, concentration, employee count, revenue/employee, segment margin. Transport: passenger/freight, tonne-km/passenger-km, fleet, load factor, yield. Infrastructure: traffic/throughput, capacity, utilization, tariff.

### Telecom
**Services:** subscribers, active users, net adds, churn, ARPU, data usage/traffic, revenue/GB, 4G/5G/broadband, enterprise revenue, network utilization, towers/fibre/spectrum, capex, leases, debt.  
**Equipment:** units, ASP, orders, order book, book-to-bill, production, capacity/utilization, concentration, R&D, exports, inventory, receivables.

### Power
Capacity, generation, PLF, availability, utilization, CUF, renewable/thermal/hydro/nuclear mix, transmission lines/substations, distribution customers, units sold, AT&C loss, tariff, PPA/merchant tariff, fuel consumption, heat rate, auxiliary consumption, fuel cost, regulatory assets, subsidy receivables, capex, commissioning, debt.

### Other Utilities
Water: connections, supplied/delivered/billed volume, tariff, non-revenue water, network, collection, capex, receivables.  
Gas distribution: connections, volume, network, utilization, tariff, realized margin, customer mix, capex.  
Waste: volume, collection, processing/treatment/disposal, service fee, recovery value, contract tenure, customer/municipality, capex, working capital.

# 19. QUARTERLY CAUSAL EXTRACTION

The extracted data should enable:

```text
WHAT CHANGED?
→ VOLUME / PRICE / MIX / COST / CAPACITY / DEMAND
→ REVENUE
→ MARGIN
→ CFO / FCF
→ BALANCE SHEET
→ MANAGEMENT EXPLANATION
→ NEXT MONITORING METRIC
```

The extractor supplies evidence; the sector engine supplies interpretation.

# 20. SEASONALITY

Do not treat every QoQ change as structural.

Capture disclosures about:

- seasonality
- festive demand
- monsoon/crop cycle
- project timing
- maintenance shutdowns
- commodity cycles
- capacity commissioning
- regulatory timing
- financial-year seasonality

# 21. MISSING DATA

If the current report does not disclose a KPI:

```text
value = NULL
status = NOT_DISCLOSED
```

Do not copy last quarter or annual values as current.

# 22. SOURCE CONFLICT

When financial results and presentation differ:

1. Check period.
2. Check scope.
3. Check reported/adjusted basis.
4. Check definitions.
5. Check restatement/reclassification.
6. Prefer official financial-result totals.
7. Preserve both values and lineage.

# 23. DATA MODEL

```json
{
  "company": "...",
  "metric": "revenue_from_operations",
  "reported_label": "Revenue from operations",
  "value": 3200.5,
  "reported_value": "3,200.50",
  "currency": "INR",
  "unit": "crore",
  "period_type": "CURRENT_QUARTER",
  "period_start": "2026-04-01",
  "period_end": "2026-06-30",
  "report_scope": "CONSOLIDATED",
  "statement_type": "P&L",
  "section": "Consolidated Financial Results",
  "data_type": "REPORTED",
  "confidence": "HIGH",
  "source_document": "...",
  "source_page": 4,
  "source_locator": "...",
  "raw_text": "..."
}
```

Calculated values additionally store:

```text
formula
input_metric_ids
```

# 24. QUARTERLY VALIDATION

Validate where applicable:

```text
Revenue + Other Income ≈ Total Income
PBT - Tax ± applicable items ≈ PAT
Opening Cash + CFO + CFI + CFF + FX ≈ Closing Cash
Assets ≈ Equity + Liabilities
```

For segment totals, account for inter-segment eliminations.

# 25. RECENT-QUARTER RED-FLAG INPUTS

Make evidence available for detecting:

- revenue up but receivables much faster
- revenue up but volume down
- EBITDA up but CFO down
- PAT up but CFO negative
- margin expansion from other income
- exceptional gains
- debt increase without operating expansion
- inventory buildup
- channel destocking
- order-book growth without execution
- order cancellations
- capacity additions without utilization
- subscriber growth without ARPU
- traffic growth without revenue
- bookings without collections
- AUM growth with asset-quality deterioration
- NIM growth with credit-cost deterioration
- generation growth with tariff/fuel pressure
- production growth without realization
- IT growth with utilization deterioration
- FCF deterioration despite EBITDA growth

The extractor does not declare the final conclusion; it supplies the evidence.

# 26. OUTPUT CATEGORIES

```text
IDENTITY
PERIOD
P&L
BALANCE_SHEET
CASH_FLOW
WORKING_CAPITAL
CAPEX
DEBT
SEGMENTS
OPERATING_KPIs
GUIDANCE
MANAGEMENT_COMMENTARY
AUDITOR_REVIEW
RELATED_PARTIES
CONTINGENCIES
REGULATORY
```

# 27. WHAT THIS ENGINE MUST NEVER DO

- Mix Q1 and 6M.
- Mix Q4 and FY.
- Mix standalone and consolidated.
- Treat guidance as actual.
- Treat blank as zero.
- Ignore parentheses.
- Ignore units.
- Treat order book as revenue.
- Treat bookings as revenue.
- Treat capacity as production.
- Treat production as sales.
- Treat AUM as revenue.
- Treat subscribers as revenue.
- Treat generation as sales.
- Carry old KPIs into the current quarter.
- Remove exceptional items without retaining reported values.
- Overwrite source conflicts silently.

# 28. FINAL PROCESS

```text
LATEST REPORT
→ FIND RESULTS TABLE
→ IDENTIFY PERIOD COLUMNS
→ IDENTIFY SCOPE
→ EXTRACT P&L
→ EXTRACT BS
→ EXTRACT CF/YTD
→ EXTRACT SEGMENTS
→ SEARCH NOTES
→ SEARCH SECTOR KPI DICTIONARY
→ SEARCH GUIDANCE / MANAGEMENT
→ NORMALIZE
→ VALIDATE
→ STORE LINEAGE
→ PASS TO SECTOR ENGINE
```

The quarterly report is the **current-state evidence book**. The annual report is the **long-term evidence book**. The sector-specific engine is the **interpretation book**.
