Yes. And I would change the approach slightly from **“build an MCP server that fetches data”** to:

> **Build a reliable financial-data platform first, and expose it through MCP.**

MCP should be the **interface/orchestration layer**, not the database or source of truth.

For your screener engine, especially because you want **all Indian stocks + sector-specific analysis + promoter integrity + regulatory red flags + historical data**, accuracy and provenance are much more important than having many autonomous agents.

The architecture I recommend is this:

```text
                         ┌──────────────────────────┐
                         │       YOUR APP/UI        │
                         │ Screener / Stock Detail  │
                         │ Research / Alerts        │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │       MCP GATEWAY        │
                         │  Tools + Resources       │
                         └────────────┬─────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
                ▼                     ▼                     ▼
       ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
       │ Fundamental    │    │ Integrity &    │    │ Sector         │
       │ Data Agent     │    │ Governance     │    │ Analysis Agent │
       │                │    │ Agent          │    │                │
       └───────┬────────┘    └───────┬────────┘    └───────┬────────┘
               │                     │                     │
               └─────────────────────┼─────────────────────┘
                                     ▼
                         ┌──────────────────────────┐
                         │   CANONICAL DATA LAYER   │
                         │  Normalized stock data   │
                         │  Historical observations │
                         │  Derived metrics         │
                         │  Provenance              │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┼──────────────────┐
                    │                 │                  │
                    ▼                 ▼                  ▼
             ┌────────────┐   ┌────────────┐    ┌────────────┐
             │ PostgreSQL │   │ Object     │    │ Redis      │
             │             │   │ Storage    │    │ Cache      │
             │ Clean data  │   │ PDFs/XBRL  │    │ Latest     │
             └────────────┘   └────────────┘    └────────────┘
                    ▲
                    │
             ┌──────┴─────────────────────────────────────┐
             │             INGESTION LAYER                 │
             └──────┬────────┬────────┬────────┬──────────┘
                    │        │        │        │
                    ▼        ▼        ▼        ▼
                  NSE      BSE      RBI      SEBI
                    │        │        │        │
                    └────────┴────────┴────────┘
                              +
                       Company IR websites
                              +
                             MCA
                              +
                    Optional secondary sources
```

## 1. The most important architectural decision

### Don't make the LLM responsible for fetching numbers.

For example, don't do:

```text
User asks about HDFC
       ↓
LLM
       ↓
call NSE
call RBI
call Screener
call web
       ↓
LLM combines everything
       ↓
answer
```

That will eventually produce inconsistent numbers.

Instead:

```text
Sources
   ↓
Scheduled ingestion
   ↓
Raw immutable data
   ↓
Parsing/normalization
   ↓
Validation
   ↓
Canonical financial database
   ↓
Derived metrics
   ↓
MCP
   ↓
LLM / Screener / UI
```

The LLM should **retrieve and interpret already-validated data**.

---

# 2. Don't build one giant MCP server internally

I'd use **one MCP gateway initially**, but internally divide it into domain services.

Something like:

```text
mcp/
├── fundamental/
├── market/
├── filings/
├── ownership/
├── regulatory/
├── banking/
├── auto/
├── fmcg/
├── pharma/
├── it/
└── research/
```

But these don't necessarily need to be separate MCP servers.

Initially:

```text
                    Financial MCP Server
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
 Fundamental            Integrity           Sector
   Tools                  Tools               Tools
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    Data Platform
```

Later, when the system becomes large, you can split them into separate MCP servers.

---

# 3. I would NOT use Screener.in as your primary data source

This is important.

Screener itself says that **it does not provide an API**. Its export facility is a premium feature. ([Screener Support][1])

Its terms also restrict copying/material reuse, so I would **not architect your production data pipeline around scraping Screener**. ([Screener][2])

Use Screener as:

```text
Secondary / reference / validation source
```

not:

```text
Your primary financial database
```

For your engine, I'd prefer:

### Primary

1. NSE
2. BSE
3. RBI
4. SEBI
5. MCA
6. Company annual reports
7. Company investor presentations/results

### Secondary

8. Screener
9. Moneycontrol
10. Tijori
11. Trendlyne
12. etc.

This gives you a much stronger architecture.

NSE itself provides corporate filings including financial results and shareholding patterns, with XBRL links and downloadable data. ([NSE India][3])

NSE also explicitly offers a **paid corporate-data product** containing fundamentals, corporate announcements and shareholding patterns, which tells us something important architecturally: high-quality exchange-level structured data is valuable and may eventually be worth licensing rather than scraping. ([NSE India][4])

---

# 4. Your source architecture

I would create a **Source Registry**.

```text
source_registry

source_id
source_name
source_type
authority_level
url
access_method
update_frequency
coverage
license
reliability_score
last_success
last_failure
```

Example:

```json
{
  "source": "RBI",
  "type": "regulator",
  "authority_level": 1,
  "coverage": [
    "bank_asset_quality",
    "capital_adequacy",
    "deposits",
    "credit"
  ],
  "reliability": 1.0
}
```

Then:

```text
Authority Level

1 = Regulator / Exchange / Company filing
2 = Audited annual report
3 = Company presentation
4 = Reputable financial database
5 = News / web
6 = LLM inference
```

Your engine should **never silently replace Level-1 data with Level-5 data**.

---

# 5. The biggest feature: provenance

Every number in your database should know:

> **Where did this number come from?**

This is absolutely critical.

Instead of:

```json
{
  "gnpa": 1.2
}
```

store:

```json
{
  "metric": "gnpa_ratio",
  "value": 1.2,
  "unit": "%",
  "period": "2026-Q1",
  "company_id": "HDFCBANK",
  "source": "RBI",
  "source_document": "...",
  "source_date": "2026-07-31",
  "retrieved_at": "...",
  "reported_at": "...",
  "confidence": 0.99
}
```

Even better:

```text
metric_observation
------------------
company_id
metric_id
value
unit
period_start
period_end
period_type
reported_date
source_id
source_document_id
source_page
source_location
extraction_method
confidence
created_at
```

Then your UI can say:

> GNPA: 1.20%
> **Source: RBI | Q1 FY27 | reported 31 Jul 2026**

That is a massive difference from a normal stock screener.

---

# 6. Raw → normalized → derived

I'd have **three separate layers**.

## Layer 1 — Raw

Never modify this.

```text
raw/
├── nse/
├── bse/
├── rbi/
├── sebi/
├── mca/
└── company_filings/
```

Store:

* JSON
* CSV
* XML/XBRL
* PDF
* HTML
* API response

with timestamp.

For example:

```text
raw/rbi/2026/09/11/bank_statistics_2026q1.json
```

---

## Layer 2 — Normalized

Convert different sources into common structures.

Example:

```text
raw:
    "Gross NPA"
    "Gross NPA Ratio"
    "GNPA (%)"
    "Gross Non-Performing Assets"

             ↓

canonical metric:

GNPA_RATIO
```

Same for:

```text
PAT
Net Profit
Profit After Tax
PAT attributable to owners
```

etc.

---

# 7. Canonical metric dictionary

This is probably one of the most important components of your entire project.

Create:

```text
metrics/
    metric_registry.yaml
```

Example:

```yaml
ROE:
  id: roe
  name: Return on Equity
  unit: percentage
  category: profitability
  applicable_sectors:
    - banking
    - nbfc
    - insurance
    - manufacturing
  primary_sources:
    - company_annual_report
    - nse
    - bse

GNPA:
  id: gnpa_ratio
  name: Gross NPA Ratio
  unit: percentage
  category: asset_quality
  applicable_sectors:
    - banking
    - nbfc

NIM:
  id: nim
  name: Net Interest Margin
  unit: percentage
  category: banking_profitability
  applicable_sectors:
    - banking
    - nbfc
```

This allows your sector `.md` files to refer to **metric IDs**, not random source names.

---

# 8. Then your sector MD becomes configuration

This is where your previous idea becomes extremely powerful.

For example:

```text
sectors/
├── banking.md
├── nbfc.md
├── automobile.md
├── fmcg.md
├── it.md
├── pharma.md
├── chemicals.md
├── metals.md
└── retail.md
```

But the MD shouldn't contain data.

It should say:

```yaml
sector: banking

required_metrics:

  profitability:
    - roe
    - roa
    - nim

  asset_quality:
    - gnpa_ratio
    - nnpa_ratio
    - provision_coverage_ratio
    - slippage_ratio

  capital:
    - crar
    - cet1
    - tier1

  valuation:
    - pe
    - pb
    - historical_pb

  growth:
    - loan_growth
    - deposit_growth
    - profit_growth_5y
```

Then your engine automatically knows:

> "This is a bank. Fetch these metrics."

---

# 9. Agents: I would use fewer than you think

Don't create:

```text
Agent 1 → NSE
Agent 2 → RBI
Agent 3 → BSE
Agent 4 → SEBI
Agent 5 → MCA
Agent 6 → Screener
```

That's unnecessarily complicated.

Instead, agents should represent **jobs**, not websites.

### Agent 1 — Data Acquisition Agent

```text
Input:
company_id

Tasks:
- determine required sources
- retrieve raw data
- store raw documents
- trigger parsers
```

---

### Agent 2 — Financial Extraction Agent

```text
Raw filings
    ↓
extract:
revenue
PAT
EPS
assets
liabilities
cash flow
etc.
```

For PDFs, XBRL, annual reports, etc.

---

### Agent 3 — Integrity Agent

This is important.

```text
Company
 ↓
NSE/BSE shareholding
 ↓
Promoter pledge
 ↓
SEBI orders
 ↓
MCA directors/charges
 ↓
Auditor changes
 ↓
Related-party transactions
 ↓
Corporate actions
 ↓
Integrity findings
```

Output:

```json
{
  "integrity_score": 78,
  "risk_level": "moderate",
  "flags": [
    {
      "type": "promoter_selling",
      "severity": "medium",
      "evidence": "..."
    }
  ]
}
```

**The agent should never invent the conclusion.**

Every flag must point back to evidence.

---

# 10. Agent 4 — Sector Analyst

This agent receives normalized data.

For a bank:

```text
ROE
ROA
NIM
GNPA
NNPA
PCR
CASA
CRAR
CET1
Loan Growth
Deposit Growth
P/B
Historical P/B
```

Then applies:

```text
sectors/banking.md
```

and produces:

```json
{
  "sector": "banking",
  "quality_score": 87,
  "asset_quality_score": 91,
  "capital_score": 94,
  "growth_score": 78,
  "valuation_score": 72
}
```

---

# 11. Agent 5 — Valuation Engine

I would actually make this **deterministic code**, not an LLM agent.

For example:

```text
current PE
current PB
historical PE
historical PB
peer PE
peer PB
ROE
growth
```

Calculate:

```text
PE premium/discount
PB premium/discount
historical valuation percentile
peer valuation percentile
```

Then:

```text
valuation_score = formula(...)
```

Don't let an LLM decide whether:

```text
P/B = 1.8
```

is cheap.

Your algorithm should do that.

The LLM can **explain** the result.

---

# 12. Same for financial ratios

These should be deterministic.

For example:

```python
ROA = net_profit / average_total_assets
ROE = net_profit / average_equity
NIM = net_interest_income / average_interest_earning_assets
```

The agent shouldn't calculate these from memory.

Your **Financial Calculation Engine** should.

---

# 13. So the real architecture becomes

```text
                    ┌────────────────────┐
                    │      USER/UI       │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     MCP GATEWAY    │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
       Data Retrieval    Analysis Tools    Research Tools
             │                │                │
             ▼                ▼                ▼
       ┌──────────┐    ┌──────────────┐   ┌────────────┐
       │Canonical │    │Calculation   │   │Integrity   │
       │Data      │    │Engine        │   │Engine      │
       └────┬─────┘    └──────┬───────┘   └─────┬──────┘
            │                 │                  │
            └─────────────────┼──────────────────┘
                              ▼
                       ┌─────────────┐
                       │ PostgreSQL  │
                       └──────┬──────┘
                              │
                 ┌────────────┼─────────────┐
                 ▼            ▼             ▼
             Raw Store    Documents      Cache
              S3/MinIO    PDFs/XBRL      Redis
                 ▲
                 │
         ┌───────┴─────────────────┐
         │       INGESTION         │
         └───────┬─────────────────┘
                 │
      ┌──────────┼───────────┬──────────┐
      ▼          ▼           ▼          ▼
     NSE        BSE         RBI        SEBI
      │          │           │          │
      └──────────┴───────────┴──────────┘
                    +
              MCA / Company IR
```

---

# 14. Your MCP tools

This is where I'd make the API very clean.

### Fundamental

```text
get_company_profile
get_financials
get_profit_loss
get_balance_sheet
get_cash_flow
get_ratios
get_growth_metrics
get_valuation
get_historical_valuation
```

### Ownership

```text
get_shareholding
get_promoter_holding
get_promoter_transactions
get_promoter_pledge
get_institutional_holding
```

### Governance

```text
get_directors
get_auditor_history
get_related_party_transactions
get_corporate_actions
get_regulatory_actions
get_sebi_orders
get_mca_information
```

### Banking

```text
get_bank_asset_quality
get_bank_capital
get_bank_nim
get_bank_casa
get_bank_credit_deposit
get_bank_slippages
get_bank_provisioning
```

Later:

```text
get_auto_metrics
get_fmcg_metrics
get_it_metrics
get_pharma_metrics
...
```

---

# 15. And one extremely powerful MCP tool

Eventually:

```text
analyze_stock
```

Input:

```json
{
  "company": "HDFCBANK",
  "analysis_type": "fundamental",
  "sector": "auto_detect"
}
```

The system does:

```text
HDFCBANK
    ↓
Identify sector
    ↓
Load banking.md
    ↓
Determine required metrics
    ↓
Retrieve canonical data
    ↓
Check data freshness
    ↓
Calculate missing ratios
    ↓
Run integrity analysis
    ↓
Run valuation
    ↓
Run sector comparison
    ↓
Return structured result
```

That's the **real brain** of your application.

---

# 16. Data freshness must be built in

Every metric should have:

```text
reported_at
available_at
retrieved_at
period_end
source
```

Then you can distinguish:

```text
FY2026
Q1 FY2027
TTM
Current
Historical
```

This prevents a huge class of errors.

For example:

```text
Price:        real-time
P/B:          calculated today
ROE:          FY2026
GNPA:         Q1 FY2027
CRAR:         Q1 FY2027
Promoter:     June 2026
SEBI order:   September 2026
```

The engine needs to understand that these aren't all from the same date.

---

# 17. Data validation layer

This is another part I consider **non-negotiable**.

Suppose:

```text
NSE says promoter holding = 42.1%
BSE says promoter holding = 42.1%
Company filing = 42.1%
```

Excellent.

But:

```text
NSE = 42.1%
BSE = 41.2%
```

Don't silently choose one.

Return:

```json
{
  "metric": "promoter_holding",
  "status": "CONFLICT",
  "sources": [
    {"source": "NSE", "value": 42.1},
    {"source": "BSE", "value": 41.2}
  ]
}
```

Then your system can investigate.

---

# 18. Confidence engine

I would create:

```text
DATA_CONFIDENCE
```

Example:

```text
1.00 = regulatory/exchange/company primary source
0.95 = two independent primary sources agree
0.90 = audited annual report
0.80 = reputable secondary source
0.60 = extracted from ambiguous PDF
0.40 = web-derived
0.20 = inference
```

And every stock analysis should show:

```text
Data completeness: 96%
Data confidence:   94%
Last updated:      11 Sep 2026
```

This is **far more valuable than pretending the data is 100% accurate**.

---

# 19. Your database

For your current scale, I would use:

### PostgreSQL

Not MongoDB.

Your data is heavily relational:

```text
Company
   ↓
Security
   ↓
Financial Period
   ↓
Metric
   ↓
Observation
   ↓
Source
   ↓
Document
```

PostgreSQL fits this extremely well.

---

### Object storage

Use:

```text
S3 / MinIO
```

for:

* Annual reports
* Investor presentations
* RBI files
* SEBI orders
* XBRL
* exchange documents

Don't dump PDFs into PostgreSQL.

---

### Redis

For:

```text
latest price
latest analysis
frequent MCP calls
API caching
rate-limit state
```

---

### Optional later: pgvector

For searching documents:

```text
"Find all auditor resignations in the last 5 years"

"Find related party transactions involving promoter entities"

"Find management commentary about asset quality"
```

You can embed annual reports and regulatory documents.

But **vector search should never replace structured financial data**.

---

# 20. The most important distinction

You actually have **three different systems**.

### System A — Data

> What happened?

```text
Revenue
PAT
ROE
GNPA
CRAR
Promoter holding
SEBI order
```

### System B — Calculation

> What does the raw data mathematically imply?

```text
ROE
CAGR
historical P/B percentile
profit growth
valuation discount
```

### System C — Intelligence

> So what?

```text
Is this a quality bank?
Is valuation attractive?
Is management trustworthy?
What are the risks?
```

**A + B should be deterministic.**

**C can use an LLM.**

That separation will make your system dramatically more reliable.

---

# 21. I would structure the repository like this

```text
fundamental-engine/
│
├── apps/
│   ├── web/
│   ├── api/
│   └── mcp/
│
├── data/
│   ├── raw/
│   ├── normalized/
│   └── derived/
│
├── ingestion/
│   ├── nse/
│   ├── bse/
│   ├── rbi/
│   ├── sebi/
│   ├── mca/
│   └── company/
│
├── parsers/
│   ├── xbrl/
│   ├── pdf/
│   ├── html/
│   └── csv/
│
├── models/
│   ├── company.py
│   ├── security.py
│   ├── financial.py
│   ├── metric.py
│   ├── ownership.py
│   ├── governance.py
│   └── source.py
│
├── calculations/
│   ├── profitability.py
│   ├── growth.py
│   ├── valuation.py
│   ├── cashflow.py
│   └── ratios.py
│
├── integrity/
│   ├── promoter.py
│   ├── auditor.py
│   ├── related_party.py
│   ├── regulatory.py
│   └── dilution.py
│
├── sectors/
│   ├── banking.md
│   ├── nbfc.md
│   ├── automobile.md
│   ├── fmcg.md
│   ├── it.md
│   └── pharma.md
│
├── agents/
│   ├── acquisition_agent.py
│   ├── extraction_agent.py
│   ├── integrity_agent.py
│   └── sector_agent.py
│
├── mcp/
│   ├── fundamental_tools.py
│   ├── ownership_tools.py
│   ├── governance_tools.py
│   ├── sector_tools.py
│   └── research_tools.py
│
├── validation/
│   ├── source_validation.py
│   ├── cross_source.py
│   ├── freshness.py
│   └── completeness.py
│
├── database/
│   ├── migrations/
│   └── schema/
│
└── tests/
    ├── calculations/
    ├── ingestion/
    ├── validation/
    └── sectors/
```

---

# 22. One more thing: don't start with all 5,000 stocks

I'd build **Banking end-to-end first**.

Something like:

```text
Phase 1

10 banks
   ↓
NSE/BSE
   ↓
RBI
   ↓
SEBI
   ↓
Company filings
   ↓
Postgres
   ↓
Validation
   ↓
Banking metrics
   ↓
Banking scoring
   ↓
MCP
   ↓
Your UI
```

Once that works perfectly:

```text
Banking
   ↓
NBFC
   ↓
Automobile
   ↓
FMCG
   ↓
IT
   ↓
Pharma
   ↓
...
```

The **data architecture stays the same**. Only the sector metric definitions change.

---

## My recommended technology stack

If you're building this yourself, I'd keep it relatively boring:

| Component      | Recommendation                  |
| -------------- | ------------------------------- |
| Backend        | **Python + FastAPI**            |
| MCP            | **Python MCP SDK**              |
| Database       | **PostgreSQL**                  |
| Raw files      | **S3 / MinIO**                  |
| Cache          | **Redis**                       |
| Jobs           | **Prefect / Temporal**          |
| PDF extraction | PyMuPDF + structured extraction |
| XBRL           | Python XBRL parser              |
| Analytics      | Pandas/Polars                   |
| Search         | PostgreSQL FTS initially        |
| Vector search  | pgvector later                  |
| LLM            | Your preferred model            |
| Frontend       | Next.js/React                   |
| Deployment     | Docker                          |
| Monitoring     | Prometheus + Grafana            |
| API validation | Pydantic                        |

You don't need Kafka, Kubernetes, ClickHouse, a dozen microservices, or 20 agents on day one.

---

# The architecture I'd actually build for you

If this were my project, I'd make the first milestone:

```text
             ┌──────────────────┐
             │   Your Screener │
             └────────┬─────────┘
                      │
                      ▼
             ┌──────────────────┐
             │    MCP Server    │
             └────────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
  Fundamentals   Integrity      Banking
        │             │             │
        └─────────────┼─────────────┘
                      ▼
                PostgreSQL
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        NSE/BSE       RBI        SEBI
          │           │           │
          └───────────┼───────────┘
                      ▼
              Raw Document Store
```

**And every number has a source + period + timestamp + confidence.**

That is the foundation I would establish **before writing any of the remaining sector `.md` files**. Once this foundation is right, the sector work we're doing becomes essentially configuration on top of a common financial-data engine.

One particularly important point: RBI/SEBI/NSE should be treated as first-class primary sources. SEBI, for example, maintains searchable enforcement orders, including entity/title/keyword search, so your integrity engine can systematically build a regulatory-history layer rather than relying on news articles. ([Securities and Exchange Board of India][5])

**Next, I would design the actual database schema + MCP tool contracts for this architecture before coding.** That will determine exactly how NSE/BSE/RBI/SEBI data flows into your screener and prevent you from having to redesign the backend when we add the 10th sector.

[1]: https://support.screener.in/article/28-export-screen-results?utm_source=chatgpt.com "Exporting Screen results in Screener - Screener Knowledge Base"
[2]: https://www.screener.in/guides/terms/?utm_source=chatgpt.com "Guide - Screener"
[3]: https://www.nseindia.com/companies-listing/corporate-filings-application?utm_source=chatgpt.com "Corporate Filings- Equity, Debt, MF, SME- NSE India"
[4]: https://www.nseindia.com/static/market-data/corporate-data-subscription?utm_source=chatgpt.com "Paid Corporate Data - NSE India"
[5]: https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&smid=133&ssid=9&utm_source=chatgpt.com "SEBI | Orders"


Yes. I would build it in **three layers: Data → Calculation → Intelligence**, with MCP sitting above them. The most important decision is that **the LLM/agents never become the source of financial numbers**.

Here is the architecture I would actually implement.

---

# 1. Final architecture

```text
                         ┌──────────────────────────┐
                         │       User / UI           │
                         │  Stock Search / Screener  │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │       MCP Gateway         │
                         │                          │
                         │ analyze_stock             │
                         │ screen_stocks             │
                         │ get_financials            │
                         │ get_valuation              │
                         │ get_integrity              │
                         │ get_bank_metrics           │
                         └────────────┬─────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
       ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
       │ Data Service   │    │ Calculation    │    │ Intelligence   │
       │                │    │ Engine         │    │ / Agents       │
       │ canonical data │    │ CAGR           │    │                │
       │ provenance     │    │ ROE/ROA        │    │ Sector Analyst │
       │ freshness      │    │ valuation      │    │ Integrity Agent│
       └───────┬────────┘    └───────┬────────┘    └───────┬────────┘
               │                     │                     │
               └─────────────────────┼─────────────────────┘
                                     ▼
                         ┌──────────────────────────┐
                         │      PostgreSQL           │
                         │                          │
                         │ Companies                │
                         │ Securities               │
                         │ Financials               │
                         │ Metrics                  │
                         │ Ownership                │
                         │ Governance               │
                         │ Provenance               │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                 ┌──────────────┐          ┌──────────────┐
                 │ Raw Storage  │          │ Redis        │
                 │ S3 / MinIO   │          │ Cache        │
                 │              │          │              │
                 │ PDFs         │          │ Latest data  │
                 │ XBRL         │          │ MCP results  │
                 │ HTML         │          │              │
                 │ CSV          │          │              │
                 └──────┬───────┘          └──────────────┘
                        ▲
                        │
                ┌───────┴────────────────────┐
                │      Ingestion Layer        │
                │                            │
                │ NSE                        │
                │ BSE                        │
                │ RBI                        │
                │ SEBI                       │
                │ MCA                        │
                │ Company IR                 │
                └────────────────────────────┘
```

---

# 2. Do NOT make one agent per website

This is important.

Don't build:

```text
NSE Agent
BSE Agent
RBI Agent
Screener Agent
Moneycontrol Agent
...
```

Instead build **source adapters**:

```text
ingestion/
├── nse/
├── bse/
├── rbi/
├── sebi/
├── mca/
└── company_ir/
```

And agents operate at the **business responsibility** level:

```text
agents/
├── acquisition_agent
├── extraction_agent
├── validation_agent
├── integrity_agent
└── sector_analysis_agent
```

For example:

```text
Acquisition Agent
       │
       ├── NSE adapter
       ├── BSE adapter
       ├── RBI adapter
       ├── SEBI adapter
       └── Company IR adapter
```

That makes the system dramatically easier to maintain.

---

# 3. PostgreSQL should be your source of truth

I recommend PostgreSQL as the canonical database.

Don't put financial data directly into JSON files and ask agents to interpret them every time.

Your database should have roughly these domains:

```text
companies
securities

financial_periods
financial_statements
financial_metrics

market_prices
valuation_metrics

shareholding
promoter_transactions
pledges
institutional_holdings

directors
auditors
related_party_transactions
regulatory_actions
corporate_actions

sources
documents
observations
data_conflicts

sector_definitions
screening_rules
screening_runs
screening_results
```

---

# 4. Most important table: `observations`

This is what will make your system reliable.

Every financial number should ultimately become an **observation**.

For example:

```text
HDFC Bank
ROE
FY2025
18.7%
```

should not simply exist as:

```json
{
  "roe": 18.7
}
```

Instead:

```json
{
  "company_id": "HDFCBANK",
  "metric_id": "roe",
  "value": 18.7,
  "unit": "percent",

  "period_start": "2024-04-01",
  "period_end": "2025-03-31",
  "period_type": "FY",

  "reported_at": "2025-05-10",
  "available_at": "2025-05-10",
  "retrieved_at": "2025-05-11",

  "source_id": "NSE",
  "document_id": "document_123",

  "source_location": "Annual Report Page 142",

  "extraction_method": "xbrl",
  "confidence": 1.0
}
```

This gives you **auditability**.

---

# 5. Database schema

I would start with these core tables.

### `companies`

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    legal_name TEXT NOT NULL,
    common_name TEXT,
    cin TEXT,
    pan TEXT,
    industry TEXT,
    sector TEXT,
    sub_sector TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### `securities`

Because one company can have multiple securities/listings.

```sql
CREATE TABLE securities (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),

    isin TEXT UNIQUE,
    nse_symbol TEXT,
    bse_code TEXT,

    security_type TEXT,
    exchange TEXT,

    listed_at DATE,

    UNIQUE(exchange, nse_symbol)
);
```

---

# 6. Metric registry

Don't hardcode metric names throughout the application.

Create:

```text
metric_registry
```

Example:

```yaml
roe:
  name: Return on Equity
  category: profitability
  unit: percent
  entity_type: company
  calculation: net_profit / average_equity

roa:
  name: Return on Assets
  category: profitability
  unit: percent
  entity_type: company

pe:
  name: Price to Earnings
  category: valuation
  unit: ratio
  entity_type: company

pb:
  name: Price to Book
  category: valuation
  unit: ratio
  entity_type: company

gnpa_ratio:
  name: Gross NPA Ratio
  category: asset_quality
  unit: percent
  entity_type: bank

nnpa_ratio:
  name: Net NPA Ratio
  category: asset_quality
  unit: percent
  entity_type: bank

nim:
  name: Net Interest Margin
  category: banking
  unit: percent
  entity_type: bank

casa_ratio:
  name: CASA Ratio
  category: banking
  unit: percent
  entity_type: bank
```

Then your entire application uses:

```text
metric_id = "roe"
```

rather than:

```text
ROE
Return on Equity
return_on_equity
roe_percent
```

depending on which source supplied it.

---

# 7. Source-specific data → canonical data

This is where your ingestion architecture becomes powerful.

Suppose RBI says:

```text
Gross NPA Ratio
```

Company annual report says:

```text
Gross Non-Performing Assets / Gross Advances
```

Your database doesn't care.

Both map to:

```text
gnpa_ratio
```

Example:

```python
class SourceAdapter:

    def fetch(self, company):
        ...

    def parse(self, raw_document):
        ...

    def normalize(self, parsed_data):
        ...
```

Then:

```text
RBI Adapter
    ↓
Raw RBI data
    ↓
RBI Parser
    ↓
Normalized Observation
    ↓
metric_id = gnpa_ratio
```

---

# 8. Raw data must NEVER be overwritten

This is another critical rule.

Suppose NSE gives you a document on:

```text
11 September 2026
```

Store the original file:

```text
raw/
    nse/
        2026/
            09/
                11/
                    company_x/
                        financial_result.pdf
```

And metadata:

```text
documents
-----------
id
source_id
url
document_type
retrieved_at
published_at
sha256
storage_path
```

If the source later changes its document, **you still have the original version**.

That is extremely valuable for financial research.

---

# 9. Never silently resolve conflicting numbers

Suppose:

```text
NSE → ROE = 18.4%
Annual Report → ROE = 18.7%
```

Don't automatically choose one.

Create:

```text
data_conflicts
```

and mark:

```json
{
  "metric": "roe",
  "source_a": "NSE",
  "value_a": 18.4,
  "source_b": "Annual Report",
  "value_b": 18.7,
  "status": "CONFLICT"
}
```

Then your validation engine determines why.

Maybe one is:

```text
standalone
```

and the other:

```text
consolidated
```

That's precisely the kind of issue that can destroy a screener if you don't track it.

---

# 10. Separate standalone vs consolidated

Your schema should explicitly contain:

```text
statement_scope
```

with:

```text
standalone
consolidated
```

Never mix them.

For example:

```json
{
  "metric_id": "profit",
  "value": 52000,
  "statement_scope": "consolidated"
}
```

This will prevent many bad comparisons.

---

# 11. Financial statement model

I'd structure it around periods.

```text
financial_periods

company
period
statement_scope
period_type
period_start
period_end
reported_date
```

Then:

```text
financial_metrics

company_id
metric_id
period_id
value
unit
source_observation_id
```

This lets you ask:

```text
Give me HDFC Bank profit for the last 10 FYs.
```

without an LLM having to search anything.

---

# 12. Calculation engine

This should be completely separate from your agents.

Example:

```text
calculations/
├── growth.py
├── profitability.py
├── valuation.py
├── banking.py
├── cashflow.py
└── historical.py
```

For example:

```python
def cagr(start_value, end_value, years):
    return ((end_value / start_value) ** (1 / years) - 1) * 100
```

Then:

```python
profit_growth_5y = cagr(
    profit_5_years_ago,
    current_profit,
    5
)
```

The LLM should **never calculate this itself** when your engine can do it deterministically.

---

# 13. Historical valuation engine

This is particularly important because your mentor emphasizes historical P/E.

You need a time series:

```text
market_prices

security_id
date
close
adjusted_close
```

Then:

```text
valuation_history

security_id
date
pe
pb
ev_ebitda
market_cap
```

You can calculate:

```text
current P/E
10Y median P/E
5Y median P/E
10Y percentile
5Y percentile
premium/discount to median
```

For example:

```json
{
  "current_pe": 27.4,
  "historical_10y_median_pe": 21.8,
  "premium_to_median": 25.7,
  "valuation_position": "EXPENSIVE"
}
```

That is far more useful than simply:

```text
P/E < 30
```

---

# 14. Banking-specific schema

Don't put bank metrics into generic company fields.

Create banking-specific metrics:

```text
bank_metrics
```

or, preferably, keep them in the unified metric system with:

```text
entity_type = bank
```

Metrics:

```text
gnpa_ratio
nnpa_ratio
provision_coverage_ratio
slippage_ratio
credit_cost

nim
nii
popp
cost_to_income

loan_growth
deposit_growth
casa_ratio
credit_deposit_ratio

retail_loan_ratio
corporate_loan_ratio
unsecured_loan_ratio

crar
cet1
tier1
leverage_ratio
```

Then your Banking screener can declare which metrics it needs.

---

# 15. Ownership and promoter data

Separate this too.

```text
shareholding
```

Example:

```text
company_id
period_end
promoter_percentage
public_percentage
fii_percentage
dii_percentage
```

Then:

```text
promoter_transactions

company_id
security_id
date
transaction_type
quantity
price
value
source_observation_id
```

And:

```text
pledges

company_id
period_end
promoter_shares
pledged_shares
pledged_percentage
```

This lets the system identify:

```text
Promoter holding declining
+
promoter selling
+
pledge increasing
```

rather than looking at one isolated number.

---

# 16. Governance database

I'd create:

```text
governance_events
```

with:

```text
event_type
severity
event_date
description
source
document
company
```

Event types:

```text
PROMOTER_SELLING
PLEDGE_INCREASE
AUDITOR_RESIGNATION
AUDITOR_QUALIFICATION
SEBI_ACTION
RBI_ACTION
MCA_ACTION
RELATED_PARTY_CONCERN
PREFERENTIAL_ALLOTMENT
DILUTION
MANAGEMENT_CHANGE
```

Then the Integrity Agent doesn't "search the internet and form an opinion."

Instead it receives:

```text
structured events + evidence
```

and interprets them.

---

# 17. MCP tools

Your MCP server should expose **clean business-level tools**, not database operations.

Bad:

```text
run_sql()
query_table()
get_raw_html()
```

Good:

```text
get_company_profile()
get_financials()
get_growth_metrics()
get_profitability()
get_valuation()
get_historical_valuation()
get_shareholding()
get_promoter_transactions()
get_promoter_pledge()
get_governance_events()
get_regulatory_actions()
get_bank_asset_quality()
get_bank_capital()
get_bank_funding()
```

---

# 18. Most important MCP tool: `analyze_stock`

This becomes your high-level orchestration tool.

Input:

```json
{
  "symbol": "HDFCBANK",
  "exchange": "NSE",
  "sector": "banking"
}
```

Internally:

```text
analyze_stock
      │
      ├── identify company
      │
      ├── identify sector
      │
      ├── load sectors/banking.md
      │
      ├── determine required metrics
      │
      ├── retrieve canonical observations
      │
      ├── check freshness
      │
      ├── calculate derived metrics
      │
      ├── run validation
      │
      ├── run integrity analysis
      │
      ├── calculate valuation position
      │
      ├── compare peers
      │
      └── generate structured result
```

---

# 19. MCP response should be structured

Don't have MCP return a giant paragraph.

Return something like:

```json
{
  "company": {
    "name": "Example Bank",
    "symbol": "EXAMPLE"
  },

  "data_quality": {
    "confidence": 0.97,
    "conflicts": 0,
    "stale_metrics": 1
  },

  "fundamental_quality": {
    "roe": 18.2,
    "average_roe_5y": 17.5,
    "roa": 1.8,
    "average_roa_5y": 1.7
  },

  "growth": {
    "profit_growth_3y": 14.2,
    "profit_growth_5y": 13.1,
    "eps_growth_5y": 12.8
  },

  "asset_quality": {
    "gnpa": 1.2,
    "nnpa": 0.3,
    "credit_cost": 0.8
  },

  "capital": {
    "cet1": 16.4,
    "crar": 18.1
  },

  "valuation": {
    "pe": 21.4,
    "pb": 3.2,
    "historical_10y_median_pe": 18.9,
    "valuation_position": "ABOVE_MEDIAN"
  },

  "integrity": {
    "promoter_pledge": 0,
    "promoter_holding_trend": "STABLE",
    "red_flags": []
  },

  "peer_position": {
    "roe_rank": 2,
    "valuation_rank": 4
  }
}
```

Then the LLM can explain it.

---

# 20. Your `.md` files should be configuration, not data

This is important for the system you're building.

For example:

```text
sectors/
└── banking.md
```

should describe:

```text
Sector
Overview
Screening Logic
Fundamental Metrics
Notes
```

But it should **not** contain:

```text
HDFC Bank ROE = 18.2%
```

Instead:

```text
metric_id: average_roe_5y
operator: ">="
value: 12
```

Then the engine resolves that metric from PostgreSQL.

---

# 21. Your screening rule format

Use the finalized schema you already established:

```yaml
screening_logic:

  - metric: market_cap
    operator: ">"
    value: 5000

  - metric: average_roe_5y
    operator: ">="
    value: 12

  - metric: average_roa_5y
    operator: ">="
    value: 1

  - metric: profit_growth_3y
    operator: ">="
    value: 8

  - metric: profit_growth_5y
    operator: ">="
    value: 10

  - metric: profit_growth_10y
    operator: ">="
    value: 10

  - metric: eps_growth_5y
    operator: ">="
    value: 10

  - metric: pledged_percentage
    operator: "<="
    value: 5
```

Every rule is:

```text
metric
operator
value
```

And everything is AND.

No ambiguous:

```text
"good ROE"
"low debt"
"reasonable valuation"
```

inside the executable screening engine.

---

# 22. Important distinction: screening vs analysis

I would actually have **two engines**.

### Screening Engine

Answers:

> Does this stock satisfy my predefined rules?

```text
PASS
FAIL
INSUFFICIENT_DATA
```

### Analysis Engine

Answers:

> Is this stock fundamentally attractive?

It can consider:

```text
quality
growth
asset quality
management
valuation
historical valuation
peer position
red flags
```

This distinction is extremely important.

A company failing a screening threshold doesn't necessarily mean it's a bad company.

---

# 23. Data freshness engine

Every metric needs freshness metadata.

For example:

```text
Price              → real-time/latest trading day
Shareholding       → latest available quarter
Financial results  → latest reported quarter/FY
GNPA               → latest reported period
SEBI action        → continuously updated
Historical P/E     → calculated daily
```

So every MCP result should contain:

```json
{
  "value": 18.7,
  "period_end": "2025-03-31",
  "reported_at": "2025-05-10",
  "retrieved_at": "2025-05-11"
}
```

This prevents a very dangerous situation:

> Current stock price + two-year-old financial data being presented as if they're current.

---

# 24. Data confidence

Give every observation a confidence score.

For example:

```text
Regulator/exchange/company primary
        ↓
       1.00

Two independent primary sources agree
        ↓
       0.98

Audited annual report extraction
        ↓
       0.95

Reputable financial database
        ↓
       0.85

PDF extraction ambiguity
        ↓
       0.70

Web article
        ↓
       0.50

LLM inference
        ↓
       0.20
```

The exact numbers can be tuned later.

The important thing is that:

**inferred data must never look identical to reported data.**

---

# 25. Agent architecture

I would use only four major agents initially.

### 1. Acquisition Agent

```text
What data do we need?
Where can we obtain it?
Has the source changed?
Retrieve document/data.
```

### 2. Extraction Agent

```text
PDF
XBRL
HTML
CSV
        ↓
structured observations
```

But even here, deterministic parsers should handle structured formats wherever possible.

### 3. Integrity Agent

```text
Promoter
Auditor
Pledge
Related parties
SEBI
Regulatory events
Corporate actions
```

Every conclusion must have evidence.

### 4. Sector Analyst Agent

```text
banking.md
+
validated data
+
calculated metrics
+
peer data
        ↓
analysis
```

---

# 26. The LLM should never do this

Avoid:

```text
Agent searches Google
       ↓
finds HDFC Bank ROE
       ↓
finds another website's ROE
       ↓
calculates CAGR
       ↓
decides it's good
```

Instead:

```text
Source
 ↓
Raw document
 ↓
Parser
 ↓
Canonical observation
 ↓
Validation
 ↓
Calculation engine
 ↓
MCP
 ↓
LLM explanation
```

That is the difference between an **AI financial toy** and a proper financial-data engine.

---

# 27. Repository structure

I would now make the repository like this:

```text
fundamental-engine/
│
├── apps/
│   ├── api/
│   ├── mcp/
│   └── web/
│
├── config/
│   ├── sources.yaml
│   ├── metrics.yaml
│   └── settings.yaml
│
├── sectors/
│   ├── banking.md
│   ├── nbfc.md
│   ├── automobile.md
│   ├── fmcg.md
│   ├── it.md
│   └── pharma.md
│
├── ingestion/
│   ├── base.py
│   ├── nse/
│   ├── bse/
│   ├── rbi/
│   ├── sebi/
│   ├── mca/
│   └── company_ir/
│
├── parsers/
│   ├── xbrl/
│   ├── pdf/
│   ├── html/
│   └── csv/
│
├── models/
│   ├── company.py
│   ├── security.py
│   ├── financial.py
│   ├── metric.py
│   ├── ownership.py
│   ├── governance.py
│   └── source.py
│
├── calculations/
│   ├── growth.py
│   ├── profitability.py
│   ├── valuation.py
│   ├── banking.py
│   └── historical.py
│
├── validation/
│   ├── freshness.py
│   ├── completeness.py
│   ├── cross_source.py
│   └── consistency.py
│
├── integrity/
│   ├── promoter.py
│   ├── pledge.py
│   ├── auditor.py
│   ├── related_party.py
│   └── regulatory.py
│
├── agents/
│   ├── acquisition.py
│   ├── extraction.py
│   ├── integrity.py
│   └── sector_analysis.py
│
├── mcp/
│   ├── fundamental.py
│   ├── valuation.py
│   ├── ownership.py
│   ├── governance.py
│   ├── banking.py
│   └── analysis.py
│
├── database/
│   ├── migrations/
│   └── schema/
│
├── tests/
│   ├── calculations/
│   ├── ingestion/
│   ├── validation/
│   └── sectors/
│
└── docker-compose.yml
```

---

# 28. Tech stack I would use

For your use case:

| Component             | Choice                           |
| --------------------- | -------------------------------- |
| Backend               | Python                           |
| API                   | FastAPI                          |
| MCP                   | Python MCP SDK                   |
| Database              | PostgreSQL                       |
| Raw storage           | S3 / MinIO                       |
| Cache                 | Redis                            |
| Jobs                  | Prefect initially                |
| Structured processing | Polars/Pandas                    |
| PDF                   | PyMuPDF + specialized extraction |
| XBRL                  | Python XBRL tooling              |
| Validation            | Pydantic                         |
| Search                | PostgreSQL FTS initially         |
| Vector search         | pgvector later                   |
| Containers            | Docker                           |
| Monitoring            | Prometheus + Grafana             |

I would **not** introduce Kafka, Kubernetes, Spark, etc. initially. You don't need that complexity for the first version.

---

# 29. Build Banking first

Don't try to ingest all 5,000+ companies immediately.

Build this:

```text
             BANKING MVP

HDFC Bank
ICICI Bank
SBI
Axis Bank
Kotak Bank
IndusInd Bank
Federal Bank
Karnataka Bank
AU Small Finance Bank
Bank of Baroda
```

Then make the entire pipeline work:

```text
NSE/BSE
   ↓
RBI
   ↓
SEBI
   ↓
Company annual reports
   ↓
Raw storage
   ↓
Extraction
   ↓
PostgreSQL
   ↓
Validation
   ↓
Banking calculations
   ↓
Banking screener
   ↓
MCP
   ↓
AI analysis
```

Only after this works reliably should you scale to every Indian listed company.

---

# 30. The end-state I want you to build toward

Ultimately, the user should be able to ask:

> **Analyze HDFC Bank according to my fundamental framework.**

And your system should produce:

```text
                    HDFC BANK
                 Fundamental Analysis

DATA QUALITY
✓ Primary sources
✓ No unresolved conflicts
✓ Latest financial period
Confidence: 97%

────────────────────────────────

FUNDAMENTAL QUALITY
ROE                  18.2%
5Y Avg ROE           17.5%
ROA                   1.8%
5Y Avg ROA            1.7%

────────────────────────────────

GROWTH
3Y Profit CAGR       14.2%
5Y Profit CAGR       13.1%
10Y Profit CAGR      ...

────────────────────────────────

ASSET QUALITY
GNPA                  1.2%
NNPA                  0.3%
Credit Cost           0.8%
Slippage              ...

────────────────────────────────

CAPITAL
CET1                 16.4%
CRAR                 18.1%

────────────────────────────────

MANAGEMENT / INTEGRITY
Promoter pledge        0%
Promoter trend        ...
Auditor               ...
Regulatory actions    ...

────────────────────────────────

VALUATION
Current P/E           21.4
10Y Median P/E        18.9
Premium                13.2%

Current P/B             3.2
Historical P/B          ...

────────────────────────────────

PEER COMPARISON
ROE                   ...
ROA                   ...
GNPA                  ...
P/B                   ...
P/E                   ...

────────────────────────────────

SCREENING
✓ Profit growth
✓ ROE
✓ ROA
✓ EPS growth
✓ Pledge

OVERALL
Fundamental Quality:  ...
Asset Quality:        ...
Growth:               ...
Management:            ...
Valuation:             ...

DATA CONFIDENCE: 97%
```

And **every number should be traceable back to an actual source/document/period**.

That is the architecture I recommend.

### The next thing I would build

Before writing the agents, I would define **three concrete artifacts**:

1. `schema.sql` — the complete PostgreSQL schema
2. `metric_registry.yaml` — every canonical metric, including Banking
3. `mcp_contracts.md` — exact input/output JSON schemas for every MCP tool

Then we can implement the **NSE → raw storage → parser → PostgreSQL → MCP** pipeline for the first few banks. That gives you the foundation on which every subsequent sector can be plugged in.
