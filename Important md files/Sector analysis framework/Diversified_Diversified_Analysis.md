# Diversified → Diversified — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

> **Classification**
> - **Macro Sector:** Diversified
> - **Sector Value:** Diversified
> - **Industry:** Diversified

This is the standalone analysis framework for the **Diversified → Diversified** sector-value/industry classification in the Fundamental Analysis Screener.

## 1. Purpose

This framework is for fundamental analysis and screening of companies classified under **Diversified**.

Unlike a single-industry company, a diversified company may operate across multiple unrelated or loosely related businesses. Therefore, the engine must avoid relying on a single-sector framework.

The core approach is:

**CONGLOMERATE MAPPING → SEGMENT NORMALIZATION → SEGMENT ECONOMICS → SOTP → CAPITAL ALLOCATION → CASH FLOW → BALANCE SHEET → MANAGEMENT → VALUATION → RED FLAGS → INVESTMENT THESIS**

The primary analytical objective is to determine:

1. What businesses the company owns
2. Which segments actually create economic value
3. Which segments consume capital
4. Whether capital is allocated efficiently
5. Whether consolidated earnings hide weak segment economics
6. Whether the holding/conglomerate structure creates or destroys value
7. Whether valuation adequately reflects the underlying businesses

---

# 2. Core Analytical Philosophy

Do not treat a diversified company as one homogeneous business.

The analysis must be performed at two levels:

### Level 1 — Segment Analysis

Analyze every material business independently.

### Level 2 — Consolidated Analysis

Analyze:

- Group cash flow
- Consolidated debt
- Capital allocation
- Corporate overhead
- Minority interests
- Cross-holdings
- Inter-segment transactions
- Holding-company structure
- Consolidated valuation

The final thesis should connect both levels.

---

# 3. Business Portfolio Mapping

Create a complete portfolio map.

For each segment record:

- Segment name
- Industry
- Business model
- Revenue
- EBITDA
- EBIT
- PAT/contribution
- Assets
- Capital employed
- ROCE
- ROIC
- Growth
- Cash generation
- Capex
- Net debt
- Ownership %
- Listed/unlisted status
- Strategic importance

Classify each business as:

- Core
- Growth
- Mature
- Cyclical
- Cash generator
- Capital consumer
- Turnaround
- Non-core
- Exit candidate
- Strategic holding

---

# 4. Segment Materiality

Rank segments by:

- Revenue contribution
- EBITDA contribution
- EBIT contribution
- PAT contribution
- Asset contribution
- Capital employed
- CFO contribution
- Capex requirement

Do not assume the largest revenue segment is the most valuable segment.

A small high-ROIC business may create more value than a large low-return business.

---

# 5. Common Financial Dataset

Collect annual, quarterly and TTM data.

## Market Data

- Market capitalization
- Enterprise value
- Share price
- Shares outstanding
- Free float
- Promoter holding
- Promoter pledge
- Institutional ownership
- Dividend yield
- Historical P/E
- Historical EV/EBITDA
- Historical P/B
- Historical EV/Sales

## Consolidated Income Statement

- Revenue
- Revenue growth
- EBITDA
- EBITDA margin
- EBIT
- EBIT margin
- PBT
- PAT
- EPS
- EPS growth
- Other income
- Exceptional items
- Finance cost
- Depreciation
- Tax rate

## Segment Financials

For every material segment:

- Revenue
- EBITDA
- EBIT
- Margin
- Assets
- Liabilities where disclosed
- Capital employed
- Capex
- Depreciation
- Growth
- Cash generation

## Balance Sheet

- Cash
- Investments
- Gross debt
- Net debt
- Equity
- Net worth
- Goodwill
- Intangibles
- Receivables
- Inventory
- Payables
- PPE
- CWIP
- Lease liabilities
- Contingent liabilities

## Cash Flow

- CFO
- Capex
- CFI
- CFF
- Free cash flow
- CFO/PAT
- FCF/PAT
- FCF margin
- Dividends
- Buybacks
- Debt repayment
- Debt raised

---

# 6. Segment Growth Analysis

Calculate for each material segment:

- Revenue CAGR 3Y
- Revenue CAGR 5Y
- Revenue CAGR 10Y
- EBITDA CAGR
- EBIT CAGR
- PAT CAGR where available
- CFO CAGR where available
- FCF CAGR where available
- YoY growth
- QoQ growth where meaningful
- TTM growth

Identify whether growth comes from:

- Volume
- Price
- Mix
- Capacity
- Acquisitions
- New businesses
- Currency
- Market-share gains

---

# 7. Segment Profitability

For every material segment calculate:

- EBITDA margin
- EBIT margin
- ROCE
- ROIC
- Asset turnover
- Capital turnover
- Incremental ROIC

Compare:

**Segment Profit → Capital Employed → Return on Capital**

This is essential for identifying:

- High-return businesses
- Low-return businesses
- Capital traps
- Hidden cash generators

---

# 8. Segment Cash Flow

Where segment cash flow is available, track:

- CFO
- Capex
- FCF
- FCF margin
- Cash conversion

Where segment-level CFO is unavailable, explicitly mark the limitation.

Do not manufacture segment cash flow from incomplete data.

Analyze:

**Segment EBIT → Working Capital → Capex → FCF**

---

# 9. Capital Allocation Analysis

This is a central component of diversified-company analysis.

Track allocation of capital toward:

- Existing businesses
- New businesses
- Acquisitions
- Minority investments
- Debt reduction
- Dividends
- Buybacks
- Corporate investments

For each major capital allocation decision record:

- Amount invested
- Business
- Investment date
- Expected return where disclosed
- Actual subsequent return
- Strategic rationale
- Funding source
- Outcome

Evaluate historical capital allocation through evidence.

---

# 10. Acquisition Analysis

For acquisitions track:

- Acquisition price
- Enterprise value
- Revenue acquired
- EBITDA acquired
- Purchase multiple
- Goodwill
- Intangibles
- Funding method
- Integration cost
- Subsequent revenue growth
- Subsequent margin
- ROIC
- Impairments
- Divestment if any

Calculate where possible:

**Acquisition EV / EBITDA**

and compare actual post-acquisition economics with the purchase assumptions.

Flag repeated acquisitions where returns remain below the group's cost of capital.

---

# 11. Divestment Analysis

Track:

- Businesses sold
- Sale price
- Book value
- Gain/loss
- Original acquisition cost
- Holding period
- Capital released
- Debt reduction
- Reinvestment of proceeds

Determine whether divestments:

- Simplified the portfolio
- Released capital
- Reduced leverage
- Improved ROIC
- Removed structurally weak assets

---

# 12. SOTP Valuation

**Sum-of-the-Parts (SOTP)** should be the primary valuation framework where segment data is sufficient.

For each segment:

1. Estimate normalized earnings/EBITDA
2. Select an appropriate peer/historical multiple
3. Calculate enterprise/equity value
4. Apply ownership percentage where required
5. Add listed investments
6. Add other investments
7. Add surplus cash
8. Subtract net debt
9. Subtract corporate liabilities
10. Adjust for minority interests

Basic framework:

**SOTP Equity Value = Σ Segment Value + Investments + Surplus Cash − Net Debt − Other Claims**

---

# 13. Segment-Specific Valuation

Do not apply one multiple to every segment.

Examples:

- Consumer business → P/E / EV/EBITDA
- Financial business → P/B / P/E
- Commodity business → normalized EV/EBITDA
- Technology business → P/E / EV/Sales / EV/EBITDA
- Realty → NAV/SOTP
- Infrastructure → EV/EBITDA / asset-based
- Holding company → NAV/SOTP with appropriate holding discount methodology

The framework must record the reason for the chosen valuation method.

---

# 14. Holding Company / Conglomerate Structure

Analyze:

- Parent ownership
- Subsidiary ownership
- Cross-holdings
- Listed subsidiaries
- Unlisted subsidiaries
- Associate companies
- Joint ventures
- Minority interests
- Corporate guarantees
- Inter-company loans
- Inter-company investments

Identify whether value is trapped because of:

- Holding-company structure
- Cross-holdings
- Taxes
- Debt
- Regulatory restrictions
- Minority interests
- Corporate overhead

---

# 15. Holding Discount Analysis

Where applicable, compare:

- SOTP value
- Market capitalization
- Implied holding discount/premium

Do not assume a universal holding-company discount.

Analyze why the discount/premium exists.

Potential factors:

- Governance
- Capital allocation
- Complexity
- Liquidity
- Tax leakage
- Cross-holdings
- Debt
- Corporate overhead
- Minority interests
- Quality of subsidiaries

The system should report the observed discount/premium and its drivers rather than applying a fixed conclusion.

---

# 16. Corporate Overhead

Track:

- Corporate employee costs
- Management remuneration
- Corporate finance cost
- Central administrative costs
- Holding-company expenses
- Other unallocated expenses

Calculate:

**Corporate Overhead / Consolidated Revenue**

and, where possible:

**Corporate Overhead / SOTP Value**

Determine whether overhead is:

- Stable
- Rising
- Falling
- Justified by portfolio scale

---

# 17. Balance Sheet Analysis

Analyze both:

### Consolidated Balance Sheet

and

### Standalone/Parent Balance Sheet

Track:

- Gross debt
- Net debt
- Cash
- Investments
- Net debt/EBITDA
- Interest coverage
- Debt maturity
- Working-capital debt
- Guarantees
- Lease liabilities

A parent company may appear financially healthy while a subsidiary carries significant debt.

Therefore identify:

**Debt by entity + Debt by segment + Consolidated debt**

---

# 18. Contingent Liabilities

Track:

- Guarantees
- Litigation
- Tax disputes
- Regulatory liabilities
- Environmental liabilities
- Subsidiary guarantees
- Cross-default provisions
- Off-balance-sheet commitments

Flag contingent liabilities that could materially affect SOTP value.

---

# 19. Working Capital

Analyze consolidated working capital:

- Receivable days
- Inventory days
- Payable days
- Cash conversion cycle

Also identify which segments are working-capital intensive.

Analyze:

**Revenue growth → Working capital → CFO**

Flag:

- Receivables growing faster than revenue
- Inventory buildup
- Persistent negative CFO
- Working-capital debt
- Large unexplained advances

---

# 20. Capex Analysis

Track:

- Consolidated capex
- Segment capex
- Maintenance capex
- Growth capex
- Capex/revenue
- Capex/depreciation
- CWIP
- Project cost
- Project completion
- Expected utilization
- Expected ROIC

For every major capex program analyze:

**Capital invested → Capacity → Revenue → EBIT → CFO → FCF → ROIC**

Identify whether capital is being deployed toward high-return or low-return segments.

---

# 21. Portfolio Capital Efficiency

Calculate:

- Consolidated ROE
- Consolidated ROCE
- Consolidated ROIC
- Segment ROCE
- Segment ROIC
- Incremental ROIC

Construct a portfolio matrix:

| Segment | Growth | ROIC | Capital Need | Cash Generation |
|---|---|---|---|---|
| Segment A | High/Medium/Low | High/Medium/Low | High/Medium/Low | High/Medium/Low |

The purpose is to identify:

- Growth engines
- Cash engines
- Capital consumers
- Value destroyers
- Potential restructuring opportunities

---

# 22. Portfolio Quality

Evaluate:

- Number of segments
- Revenue concentration
- Profit concentration
- Cash-flow concentration
- Capital concentration
- Cyclicality
- Geographic diversification
- Customer diversification

A diversified revenue base does not automatically mean diversified economic risk.

---

# 23. Cyclicality

For each segment determine:

- Cyclical
- Defensive
- Secular growth
- Regulated
- Mature
- Emerging

Calculate normalized:

- Revenue
- EBITDA
- EBIT
- PAT
- CFO
- FCF

Consolidated earnings should be interpreted in the context of the cycle mix.

---

# 24. Management & Governance

Track:

- Promoter holding
- Promoter pledge
- Promoter buying/selling
- Share dilution
- Related-party transactions
- Auditor changes
- Auditor qualifications
- Executive remuneration
- Capital allocation
- Acquisitions
- Divestments
- Guarantees
- Subsidiary transactions

Analyze management's historical decisions:

**Capital Allocation → Investment → Outcome → ROIC**

---

# 25. Concall Analysis

Parse earnings calls and management commentary for:

- Segment demand
- Segment growth
- Margin outlook
- Capex guidance
- Acquisition plans
- Divestment plans
- New-business investments
- Debt reduction
- Capital allocation
- Subsidiary performance
- Regulatory developments
- Management guidance

Track:

**Guidance → Actual → Variance → Explanation**

Do not treat positive management commentary as evidence unless subsequent operating results support it.

---

# 26. Competitive Advantage

Assess separately for each major segment:

- Brand
- Scale
- Cost position
- Distribution
- Technology
- Market share
- Network effects
- Customer relationships
- Resource ownership
- Licenses
- Switching costs
- IP
- Geographic advantage

Then determine whether the parent creates additional portfolio-level advantages through:

- Shared distribution
- Shared infrastructure
- Capital access
- Procurement
- Cross-selling
- Talent
- Technology
- Brand

Do not assume diversification itself is a moat.

---

# 27. Peer Comparison

Peer comparison must happen at two levels.

## Segment Peers

Compare each business with direct industry peers.

Metrics:

- Growth
- Margin
- ROCE
- ROIC
- Cash conversion
- Debt
- Valuation

## Conglomerate Peers

Compare:

- Portfolio growth
- Consolidated ROIC
- Capital allocation
- Net debt
- SOTP discount/premium
- Corporate overhead
- Dividend/buyback policy

Avoid comparing diversified companies solely on consolidated P/E.

---

# 28. Valuation Framework

Primary methods:

### SOTP

Use for material multi-business portfolios.

### DCF

Use for businesses with reasonably predictable cash flows.

### P/E

Use selectively for mature profitable segments.

### EV/EBITDA

Use for capital-intensive or leverage-sensitive businesses.

### P/B

Use for financial/asset-based businesses where relevant.

### NAV

Use for asset-backed businesses.

### Market Value of Listed Investments

Value listed holdings separately where appropriate.

---

# 29. Historical Valuation

Track:

- Historical P/E
- Historical EV/EBITDA
- Historical P/B
- Historical SOTP discount/premium
- Historical FCF yield

Compare current valuation with:

1. Own history
2. Segment peer valuations
3. SOTP
4. Growth
5. ROIC
6. Balance-sheet quality
7. Capital allocation quality

---

# 30. Causal Analysis Engine

The diversified-company causal chain should be:

**Portfolio → Segment Demand → Segment Revenue → Segment Margin → Segment FCF → Capital Allocation → Consolidated FCF → ROIC → SOTP Value**

For capital allocation:

**Cash Generator → Capital Allocation → Growth/Returns → Portfolio ROIC**

For weak segments:

**Capital Injection → Low Return → Cash Drain → Consolidated ROIC Dilution**

The engine should explicitly identify whether value creation comes from:

- Existing business growth
- Margin expansion
- New investments
- Acquisitions
- Portfolio restructuring
- Debt reduction
- Buybacks

---

# 31. Red-Flag Engine

## Portfolio Red Flags

- Excessive complexity
- Poor segment disclosure
- Profit concentrated in one weak business
- Multiple low-return businesses
- Cross-subsidization
- Persistent capital misallocation

## Capital Allocation Red Flags

- Acquisitions at high valuations
- Repeated low-return investments
- Unexplained diversification
- Debt-funded acquisitions
- Capex without adequate returns
- Persistent value destruction

## Balance-Sheet Red Flags

- High consolidated debt
- Debt concentrated in weak subsidiaries
- Parent guarantees
- Cross-default exposure
- Refinancing dependence

## Governance Red Flags

- Related-party transactions
- Auditor issues
- Frequent restructuring
- Complex ownership
- Minority shareholder conflicts
- Unexplained inter-company transactions

## Valuation Red Flags

- Large SOTP discount without explanation
- Valuation dependent on optimistic segment assumptions
- Unlisted assets with weak transparency
- Excessive corporate overhead

---

# 32. Positive-Signal Engine

Look for:

- High-quality core businesses
- Improving segment ROIC
- Strong cash generators
- Disciplined capital allocation
- Debt reduction
- Successful acquisitions
- Successful divestments
- Portfolio simplification
- Rising SOTP value
- Strong subsidiary performance
- Sustainable FCF
- Better disclosure
- Lower corporate overhead

Signals should be supported by operating and financial evidence.

---

# 33. Scenario Analysis

Build scenarios at the segment level.

## Bull Case

- Strong growth in high-ROIC businesses
- Successful new investments
- Margin improvement
- Debt reduction
- Higher SOTP multiples

## Base Case

- Normal segment growth
- Stable margins
- Planned capex
- Normalized valuation

## Bear Case

- Weak cyclical segments
- Low-return capex
- Acquisition underperformance
- Higher debt
- Lower segment valuations
- Wider SOTP discount

Calculate impact on:

- Revenue
- EBITDA
- PAT
- CFO
- FCF
- Net debt
- ROIC
- SOTP
- Market-value-to-SOTP relationship

---

# 34. Scoring Architecture

Suggested dimensions:

| Dimension | Suggested Weight |
|---|---:|
| Portfolio Quality | 15% |
| Segment Economics | 15% |
| Capital Allocation | 15% |
| Cash Flow Quality | 15% |
| Balance Sheet | 10% |
| ROIC / Capital Efficiency | 10% |
| Management & Governance | 10% |
| Growth | 5% |
| Valuation / SOTP | 5% |

The engine should also maintain **segment-level scores internally**, but the final output must show the underlying evidence.

Do not produce high-confidence scoring when segment disclosure or ownership data is materially incomplete.

---

# 35. Data Quality Framework

Every metric must carry:

- metric_name
- value
- period
- unit
- source
- source_date
- data_type
- confidence

Allowed data types:

- REPORTED
- CALCULATED
- ESTIMATED
- MANAGEMENT-DISCLOSED
- THIRD-PARTY

Confidence:

- HIGH
- MEDIUM
- LOW

For SOTP assumptions store:

- Segment
- Valuation method
- Earnings metric
- Multiple
- Multiple source
- Normalization method
- Ownership %
- Resulting value
- Confidence

---

# 36. Source Hierarchy

Preferred source order:

1. Annual Report
2. Quarterly Results
3. Segment reporting
4. Investor Presentation
5. Earnings Call Transcript
6. NSE/BSE filings
7. Regulatory filings
8. Company investor-relations disclosures
9. Reliable financial databases
10. Third-party research

Segment reporting from company filings should be the primary source for portfolio analysis.

---

# 37. Agent Architecture

Recommended pipeline:

```text
Company Identification Agent
        ↓
Portfolio Mapping Agent
        ↓
Segment Classification Agent
        ↓
Financial Data Agent
        ↓
Segment Financial Agent
        ↓
Segment Operating Metrics Agent
        ↓
Segment ROIC Agent
        ↓
Working Capital Agent
        ↓
Capex Agent
        ↓
Cash Flow Agent
        ↓
Capital Allocation Agent
        ↓
Acquisition / Divestment Agent
        ↓
Management / Concall Agent
        ↓
Governance Agent
        ↓
Peer Comparison Agent
        ↓
SOTP Valuation Agent
        ↓
Holding Discount Agent
        ↓
Red Flag Agent
        ↓
Causal Analysis Agent
        ↓
Scoring Agent
        ↓
Investment Thesis Agent
```

---

# 38. Recommended Database Structure

## Company

- company_id
- company_name
- sector
- industry
- business_model
- market_cap

## Segment

- company_id
- segment_id
- segment_name
- industry
- classification
- ownership
- listed_status
- strategic_status

## Segment Financial Metric

- company_id
- segment_id
- metric_name
- value
- period
- unit
- source
- confidence

## Capital Allocation

- company_id
- date
- transaction_type
- segment
- amount
- funding_source
- expected_return
- actual_return
- outcome

## Acquisition

- company_id
- acquisition_name
- date
- EV
- purchase_price
- revenue
- EBITDA
- goodwill
- funding
- post_acquisition_ROIC

## SOTP

- company_id
- segment_id
- valuation_method
- normalized_metric
- multiple
- enterprise_value
- equity_value
- ownership
- source
- confidence

---

# 39. Final Screener Output

## 1. Company Snapshot

- Market cap
- Revenue
- EBITDA
- PAT
- CFO
- FCF
- Net debt
- ROIC

## 2. Portfolio Map

Show every material segment with:

- Revenue
- EBITDA
- EBIT
- Growth
- ROIC
- Capital employed
- Capex
- Cash generation

## 3. Segment Quality

Identify:

- Growth engines
- Cash engines
- Capital consumers
- Low-return businesses
- Cyclical businesses

## 4. Capital Allocation

Show:

- Major investments
- Acquisitions
- Divestments
- Dividends
- Buybacks
- Debt reduction

## 5. Balance Sheet

- Consolidated debt
- Parent debt
- Subsidiary debt
- Guarantees
- Liquidity

## 6. Cash Flow

- CFO
- FCF
- CFO/PAT
- FCF/PAT
- Capex

## 7. Capital Efficiency

- ROE
- ROCE
- ROIC
- Segment ROIC
- Incremental ROIC

## 8. Management

- Guidance
- Capital allocation history
- Concall observations
- Governance

## 9. SOTP Valuation

For every material segment show:

- Valuation method
- Normalized earnings
- Multiple
- Segment value
- Ownership
- Value contribution

Then show:

- Gross SOTP
- Net debt
- Other claims
- Equity SOTP
- Market capitalization
- Implied discount/premium

## 10. Peer Position

Show segment peers and conglomerate peers separately.

## 11. Causal Analysis

Explain:

**Portfolio → Segment Economics → Cash Generation → Capital Allocation → Consolidated ROIC → SOTP Value**

## 12. Red Flags

List material concerns with:

- Severity
- Evidence
- Source
- Potential impact

## 13. Positive Signals

List evidence-backed strengths.

## 14. Investment Thesis

Produce:

- Portfolio thesis
- Segment thesis
- Growth engine
- Cash engine
- Capital allocation thesis
- Balance-sheet thesis
- SOTP thesis
- Bull case
- Bear case
- Key risks
- Thesis-break conditions
- Next-quarter metrics to monitor

---

# 40. Implementation Principles

1. Never treat a diversified company as a single homogeneous business.
2. Analyze every material segment separately.
3. Use segment-level revenue, EBIT, ROIC and capital employed wherever available.
4. Identify which businesses generate cash and which consume it.
5. Track capital allocation historically.
6. Analyze acquisitions and divestments based on actual returns.
7. Use SOTP where segment data supports it.
8. Do not apply one valuation multiple to all segments.
9. Analyze consolidated and standalone balance sheets separately.
10. Identify subsidiary debt and parent guarantees.
11. Track corporate overhead.
12. Account for minority interests and ownership percentages.
13. Normalize cyclical segments.
14. Preserve source provenance.
15. Explicitly label estimated SOTP assumptions.
16. Do not assume diversification creates a moat.
17. Do not assume a holding discount is justified without analyzing its drivers.
18. Make the final thesis traceable to segment economics and capital allocation.

---

# 41. Sector-Level Fundamental Question

The final engine should answer:

> **Does this diversified company own a portfolio of economically attractive businesses, allocate capital efficiently between them, generate sustainable consolidated cash flow, maintain a resilient balance sheet, and trade at a valuation that appropriately reflects the underlying segment value?**

The analysis must make the portfolio economics visible rather than allowing consolidated financial statements to hide differences between high-return businesses, cyclical businesses and persistent capital consumers.
