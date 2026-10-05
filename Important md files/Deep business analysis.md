Exactly. After looking through the **full ITC Initiating Coverage report**, I think your idea should be bigger than a simple PDF extractor.

What you are describing is essentially a **Business Intelligence + Fundamental Research Engine** for every stock in your existing screener.

The ITC report gives us an excellent blueprint: it isn't merely collecting financial ratios. It reconstructs **how the business works, what drives it, what could change, how those drivers translate into financials, and what the business may be worth under different assumptions**. The report itself has 16 research chapters plus financial, valuation, terminology and source appendices. ITC_Initiation_Report

## The system I would build

Call the new module something like:

> **Business Intelligence Engine (BIE)**

Your existing screener remains the **quantitative screening layer**.

The new BIE becomes the **deep company-understanding layer**.

```text
                    EXISTING SCREENER
                          │
             ┌────────────┴────────────┐
             │                         │
       Quantitative Engine       Business Intelligence
             │                         │
       Ratios / Signals          PDF / Filings / Research
             │                         │
             └────────────┬────────────┘
                          ▼
                 COMPANY KNOWLEDGE
                          │
                          ▼
                  FUNDAMENTAL ENGINE
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         Score / Rank            Deep Report
                                      │
                                      ▼
                               PDF / Dashboard
```

---

# What the new system needs to extract

And yes — **we should preserve essentially everything in this ITC report**, not just the obvious financial metrics.

I would divide it into **18 major modules**.

---

## 1. Company Identity & Business Architecture

Extract:

- Company name
- NSE/BSE ticker
- ISIN
- Industry
- Sector
- Reporting currency
- Fiscal year
- Business segments
- Subsidiaries
- Associates
- Joint ventures
- Listed investments
- Ownership structure
- Demerged businesses
- Recently acquired businesses
- Pending acquisitions
- Proposed mergers
- Corporate restructuring
- Legal perimeter
- Standalone vs consolidated structure

This is important because the ITC report specifically distinguishes operating segments, investments and consolidated PAT rather than treating them as interchangeable. ITC_Initiation_Report

### Output

```json
{
  "company": "ITC Ltd",
  "segments": [
    "Cigarettes",
    "FMCG",
    "Agri",
    "Paper",
    "Technology"
  ],
  "subsidiaries": [],
  "associates": [],
  "recent_transactions": []
}
```

---

# 2. Business Model

This is the part I think your current screener is missing most.

Extract:

### What does the company actually do?

- Products
- Services
- Customers
- Customer types
- Distribution model
- Revenue streams
- Geography
- Domestic/export split
- B2B/B2C
- Recurring/non-recurring revenue
- Pricing model
- Volume drivers
- Capacity
- Utilization
- Distribution reach
- Brands
- Market position
- Competitive advantages
- Dependence on particular products/customers

For ITC, for example, the report separates cigarettes, FMCG-Others, Agri, Paper and Technology because their economics are fundamentally different. ITC_Initiation_Report

---

# 3. Segment Economics

For **every business segment**, create:

```text
Revenue
Revenue growth
PBIT
PBIT margin
EBITDA
EBITDA margin
Profit contribution
Asset intensity
Capital intensity
Working-capital intensity
Growth drivers
Margin drivers
Risks
Competitors
Capacity
Utilization
Management commentary
```

Then:

### Segment contribution

```text
Revenue contribution %
Profit contribution %
Capital contribution %
Growth contribution %
Cash-flow contribution %
```

This is how you discover things like:

> "One segment produces 20% of revenue but 70% of profit."

The ITC report explicitly demonstrates this distinction with cigarette PBIT. ITC_Initiation_Report

---

# 4. Industry & Competition Engine

For each company:

```text
Industry
Industry growth
Market size
Market growth
Market structure
Market share
Competitors
Competitive advantages
Competitive threats
Entry barriers
Substitution risk
Pricing power
Commodity exposure
Regulatory exposure
Technology disruption
Demand cyclicality
```

And automatically identify:

### Peer set

Not simply "same sector".

Instead:

```text
Business segment
      ↓
Comparable companies
      ↓
Peer quality filter
      ↓
Relevant peer set
```

The ITC report, for example, uses different competitors for cigarettes, FMCG, paper, agri and technology rather than applying one generic peer group. ITC_Initiation_Report

---

# 5. Business Drivers Engine

This should be one of the most important components.

For every business:

```text
Revenue =
Volume × Price

or

Revenue =
Customers × ARPU

or

Revenue =
Capacity × Utilization × Realization

or

Revenue =
AUM × Yield
```

depending on the sector.

The system should identify the appropriate **business-driver equation** automatically from the sector framework.

For ITC cigarettes, for example:

```text
Volume
×
Realization
×
Product Mix
-
Excise / Taxes
=
Economic Revenue
```

The report specifically separates cigarette ex-excise revenue from booked revenue because the tax structure makes headline revenue misleading. ITC_Initiation_Report

---

# 6. Management Commentary Extractor

This is where PDF extraction becomes really valuable.

Extract:

### Management says:

- Demand outlook
- Volume outlook
- Pricing outlook
- Margin outlook
- Industry outlook
- Capacity plans
- Capex plans
- Expansion plans
- New products
- New markets
- Acquisitions
- Cost reduction
- Distribution expansion
- Digital strategy
- Risks
- Opportunities

But **do not convert management commentary into fact**.

Store:

```text
statement
speaker
date
source
document
page
type = management_guidance
confidence
```

So:

> "Management expects X"

doesn't become:

> "X will happen."

This distinction is explicitly maintained in the ITC report between company-reported information and analyst assumptions. ITC_Initiation_Report

---

# 7. Historical Financial Engine

Not just current ratios.

Build:

```text
FY20
FY21
FY22
FY23
FY24
FY25
FY26
Q1 FY27
...
```

For every year/quarter:

### P&L

- Revenue
- EBITDA
- EBIT
- PBT
- PAT
- EPS
- Margins

### Balance Sheet

- Cash
- Debt
- Equity
- Assets
- Working capital
- Receivables
- Inventory
- Payables

### Cash Flow

- CFO
- Capex
- CFI
- CFF
- FCF

### Segment

- Revenue
- PBIT
- Margin

---

# 8. Normalization Engine

This is **critical**.

The system must detect:

```text
Demergers
Acquisitions
Discontinued operations
Exceptional items
One-time gains
Fair-value gains
Accounting changes
Tax changes
Subsidiary consolidation changes
Currency effects
```

Then create:

```text
Reported
Adjusted
Normalized
```

For example, the ITC report deliberately avoids extrapolating FY25 headline PAT because it included discontinued hotel operations and demerger-related effects. ITC_Initiation_Report

This should be automatic.

---

# 9. Financial Ratio Engine

Then calculate **all core ratios**.

### Growth

```text
Revenue CAGR
EBITDA CAGR
EBIT CAGR
PAT CAGR
EPS CAGR
CFO CAGR
FCF CAGR
```

### Profitability

```text
Gross Margin
EBITDA Margin
EBIT Margin
PAT Margin
ROE
ROCE
ROA
ROIC
```

### Balance Sheet

```text
Debt/Equity
Net Debt/EBITDA
Interest Coverage
Current Ratio
Working Capital Days
Receivable Days
Inventory Days
Payable Days
```

### Cash

```text
CFO/PAT
FCF/PAT
FCF Margin
Capex/Revenue
Dividend Coverage
Cash Conversion
```

---

# 10. Sector-Specific Metric Engine

This is where your existing **sector framework work** becomes extremely useful.

For example:

### Banking

```text
NIM
CASA
GNPA
NNPA
PCR
Slippage
Credit Cost
ROA
ROE
CRAR
LDR
Cost/Income
```

### IT

```text
Revenue growth
Constant-currency growth
Deal wins
Book-to-bill
Attrition
Utilization
Revenue/employee
EBIT margin
Client concentration
DSO
FCF conversion
```

### FMCG

```text
Volume growth
Price growth
Distribution reach
Market share
Gross margin
EBITDA margin
Ad spend
Working capital
```

### Manufacturing

```text
Capacity
Utilization
Realization
Volume
Raw material cost
EBITDA/ton
ROCE
Capex
Order book
```

And so on.

---

# 11. Forecasting Engine

Now we reach the part you specifically mentioned:

> **Calculation methods and predictions**

This should NOT simply ask GPT:

> "Predict ITC revenue."

Instead:

```text
Historical data
      +
Business drivers
      +
Industry data
      +
Management commentary
      +
Capacity
      +
Macro assumptions
      ↓
Forecast engine
```

For example:

```text
Revenue FY27

= Volume growth
× Price realization
× Product mix
```

Then:

```text
EBITDA

= Revenue × expected EBITDA margin
```

Then:

```text
PAT

= PBT - tax
```

Then:

```text
CFO

= PAT
+ non-cash items
- working-capital investment
```

The ITC model follows this type of segmented approach and forecasts FY27–FY31 rather than simply extending one historical CAGR. ITC_Initiation_Report

---

# 12. Prediction Engine

I'd create **three scenarios automatically**:

### Bear

```text
Lower volume
Lower realization
Lower margins
Higher working capital
Higher capex
Higher cost
Lower valuation multiple
```

### Base

Most reasonable assumptions.

### Bull

```text
Higher volume
Better realization
Operating leverage
Better margins
Better cash conversion
Higher valuation multiple
```

And importantly:

**Don't produce one "predicted price".**

Produce:

```text
Bear      ₹216
Base      ₹255
Bull      ₹291
```

The ITC report uses precisely this Base/Bull/Bear architecture and changes the operating forecasts and valuation methods when the scenario changes. ITC_Initiation_Report

---

# 13. Valuation Engine

This should support multiple methods.

### DCF

```text
Revenue
→ EBITDA
→ EBIT
→ NOPAT
→ CFO
→ Capex
→ Working Capital
→ FCFF
→ Discount
→ Terminal Value
→ Enterprise Value
→ Equity Value
→ Value/Share
```

The ITC report uses FCFF, WACC and terminal growth and explicitly treats terminal value as a major uncertainty. ITC_Initiation_Report

### SOTP

```text
Segment 1 × Multiple
+
Segment 2 × Multiple
+
Segment 3 × Multiple
+
Investments
+
Cash
-
Debt
=
Equity Value
```

ITC's report uses segment-specific PBIT multiples rather than treating the entire company with one multiple. ITC_Initiation_Report

### Relative valuation

```text
Peer P/E
Peer EV/EBITDA
Peer P/B
Peer PEG
Sector multiples
```

### Optional

```text
EV/Sales
Dividend Discount
Residual Income
NAV
Replacement Cost
```

depending on sector.

---

# 14. Sensitivity Engine

Automatically test:

```text
Revenue growth ± X%
Margin ± X%
WACC ± X%
Terminal growth ± X%
Multiple ± X%
Volume ± X%
Realization ± X%
Commodity price ± X%
```

Then generate:

### DCF matrix

```text
             WACC
          10% 11% 12% 13% 14%
g 2.5%
g 3.0%
g 3.5%
g 4.0%
g 4.5%
```

The ITC report does exactly this for WACC and terminal growth. ITC_Initiation_Report

---

# 15. Risk Engine

Extract and classify:

### Business risk
### Financial risk
### Regulatory risk
### Governance risk
### Accounting risk
### Commodity risk
### Customer concentration
### Supplier concentration
### Technology risk
### ESG risk
### Litigation
### Promoter/ownership risk
### Capital allocation risk

The ITC report explicitly separates regulatory/public-health, demand/cost/margin, accounting/model-construction, and governance/capital-allocation risks. ITC_Initiation_Report

---

# 16. "What Could Change the Thesis?"

This is a fantastic feature to automate.

Instead of merely:

> BUY / HOLD / SELL

generate:

### Bullish triggers

```text
Revenue growth > X%
Margin > X%
Debt falls below X
Market share increases
Capacity utilization > X%
```

### Bearish triggers

```text
Volume declines
Margin compression
Debt increases
Working capital deteriorates
Regulation changes
Management guidance reduced
```

This becomes your **monitoring engine**.

The ITC report's final monitoring section specifically identifies future cigarette PBIT, price/product mix, excise, FMCG growth/cash conversion, Century integration, ITC Infotech/Happiest Minds milestones, ITC Hotels stake and treasury/capex as things to monitor. ITC_Initiation_Report

---

# 17. Source & Evidence Engine

This is **non-negotiable**.

Every extracted number should have:

```text
company
metric
value
period
document
document_date
page
source_url
source_type
extraction_method
confidence
```

Example:

```json
{
  "metric": "FY26 Revenue",
  "value": 81640,
  "unit": "INR_CRORE",
  "period": "FY2026",
  "source_type": "AUDITED_FILING",
  "document": "ITC FY26 Results",
  "page": 42,
  "source_url": "...",
  "confidence": 0.99
}
```

The report's own methodology is very clear about this: actual financial figures come from dated primary filings/company releases, while market/peer observations retain exact as-of dates in `Source Register` and `Peer_Snapshot`. ITC_Initiation_Report

---

# 18. Editorial Report Generator

Finally, the system takes all of this and generates:

```text
                    COMPANY REPORT

1. Executive Summary
2. Business Architecture
3. Business Model
4. Industry
5. Competition
6. Segment Analysis
7. Management Quality
8. Historical Financials
9. Normalized Financials
10. Business Drivers
11. Growth Analysis
12. Profitability
13. Balance Sheet
14. Cash Flow
15. Capital Allocation
16. Corporate Actions
17. Forecast
18. Bear/Base/Bull
19. DCF
20. SOTP
21. Relative Valuation
22. Sensitivity
23. Risks
24. Governance
25. ESG
26. Bull Case
27. Bear Case
28. What Changes the Thesis
29. Monitoring Checklist
30. Conclusion
31. Methodology
32. Definitions
33. Source Register
```

That is essentially the **ITC report converted from a manually researched document into a repeatable software system**.

---

# But don't build this all at once

I strongly recommend **5 phases**.

### Phase 1 — Document Intelligence

Build:

```text
PDF ingestion
      ↓
PDF parser
      ↓
OCR/table extraction
      ↓
document classification
      ↓
section detection
      ↓
metric extraction
      ↓
source/page citation
      ↓
PostgreSQL
```

Start with:

- Annual Report
- Quarterly results
- Investor presentation
- Earnings release
- Corporate announcements

---

### Phase 2 — Universal Business Model

Build the parts that work for **every stock**:

```text
Company identity
Business segments
Products
Services
Business model
Revenue drivers
Industry
Competitors
Management commentary
Corporate actions
Historical financials
Balance sheet
Cash flow
Risks
Capital allocation
Sources
```

This gets you coverage of your entire stock universe.

---

### Phase 3 — Sector Intelligence

Then plug in your sector frameworks:

```text
Banking
NBFC
IT
FMCG
Pharma
Auto
Capital Goods
Chemicals
Energy
Telecom
Insurance
Real Estate
Metals
etc.
```

Each sector gets its own:

```text
metrics
formulas
business drivers
forecast methodology
valuation methodology
risk framework
```

This is where the work we've already discussed around your **sector framework / metrics / weights** becomes the foundation.

---

### Phase 4 — Forecast + Valuation

Add:

```text
Forecast engine
Bear/Base/Bull
DCF
SOTP
Relative valuation
Sensitivity
Target/reference value
```

**No LLM calculation.**

Python performs calculations.

LLM explains them.

---

### Phase 5 — Editorial Intelligence

Finally let the LLM produce the narrative:

```text
Why is this business attractive?

What is changing?

What is the market missing?

What could go wrong?

What needs to happen for the thesis to work?

What should we monitor next quarter?

What is the valuation saying?
```

This is where your LLM becomes extremely powerful because it now has **structured evidence rather than raw PDFs**.

---

# The architecture I'd use

```text
                         EXISTING STOCK SCREENER
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ COMPANY UNIVERSE │
                         │   Nifty 500 etc. │
                         └────────┬─────────┘
                                  │
                                  ▼
                  ┌────────────────────────────┐
                  │ DOCUMENT INTELLIGENCE      │
                  │                            │
                  │ Annual Reports             │
                  │ Results                    │
                  │ Presentations               │
                  │ Press Releases              │
                  │ Corporate Announcements     │
                  └──────────────┬─────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │ PDF EXTRACTION ENGINE  │
                     │                        │
                     │ Text                   │
                     │ Tables                 │
                     │ Charts                 │
                     │ Footnotes              │
                     │ Page references        │
                     └────────────┬───────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │ FACT EXTRACTION ENGINE │
                     └────────────┬───────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
        Business Facts      Financial Facts      Events/Facts
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  ▼
                     ┌────────────────────────┐
                     │ VALIDATION + PROVENANCE│
                     └────────────┬───────────┘
                                  ▼
                         ┌─────────────────┐
                         │   POSTGRESQL    │
                         └────────┬────────┘
                                  │
                  ┌───────────────┼────────────────┐
                  ▼               ▼                ▼
             UNIVERSAL       SECTOR ENGINE    VALUATION
              ENGINE              │             ENGINE
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                 Banking         IT           FMCG ...
                                  │
                                  ▼
                         FORECAST ENGINE
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                       BEAR              BASE/BULL
                         │                 │
                         └────────┬────────┘
                                  ▼
                           LLM EDITORIAL
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │ COMPANY INTELLIGENCE   │
                     │ REPORT                 │
                     │                        │
                     │ Dashboard + PDF        │
                     └────────────────────────┘
```

## And one very important design decision

**Don't make the PDF extractor a one-off "ITC report extractor."**

Make it a **generic company document intelligence engine**.

For ITC:

```text
Cigarettes
FMCG
Agri
Paper
Technology
```

For another company:

```text
Auto
Components
Finance
Insurance
EV
```

The extractor should discover the business structure first and then route it into the appropriate sector framework.

That is how you can eventually run:

> **"Analyze all companies."**

without manually creating different prompts.

The ITC report already gives us the target output very clearly: historical + forecast financials, business architecture, segment economics, business drivers, cash conversion, valuation, scenarios, risks, monitoring, definitions and source documentation. ITC_Initiation_Report

**So yes: I would absolutely build this as a separate system alongside your existing screener, and build it incrementally.** The first milestone should be **Document Intelligence + Universal Company Fact Schema**, not the forecasting or LLM layer.

Example sources used for ITC: 

SOURCES & DOCUMENTATION
All actual financial figures come from dated primary filings or public company releases. Quoted market values and peer snapshots are external public-data observations retained with their exact as-of dates inside “Source Register” and “Peer_Snapshot” in the companion workbook. The bibliography below identifies the principal sources for the research narrative. Model estimates are the author’s mechanical assumptions and are not published ITC guidance.
[1] NSE — FY26 audited standalone financial results https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_INDAS_159755_21052026183213_iXBRL_WEB.html
[2] ITC — Q1 FY27 press release, 31 July 2026 https://itcportal.com/media-centre/press-releases/media-statement-financial-results-for-the-quarter-ended-30th-june-2026.html
[3] NSE — Q1 FY27 standalone financial results https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_INDAS_181204_31072026172335_iXBRL_WEB.html
[4] NSE — FY25 financial results and demerger reporting https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_INDAS_92862_22052025181843_iXBRL_WEB.html
[5] ITC — announced Century Pulp and Paper transaction https://itcportal.com/media-centre/press-releases/itc-announces-strategic-acquisition-of-pulp---paper-undertaking-0.html
[5a] Business Standard — August 2026 completion disclosure https://www.business-standard.com/companies/news/itc-completes-century-pulp-acquisition-expands-paper-business-scale-126080301416_1.html
[6] ITC — proposed Infotech and Happiest Minds combination, 31 August 2026 https://itcportal.com/media-centre/press-releases/strategic-combination-of-itc-infotech-and-happiest-minds-technologies-to-create-a-scaled-future-ready-ai-first-global-technology-services-enterprise-with-us-dollar-1-billion-revenue-by-fy28.html
[7] ITC — Annual Report and Accounts FY2026 https://itcportal.com/investors/itc-reports-and-accounts/itc-report-and-accounts-2026.html
[8] ITC & ITC Hotels historical market closes https://stockanalysis.com/quote/nse/ITC/history/
[8a] ITC Hotels quotation https://stockanalysis.com/quote/nse/ITCHOTELS/history/
[9] NSE — audited FY26 consolidated result https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_INDAS_159756_21052026183229_iXBRL_WEB.html
[10] ITC — Q1 FY27 investor presentation https://itcportal.com/content/dam/itc-corporate/pdfs/financial-result/quarterly-results-2026-2027/june-2026/ITC-Quarterly-Result-Presentation-Q1-FY2027.pdf
[11] ITC — FY26 financial results press release https://itcportal.com/media-centre/press-releases/media-statement-financial-results-for-the-quarter-and-year-ended-31st-march-2026.html

The file is in 