# Fundamental Screener — Annual Report Fetching & Extraction Engine
## Master Document-Parsing Book for All Sector-Specific Analysis Engines


# 1. PURPOSE AND ARCHITECTURE

This is the **upstream document-extraction book** for the Fundamental Screener. It is not the sector-analysis engine. The sector engines must first use this document to decide **where to look, what to extract, how to normalize it, and how to preserve evidence**.

```text
REPORT
→ DOCUMENT CLASSIFICATION
→ SECTION / NOTE LOCATOR
→ PERIOD + SCOPE IDENTIFICATION
→ TABLE EXTRACTION
→ ACCOUNTING NORMALIZATION
→ VALIDATION
→ SOURCE LINEAGE
→ COMMON DATA LAYER
→ SECTOR ENGINE
→ CAUSAL ANALYSIS
```

Core rule: **fetch first, interpret second**.

Never invent an unavailable value. Use `NOT_DISCLOSED`, `NOT_APPLICABLE`, `NOT_MATERIAL`, or `NULL` as appropriate.

# 2. REPORT SECTION MAP

Highest-priority annual-report locations:

- Corporate Information
- Financial Highlights
- Chairman/CEO/MD Message
- Management Discussion & Analysis (MD&A)
- Board/Directors' Report
- Corporate Governance Report
- Business Responsibility / BRSR / ESG
- Independent Auditor's Report
- Standalone Balance Sheet
- Standalone Statement of Profit and Loss
- Standalone Cash Flow Statement
- Standalone Statement of Changes in Equity
- Notes to Standalone Financial Statements
- Consolidated Auditor's Report
- Consolidated Balance Sheet
- Consolidated Statement of Profit and Loss
- Consolidated Cash Flow Statement
- Consolidated Statement of Changes in Equity
- Notes to Consolidated Financial Statements

Important aliases:

```text
Profit and Loss / Statement of Profit and Loss / Income Statement
Balance Sheet / Statement of Assets and Liabilities / Statement of Financial Position
Cash Flow / Statement of Cash Flows
Notes / Notes to Financial Statements
Directors' Report / Board's Report
Management Discussion and Analysis / MD&A
Consolidated Financial Statements / Group Financial Statements
Standalone Financial Statements / Company Financial Statements
```

Do not rely on fixed page numbers. Use the table of contents and headings to locate sections.

# 3. PERIOD CONTROL

Every value must carry:

```text
period_start
period_end
period_label
period_type
duration
```

Distinguish:

- Flow: revenue, EBITDA, PAT, CFO, capex, production, sales.
- Stock: cash, debt, inventory, receivables, PPE, equity, order book, capacity.

Annual examples:

```text
FY2026
Year ended 31-Mar-2026
01-Apr-2025 to 31-Mar-2026
As at 31-Mar-2026
```

Never mix a year-end stock number with a full-year flow without a valid calculation.

# 4. STANDALONE VS CONSOLIDATED

Every financial record MUST contain:

```text
report_scope = STANDALONE | CONSOLIDATED
```

Extract both whenever available.

Never combine:

```text
Standalone Revenue + Consolidated EBITDA
```

The sector engine decides which scope is appropriate.

For consolidated statements, also preserve:

- parent
- subsidiaries
- associates
- joint ventures
- non-controlling interests
- ownership percentages where disclosed

# 5. SIGN, BLANK AND PRESENTATION NORMALIZATION

Parentheses mean negative values:

```text
(250) → -250
Profit/(Loss) (120) → -120
```

Recognize `₹`, `Rs.`, `INR`, commas, decimals and OCR variants.

Do NOT convert:

- blank
- `-`
- `—`
- `N/A`

to zero.

Use:

```text
Nil → 0 when explicitly numeric
0 → 0
blank → NOT_DISCLOSED
N/A → NOT_APPLICABLE
- / — → NOT_DISCLOSED or NOT_APPLICABLE based on context
```

Preserve:

```text
raw_value
normalized_value
```

# 6. UNITS AND CURRENCY

Reports may use:

- INR / ₹ / Rs.
- lakh
- crore
- million
- billion
- USD/EUR/other currencies
- tonnes/MT
- million tonnes
- MW/GW
- GWh/TWh
- units/million units
- barrels/litres
- subscribers/customers
- km

Store:

```text
reported_value
reported_unit
normalized_value
normalized_unit
conversion_factor
currency
```

Never silently convert foreign currency into INR.

# 7. COMPARATIVE COLUMNS

Before assigning any table value, identify:

- current year
- previous year
- current period
- comparative period
- as-at date
- unit
- scope

Possible labels:

```text
CURRENT
PREVIOUS
RESTATED
REGROUPED
RECLASSIFIED
RECAST
```

If the report says prior-year figures were regrouped/reclassified/restated, preserve that status.

# 8. MASTER P&L EXTRACTION

Search the Statement of Profit and Loss and related notes for:

### Revenue
- Revenue from operations
- Sales
- Revenue from contracts with customers
- Sale of products
- Sale of services
- Other operating revenue
- Gross revenue

### Costs
- Materials consumed
- Purchases
- Inventory changes
- Employee benefits
- Power and fuel
- Manufacturing
- Freight
- Subcontracting
- Selling/distribution
- Advertising
- Other operating expenses
- Finance costs
- Depreciation
- Amortization

### Profit
- EBITDA if reported
- Operating profit
- EBIT if reported
- PBT
- Exceptional items
- Tax
- PAT
- Profit attributable to owners
- Non-controlling interest
- OCI
- Total comprehensive income
- Basic EPS
- Diluted EPS

Always keep **operating revenue** and **other income** separate.

# 9. OTHER INCOME AND EXCEPTIONAL ITEMS

Search notes for:

- Interest income
- Dividend income
- Investment gains/losses
- Fair-value changes
- FX gains/losses
- Rental income
- Government grants
- Asset-sale gains
- Insurance proceeds
- Exceptional items
- Impairment
- Restructuring
- Business disposal
- Litigation settlements
- One-time tax items

Store exceptional items separately. Do not silently normalize reported PAT.

# 10. TAX AND EPS

Extract:

- current tax
- deferred tax
- tax expense
- effective tax rate if disclosed
- tax reconciliation
- deferred tax assets/liabilities
- tax disputes
- basic EPS
- diluted EPS
- weighted average shares
- face value
- share capital
- bonus/split/rights/ESOP effects

Check capital changes before comparing EPS.

# 11. BALANCE SHEET EXTRACTION

### Non-current assets
- PPE
- ROU assets
- CWIP
- investment property
- goodwill
- intangibles
- investments
- loans
- other financial assets
- deferred tax assets
- other non-current assets

### Current assets
- inventory
- trade receivables
- contract assets
- cash and cash equivalents
- bank balances
- current investments
- loans
- other financial assets
- other current assets

### Equity
- share capital
- securities premium
- retained earnings
- other reserves
- OCI
- treasury shares
- non-controlling interest

### Liabilities
- long-term borrowings
- current borrowings
- lease liabilities
- trade payables
- contract liabilities
- provisions
- tax liabilities
- other financial liabilities
- other current/non-current liabilities

Mandatory validation:

```text
Assets ≈ Equity + Liabilities
```

Flag parsing/reconciliation failures instead of silently correcting them.

# 12. CASH FLOW EXTRACTION

Search the Cash Flow Statement and notes.

### CFO
- PBT
- depreciation/amortization
- finance costs
- interest/dividend
- inventory changes
- receivable changes
- payable changes
- other working-capital movements
- taxes paid
- net CFO

### CFI
- PPE purchases
- intangible purchases
- capex
- investments
- acquisitions
- asset sales
- loans given/recovered
- investment income

### CFF
- debt raised
- debt repaid
- lease payments
- equity issue
- buyback
- dividends
- financing costs

Also extract opening cash, closing cash and FX effects.

# 13. CAPEX, WORKING CAPITAL AND DEBT

CAPEX can be hidden in:

1. Cash flow
2. PPE note
3. CWIP note
4. Intangible note
5. MD&A
6. Commitments
7. Project disclosures

Extract:

- maintenance capex
- growth/expansion capex
- actual capex
- planned capex
- capacity additions
- project cost
- CWIP
- capital commitments

Do not label all PPE additions as maintenance capex.

Working capital:

- inventory
- receivables
- payables
- contract assets/liabilities
- advances
- other current assets/liabilities
- ageing

Debt:

- gross debt
- current/non-current debt
- term loans
- bonds/debentures
- commercial paper
- working-capital borrowings
- secured/unsecured
- lease liabilities
- interest rate
- maturity
- currency
- security
- covenants
- refinancing

# 14. NOTES TO ACCOUNTS

The notes are a primary extraction source, not an optional appendix.

Search:

- Revenue
- Segment reporting
- PPE/CWIP
- Intangibles
- Goodwill
- Borrowings
- Leases
- Inventory
- Receivables
- Payables
- Provisions
- Tax
- Investments
- Subsidiaries
- Associates
- JVs
- Related parties
- Contingent liabilities
- Commitments
- Business combinations
- Impairment
- Fair values
- Derivatives
- FX
- Employee benefits
- Share-based payments
- Government grants
- Regulatory balances
- Accounting judgements/policies

# 15. REVENUE AND SEGMENT NOTES

Revenue note:

- product/service revenue
- geography
- domestic/export
- customer type
- point-in-time/over-time
- contract assets
- contract liabilities
- customer advances
- remaining performance obligations where disclosed

Segment note:

- reported segment name
- normalized segment name
- revenue
- external revenue
- inter-segment revenue
- segment result/EBIT
- margin if disclosed
- assets
- liabilities
- capex
- depreciation
- geography

Never merge two reported segments merely because their names appear similar.

# 16. SUBSIDIARIES, ASSOCIATES, JVs

Extract:

- entity
- relationship
- ownership %
- country
- business
- revenue
- profit/loss
- net worth
- assets
- liabilities
- debt
- acquisition/disposal date
- contribution to consolidated earnings
- NCI

This is critical for the Diversified engine and for consolidated-quality analysis.

# 17. CONTINGENCIES AND COMMITMENTS

Search:

- contingent liabilities
- litigation
- tax disputes
- guarantees
- performance guarantees
- bank guarantees
- letters of credit
- capital commitments
- purchase commitments
- environmental/decommissioning obligations

Keep these separate from debt. Do not automatically add contingent liabilities to net debt.

# 18. RELATED PARTIES

Extract:

- promoter/group entity
- KMP
- subsidiaries/associates/JVs
- transaction type
- sales/purchases
- loans/advances
- guarantees
- rent
- management fees
- interest
- outstanding receivable/payable
- terms/security

Flag for downstream investigation; do not automatically call a transaction improper.

# 19. PROMOTER / OWNERSHIP / GOVERNANCE

Search:

- promoter/promoter group
- public holding
- institutional ownership
- pledged/encumbered shares
- board composition
- director changes
- KMP
- remuneration
- auditor changes
- audit qualifications
- internal-control observations
- related parties
- capital allocation
- acquisitions
- divestments
- buybacks
- dividends
- debt reduction

Annual-report ownership is historical to the report date. Current promoter/pledge data should be separately sourced from current exchange filings.

# 20. AUDITOR AND ACCOUNTING-POLICY EXTRACTION

Auditor:

- opinion
- qualification
- adverse/disclaimer
- emphasis of matter
- key audit matters
- going-concern references
- internal financial controls
- significant judgements
- component-auditor issues

Accounting policies:

- revenue recognition
- inventory valuation
- depreciation/useful lives
- impairment
- leases
- financial instruments
- FX
- taxes
- provisions
- employee benefits
- grants
- borrowing costs
- business combinations

Do not convert audit language into an automated fraud/quality conclusion.

# 21. MANAGEMENT GUIDANCE

Search:

- outlook
- growth targets
- margin targets
- capex plans
- capacity plans
- volume targets
- order-book targets
- pricing expectations
- new-product targets
- debt reduction
- acquisition/divestment plans

Store:

```text
guidance_type
metric
target
period
speaker
statement
source
data_type = MANAGEMENT_DISCLOSED
```

Never store guidance as actual reported financial data.

# 22. UNIVERSAL OPERATING-KPI DICTIONARY

The sector engines already built for all 22 Sector Values can request these keys. The annual engine should search **MD&A + business review + segment notes + KPI pages + notes** before declaring a metric unavailable.

### Commodities — Metals & Mining
Production, sales/shipment volume, capacity, utilization, ore grade, recovery, resources/reserves, mine life, realization, commodity price, cost/tonne, EBITDA/tonne, cash cost, export/domestic mix, downstream output, smelting/refining, energy, freight, mine capex, exploration, environmental obligations.

### Commodities — Construction Materials
Cement/clinker/RMC/aggregate/pipe/tile/sanitaryware volume, installed capacity, utilization, realization, regional pricing, fuel, power, freight, raw materials, channel/dealers, market share, capacity additions.

### Commodities — Chemicals
Production, sales, realization, product mix, capacity, utilization, raw-material cost, energy, freight, export/domestic mix, customer concentration, specialty share, commodity exposure, registrations, new products, contract manufacturing, plant additions, R&D.

### Commodities — Fertilizers & Agrochemicals
Volume, product mix, realization, raw-material prices, subsidy, subsidy receivables, crop exposure, seasonality, monsoon sensitivity, channel/dealer inventory, exports, registrations, molecules, capacity, utilization, energy.

### Commodities — Forest Materials
Paper/paperboard/pulp/jute volume, realization, capacity, utilization, pulp/wood availability, waste-paper cost, energy, freight, exports, product mix, environmental costs.

### Consumer Discretionary — Realty
Launches, bookings/pre-sales, area sold/launched, realization/sq ft, collections, inventory, unsold stock, project progress, construction cost, land bank, development rights, JDA, project debt, customer advances, rental occupancy/income, pipeline.

### Consumer Discretionary — Textiles
Yarn/fabric/garment volume, production, ASP, utilization, capacity, cotton/fibre cost, energy, export/domestic demand, brand/store metrics, technical/home textile metrics, inventory, customer concentration.

### Consumer Discretionary — Consumer Services
Customers, active users, transactions/orders, GMV, revenue, take rate, commission, ARPU, churn, retention, store count, footfall, same-store growth, service-provider count, utilization, segment revenue/margin.

### Consumer Discretionary — Media, Entertainment & Publication
Subscribers, audience, engagement, advertising, subscription revenue, ARPU, content revenue/cost, content library/amortization, circulation, ad rates, screens, occupancy, ticket volumes, digital users, OTT metrics, content monetization.

### Consumer Discretionary — Automobile & Auto Components
Production, dispatches, wholesale/retail volume, model mix, ASP, market share, EV/ICE volume, exports, capacity, utilization, order book, content/vehicle, launches, commodity cost, warranty, R&D, customer concentration.

### Consumer Discretionary — Consumer Durables
Units, ASP, volume, premium mix, distribution, stores/dealers, e-commerce, channel inventory, raw-material cost, launches, market share, capacity, utilization, service network, warranty.

### Diversified — Diversified
Every material segment's revenue, EBIT/result, margin, assets, liabilities, capex, depreciation, growth, operating KPIs, subsidiary/JV/associate contribution, listed investments, corporate overhead, parent/subsidiary debt, guarantees, acquisitions and disposals.

### Energy — Oil, Gas & Consumable Fuels
Production, refinery throughput, GRM, crude intake, gas/LNG volume, pipeline utilization, retail fuel volume, marketing margin, realization, oil/gas price, inventory gains/losses, fuel cost, capex, reserves, capacity, regulation/subsidy.

### FMCG — Fast Moving Consumer Goods
Volume/value/price growth, mix, gross margin, premiumization, market share, rural/urban growth, general/modern trade, e-commerce/quick commerce, new products, advertising/brand spend, channel inventory, raw-material costs, contract manufacturing, capacity/utilization.

### Financial Services — Financial Services
**Banks:** deposits, advances, CASA, NIM, GNPA, NNPA, slippages, credit cost, provision coverage, CRAR, CET1, PPOP, cost/income, fee income, retail/wholesale mix, restructuring.  
**Insurance:** GWP, NBP, APE, VNB, VNB margin, persistency, claims/combined ratio, solvency, embedded value, AUM.  
**Capital Markets:** AUM, clients, trading volume, market share, brokerage, advisory/distribution.  
**NBFC:** AUM, disbursements, yield, cost of funds, spread, NIM, GNPA, NNPA, collection efficiency, credit cost, capital adequacy.  
**Fintech:** users, transactions, TPV/GMV, take rate, revenue, contribution margin, CAC, retention, AUM/origination.

### Healthcare — Healthcare
**Hospitals:** beds, occupancy, ARPOB, IPD/OPD, ALOS, payer/specialty mix, new beds, capex, revenue/bed.  
**Pharma:** geography, product sales, volume/price, launches, approvals, pipeline, R&D, API, capacity/utilization, regulatory observations.  
**Equipment:** installed base, units, ASP, consumables, service revenue, orders/order book, utilization, R&D, concentration.

### Industrials — Capital Goods
Order inflow, order book, book-to-bill, order-book/revenue, capacity, utilization, production, ASP, project execution, completion, cost overruns, cancellations, customer concentration, government/private mix, exports, R&D, equipment fleet, ROCE.

### Industrials — Construction
Order inflow/book, book-to-bill, project pipeline/execution, revenue/margin, fixed-price/cost-plus/EPC/turnkey mix, government/private mix, materials, subcontracting, labour, equipment utilization, retention, advances, claims, liquidated damages, guarantees, working capital.

### Information Technology — Information Technology
**IT Services:** revenue, constant-currency growth, volume, pricing, utilization, attrition, headcount, offshore/onsite mix, billing rates, large deals, TCV/bookings, order pipeline, top-client concentration, revenue/employee, AI/cloud/digital mix, margin.  
**Software:** ARR, subscription/recurring revenue, customers, net retention, churn, ACV, R&D.  
**Hardware:** units, ASP, production, capacity, utilization, inventory, component cost.

### Services — Services
Customers, transactions, revenue, pricing, utilization, capacity, market share, contracts, order book, project pipeline, customer concentration, government/export mix, employee count, revenue/employee, segment margin. Transport: passenger/freight volume, tonne-km, passenger-km, fleet, load factor, yield. Infrastructure: traffic, throughput, capacity, utilization, tariff.

### Telecommunication — Telecommunication
**Services:** subscribers, active subscribers, adds, churn, ARPU, data usage, traffic, revenue/GB, 4G/5G, broadband, enterprise revenue, network utilization, towers, fibre, spectrum, capex, leases, debt.  
**Equipment:** units, ASP, orders, order book, book-to-bill, production, capacity, utilization, concentration, R&D, exports, inventory, receivables.

### Utilities — Power
Installed capacity, generation, PLF, availability, utilization, CUF, renewable/thermal/hydro/nuclear capacity, transmission lines/substations, distribution customers, units sold, AT&C loss, tariff, PPA/merchant tariff, fuel consumption, heat rate, auxiliary consumption, fuel cost, regulatory assets, subsidy receivables, capex, commissioning, debt.

### Utilities — Other Utilities
**Water:** connections, water supplied/delivered/billed, volume, tariff, non-revenue water, network, collection efficiency, capex, regulatory receivables.  
**Gas distribution:** connections, volume, network length, utilization, tariff, realized margin, customer mix, capex.  
**Waste:** volume, collection, processing, treatment, disposal, service fee, recovery value, contract tenure, municipality/customer, capex, working capital.

# 23. DATA MODEL

Every extracted metric:

```json
{
  "company": "...",
  "metric": "revenue_from_operations",
  "reported_label": "Revenue from operations",
  "value": 12500.5,
  "reported_value": "12,500.50",
  "currency": "INR",
  "unit": "crore",
  "period": "FY2026",
  "period_end": "2026-03-31",
  "report_scope": "CONSOLIDATED",
  "statement_type": "P&L",
  "section": "Consolidated Statement of Profit and Loss",
  "note_number": "28",
  "page": 321,
  "data_type": "REPORTED",
  "confidence": "HIGH",
  "source_document": "...",
  "source_locator": "...",
  "raw_text": "..."
}
```

Calculated metrics additionally require:

```text
formula
input_metric_ids
```

# 24. CONFIDENCE

`HIGH`: clear table, heading, period, unit and scope.  
`MEDIUM`: OCR/table reconstruction or minor ambiguity.  
`LOW`: narrative inference, ambiguous unit/period or broken OCR.

Low-confidence values should not silently drive critical calculations.

# 25. TABLE VALIDATION

For each table:

1. Identify title.
2. Identify unit.
3. Identify period columns.
4. Identify scope.
5. Identify row labels.
6. Normalize signs.
7. Preserve footnotes.
8. Validate subtotals/totals where possible.
9. Preserve raw table text.

# 26. CROSS-STATEMENT VALIDATION

Where relevant, compare:

```text
PAT ↔ equity/retained earnings movement
Depreciation ↔ cash-flow adjustment
Capex ↔ PPE/CWIP movement
Debt raised/repaid ↔ debt movement
Dividend ↔ equity/cash flow
Closing cash ↔ balance sheet cash
```

Differences may arise from acquisitions, disposals, FX, fair-value movements, consolidation changes or non-cash transactions. Flag; do not silently "fix".

# 27. SOURCE CONFLICT RULE

If values differ:

1. Check period.
2. Check standalone/consolidated.
3. Check current/comparative column.
4. Check reported vs calculated.
5. Check restatement/reclassification.
6. Prefer the primary financial statement for accounting totals.
7. Preserve the alternative value and reason.

# 28. OUTPUT CATEGORIES

Expose the common data layer as:

```text
IDENTITY
OWNERSHIP
MANAGEMENT
GOVERNANCE
P&L
BALANCE_SHEET
CASH_FLOW
WORKING_CAPITAL
CAPEX
DEBT
TAX
SEGMENTS
SUBSIDIARIES
RELATED_PARTIES
CONTINGENT_LIABILITIES
ACCOUNTING_POLICIES
AUDITOR
OPERATING_KPIs
REGULATORY
GUIDANCE
ESG
```

# 29. WHAT THIS ENGINE MUST NEVER DO

- Invent values.
- Convert missing to zero.
- Mix standalone and consolidated.
- Mix periods.
- Ignore parentheses.
- Ignore units.
- Treat guidance as actual.
- Treat other income as operating revenue.
- Treat exceptional items as recurring.
- Treat capacity as production.
- Treat production as sales.
- Treat order book as revenue.
- Treat announced capex as actual capex.
- Treat contingent liabilities as debt.
- Carry an old KPI forward as current.
- Replace a primary filing with an aggregator without preserving provenance.

# 30. FINAL PROCESS

```text
WHERE IS THE INFORMATION?
→ WHICH SECTION?
→ WHICH TABLE / NOTE?
→ WHICH PERIOD?
→ WHICH SCOPE?
→ WHICH UNIT?
→ WHAT SIGN?
→ REPORTED OR CALCULATED?
→ VALIDATE
→ STORE RAW + NORMALIZED VALUE
→ STORE SOURCE LINEAGE
→ PASS TO SECTOR ENGINE
```

The annual report is the **long-term evidence book**. The sector-specific framework is the **interpretation book**.



# 31. ANNUAL-SPECIFIC SECTION PRIORITY

When the sector engine asks for a value, search in this order:

```text
1. Audited financial statement
2. Relevant note to that statement
3. Segment note
4. MD&A / business review
5. Board report
6. Corporate governance / BRSR
7. Other annual-report disclosures
```

For promoter/pledge/current ownership, the annual report is historical. Current exchange shareholding filings should be treated as a separate current source.

# 32. ANNUAL FINANCIAL-HISTORY EXTRACTION

Where the annual report presents multi-year highlights, extract:

- revenue
- EBITDA
- EBIT
- PAT
- EPS
- assets
- debt
- net worth
- CFO
- capex
- FCF where disclosed
- ROE/ROCE/ROIC where disclosed
- dividends

Store the period for every year rather than assuming a five-year table is aligned.

# 33. ANNUAL CAPITAL-ALLOCATION EXTRACTION

Search Board Report, MD&A, notes and financial statements for:

- maintenance capex
- expansion capex
- acquisitions
- investments
- divestments
- buybacks
- dividends
- debt repayment
- fund raising
- new businesses
- capacity expansion
- restructuring

For acquisitions extract purchase price, acquired revenue/profit if disclosed, goodwill, consideration, ownership and acquisition date.

# 34. ANNUAL RISK EXTRACTION

Search:

- Risk Management
- Principal Risks
- Internal Controls
- Legal proceedings
- Contingent liabilities
- Regulatory matters
- Environmental obligations
- Customer concentration
- Supplier concentration
- Currency risk
- Interest-rate risk
- Commodity risk
- Liquidity risk
- Cyber/technology risk
- Business continuity

Store evidence; do not automatically convert a disclosed risk into a quantified loss.

# 35. ANNUAL MANAGEMENT-GUIDANCE HISTORY

The annual engine should preserve prior management targets so the later quarterly engine can perform:

```text
GUIDANCE → ACTUAL → VARIANCE → EXPLANATION
```

Status:

```text
MET
EXCEEDED
MISSED
REVISED
NOT_COMPARABLE
```

# 36. ANNUAL COMPLETION CHECKLIST

- Correct company/year/report.
- Standalone P&L, BS, CF and equity.
- Consolidated P&L, BS, CF and equity.
- Notes searched.
- Revenue note searched.
- Segment note searched.
- Debt note searched.
- PPE/CWIP searched.
- Inventory/receivables/payables searched.
- Tax searched.
- Related parties searched.
- Contingencies/commitments searched.
- Subsidiaries/JVs/associates searched.
- Auditor report captured.
- Accounting policies captured.
- Promoter/governance evidence captured.
- MD&A/KPI dictionary searched.
- Management guidance captured.
- Missing values explicitly marked.
