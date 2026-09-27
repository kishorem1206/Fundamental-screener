# Healthcare → Healthcare — Fundamental Analysis Framework

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
> - **Macro Sector:** Healthcare
> - **Sector Value:** Healthcare
> - **Industries:** Healthcare Services; Pharmaceuticals & Biotechnology; Healthcare Equipment & Supplies

This is the standalone implementation framework for the **Healthcare → Healthcare** sector value. It covers all three industries in this classification and keeps healthcare-services, pharmaceutical/biotechnology, and equipment/supplies economics distinct.

## 1. Purpose and Scope

This framework covers the **Healthcare** sector and consolidates analysis for:

- Healthcare Services
- Pharmaceuticals & Biotechnology
- Healthcare Equipment & Supplies

Healthcare businesses require a combination of financial, operating, regulatory, product, clinical and competitive analysis.

Core architecture:

**RAW DATA → NORMALIZATION → BUSINESS MODEL → OPERATING METRICS → FINANCIALS → PRODUCT/PIPELINE → REGULATORY → PEER → CAUSAL ANALYSIS → RED FLAGS → SCORING → VALUATION → INVESTMENT THESIS**

The primary objective is to distinguish:

- Sustainable healthcare demand
- Volume vs price growth
- Product mix
- Capacity-led growth
- New-product growth
- Patent/exclusivity effects
- Regulatory-driven effects
- Temporary margin benefits
- Sustainable cash generation

---

# 2. Business-Model Classification

## 2.1 Healthcare Services

Classify:

- Hospitals
- Diagnostic chains
- Pathology
- Radiology
- Clinics
- Specialty healthcare
- Healthcare delivery platforms
- Contract healthcare services

Track:

- Beds
- Occupancy
- ARPOB
- Patient volumes
- Revenue mix
- Payor mix
- Case mix
- Average length of stay
- New facilities
- Asset turns
- ROCE

---

## 2.2 Pharmaceuticals

Classify:

- Generics
- Branded generics
- Specialty pharma
- Complex generics
- API
- CDMO/CRAMS
- Biosimilars
- Vaccines
- Contract manufacturing
- Domestic formulations
- Export formulations

Track:

- Revenue by geography
- Product mix
- Volume
- Realization
- Gross margin
- R&D
- ANDA/approval pipeline where applicable
- Product concentration
- Regulatory exposure
- US/EU exposure
- Pricing pressure

---

## 2.3 Biotechnology

Track:

- R&D spend
- Pipeline
- Clinical stages
- Trial milestones
- Probability-adjusted pipeline
- Licensing
- Partnerships
- Cash burn
- Cash runway
- Commercial products
- Regulatory milestones

For biotech, reported historical earnings may be less informative than:

**Pipeline → Probability of Success → Addressable Market → Commercialization → Cash Flow**

---

## 2.4 Healthcare Equipment & Supplies

Classify:

- Medical devices
- Diagnostics equipment
- Consumables
- Implants
- Surgical equipment
- Hospital equipment
- Laboratory equipment

Track:

- Installed base
- New placements
- Consumables pull-through
- Utilization
- Revenue/device
- Service revenue
- Recurring revenue
- Gross margin
- Product mix
- Regulatory approvals

---

# 3. Common Financial Dataset

Collect annual, quarterly and TTM data.

## Market Data

- Market capitalization
- Enterprise value
- Share price
- Shares outstanding
- Promoter holding
- Promoter pledge
- Institutional ownership
- Dividend yield
- P/E
- EV/EBITDA
- P/B
- EV/Sales
- FCF yield
- Historical valuation

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
- R&D
- Other income
- Exceptional items
- Finance cost
- Depreciation
- Tax

Always separate:

**Core healthcare operating revenue → operating profit → other income → exceptional items → PAT**

---

# 4. Healthcare Services — Hospital Framework

## Capacity

Track:

- Total beds
- Operational beds
- Occupancy
- New beds
- Expansion pipeline
- ICU beds
- Specialty beds
- Bed utilization

## Revenue

Track:

- Revenue
- Revenue/bed
- Revenue/occupied bed
- ARPOB
- Patient volumes
- Inpatient volume
- Outpatient volume

## Case Mix

Track:

- Cardiology
- Oncology
- Orthopedics
- Neurology
- Gastroenterology
- General medicine
- Other specialties

Measure:

- Specialty revenue mix
- Specialty growth
- Specialty margins

## Payor Mix

Track:

- Cash
- Insurance
- Government
- Corporate
- Other

Analyze:

**Payor Mix → Realization → Margin → Cash Collection**

---

# 5. Hospital Operating Economics

Core chain:

**Beds → Occupancy → Patient Volume → ARPOB → Revenue → EBITDA Margin → CFO → Capex → ROCE**

Track:

- Occupancy
- ARPOB
- ALOS
- Revenue/bed
- EBITDA/bed
- ROCE
- New-bed ramp-up

Separate mature hospitals from recently commissioned facilities.

---

# 6. Hospital Expansion Analysis

For every new hospital:

- Land cost
- Construction cost
- Equipment cost
- Total capex
- Beds
- Commissioning date
- Ramp-up period
- Occupancy
- ARPOB
- EBITDA margin
- Expected ROCE

Track:

**Capex → Beds → Occupancy → ARPOB → EBITDA → CFO → ROCE**

Flag:

- Cost overruns
- Delayed commissioning
- Slow occupancy ramp
- Excessive leverage

---

# 7. Diagnostics Framework

Track:

- Test volumes
- Realization/test
- Revenue/test
- Labs
- Collection centers
- Geographic coverage
- B2C/B2B mix
- Specialized tests
- Preventive diagnostics
- Digital channels

Analyze:

**Tests → Realization → Revenue → Gross Margin → EBITDA → CFO**

Key metrics:

- Revenue/test
- Tests/center
- Revenue/center
- EBITDA/center

---

# 8. Pharma Revenue Decomposition

Decompose:

**Volume + Price + Product Mix + Geography + Currency + New Products + Acquisitions**

Track:

- Domestic growth
- US growth
- Europe growth
- Emerging-market growth
- API
- Formulations
- Specialty
- Contract manufacturing

Compare:

**Reported Growth vs Constant-Currency Growth**

---

# 9. Pharma Geography Analysis

Track revenue and profitability by:

- India
- US
- Europe
- Emerging markets
- Other regions

For US exposure track:

- Product approvals
- Launches
- Competition
- Price erosion
- Concentration
- Regulatory observations
- Channel/customer concentration

For India track:

- Prescription growth
- Chronic/acute mix
- Therapy areas
- New launches
- Price regulation
- Market share

---

# 10. Product & Portfolio Analysis

Track:

- Top products
- Product revenue
- Product growth
- Product margin
- Product concentration
- New launches
- Mature products
- Loss-of-exclusivity exposure
- Patent/exclusivity where relevant

Flag:

- Single-product dependence
- Rapid product decline
- Regulatory exposure
- Price erosion

---

# 11. R&D Framework

Track:

- R&D spend
- R&D/revenue
- R&D growth
- Pipeline size
- Clinical-stage assets
- Regulatory submissions
- Approvals
- Launches
- R&D productivity

For innovative pharma/biotech:

**R&D → Clinical Milestone → Approval → Launch → Revenue → FCF**

Do not treat R&D spend itself as value creation.

---

# 12. Biotechnology Pipeline

For each pipeline asset track:

- Molecule/product
- Indication
- Phase
- Addressable market
- Trial status
- Key endpoint
- Regulatory status
- Partner
- Milestone
- Expected launch
- Probability of success
- Commercial opportunity

Use probability-adjusted analysis where appropriate.

Clearly label assumptions as:

**ESTIMATED**

---

# 13. API / CDMO / CRAMS

Track:

- Capacity
- Utilization
- Customer concentration
- Molecules
- Commercialized molecules
- Development pipeline
- Revenue/order book
- Realization
- Gross margin
- EBITDA margin
- Capex
- ROCE

Analyze:

**Customer Projects → Commercialization → Capacity Utilization → Revenue → Margin → ROCE**

---

# 14. Healthcare Equipment & Devices

Track:

- Units sold
- ASP
- Installed base
- New installations
- Consumables
- Service contracts
- Recurring revenue
- Product mix
- Regulatory approvals

Important:

**Installed Base → Consumables/Service → Recurring Revenue**

A large installed base may create recurring economics where supported by evidence.

---

# 15. Medical Consumables

Track:

- Volume
- ASP
- Market share
- Hospital penetration
- Recurring demand
- Product mix
- Gross margin
- Capacity

Analyze:

**Procedure Volume → Consumable Usage → Revenue → Gross Margin → FCF**

---

# 16. Regulatory Analysis

Track relevant regulatory events:

- USFDA inspections
- Warning letters
- Import alerts
- Form 483 observations
- Product recalls
- GMP observations
- Clinical holds
- Approval delays
- Pricing controls
- Patent litigation
- Licensing issues

For India:

- CDSCO
- NPPA
- Government pricing controls
- Drug approvals

Regulatory information should be separately classified from financial data.

---

# 17. Pricing & Volume

For healthcare businesses calculate:

**Revenue Growth = Volume + Price + Mix + Currency + New Products + Acquisitions**

Separate:

- Price increases
- Product mix
- Therapy mix
- Geography mix
- Specialty mix

A pharma company growing revenue because of price/mix should not be treated identically to one growing through sustainable volume and new products.

---

# 18. Gross Margin Analysis

Track:

- Gross profit
- Gross margin
- Input costs
- API costs
- Raw materials
- Freight
- Product mix
- Geography mix

Analyze:

**Input Cost → Product Cost → Price/Mix → Gross Margin**

For hospitals also analyze:

- Doctor cost
- Consumables
- Employee cost
- Occupancy
- Specialty mix

---

# 19. Operating Margin

Track:

- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- Employee cost
- R&D
- SG&A
- Marketing
- Regulatory costs
- New facility costs

Separate:

- Mature-business margin
- New-facility margin
- Temporary launch costs
- R&D investment
- One-off regulatory expenses

---

# 20. Working Capital

Track:

- Receivable days
- Inventory days
- Payable days
- Cash conversion cycle
- Inventory
- Receivables
- Contract assets where applicable

Calculate:

**CCC = Receivable Days + Inventory Days − Payable Days**

Pharma:

- Distributor inventory
- Channel inventory
- Export receivables

Hospitals:

- Insurance receivables
- Government receivables
- Corporate receivables

Flag:

- Receivables growing faster than revenue
- Inventory buildup
- Weak CFO conversion

---

# 21. Cash Flow

Track:

- CFO
- EBITDA
- PAT
- CFO/PAT
- CFO/EBITDA
- Capex
- FCF
- FCF margin
- FCF/PAT

Separate:

- Sustainable operating cash
- Working-capital release
- Asset sales
- Exceptional receipts

For biotech, also track:

- Cash burn
- Cash runway
- Financing requirement

---

# 22. Balance Sheet

Track:

- Cash
- Investments
- Gross debt
- Net debt
- Net debt/EBITDA
- Debt/equity
- Interest coverage
- Goodwill
- Intangibles
- CWIP
- Contingent liabilities

For biotech:

- Cash
- Cash burn
- Runway
- Expected funding need

For hospitals:

- Project debt
- Lease liabilities
- Expansion capex

---

# 23. Capital Allocation

Track:

- Maintenance capex
- Growth capex
- R&D
- Acquisitions
- Licensing
- Dividends
- Buybacks
- Debt repayment

Evaluate:

**FCF → Reinvestment → Incremental Revenue/EBITDA → Incremental ROIC**

For acquisitions track:

- Purchase price
- Revenue acquired
- EBITDA
- Goodwill
- Synergy
- Integration
- ROIC

---

# 24. Return Ratios

Track:

- ROE
- ROCE
- ROIC
- ROA
- Asset turnover
- Incremental ROIC

For hospitals:

**EBIT / Capital Employed**

For pharma:

**EBIT / Invested Capital**

For asset-light healthcare:

Track incremental capital efficiency separately.

---

# 25. Competitive Advantage

Assess:

- Brand
- Product portfolio
- Distribution
- Physician relationships
- Hospital network
- Location
- Clinical reputation
- Regulatory approvals
- Manufacturing capability
- IP/patents
- R&D capability
- Cost position
- Installed base
- Recurring consumables

Evidence should come from:

- Market share
- Pricing
- Volume
- Margin
- Customer retention
- Product approvals
- Capacity utilization

---

# 26. Management & Concall Analysis

Extract:

- Demand outlook
- Volume guidance
- Pricing
- New launches
- Regulatory outlook
- R&D pipeline
- Capex
- Hospital occupancy
- ARPOB
- Margin guidance
- Acquisition strategy
- Product approvals
- Cash-flow expectations

Track:

**Guidance → Actual → Variance → Explanation**

Classify:

- MET
- EXCEEDED
- MISSED
- REVISED

Management statements must be labelled:

**MANAGEMENT-DISCLOSED**

---

# 27. Governance

Track:

- Promoter holding
- Promoter pledge
- Promoter transactions
- Related parties
- Auditor changes
- Auditor qualifications
- Regulatory actions
- Executive remuneration
- Subsidiary transactions
- Contingent liabilities

Healthcare-specific governance risks:

- Regulatory violations
- Product-quality issues
- Clinical disclosure concerns
- Aggressive accounting
- Unusual licensing arrangements

---

# 28. Peer Comparison

## Hospitals

Compare:

- Occupancy
- ARPOB
- Revenue/bed
- EBITDA margin
- ROCE
- Bed additions
- Ramp-up

## Pharma

Compare:

- Revenue growth
- Domestic growth
- US growth
- EBITDA margin
- R&D/revenue
- Product concentration
- ROCE
- FCF

## Biotech

Compare:

- Pipeline
- R&D intensity
- Cash burn
- Cash runway
- Partnerships
- Milestones

## Diagnostics

Compare:

- Tests
- Revenue/test
- Network
- Margin
- ROCE

## Devices

Compare:

- Installed base
- Recurring revenue
- ASP
- Gross margin
- Market share
- ROIC

---

# 29. Valuation Framework

## Hospitals

Use:

- P/E
- EV/EBITDA
- EV/bed
- EV/revenue
- DCF
- FCF yield

Consider mature vs new-bed economics.

## Pharma

Use:

- P/E
- EV/EBITDA
- EV/Sales
- FCF yield
- DCF

Adjust for:

- Growth
- Pipeline
- Regulatory risk
- Product concentration

## Biotech

Use:

- Risk-adjusted NPV
- Pipeline valuation
- Cash-adjusted valuation
- DCF where commercial visibility exists

## Diagnostics

Use:

- P/E
- EV/EBITDA
- EV/revenue
- DCF

## Devices

Use:

- P/E
- EV/EBITDA
- EV/Sales
- DCF
- FCF yield

Do not apply one valuation multiple to all healthcare business models.

---

# 30. Historical Valuation

Track:

- P/E percentile
- EV/EBITDA percentile
- EV/Sales percentile
- FCF yield
- Historical median
- Peer median

Compare with:

1. Own history
2. Peer valuation
3. Growth
4. ROIC
5. Margin
6. Pipeline quality
7. Regulatory risk
8. Cash generation

No universal valuation threshold should be hard-coded.

---

# 31. Normalized Earnings

Adjust for:

- Temporary input-cost changes
- One-off regulatory costs
- Launch costs
- New-hospital ramp-up
- Exceptional gains/losses
- Acquisition effects
- Temporary product pricing

Calculate:

- Normalized EBITDA
- Normalized EBIT
- Normalized PAT
- Normalized CFO
- Normalized FCF

Clearly label all normalized values:

**ESTIMATED**

---

# 32. Scenario Analysis

## Hospitals

Variables:

- Occupancy
- ARPOB
- Beds
- EBITDA margin
- Capex
- Ramp-up

## Pharma

Variables:

- Volume
- Price erosion
- New launches
- Regulatory events
- Gross margin
- R&D

## Biotech

Variables:

- Clinical success
- Approval
- Launch timing
- Market size
- Commercial uptake
- Cash burn

## Diagnostics

Variables:

- Test volume
- Realization
- Network expansion
- Margin

Calculate impact on:

- Revenue
- EBITDA
- PAT
- CFO
- FCF
- ROIC
- Valuation

---

# 33. Causal Analysis

## Hospital

**Beds → Occupancy → Patient Volume → ARPOB → Revenue → EBITDA → CFO → Capex → ROCE**

## Pharma

**Disease/Category Demand → Volume → Price/Mix → Revenue → Gross Margin → EBITDA → R&D → CFO → FCF → ROIC**

## Biotech

**R&D → Clinical Milestone → Approval → Launch → Market Penetration → Revenue → FCF**

## Diagnostics

**Tests → Realization/Test → Revenue → Gross Margin → EBITDA → CFO → FCF**

## Medical Devices

**Installed Base → New Placements → Utilization → Consumables/Service → Recurring Revenue → Margin → FCF**

---

# 34. Red-Flag Engine

## Pharma

- Regulatory observations
- Product recalls
- Price erosion
- Product concentration
- Weak R&D productivity
- Inventory buildup
- Receivables deterioration

## Hospitals

- Falling occupancy
- Falling ARPOB
- Weak new-bed ramp
- High project debt
- Capex overruns
- Declining ROCE

## Biotech

- High cash burn
- Short runway
- Clinical failure
- Approval delays
- Excessive dilution
- Dependence on one asset

## Diagnostics

- Falling test volumes
- Falling realization
- Market-share loss
- Aggressive acquisitions
- Weak cash conversion

## Devices

- Customer concentration
- Regulatory problems
- Product recalls
- Weak installed-base economics
- High inventory

## Governance

- Promoter pledge
- Related-party concerns
- Auditor qualifications
- Regulatory actions
- Frequent dilution
- Unexplained exceptional items

---

# 35. Positive-Signal Engine

Look for:

- Sustainable volume growth
- Market-share gains
- Strong brands
- Pricing power
- High occupancy
- Rising ARPOB
- Successful product launches
- Strong pipeline
- Regulatory execution
- High R&D productivity
- Recurring revenue
- High ROIC
- Strong CFO conversion
- Low leverage
- Disciplined capex
- Successful acquisitions

Every positive signal should be supported by evidence.

---

# 36. Scoring Architecture

Suggested base weighting:

| Dimension | Weight |
|---|---:|
| Business / Clinical Quality | 10% |
| Growth Quality | 15% |
| Product / Pipeline / Capacity | 10% |
| Competitive Advantage | 10% |
| Operating Quality | 10% |
| Cash Flow Quality | 15% |
| Balance Sheet | 10% |
| ROIC / Capital Efficiency | 5% |
| Management & Governance | 10% |
| Valuation | 5% |

Adjust by sub-industry.

Hospitals:

- Occupancy
- ARPOB
- Bed economics
- ROCE

Pharma:

- Product growth
- Regulatory quality
- R&D/pipeline
- Geography

Biotech:

- Pipeline
- Clinical milestones
- Cash runway

Diagnostics:

- Test volume
- Realization
- Network productivity

Devices:

- Installed base
- Recurring revenue
- Product economics

---

# 37. Data Quality Framework

Every metric must carry:

- metric_name
- value
- period
- unit
- source
- source_date
- data_type
- confidence

Allowed:

- REPORTED
- CALCULATED
- ESTIMATED
- MANAGEMENT-DISCLOSED
- THIRD-PARTY

Confidence:

- HIGH
- MEDIUM
- LOW

Never manufacture:

- Market share
- Clinical success probability
- Pipeline value
- Regulatory outcome
- Hospital occupancy
- Product economics

---

# 38. Source Hierarchy

Preferred:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings Call Transcript
5. NSE/BSE filings
6. Company investor relations
7. CDSCO / NPPA
8. USFDA / relevant foreign regulators
9. Clinical-trial/regulatory disclosures
10. Reliable financial databases
11. Third-party research

Regulatory and clinical information should retain its original source.

---

# 39. Agent Architecture

```text
Company Identification Agent
        ↓
Healthcare Business Classification Agent
        ↓
Sub-Industry Agent
        ↓
Financial Data Agent
        ↓
Healthcare Operating Metrics Agent
        ↓
Hospital / Pharma / Biotech / Diagnostics / Devices Agent
        ↓
Product & Pipeline Agent
        ↓
Regulatory Agent
        ↓
Market Share / Competitive Agent
        ↓
R&D Agent
        ↓
Capacity / Utilization Agent
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
Normalization Agent
        ↓
Valuation Agent
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

# 40. Database Structure

## Company

- company_id
- company_name
- sector
- industry
- sub_industry
- business_model
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

## Healthcare Operating Metric

- company_id
- metric_name
- value
- period
- unit
- segment
- geography
- category
- source
- confidence

## Hospital

- company_id
- beds
- occupancy
- ARPOB
- patient_volume
- ALOS
- specialty_mix
- payor_mix
- period
- source

## Product

- company_id
- product
- category
- geography
- revenue
- growth
- margin
- market_share
- regulatory_status
- source

## Pipeline

- company_id
- asset
- indication
- phase
- milestone
- regulatory_status
- addressable_market
- expected_launch
- probability
- source
- confidence

## Regulatory Event

- company_id
- regulator
- event_type
- date
- severity
- status
- impact
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
- method
- metric
- normalized_value
- multiple
- current_value
- historical_median
- peer_median
- percentile
- confidence

---

# 41. Final Screener Output

## 1. Company Snapshot

- Business model
- Healthcare sub-industry
- Market cap
- Revenue
- EBITDA
- PAT
- ROIC
- Net debt
- FCF

## 2. Business Quality

- Category
- Competitive position
- Brand/IP
- Distribution
- Clinical/product capability

## 3. Growth Quality

- Volume
- Price
- Mix
- Market share
- New products
- Capacity

## 4. Operating Quality

- Utilization
- Gross margin
- EBITDA margin
- EBIT margin
- Unit economics

## 5. Product / Pipeline

- Product portfolio
- Pipeline
- Regulatory status
- Launches
- Concentration

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

## 9. Management

- Guidance
- Capital allocation
- Acquisitions
- Concall observations
- Governance

## 10. Regulatory Risk

- Regulatory events
- Severity
- Current status
- Potential financial impact

## 11. Valuation

- P/E
- EV/EBITDA
- EV/Sales
- FCF yield
- Historical valuation
- Peer valuation
- Normalized valuation

## 12. Causal Analysis

Explain the business-specific chain from demand/product/capacity through earnings and cash flow.

## 13. Red Flags

For each:

- Issue
- Severity
- Evidence
- Source
- Potential impact

## 14. Positive Signals

Evidence-backed strengths.

## 15. Investment Thesis

Produce:

- Business thesis
- Growth thesis
- Product/pipeline thesis
- Competitive-advantage thesis
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

# 42. Implementation Principles

1. Classify the healthcare business before applying ratios.
2. Separate healthcare services, pharma, biotech and devices.
3. Separate volume from price and mix.
4. Track product/category/geography contribution.
5. Track regulatory and clinical events separately from financial data.
6. For hospitals prioritize beds, occupancy, ARPOB, case mix and ROCE.
7. For pharma prioritize products, geography, regulatory exposure, R&D and cash flow.
8. For biotech prioritize pipeline, milestones, probability-adjusted economics and cash runway.
9. For diagnostics prioritize test volume, realization and network productivity.
10. For devices prioritize installed base, placements and recurring consumables/service.
11. Separate core operating earnings from other income.
12. Normalize temporary margin and launch effects.
13. Analyze working capital and CFO conversion.
14. Evaluate capex against incremental returns.
15. Compare valuation with own history, peers and normalized earnings.
16. Do not hard-code universal valuation thresholds.
17. Clearly label reported, calculated, estimated, management-disclosed and third-party data.
18. Preserve source provenance for every material metric.
19. Do not manufacture missing clinical, regulatory, market-share or operating data.
20. Make the final thesis traceable to underlying evidence and cash generation.

---

# 43. Sector-Level Fundamental Question

> **Does this healthcare company possess durable demand, competitive products/services, strong operating economics, regulatory and clinical execution, sustainable cash generation and high returns on capital, while its current valuation is supported by normalized long-term earnings power?**

The engine should distinguish **volume-led growth from price-led growth, temporary regulatory or margin benefits from structural economics, pipeline potential from realized commercial value, and accounting earnings from sustainable cash generation**.
