# Banking Stock Analysis Report

## Report Generation & Rendering — Single Source of Truth

**Version:** 1.0
**Status:** CANONICAL
**Framework:** BANKING
**Primary Output:** Self-contained HTML
**Secondary Output:** PDF generated from the HTML
**Rendering Philosophy:** Premium financial research report

---

# 1. Purpose

This document is the canonical specification for generating the final downloadable report after a banking-stock analysis has completed.

It defines:

* Report structure
* Information hierarchy
* Visual hierarchy
* Required sections
* Required metrics
* Charts
* Cards
* Tables
* Scores
* Red flags
* Narrative
* Peer comparisons
* Historical trends
* Data provenance
* HTML rendering rules
* PDF rendering rules
* Missing-data behavior
* Investment conclusion
* Disclaimers

The analysis engine MUST generate the underlying structured data first.

The report renderer MUST NOT invent financial information.

The renderer may only present information supplied by:

1. The analysis engine
2. The banking sector framework
3. Validated financial data
4. Approved external data sources

---

# 2. Output Strategy

The preferred output is:

```text
analysis.html
```

The optional secondary output is:

```text
analysis.pdf
```

The HTML is the authoritative visual artifact.

The PDF is a rendered snapshot of the HTML.

If PDF rendering causes loss of:

* charts
* layout
* typography
* gradients
* cards
* tables
* spacing
* visual hierarchy

the HTML remains the primary output.

---

# 3. Design Language

The visual language should be inspired by premium institutional research terminals and modern financial intelligence products.

The report must feel:

```text
Premium
Calm
Analytical
Editorial
Data-rich
Modern
Trustworthy
Non-gimmicky
```

Avoid:

```text
Generic Bootstrap dashboards
Bright white corporate templates
Excessive gradients
Huge colorful KPI boxes
Cheap-looking dashboards
Overly saturated colors
Emoji-heavy interfaces
Dense spreadsheet-like layouts
```

---

# 4. Visual Reference

The reference visual language uses:

```text
Deep navy background
Glass-like cards
Gold accent
Muted teal for positive signals
Warm orange/red for risk
Off-white primary typography
Muted blue-grey secondary typography
Editorial serif headings
Clean sans-serif body text
```

The reference HTML uses a deep navy palette with glass cards, gold, orange, teal, red and muted typography.

Use the following conceptual palette:

```css
--navy-950
--navy-900
--navy-850
--navy-800

--gold
--gold-bright

--teal
--orange
--red

--ink
--ink-dim
--ink-faint

--glass
--glass-hi
--glass-border
```

Do not hard-code colors into individual components.

Use CSS variables.

---

# 5. Typography

Use:

### Primary display font

```text
Fraunces
```

or an equivalent elegant editorial serif.

### Body font

```text
Inter
```

or equivalent modern sans-serif.

The reference HTML uses Fraunces for editorial headings and Inter for body/UI typography.

Typography hierarchy:

```text
Report Title
↓
Section Heading
↓
Card Heading
↓
Metric Value
↓
Body Narrative
↓
Supporting Label
↓
Source / Disclaimer
```

---

# 6. Page Width

Desktop:

```text
Maximum width: approximately 1180px
```

Content should be centered.

Use generous horizontal and vertical spacing.

The reference layout uses a centered 1180px content area with approximately 20px mobile gutters.

---

# 7. Report Structure

The final report MUST follow this structure:

```text
01 Cover / Hero
02 Investment Snapshot
03 Banking Scorecard
04 Growth & Franchise
05 Funding Quality
06 Core Profitability
07 Asset Quality
08 Capital & Balance Sheet
09 Operating Efficiency
10 Historical Trend
11 Peer Comparison
12 Valuation
13 Red Flags
14 Positive Signals
15 Investment Thesis
16 What Could Change the Thesis
17 What to Track Next
18 Data & Methodology
19 Disclaimer
```

The renderer may split sections across multiple pages/screens.

---

# 8. COVER / HERO

The first section must immediately identify the company.

Display:

```text
Company Name
Ticker
Exchange
Sector
Sub-sector
Analysis Date
Current Price
Market Capitalization
Overall Score
Investment Stance
```

Example conceptual layout:

```text
┌─────────────────────────────────────────────┐
│ BANKING INTELLIGENCE                        │
│                                             │
│ HDFC Bank                                   │
│ Private Sector Bank                         │
│                                             │
│ 82 / 100        ATTRACTIVE                  │
│                                             │
│ Strong profitability + resilient asset      │
│ quality, with valuation as the key watch.   │
│                                             │
│ ₹1,850     Market Cap ₹14.2L Cr             │
└─────────────────────────────────────────────┘
```

Do not fabricate values.

---

# 9. INVESTMENT SNAPSHOT

Immediately after the hero, provide a compact summary.

Required cards:

```text
Overall Score
Business Quality
Risk Quality
Valuation
Growth
```

Each card must contain:

```text
Metric name
Score
Short interpretation
Trend indicator
```

Use compact metric chips/cards rather than oversized dashboard widgets.

The reference design uses compact statistic chips with a label and prominent value.

---

# 10. OVERALL VERDICT

Create a visually prominent verdict panel.

Required:

```text
Verdict label
Headline
Score
One-paragraph explanation
```

Possible verdicts:

```text
Exceptional
Strong
Attractive
Watch
Neutral
Caution
Weak
High Risk
```

The verdict must be determined by the analysis engine.

Do not let the renderer invent the verdict.

Use a visual score bar.

The reference design uses a score bar followed by a verdict panel with headline and explanation.

---

# 11. BANKING SCORECARD

Create a major section:

```text
Banking Quality Scorecard
```

Display:

| Category         | Score | Trend | Interpretation |
| ---------------- | ----: | ----- | -------------- |
| Growth           |     — | —     | —              |
| Funding          |     — | —     | —              |
| Profitability    |     — | —     | —              |
| Asset Quality    |     — | —     | —              |
| Capital Strength |     — | —     | —              |
| Efficiency       |     — | —     | —              |
| Valuation        |     — | —     | —              |

Each score should be visually represented.

Use:

```text
score bar
numeric score
trend indicator
```

Avoid pie charts for category scores.

---

# 12. GROWTH & FRANCHISE

Required metrics:

```text
Loan Growth
Deposit Growth
NII Growth
PAT Growth
3Y Loan CAGR
3Y Deposit CAGR
```

Display a trend chart:

```text
Loan Growth vs Deposit Growth
```

Recommended chart:

```text
Line chart
```

with:

```text
Loan Growth
Deposit Growth
```

Show 3Y–5Y history where available.

Below the chart provide an analytical narrative.

The narrative must answer:

```text
Is growth accelerating?
Is growth slowing?
Is loan growth outrunning deposits?
Is growth supported by funding?
Is growth translating into earnings?
```

---

# 13. FUNDING QUALITY

Display:

```text
CASA Ratio
CASA Trend
Deposit Growth
Term Deposit Growth
Retail Deposit Growth
Loan-to-Deposit Ratio
```

Recommended visual:

```text
CASA historical line chart
```

and:

```text
Funding mix stacked bar chart
```

where data is available.

Create a callout when:

```text
CASA is improving
```

or:

```text
CASA is deteriorating
```

Do not create a callout if the data does not support it.

---

# 14. CORE PROFITABILITY

Required metrics:

```text
NIM
NII Growth
ROA
ROE
Cost-to-Income
PAT Growth
```

Recommended visual arrangement:

```text
┌──────────────┬──────────────┬──────────────┐
│ NIM          │ ROA          │ ROE          │
│ 3.8%         │ 2.1%         │ 17.4%        │
└──────────────┴──────────────┴──────────────┘

            NIM Trend Chart

            ROA / ROE Trend
```

Use historical trends wherever possible.

The report must distinguish:

```text
core profitability
```

from:

```text
one-off income
trading gains
treasury gains
```

---

# 15. ASSET QUALITY

This is one of the most important sections.

Required metrics:

```text
Gross NPA
Net NPA
Provision Coverage Ratio
Credit Cost
Slippage Ratio
Write-offs
Recoveries
```

Recommended layout:

```text
Asset Quality Dashboard

GNPA       NNPA       PCR       Credit Cost
```

Follow with:

```text
GNPA / NNPA historical trend
```

and:

```text
Credit Cost trend
```

The report must explicitly answer:

```text
Is asset quality improving?
Is deterioration accelerating?
Are provisions adequate?
Are write-offs masking deterioration?
Are slippages rising?
```

Never describe a bank as "low risk" solely because current GNPA is low.

---

# 16. CAPITAL & BALANCE SHEET

Required:

```text
CAR
CET1
Tier 1 Capital
Loan-to-Deposit Ratio
Capital Buffer
```

Display:

```text
Current CAR
Regulatory requirement
Buffer
```

Use a visual capital-strength indicator.

Narrative must explain:

```text
Is capital sufficient for growth?
Is capital improving or weakening?
Can the bank sustain current loan growth?
```

---

# 17. OPERATING EFFICIENCY

Required where available:

```text
Cost-to-Income
Operating Expense Growth
Business per Employee
Profit per Employee
Branch Growth
```

Recommended visual:

```text
Cost-to-Income Trend
```

Narrative:

```text
Is operating leverage improving?
Is expense growth below income growth?
Is growth requiring disproportionately higher operating costs?
```

---

# 18. HISTORICAL TREND

Create a dedicated historical section.

The minimum historical window should be:

```text
3 years
```

Prefer:

```text
5 years
```

where data is available.

Required trend metrics:

```text
NIM
CASA
Loan Growth
Deposit Growth
GNPA
NNPA
PCR
Credit Cost
ROA
ROE
CAR
PAT Growth
```

The report should make deterioration and improvement visually obvious.

Use:

```text
line charts
area charts
small multiples
```

Do NOT overcrowd one chart with too many variables.

---

# 19. PEER COMPARISON

Create a polished peer comparison table.

Required columns:

```text
Company
Loan Growth
Deposit Growth
NIM
CASA
GNPA
NNPA
ROA
ROE
CAR
P/B
```

Highlight:

```text
Company under analysis
```

without making the table visually aggressive.

Use relative ranking where useful.

Example:

```text
Top quartile
Above median
Median
Below median
Bottom quartile
```

Do not compare companies across incompatible business models.

---

# 20. VALUATION

Create a dedicated valuation section.

Primary:

```text
P/B
```

Secondary:

```text
P/E
```

Where sufficient data exists, include:

```text
Historical P/B
Current P/B
5Y median P/B
Peer P/B
ROE
```

Recommended chart:

```text
Current P/B vs Historical P/B
```

or:

```text
P/B vs ROE peer scatter
```

The narrative must answer:

```text
Is the bank cheap?
Is the bank expensive?
Is the premium justified?
What ROE is the market paying for?
```

Never conclude:

```text
Low P/B = cheap
```

without considering profitability and asset quality.

---

# 21. RED FLAGS

Create a visually distinct risk section.

Each red flag must contain:

```text
Severity
Title
Evidence
Metric
Current value
Historical comparison
Why it matters
```

Severity:

```text
HIGH
MEDIUM
LOW
```

Visual treatment:

```text
HIGH → red/orange emphasis
MEDIUM → amber/gold emphasis
LOW → muted emphasis
```

Do not create red flags without evidence.

If no meaningful red flags exist:

```text
No material red flags identified from the available validated data.
```

---

# 22. POSITIVE SIGNALS

Create a corresponding positive-signal section.

Examples:

```text
Improving CASA
Stable/rising NIM
Falling GNPA
Falling NNPA
Low credit cost
Strong ROA
Strong ROE
High CET1
Healthy deposit growth
Improving cost-to-income
```

Each positive signal must cite the underlying metric.

---

# 23. INVESTMENT THESIS

The report must include a narrative section:

```text
Why this bank is interesting
```

Structure:

```text
1. Core strength
2. Growth engine
3. Competitive advantage
4. Profitability quality
5. Risk profile
6. Valuation
```

Maximum:

```text
5–7 concise paragraphs
```

Avoid generic language.

The narrative must be tied to actual data.

---

# 24. WHAT COULD CHANGE THE THESIS

Create a section:

```text
What would make us more bullish?
```

and:

```text
What would make us more cautious?
```

Examples:

### More bullish

```text
NIM stabilizes
CASA improves
Loan growth remains healthy
GNPA continues falling
ROA expands
Capital remains strong
```

### More cautious

```text
NIM contracts materially
CASA declines
Credit costs rise
Slippages increase
GNPA/NNPA worsen
CET1 falls
Loan growth outpaces deposits
```

These are monitoring conditions, not predictions.

---

# 25. WHAT TO TRACK NEXT

Provide a concise monitoring dashboard.

Example:

```text
NEXT QUARTER WATCHLIST

NIM             → Watch
CASA            → Positive
Loan Growth     → Neutral
Deposit Growth  → Positive
GNPA            → Watch
Credit Cost     → Watch
ROA             → Positive
CET1            → Positive
Valuation       → Watch
```

Each item should contain:

```text
Metric
Current value
Previous value
Direction
Why it matters
```

---

# 26. DATA QUALITY

Include a transparent section:

```text
Data Quality & Coverage
```

Show:

```text
Metrics analysed: X
Metrics available: X
Metrics unavailable: X
Primary-source coverage: X%
Calculated metrics: X
Estimated metrics: X
```

Display a confidence indicator:

```text
HIGH
MEDIUM
LOW
```

Never hide missing data.

---

# 27. SOURCE PROVENANCE

Every important number must be traceable.

Each metric should internally retain:

```text
metric
value
period
source
source URL
source document
retrieved date
reported/calculated
confidence
```

The report may display a compact source label such as:

```text
Source: HDFC Bank Q1 FY27 Investor Presentation
```

Do not clutter every card with long URLs.

Instead provide:

```text
Source
```

links in the methodology/data section.

---

# 28. CHART RULES

Charts must be:

```text
Clean
Minimal
Readable
Professional
Consistent
```

Avoid:

```text
3D charts
Pie charts unless genuinely useful
Heavy borders
Chartjunk
Excessive gridlines
Too many data series
```

Preferred charts:

```text
Line
Area
Grouped bar
Stacked bar
Scatter
```

Each chart must have:

```text
Title
Subtitle/context
Axis labels where useful
Legend
Source
```

The reference HTML uses large chart containers inside cards rather than embedding charts into cramped layouts.

---

# 29. CARD RULES

Cards should represent one coherent analytical concept.

Good:

```text
NIM
ROA
ROE
```

Bad:

```text
NIM + GNPA + CASA + P/B + CAR + Loan Growth
```

Cards should use:

```text
Rounded corners
Subtle border
Subtle shadow
Glass/translucent surface
Generous padding
```

The reference design uses rounded glass cards with subtle borders and shadows.

---

# 30. NARRATIVE RULES

Every major chart should be followed by interpretation.

Do NOT make the report:

```text
chart
chart
chart
chart
```

Instead:

```text
Chart
↓
What it shows
↓
Why it matters
↓
Investment implication
```

The reference report uses short explanatory narrative paragraphs directly below analytical visualizations.

---

# 31. RESPONSIVE HTML

The HTML must work on:

```text
Desktop
Laptop
Tablet
Mobile
```

Use responsive grids.

Example:

```css
grid-template-columns: 1fr 1fr;
```

becoming:

```css
grid-template-columns: 1fr;
```

on smaller screens.

The reference implementation uses responsive two-column grids that collapse to one column on smaller screens.

---

# 32. INTERACTION

HTML may include lightweight interactions.

Allowed:

```text
Section navigation
Tabs
Chart toggles
Metric-period toggles
Expand/collapse
Peer filters
```

Do NOT require interaction for understanding the core report.

The downloadable HTML must remain useful even if JavaScript fails.

---

# 33. PDF MODE

When generating PDF from HTML:

```text
Preserve the HTML visual design.
```

Do NOT create a separate generic PDF template.

PDF requirements:

```text
A4 / Letter compatible
Background graphics enabled
Charts preserved
Cards preserved
No clipped content
No broken tables
No orphaned headings
No overlapping elements
Page numbers
Company name in header
Section name in footer/header
```

Use print-specific CSS:

```css
@media print
```

and:

```css
page-break-inside: avoid;
break-inside: avoid;
```

for cards, tables and important analytical blocks.

---

# 34. PRINT COLOR

The PDF should preserve the dark premium aesthetic.

Do not automatically convert the report to a white document.

If a printing-friendly version is required, support a separate:

```text
print-light
```

theme.

But the standard downloadable PDF should preserve the primary dark visual identity.

---

# 35. PAGE BREAK STRATEGY

Avoid:

```text
Heading at bottom of page
Chart separated from title
Table header separated from table
Verdict separated from explanation
Metric card split across pages
```

Prefer logical page boundaries:

```text
Hero
↓
Scorecard
↓
Major analytical section
↓
Supporting charts
```

---

# 36. ERROR HANDLING

If a chart cannot render:

```text
Do NOT break the entire report.
```

Show:

```text
Chart unavailable
```

and preserve the surrounding narrative/data.

The reference HTML uses diagnostics and isolated error handling so one failed section does not prevent the rest of the report from rendering.

---

# 37. MISSING DATA

If a metric is unavailable:

Display:

```text
N/A
```

Do NOT display:

```text
0
Unknown
—
```

unless explicitly configured.

The narrative must say:

```text
Data unavailable for this period.
```

Do not infer missing financial data.

---

# 38. DATA CONFIDENCE

Every analysis section should internally know:

```text
HIGH CONFIDENCE
MEDIUM CONFIDENCE
LOW CONFIDENCE
```

Confidence depends on:

```text
Source quality
Data completeness
Historical coverage
Calculation reliability
Conflicting sources
```

The renderer may show a small confidence badge.

---

# 39. AI WRITING STYLE

The AI narrative should sound like:

```text
An experienced equity research analyst
```

not:

```text
A generic chatbot
```

Use:

```text
specific
evidence-backed
concise
analytical
balanced
```

Avoid:

```text
This stock is amazing.
This company is very good.
Investors should definitely buy.
The future looks bright.
```

Prefer:

```text
NIM has remained stable despite higher funding costs, suggesting that the bank has retained pricing power. The key risk is whether this resilience persists as deposit costs reprice.
```

---

# 40. INVESTMENT LANGUAGE

Do not make absolute predictions.

Prefer:

```text
supports
suggests
indicates
raises concern
could pressure
warrants monitoring
appears attractive relative to
```

Avoid:

```text
will rise
guaranteed
certain
sure-shot
multibagger
risk-free
```

---

# 41. FINAL CONCLUSION

The report must end with:

```text
Investment View
```

containing:

```text
Overall Score
Business Quality
Risk
Valuation
Key Bull Case
Key Bear Case
What to Monitor
Final Interpretation
```

Example structure:

```text
STRONG BUSINESS / FAIR VALUATION

The bank combines strong ROA, improving asset quality and
healthy deposit growth. The principal concern is valuation:
the current P/B already discounts a meaningful portion of
the profitability advantage.

Bull case:
...

Bear case:
...

Monitor:
...
```

The conclusion must be generated from the analysis data.

---

# 42. DISCLAIMER

End with a concise disclaimer:

```text
This report is generated from available financial and market
data and is intended for research and educational purposes.
It is not investment advice. Historical performance and
financial metrics do not guarantee future results. Data may
contain delays, revisions or omissions. Always verify
important figures against the latest official company,
exchange and regulatory disclosures before making investment
decisions.
```

---

# 43. FINAL FILES

After successful analysis, generate:

```text
/company_analysis/
    ├── company_analysis.html
    ├── company_analysis.pdf
    └── data/
        └── analysis.json
```

The minimum downloadable artifact is:

```text
company_analysis.html
```

The preferred bundle is:

```text
HTML + PDF
```

The JSON is optional but strongly recommended for reproducibility.

---

# 44. HTML SELF-CONTAINMENT

The downloadable HTML should preferably be self-contained.

Where practical:

```text
CSS → embedded
JavaScript → embedded
Chart data → embedded
Analysis data → embedded
```

External dependencies should be minimized.

If external fonts or libraries are used, the renderer should have a fallback.

The report must remain readable if a CDN is unavailable.

---

# 45. Reproducibility

Given:

```text
analysis.json
sector framework version
report renderer version
```

the system should be able to reproduce the same report.

Store internally:

```text
framework_version
analysis_timestamp
data_timestamp
renderer_version
company_id
```

---

# 46. Source of Truth Hierarchy

When generating the final report:

```text
banking_report_output.md
        ↓
banking.md
        ↓
validated analysis data
        ↓
raw source data
```

If a conflict exists:

```text
This document
+
banking.md
```

define what should be displayed and analysed.

Raw data must never override framework definitions without an explicit framework update.

---

# 47. Separation of Responsibilities

## Sector Framework

Defines:

```text
What should be analysed
```

## Analysis Engine

Defines:

```text
What the data says
```

## AI Analyst

Defines:

```text
What the data means
```

## Report Renderer

Defines:

```text
How the analysis looks
```

The renderer must NOT perform investment analysis.

The AI analyst must NOT control CSS/layout.

The sector framework must NOT contain presentation markup.

---

# 48. Golden Rule

The final report should feel like:

```text
A premium institutional research note
+
A modern interactive financial dashboard
+
An editorial investment thesis
```

It should NOT feel like:

```text
A spreadsheet exported to PDF.
```

The report should make a reader understand the company's:

```text
Business Quality
Growth
Funding
Profitability
Asset Quality
Capital Strength
Valuation
Risks
Investment Thesis
```

within the first few minutes.

---

# 49. Final Rendering Pipeline

The implementation MUST follow:

```text
                COMPANY
                   ↓
          DATA COLLECTION
                   ↓
          DATA VALIDATION
                   ↓
        BANKING FRAMEWORK
                   ↓
        METRIC CALCULATION
                   ↓
        TREND CALCULATION
                   ↓
         PEER COMPARISON
                   ↓
          RED FLAG ENGINE
                   ↓
           AI INTERPRETATION
                   ↓
         STRUCTURED ANALYSIS
                   ↓
      banking_report_output.md
                   ↓
            HTML RENDERER
                   ↓
       ┌───────────┴───────────┐
       ↓                       ↓
   HTML REPORT             PDF EXPORT
       ↓                       ↓
Downloadable            Downloadable
Interactive              Printable
Responsive               Fixed-layout
```

The HTML renderer is the primary presentation layer.

The PDF renderer is a print/export layer over the HTML design.

---

# 50. NON-NEGOTIABLE REQUIREMENTS

The implementation MUST satisfy all of the following:

```text
✓ Rich visual hierarchy
✓ Premium dark financial aesthetic
✓ Responsive HTML
✓ Beautiful charts
✓ Metric cards
✓ Scorecards
✓ Peer tables
✓ Historical trends
✓ Red flags
✓ Positive signals
✓ Investment thesis
✓ Data provenance
✓ Missing-data transparency
✓ PDF export
✓ No invented numbers
✓ No invented conclusions
✓ No irrelevant banking metrics
✓ No generic industrial-company dashboard
✓ No raw spreadsheet-style output
✓ No broken sections when one chart fails
✓ No clipping in PDF
✓ No unnecessary page breaks
✓ Consistent typography
✓ Consistent spacing
✓ Consistent component design
```

---

# 51. Design Principle

**Data determines the content.**

**The banking framework determines what matters.**

**The AI determines the interpretation.**

**This document determines how that interpretation becomes a beautiful downloadable research product.**

---

# 52. Implementation Decisions (recorded 2026-09-06)

These are concrete engineering choices made when implementing this spec, kept here so the decision and its reasoning stay attached to the canonical doc rather than living only in a plan file.

## PDF Engine: Playwright + Chromium

Chosen over WeasyPrint. Rationale: section 3-6 and 28-30's glass-card design language depends on `backdrop-filter` blur and modern CSS (gradients, grid) that a pure-Python CSS renderer (WeasyPrint) does not support faithfully — it does not execute a real browser engine. Playwright drives headless Chromium against the actual generated HTML, so the PDF is a true rendered snapshot (section 2's requirement) rather than an approximation. Cost: a one-time `playwright install chromium` (~300MB binary download) as part of environment setup.

Page numbers, company-name header, and section footer (section 33) are implemented via Playwright's native `page.pdf(display_header_footer=True, header_template=..., footer_template=...)` rather than custom pagination logic.

## Historical Trend Data: Backfill, Not Latest-Quarter-Only

Section 18 (Historical Trend) and the trend columns throughout sections 12-20 assume 3-5 years of quarterly data. The banking ingestion pipeline (`app/ingestion/`) originally only pulled the latest quarter's filing. This was extended to backfill ~3-5 years (≈15-20 quarters) of BSE "Financial Results" filings per bank on first analysis, so trend charts have real historical data from the first generated report rather than showing N/A everywhere. Backfill runs once per company (long-TTL gate), then subsequent analyses only ingest the latest incremental quarter — first-time report generation for a bank is therefore slower (several minutes of OCR+LLM extraction across many filings) than for an already-backfilled company.

## Charts: Hand-Rolled Inline SVG, No JS Charting Library

Satisfies section 44 (self-containment, must remain readable without a CDN) exactly: chart markup is plain `<svg>` generated server-side in Python from the same data the template renders, identical in the live HTML and the Playwright-printed PDF. No chart.js/d3/etc. dependency, no CDN fetch, no JS execution required to see a chart.
