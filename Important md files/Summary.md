# Llama Report Interpretation & Rendering Architecture

## 1. Objective

The fundamental screener already has dedicated agents responsible for fetching, extracting, validating, and calculating financial and sector-specific metrics.

The role of the locally hosted Llama model is **not to fetch data or perform primary financial calculations**.

Llama acts as the:

1. **Business-context interpreter**
2. **Financial-data interpreter**
3. **Cross-metric reasoning layer**
4. **Narrative generation engine**
5. **Report section generator**
6. **Report structure / blueprint generator**

The PDF renderer remains responsible for the actual visual rendering.

### Core principle

```text
Agents      → What is the data?
Llama       → What does the data mean?
Renderer    → How should it look?
```

---

# 2. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │      USER / UI      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  RESEARCH ORCHESTRATOR
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │ Financial   │       │ Sector      │       │ Company /   │
       │ Agents      │       │ Agents      │       │ Business    │
       └──────┬──────┘       └──────┬──────┘       │ Agents      │
              │                     │              └──────┬──────┘
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ MASTER COMPANY DATA │
                         │      OBJECT         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    LOCAL LLAMA      │
                         │ Interpretation Layer│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   REPORT BLUEPRINT  │
                         │       JSON          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    PDF RENDERER     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                              FINAL PDF
```

---

# 3. Responsibilities

## 3.1 Existing Agents

Agents are responsible for obtaining reliable structured information.

They should provide:

* Financial metrics
* Historical financials
* Balance-sheet metrics
* Cash-flow metrics
* Shareholding data
* Valuation metrics
* Sector metrics
* Industry metrics
* Company operational metrics
* Management commentary
* Order book
* Capacity
* Capex
* Guidance
* Business segments
* Customer information
* Geographic exposure
* Corporate actions
* Relevant source references

Agents should also provide:

* Period
* Unit
* Source
* Source date
* Source page where available
* Confidence / validation status

---

# 4. Llama Responsibilities

Llama should consume the verified structured data and interpret it.

### Llama SHOULD:

* Explain the business model
* Summarize the company
* Explain revenue drivers
* Explain changes in business mix
* Identify growth drivers
* Identify important dependencies
* Connect operational metrics with financial metrics
* Interpret financial trends
* Explain margin movements
* Explain capital allocation
* Interpret balance-sheet changes
* Interpret cash-flow quality
* Explain valuation context
* Identify risks
* Prioritize what matters
* Generate concise investment-research narrative
* Convert structured data into report-ready sections
* Decide which insights deserve emphasis

### Llama SHOULD NOT:

* Fetch external data
* Invent missing data
* Assume financial values
* Replace deterministic calculations
* Calculate important financial ratios independently
* Override agent-provided values
* Treat management guidance as actual results
* Treat an order pipeline as an order book
* Create unsupported claims
* Generate investment conclusions unsupported by the supplied data

---

# 5. Deterministic vs LLM Responsibilities

| Task                        | Owner         |
| --------------------------- | ------------- |
| Revenue calculation         | Agent / code  |
| EBITDA calculation          | Agent / code  |
| CAGR                        | Agent / code  |
| ROE                         | Agent / code  |
| ROCE                        | Agent / code  |
| Debt/Equity                 | Agent / code  |
| Working-capital days        | Agent / code  |
| Valuation multiples         | Agent / code  |
| Historical financials       | Agent         |
| Sector metrics              | Sector agent  |
| Company operational metrics | Company agent |
| Source retrieval            | Agents        |
| Business-model explanation  | Llama         |
| Trend interpretation        | Llama         |
| Cross-metric interpretation | Llama         |
| Risk narrative              | Llama         |
| Growth-driver narrative     | Llama         |
| Report narrative            | Llama         |
| Report structure            | Llama         |
| Tables                      | Renderer      |
| Charts                      | Renderer      |
| Typography                  | Renderer      |
| Pagination                  | Renderer      |
| PDF generation              | Renderer      |

---

# 6. Master Company Data Object

All agents should eventually feed a unified company object.

Example:

```json
{
  "company": {
    "name": "Waaree Energies Ltd",
    "sector": "Solar Manufacturing",
    "industry": "Solar PV Manufacturing"
  },

  "business": {
    "segments": [],
    "products": [],
    "customers": [],
    "geographies": [],
    "revenue_mix": []
  },

  "operations": {
    "production": [],
    "capacity": [],
    "utilisation": [],
    "technology_mix": []
  },

  "orders": {
    "order_book": {},
    "order_pipeline": {}
  },

  "expansion": [],

  "financials": {
    "income_statement": {},
    "balance_sheet": {},
    "cash_flow": {}
  },

  "ratios": {},

  "valuation": {},

  "shareholding": {},

  "management": {},

  "guidance": {},

  "sector": {},

  "risks": [],

  "sources": []
}
```

This object becomes the **single input to the interpretation layer**.

---

# 7. Provenance

Every important fact should retain its source.

Example:

```json
{
  "metric": "order_book",
  "value": 53000,
  "unit": "INR_CRORE",
  "period": "Q4_FY26",

  "source": {
    "type": "investor_presentation",
    "document": "Waaree Energies Q4 FY26 Investor Presentation",
    "page": 8
  },

  "status": "reported",
  "confidence": "high"
}
```

For management guidance:

```json
{
  "metric": "EBITDA_target",
  "low": 7000,
  "high": 7700,
  "unit": "INR_CRORE",
  "period": "FY27",

  "status": "management_guidance",

  "source": {
    "type": "investor_presentation",
    "page": 32
  }
}
```

This distinction is mandatory.

---

# 8. Fact vs Interpretation

The report engine should distinguish between:

## FACT

Directly supplied by an agent.

Example:

> Order book stood at ₹53,000 Cr as of Q4 FY26.

## INTERPRETATION

Generated by Llama from supplied facts.

Example:

> The sizeable order book provides strong revenue visibility, although execution capacity, realisations and margin sustainability remain important determinants of profitability.

The interpretation must never introduce a new unsupported fact.

---

# 9. Llama Output

Llama should NOT directly generate the PDF.

Instead, Llama generates a structured **Report Blueprint**.

Example:

```json
{
  "report": {
    "company": "Waaree Energies Ltd"
  },

  "sections": [

    {
      "id": "company_snapshot",
      "type": "text",
      "title": "Company Snapshot",
      "content": "..."
    },

    {
      "id": "business_model",
      "type": "business_model",
      "title": "Business Model",
      "content": "...",
      "key_points": []
    },

    {
      "id": "business_mix",
      "type": "metric_table",
      "title": "Business Mix",
      "metrics": []
    },

    {
      "id": "operating_scale",
      "type": "metric_table",
      "title": "Operating Scale",
      "metrics": []
    },

    {
      "id": "growth_drivers",
      "type": "insight_cards",
      "title": "Growth Drivers",
      "items": []
    },

    {
      "id": "risks",
      "type": "risk_cards",
      "title": "Key Risks",
      "items": []
    }
  ]
}
```

The renderer then converts these objects into PDF components.

---

# 10. Company Overview / Preface

The fundamental report should begin with a company-specific preface.

Recommended structure:

```text
COMPANY & BUSINESS OVERVIEW

1. Company Snapshot

2. Business Model

3. Products & Services

4. Revenue Segments

5. Customer Segments

6. Geographic Exposure

7. Operating Scale

8. Manufacturing / Infrastructure

9. Order Book & Order Pipeline

10. Capacity

11. Capacity Expansion

12. New Ventures / Adjacent Businesses

13. Management & Corporate Actions

14. Management Guidance

15. Key Growth Drivers

16. Key Business Risks
```

This section should be generated dynamically depending on the company's business.

---

# 11. Business Model Interpretation

Llama should answer:

### What does the company actually do?

```text
Core products
Core services
Primary customers
Primary markets
```

### How does it make money?

```text
Revenue sources
Pricing drivers
Volume drivers
Mix drivers
Recurring vs non-recurring revenue
```

### Where does it sit in the value chain?

```text
Raw material
      ↓
Manufacturing
      ↓
Distribution
      ↓
Customer
```

### What drives growth?

```text
Volume
Price
Market share
Capacity
New products
New geographies
Acquisitions
Vertical integration
```

---

# 12. Cross-Metric Interpretation

This is one of the most important responsibilities of Llama.

Llama should look for relationships between metrics.

Example:

```text
Revenue Growth             ↑
Production                 ↑
Capacity                   ↑
Order Book                 ↑
EBITDA Margin              ↓
Capex                      ↑
Working Capital            ↑
```

Llama should interpret this collectively rather than discussing each metric independently.

Possible output:

> The company is scaling rapidly through capacity expansion and strong order visibility. However, the simultaneous increase in capital expenditure and working-capital requirements means that execution, utilisation and incremental return on capital should be monitored closely.

---

# 13. Financial Interpretation

The financial agents provide the numbers.

Llama interprets them.

### Revenue

Llama should explain:

* Growth trend
* Growth consistency
* Organic vs inorganic growth where available
* Segment contribution
* Volume vs price/mix where available

### Margins

Interpret:

* Expansion
* Compression
* Operating leverage
* Product mix
* Cost pressures
* Sustainability

### ROE / ROCE

Interpret:

* Improvement / deterioration
* Capital efficiency
* Whether growth is consuming excessive capital
* Incremental capital efficiency where data permits

### Cash Flow

Interpret:

* CFO vs EBITDA/PAT
* FCF generation
* Working-capital intensity
* Capex requirements
* Cash conversion

---

# 14. Sector-Aware Interpretation

Llama should receive the sector classification and sector-specific metrics.

It should NOT use one generic interpretation template for every company.

Example:

```text
Sector
   ↓
Sector Configuration
   ↓
Relevant Metrics
   ↓
Llama Interpretation
```

### Solar Manufacturing

Potential interpretation inputs:

```text
Module capacity
Cell capacity
Wafer capacity
Production
Utilisation
Module ASP
Cell ASP
Technology mix
Order book
Exports
Domestic sales
Capex
Working capital
```

### Banking

Potential inputs:

```text
Loan growth
Deposit growth
CASA
NIM
GNPA
NNPA
PCR
Slippages
Credit cost
ROA
ROE
Capital adequacy
```

### IT Services

Potential inputs:

```text
Revenue growth
CC growth
TCV
Deal wins
Utilisation
Attrition
Revenue/employee
EBIT margin
Offshore mix
Client concentration
```

The Llama prompt should dynamically receive the relevant sector schema.

---

# 15. Dynamic Section Generation

Not every company should receive the same sections.

For example:

```text
Manufacturing company
    → Capacity
    → Utilisation
    → Production
    → Order book
    → Capex

Bank
    → Loan book
    → Deposits
    → Asset quality
    → NIM
    → Capital adequacy

IT company
    → Deal wins
    → TCV
    → Utilisation
    → Attrition
    → Revenue/employee
```

The orchestrator should determine the available sections.

Llama should then interpret those sections.

---

# 16. Prompt Architecture

Instead of one massive prompt, maintain modular prompts.

```text
prompts/
│
├── company_snapshot.prompt
├── business_model.prompt
├── business_mix.prompt
├── operational_analysis.prompt
├── growth_drivers.prompt
├── financial_interpretation.prompt
├── balance_sheet_interpretation.prompt
├── cashflow_interpretation.prompt
├── valuation_interpretation.prompt
├── management_analysis.prompt
├── risk_analysis.prompt
├── sector_analysis.prompt
└── final_conclusion.prompt
```

The report orchestrator chooses the appropriate prompts.

---

# 17. Master Llama System Prompt

Conceptually:

```text
You are the interpretation engine of a fundamental equity
research system.

You receive structured, verified company data generated by
specialized financial and sector agents.

Your responsibility is to interpret the supplied information
and generate concise, professional fundamental research.

STRICT RULES:

1. Do not fetch external information.
2. Use only supplied data.
3. Never invent numbers.
4. Never estimate missing values unless explicitly instructed.
5. Do not modify agent-provided values.
6. Preserve units exactly.
7. Preserve reporting periods.
8. Clearly distinguish historical results from guidance.
9. Clearly distinguish order book from order pipeline.
10. Clearly distinguish facts from interpretation.
11. Do not treat management guidance as actual performance.
12. Do not create unsupported claims.
13. Highlight relationships between metrics.
14. Prioritize material insights.
15. Avoid generic investment commentary.
16. Keep the output suitable for an equity research report.
17. Return structured JSON according to the supplied schema.
```

---

# 18. Interpretation Pipeline

```text
Agent Outputs
      ↓
Validation
      ↓
Normalization
      ↓
Master Company Object
      ↓
Sector Configuration
      ↓
Llama Context Builder
      ↓
Llama
      ↓
Structured Report Blueprint
      ↓
Blueprint Validation
      ↓
PDF Renderer
```

---

# 19. Llama Context Builder

Do not blindly send every piece of raw data to the model.

Create a context builder.

```text
MASTER DATA
     ↓
Relevant facts
     ↓
Relevant historical trends
     ↓
Relevant sector metrics
     ↓
Relevant valuation metrics
     ↓
Relevant management commentary
     ↓
LLAMA CONTEXT
```

The context should be organized logically:

```text
COMPANY
BUSINESS
OPERATIONS
FINANCIALS
BALANCE SHEET
CASH FLOW
VALUATION
SECTOR
MANAGEMENT
RISKS
SOURCES
```

---

# 20. Output Validation

The Llama output should pass a validator before entering the PDF renderer.

Validate:

### Numbers

```text
Did Llama introduce a number that wasn't supplied?
```

### Periods

```text
Is FY26 being incorrectly described as FY27?
```

### Units

```text
₹ Cr
₹ million
GW
GWh
%
```

### Guidance

```text
Actual
vs
Management Guidance
```

### Order Book

```text
Order Book
vs
Order Pipeline
```

### Unsupported claims

```text
Does every factual claim map back to supplied data?
```

If validation fails:

```text
Llama Output
      ↓
Validator
      ↓
FAIL
      ↓
Regenerate / Repair
```

---

# 21. PDF Renderer

The PDF renderer should be completely independent of the Llama model.

It receives:

```json
{
  "report": {
    "sections": []
  }
}
```

and renders components such as:

```text
TextBlock
MetricCard
MetricTable
TrendTable
InsightCard
RiskCard
Chart
Timeline
CapacityChart
RevenueMixChart
```

This allows the visual design to change without modifying the Llama layer.

---

# 22. Recommended PDF Structure

```text
PAGE 1
──────────────────────────────
Company Header
Investment Snapshot
Key Metrics
Valuation
Fundamental Score
──────────────────────────────

PAGE 2+
──────────────────────────────
COMPANY & BUSINESS OVERVIEW

Company Snapshot
Business Model
Revenue Mix
Products
Customers
Geographies
Operating Scale
Capacity
Order Book
Expansion
New Ventures
Management
Guidance
──────────────────────────────

SECTOR ANALYSIS

Industry Structure
Demand Drivers
Competitive Position
Sector-specific metrics
──────────────────────────────

FINANCIAL ANALYSIS

Revenue
EBITDA
PAT
Margins
ROE
ROCE
Cash Flow
──────────────────────────────

BALANCE SHEET

Debt
Working Capital
Liquidity
Capital Allocation
──────────────────────────────

VALUATION

P/E
EV/EBITDA
P/B
DCF
Historical valuation
Peer valuation
──────────────────────────────

MANAGEMENT & GOVERNANCE
──────────────────────────────

RISKS
──────────────────────────────

BULL / BASE / BEAR
──────────────────────────────

FINAL FUNDAMENTAL ASSESSMENT
──────────────────────────────
```

---

# 23. Important Design Principle

Do not make Llama responsible for visual coordinates.

Bad architecture:

```text
Llama
 ↓
HTML/CSS
 ↓
PDF
```

Preferred architecture:

```text
Llama
 ↓
Semantic Report JSON
 ↓
Renderer
 ↓
PDF
```

Llama should say:

```json
{
  "type": "risk_card",
  "priority": "high",
  "title": "Execution Risk",
  "content": "..."
}
```

The renderer decides:

```text
Where the card goes
Font
Size
Spacing
Icon
Page position
Colors
Borders
```

---

# 24. Example: Waaree Energies

The agents provide:

```text
Module revenue contribution = 91%
Module production = 7.1 → 12.6 GW
Cell production = 0.1 → 2.3 GW
Module capacity = 26 GW
Cell capacity = 5.4 GW
Order book = ₹53,000 Cr
Pipeline = 100+ GW
Planned ingot/wafer/cell capacity = 10 GW
Planned capex = ₹6,200 Cr
FY27 EBITDA guidance = ₹7,000–7,700 Cr
```

Llama should transform this into:

```text
BUSINESS MODEL

Waaree Energies is primarily a solar PV manufacturing business,
with modules remaining the dominant revenue contributor. The
company is simultaneously increasing vertical integration into
cells and ingot-wafer manufacturing while expanding into
adjacent renewable-energy businesses.

GROWTH DRIVERS

1. Expansion of module manufacturing capacity
2. Increasing cell production
3. Planned backward integration
4. Large order book
5. Expansion into adjacent energy businesses

WHAT MATTERS

The key variables to monitor are capacity utilisation,
module realisations, margin sustainability, working-capital
requirements and the return generated on the company's
large expansion programme.

KEY RISKS

Rapid capacity expansion increases execution and capital
requirements. Profitability will remain sensitive to module
pricing, input costs, utilisation and industry supply-demand
conditions.
```

The renderer then turns these into the designed PDF.

---

# 25. Final Architecture

The complete system should ultimately follow:

```text
                 ┌────────────────────────┐
                 │       DATA AGENTS      │
                 │                        │
                 │ Financial              │
                 │ Sector                 │
                 │ Company                │
                 │ Management             │
                 │ Valuation              │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │    DATA VALIDATION     │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │ MASTER COMPANY OBJECT  │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │   CONTEXT BUILDER      │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │       LOCAL LLAMA      │
                 │                        │
                 │ Interpretation          │
                 │ Reasoning               │
                 │ Narrative               │
                 │ Prioritisation          │
                 │ Report Structure        │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │ REPORT BLUEPRINT JSON   │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │   OUTPUT VALIDATOR     │
                 └───────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │     PDF RENDERER       │
                 │                        │
                 │ Tables                 │
                 │ Charts                 │
                 │ Cards                  │
                 │ Layout                 │
                 │ Pagination             │
                 └───────────┬────────────┘
                             │
                             ▼
                    FUNDAMENTAL REPORT
```

## Core Principle

> **Agents provide the truth.
> Llama provides the interpretation.
> The renderer provides the presentation.**

This separation should be treated as a core architectural rule of the fundamental screener.
