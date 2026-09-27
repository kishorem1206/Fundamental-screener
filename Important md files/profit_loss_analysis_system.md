# Profit & Loss Analysis System
## 10-Year P&L Analysis Framework for Fundamental Screener

### Purpose

The Fundamental Screener should have a dedicated **Profit & Loss Analysis Engine** that analyzes at least 10 years of annual financial data plus TTM data.

The framework is inspired by the analytical structure used in the **Safal Niveshak Stock Analysis Excel**, while also incorporating the useful presentation metrics commonly shown by Screener-style reports.

The objective is not merely to display the P&L statement. The engine should determine:

- How fast the business is growing
- Whether growth is accelerating or slowing
- Whether profits are growing faster or slower than sales
- Whether margins are improving or deteriorating
- What is driving the cost structure
- Whether earnings are operationally driven
- Whether interest, depreciation or other income materially affect earnings
- Whether EPS is growing consistently
- Whether retained earnings are creating value
- How current performance compares with long-term history

---

# 1. Architecture

```text
Financial Data Agent
        |
        v
10+ Year P&L Dataset
        |
        v
P&L Normalization
        |
        v
Deterministic P&L Calculation Engine
        |
        +-------------------+
        |                   |
        v                   v
Trend / Ratio Engine     Quality Flags
        |                   |
        +---------+---------+
                  |
                  v
           P&L Analysis Object
                  |
                  v
                Llama
                  |
                  v
       P&L Interpretation / Narrative
                  |
                  v
           Report Blueprint
                  |
                  v
             PDF Renderer
```

## Responsibility Split

### Financial/Data Agent

Provides:

- Sales
- Expenses
- Material cost
- Employee cost
- Power and fuel
- Other manufacturing expenses
- Selling and administrative expenses
- Operating profit
- Other income
- Depreciation
- Interest
- PBT
- Tax
- Net profit
- EPS
- Dividend
- Share count
- Market price
- Market capitalization
- Relevant balance-sheet data for ROE
- Source and period for each metric

### Deterministic Calculation Engine

Calculates:

- YoY growth
- CAGR
- Margins
- Expense ratios
- Interest coverage
- EPS growth
- Dividend payout
- Retained earnings
- Buffett's $1 Test
- Trend comparisons
- Margin averages
- P&L quality indicators

### Llama

Interprets the calculated data.

Llama should answer:

- What happened?
- What changed?
- Is the change positive or negative?
- Is the trend improving or deteriorating?
- What is the likely significance of the supplied data?
- What should an investor monitor?

Llama must not invent financial data.

### PDF Renderer

Renders:

- 10-year P&L table
- TTM column
- Growth cards
- Margin cards
- Charts
- Trend analysis
- Llama-generated interpretation
- Flags and observations

---

# 2. Historical Data Requirement

The engine should preferably maintain:

```text
FY-10
FY-9
FY-8
FY-7
FY-6
FY-5
FY-4
FY-3
FY-2
FY-1
FY
TTM
```

For companies with longer history, additional years can be retained internally.

The minimum analytical window should be 10 completed financial years.

---

# 3. Core P&L Table

The report should display:

| Particulars | FY-10 | FY-9 | FY-8 | ... | FY-2 | FY-1 | FY | TTM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sales | | | | | | | | |
| YoY Sales Growth | | | | | | | | |
| Expenses | | | | | | | | |
| Material Cost | | | | | | | | |
| Material Cost % of Sales | | | | | | | | |
| Power & Fuel | | | | | | | | |
| Other Manufacturing Expense | | | | | | | | |
| Employee Cost | | | | | | | | |
| Selling & Admin Cost | | | | | | | | |
| Operating Profit | | | | | | | | |
| Operating Profit Margin | | | | | | | | |
| Other Income | | | | | | | | |
| Other Income % of Sales | | | | | | | | |
| Depreciation | | | | | | | | |
| Interest | | | | | | | | |
| Interest Coverage | | | | | | | | |
| Profit Before Tax | | | | | | | | |
| YoY PBT Growth | | | | | | | | |
| PBT Margin | | | | | | | | |
| Tax | | | | | | | | |
| Net Profit | | | | | | | | |
| YoY Net Profit Growth | | | | | | | | |
| Net Profit Margin | | | | | | | | |
| EPS | | | | | | | | |
| YoY EPS Growth | | | | | | | | |
| P/E | | | | | | | | |
| Price | | | | | | | | |
| Dividend Payout | | | | | | | | |
| Market Capitalization | | | | | | | | |
| Retained Earnings | | | | | | | | |

---

# 4. Sales Growth Analysis

## Required Metrics

Calculate:

- 10-Year Sales CAGR
- 7-Year Sales CAGR
- 5-Year Sales CAGR
- 3-Year Sales CAGR
- TTM growth

Also calculate:

- Annual YoY growth
- Average growth
- Median growth
- Highest growth
- Lowest growth
- Number of negative-growth years
- Growth volatility
- Recent growth vs long-term growth

## CAGR Formula

```text
CAGR = (Ending Sales / Beginning Sales) ^ (1 / Number of Years) - 1
```

## Required Presentation

### Compounded Sales Growth

| Period | CAGR |
|---|---:|
| 10 Years | XX% |
| 7 Years | XX% |
| 5 Years | XX% |
| 3 Years | XX% |
| TTM | XX% |

---

# 5. Profit Growth Analysis

Profit growth should primarily use **Net Profit**, while PBT should also be tracked separately.

Calculate:

- 10-Year Net Profit CAGR
- 7-Year Net Profit CAGR
- 5-Year Net Profit CAGR
- 3-Year Net Profit CAGR
- TTM YoY growth
- PBT CAGR
- EPS CAGR

## Required Comparison

```text
Revenue CAGR
       vs
PBT CAGR
       vs
Net Profit CAGR
       vs
EPS CAGR
```

This comparison is critical.

### Example

```text
Revenue CAGR      15%
PBT CAGR          20%
Net Profit CAGR   23%
EPS CAGR          22%
```

Interpretation:

> Earnings have grown faster than revenue, suggesting that profitability and/or operating leverage have contributed meaningfully to earnings growth.

The interpretation must only mention operating leverage if the supplied metrics support that conclusion.

---

# 6. Screener-Style Growth Cards

The report should include:

### Compounded Sales Growth

| Period | CAGR |
|---|---:|
| 10 Years | XX% |
| 5 Years | XX% |
| 3 Years | XX% |
| TTM | XX% |

### Compounded Profit Growth

| Period | CAGR |
|---|---:|
| 10 Years | XX% |
| 5 Years | XX% |
| 3 Years | XX% |
| TTM | XX% |

---

# 7. Year-on-Year Growth Analysis

For every year calculate:

```text
Sales Growth
PBT Growth
Net Profit Growth
EPS Growth
```

The engine should detect:

- Positive growth
- Negative growth
- Acceleration
- Deceleration
- Growth reversals
- Exceptional growth years
- Exceptional decline years

Example:

```text
FY22   +28%
FY23   +31%
FY24   +17%
FY25    +8%
FY26    +4%
```

Llama interpretation:

> Revenue growth has decelerated materially over the last two years compared with the earlier part of the period.

---

# 8. Long-Term vs Short-Term Trend Analysis

This is a core Safal Niveshak-style analysis.

Compare:

```text
10Y Growth
7Y Growth
5Y Growth
3Y Growth
Latest / TTM Growth
```

## Trend Logic

### Improving

```text
3Y CAGR > 5Y CAGR > 10Y CAGR
```

### Moderating

```text
3Y CAGR < 5Y CAGR < 10Y CAGR
```

### Stable

Growth rates remain within a defined tolerance band.

### Volatile

Large variation between annual growth rates.

The exact thresholds should be configurable.

## Llama should explain:

- Whether long-term growth is intact
- Whether recent growth is slowing
- Whether recent growth is improving
- Whether the change is consistent or volatile

---

# 9. Operating Profit Analysis

Calculate:

```text
Operating Profit
Operating Profit Growth
Operating Profit Margin
```

## Operating Profit Margin

```text
OPM = Operating Profit / Sales × 100
```

Calculate:

- Current OPM
- 10Y average OPM
- 7Y average OPM
- 5Y average OPM
- 3Y average OPM
- Peak OPM
- Lowest OPM
- OPM change vs 10Y average
- OPM change vs 5Y average
- OPM trend

---

# 10. Margin Trend Analysis

Classify OPM as:

### Expanding

Current/recent OPM is materially above historical levels.

### Contracting

Current/recent OPM is materially below historical levels.

### Stable

Current/recent OPM is broadly in line with historical levels.

### Volatile

OPM shows large fluctuations across the historical period.

Llama should explain the significance.

Example:

> Operating margins are currently below the recent five-year average, indicating some deterioration in profitability relative to the company's recent operating history.

Do not state the cause unless supporting data is available.

---

# 11. Expense Structure Analysis

The P&L engine should analyze expenses as a percentage of sales.

Required:

```text
Material Cost / Sales
Power & Fuel / Sales
Other Manufacturing Expense / Sales
Employee Cost / Sales
Selling & Admin Cost / Sales
```

Calculate for every year.

## Expense Trend Detection

Identify:

- Rising material-cost intensity
- Falling material-cost intensity
- Rising employee-cost intensity
- Falling employee-cost intensity
- Rising selling/admin cost
- Falling selling/admin cost
- Large year-to-year fluctuations

---

# 12. Expense Structure by Business Type

The interpretation should adapt to the company type.

## Manufacturing

Focus on:

- Material cost
- Power and fuel
- Manufacturing expenses
- Inventory-linked cost changes
- Employee cost

## Services / IT

Focus on:

- Employee cost
- Subcontracting
- Selling/admin cost
- Employee-cost-to-sales ratio

## Financial Services

Do not force manufacturing expense categories.

Use sector-specific P&L definitions.

The schema must therefore support:

```text
Universal P&L Metrics
+
Sector-Specific P&L Metrics
```

---

# 13. Other Income Analysis

Calculate:

```text
Other Income / Sales
Other Income / PBT
```

Detect:

- High other-income dependency
- Sudden spikes
- Sudden declines
- Persistent increase
- Negative other income

## Warning

If Other Income contributes materially to PBT, flag:

```text
OTHER INCOME DEPENDENCY
```

Llama should explain:

> A meaningful portion of reported PBT is supported by other income rather than operating profit.

Only generate this observation when the supplied numbers support it.

---

# 14. Depreciation Analysis

Track:

```text
Depreciation
Depreciation / Sales
Depreciation / Operating Profit
YoY Depreciation Growth
```

Detect:

- Rising depreciation burden
- Falling depreciation burden
- Sudden depreciation increase
- Depreciation accelerating faster than sales

This is particularly important for capital-intensive businesses.

---

# 15. Interest Analysis

Track:

```text
Interest Expense
Interest / Sales
Interest / Operating Profit
Interest Coverage
```

## Interest Coverage

```text
Interest Coverage =
(PBT + Interest) / Interest
```

or use the standardized methodology adopted by the financial-data engine.

## Flags

```text
Strong Coverage
Adequate Coverage
Weak Coverage
Negative / Unsafe Coverage
```

Thresholds must be configurable.

---

# 16. PBT Analysis

Calculate:

```text
PBT
PBT Growth
PBT Margin
PBT CAGR
```

## PBT Margin

```text
PBT Margin = PBT / Sales × 100
```

Calculate:

- Current PBT margin
- 10Y average
- 7Y average
- 5Y average
- 3Y average
- Peak
- Lowest
- Current vs historical average

---

# 17. Net Profit Analysis

Calculate:

```text
Net Profit
Net Profit Growth
Net Profit Margin
Net Profit CAGR
```

## Net Profit Margin

```text
NPM = Net Profit / Sales × 100
```

Track:

- Current NPM
- 10Y average NPM
- 5Y average NPM
- 3Y average NPM
- Peak NPM
- Lowest NPM
- Margin trend

---

# 18. EPS Analysis

Track:

```text
EPS
EPS YoY Growth
EPS CAGR
```

Also detect:

- EPS growth faster than PAT
- EPS growth slower than PAT
- EPS dilution
- Share-count impact
- Negative EPS years

EPS should be analyzed separately from PAT because changes in share count can materially affect per-share earnings.

---

# 19. Stock Price CAGR

Stock-price analysis should be handled by the market-data agent/calculation engine.

Required:

### Stock Price CAGR

| Period | CAGR |
|---|---:|
| 10 Years | XX% |
| 5 Years | XX% |
| 3 Years | XX% |
| 1 Year | XX% |

Formula:

```text
Stock Price CAGR =
(Ending Adjusted Price / Beginning Adjusted Price) ^ (1 / Number of Years) - 1
```

Use adjusted prices where the market-data methodology requires it.

Do not let Llama calculate this.

---

# 20. Return on Equity

ROE requires balance-sheet data.

Preferred methodology:

```text
ROE =
Net Profit / Average Shareholders' Equity
```

Calculate:

- 10Y average ROE
- 5Y average ROE
- 3Y average ROE
- Latest ROE
- ROE trend
- ROE volatility

### Required Presentation

| Period | ROE |
|---|---:|
| 10 Years | XX% |
| 5 Years | XX% |
| 3 Years | XX% |
| Last Year | XX% |

---

# 21. Dividend Payout

Calculate:

```text
Dividend Payout =
Dividend / Net Profit
```

Track:

- Current payout
- 3Y average
- 5Y average
- 10Y average
- Payout volatility
- Retention ratio

```text
Retention Ratio = 1 - Dividend Payout
```

---

# 22. Retained Earnings

Calculate:

```text
Retained Earnings =
Net Profit × (1 - Dividend Payout)
```

Track cumulative retained earnings across the analysis period.

This is used for the Buffett's $1 Test.

---

# 23. Buffett's $1 Test

Where required by the screening framework:

```text
Buffett's $1 Test =
Increase in Market Capitalization /
Cumulative Retained Earnings
```

The metric should be presented as:

```text
For every ₹1 retained by the company,
how much additional market value has been created?
```

This should not be interpreted in isolation.

It must be evaluated alongside:

- ROE
- ROCE
- Debt
- Cash flow
- Valuation
- Share dilution
- Business quality

---

# 24. Earnings Quality Analysis

The engine should evaluate the bridge:

```text
Sales
  ↓
Operating Profit
  ↓
Other Income
  ↓
Depreciation
  ↓
Interest
  ↓
PBT
  ↓
Tax
  ↓
Net Profit
```

The system should identify whether earnings are primarily generated by:

1. Core operating performance
2. Margin expansion
3. Other income
4. Lower interest burden
5. Lower tax rate
6. Exceptional/non-operating factors

Only make the attribution when the supplied data supports it.

---

# 25. Revenue vs Profit Relationship

This is one of the highest-value analytical checks.

Compare:

```text
Sales Growth
Operating Profit Growth
PBT Growth
Net Profit Growth
EPS Growth
```

### Case A — Healthy Operating Leverage

```text
Sales Growth       12%
Operating Profit   18%
Net Profit         20%
```

Possible interpretation:

> Earnings are growing faster than revenue, indicating improving profitability and/or operating leverage.

### Case B — Margin Pressure

```text
Sales Growth       18%
Operating Profit   10%
Net Profit          7%
```

Possible interpretation:

> Revenue growth is not translating proportionately into operating and net profit growth, indicating pressure on earnings conversion.

### Case C — Non-operating Support

```text
Operating Profit Growth   10%
PBT Growth                25%
Net Profit Growth         24%
```

The engine should investigate:

- Other income
- Interest
- Depreciation
- Tax

before generating the interpretation.

---

# 26. P&L Inflection Point Detection

Identify major changes in:

- Sales growth
- Profit growth
- OPM
- PBT margin
- NPM
- Other income
- Interest
- Depreciation
- EPS

Examples:

```text
Revenue growth acceleration
Revenue growth deceleration
Margin expansion
Margin contraction
Profit inflection
Loss → profit
Profit → loss
Interest spike
Depreciation spike
Other-income spike
EPS inflection
```

Each inflection should contain:

```json
{
  "year": "FY2026",
  "type": "margin_compression",
  "metric": "OPM",
  "observation": "OPM declined versus recent historical levels",
  "severity": "medium"
}
```

---

# 27. P&L Consistency Analysis

Measure:

- Number of positive-growth years
- Number of negative-growth years
- Number of profitable years
- Number of loss years
- Standard deviation of growth
- Standard deviation of margins
- Maximum drawdown in profit
- Maximum sales decline

A company with high CAGR but extreme volatility should not automatically receive a high P&L-quality score.

---

# 28. 10-Year / 7-Year / 5-Year / 3-Year Trend Table

Include a dedicated table.

| Metric | 10Y | 7Y | 5Y | 3Y |
|---|---:|---:|---:|---:|
| Sales Growth | | | | |
| PBT Growth | | | | |
| PBT Margin | | | | |
| P/E | | | | |

Additional metrics can be added:

| Metric | 10Y | 7Y | 5Y | 3Y |
|---|---:|---:|---:|---:|
| Net Profit CAGR | | | | |
| EPS CAGR | | | | |
| OPM | | | | |
| NPM | | | | |
| ROE | | | | |

---

# 29. Common-Size P&L Analysis

Every expense should also be analyzed as a percentage of sales.

Base:

```text
Sales = 100%
```

Example:

| Metric | FY-10 | FY-5 | FY | TTM |
|---|---:|---:|---:|---:|
| Sales | 100% | 100% | 100% | 100% |
| Material Cost | | | | |
| Power & Fuel | | | | |
| Manufacturing Expenses | | | | |
| Employee Cost | | | | |
| Selling & Admin | | | | |
| Operating Profit | | | | |
| Other Income | | | | |
| Depreciation | | | | |
| Interest | | | | |
| PBT | | | | |
| Tax | | | | |
| Net Profit | | | | |

This makes structural changes in the P&L easier to identify.

---

# 30. P&L Red Flags

Automatically generate flags where applicable.

## Growth

```text
DECLINING SALES GROWTH
NEGATIVE SALES GROWTH
HIGH GROWTH VOLATILITY
PROFIT GROWTH BELOW SALES GROWTH
```

## Margins

```text
MARGIN COMPRESSION
MARGIN VOLATILITY
LOWEST-HISTORICAL MARGIN
```

## Expenses

```text
RISING MATERIAL COST
RISING EMPLOYEE COST
RISING SELLING/ADMIN COST
UNUSUAL EXPENSE SPIKE
```

## Earnings Quality

```text
HIGH OTHER-INCOME DEPENDENCY
HIGH INTEREST BURDEN
RISING DEPRECIATION BURDEN
TAX-DRIVEN PROFIT GROWTH
```

## EPS

```text
EPS DILUTION
EPS GROWTH BELOW PAT GROWTH
```

---

# 31. P&L Positive Signals

Automatically identify:

```text
CONSISTENT SALES GROWTH
ACCELERATING SALES GROWTH
PROFIT GROWTH ABOVE SALES GROWTH
EXPANDING OPM
EXPANDING NPM
HIGH INTEREST COVERAGE
DECLINING COST INTENSITY
CONSISTENT EPS GROWTH
HIGH ROE
STABLE MARGINS
POSITIVE EARNINGS CONSISTENCY
```

---

# 32. P&L Quality Score

The engine may generate a separate P&L score.

Example:

```text
P&L QUALITY SCORE
────────────────────────

Sales Growth             8/10
Profit Growth            8/10
Growth Consistency       7/10
Operating Margins        7/10
Profit Conversion        8/10
EPS Growth               8/10
Earnings Quality         7/10
────────────────────────
Overall P&L Score        7.6/10
```

The score must be generated by deterministic rules.

Llama explains the score.

Llama must not arbitrarily assign the numerical score.

---

# 33. Llama Interpretation Layer

Llama receives the verified P&L analysis object.

Example input:

```json
{
  "sales_cagr": {
    "10y": 0.26,
    "5y": 0.14,
    "3y": 0.10,
    "ttm": 0.13
  },

  "profit_cagr": {
    "10y": 0.50,
    "5y": 0.08,
    "3y": 0.04,
    "ttm": 0.10
  },

  "current_opm": 0.16,
  "five_year_average_opm": 0.18,

  "growth_trend": "moderating",
  "margin_trend": "contracting"
}
```

Llama should generate:

```text
P&L Assessment

The company has delivered strong long-term sales growth, but
the pace of growth has moderated over the more recent 3–5 year
periods. Historical profit growth has significantly exceeded
sales growth, indicating that earnings benefited from stronger
profit conversion over the longer period.

More recently, profit growth has moderated and current operating
margins are below the recent historical average. The key issue
to monitor is whether earnings growth can re-accelerate while
operating margins stabilise.
```

---

# 34. Llama Rules

Llama MUST:

1. Use only supplied data.
2. Never invent numbers.
3. Never invent causes.
4. Never change calculated values.
5. Preserve financial periods.
6. Preserve units.
7. Distinguish historical data from TTM.
8. Distinguish facts from interpretation.
9. Mention uncertainty where appropriate.
10. Prioritize material changes.
11. Compare recent performance with historical performance.
12. Highlight contradictory signals.
13. Avoid generic statements.
14. Avoid unsupported investment recommendations.

---

# 35. Llama P&L Output

Recommended JSON:

```json
{
  "pnl_analysis": {

    "overall_assessment": {
      "summary": "",
      "strength": "",
      "concern": ""
    },

    "sales_growth": {
      "assessment": "",
      "trend": "",
      "key_observation": ""
    },

    "profit_growth": {
      "assessment": "",
      "trend": "",
      "key_observation": ""
    },

    "margin_analysis": {
      "assessment": "",
      "trend": "",
      "key_observation": ""
    },

    "expense_analysis": {
      "assessment": "",
      "key_changes": []
    },

    "earnings_quality": {
      "assessment": "",
      "key_points": []
    },

    "eps_analysis": {
      "assessment": "",
      "key_observation": ""
    },

    "inflection_points": [],

    "positive_signals": [],

    "red_flags": [],

    "things_to_monitor": []
  }
}
```

---

# 36. PDF Presentation

The P&L section should contain:

## Section Header

```text
PROFIT & LOSS ANALYSIS
10-Year Financial Performance
```

## Part 1 — 10-Year P&L Table

Full annual P&L table.

## Part 2 — Growth Cards

```text
┌────────────────────┐
│ Compounded Sales   │
│ Growth             │
│                    │
│ 10Y       XX%      │
│ 5Y        XX%      │
│ 3Y        XX%      │
│ TTM       XX%      │
└────────────────────┘

┌────────────────────┐
│ Compounded Profit  │
│ Growth             │
│                    │
│ 10Y       XX%      │
│ 5Y        XX%      │
│ 3Y        XX%      │
│ TTM       XX%      │
└────────────────────┘

┌────────────────────┐
│ Stock Price CAGR   │
│                    │
│ 10Y       XX%      │
│ 5Y        XX%      │
│ 3Y        XX%      │
│ 1Y        XX%      │
└────────────────────┘

┌────────────────────┐
│ Return on Equity   │
│                    │
│ 10Y       XX%      │
│ 5Y        XX%      │
│ 3Y        XX%      │
│ Last Year XX%      │
└────────────────────┘
```

---

# 37. Recommended P&L Charts

The renderer should support:

### Revenue Trend

10-year Sales trend.

### Operating Profit Trend

10-year Operating Profit trend.

### Net Profit Trend

10-year Net Profit trend.

### OPM Trend

10-year Operating Profit Margin.

### Revenue vs Profit Growth

Compare:

```text
Sales Growth
PBT Growth
Net Profit Growth
EPS Growth
```

### ROE Trend

10-year ROE.

### Common-Size P&L

Expense composition over time.

---

# 38. Final P&L Interpretation

The final P&L section should conclude with a concise summary.

Recommended structure:

```text
P&L CONCLUSION

Growth:
[Interpretation]

Profitability:
[Interpretation]

Margins:
[Interpretation]

Earnings Quality:
[Interpretation]

Recent Trend:
[Interpretation]

Key Concern:
[Interpretation]

What to Monitor:
[Interpretation]
```

---

# 39. Example Final Output

```text
P&L CONCLUSION

Growth:
Long-term sales growth has been strong, but recent growth has
moderated compared with the 10-year trajectory.

Profitability:
Historical profit growth has exceeded revenue growth, indicating
stronger earnings conversion over the longer period.

Margins:
Current operating margins are below the recent historical average,
making margin recovery an important variable to monitor.

Earnings Quality:
The analysis should assess whether earnings are primarily driven
by core operations or supported by other income, lower interest
costs or tax effects.

Recent Trend:
Recent earnings growth is weaker than the long-term historical
growth rate.

What to Monitor:
Revenue growth recovery, operating-margin stability, expense
intensity and EPS growth.
```

---

# 40. Complete P&L Analysis Flow

```text
                  10+ YEAR FINANCIAL DATA
                           |
                           v
                  ┌─────────────────┐
                  │ P&L NORMALIZER  │
                  └────────┬────────┘
                           |
                           v
                  ┌─────────────────┐
                  │ P&L CALCULATOR  │
                  └────────┬────────┘
                           |
          ┌────────────────┼─────────────────┐
          |                |                 |
          v                v                 v
       Growth            Margins          Expenses
          |                |                 |
          v                v                 v
        Profit           Quality          Earnings
          |                |                 |
          └────────────────┼─────────────────┘
                           |
                           v
                  ┌─────────────────┐
                  │ TREND DETECTOR  │
                  └────────┬────────┘
                           |
                           v
                  ┌─────────────────┐
                  │ P&L ANALYSIS    │
                  │     OBJECT      │
                  └────────┬────────┘
                           |
                           v
                         LLAMA
                           |
                           v
                  ┌─────────────────┐
                  │ INTERPRETATION  │
                  └────────┬────────┘
                           |
                           v
                  ┌─────────────────┐
                  │ REPORT BLUEPRINT│
                  └────────┬────────┘
                           |
                           v
                    PDF RENDERER
```

---

# 41. Core Design Principle

The P&L system must maintain a strict separation:

```text
DATA AGENTS
    ↓
Provide verified numbers

CALCULATION ENGINE
    ↓
Calculate ratios, CAGR and trends

LLAMA
    ↓
Interpret the numbers

PDF RENDERER
    ↓
Present the analysis
```

Never make Llama responsible for primary financial calculations.

---

# 42. Minimum P&L Output

Every company report should contain at minimum:

1. 10-year P&L table
2. TTM P&L
3. YoY sales growth
4. YoY PBT growth
5. YoY net profit growth
6. YoY EPS growth
7. 10Y Sales CAGR
8. 7Y Sales CAGR
9. 5Y Sales CAGR
10. 3Y Sales CAGR
11. TTM Sales Growth
12. 10Y Profit CAGR
13. 7Y Profit CAGR
14. 5Y Profit CAGR
15. 3Y Profit CAGR
16. TTM Profit Growth
17. OPM
18. PBT Margin
19. Net Profit Margin
20. Expense composition
21. Other Income analysis
22. Interest coverage
23. EPS CAGR
24. Dividend payout
25. ROE
26. Stock Price CAGR
27. Long-term vs short-term trend comparison
28. P&L red flags
29. P&L positive signals
30. Llama-generated P&L interpretation

---

# 43. Recommended Report Order

```text
COMPANY & BUSINESS OVERVIEW
        ↓
SECTOR / INDUSTRY ANALYSIS
        ↓
PROFIT & LOSS ANALYSIS
        ↓
BALANCE SHEET ANALYSIS
        ↓
CASH FLOW ANALYSIS
        ↓
CAPITAL EFFICIENCY
        ↓
MANAGEMENT & GOVERNANCE
        ↓
VALUATION
        ↓
RISK ANALYSIS
        ↓
BULL / BASE / BEAR
        ↓
FINAL FUNDAMENTAL ASSESSMENT
```

The P&L section therefore becomes a **full analytical module**, not merely a reproduction of the financial statement.
