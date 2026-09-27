# Consumer Discretionary → Media, Entertainment & Publication — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

## 1. Purpose

This is a standalone, implementation-ready framework for companies classified under:

**Macro Sector:** Consumer Discretionary  
**Sector Value:** Media, Entertainment & Publication  
**Industries:** Media; Printing & Publication; Entertainment

The framework is designed for a fundamental-analysis engine that moves through:

**RAW DATA → NORMALIZATION → CALCULATED METRICS → TREND → PEER → CAUSAL ANALYSIS → RED FLAGS → SCORING → INVESTMENT THESIS**

The source framework classifies this sector value across television, digital media, advertising, broadcasting, publishing, printing, film, music, gaming, entertainment, sports/media rights and subscription businesses. Its stated key drivers are advertising revenue, subscription revenue, content monetization, audience, engagement, ARPU, content library, distribution and rights economics. 

> Implementation rule: do not compare every company in this Sector Value using the same operating metrics. First classify the company's actual business model and then activate the relevant metric modules.

---

# 2. Business Classification

Before calculating ratios, classify the company.

## 2.1 Media

Possible business models:

- Television
- Digital media
- Advertising-led media
- Broadcasting
- News/media networks
- Subscription-led media
- Hybrid advertising + subscription
- Sports/media rights
- Digital content platforms

Core economic drivers:

- Audience
- Reach
- Engagement
- Advertising inventory
- Ad rates
- Subscription base
- ARPU
- Digital share
- Distribution
- Content monetization

Core causal chain:

**Audience → Engagement → Inventory / Subscribers → Monetization → Revenue → Content / Distribution Cost → Margin → Cash**

---

## 2.2 Printing & Publication

Possible business models:

- Newspapers
- Magazines
- Books
- Commercial printing
- Publishing
- Print + digital publishing
- Subscription-led publications
- Advertising-led publications

Core economic drivers:

- Circulation
- Print volume
- Realisation
- Paper cost
- Print utilization
- Advertising revenue
- Subscription revenue
- Digital transition

Core causal chain:

**Circulation / Print Volume → Realisation + Advertising → Revenue → Paper / Printing Cost → Margin → Cash**

---

## 2.3 Entertainment

Possible business models:

- Film production
- Film distribution
- Music
- Gaming
- Streaming
- Content libraries
- Theatre/exhibition-linked businesses
- Sports/media rights
- Content licensing
- Subscription entertainment
- Advertising-supported entertainment

Core economic drivers:

- Content spend
- Content library
- Releases
- Box-office revenue where applicable
- Streaming subscribers
- ARPU
- Engagement
- Rights income
- Production cost
- Monetization window

Core causal chain:

**Audience → Content Engagement → Monetization → Revenue → Content Cost → Contribution / EBITDA → Cash**

---

# 3. Company Revenue Architecture

The engine must decompose revenue before interpreting growth.

Track:

- Advertising revenue
- Subscription revenue
- Content licensing revenue
- Distribution revenue
- Rights income
- Box-office revenue where applicable
- Print revenue
- Publishing revenue
- Digital revenue
- Other operating revenue
- Other income

Separate:

**Core operating revenue vs other income**

and:

**Recurring / repeatable revenue vs volatile / event-driven revenue**

and where possible:

**Organic growth vs acquisition-led growth**

---

# 4. Audience & Demand Engine

Audience is the economic starting point for many media and entertainment businesses.

Track wherever disclosed:

- Total audience
- Unique users
- Monthly active users
- Daily active users
- Reach
- Watch time
- Page views
- Video views
- Downloads
- Subscribers
- Paid subscribers
- Paying customers
- Engagement time
- Content consumption
- Average session duration
- Retention
- Churn
- Repeat usage

Do not treat audience growth as automatically equivalent to revenue growth.

Analyze:

**Audience Growth → Engagement → Monetizable Inventory → Monetization Rate → Revenue**

Flag situations where:

- Audience rises but monetization falls
- Engagement rises but ARPU declines materially
- Subscribers rise but churn remains high
- Traffic rises mainly from low-value users
- Revenue growth is substantially below audience growth without a clear strategic explanation

---

# 5. Advertising Economics

For advertising-led businesses, track:

- Advertising revenue
- Ad inventory
- Ad impressions where available
- Fill rate where available
- Ad rates
- Revenue per impression / monetized user where available
- Digital advertising share
- TV advertising share
- Print advertising share
- Customer / advertiser concentration
- Sector mix of advertisers
- Premium inventory mix

Analyze advertising revenue as:

**Audience × Engagement × Inventory × Fill / Monetization Rate × Ad Rate**

Where data permits, separate:

- Volume effect
- Rate effect
- Mix effect
- Digital transition
- Geographic effect
- Event-driven advertising

### Advertising quality

Assess whether revenue growth comes from:

1. More audience
2. More engagement
3. More inventory
4. Better ad rates
5. Better advertiser mix
6. Higher digital monetization
7. Temporary events

Do not assume higher ad revenue automatically means stronger underlying economics.

---

# 6. Subscription Economics

For subscription businesses track:

- Opening subscribers
- Gross additions
- Churn
- Closing subscribers
- Paid subscribers
- ARPU
- Subscription revenue
- Annualized recurring revenue where relevant
- Renewal rate
- Average subscription duration
- Premium vs basic mix
- Geographic mix

Core chain:

**Opening Subscribers + Additions − Churn = Closing Subscribers**

Then:

**Subscribers × ARPU → Subscription Revenue**

Analyze:

- Subscriber growth
- ARPU growth
- Revenue growth
- Churn trend
- Retention
- Pricing changes
- Premiumization
- Promotional pricing
- Customer acquisition economics

Flag:

- Subscriber growth driven primarily by discounts
- ARPU decline without strategic rationale
- Rising acquisition cost
- High churn after price increases
- Revenue growth materially below subscriber growth

---

# 7. Content Economics

Content is often the key economic asset and cost driver.

Track:

- Content spend
- Production cost
- Acquisition cost
- Content library value
- Number of releases
- Content hours
- New titles
- Renewal spend
- Sports/media rights cost
- Licensing cost
- Content amortization
- Content capitalization where relevant
- Content monetization window
- Rights income
- Licensing income

Analyze:

**Content Spend → Audience / Engagement → Monetization → Revenue → Cash Return**

Do not judge content spending only by absolute growth.

Assess:

- Content spend / revenue
- Content spend / subscriber
- Content spend / audience
- Revenue generated per content unit where calculable
- Library monetization
- New content vs catalogue economics
- Rights renewal risk
- Hit-driven volatility

---

# 8. Content Library Analysis

Where a meaningful content library exists, track:

- Gross content assets where disclosed
- Net content assets
- Additions
- Amortization
- Impairments
- Licensing income
- Catalogue monetization
- Remaining monetization window
- Rights ownership
- Exclusive vs non-exclusive rights

Flag:

- Large capitalized content balances with weak monetization
- Repeated content impairments
- Rising content spend without proportional revenue growth
- Short monetization windows combined with high acquisition costs
- Dependence on a small number of successful titles

---

# 9. Printing & Publication Operating Metrics

For printing and publication businesses track:

- Circulation
- Volume
- Copies sold
- Subscription base
- Realisation per copy
- Advertising revenue
- Subscription revenue
- Print utilization
- Paper consumption
- Paper cost
- Newsprint / paper price exposure
- Print capacity
- Digital revenue
- Digital audience
- Digital subscribers

Analyze:

**Circulation × Realisation → Subscription / Print Revenue**

and:

**Advertising Volume × Ad Rate → Advertising Revenue**

Then:

**Revenue → Paper + Printing + Distribution Cost → EBITDA → CFO**

---

# 10. Paper & Input-Cost Analysis

For print-heavy companies, paper can be a major cost driver.

Track:

- Paper cost
- Paper cost / revenue
- Paper price movement
- Imported vs domestic paper exposure where disclosed
- Currency exposure where relevant
- Inventory of paper
- Procurement contracts where disclosed

Analyze:

**Paper Price → Gross Margin → EBITDA Margin → CFO**

Separate:

- Input-price effect
- Volume effect
- Pricing effect
- Mix effect
- Productivity effect

Flag margin expansion caused primarily by temporary paper-cost declines.

---

# 11. Print Capacity & Utilization

Track:

- Installed print capacity
- Print utilization
- Print volumes
- Number of printing facilities
- Capacity additions
- Capacity closures
- Capex
- Revenue / printing capacity where calculable

Analyze:

**Volume → Utilization → Fixed-cost absorption → Margin**

Flag:

- Low utilization with continued capex
- Capacity additions without demand visibility
- Declining print volumes despite capacity expansion

---

# 12. Entertainment Release Economics

For film / content businesses, track where applicable:

- Number of releases
- Release frequency
- Production budget
- Marketing spend
- Distribution cost
- Box-office revenue
- Theatre share
- Digital rights income
- Satellite rights
- Music rights
- International rights
- Licensing income
- Content amortization

Analyze:

**Content Investment → Release → Audience → Box Office / Rights / Streaming → Revenue → Content Cost → Cash**

Do not treat one successful release as proof of recurring business quality.

Measure:

- Hit rate
- Revenue concentration
- Average revenue per release
- Median release performance where sufficient data exists
- Content-cost recovery
- Rights realization
- Library monetization

---

# 13. Streaming / Digital Entertainment

Track:

- Subscribers
- Paid subscribers
- MAU / DAU
- Watch hours
- Engagement
- ARPU
- Churn
- Retention
- Subscription revenue
- Advertising revenue
- Content spend
- Content library
- Customer acquisition cost where disclosed
- Contribution margin where disclosed

Core chain:

**Subscribers / Users → Engagement → ARPU / Ad Monetization → Revenue → Content Cost → Contribution Margin → Cash**

Analyze:

- Revenue / subscriber
- Content spend / subscriber
- Revenue growth vs content-spend growth
- ARPU trend
- Churn
- Engagement
- Monetization efficiency

---

# 14. Gaming Economics

For gaming businesses, where applicable track:

- Downloads
- Monthly active users
- Daily active users
- Paying users
- Average revenue per paying user
- Average revenue per user
- Engagement
- Retention
- In-app purchases
- Advertising revenue
- Platform fees
- Content development cost
- Customer acquisition cost

Analyze:

**Users → Engagement → Paying Users → ARPPU / ARPU → Revenue → Platform / Content Cost → Margin → Cash**

Flag:

- User growth without monetization
- Heavy dependence on a small number of titles
- Rising acquisition cost
- Falling retention
- High content-development spend without successful monetization

---

# 15. Sports / Media Rights Economics

Track:

- Rights acquired
- Rights duration
- Rights cost
- Audience
- Reach
- Engagement
- Advertising revenue
- Subscription revenue
- Sponsorship revenue
- Distribution revenue
- Monetization per viewer / subscriber where calculable

Analyze:

**Rights Cost → Audience → Advertising + Subscription + Sponsorship → Revenue → Rights Economics → Cash**

Key question:

**Does incremental monetization justify the rights cost?**

Flag:

- Large rights-cost increases without corresponding monetization
- Short-duration rights creating recurring renewal risk
- Dependence on a single major sporting property

---

# 16. Distribution Economics

Track:

- Distribution reach
- Distribution partners
- Platforms
- Digital penetration
- Direct-to-consumer share
- Third-party platform dependence
- Revenue share / platform fees where disclosed
- Distribution cost
- Geographic reach

Assess:

- Control over customer relationship
- Platform dependency
- Bargaining power
- Distribution concentration
- Ability to shift from third-party distribution to direct monetization

---

# 17. Volume, Price & Mix Analysis

Do not rely on revenue growth alone.

Decompose:

**Revenue Growth = Volume / Audience Growth + Price / Rate Growth + Mix + New Content / Releases + New Distribution + Acquisitions + Currency**

For media:

- Audience growth
- Ad inventory growth
- Ad-rate growth
- Digital mix
- Subscription growth
- ARPU

For printing:

- Circulation
- Print volume
- Realisation
- Advertising
- Paper cost

For entertainment:

- Release count
- Content monetization
- Subscriber growth
- ARPU
- Rights income
- Box office

---

# 18. Margin Analysis

Track:

- Gross margin
- EBITDA margin
- EBIT margin
- PAT margin
- Contribution margin where relevant
- Content cost / revenue
- Advertising cost / revenue
- Distribution cost / revenue
- Employee cost / revenue
- Other operating cost / revenue

Analyze margin movement through:

**Revenue Mix → Audience / Volume → Pricing → Content Cost → Distribution Cost → Operating Leverage → EBITDA**

Classify margin changes as:

- Structural
- Cyclical
- Temporary
- One-off
- Accounting-driven

Flag:

- EBITDA growth without CFO growth
- Margin expansion caused by temporary cost declines
- Capitalized expenses obscuring operating costs
- Rising content spend without monetization improvement

---

# 19. Working Capital

Track:

- Receivable days
- Inventory days where applicable
- Payable days
- Cash conversion cycle
- Content advances where disclosed
- Rights advances
- Contract assets
- Contract liabilities
- Customer advances
- Deferred revenue
- Other operating working capital

Analyze:

**Revenue Growth → Receivables / Contract Assets → CFO**

For subscription businesses, distinguish:

- Cash collected upfront
- Revenue recognized
- Contract liabilities / deferred revenue

For printing:

- Paper inventory
- Receivables
- Payables

Flag:

- Receivables growing materially faster than revenue
- Working capital absorbing operating profit
- Customer advances temporarily masking weak cash generation
- Large content / rights advances without adequate monetization

---

# 20. Cash Flow Analysis

Track:

- CFO
- Capex
- CFI
- CFF
- Free cash flow
- CFO / PAT
- FCF / PAT
- FCF margin
- Cash conversion
- Dividends
- Buybacks
- Debt repayment
- Debt raised

Core chain:

**EBITDA → EBIT → PAT → CFO → Capex → FCF**

For media and entertainment, also analyze:

**Content Investment / Rights Investment → Monetization → CFO → FCF**

Important distinction:

**Accounting profit ≠ economic cash generation**

Flag:

- PAT rising while CFO falls
- Persistent negative FCF
- Large content investment with weak cash recovery
- Acquisition-led earnings growth with poor cash conversion

---

# 21. Balance Sheet & Funding

Track:

- Cash
- Investments
- Gross debt
- Net debt
- Equity
- Net worth
- Goodwill
- Intangible assets
- Content assets
- Receivables
- Inventory
- CWIP
- PPE
- Lease liabilities
- Customer advances
- Contract liabilities

Calculate:

- Net debt / EBITDA
- Debt / equity
- Interest coverage
- Net debt / CFO
- Asset turnover
- ROCE
- ROIC

Assess:

- Financial leverage
- Lease obligations
- Content/intangible asset concentration
- Acquisition goodwill
- Funding requirements
- Refinancing risk

---

# 22. ROCE / ROIC

Calculate:

- ROCE
- ROIC
- ROA
- Asset turnover
- Capital turnover

Decompose:

**ROCE = Operating Margin × Capital Turnover**

For media / entertainment, investigate whether high returns arise from:

- Strong monetization
- Asset-light model
- High audience scale
- Strong rights economics
- Low capital intensity

Or whether reported returns are distorted by:

- Underinvestment
- Capitalized content
- Acquisitions
- One-off gains
- Intangible accounting

---

# 23. Competitive Advantage

Assess:

- Brand
- Audience scale
- Content library
- Exclusive rights
- Distribution reach
- Subscriber base
- Network effects where applicable
- Switching costs
- Advertiser relationships
- Content-production capability
- Technology
- Data / personalization
- Cost advantage
- Licensing relationships

Separate:

**Brand / audience advantage**

from:

**Content advantage**

from:

**Distribution advantage**

from:

**Cost advantage**

Do not assume a large audience automatically creates a durable moat.

---

# 24. Management & Capital Allocation

Track:

- Promoter holding
- Promoter pledge
- Promoter buying / selling
- Institutional ownership
- Dilution
- ESOP dilution
- Related-party transactions
- Auditor changes
- Auditor qualifications
- Auditor resignations
- Regulatory actions
- Contingent liabilities
- Management remuneration
- Acquisitions
- Dividends
- Buybacks
- Debt reduction
- Content / rights investment

Evaluate whether management allocates capital toward:

- High-return content
- Sustainable audience acquisition
- Product / platform development
- Distribution
- Debt reduction
- Value-accretive acquisitions

Flag:

- Repeated acquisitions with weak returns
- Large rights/content commitments without adequate monetization
- Persistent dilution
- Weak disclosure around key operating metrics

---

# 25. Concall Intelligence

Extract and classify management commentary around:

### Demand

- Advertising demand
- Consumer engagement
- Subscriber trends
- Audience trends
- Digital migration

### Pricing

- Ad rates
- Subscription pricing
- ARPU
- Pricing power

### Content

- Content slate
- Content pipeline
- Production plans
- Rights acquisition
- Content monetization

### Costs

- Paper prices
- Content costs
- Production costs
- Distribution costs
- Employee costs

### Growth

- Audience
- Subscribers
- Digital penetration
- New launches
- New markets
- New platforms

### Guidance

Track:

**Guidance → Subsequent Result → Variance → Management Explanation**

Classify statements as:

- Positive guidance
- Neutral guidance
- Cautious guidance
- Negative guidance
- Quantified guidance
- Qualitative commentary

Do not treat optimistic commentary alone as evidence. Compare statements against subsequent reported operating and financial data.

---

# 26. Industry Supply-Demand & Cycle Analysis

Analyze the relevant industry separately.

## Media

Assess:

- Advertising cycle
- Audience fragmentation
- Digital migration
- Ad inventory supply
- Ad-rate environment
- Subscription penetration
- Platform competition

## Printing & Publication

Assess:

- Print circulation trend
- Digital substitution
- Paper prices
- Advertising cycle
- Print-capacity utilization
- Distribution economics

## Entertainment

Assess:

- Content supply
- Consumer spending
- Streaming competition
- Release calendar
- Rights inflation
- Box-office cycle
- Subscription competition
- Gaming/content monetization trends

Distinguish:

**Structural change**

from:

**temporary cycle**

---

# 27. Peer Comparison

Compare companies by business model, not only by Sector Value.

## Media peers

Compare:

- Audience
- Engagement
- Advertising revenue growth
- Subscription revenue growth
- Digital share
- ARPU
- EBITDA margin
- Content cost / revenue
- CFO / PAT
- FCF margin
- ROCE / ROIC
- Valuation

## Printing / Publication peers

Compare:

- Circulation
- Volume growth
- Realisation
- Advertising revenue
- Paper cost / revenue
- Print utilization
- EBITDA margin
- CFO / PAT
- FCF
- ROCE

## Entertainment peers

Compare:

- Content spend
- Release count
- Subscriber growth
- ARPU
- Engagement
- Rights income
- Content monetization
- Content cost / revenue
- EBITDA
- CFO
- FCF
- ROIC
- Valuation

Never force a retailer-style or manufacturing-style peer comparison onto media or entertainment companies.

---

# 28. Valuation Framework

Use valuation methods appropriate to the business model.

Track:

- P/E
- EV/EBITDA
- EV/Sales
- P/B where meaningful
- DCF
- FCF yield
- Historical valuation
- Peer valuation
- Growth-adjusted valuation

For media / entertainment, valuation may need to incorporate:

- Audience scale
- Subscriber growth
- ARPU
- Content economics
- FCF
- Rights commitments
- Net cash / net debt
- Library / intangible economics

Output:

- Current valuation
- Historical valuation
- Peer valuation
- Growth-adjusted valuation
- Margin-adjusted valuation
- Cash-flow-adjusted valuation
- Margin of safety

Do not hard-code one universal multiple for the entire Sector Value.

---

# 29. Historical Valuation

Track:

- Historical P/E
- Historical EV/EBITDA
- Historical EV/Sales
- Historical P/B where meaningful
- Historical FCF yield

Compare valuation against:

- Revenue growth
- Audience growth
- Subscriber growth
- ARPU
- EBITDA margin
- ROIC
- FCF
- Balance-sheet strength
- Industry conditions

A lower historical multiple is not automatically cheap, and a higher multiple is not automatically expensive.

---

# 30. Causal Analysis Engine

The system must explain **why** financial metrics changed.

## Universal Media / Entertainment Chain

**Audience → Engagement → Monetization → Revenue → Content Cost → Margin → Cash**

## Advertising Chain

**Audience → Reach → Engagement → Ad Inventory → Fill / Monetization → Ad Rates → Advertising Revenue → Margin → CFO**

## Subscription Chain

**Subscribers → Retention / Churn → ARPU → Subscription Revenue → Content / Service Cost → Margin → CFO**

## Publishing Chain

**Circulation → Realisation + Advertising → Revenue → Paper / Printing Cost → EBITDA → CFO**

## Entertainment Content Chain

**Content Spend → Release / Availability → Audience → Rights / Subscription / Advertising Revenue → Content Cost Recovery → Margin → FCF**

## Sports Rights Chain

**Rights Cost → Audience → Advertising + Subscription + Sponsorship → Revenue → Rights Margin → Cash**

The engine should identify where the causal chain breaks.

Example:

**Audience ↑ → Engagement ↑ → Revenue ↓**

Possible investigation:

- Monetization weakened
- Ad rates declined
- Mix shifted
- Subscription ARPU declined
- Platform economics changed

Do not automatically assign a cause unless supported by data or management disclosure.

---

# 31. Red Flags

## Growth

- Revenue growth without audience / volume growth
- Acquisition-led growth masking organic weakness
- Subscriber growth with weak retention
- Traffic growth without monetization

## Advertising

- Revenue dependent on a small advertiser base
- Ad revenue growth without audience support
- Falling ad rates
- Weak monetization despite engagement growth

## Subscription

- Rising churn
- Falling ARPU
- Heavy promotional pricing
- High subscriber acquisition cost
- Subscriber growth without cash generation

## Content

- Content spend rising faster than monetization
- Repeated content impairments
- Large content assets with weak returns
- Dependence on a few successful titles
- Rights costs rising faster than monetization

## Printing

- Declining circulation
- Low print utilization
- Paper-cost inflation without pricing ability
- High capex despite secular volume decline

## Cash Flow

- PAT rising while CFO falls
- Persistent negative FCF
- Large advances / receivables
- Weak cash recovery from content investment

## Governance

- Auditor qualifications
- Auditor resignation
- Related-party concerns
- Promoter pledge
- Repeated dilution
- Aggressive acquisitions

---

# 32. Positive Signals

Look for combinations such as:

- Audience growth + engagement growth + monetization growth
- Subscriber growth + stable/improving ARPU + falling churn
- Advertising growth supported by audience and ad-rate growth
- Digital monetization improving faster than legacy-media decline
- Content spend generating improving revenue / cash returns
- Strong content library monetization
- Improving rights economics
- Rising FCF with stable or improving ROIC
- Low leverage with strong recurring cash generation
- Sustainable competitive advantage in audience, content or distribution

A positive signal should be supported by multiple data points rather than a single quarter.

---

# 33. Scenario Analysis

Build Bull / Base / Bear scenarios.

## Bull

Potential assumptions:

- Strong audience growth
- Higher engagement
- Better ad rates
- Subscriber growth
- ARPU expansion
- Strong content performance
- Better content monetization
- Operating leverage
- Lower input costs where relevant

Calculate:

- Revenue
- EBITDA
- EBIT
- PAT
- CFO
- FCF
- ROIC
- Net debt
- Valuation

## Base

Potential assumptions:

- Normal audience growth
- Stable monetization
- Normal content performance
- Stable margins
- Planned investment
- Normal industry conditions

## Bear

Potential assumptions:

- Advertising slowdown
- Audience stagnation
- Higher churn
- ARPU pressure
- Weak content performance
- Rights inflation
- Higher content cost
- Paper-cost inflation
- Working-capital stress

Calculate the same financial outputs.

---

# 34. Scoring Architecture

Use the common Consumer Discretionary framework as the starting architecture:

| Category | Base Weight |
|---|---:|
| Business Quality | 15% |
| Demand & Growth | 15% |
| Competitive Position | 10% |
| Operating Quality | 15% |
| Cash Flow Quality | 15% |
| Balance Sheet | 10% |
| Capital Efficiency | 10% |
| Management & Governance | 5% |
| Valuation | 5% |

For Media, Entertainment & Publication, activate industry-specific metrics inside these categories.

### Business Quality

- Business-model durability
- Revenue diversification
- Recurring vs volatile revenue
- Audience quality

### Demand & Growth

- Audience growth
- Engagement
- Subscriber growth
- ARPU
- Advertising growth
- Content monetization

### Competitive Position

- Brand
- Content library
- Distribution
- Rights
- Audience scale

### Operating Quality

- Monetization
- Content efficiency
- Margin
- Cost control

### Cash Flow Quality

- CFO/PAT
- FCF
- Content investment recovery

### Balance Sheet

- Net debt
- Lease liabilities
- Content / intangible concentration

### Capital Efficiency

- ROCE
- ROIC
- Asset turnover

### Management & Governance

- Guidance quality
- Capital allocation
- Disclosure quality
- Governance

### Valuation

- P/E
- EV/EBITDA
- EV/Sales
- FCF yield
- Historical valuation
- Peer valuation

**Critical rule:** do not produce a misleading final score when critical industry data is missing. Show a data-confidence limitation.

---

# 35. Metric Classification

Every metric should be tagged:

- CORE
- SUPPORTING
- DIAGNOSTIC
- SECTOR_SPECIFIC
- VALUATION
- PRESENTATION

Examples:

| Metric | Classification |
|---|---|
| Revenue growth | CORE |
| EBITDA margin | CORE |
| CFO/PAT | CORE |
| FCF margin | CORE |
| Audience growth | SECTOR_SPECIFIC |
| Subscriber growth | SECTOR_SPECIFIC |
| ARPU | SECTOR_SPECIFIC |
| Ad rates | SECTOR_SPECIFIC |
| Engagement | SECTOR_SPECIFIC |
| Content spend / revenue | DIAGNOSTIC |
| Content monetization | DIAGNOSTIC |
| P/E | VALUATION |
| EV/EBITDA | VALUATION |
| ROIC | CORE |
| Net debt / EBITDA | CORE |

---

# 36. Data Quality Framework

Every metric must store:

```text
metric_name
value
period
unit
source
source_date
data_type
confidence
```

Data types:

- REPORTED
- CALCULATED
- ESTIMATED
- MANAGEMENT-DISCLOSED
- THIRD-PARTY

Confidence:

- HIGH
- MEDIUM
- LOW

Calculated metrics must retain input lineage.

Example:

```text
RevPAR
  = Occupancy × ADR
```

Store both Occupancy and ADR as source inputs.

---

# 37. Source Hierarchy

Use:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings / Concall Transcript
5. NSE/BSE filings
6. Regulatory filings
7. Company website / Investor Relations
8. Reliable financial databases
9. Third-party research

For industry-specific metrics, prefer primary company disclosures.

Third-party data must not silently override company-reported data.

---

# 38. Missing Data Logic

Never convert missing values into zero.

Allowed states:

- AVAILABLE
- CALCULABLE
- PARTIAL
- MISSING_INPUT
- SOURCE_REQUIRED
- NOT_APPLICABLE
- INVALID

Example:

If subscriber count is unavailable:

```text
subscriber_growth = MISSING_INPUT
```

not:

```text
subscriber_growth = 0
```

The final report must show:

**Data Coverage: X%**

and identify missing critical metrics.

---

# 39. Agent Architecture

Recommended pipeline:

```text
Company Identification
        ↓
Business Classification
        ↓
Revenue Model Classification
        ↓
Financial Data
        ↓
Audience / Demand Metrics
        ↓
Advertising / Subscription Economics
        ↓
Content Economics
        ↓
Printing / Publishing Module (if applicable)
        ↓
Working Capital
        ↓
Capex & Asset Efficiency
        ↓
Cash Flow
        ↓
Management / Concall
        ↓
Competitive Advantage
        ↓
Industry Cycle
        ↓
Peer Comparison
        ↓
Valuation
        ↓
Red Flag Detection
        ↓
Causal Analysis
        ↓
Scoring
        ↓
Investment Thesis
```

Each module should return:

```text
metric
value
trend
source
confidence
interpretation
causal_link
red_flags
positive_signals
```

---

# 40. Database Structure

Recommended metric table:

```text
company_id
sector
sector_value
industry
metric_name
metric_category
period
value
unit
source
source_date
data_type
confidence
calculation_formula
input_metrics
```

Recommended industry operating-metric categories:

```text
AUDIENCE
ENGAGEMENT
ADVERTISING
SUBSCRIPTIONS
CONTENT
RIGHTS
PRINTING
PUBLISHING
DIGITAL
UNIT_ECONOMICS
MARGINS
WORKING_CAPITAL
CAPEX
CASH_FLOW
BALANCE_SHEET
ROIC
GOVERNANCE
VALUATION
```

---

# 41. Data Coverage Dashboard

The application should show:

**DATA COVERAGE**

Example:

```text
78% of tracked metrics available
```

Then:

```text
Critical data gaps:
- Subscriber churn
- Audience monetization
- Content-level profitability
- Rights economics
```

Do not let unavailable metrics silently weaken or strengthen the score.

---

# 42. Final Screener Output

The report should answer:

## Business

- What exactly does the company do?
- Which Media / Printing / Entertainment model applies?
- How does it make money?

## Demand

- Is audience growing?
- Is engagement improving?
- Are subscribers increasing?
- Is demand structural or cyclical?

## Monetization

- Is the company monetizing audience better?
- Are ad rates improving?
- Is ARPU improving?
- Is subscription economics improving?

## Content

- Is content investment generating adequate returns?
- Is the content library becoming more valuable?
- Is the business dependent on a few hits?

## Financials

- Is revenue growing?
- What is driving the growth?
- Are margins improving?
- Is cash conversion strong?

## Capital Efficiency

- Is ROCE / ROIC improving?
- Is growth requiring excessive capital?

## Balance Sheet

- Is leverage manageable?
- Are content / intangible assets significant?
- Are lease or rights commitments material?

## Management

- What is management guiding?
- Did prior guidance translate into results?
- Is capital allocation disciplined?

## Valuation

- How does current valuation compare with history and peers?
- Does valuation reflect the company's growth and cash generation?

## Risks

- What can break the thesis?
- Which metrics should be monitored every quarter?

---

# 43. Quarterly Monitoring System

For every quarter automatically compare:

```text
Current Quarter
vs Previous Quarter
vs Same Quarter Last Year
vs TTM
vs 3Y Trend
```

Track changes in:

- Audience
- Engagement
- Subscribers
- ARPU
- Advertising revenue
- Subscription revenue
- Content spend
- Content monetization
- Rights cost
- Revenue
- EBITDA
- CFO
- FCF
- ROIC
- Net debt

Generate:

**What changed? → Why did it change? → Is it temporary or structural? → What should be monitored next?**

---

# 44. Guidance Tracking

Maintain a structured table:

| Date | Metric | Management Guidance | Actual | Variance | Explanation | Status |
|---|---|---|---|---|---|---|

Possible statuses:

- ACHIEVED
- PARTIALLY_ACHIEVED
- MISSED
- AHEAD_OF_GUIDANCE
- NOT_TESTABLE_YET

This allows the system to assess management commentary against subsequent evidence rather than treating commentary as fact.

---

# 45. Fundamental Thesis Generator

Generate the thesis from evidence:

```text
Business Model
+
Demand / Audience
+
Monetization
+
Content Economics
+
Margin
+
Cash Flow
+
Capital Efficiency
+
Balance Sheet
+
Management
+
Competitive Position
+
Valuation
+
Risks
=
Fundamental Thesis
```

The thesis must distinguish:

### Evidence

What the reported / calculated data shows.

### Interpretation

What the evidence may imply.

### Uncertainty

What cannot yet be established because of missing or low-confidence data.

### Monitoring triggers

What future data would confirm or invalidate the current interpretation.

---

# 46. Implementation Principles

1. **Classify first, calculate second.**
2. **Audience is not revenue.**
3. **Revenue growth is not automatically quality growth.**
4. **Subscriber growth must be evaluated with churn and ARPU.**
5. **Advertising growth must be evaluated with audience, inventory and ad rates.**
6. **Content spend must be evaluated against monetization and cash returns.**
7. **Do not confuse one successful release with recurring business quality.**
8. **Separate structural digital transition from temporary advertising cycles.**
9. **Separate accounting profit from cash generation.**
10. **Track management guidance against subsequent results.**
11. **Compare companies by business model, not merely classification.**
12. **Never treat missing data as zero.**
13. **Every calculated metric must retain its input lineage.**
14. **Every major conclusion should have an evidence trail.**
15. **The system must explain WHY metrics changed, not merely whether they passed a threshold.**

---

# 47. Central Fundamental Question

The entire Media, Entertainment & Publication analysis should ultimately answer:

> **Can this company sustainably convert audience, engagement, content and distribution into growing monetization, strong margins and durable free cash flow without requiring disproportionate content, rights or capital investment?**

That is the central question around which the sector-specific screener should be built.
