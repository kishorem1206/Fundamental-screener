Yes. I reviewed the generated **13-page ITC report**, and the problem is not really the amount of information — it is the **layout engine**. The report has good raw material, but it currently feels like a collection of HTML tables/text blocks exported to PDF rather than a designed equity-research product. 

The biggest issues I see:

* **Charts are too small** relative to the page, especially the price-history charts on page 1 and peer-performance chart on page 6.
* **Huge dead spaces** appear when a section doesn't naturally fill the remaining page.
* Sections are sometimes split awkwardly across pages.
* Tables dominate entire pages without enough visual hierarchy.
* Important numbers such as **77/100, 99/100 profitability, 100/100 balance sheet, 16.4x P/E** don't get the visual treatment they deserve. 
* Page 8's forward-estimate table exposes ugly raw numbers such as `207300000000.00` instead of `₹207.3B / ₹20,730 Cr`. 
* The report has good data but insufficient **visual storytelling**.
* The AI analysis, risk flags, thesis, catalysts and monitoring points should feel like an **investment dashboard**, not paragraphs. 
* The sources page is functional but visually very plain. 

## Give your coding/Claude agent this prompt

Copy this **as-is**:

```md
# FUNDAMENTAL SCREENER — PDF DESIGN SYSTEM UPGRADE

We need to completely redesign the generated Fundamental Equity Research PDF renderer.

I have attached a current generated ITC report. Study the actual rendered PDF carefully before changing the code.

The current PDF contains good analytical content and data, but the visual output looks like a raw HTML/table export rather than a premium institutional equity-research report.

DO NOT change the underlying analysis logic or data pipeline unless required to fix obvious presentation/data-formatting bugs.

The primary objective is:

> Transform the PDF from a "document containing tables and text" into a premium, highly visual, editorial-quality investment research report — similar in polish and information density to a high-end Claude Artifact / modern fintech research dashboard.

Think:
- Bloomberg-style information hierarchy
- modern fintech dashboard
- premium equity research report
- editorial magazine layout
- clean SaaS dashboard
- Claude Artifact-level visual polish

The PDF must feel intentionally designed, not programmatically dumped onto pages.

---

# 1. CORE DESIGN PRINCIPLE

Every page should have a visual hierarchy.

The reader should immediately know:

1. What is this section?
2. What are the 2–4 most important numbers?
3. What is the conclusion?
4. What should I look at next?

Do NOT let paragraphs, tables and charts have equal visual importance.

Use this hierarchy:

LEVEL 1 — Section title
Large, bold, highly visible.

LEVEL 2 — Key insight / headline
A short sentence explaining what matters.

LEVEL 3 — KPI cards / charts / tables
Primary visual information.

LEVEL 4 — Supporting explanation
Smaller, muted text.

LEVEL 5 — Sources / footnotes
Small but readable.

---

# 2. REMOVE DEAD SPACE

This is one of the biggest problems in the current PDF.

Never leave large unexplained empty regions simply because the next section does not fit.

The layout engine must intelligently reflow content.

Implement:

- dynamic vertical layout
- section-aware page breaking
- content measurement before rendering
- keep headings attached to their content
- keep KPI cards attached to their labels
- keep chart titles attached to charts
- prevent orphan headings
- prevent a single bullet from being stranded on the next page
- prevent half-empty pages wherever possible

If a section is too large:

→ split it intentionally into logical subsections.

Do NOT:

→ push the entire next section to another page and leave 30–40% blank.

Use available page space intelligently.

---

# 3. THINK IN "DESIGNED SECTIONS", NOT DOCUMENT PARAGRAPHS

Every major section should have a deliberate visual composition.

For example:

## PAGE / SECTION:

PROFIT & LOSS

[headline insight]

[Revenue KPI] [PAT KPI] [EPS KPI]

        LARGE REVENUE CHART

[margin chart]       [growth chart]

[compact financial table]

[2–3 key observations]

This is dramatically better than:

heading
table
heading
table
paragraph
paragraph
paragraph

---

# 4. CREATE A PREMIUM COVER / HERO PAGE

The first page should feel like the cover of an institutional research report.

Current page 1 contains:

- company name
- sector
- price
- market cap
- P/E
- 52-week range
- price history
- company overview

Redesign it.

Structure:

------------------------------------------------
FUNDAMENTAL EQUITY RESEARCH

ITC LTD.
Fast Moving Consumer Goods · NSE: ITC

₹259.85     +0.21%

As of 14 Sep 2026

------------------------------------------------

[PRICE] [MARKET CAP] [P/E] [52W RANGE]

------------------------------------------------

INVESTMENT VIEW

77 / 100       GOOD
ATTRACTIVE     HIGH CONFIDENCE

------------------------------------------------

LARGE 1-YEAR PRICE CHART

------------------------------------------------

BUSINESS AT A GLANCE

[4–5 compact business segment cards]

------------------------------------------------

KEY TAKEAWAYS

✓ Strong profitability
✓ Net-cash / low leverage
⚠ Weak revenue growth
⚠ Recent price weakness

------------------------------------------------

Do NOT put two tiny charts side-by-side.

The 1-year chart should be LARGE and dominant.

The 5-year chart can appear later in the market/price section.

---

# 5. CHARTS MUST BE LARGE

This is critical.

The current charts look like miniature figures embedded inside a document.

Charts should be treated as first-class visual objects.

Rules:

- A primary chart should occupy ~55–75% of usable page width.
- A major chart should generally occupy at least 30–40% of page height.
- Never shrink a chart merely to make text fit.
- If the chart is important, give it its own row.
- Use large readable axis labels.
- Use subtle grid lines.
- Use direct labels where possible.
- Avoid unnecessary legends.
- Use consistent typography.
- Use consistent chart margins.

For example:

BAD:

[small chart] [small chart]
tiny labels
huge whitespace

GOOD:

------------------------------------
1-YEAR PRICE PERFORMANCE
------------------------------------

          LARGE CHART

------------------------------------

Key observation:
Stock has fallen X% from...

------------------------------------

If two charts genuinely belong together:

[CHART A — 50%] [CHART B — 50%]

But never use two charts side-by-side simply because there are two charts available.

---

# 6. USE VISUAL STORYTELLING FOR FINANCIAL DATA

Do not render every metric as a boring row.

Convert important metrics into visual components.

Example:

FINANCIAL QUALITY

Revenue CAGR
3.6%
↓ Weak

PAT CAGR
2.5%
↓ Weak

EBITDA Margin
38.1%
↑ Strong

ROCE
36.5%
↑ Strong

ROE
28.4%
↑ Strong

FCF/PAT
78.7%
↑ Strong

Debt/Equity
0.0x
✓ Excellent

Interest Coverage
330x
✓ Excellent

Use small status indicators / badges.

---

# 7. BUILD KPI CARDS

Create reusable KPI card components.

Example:

┌──────────────────────┐
│ ROCE                 │
│                      │
│ 36.5%                │
│ Strong               │
└──────────────────────┘

Cards should support:

- metric
- value
- unit
- status
- optional trend
- optional comparison
- optional sparkline

Do NOT make every card huge.

Use a responsive grid:

4 cards per row on wide layouts
2 cards per row when necessary

---

# 8. INVESTMENT SNAPSHOT SHOULD BECOME A HERO COMPONENT

The current Investment Snapshot contains:

77/100
GOOD
78%
94%
ATTRACTIVE

This should become one of the strongest visual components in the report.

Create something like:

╔══════════════════════════════════════════════╗
║             INVESTMENT SNAPSHOT              ║
║                                              ║
║        77 / 100          GOOD                ║
║        FUNDAMENTAL       AI RATING           ║
║                                              ║
║  Growth      ███░░ 30                     ║
║  Profitability █████ 99                    ║
║  Cash Flow   ████░ 85                      ║
║  Balance Sheet █████ 100                   ║
║  Efficiency  ███░░ 62                      ║
║  Valuation   ████░ 75                      ║
║                                              ║
║       VALUATION: ATTRACTIVE                  ║
╚══════════════════════════════════════════════╝

Prefer visual score bars / radial score / horizontal score cards over a plain table.

---

# 9. P&L SECTION MUST FEEL LIKE A FINANCIAL DASHBOARD

Current P&L page is too table-heavy.

Keep the detailed P&L table, but place it after the visual analysis.

Recommended layout:

P&L ANALYSIS

"Revenue growth has slowed materially while margins remain resilient."

[Revenue KPI] [PAT KPI] [EPS KPI] [OPM KPI]

LARGE:
Revenue & Operating Profit trend

SECOND ROW:
Revenue CAGR chart
Profit CAGR chart
Margin trend chart

THEN:
12-year P&L table

THEN:
RED FLAGS / POSITIVE SIGNALS

Use visual chips:

🔴 Declining Sales Growth
🔴 Profit Growth Below Sales Growth

🟢 Stable Margins
🟢 Strong Interest Coverage
🟢 High ROE

THEN:
2–4 concise interpretation bullets.

---

# 10. DO NOT LET TABLES TAKE OVER THE REPORT

Tables are necessary for raw financial history, but they should not visually dominate every page.

Improve tables:

- smaller but readable typography
- stronger header hierarchy
- alternating row backgrounds
- subtle borders
- right-align numeric values
- consistent number formatting
- abbreviate large numbers
- highlight latest/TTM columns
- highlight important metrics
- avoid excessively tall rows
- avoid wrapping numbers unnecessarily

Example:

207300000000.00

MUST become:

₹20,730 Cr

or

₹207.3 B

depending on the report's unit system.

NEVER expose raw API precision unless explicitly required.

---

# 11. NUMBER FORMATTING MUST BE GLOBAL

Create one centralized financial formatting utility.

Rules:

₹325586 Cr
→ ₹3.26L Cr / ₹3.26T depending on convention

207300000000
→ ₹20,730 Cr

16.3943
→ 16.4x

3.65
→ 3.7%

330.15
→ 330x

0.0329
→ 0.03x

Never display:

207300000000.00
16.394300000
330.150000
0.03290000

unless raw precision is specifically required.

Use consistent India-friendly financial notation:

₹ Cr
₹ lakh Cr
%
x

---

# 12. BUSINESS OVERVIEW SHOULD BECOME VISUAL

Instead of a huge paragraph describing business segments:

Create:

BUSINESS MIX

[ Cigarettes       45% ]
[ FMCG Others      27% ]
[ Agri Business    14% ]
[ Paper & Packaging 8% ]
[ Others            6% ]

Use a horizontal stacked bar or donut/pie where appropriate.

Then:

BUSINESS MOAT

75%
Organised cigarette market share

26+ Cr
Household reach

8 Lakh+
UNNATI outlets

2.1 Mn+
Farmers supported

62
Manufacturing units

This immediately communicates scale.

---

# 13. OWNERSHIP & GOVERNANCE

Current page is mostly two tables.

Redesign into:

OWNERSHIP & GOVERNANCE

[Promoter] [FII] [DII] [Public]

Then a large ownership trend chart.

Then:

PLEDGE STATUS

NO PLEDGE DATA / NO PLEDGE REPORTED

Then a compact historical table.

The chart should visually dominate the section.

---

# 14. MARKET INTELLIGENCE

Turn this into a dashboard.

ANALYST CONSENSUS

Yahoo Finance

BUY
₹327
+25.8% implied upside

IndianAPI

BUY
₹335
Target

Then:

FORWARD ESTIMATES

EPS

FY26A → FY27E → FY28E

with a clean bar/line visualization.

Revenue estimates should be normalized to ₹ Cr.

Then:

EARNINGS CALENDAR

Next earnings:
29 Oct 2026

Then:

RECENT CORPORATE ACTIONS

Use timeline-style presentation instead of a plain bullet list.

Then:

RECENT NEWS

Use compact cards:

DATE
HEADLINE
SOURCE
CATEGORY

Do not dump raw article text.

---

# 15. RISK SECTION SHOULD LOOK LIKE A RISK DASHBOARD

Instead of:

[HIGH] Weak Revenue Growth

Create:

RISK RADAR

🔴 HIGH
Weak Revenue Growth

Revenue CAGR below 4%.

🟡 MEDIUM
Margin pressure

...

🟢 LOW
Governance events

No material governance issue identified.

Use severity visually.

---

# 16. AI FUNDAMENTAL ANALYSIS

This should be one of the most visually attractive sections.

Create:

AI FUNDAMENTAL VIEW

GOOD
HIGH CONVICTION
ATTRACTIVE VALUATION

Then a large:

INVESTMENT THESIS

"ITC combines exceptional balance-sheet strength and profitability with weak near-term growth."

Then divide:

┌────────────────┐ ┌────────────────┐
│ BULL CASE      │ │ BEAR CASE      │
│                │ │                │
│ • Strong FCF   │ │ • Weak growth  │
│ • Brand moat   │ │ • Margin risk  │
│ • Low debt     │ │ • Competition  │
└────────────────┘ └────────────────┘

Then:

CATALYSTS

→ Improving FCF
→ Stable cash generation

RISKS

→ Weak revenue growth
→ PAT margin deterioration

WHAT TO MONITOR

→ Revenue growth
→ PAT margin
→ Debt trend

This should look like an investment decision dashboard.

---

# 17. ADD "SO WHAT?" INSIGHT CALLOUTS

Every major quantitative section should have a small insight box.

Example:

┌───────────────────────────────────────────┐
│ SO WHAT?                                  │
│                                           │
│ ITC's balance sheet is exceptionally      │
│ strong, but the key debate is whether     │
│ revenue growth can reaccelerate.          │
└───────────────────────────────────────────┘

Use 1–2 sentences.

Do not repeat the entire analysis paragraph.

---

# 18. TYPOGRAPHY

Create a strict typography system.

Suggested:

Display / H1:
28–36 px equivalent

Section H2:
20–24 px

Subheading:
13–16 px

Body:
9.5–11 px

Table:
8.5–10 px

Footnotes:
7.5–8.5 px

Important numbers:
20–32 px

Do NOT make body text excessively tiny just to fit content.

Prefer:
more pages with excellent readability

over:
fewer pages with tiny text.

---

# 19. COLOR SYSTEM

Create a restrained professional palette.

Base:

Background:
warm white / very light gray

Primary:
deep navy / charcoal

Accent:
blue

Positive:
green

Negative:
red

Warning:
amber

Muted:
cool gray

Do NOT use many bright colors.

The current blue-heavy design should become more sophisticated.

Use color primarily to communicate:

- positive
- negative
- warning
- selected/highlighted
- primary brand accent

---

# 20. PAGE BACKGROUNDS / CARDS

Use subtle cards.

Not every element needs a border.

Use:

- white / slightly tinted cards
- 8–12 px corner radius
- subtle shadow OR subtle border
- consistent internal padding

Avoid:

- giant dark tables covering the entire page
- excessive borders
- excessive rounded boxes
- heavy visual noise

Tables can retain dark headers, but the entire report should not look like a dark spreadsheet.

---

# 21. PAGE HEADER / FOOTER

Every page after the cover should have:

Top:
ITC LTD. | FUNDAMENTAL EQUITY RESEARCH

Bottom:

ITC · NSE: ITC
Analysis date
Page X / Y

Keep it subtle.

---

# 22. SECTION DIVIDERS

Major sections can begin with a strong visual divider.

Example:

01
BUSINESS QUALITY

------------------------------------------------

02
FINANCIAL PERFORMANCE

------------------------------------------------

03
BALANCE SHEET

------------------------------------------------

04
VALUATION

------------------------------------------------

05
MARKET INTELLIGENCE

------------------------------------------------

06
AI FUNDAMENTAL VIEW

This gives the report a magazine/editorial feel.

---

# 23. PAGE COMPOSITION

Target approximately:

60–75% meaningful visual/content occupancy per page.

Avoid:

<40% content occupancy

unless intentionally used as a section-opening page.

Use:

- full-width charts
- 2-column layouts
- KPI grids
- callout cards
- timelines
- compact tables
- insight boxes

to naturally fill pages.

---

# 24. DO NOT FORCE FIXED PAGE COUNTS

The PDF should NOT be designed around exactly 13 pages.

The number of pages should emerge naturally from the content.

It is acceptable if the redesigned report becomes:

10 pages
12 pages
14 pages
15 pages

etc.

The priority is:

READABILITY > CONSISTENCY > INFORMATION DENSITY > PAGE COUNT

---

# 25. SMART PAGE-BREAK ENGINE

Implement layout primitives such as:

Section
Row
Column
Card
KPIGrid
ChartBlock
TableBlock
InsightBlock
Timeline
Callout
PageBreak

Each component must expose its estimated height.

Before rendering:

1. Measure component.
2. Check remaining page space.
3. If component fits → render.
4. If it doesn't fit → intelligently move it.
5. If component itself exceeds one page → split it.
6. Never strand headings.
7. Never leave giant empty regions.

---

# 26. CHART SIZING ALGORITHM

Charts must have minimum dimensions.

For example:

PRIMARY_CHART:
min-height: 260–320px

SECONDARY_CHART:
min-height: 190–240px

SPARKLINE:
min-height: 50–80px

Do not allow a chart to shrink below its readability threshold.

If there isn't enough room:

→ move chart to next page.

Do NOT shrink it into a tiny figure.

---

# 27. VISUALIZE TIME SERIES BETTER

For:

Revenue
Operating Profit
PAT
EPS
Margins
ROCE
ROE
FCF
Stock Price

prefer visual charts where sufficient historical data exists.

Use:

- line charts
- bar charts
- margin trend lines
- indexed performance charts
- sparklines inside KPI cards

Do not turn every time series into a giant table.

Tables should remain available for exact historical values.

---

# 28. CREATE A "KEY TAKEAWAYS" SYSTEM

At the beginning of major sections:

KEY TAKEAWAYS

1. Revenue growth has slowed materially.
2. Profitability remains exceptionally strong.
3. Balance sheet remains very strong.
4. Valuation appears reasonable relative to quality.

Use numbered insight cards.

This makes the report scannable.

---

# 29. DATA QUALITY / SOURCE TRANSPARENCY

Keep source transparency.

But make it elegant.

Instead of a giant raw source table only:

DATA SOURCES

NSE
Regulatory filings / ownership

Screener
Financial statements / ratios

Yahoo Finance
Market data / consensus

IndianAPI
Analyst consensus

Google News
Recent developments

Then retain a detailed source table below.

Add small source badges throughout the report where useful.

Example:

Revenue CAGR
3.6%
[Screener]

---

# 30. IMPORTANT: FIX OBVIOUS PRESENTATION/DATA ISSUES

While redesigning, detect obvious formatting inconsistencies.

Examples from the current report:

- Narrative says market capitalization is "not available" even though the report has ₹325,586 Cr on the first page.
- Revenue estimates appear as raw 12-digit numbers.
- Some text contains awkward encoding artifacts such as "debt■to■equity".
- "ATTRACTIVE" wraps awkwardly in the KPI card.
- Some sections have duplicated / inconsistent terminology.
- Percentages and ratios need consistent rounding.
- Avoid unnecessary decimals.
- Prevent text overflow inside KPI cards.
- Prevent labels from wrapping into ugly two-line collisions.

DO NOT silently alter factual financial values.

Only fix presentation, formatting, and clearly erroneous rendering.

---

# 31. CONTENT DENSITY RULE

Do not solve whitespace by simply increasing font sizes.

Do not solve density by simply shrinking everything.

Instead:

1. restructure
2. group
3. visualize
4. prioritize
5. then size typography

The reader should be able to skim the entire report in 2–3 minutes and understand:

- business quality
- growth
- profitability
- balance sheet
- cash flow
- valuation
- risks
- catalysts
- investment thesis

while still being able to drill into detailed tables.

---

# 32. FINAL DESIGN TEST

After implementation, generate the same ITC report again.

Then visually inspect EVERY PAGE.

For each page ask:

1. Is there unnecessary whitespace?
2. Is any chart too small?
3. Is any table unnecessarily large?
4. Is the main insight obvious within 3 seconds?
5. Are numbers formatted professionally?
6. Are headings stranded?
7. Are charts and captions attached?
8. Is there a good balance of text and visuals?
9. Does the page look like a premium financial product?
10. Does anything look like an accidental HTML export?

If YES to #10, redesign that component.

---

# 33. TARGET VISUAL FEEL

The final result should feel like:

"An analyst opened Bloomberg + a modern fintech dashboard + an editorial research report and designed this intentionally."

NOT:

"An AI generated a PDF from Markdown."

The underlying analysis can remain exactly the same.

The visual system is what must change.

---

# 34. MOST IMPORTANT RULE

DO NOT merely add colors, borders, shadows, or rounded corners to the existing PDF.

That is NOT a redesign.

Recompose the information.

Turn:

paragraph → insight card
metric row → KPI card
raw table → analytical table
bullet list → visual checklist
time series → chart
risk → risk card
analyst targets → consensus cards
corporate actions → timeline
score table → score visualization
business segments → composition visualization

The goal is a genuine information-design system.

---

# 35. DELIVERABLE

Implement the new PDF renderer while keeping the existing data model and analysis pipeline intact.

Create reusable components so every stock automatically receives the same premium visual treatment.

The renderer must work for:

- ITC
- banks
- IT
- FMCG
- pharma
- manufacturing
- auto
- financial services
- other sectors

Sector-specific data may change, but the visual design system must remain consistent.

After implementation:

1. Generate the ITC PDF.
2. Render every PDF page to images.
3. Inspect every page.
4. Fix layout problems.
5. Regenerate.
6. Repeat until there are no major whitespace, sizing, overflow, or hierarchy problems.

Do NOT stop after the first successful PDF generation.

The definition of done is:

> The PDF looks like a premium investment research product, not a generated document.
```

### One more thing I'd strongly recommend

Don't tell your coding agent merely **"make it look like Claude Artifact."** That tends to result in superficial styling.

The important part is the **layout philosophy** above. Your current PDF actually has enough content for a very impressive report — the raw material is there. For example, you already have 12-year P&L data, CAGR analysis, margins, cash-flow quality, valuation, ownership, analyst estimates, corporate actions, news, risks and AI thesis.  

The biggest architectural change I would make is:

**Markdown/content → structured report JSON → layout engine → visual components → PDF**

rather than:

**Markdown → HTML → PDF**

That one change will make it much easier to achieve the "Claude Artifact" feel consistently across **every stock and every sector**.
