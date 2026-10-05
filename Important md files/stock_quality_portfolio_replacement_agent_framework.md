# Stock Quality & Portfolio Replacement Agent Framework

## Purpose

This framework is designed for an AI agent that reviews stocks in a portfolio or watchlist and decides whether a stock should be:

- Kept
- Watched
- Added gradually
- Replaced
- Avoided
- Treated only as a tactical/speculative position

The agent must **not make decisions using one score alone**.

The core logic is:

> **Quality → Fundamentals → Relative Strength → Technical → Valuation → Portfolio Comparison → Position Size → Asset Allocation**

The aim is not only to find "good companies."  
The aim is to identify:

1. Strong businesses
2. Improving businesses
3. Deteriorating businesses
4. Stocks showing resilience during weak market conditions
5. Better same-sector replacement opportunities
6. Better opportunities than existing portfolio holdings

---

# 1. Core Principle

Do not combine every factor into one score too early.

Each score answers a different question:

| Dimension | Main Question |
|---|---|
| Business Quality | Is this a good business? |
| Fundamental Strength | Are the financial numbers strong? |
| Quantitative Strength | Are measurable trends improving? |
| Relative Strength | Is the stock performing better than market/sector/portfolio? |
| Technical Strength | Is price behaviour confirming strength or reversal? |
| Valuation | Is the current price reasonable? |
| Portfolio Fit | Is this better than what I already own? |
| Position Size | How much capital should be allocated? |

A strong technical score must **not repair poor fundamentals**.

A cheap valuation must **not repair poor business quality**.

---

# 2. Quality Score Framework

Use Quality Score as the first screening gate.

| Quality Score | Classification | Default Action |
|---:|---|---|
| 65+ | Strong quality | Preferred/core candidate |
| 50–64 | Good / acceptable | Investable |
| 40–49 | Borderline | Watch / improving candidate |
| Below 40 | Weak | Usually replacement candidate |
| Below 30 | Very weak | Avoid except deliberate turnaround/speculative case |

## Important Rule

- **50 = minimum practical quality gate**
- **65+ = preferred quality range**
- Do not automatically remove a stock between 40 and 49.
- A 40–49 stock can remain on watch if:
  - Trend is improving
  - Valuation is fair or cheap
  - Relative strength is good
  - Fundamentals are improving
  - Quality momentum is positive

---

# 3. Business Quality / Qualitative Score

This score should measure the nature of the business, not share-price movement.

Possible factors:

- Management quality
- Governance
- Capital allocation discipline
- Competitive advantage
- Pricing power
- Brand strength
- Customer concentration
- Industry structure
- Regulatory risk
- Earnings predictability
- Business durability
- Cyclicality
- Promoter behaviour
- Execution track record

## Special Situational Logic

If the overall sector is weak but the stock is behaving well, ask:

> Why is this company holding up better?

Possible explanations:

- Better earnings
- Better margin resilience
- Stronger cash flow
- Falling debt
- Strong order book
- Better management guidance
- Stronger balance sheet
- Sector leadership
- Better product mix

These reasons can strengthen the qualitative/business-quality assessment.

Do **not** directly classify price outperformance itself as business quality.

---

# 4. Fundamental Score

Fundamental Score must be based mainly on hard financial data.

Suggested inputs:

- Revenue growth
- PAT growth
- EPS growth
- ROE
- ROCE
- Operating margin
- Net margin
- Free cash flow
- CFO/PAT conversion
- Debt/equity
- Interest coverage
- Working capital trend
- Share dilution
- Dividend sustainability
- Balance-sheet strength
- Earnings consistency

## Growth / "Double In" Metric

"Double in X years" is useful as a growth indicator, but it must not dominate quality.

Example:

A company whose PAT doubles in 1.5 years may simply be recovering from a very low base.

Therefore:

> Fast doubling time ≠ automatically high-quality business

Use it together with:

- 3Y/5Y revenue CAGR
- 3Y/5Y PAT CAGR
- EPS CAGR
- FCF growth
- ROE/ROCE trend

---

# 5. Quantitative Score

Quantitative Score should capture measurable behaviour and improvement.

Possible factors:

- Revenue CAGR
- PAT CAGR
- EPS CAGR
- Margin change
- ROE/ROCE change
- Debt reduction
- Earnings revisions
- Drawdown
- Volatility
- Risk-adjusted return
- Relative return vs index
- Relative return vs sector
- Relative return vs existing portfolio
- Quality Score change over time

This score answers:

> Are the measurable numbers getting better or worse?

---

# 6. Relative Strength Score

Relative strength must be measured separately.

Compare the stock against:

1. Market benchmark
2. Sector benchmark
3. Existing portfolio holdings
4. Same-sector alternatives

Example:

- Nifty: -10%
- Sector: -8%
- Stock: -2%

This stock is showing resilience.

Another example:

- Nifty: +15%
- Sector: +22%
- Stock: +5%

The stock is positive in absolute terms, but weak relative to its environment.

## Suggested Relative Strength Fields

- 1M stock vs market
- 3M stock vs market
- 6M stock vs market
- 1Y stock vs market
- 1M stock vs sector
- 3M stock vs sector
- 6M stock vs sector
- 1Y stock vs sector
- Drawdown vs benchmark
- Recovery speed
- New-high participation
- Relative strength percentile within sector

---

# 7. Technical Score

Technical Score should measure market behaviour.

Possible inputs:

- Trend structure
- Higher highs / higher lows
- Moving average position
- Moving average slope
- RSI
- RSI relative strength
- MACD
- MACD histogram
- Volume confirmation
- Breakout/breakdown
- Support/resistance
- Reversal structure
- Momentum
- Volatility contraction
- Base formation
- Price recovery after drawdown

## Key Rule

Do not allow this:

> Fundamental Score = 30  
> Technical Score = 90  
> Average = 60  
> Result = BUY

This is not acceptable for a long-term quality portfolio.

Instead:

> If fundamentals are below the minimum gate, strong technicals can only make it a tactical/speculative candidate.

---

# 8. Valuation Score

Valuation should be used **after** business quality and fundamentals.

Possible inputs:

- P/E vs own history
- P/E vs sector
- PEG
- EV/EBITDA
- P/B
- FCF yield
- Earnings yield
- DCF range
- Relative valuation percentile
- Growth-adjusted valuation

## Interpretation

### Strong quality + expensive
Good business, poor entry price.

### Strong quality + fair
Investable if other conditions support.

### Strong quality + cheap
Potential high-conviction candidate.

### Weak quality + cheap
Possible value trap.

### Weak quality + expensive
Usually avoid.

## Core Rule

> Cheap valuation must not compensate for weak fundamentals.

---

# 9. Trend Classification

Trend should reflect business/fundamental direction, not just price.

Possible states:

- Improving
- Stable
- Cyclical
- Declining
- Insufficient data

Examples of improving trend:

- ROCE rising
- Margins rising
- Debt falling
- EPS revisions improving
- Free cash flow improving
- Revenue/PAT growth accelerating

Examples of declining trend:

- Margins falling
- Debt rising
- ROCE falling
- Cash flow weakening
- Earnings downgrades
- Persistent negative growth

---

# 10. Quality Momentum

Do not use only the current Quality Score.

Track how quality is changing.

Example A:

- 12 months ago: 39
- 6 months ago: 46
- Today: 54

Quality Momentum = +15

Interpretation:

> Improving company

Example B:

- 12 months ago: 72
- 6 months ago: 65
- Today: 54

Quality Momentum = -18

Interpretation:

> Deteriorating company

Both stocks currently score 54, but the direction is completely different.

## Recommended Fields

- Current Quality Score
- 6M Ago Quality Score
- 12M Ago Quality Score
- Quality Momentum 6M
- Quality Momentum 12M
- Direction: Improving / Stable / Declining

---

# 11. Sector-Relative Quality

Avoid using only absolute Quality Score.

Also calculate:

> Sector Quality Percentile

Example:

- Pharma Stock A: Quality Score 58, Sector Rank #3/30
- IT Stock B: Quality Score 65, Sector Rank #15/25

Stock A may be stronger relative to its own sector.

Suggested labels:

- Top 10%
- Top 25%
- Top 40%
- Top 50%
- Bottom 50%

Suggested rule:

> Core portfolio candidate = Quality Score >= 50 AND preferably Top 40% within sector

A score of 65+ may qualify as preferred quality, subject to red flags.

---

# 12. Portfolio Comparison Logic

Do not ask only:

> Is this stock good?

Ask:

> Is this stock better than what I already own?

For every replacement decision, compare:

- Existing stock
- Candidate stock
- Same-sector peer group

Compare them on:

- Fundamental Score
- Quality Score
- Quality Momentum
- Quantitative Score
- Relative Strength
- Technical Score
- Valuation
- Risk
- Drawdown
- Sector rank
- Expected upside
- Downside risk

## Example

Existing Stock A:

- Fundamental: 72
- Quality: 75
- Quantitative: 42
- Technical: 38
- Valuation: Expensive

Candidate Stock B:

- Fundamental: 67
- Quality: 68
- Quantitative: 80
- Technical: 76
- Valuation: Fair

Interpretation:

Stock A may still be the better business.

Stock B may currently be the better investment opportunity.

Do not confuse:

> Better company

with:

> Better current opportunity

---

# 13. Position Sizing Logic

Position sizing comes **after** all screening.

Suggested logic:

| Situation | Position Approach |
|---|---|
| Strong fundamentals + strong quality + strong relative strength + fair/cheap valuation | Higher allocation |
| Strong fundamentals + weak technicals | Smaller starting position or wait |
| Strong fundamentals + expensive valuation | Hold/watch, limited fresh allocation |
| Quality 50–64 + improving + strong momentum | Normal/moderate allocation |
| Quality 40–49 + improving + strong relative strength | Small starter position/watchlist |
| Weak fundamentals + strong technical momentum | Tactical/speculative only |
| Weak fundamentals + declining trend | Avoid/replace |

Position size should also depend on:

- Portfolio concentration
- Sector exposure
- Correlation with existing holdings
- Volatility
- Downside risk
- Liquidity
- Conviction level
- Time horizon

---

# 14. Asset Allocation Logic

Do not make stock selection without portfolio context.

Before recommending a position, the agent must check:

- Existing sector allocation
- Existing stock concentration
- Cash allocation
- Equity allocation
- Gold allocation
- Debt/fixed income allocation
- International allocation
- Portfolio volatility
- Drawdown tolerance

A good stock can still be a bad portfolio addition if the sector is already overweight.

---

# 15. Decision Matrix

| Situation | Classification |
|---|---|
| Quality 65+ + Improving + Fair/Cheap | High-conviction candidate |
| Quality 50–64 + Improving | Investable / emerging quality |
| Quality 40–49 + Improving + strong relative strength | Watch / recovery candidate |
| Quality 40–49 + Declining | Replacement candidate |
| Quality <40 + strong technical momentum | Tactical/speculative only |
| Quality <40 + Declining | Avoid / replace |
| Quality 65+ + Expensive | Good business, wait for price |
| Quality 65+ + weak technical | Good business, poor timing |
| Weak quality + Cheap | Possible value trap |
| Strong quality + Cheap + improving trend | Priority candidate |

---

# 16. Agent Decision Flow

```text
START
  |
  v
CHECK BUSINESS QUALITY
  |
  v
CHECK FUNDAMENTAL SCORE
  |
  +--> Quality >= 50?
  |        |
  |        +--> YES --> Continue
  |        |
  |        +--> NO --> Is Quality 40-49 and Improving?
  |                     |
  |                     +--> YES --> Watch/Recovery Bucket
  |                     |
  |                     +--> NO --> Replace/Avoid Bucket
  |
  v
CHECK QUALITY MOMENTUM
  |
  v
CHECK QUANTITATIVE STRENGTH
  |
  v
CHECK RELATIVE STRENGTH
  |
  v
CHECK TECHNICAL STRUCTURE
  |
  v
CHECK VALUATION
  |
  v
COMPARE WITH SAME-SECTOR STOCKS
  |
  v
COMPARE WITH EXISTING PORTFOLIO HOLDING
  |
  v
IS CANDIDATE CLEARLY BETTER?
  |
  +--> NO --> Keep existing / watch
  |
  +--> YES --> Define replacement logic
                |
                v
          DEFINE POSITION SIZE
                |
                v
          CHECK SECTOR ALLOCATION
                |
                v
          CHECK TOTAL ASSET ALLOCATION
                |
                v
              FINAL ACTION
```

---

# 17. Minimum Gates

Recommended default gates:

## Long-Term / Core Portfolio

- Quality Score >= 50
- No major governance red flag
- No serious balance-sheet weakness
- No persistent deterioration in cash flow
- Prefer positive or stable Quality Momentum
- Prefer Top 40% sector quality ranking

## Preferred Core Candidate

- Quality Score >= 65
- Improving or stable fundamentals
- Good sector rank
- Fair or cheap valuation preferred
- Positive relative strength preferred

## Recovery / Watch Candidate

- Quality Score 40–49
- Positive Quality Momentum
- Improving fundamentals
- Strong relative strength
- Fair/cheap valuation
- No major governance or balance-sheet red flags

## Tactical Candidate

- Weak fundamentals but strong technical momentum
- Must remain outside the core-quality bucket
- Smaller position only
- Clear exit rule required

---

# 18. Avoid Double Counting

The agent must check whether the same signal is being counted twice.

Example:

- Relative strength included in Quantitative Score
- Relative strength again included fully in Technical Score

This can distort the result.

Each signal should ideally have one primary home.

Suggested separation:

### Fundamental
Financial statements and business economics

### Quality
Business durability and management characteristics

### Quantitative
Measured changes and statistical behaviour

### Relative Strength
Performance vs benchmarks and peers

### Technical
Price/volume structure and timing

### Valuation
Price paid relative to business value

---

# 19. Sector-Specific Scoring

Do not apply the same formula blindly to all sectors.

Examples:

## Banks / Financials

Debt cannot be evaluated the same way as manufacturing companies.

Focus more on:

- ROA
- ROE
- NIM
- GNPA
- NNPA
- Credit cost
- CASA
- Loan growth
- Deposit growth
- Provision coverage
- Capital adequacy

## IT Services

Focus more on:

- Revenue growth
- EBIT margin
- Deal wins
- Attrition
- Client concentration
- FCF
- Return ratios
- Pricing
- Utilisation

## Pharma

Focus more on:

- Product pipeline
- Regulatory approvals
- USFDA risk
- R&D productivity
- Geographic mix
- Margin
- FCF
- Specialty contribution

## Capital Goods / Industrials

Focus more on:

- Order book
- Order inflow
- Execution
- Working capital
- ROCE
- Capacity utilisation
- Debt
- Cash conversion

The agent should use sector-specific fundamentals before producing the final quality judgement.

---

# 20. Suggested Agent Output Format

For every stock, return:

## Stock Summary

- Symbol:
- Sector:
- Current Price:
- Quality Score:
- Fundamental Score:
- Quantitative Score:
- Relative Strength Score:
- Technical Score:
- Valuation:
- Trend:
- Quality Momentum:
- Sector Quality Percentile:

## Business Interpretation

- What is strong?
- What is weak?
- What is improving?
- What is deteriorating?
- Why is the stock outperforming or underperforming?

## Relative Comparison

- vs Market:
- vs Sector:
- vs Existing Portfolio Holding:
- vs Best Same-Sector Alternative:

## Classification

Choose one:

- Core Quality
- Investable
- Improving / Watch
- Recovery Candidate
- Tactical Only
- Replacement Candidate
- Avoid

## Portfolio Action

Choose one:

- Hold
- Add gradually
- Add on confirmation
- Reduce
- Replace
- Avoid
- Watch

## Position Sizing Guidance

- Small
- Medium
- High
- Tactical only

Include reason.

## Replacement Recommendation

If replacement is suggested:

- Existing Stock:
- Replacement Candidate:
- Why candidate is better:
- Fundamental difference:
- Quality difference:
- Valuation difference:
- Relative strength difference:
- Technical difference:
- Risk difference:

---

# 21. Agent Prompt

Use the following logic when reviewing a stock or portfolio:

> Do not judge a stock using one score alone. First assess Business Quality and Fundamental Strength. Treat Quality Score >= 50 as the practical minimum gate for a long-term core portfolio and 65+ as preferred quality. Stocks scoring 40–49 should not be rejected automatically if fundamentals are improving, Quality Momentum is positive, valuation is reasonable, and relative strength is strong.
>
> Separate Business Quality, Fundamental Score, Quantitative Score, Relative Strength, Technical Score and Valuation. Do not allow strong technicals or cheap valuation to compensate for structurally weak fundamentals.
>
> If a stock performs better while the market or its sector is weak, identify why. Separate the fundamental reason from the measurable price-based relative strength.
>
> Compare each stock against its sector, the market and the user's existing portfolio. Do not ask only whether the stock is good. Ask whether it is a better opportunity than the stock already owned.
>
> Track Quality Momentum using current, 6-month and 12-month scores where possible. A rising quality score and a falling quality score with the same current value must be treated differently.
>
> Use sector-specific financial metrics. Do not apply manufacturing leverage rules to banks or other financial companies.
>
> After the stock passes the quality and fundamental gates, use quantitative strength, relative strength, technical structure and valuation to determine entry timing and position sizing.
>
> Only after individual stock analysis should you decide portfolio replacement, sector allocation and total asset allocation.
>
> Return a clear classification, action, reasoning, major risks and replacement candidate where relevant.

---

# 22. Final Philosophy

The framework is not:

> High score = Buy  
> Low score = Sell

The framework is:

> **Understand the business → Check the numbers → Understand the direction → Measure relative strength → Check price behaviour → Check valuation → Compare with what you already own → Decide allocation.**

The goal is to build a portfolio of strong or improving businesses while continuously comparing them against better alternatives.
