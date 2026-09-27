# Fundamental P&L Analysis Engine --- Implementation Specification

## Purpose

This specification adds a **deep, mentor-style P&L analysis layer** to
the existing Fundamental Screener without removing or replacing the
current analysis.

The new module should treat the P&L as an **income-generation system**,
not simply as a collection of ratios. It must explain:

-   how revenue becomes gross profit, operating profit and PAT
-   whether margins are strong relative to direct sector peers
-   whether margins are stable, expanding or stagnating
-   how quickly revenue and profit double
-   whether standalone and consolidated results tell materially
    different stories
-   whether reported income is actually coming from the core business
-   whether subsidiaries/investments distort the apparent quality of the
    business
-   where operational efficiency is being gained or lost
-   how all of the above contribute to a dedicated P&L quality score

The source framework explicitly emphasizes cost control, operational
efficiency, margin stability, peer positioning and statement structure.
It also warns that high revenue without strong margins can be
misleading.

> **Important implementation principle:** keep the existing screener
> analysis intact. This module should become an additional P&L
> intelligence layer that feeds the overall fundamental score.

------------------------------------------------------------------------

# 1. Source Framework to Implement

The attached guide defines the P&L income cascade as:

**Total Revenue → COGS → Gross Profit → OPEX → Operating Profit / EBITDA
→ Depreciation + Interest + Tax → Net Profit / PAT**

The guide defines:

-   Gross Profit = Revenue − COGS
-   Gross Margin = Gross Profit / Revenue × 100
-   Net Profit Margin = Net Profit / Revenue × 100

It specifically recommends flagging situations where gross margin is
healthy but net margin is negative because of excessive interest or
operational overhead.

The guide also requires **strict intra-sector peer benchmarking** rather
than comparing margins across unrelated sectors.

Source: *Fundamental P&L Analysis & Screener Framework*, pages 1--2.
fileciteturn0file0L17-L37

------------------------------------------------------------------------

# 2. What the New P&L Module Should Produce

For every stock, the engine should produce five layers.

## Layer A --- Raw P&L

Store and normalize:

-   Revenue
-   COGS / material cost where available
-   Gross Profit
-   Gross Margin
-   Employee Cost
-   Other Operating Expenses
-   EBITDA / Operating Profit
-   EBITDA Margin
-   Depreciation
-   EBIT
-   EBIT Margin
-   Finance Cost / Interest
-   PBT
-   Tax
-   PAT
-   Net Profit Margin
-   Exceptional Items
-   Other Income
-   Core Operating Income
-   Non-Core Income

Both **Standalone** and **Consolidated** versions should be stored
independently.

## Layer B --- Trend Analysis

Calculate:

-   YoY Revenue Growth
-   3Y Revenue CAGR
-   5Y Revenue CAGR
-   10Y Revenue CAGR
-   YoY EBITDA Growth
-   3Y EBITDA CAGR
-   5Y EBITDA CAGR
-   YoY PAT Growth
-   3Y PAT CAGR
-   5Y PAT CAGR
-   Gross Margin trend
-   EBITDA Margin trend
-   EBIT Margin trend
-   PAT Margin trend
-   Margin volatility
-   Margin expansion/contraction
-   Revenue doubling period
-   PAT doubling period

## Layer C --- Peer Intelligence

Compare the company against **direct sector/industry peers**:

-   Revenue growth percentile
-   EBITDA margin percentile
-   EBIT margin percentile
-   PAT margin percentile
-   Margin stability percentile
-   Revenue doubling velocity percentile
-   PAT doubling velocity percentile
-   Core earnings quality percentile

## Layer D --- Structural Diagnostics

Analyze:

-   Standalone vs Consolidated divergence
-   Subsidiary contribution
-   Other income dependency
-   Dividend income dependency
-   Capital-gain dependency
-   Interest burden
-   Depreciation burden
-   Exceptional-item dependency
-   Conglomerate / SOTP requirement

## Layer E --- P&L Score + Narrative

Output:

1.  P&L Score: 0--100
2.  P&L classification
3.  Positive drivers
4.  Negative drivers
5.  Peer position
6.  Margin headroom
7.  Revenue/profit velocity
8.  Earnings quality
9.  Standalone/consolidated diagnosis
10. Important red flags
11. Data-confidence level

------------------------------------------------------------------------

# 3. Canonical Data Model

Do NOT calculate everything directly from presentation-layer data.

Create a normalized financial-period model first.

``` text
Company
 ├── company_id
 ├── symbol
 ├── name
 ├── sector
 ├── industry
 ├── peer_group_id
 └── is_conglomerate

FinancialPeriod
 ├── company_id
 ├── period
 ├── period_type
 │    ├── FY
 │    ├── Q
 │    └── TTM
 ├── statement_type
 │    ├── standalone
 │    └── consolidated
 ├── revenue
 ├── cogs
 ├── gross_profit
 ├── employee_cost
 ├── other_opex
 ├── operating_profit
 ├── depreciation
 ├── ebit
 ├── finance_cost
 ├── other_income
 ├── pbt
 ├── tax
 ├── exceptional_items
 ├── pat
 ├── core_operating_income
 ├── non_operating_income
 └── source_metadata
```

Every number should retain:

``` text
source
source_date
period
statement_type
currency
unit
reported_value
normalized_value
confidence
```

This is important because P&L analysis should never silently mix
standalone and consolidated values.

------------------------------------------------------------------------

# 4. Stage-by-Stage Implementation

# Stage 0 --- Freeze the Existing Screener

Before implementing anything:

### Objective

Do not break the existing fundamental engine.

Create a clear boundary:

``` text
Existing Fundamental Engine
          │
          ├── Existing P&L Metrics
          │
          ├── Existing Balance Sheet
          │
          ├── Existing Cash Flow
          │
          └── Existing Valuation
                    │
                    ▼
             New P&L Engine
                    │
                    ▼
             P&L Intelligence
                    │
                    ▼
             Overall Fundamental Score
```

### Acceptance criteria

-   Existing scores remain reproducible.
-   Existing API contracts remain valid.
-   Existing database records are not overwritten.
-   New P&L metrics are additive.

------------------------------------------------------------------------

# Stage 1 --- Build the Financial Data Normalization Layer

This is the most important engineering stage.

Different companies report P&L line items differently.

Examples:

``` text
Revenue
Sales
Revenue from Operations
Income from Operations
Total Revenue
```

These must map into a canonical field:

``` text
revenue
```

Similarly:

``` text
Employee Benefits Expense
Employee Cost
Staff Cost
```

→

``` text
employee_cost
```

Create a mapping layer:

``` python
CANONICAL_MAPPING = {
    "revenue": [
        "Revenue",
        "Sales",
        "Revenue from Operations",
        "Income from Operations"
    ],
    "employee_cost": [
        "Employee Cost",
        "Employee Benefits Expense",
        "Employee Benefits"
    ],
    "finance_cost": [
        "Finance Cost",
        "Interest Cost",
        "Financial Charges"
    ]
}
```

Do not hard-code a single source's labels into the analytical engine.

------------------------------------------------------------------------

# Stage 2 --- Build the P&L Income Cascade

Implement the complete cascade.

``` text
Revenue
   │
   ├── COGS
   │
   ▼
Gross Profit
   │
   ├── Operating Expenses
   │
   ▼
EBITDA / Operating Profit
   │
   ├── Depreciation
   │
   ▼
EBIT
   │
   ├── Finance Cost
   ├── Other Income
   ├── Exceptional Items
   │
   ▼
PBT
   │
   ├── Tax
   ▼
PAT
```

Core calculations:

``` python
gross_profit = revenue - cogs

gross_margin = gross_profit / revenue * 100

ebitda_margin = ebitda / revenue * 100

ebit_margin = ebit / revenue * 100

pat_margin = pat / revenue * 100
```

Always protect against:

``` python
revenue == 0
```

and missing COGS.

If COGS cannot be reliably derived, return:

``` text
gross_margin = null
gross_margin_confidence = LOW
```

rather than inventing a value.

------------------------------------------------------------------------

# Stage 3 --- Build Cost Structure Analysis

The engine should explain **why margins move**.

Calculate:

``` text
COGS / Revenue
Employee Cost / Revenue
Other OPEX / Revenue
Depreciation / Revenue
Finance Cost / Revenue
Tax / PBT
```

Then calculate changes:

``` text
Δ COGS Ratio
Δ Employee Cost Ratio
Δ OPEX Ratio
Δ Depreciation Ratio
Δ Finance Cost Ratio
```

Example:

``` text
Revenue Growth: +18%
Employee Cost Growth: +27%
EBITDA Growth: +8%
EBITDA Margin: 24% → 20%
```

Interpretation:

> Revenue is growing, but employee costs are growing faster than
> revenue, causing operating leverage to deteriorate.

This is much more useful than simply saying:

> EBITDA margin fell.

------------------------------------------------------------------------

# Stage 4 --- Margin Trend Engine

Create a historical matrix:

  Metric             FY-5   FY-4   FY-3   FY-2   FY-1   FY
  ---------------- ------ ------ ------ ------ ------ ----
  Revenue Growth                                      
  Gross Margin                                        
  EBITDA Margin                                       
  EBIT Margin                                         
  PAT Margin                                          

Calculate:

### Margin direction

``` text
Expansion
Stable
Compression
Volatile
```

### Margin change

``` python
margin_change = current_margin - historical_margin
```

### Margin volatility

Use a configurable rolling standard deviation:

``` python
margin_volatility = std(margin_series)
```

Do not treat a volatile margin as equivalent to a stable margin even if
the current margin is high.

------------------------------------------------------------------------

# Stage 5 --- Intra-Sector Peer Engine

This is mandatory.

The source explicitly states that a margin in isolation is meaningless
and that companies must be compared against direct industry peers.

Source: page 1. fileciteturn0file0L34-L37

Create:

``` text
Peer Group
 ├── Company A
 ├── Company B
 ├── Company C
 └── Company D
```

For each metric calculate:

``` text
Peer Median
Peer Mean
Peer Min
Peer Max
Company Rank
Company Percentile
```

Example:

``` text
Company PAT Margin: 20.4%
Peer Median: 15.2%
Peer Maximum: 22.1%
Percentile: 82
```

Output:

> PAT margin is in the top 18% of the peer group.

Do not compare a pharma company with an FMCG company merely because both
have 15% PAT margins.

------------------------------------------------------------------------

# Stage 6 --- Margin Ceiling / Headroom Engine

The source introduces a particularly important concept:

## Margin Expansion vs Stagnation

A company near the industry's peak margin may have limited further
margin-driven earnings growth.

A lower-margin company can have substantial catch-up potential if
revenue is growing and operational efficiency improves.

Source: page 2. fileciteturn0file0L64-L78

Calculate:

``` python
sector_peak_margin = peer_group.max(pat_margin)

margin_headroom = sector_peak_margin - company_pat_margin

margin_headroom_pct = (
    margin_headroom / sector_peak_margin
) * 100
```

Classify:

``` text
Near Peak
Moderate Headroom
High Headroom
Severe Underperformance
```

But add an important second dimension:

``` text
Margin Headroom + Revenue Growth
```

A low-margin company with declining revenue should NOT automatically
receive a high-growth interpretation.

Use:

``` text
High headroom + high revenue growth
    → Strong expansion candidate

High headroom + weak revenue growth
    → Potential efficiency turnaround

Low headroom + high revenue growth
    → Growth-led compounder

Low headroom + weak revenue growth
    → Mature / stagnant candidate
```

The source's examples identify peak-margin stagnation and second-tier
catch-up potential as distinct trajectories.
fileciteturn0file0L68-L78

------------------------------------------------------------------------

# Stage 7 --- Revenue & Profit Doubling Velocity

Create a dedicated velocity engine.

The source treats the time required to double revenue and profit as a
core business-momentum metric.

Source: pages 2--3. fileciteturn0file0L76-L98

## Revenue Doubling Period

For historical annual revenue:

``` text
Find earliest historical period where:

Revenue >= 2 × reference revenue
```

Return:

``` text
doubling_years
doubling_start_year
doubling_end_year
```

Also calculate a CAGR-based theoretical doubling period when
appropriate:

``` python
doubling_years = ln(2) / ln(1 + CAGR)
```

Only use the CAGR method when the CAGR is positive and the underlying
periods are valid.

## Suggested interpretation

The source provides these broad examples:

``` text
< 5 years   → Fast growth
5–8 years   → Strong / healthy growth
8–10 years  → Steady compounder
> 10 years  → Slow growth
```

Do not hard-code these as universal sector truths. Store them as
configurable thresholds.

## Do the same for PAT

This creates:

``` text
Revenue Doubling Velocity
PAT Doubling Velocity
```

The combination is more informative:

``` text
Revenue doubles quickly
PAT doubles faster
→ Margin expansion / operating leverage

Revenue doubles quickly
PAT doubles similarly
→ Stable economics

Revenue doubles quickly
PAT doubles slower
→ Margin compression / cost pressure
```

------------------------------------------------------------------------

# Stage 8 --- Standalone vs Consolidated Engine

This must be a first-class module.

The source explicitly says the screener should process standalone and
consolidated statements independently and compare their divergence.

Source: page 3. fileciteturn0file0L99-L124

For every key metric calculate:

``` text
Standalone Revenue
Consolidated Revenue
Standalone EBITDA
Consolidated EBITDA
Standalone PAT
Consolidated PAT
```

Then:

``` python
revenue_structural_ratio = (
    standalone_revenue / consolidated_revenue
)

pat_structural_ratio = (
    standalone_pat / consolidated_pat
)
```

The source specifically defines:

``` text
CSR = Standalone Revenue / Consolidated Revenue
```

and highlights CSR \< 0.30 as a signal of substantial global/subsidiary
reliance.

Source: page 5. fileciteturn0file0L193-L201

Create a diagnostic:

``` text
CSR > 0.80
→ Primarily parent/domestic/core business

CSR 0.50–0.80
→ Material subsidiary contribution

CSR 0.30–0.50
→ Significant group contribution

CSR < 0.30
→ Consolidated structure dominates
```

These interpretation bands should be configurable.

------------------------------------------------------------------------

# Stage 9 --- Subsidiary Contribution Analysis

Do not stop at CSR.

Calculate:

``` text
Consolidated Revenue
− Standalone Revenue
= Approximate Non-Standalone Contribution
```

Then:

``` python
subsidiary_revenue_share = (
    consolidated_revenue - standalone_revenue
) / consolidated_revenue
```

Similarly:

``` text
Subsidiary PAT Contribution
Subsidiary EBITDA Contribution
```

If segment/subsidiary data exists, use it instead of approximating from
standalone/consolidated differences.

Output examples:

``` text
Core parent business contributes ~24% of consolidated revenue.

The group is therefore primarily driven by subsidiaries / overseas operations.
```

or:

``` text
Standalone and consolidated revenue are nearly identical.

The business is structurally close to a pure parent-company operating model.
```

------------------------------------------------------------------------

# Stage 10 --- Quality of Earnings Engine

This is one of the most important additions.

The source warns about the **Non-Core Revenue Trap** and explicitly
requires the screener to isolate core operating income from
non-operating/investment income.

Source: page 4. fileciteturn0file0L157-L171

Create:

``` python
EQI = core_operating_income / total_income
```

The source defines the Earnings Quality Index as:

``` text
EQI = Core Operating Revenue / Total Income
```

Source: page 5. fileciteturn0file0L193-L201

Scoring thresholds in the source:

``` text
EQI ≥ 0.90 → 100 points
0.70–0.89 → 60 points
< 0.70 → 20 points
```

Store these as configuration, not hard-coded business logic.

------------------------------------------------------------------------

# Stage 11 --- Non-Core Income Decomposition

Build a separate bucket:

``` text
Other Income
 ├── Dividend Income
 ├── Interest Income
 ├── Investment Gains
 ├── Capital Gains
 ├── Fair Value Gains
 ├── Asset Sale Gains
 └── Other
```

Then calculate:

``` text
Non-Core Income / Total Income
Non-Core Income / PAT
Non-Core Income / EBITDA
```

Create red flags:

``` text
Dividend income unusually large
Investment gains materially support PAT
Exceptional gains support PAT
Other income growth > operating income growth
PAT growth materially exceeds operating profit growth
```

The source's Jio Financial Services case demonstrates why this matters:
reported income contained a significant dividend component while core
operating income was much smaller. fileciteturn0file0L160-L166

------------------------------------------------------------------------

# Stage 12 --- Earnings Bridge

For every year, generate:

``` text
Revenue
    ↓
Gross Profit
    ↓
EBITDA
    ↓
EBIT
    ↓
PBT
    ↓
PAT
```

Then explain changes.

Example:

``` text
Revenue       +15%
Gross Profit  +13%
EBITDA        +8%
EBIT          +6%
PBT           +4%
PAT           +2%
```

Narrative:

> Revenue grew strongly, but earnings growth decelerated at every
> downstream level. The main issue is operating margin compression
> rather than top-line weakness.

This should be one of the primary narrative outputs in the PDF.

------------------------------------------------------------------------

# Stage 13 --- Operating Leverage Detector

Compare growth rates:

``` text
Revenue Growth
vs
EBITDA Growth
vs
PAT Growth
```

Rules:

``` text
EBITDA Growth > Revenue Growth
→ Positive operating leverage

EBITDA Growth < Revenue Growth
→ Negative operating leverage

PAT Growth > EBITDA Growth
→ Below-EBITDA items are helping

PAT Growth < EBITDA Growth
→ Interest / depreciation / tax may be absorbing gains
```

Then inspect:

``` text
Finance Cost / Revenue
Depreciation / Revenue
Tax Rate
Other Income
Exceptional Items
```

The result should identify the actual bottleneck rather than simply
assigning a "good/bad" label.

------------------------------------------------------------------------

# Stage 14 --- Interest & Overhead Trap Detector

Implement the source's explicit diagnostic:

``` text
Healthy Gross Margin
+
Weak / Negative PAT Margin
```

→ investigate:

``` text
Finance Cost
Employee Cost
Other OPEX
Depreciation
Exceptional Items
```

Create a diagnostic object:

``` json
{
  "type": "margin_cascade_break",
  "severity": "HIGH",
  "gross_margin": 32.5,
  "pat_margin": -1.2,
  "likely_drivers": [
    "finance_cost",
    "operating_overhead"
  ]
}
```

The source specifically says this condition should trigger a screener
flag. fileciteturn0file0L29-L33

------------------------------------------------------------------------

# Stage 15 --- Margin Stability Score

High current margin is not enough.

Calculate:

``` text
Current Margin
5Y Average Margin
10Y Average Margin
5Y Standard Deviation
Maximum Margin
Minimum Margin
```

Then classify:

``` text
High + Stable
High + Volatile
Low + Improving
Low + Stable
High + Declining
```

This is important because a company with 25% PAT margin today but a
highly unstable history should not be treated the same as a company that
has maintained 22--25% for a decade.

------------------------------------------------------------------------

# Stage 16 --- P&L Master Score

The source defines five sub-metrics.

## M1 --- Sector Margin Percentile

Weight:

``` text
25%
```

Formula:

``` text
Percentile Rank of company NPM within peer sector
```

Source thresholds:

``` text
>80th percentile → 100 points
50th–80th → 70 points
<50th → 30 points
```

Source: page 4. fileciteturn0file0L172-L189

------------------------------------------------------------------------

## M2 --- Margin Headroom Opportunity

Weight:

``` text
20%
```

Formula:

``` text
ΔM = Sector Peak NPM − Company NPM
```

The source says companies below the peak with growing sales should
receive a high expansion score, but it does not define complete numeric
thresholds.

Therefore implement M2 as a configurable scoring function:

``` text
margin_headroom_score(
    headroom,
    revenue_growth,
    margin_trend
)
```

Do NOT invent fixed thresholds into the core framework without
configuration/versioning.

------------------------------------------------------------------------

## M3 --- Sales Doubling Velocity

Weight:

``` text
20%
```

Formula:

``` text
V2x = Years required to double Revenue
```

Source thresholds:

``` text
<5 years → 100
5–8 years → 80
>10 years → 40
```

Source: page 4. fileciteturn0file0L187-L189

The missing 8--10-year boundary should be handled through configurable
interpolation rather than silently inventing a source rule.

------------------------------------------------------------------------

## M4 --- Earnings Quality Index

Weight:

``` text
20%
```

Formula:

``` text
EQI = Core Operating Revenue / Total Income
```

Source thresholds:

``` text
≥0.90 → 100
0.70–0.89 → 60
<0.70 → 20
```

Source: page 5. fileciteturn0file0L193-L201

------------------------------------------------------------------------

## M5 --- Consolidated Structural Ratio

Weight:

``` text
15%
```

Formula:

``` text
CSR = Standalone Revenue / Consolidated Revenue
```

Primary diagnostic:

``` text
CSR < 0.30
→ High global/subsidiary reliance
```

The source does not provide a complete numeric score table for M5.

Therefore keep:

``` text
M5_score
M5_diagnostic
```

as separate fields.

------------------------------------------------------------------------

# Stage 17 --- Master Score Calculation

The source formula is:

``` text
ScorePL =
    (0.25 × M1)
  + (0.20 × M2)
  + (0.20 × M3)
  + (0.20 × M4)
  + (0.15 × M5)
```

Source: page 5. fileciteturn0file0L202-L211

Output:

``` text
0–100 P&L Score
```

Source classifications:

``` text
Score ≥ 80
→ Premium Quality Growth / Efficiency Leader

Score 60–79
→ Stable Compounder / Margin Expansion Candidate

Score < 60
→ High Overhead / Non-Core Income Trap / Stagnant Performer
```

Do not display the score without exposing its component scores.

------------------------------------------------------------------------

# Stage 18 --- Add a Diagnostic Scorecard

The five source metrics are not enough to explain the company.

Create a separate diagnostic scorecard:

``` text
P&L QUALITY
────────────────────────────
Revenue Growth              ████████░░
Gross Margin                █████████░
EBITDA Margin               ████████░░
PAT Margin                  █████████░
Margin Stability            ███████░░░
Operating Leverage          ████████░░
Earnings Quality             █████████░
Peer Position               █████████░
Margin Headroom              ██████░░░░
Revenue Velocity             ████████░░
Profit Velocity              █████████░
Structural Simplicity        ██████░░░░
```

This is a presentation layer and should not silently replace the
source's five-factor ScorePL.

------------------------------------------------------------------------

# Stage 19 --- Rule-Based P&L Diagnostics

Create reusable rules.

## Rule: Revenue Growth Without Profit Growth

``` text
IF revenue_growth > 10%
AND pat_growth < revenue_growth
THEN flag = "profit_conversion_weak"
```

## Rule: Margin Compression

``` text
IF current_pat_margin < 5Y_average_pat_margin
THEN flag = "margin_compression"
```

## Rule: Strong Margin Headroom

``` text
IF current_margin < peer_peak
AND revenue_growth > 0
AND margin_trend > 0
THEN flag = "margin_expansion_candidate"
```

## Rule: Peak Margin

``` text
IF current_margin >= 95% of peer_peak
THEN flag = "near_sector_peak"
```

## Rule: Non-Core Dependency

``` text
IF EQI < 0.70
THEN flag = "non_core_income_dependency"
```

## Rule: Consolidated Reliance

``` text
IF CSR < 0.30
THEN flag = "high_subsidiary_global_reliance"
```

## Rule: Interest Trap

``` text
IF gross_margin healthy
AND pat_margin weak
AND finance_cost_ratio elevated
THEN flag = "interest_burden"
```

## Rule: Operating Overhead Trap

``` text
IF revenue_growth positive
AND EBITDA_margin declining
AND employee_cost_ratio increasing
THEN flag = "operating_overhead_pressure"
```

------------------------------------------------------------------------

# Stage 20 --- Narrative Generation

The engine should generate deterministic facts first.

Example structured output:

``` json
{
  "revenue_growth": 18.2,
  "pat_growth": 11.4,
  "pat_margin": 20.4,
  "peer_percentile": 82,
  "sector_peak_margin": 22.1,
  "margin_headroom": 1.7,
  "revenue_doubling_years": 6.8,
  "eqi": 0.94,
  "csr": 0.88,
  "flags": [
    "high_peer_margin",
    "stable_earnings_quality"
  ]
}
```

Only then allow the LLM to convert this into prose.

### LLM rule

The LLM must NOT calculate financial numbers.

It should receive:

``` text
verified metrics
verified formulas
verified peer statistics
verified flags
```

and produce:

``` text
P&L Summary
Why margins changed
Peer positioning
Growth trajectory
Quality of earnings
Standalone vs consolidated interpretation
Risks
```

------------------------------------------------------------------------

# Stage 21 --- Use LLM + Embeddings Correctly

If the application already has an embedding model and a Llama-class
model, use them for **interpretation and retrieval**, not primary
arithmetic.

## Embeddings

Use embeddings for:

-   management commentary retrieval
-   annual-report P&L explanations
-   concall references to margins
-   management guidance
-   cost-pressure commentary
-   pricing commentary
-   utilization commentary
-   employee-cost commentary
-   subsidiary commentary

Example retrieval:

``` text
Query:
"Why did EBITDA margin decline?"

Retrieve:
- annual report
- earnings call
- investor presentation
- management commentary
```

## Llama

Use the LLM to synthesize:

``` text
Financial metrics
+
Historical trend
+
Peer data
+
Management commentary
```

into:

> Margin declined because employee costs increased faster than revenue,
> while management expects utilization improvement to partially offset
> the pressure.

But the statement must be backed by retrieved evidence.

------------------------------------------------------------------------

# Stage 22 --- Data Confidence System

Every metric should have confidence.

``` text
HIGH
→ directly reported / reliably derived

MEDIUM
→ derived from multiple reported values

LOW
→ estimated / incomplete line-item mapping

UNAVAILABLE
→ insufficient data
```

Never turn missing data into zero.

For example:

``` text
COGS unavailable
```

must not become:

``` text
COGS = 0
```

because that would artificially inflate Gross Margin.

------------------------------------------------------------------------

# Stage 23 --- Peer Group Architecture

Peer selection should be deterministic.

Preferred hierarchy:

``` text
Industry
   ↓
Sub-industry
   ↓
Business model
   ↓
Comparable operating economics
```

Example:

``` text
Defense Shipbuilding
 ├── Cochin Shipyard
 ├── Mazagon Dock
 └── GRSE
```

The source uses these companies as an example of peer-margin and
headroom comparison. fileciteturn0file0L49-L63

Avoid:

``` text
Defense + IT + Pharma
```

just because the companies are all large-cap.

------------------------------------------------------------------------

# Stage 24 --- Conglomerate Handling

A company operating across unrelated businesses should not receive a
simplistic single-sector P&L score.

The source specifically warns that conglomerates such as Reliance
Industries require segment-level / SOTP treatment.

Source: page 4. fileciteturn0file0L167-L171

Create:

``` text
is_conglomerate
segment_count
segment_sector_count
sotp_required
```

If:

``` text
sotp_required = true
```

then produce:

``` text
Group P&L
+
Segment P&L
+
Segment margin
+
Segment growth
+
Segment contribution
```

and clearly mark the consolidated P&L score as:

``` text
"Group-level score — interpret with SOTP"
```

------------------------------------------------------------------------

# Stage 25 --- Database Tables

Recommended tables:

``` text
companies
financial_periods
financial_line_items
financial_metrics
peer_groups
peer_group_members
peer_statistics
pl_diagnostics
pl_scores
pl_score_components
pl_trends
pl_structural_analysis
pl_income_quality
financial_sources
```

## pl_score_components

``` text
company_id
period
m1_sector_margin_percentile
m1_score
m2_margin_headroom
m2_score
m3_revenue_doubling_years
m3_score
m4_eqi
m4_score
m5_csr
m5_score
master_pl_score
algorithm_version
calculated_at
```

------------------------------------------------------------------------

# Stage 26 --- API Design

## Company P&L endpoint

``` http
GET /api/v1/stocks/{symbol}/fundamentals/pl
```

Return:

``` json
{
  "company": {},
  "income_cascade": {},
  "historical_trends": {},
  "margin_analysis": {},
  "peer_analysis": {},
  "doubling_velocity": {},
  "standalone_vs_consolidated": {},
  "earnings_quality": {},
  "diagnostics": [],
  "score": {},
  "confidence": {}
}
```

## Peer endpoint

``` http
GET /api/v1/stocks/{symbol}/fundamentals/pl/peers
```

## Historical endpoint

``` http
GET /api/v1/stocks/{symbol}/fundamentals/pl/history
```

## Score endpoint

``` http
GET /api/v1/stocks/{symbol}/fundamentals/pl/score
```

------------------------------------------------------------------------

# Stage 27 --- Screener Filters

Expose the new P&L engine as actual screening filters.

Examples:

``` text
P&L Score > 80

PAT Margin > Sector Median

PAT Margin Percentile > 80

EBITDA Margin > 20%

Margin Trend = Expanding

Revenue Doubling < 8 years

PAT Doubling < 8 years

EQI > 0.90

CSR > 0.80

Margin Headroom > X%

Finance Cost / Revenue < X%

Other Income / PAT < X%

Revenue Growth > PAT Growth

Operating Leverage = Positive
```

This turns the module from a report generator into a genuine screener
engine.

------------------------------------------------------------------------

# Stage 28 --- UI Design

The company page should have a dedicated:

# P&L Intelligence

section.

## 1. P&L Score Card

``` text
P&L QUALITY SCORE

82 / 100

Premium Quality Growth /
Efficiency Leader
```

Show component scores underneath.

## 2. Income Cascade

Visual:

``` text
Revenue
₹100
  ↓
Gross Profit
₹42
  ↓
EBITDA
₹28
  ↓
EBIT
₹23
  ↓
PBT
₹22
  ↓
PAT
₹17
```

## 3. Margin Trend Chart

Plot:

``` text
Gross Margin
EBITDA Margin
EBIT Margin
PAT Margin
```

over 5--10 years.

## 4. Peer Benchmark

Show:

``` text
Company      PAT Margin   Percentile
Company A      20.4%         82
Company B      17.2%         68
Company C      14.5%         51
Company D       9.9%         24
```

## 5. Revenue vs PAT Growth

A dual-line chart showing:

``` text
Revenue CAGR
PAT CAGR
```

## 6. Doubling Velocity

``` text
Revenue doubles in: 6.8 years
PAT doubles in:     5.2 years
```

Interpretation:

``` text
PAT is compounding faster than revenue.
Potential operating leverage / margin expansion.
```

## 7. Standalone vs Consolidated

Use a comparison card:

``` text
Standalone Revenue       ₹X Cr
Consolidated Revenue     ₹Y Cr

Core Revenue Share       XX%
Subsidiary Contribution  XX%
CSR                      0.XX
```

## 8. Earnings Quality

``` text
EQI: 94%

Core Operating Income    94%
Non-Core Income           6%
```

## 9. Red Flags

Use severity:

``` text
HIGH
MEDIUM
LOW
```

Never hide the underlying metric.

------------------------------------------------------------------------

# Stage 29 --- PDF Report Design

The P&L section of the generated PDF should feel like an analytical
report, not a spreadsheet dump.

Recommended page sequence:

``` text
PAGE 1
P&L Executive Summary
Score + Key Insights + Major Flags

PAGE 2
Income Cascade
Revenue → Gross Profit → EBITDA → PAT

PAGE 3
5–10 Year Margin & Growth Trend

PAGE 4
Peer Benchmark
PAT Margin + EBITDA Margin + Percentile

PAGE 5
Margin Headroom + Doubling Velocity

PAGE 6
Standalone vs Consolidated

PAGE 7
Quality of Earnings
Core vs Non-Core Income

PAGE 8
Cost Structure & Earnings Bridge

PAGE 9
P&L Score Calculation

PAGE 10
Final P&L Diagnosis
```

Do not force every chart onto one page.

The report should prioritize whitespace, large charts, readable labels
and clear hierarchy.

------------------------------------------------------------------------

# Stage 30 --- Validation Framework

Before production, manually validate the engine across the sectors
suggested by the source.

## FMCG / Retail

Benchmark:

``` text
Nestle India
HUL
Dabur
ITC
```

Check:

-   10Y revenue doubling
-   Operating margin consistency
-   PAT margin
-   peer percentile

## Automobile / Auto Ancillary

Benchmark:

``` text
Maruti Suzuki
Tata Motors
M&M
Bajaj Auto
```

Check:

-   standalone vs consolidated
-   domestic vs group economics
-   margin differences

## Defense / Capital Goods

Benchmark:

``` text
Cochin Shipyard
Mazagon Dock
GRSE
HAL
```

Check:

-   peak margin
-   margin headroom
-   revenue velocity

## Logistics / Pharma

Check:

-   COGS ratio
-   OPEX ratio
-   employee cost
-   operational efficiency bottlenecks

These benchmark categories are explicitly recommended in the source's
validation section. fileciteturn0file0L212-L228

------------------------------------------------------------------------

# Stage 31 --- Automated Unit Tests

Build tests for:

## Formula tests

``` text
Gross Profit
Gross Margin
EBITDA Margin
EBIT Margin
PAT Margin
EQI
CSR
```

## Edge cases

``` text
Revenue = 0
Revenue < 0
PAT < 0
Negative EBITDA
Negative PBT
Missing COGS
Missing Other Income
Standalone only
Consolidated only
Newly listed company
Acquisition year
Merger year
Demerger year
Exceptional gain
Exceptional loss
```

## Peer tests

``` text
1 company peer group
2 company peer group
missing peer
different fiscal year
different reporting period
```

## Doubling tests

``` text
Revenue already > 2x
Revenue never doubles
Revenue declines
Revenue is negative / invalid
```

------------------------------------------------------------------------

# Stage 32 --- Historical Backtesting

Do not validate only against the latest annual result.

For each test company:

``` text
Run engine as of FY2018
Run engine as of FY2019
Run engine as of FY2020
...
Run engine as of latest FY
```

Verify:

-   no look-ahead bias
-   peer group data available at that point
-   no future financial values leak into historical score
-   score changes are explainable
-   source data remains reproducible

------------------------------------------------------------------------

# Stage 33 --- Version the Algorithm

Every score should carry:

``` text
algorithm_version
data_version
peer_group_version
calculated_at
```

Example:

``` text
PL_ENGINE_V1.0
```

When thresholds or formulas change:

``` text
PL_ENGINE_V1.1
```

This is critical because a screener score without versioning becomes
impossible to audit.

------------------------------------------------------------------------

# Stage 34 --- Recommended Build Order

Implement in this exact order.

``` text
STEP 1
Financial data normalization

↓

STEP 2
Standalone / Consolidated separation

↓

STEP 3
Income cascade

↓

STEP 4
Historical margin engine

↓

STEP 5
Cost structure analysis

↓

STEP 6
Peer-group engine

↓

STEP 7
Margin headroom engine

↓

STEP 8
Revenue + PAT doubling engine

↓

STEP 9
Quality-of-earnings engine

↓

STEP 10
Structural / subsidiary engine

↓

STEP 11
Diagnostic rules

↓

STEP 12
M1–M5 scoring

↓

STEP 13
P&L narrative engine

↓

STEP 14
API

↓

STEP 15
Screener filters

↓

STEP 16
Dashboard UI

↓

STEP 17
PDF rendering

↓

STEP 18
Backtesting + validation
```

Do not start with the PDF.

**The data and calculation layer must become correct first.**

------------------------------------------------------------------------

# Stage 35 --- Final P&L Output Contract

Every company should ultimately produce something structurally similar
to:

``` json
{
  "pl_score": 82,
  "classification": "Premium Quality Growth / Efficiency Leader",

  "revenue": {
    "growth_1y": 18.2,
    "cagr_3y": 16.4,
    "cagr_5y": 14.8,
    "doubling_years": 6.8
  },

  "margins": {
    "gross": 42.1,
    "ebitda": 28.4,
    "ebit": 23.1,
    "pat": 20.4
  },

  "peer_position": {
    "pat_margin_percentile": 82,
    "ebitda_margin_percentile": 77,
    "sector_peak_pat_margin": 22.1,
    "margin_headroom": 1.7
  },

  "earnings_quality": {
    "eqi": 0.94,
    "non_core_income_share": 0.06
  },

  "structure": {
    "csr": 0.88,
    "subsidiary_reliance": "LOW"
  },

  "velocity": {
    "revenue_doubling_years": 6.8,
    "pat_doubling_years": 5.2
  },

  "diagnostics": [
    "High peer-margin position",
    "PAT compounding faster than revenue",
    "High earnings quality"
  ],

  "risk_flags": [],

  "score_components": {
    "M1": {},
    "M2": {},
    "M3": {},
    "M4": {},
    "M5": {}
  }
}
```

------------------------------------------------------------------------

# 36. What the Final AI-Generated P&L Analysis Should Sound Like

The final report should not say:

> Revenue increased 18% and PAT increased 11%.

Instead:

> **Revenue grew strongly, but profit conversion weakened.** Revenue
> increased 18%, while PAT grew 11%, indicating downstream earnings
> growth is lagging the top line. The primary area to investigate is
> operating leverage and cost absorption.

Then:

> **Margin quality remains strong relative to peers.** PAT margin is in
> the upper peer percentile, although the company is approaching the
> sector's current margin ceiling. This reduces the probability of
> further earnings acceleration from margin expansion alone.

Then:

> **Earnings quality is high.** The majority of reported income is
> attributable to core operating activity, with limited dependence on
> non-operating income.

Then:

> **Structural dependence is low.** Standalone revenue remains a large
> proportion of consolidated revenue, suggesting the group-level numbers
> are broadly representative of the parent operating business.

Then:

> **Overall P&L diagnosis:** high-quality business economics, strong
> peer positioning, but slowing profit conversion requires monitoring.

Every sentence must be traceable to a verified metric or retrieved
management/source statement.

------------------------------------------------------------------------

# 37. Critical Engineering Rules

## Rule 1 --- Never mix standalone and consolidated data

Every metric must have:

``` text
statement_type
```

attached.

## Rule 2 --- Never compare unrelated sectors

Peer comparisons must use the assigned peer group.

## Rule 3 --- Never treat Other Income as operating revenue

Strip or separately classify non-core income.

## Rule 4 --- Never treat missing data as zero

Use:

``` text
null + confidence flag
```

## Rule 5 --- Never let the LLM calculate the score

The deterministic engine calculates.

The LLM explains.

## Rule 6 --- Never expose a score without its components

Users should be able to drill from:

``` text
Score
→ M1–M5
→ underlying metric
→ raw financial value
→ source
```

## Rule 7 --- Preserve historical reproducibility

A 2024 score should remain reproducible using the data available at that
time.

## Rule 8 --- Make thresholds configurable

Especially for:

-   margin headroom
-   doubling velocity
-   CSR interpretation
-   peer classifications

The attached source does not specify complete numeric scoring thresholds
for every component, so configuration is preferable to silently
inventing rules.

------------------------------------------------------------------------

# 38. MVP vs Full Version

## MVP

Implement first:

``` text
✓ Revenue
✓ EBITDA
✓ PAT
✓ Gross Margin
✓ EBITDA Margin
✓ PAT Margin
✓ 5Y trends
✓ Peer percentile
✓ Revenue doubling
✓ Standalone vs Consolidated
✓ EQI
✓ CSR
✓ M1–M5
✓ Basic diagnostics
```

## V2

Add:

``` text
✓ Cost-driver decomposition
✓ Margin stability
✓ PAT doubling
✓ Operating leverage
✓ Subsidiary contribution
✓ Non-core income decomposition
✓ Conglomerate/SOTP handling
✓ LLM narrative
✓ Concalls + annual-report retrieval
```

## V3

Add:

``` text
✓ Historical point-in-time backtesting
✓ Automated peer discovery
✓ Sector-specific P&L models
✓ Management guidance tracking
✓ Earnings-surprise analysis
✓ Margin forecast
✓ Scenario analysis
✓ P&L anomaly detection
```

------------------------------------------------------------------------

# 39. Definition of Done

The P&L engine is production-ready only when:

``` text
[ ] Existing screener still works
[ ] Financial data is normalized
[ ] Standalone and consolidated are separated
[ ] Income cascade is correct
[ ] Gross / EBITDA / EBIT / PAT margins work
[ ] Historical trend engine works
[ ] Peer groups are deterministic
[ ] Peer percentiles work
[ ] Margin headroom works
[ ] Revenue doubling works
[ ] PAT doubling works
[ ] EQI works
[ ] CSR works
[ ] Non-core income is isolated
[ ] Cost-driver analysis works
[ ] Diagnostic rules work
[ ] M1–M5 scores are reproducible
[ ] Algorithm version is stored
[ ] Missing data is handled safely
[ ] LLM cannot alter financial calculations
[ ] PDF section renders correctly
[ ] Sector benchmark tests pass
[ ] Historical backtests pass
[ ] Every important metric is source-traceable
```

------------------------------------------------------------------------

# 40. Core Architecture Summary

The final architecture should be:

``` text
                  RAW FINANCIAL DATA
                         │
                         ▼
              ┌─────────────────────┐
              │ DATA NORMALIZATION   │
              └──────────┬──────────┘
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       STANDALONE              CONSOLIDATED
             │                       │
             └───────────┬───────────┘
                         ▼
                 INCOME CASCADE
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     MARGINS          COSTS          EARNINGS
        │                │             QUALITY
        ▼                ▼                │
   TREND ENGINE     EFFICIENCY            ▼
        │             ENGINE          EQI ENGINE
        └──────────────┬─────────────────┘
                       ▼
                 PEER ENGINE
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       MARGIN HEADROOM      DOUBLING VELOCITY
             │                   │
             └─────────┬─────────┘
                       ▼
              STRUCTURAL ANALYSIS
                       │
                       ▼
                 M1 – M5 SCORE
                       │
                       ▼
               DIAGNOSTIC ENGINE
                       │
                       ▼
             VERIFIED METRICS JSON
                       │
             ┌─────────┴──────────┐
             ▼                    ▼
        SCREENER UI           LLM NARRATIVE
                                  │
                                  ▼
                             PDF REPORT
```

## Bottom Line

The key change is that the app should stop treating P&L as:

``` text
Revenue
PAT
Margin
Growth
```

and instead treat it as:

``` text
Revenue
   ↓
Cost Structure
   ↓
Gross Profit
   ↓
Operating Efficiency
   ↓
EBITDA
   ↓
Capital / Depreciation / Interest Burden
   ↓
PAT
   ↓
Margin Quality
   ↓
Peer Position
   ↓
Margin Headroom
   ↓
Growth Velocity
   ↓
Earnings Quality
   ↓
Standalone / Consolidated Structure
   ↓
P&L Score
   ↓
Investment Diagnosis
```

This preserves the mentor framework while turning it into a robust,
auditable software module that can sit alongside the existing
Fundamental Screener analysis.
