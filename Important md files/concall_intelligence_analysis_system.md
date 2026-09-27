# Concall Intelligence & Management Guidance Analysis System

## Objective

Build a **Concall Intelligence Engine** for every NSE-listed stock that automatically:

1. Fetches earnings-call transcripts and related corporate announcements.
2. Parses management commentary and analyst Q&A.
3. Extracts **forward-looking guidance**.
4. Identifies whether management commentary is positive, neutral, cautious or negative.
5. Tracks every guidance item across quarters.
6. Detects upgrades, downgrades, reiterations and withdrawals of guidance.
7. Measures management's confidence and certainty in its language.
8. Compares what management previously said with what actually happened.
9. Identifies important future business developments.
10. Creates a searchable historical management-communication database.
11. Produces a stock-level **Management Commentary / Concall Scorecard**.

The system should use:

```text
NSE Corporate Filings
        ↓
Transcript Ingestion
        ↓
Document Parser
        ↓
Chunking
        ↓
EmbeddingGemma
        ↓
Vector Database
        ↓
Relevant Context Retrieval
        ↓
Llama
        ↓
Structured Concall Extraction
        ↓
Deterministic Guidance Tracker
        ↓
Management Trend / Tone Analysis
        ↓
Stock-Level Concall Report
```

---

# 1. Why Concall Analysis Is Different From Normal NLP

Do NOT build this as a simple:

```text
Transcript → Sentiment → Positive/Negative
```

That would be too weak for investment research.

A good concall engine must distinguish:

```text
Historical fact
vs
Current performance
vs
Forward guidance
vs
Management aspiration
vs
Management expectation
vs
Conditional statement
vs
Analyst question
vs
Management answer
```

For example:

> "We expect EBITDA margin to remain between 20.5% and 21%."

This is a **quantifiable forward guidance**.

Whereas:

> "We believe the long-term opportunity remains very strong."

This is a **positive qualitative outlook**, not numerical guidance.

And:

> "If demand improves, margins could recover."

This is **conditional commentary**, not firm guidance.

---

# 2. Data Source — NSE

The primary ingestion source should be **NSE Corporate Filings / Corporate Announcements**.

NSE's corporate-filings interface exposes company announcements and allows filtering by company, subject and date range. Earnings-call transcripts appear under categories such as:

```text
Analysts/Institutional Investor Meet/Con. Call Updates
```

NSE examples show actual transcript filings for listed companies. urlNSE Corporate Filings – Announcementshttps://www.nseindia.com/companies-listing/corporate-filings-announcements

NSE also provides an End-of-Day Corporate Announcement data product for scalable institutional ingestion. The official NSE page currently describes corporate-announcement data containing company fundamentals, corporate announcements and shareholding-pattern information, delivered through SFTP. citeturn0search9

### Important

Do not depend on a third-party transcript provider as the primary source.

Recommended source priority:

```text
1. NSE filing
2. Company filing / investor-relations page
3. BSE filing
4. Third-party source only as fallback
```

The source must be stored with every extracted statement.

---

# 3. Universe-Level Ingestion

The system should work for:

```text
ALL NSE-listed stocks
```

Not just stocks already selected by the fundamental screener.

## Pipeline

```text
NSE Universe
     ↓
Identify New Corporate Announcements
     ↓
Filter Concall / Investor Meet Filings
     ↓
Download Transcript
     ↓
Normalize Document
     ↓
Deduplicate
     ↓
Store Raw Document
     ↓
Parse
     ↓
Embed
     ↓
Extract
```

The system should run after every market-day filing cycle.

---

# 4. Concall Document Data Model

Every transcript should have:

```json
{
  "company_id": "",
  "nse_symbol": "",
  "company_name": "",
  "quarter": "Q1 FY27",
  "financial_period": "",
  "call_date": "",
  "filing_date": "",
  "source": "NSE",
  "source_url": "",
  "document_hash": "",
  "document_type": "earnings_call_transcript",
  "language": "English",
  "management_participants": [],
  "analysts": [],
  "raw_document_path": "",
  "parsed_text_path": "",
  "embedding_status": "",
  "extraction_status": ""
}
```

---

# 5. Transcript Parsing

The parser should identify speakers.

Example:

```text
Moderator
CEO
CFO
COO
Investor Relations
Analyst
Management
```

Store every utterance as:

```json
{
  "speaker": "CEO",
  "speaker_name": "",
  "speaker_role": "CEO",
  "section": "opening_remarks",
  "text": "",
  "page": 10,
  "sequence": 143
}
```

This is extremely important.

The system must know whether a statement came from:

```text
CEO
CFO
Other Management
Analyst
Moderator
```

An analyst saying:

> "Are you expecting 20% growth?"

must never become management guidance.

---

# 6. Section Detection

Automatically classify transcript sections:

```text
1. Opening Remarks
2. Business Update
3. Revenue Commentary
4. Margin Commentary
5. Segment Commentary
6. Order Book / Pipeline
7. Capex
8. Debt
9. Cash Flow
10. Management Outlook
11. Guidance
12. Analyst Q&A
13. Closing Remarks
```

Q&A should be further split into:

```text
QUESTION
ANSWER
```

---

# 7. Where EmbeddingGemma Fits

**Yes — EmbeddingGemma is highly useful here.**

Do NOT use EmbeddingGemma to decide whether management is positive.

Its primary role should be:

```text
Semantic Search
+
Historical Retrieval
+
Similarity Matching
+
Guidance Tracking
+
Context Retrieval
```

## EmbeddingGemma Pipeline

```text
Transcript
   ↓
Chunks
   ↓
EmbeddingGemma
   ↓
Vector Database
```

Store embeddings for:

- Full paragraphs
- Management answers
- Guidance statements
- Outlook statements
- Business updates
- Analyst questions
- Guidance-related historical statements

---

# 8. Why Embeddings Are Critical

Suppose a company said:

### Q1 FY26

> "We expect margins to be around 18% for the year."

### Q2 FY26

> "We continue to maintain our margin expectation."

### Q3 FY26

> "We now expect margins closer to 19%."

### Q4 FY26

> Actual margin = 19.2%

The system needs to connect all four statements.

Exact keyword search is insufficient.

EmbeddingGemma can retrieve semantically similar historical statements such as:

```text
"margin expectation"
"margin outlook"
"EBITDA margin guidance"
"profitability target"
"operating margin trajectory"
```

even when the wording changes.

---

# 9. Vector Database Schema

Recommended:

```text
concall_chunks
----------------------------
id
company_id
quarter
call_date
speaker
speaker_role
section
chunk_text
embedding
page_number
source_url
document_id
```

Recommended metadata filters:

```text
company_id
financial_year
quarter
speaker_role
statement_type
guidance_category
```

---

# 10. Embedding Collections

Use separate logical collections or metadata namespaces:

### Collection A — Transcript

All transcript chunks.

### Collection B — Guidance

Only forward-looking statements.

### Collection C — Management Claims

Historical statements made by management.

### Collection D — Q&A

Questions and management answers.

### Collection E — Business Themes

Statements around:

```text
Demand
Pricing
Margins
Capex
Hiring
Utilization
Order Book
Exports
New Products
Expansion
Debt
M&A
Regulation
Competition
```

---

# 11. Where Llama Fits

Use Llama as the **reasoning / extraction / interpretation layer**.

Do not send the entire transcript blindly to Llama.

Instead:

```text
Transcript
    ↓
EmbeddingGemma
    ↓
Relevant chunks
    ↓
Llama
```

Llama should receive:

```text
Current statement
+
speaker metadata
+
relevant historical statements
+
previous guidance
+
actual result
```

This creates a much stronger system.

---

# 12. Core Llama Tasks

Llama should perform:

### A. Guidance Extraction

Identify:

- Revenue guidance
- EBITDA guidance
- EBIT guidance
- Margin guidance
- PAT guidance
- EPS guidance
- Volume guidance
- Order intake guidance
- Order book guidance
- Capex guidance
- Debt guidance
- ROE/ROCE guidance
- Store additions
- Capacity additions
- Production targets
- Utilization targets
- Headcount guidance
- Cost guidance

### B. Qualitative Outlook Extraction

Identify:

- Demand outlook
- Industry outlook
- Pricing outlook
- Competitive environment
- New product outlook
- Geographic outlook
- Segment outlook
- Regulatory outlook
- Technology outlook

### C. Tone / Confidence

Identify:

```text
Positive
Cautiously Positive
Neutral
Cautiously Negative
Negative
```

and separately:

```text
High Confidence
Medium Confidence
Low Confidence
Conditional
Aspirational
```

These are NOT the same thing.

---

# 13. Guidance Object

Every guidance statement should become a structured object.

```json
{
  "company_id": "",
  "quarter": "Q1 FY27",
  "speaker": "CEO",
  "speaker_role": "CEO",

  "category": "EBIT_margin",

  "statement": "We are confident of achieving EBITDA margin of 20.5% to 21% on a consolidated basis.",

  "guidance_type": "quantitative",

  "period": "FY27",

  "target": {
    "low": 20.5,
    "high": 21.0,
    "unit": "percent"
  },

  "direction": "positive",

  "confidence": "high",

  "certainty": "explicit",

  "conditional": false,

  "status": "reiterated",

  "source": {
    "document_id": "",
    "page": 10
  }
}
```

---

# 14. Guidance Categories

Create a controlled taxonomy.

## Financial

```text
Revenue
Revenue Growth
EBITDA
EBITDA Margin
EBIT
EBIT Margin
PAT
PAT Margin
EPS
ROE
ROCE
FCF
FCF/PAT
```

## Operating

```text
Volume
Utilization
Capacity
Production
Store Count
Customers
Headcount
Attrition
Order Intake
Order Book
Pipeline
```

## Capital Allocation

```text
Capex
Debt
Net Debt
Dividend
Buyback
M&A
```

## Business

```text
Demand
Pricing
Market Share
Geography
Segments
Product Launch
Expansion
New Capacity
```

---

# 15. Guidance Status

Every new statement should be compared with the previous guidance.

Possible status:

```text
NEW
REITERATED
UPGRADED
DOWNGRADED
WITHDRAWN
DELAYED
ACHIEVED
MISSED
PARTIALLY_ACHIEVED
NO_LONGER_GUIDED
```

Example:

### Previous

```text
FY27 EBITDA margin: 18–19%
```

### Current

```text
FY27 EBITDA margin: 19–20%
```

System:

```text
status = UPGRADED
previous = 18–19%
current = 19–20%
```

---

# 16. Guidance Change Engine

Do NOT ask Llama to decide numerical upgrades where deterministic comparison is possible.

Example:

```text
Previous midpoint = 18.5%
Current midpoint = 19.5%
```

Calculation engine:

```text
Guidance Change = +100 bps
Status = UPGRADED
```

Llama only explains the management commentary around it.

---

# 17. Guidance Confidence Engine

Separate:

### Positive Tone

```text
strongly confident
very strong demand
exceptional growth
well positioned
robust growth
ahead of plan
```

### Weak / Cautious Tone

```text
challenging
uncertain
cautious
soft
muted
volatile
remains difficult
we are watching
too early to call
```

### High Certainty

```text
we will
we expect
we remain confident
we are on track
we reiterate
we are committed to
```

### Low Certainty

```text
we believe
we think
potentially
could
may
if
subject to
depending on
we would expect
```

Important:

**Do not equate positive words with high confidence.**

---

# 18. Management Tone Score

Generate a deterministic + Llama-assisted score.

Example:

```text
Management Tone
────────────────────────
Growth Outlook       +2
Demand               +2
Margins              +2
Order Book           +2
Capex                +1
Industry Outlook     +1
Risk Commentary      -1
────────────────────────
Net Tone             +9
```

Possible final classification:

```text
Very Positive
Positive
Mildly Positive
Neutral
Mildly Negative
Negative
Very Negative
```

But this score must be based on explicit extracted evidence.

---

# 19. More Important Than Tone: Guidance Quality

The system should calculate:

```text
Guidance Quality
```

based on:

1. Specificity
2. Quantifiability
3. Time horizon
4. Management confidence
5. Historical accuracy
6. Consistency
7. Subsequent achievement

Example:

```text
"Demand remains strong."

Guidance Quality = Low
```

Whereas:

```text
"We expect FY27 EBITDA margin of 20.5–21%."

Guidance Quality = High
```

---

# 20. Management Credibility Tracker

This is one of the most valuable features.

For every management guidance:

```text
Guidance Given
       ↓
Future Result
       ↓
Actual vs Guidance
       ↓
Track Accuracy
```

Example:

| Quarter | Guidance | Actual | Result |
|---|---:|---:|---|
| Q1 | 18–19% | 18.2% | Achieved |
| Q2 | 18–19% | 18.8% | Achieved |
| Q3 | 19–20% | 18.5% | Missed |
| Q4 | 19–20% | 19.4% | Achieved |

Then calculate:

```text
Guidance Hit Rate
Guidance Miss Rate
Average Positive Surprise
Average Negative Surprise
```

---

# 21. Management Credibility Score

Example:

```text
Management Guidance Credibility
────────────────────────────────
Revenue Guidance Accuracy      87%
Margin Guidance Accuracy       91%
Capex Guidance Accuracy        78%
Order Book Guidance Accuracy   84%
────────────────────────────────
Overall                         85%
```

This becomes a powerful input into the overall fundamental analysis.

---

# 22. Management Promise Tracker

Not every important statement is numerical.

Examples:

```text
"We will launch the new plant in Q3."

"We expect the new facility to reach 70% utilization."

"We expect the acquired company to become margin accretive."

"We expect the integration to complete by December."

"We expect the new product to contribute meaningfully next year."
```

Create:

```json
{
  "promise": "",
  "target_date": "",
  "expected_outcome": "",
  "status": "pending",
  "source_quarter": "",
  "verification_metric": ""
}
```

Then verify in subsequent quarters.

---

# 23. Future Events Tracker

Extract future events:

```text
Plant commissioning
Capacity expansion
Product launch
Acquisition integration
New geography
New customer
Large contract
Store opening
Regulatory approval
Debt repayment
Capex completion
Hiring
Margin improvement
Cost reduction
```

Each becomes a tracked event.

---

# 24. "What Management Said Last Quarter" Engine

At the beginning of every new concall analysis:

```text
Current Concall
      ↓
Retrieve previous guidance
      ↓
Retrieve previous promises
      ↓
Retrieve relevant historical statements
      ↓
Compare with current commentary
```

Output:

```text
LAST QUARTER → THIS QUARTER

Revenue guidance:
Maintained

Margin guidance:
Upgraded

Capex:
Delayed

New plant:
On track

Demand:
Improved

Order pipeline:
Strengthened
```

---

# 25. Contradiction Detection

This is essential.

Example:

### Q1

> "We expect no major pricing pressure."

### Q2

> "Pricing pressure has increased materially."

System:

```text
CONTRADICTION / CHANGE IN MANAGEMENT VIEW
```

Another example:

### Q1

> "We expect capacity commissioning in Q3."

### Q2

> "Commissioning has been pushed to Q4."

System:

```text
TIMELINE DELAY
```

---

# 26. Management Language vs Actual Data

The Concall Engine should connect with the Fundamental Engine.

Example:

Management:

> "Margins will expand meaningfully."

Financial data:

```text
OPM:
Q1   16.2%
Q2   16.1%
Q3   15.7%
```

System:

```text
MANAGEMENT GUIDANCE
      ↓
EXPECTED MARGIN EXPANSION

ACTUAL DATA
      ↓
MARGIN DECLINE

STATUS
      ↓
GUIDANCE UNDER PRESSURE
```

This is far more useful than sentiment analysis.

---

# 27. Concall-to-Financial Verification

Every important statement should eventually be mapped to an observable metric.

Example:

```text
Management Claim
        ↓
Observable Metric
```

Examples:

```text
"Demand is strong"
        ↓
Revenue Growth / Order Intake

"Margins will improve"
        ↓
EBITDA Margin / EBIT Margin

"Working capital will improve"
        ↓
CCC / Receivable Days / FCF

"Capacity utilization will increase"
        ↓
Utilization %

"Debt will reduce"
        ↓
Net Debt

"New product will scale"
        ↓
Product Revenue
```

This creates a **Management vs Reality Engine**.

---

# 28. Concall RAG Architecture

Use Retrieval-Augmented Generation.

```text
                    USER / PIPELINE
                           |
                           v
                  Current Transcript
                           |
                           v
                     Chunking
                           |
                           v
                    EmbeddingGemma
                           |
                           v
                     Vector DB
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
   Prior Guidance    Similar Statements   Relevant Q&A
          |                |                |
          +----------------+----------------+
                           |
                           v
                         Llama
                           |
                           v
                  Structured JSON
                           |
                           v
                 Deterministic Engine
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
         Guidance       Promises      Tone/Confidence
         Tracker         Tracker          Analysis
             |             |             |
             +-------------+-------------+
                           |
                           v
                 Management Scorecard
```

---

# 29. Retrieval Strategy

For each current guidance statement:

### Retrieval 1

Retrieve previous guidance for the same metric.

```text
company_id = same
category = same
```

### Retrieval 2

Semantic search for similar historical statements.

### Retrieval 3

Retrieve actual financial result associated with the previous guidance.

### Retrieval 4

Retrieve management commentary explaining deviations.

This gives Llama enough context to reason.

---

# 30. Example — Coforge

The provided Coforge Q1 FY27 transcript demonstrates exactly why this architecture is useful.

Management stated that the previously shared FY27 outlook remained unchanged and gave:

```text
Consolidated EBITDA margin: 20.5–21%
Standalone EBIT margin: 16.5–17%
Consolidated EBIT margin: 15.5% or higher
FCF/PAT: 100%+
```

These are strong examples of structured quantitative guidance.

The transcript also contains statements that Encora integration was ahead of plan and that management expected to surpass the previously shared 15.5% consolidated EBIT-margin guidance. These are distinct from the formal numerical guidance and should be captured as **guidance status / confidence commentary** rather than mixed together. fileciteturn0file0L251-L266

The same call also contains a useful example of management explicitly rejecting a hard Q2 revenue-growth number while still describing Q2 onward growth as robust. That distinction is extremely important:

```text
Hard numerical guidance:
NO

Qualitative positive outlook:
YES
```

fileciteturn0file0L662-L669

---

# 31. Concall Output JSON

Recommended final object:

```json
{
  "company": "",
  "quarter": "",
  "call_date": "",

  "overall_tone": {
    "classification": "positive",
    "score": 8.2,
    "confidence": "high"
  },

  "guidance": [],

  "guidance_changes": [],

  "future_events": [],

  "management_promises": [],

  "business_outlook": {
    "demand": "",
    "pricing": "",
    "margins": "",
    "capex": "",
    "industry": "",
    "competition": "",
    "geography": "",
    "segments": ""
  },

  "risks": [],

  "positive_signals": [],

  "negative_signals": [],

  "contradictions": [],

  "previous_guidance_status": [],

  "management_credibility": {},

  "key_takeaways": [],

  "things_to_monitor": []
}
```

---

# 32. Guidance JSON

Use a normalized schema:

```json
{
  "metric": "EBITDA Margin",

  "period": "FY27",

  "previous_guidance": {
    "low": 19,
    "high": 20
  },

  "current_guidance": {
    "low": 20.5,
    "high": 21
  },

  "change": {
    "midpoint_bps": 125,
    "status": "UPGRADED"
  },

  "management_language": {
    "tone": "very_positive",
    "confidence": "high",
    "certainty": "explicit"
  },

  "actual": null,

  "verification_status": "pending",

  "source": {
    "quarter": "Q1 FY27",
    "page": 10
  }
}
```

---

# 33. Concall Dashboard

For every stock:

```text
                 MANAGEMENT COMMENTARY
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        v                v                v
      TONE            GUIDANCE         CREDIBILITY
      +8.2             ↑ 3              86%
        │                │                │
        └────────────────┼────────────────┘
                         │
                         v
                  FUTURE OUTLOOK
                         │
             ┌───────────┼───────────┐
             v           v           v
           Growth      Margin      Demand
             +++         ++          +++
```

---

# 34. Quarterly Stock Timeline

Every stock should have a management timeline:

```text
FY25 Q1
   ↓
FY25 Q2
   ↓
FY25 Q3
   ↓
FY25 Q4
   ↓
FY26 Q1
   ↓
FY26 Q2
   ↓
FY26 Q3
   ↓
FY26 Q4
   ↓
FY27 Q1
```

Each quarter stores:

```text
Tone
Guidance
Changes
Promises
Risks
Key themes
Actual vs prior guidance
```

This lets the user see how management thinking evolved.

---

# 35. Management Sentiment Timeline

Do not show only one sentiment number.

Show:

```text
Q1   +4.2
Q2   +5.8
Q3   +7.1
Q4   +6.4
Q1   +8.2
```

Then identify:

```text
Tone improving
Tone deteriorating
Tone stable
High volatility
```

But always display the evidence behind the score.

---

# 36. Theme-Level Sentiment

A company can be positive overall but negative on one important area.

Therefore calculate separately:

```text
Demand             +8
Revenue             +7
Margins             +6
Pricing             +2
Capex               +5
Debt                -2
Competition         -1
Industry            +4
```

This is much more useful than a single sentiment score.

---

# 37. Analyst Question Intelligence

The questions themselves contain valuable information.

Track recurring analyst concerns:

```text
Margin pressure
Demand weakness
Pricing
Capex
Debt
Competition
Order book
Management credibility
Working capital
Guidance
```

If the same concern appears repeatedly:

```text
Q1: Analyst asks about margin pressure
Q2: Analyst asks about margin pressure
Q3: Analyst asks about margin pressure
```

Generate:

```text
RECURRING INVESTOR CONCERN
```

Then compare management's responses over time.

---

# 38. Unanswered / Avoided Questions

Detect cases where management:

- Avoids a numerical answer
- Gives a qualitative answer instead
- Says "too early to comment"
- Refuses to provide guidance
- Redirects the question
- Provides a broad answer instead of the requested metric

This should NOT automatically be treated as negative.

Classification:

```text
ANSWERED
PARTIALLY ANSWERED
NON-COMMITTAL
DECLINED
DEFERRED
```

This is a separate dimension from sentiment.

---

# 39. Management Confidence Language

Create a confidence lexicon, but let Llama interpret context.

### Strong

```text
confident
very confident
firmly
on track
will deliver
committed
reiterate
expect to achieve
remain confident
```

### Moderate

```text
expect
believe
anticipate
likely
should
we see
we think
```

### Weak / Conditional

```text
could
may
potentially
if
subject to
depending on
too early
cannot comment
uncertain
```

Never classify based on a single keyword alone.

---

# 40. Future Guidance Database

Create a dedicated table:

```text
management_guidance
────────────────────────────────────────
id
company_id
quarter
date
metric
category
period
target_low
target_high
target_value
unit
statement
speaker
tone
confidence
certainty
conditional
status
previous_guidance_id
actual_value
verification_status
source_document
source_page
```

This becomes the central historical management database.

---

# 41. Promise Database

```text
management_promises
────────────────────────────────
id
company_id
quarter
promise
category
target_date
expected_metric
expected_value
status
actual_value
verification_date
source_document
source_page
```

Statuses:

```text
PENDING
ON_TRACK
ACHIEVED
DELAYED
MISSED
PARTIALLY_ACHIEVED
CANCELLED
```

---

# 42. Management Credibility Database

```text
management_credibility
──────────────────────────────
company_id
metric
guidance_count
achieved_count
missed_count
partially_achieved_count
hit_rate
avg_positive_surprise
avg_negative_surprise
last_updated
```

---

# 43. Agent Architecture

Do not make one giant agent.

Recommended:

```text
                    ORCHESTRATOR
                         |
       +-----------------+------------------+
       |                 |                  |
       v                 v                  v
  NSE Ingestion      Transcript        Financial Data
     Agent              Agent              Agent
       |                 |                  |
       +-----------------+------------------+
                         |
                         v
                  Embedding Agent
                   EmbeddingGemma
                         |
                         v
                    Vector DB
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
 Guidance Agent     Theme Agent     Q&A Agent
        |                |                |
        +----------------+----------------+
                         |
                         v
                    Llama Analyst
                         |
                         v
              Verification Engine
                         |
                         v
              Management Scorecard
                         |
                         v
                  Report Generator
```

---

# 44. What EmbeddingGemma Should NOT Do

Do not use it for:

```text
Numerical calculations
Guidance upgrade/downgrade
Sentiment decision by itself
Financial scoring
Management credibility calculation
Final investment conclusion
```

Use it for retrieval and similarity.

---

# 45. What Llama Should NOT Do

Do not allow Llama to directly calculate:

```text
CAGR
Margins
Guidance midpoint changes
Actual vs guidance
Hit rates
Financial ratios
Score calculations
```

Those belong to deterministic code.

Llama should interpret verified facts.

---

# 46. Deterministic Verification Layer

This layer is essential.

```text
Llama Extraction
       ↓
Schema Validation
       ↓
Numeric Validation
       ↓
Source Validation
       ↓
Historical Comparison
       ↓
Final Structured Data
```

For example:

If Llama extracts:

```text
Previous EBITDA margin = 18%
Current EBITDA margin = 17%
```

Code calculates:

```text
Status = DOWNGRADED
Change = -100 bps
```

Llama does not decide this.

---

# 47. Confidence / Evidence Model

Every extracted statement should have:

```text
source
page
speaker
speaker_role
exact_statement
extraction_confidence
```

Example:

```json
{
  "statement": "We remain confident of achieving 20.5% to 21% EBITDA margin.",
  "speaker": "CEO",
  "speaker_role": "CEO",
  "page": 10,
  "source": "NSE",
  "extraction_confidence": 0.97
}
```

This makes the system auditable.

---

# 48. Hallucination Protection

For every Llama-generated statement:

```text
Generated Interpretation
        ↓
Evidence Retrieval
        ↓
Evidence Match
```

If no supporting evidence exists:

```text
DO NOT GENERATE CLAIM
```

Recommended output:

```text
insufficient_evidence = true
```

---

# 49. Concall Report Format

For each company:

## Management Outlook

```text
Overall Tone: Positive
Confidence: High

Management remains constructive on demand and expects
continued growth. Margin guidance has been reiterated/upgraded.
```

## Guidance Changes

| Metric | Previous | Current | Change | Status |
|---|---:|---:|---:|---|
| Revenue | | | | |
| EBITDA Margin | | | | |
| EBIT Margin | | | | |
| FCF/PAT | | | | |

## Future Events

| Event | Expected Timing | Status |
|---|---|---|
| Capacity | | |
| Product | | |
| M&A integration | | |

## Management vs Previous Guidance

```text
Revenue          Maintained
Margins          Upgraded
Capex            Delayed
Demand           Improved
```

## Risks

```text
1.
2.
3.
```

## Key Takeaways

```text
1.
2.
3.
```

---

# 50. Final "Management View" Scorecard

Recommended:

```text
MANAGEMENT COMMENTARY SCORECARD
──────────────────────────────────

Demand Outlook              8/10
Revenue Outlook             8/10
Margin Outlook              9/10
Order Book Visibility       9/10
Capex Outlook               7/10
Industry Outlook            8/10
Risk Commentary             6/10

Guidance Quality            8/10
Management Credibility      8.5/10
Overall Management View     8.1/10
```

Again:

```text
Deterministic engine → scores
Llama → explanation
```

---

# 51. The Most Important Output

The system should ultimately answer:

> **What is management telling us about the future, how confident are they, how has that view changed, and how reliable have they historically been?**

Not simply:

> "Was the concall positive?"

The complete model is:

```text
WHAT THEY SAID
      ↓
WHAT THEY MEANT
      ↓
WHAT CHANGED
      ↓
WHAT THEY EXPECT
      ↓
HOW CONFIDENT THEY ARE
      ↓
WHAT THEY SAID PREVIOUSLY
      ↓
WHETHER THEY DELIVERED PREVIOUSLY
      ↓
WHAT THE ACTUAL FINANCIAL DATA SHOWS
      ↓
WHAT WE SHOULD WATCH NEXT
```

---

# 52. Recommended Technology Stack

```text
DATA
├── NSE Corporate Filings
├── NSE EOD Corporate Announcements
└── Company filings as fallback

DOCUMENT PROCESSING
├── PDF parser
├── OCR if required
├── Speaker/section parser
└── Document normalizer

EMBEDDINGS
└── EmbeddingGemma

VECTOR DATABASE
├── Qdrant
├── pgvector
└── Milvus

LLM
└── Llama

DATABASE
└── PostgreSQL

OBJECT STORAGE
└── S3 / MinIO

ORCHESTRATION
├── Python
├── FastAPI
└── Celery / Temporal / equivalent

REPORTING
└── Existing Fundamental Screener PDF pipeline
```

For your existing system, **PostgreSQL + pgvector** is a particularly clean starting point because financial facts, guidance objects and embeddings can live in the same database.

---

# 53. Recommended Processing Cost Optimization

Do NOT send every transcript paragraph to Llama.

Use a two-stage architecture:

```text
                Transcript
                    |
                    v
               Chunking
                    |
                    v
             EmbeddingGemma
                    |
                    v
        Guidance / Outlook Retrieval
                    |
                    v
                 Llama
```

Only send likely relevant chunks to Llama:

```text
guidance
outlook
future
expect
anticipate
confident
target
margin
growth
capex
order
demand
pricing
expansion
```

Plus semantically retrieved chunks.

This dramatically reduces inference cost.

---

# 54. Best Version of the System

The final architecture should combine **three intelligence layers**:

## Layer 1 — Semantic Memory

```text
EmbeddingGemma
```

Answers:

> "What did management say previously about this topic?"

## Layer 2 — Reasoning

```text
Llama
```

Answers:

> "What does this statement mean and how does it relate to previous commentary?"

## Layer 3 — Financial Truth

```text
Deterministic Financial Engine
```

Answers:

> "Did management actually deliver?"

This separation is critical.

---

# 55. Integration With Your Fundamental Screener

Your overall system can eventually become:

```text
                         STOCK
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
           P&L        Balance Sheet   Cash Flow
             |             |             |
             +-------------+-------------+
                           |
                           v
                  Fundamental Engine
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Valuation     Management     Industry
                         Concall        Analysis
             |             |             |
             +-------------+-------------+
                           |
                           v
                    Risk Engine
                           |
                           v
                   Final Stock Score
                           |
                           v
                    Investment Report
```

The Concall Engine should therefore become a **separate first-class module**, not a feature buried inside the P&L analyzer.

---

# 56. Final Architecture Recommendation

For your specific setup:

```text
NSE
 │
 ├── Corporate Announcements
 │
 └── Concall Transcripts
 │
 ▼
NSE INGESTION SERVICE
 │
 ▼
RAW DOCUMENT STORE
 │
 ▼
DOCUMENT PARSER
 │
 ├── Speaker Detection
 ├── Section Detection
 └── Q&A Detection
 │
 ▼
CHUNKING SERVICE
 │
 ▼
EMBEDDINGGEMMA
 │
 ▼
PGVECTOR / QDRANT
 │
 ├── Current Transcript
 ├── Historical Concalls
 ├── Historical Guidance
 ├── Management Promises
 └── Recurring Themes
 │
 ▼
RETRIEVAL ENGINE
 │
 ├── Previous Guidance
 ├── Similar Statements
 ├── Previous Promises
 └── Relevant Financial Data
 │
 ▼
LLAMA
 │
 ├── Guidance Extraction
 ├── Outlook Extraction
 ├── Tone
 ├── Confidence
 ├── Risks
 ├── Future Events
 └── Management Interpretation
 │
 ▼
DETERMINISTIC VERIFICATION ENGINE
 │
 ├── Guidance Change
 ├── Actual vs Guidance
 ├── Guidance Hit Rate
 ├── Promise Status
 ├── Management Credibility
 └── Financial Cross-check
 │
 ▼
MANAGEMENT INTELLIGENCE DATABASE
 │
 ▼
FUNDAMENTAL SCREENER
 │
 ▼
FINAL REPORT
```

## Bottom Line

**Yes, absolutely use both models.**

Your best division of labor is:

```text
EmbeddingGemma
    = MEMORY

Llama
    = REASONING

Python / SQL
    = TRUTH + CALCULATIONS

NSE
    = PRIMARY SOURCE

PostgreSQL + pgvector
    = LONG-TERM MANAGEMENT MEMORY
```

That architecture will let you move beyond simple concall sentiment and build something substantially more valuable: a **longitudinal Management Intelligence Engine that tracks what management promised, how their language changed, how confident they sounded, and whether they actually delivered.**
