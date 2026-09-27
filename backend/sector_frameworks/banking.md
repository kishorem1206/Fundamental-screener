# Banking Sector Fundamental Analysis

## Single Source of Truth — Version 1.0

> **DOCUMENT STATUS: CANONICAL**
>
> This document is the authoritative specification for analysing listed banking companies.
>
> Any AI agent, scoring engine, validation agent, report generator, API, or frontend component analysing a company classified as `BANK` MUST use this document as the primary source of truth.
>
> Do NOT invent, add, remove, or substitute banking metrics without explicitly updating this document.
>
> This document defines:
>
> * What metrics must be analysed
> * What each metric means
> * How metrics should be interpreted
> * Which metrics are mandatory vs optional
> * What trends matter
> * What constitutes a red flag
> * What data sources should be preferred
> * How missing data should be handled
> * How peer comparison should work
> * How valuation should be interpreted
> * How the final banking investment analysis should be structured

---

# 1. Scope

This framework applies ONLY to companies classified as:

```text
BANK
COMMERCIAL_BANK
PRIVATE_BANK
PUBLIC_SECTOR_BANK
SMALL_FINANCE_BANK
UNIVERSAL_BANK
```

It does NOT apply to:

```text
NBFC
HFC
INSURANCE
AMC
BROKING
FINTECH
PAYMENTS_BANK
OTHER_FINANCIAL_SERVICES
```

unless explicitly specified by a future framework.

For NBFCs, use:

```text
nbfc.md
```

For Insurance, use:

```text
insurance.md
```

---

# 2. Core Philosophy

A bank must NOT be analysed like a normal manufacturing or service company.

Traditional metrics such as:

```text
Revenue CAGR
EBITDA Margin
Debt/Equity
Current Ratio
Free Cash Flow
```

must NOT be treated as the primary measures of banking quality.

A bank is fundamentally a:

```text
Deposit/Funding
        ↓
Lending
        ↓
Interest Spread
        ↓
Credit Risk
        ↓
Provisioning
        ↓
Capital
        ↓
Return on Assets / Equity
```

business.

Therefore the analysis must focus on:

1. Funding quality
2. Loan growth
3. Net interest margin
4. Asset quality
5. Provisioning
6. Operating efficiency
7. Capital adequacy
8. Profitability
9. Balance-sheet liquidity
10. Valuation
11. Trend
12. Peer-relative performance

---

# 3. Mandatory Banking Metrics

Every bank analysis SHOULD attempt to obtain the following metrics.

## A. Funding Quality

### 3.1 CASA Ratio

Metric key:

```text
casa_ratio
```

Definition:

```text
CASA Ratio =
(Current Account Deposits + Savings Account Deposits)
/
Total Deposits
× 100
```

Interpretation:

Higher CASA generally indicates a lower-cost and more stable deposit franchise.

However:

```text
HIGH CASA ≠ automatically good
LOW CASA ≠ automatically bad
```

The trend and peer comparison are more important than a single number.

Analyse:

```text
Current CASA
Previous-year CASA
3Y CASA trend
5Y CASA trend if available
Peer CASA
```

Red flag:

```text
CASA declining persistently
+
term deposit growth accelerating
```

This may indicate rising funding costs.

---

### 3.2 Deposit Growth

Metric key:

```text
deposit_growth
```

Track:

```text
YoY Deposit Growth
3Y Deposit CAGR
5Y Deposit CAGR
```

Interpret alongside:

```text
Loan Growth
CASA Growth
Term Deposit Growth
```

Do NOT interpret deposit growth in isolation.

---

### 3.3 Term Deposit Growth

Metric key:

```text
term_deposit_growth
```

Rapid term-deposit growth combined with declining CASA can indicate increasing funding costs.

Important relationship:

```text
Term Deposit Growth > Overall Deposit Growth
+
CASA declining
=
Potential Funding Cost Pressure
```

---

# 4. Core Earnings

## 4.1 Net Interest Margin

Metric key:

```text
nim
```

NIM is one of the most important banking metrics.

Track:

```text
Current NIM
YoY change
QoQ change
3Y trend
5Y trend
Peer median
```

Interpret:

```text
Rising NIM
    → improving core spread

Stable NIM
    → stable core economics

Declining NIM
    → potential funding/mix/pricing pressure
```

A 5-10 bps movement can be materially meaningful for a large bank.

Do NOT compare NIM blindly across fundamentally different banking models.

---

## 4.2 Net Interest Income Growth

Metric key:

```text
nii_growth
```

Track:

```text
YoY NII Growth
3Y NII CAGR
5Y NII CAGR
```

Interpret together with:

```text
Loan Growth
NIM
Deposit Growth
```

High NII growth caused only by aggressive balance-sheet expansion is different from high NII growth supported by sustainable NIM.

---

# 5. Loan / Credit Growth

## 5.1 Loan / Advances Growth

Metric key:

```text
loan_growth
```

Track:

```text
YoY Loan Growth
3Y CAGR
5Y CAGR
```

Compare against:

```text
Deposit Growth
Nominal economic growth
Peer loan growth
Asset quality
Capital adequacy
```

Do NOT reward extremely high loan growth automatically.

---

## 5.2 Loan Growth vs Deposit Growth

Derived metric:

```text
loan_growth_minus_deposit_growth
```

Interpret:

```text
Deposit Growth > Loan Growth
```

can indicate balance-sheet normalization / liquidity strengthening.

Whereas:

```text
Loan Growth >> Deposit Growth
```

can increase funding and liquidity pressure.

The attached banking framework explicitly uses the relationship between deposit growth and loan growth as a "balance sheet repair" signal.

---

# 6. Liquidity / Balance Sheet

## 6.1 Loan-to-Deposit Ratio

Metric key:

```text
loan_to_deposit_ratio
```

Formula:

```text
Gross Advances / Deposits × 100
```

Interpret in context.

A high LDR means a larger proportion of deposits is deployed into loans.

Potential concern:

```text
High LDR
+
weak deposit growth
+
high loan growth
=
funding/liquidity pressure
```

Do NOT use one universal threshold for every bank.

Track:

```text
Current LDR
Historical LDR
Peer LDR
Trend
```

The supplied banking framework specifically highlights LDR and uses >90% as one component of a "repair phase" trigger.

---

# 7. Asset Quality

Asset quality is one of the highest-priority banking categories.

## 7.1 Gross NPA

Metric key:

```text
gross_npa
```

Definition:

Percentage of gross advances classified as non-performing.

Track:

```text
Current GNPA
YoY change
QoQ change
3Y trend
5Y trend
Peer comparison
```

Lower is generally better.

But trend is critical.

---

## 7.2 Net NPA

Metric key:

```text
net_npa
```

Track:

```text
Current NNPA
YoY change
3Y trend
Peer comparison
```

Lower is generally better.

---

## 7.3 Provision Coverage Ratio

Metric key:

```text
provision_coverage_ratio
```

Interpret together with:

```text
Gross NPA
Net NPA
Credit Cost
Write-offs
```

A low NNPA relative to GNPA should be examined alongside provisioning.

The supplied framework specifically connects the Gross-NPA/Net-NPA relationship with provisioning strength.

---

## 7.4 Credit Cost

Metric key:

```text
credit_cost
```

Track:

```text
Current Credit Cost
YoY change
3Y average
5Y average
```

High or rising credit cost can indicate deteriorating loan economics even before headline profitability visibly deteriorates.

---

## 7.5 Slippage Ratio

Metric key:

```text
slippage_ratio
```

Track where available.

This measures fresh deterioration entering the NPA pool.

A bank with:

```text
Low GNPA
+
High Slippages
```

should NOT automatically be classified as low-risk.

---

## 7.6 Write-Offs

Metric key:

```text
write_offs
```

Track:

```text
Absolute write-offs
Write-offs / advances
Write-off trend
Recoveries from written-off accounts
```

Do not interpret declining GNPA without checking whether write-offs are driving the improvement.

---

# 8. Profitability

## 8.1 Return on Assets

Metric key:

```text
roa
```

ROA is one of the most important banking profitability metrics.

Track:

```text
Current ROA
3Y average
5Y average
Trend
Peer median
```

Small changes can be economically meaningful in banking.

The supplied framework identifies ROA as a definitive measure of balance-sheet profitability and notes that even a 10-basis-point movement can matter materially.

---

## 8.2 Return on Equity

Metric key:

```text
roe
```

Track:

```text
Current ROE
3Y average
5Y average
Trend
Peer comparison
```

ROE must always be interpreted alongside:

```text
ROA
Leverage
Capital Adequacy
Asset Quality
```

High ROE generated primarily through excessive leverage should not receive the same quality score as high ROE generated through strong ROA.

---

## 8.3 Net Profit Growth

Metric key:

```text
pat_growth
```

Track:

```text
YoY PAT Growth
3Y PAT CAGR
5Y PAT CAGR
```

Do NOT treat PAT growth alone as proof of improving quality.

Break PAT growth into:

```text
NII growth
NIM
Other income
Operating expenses
Credit costs
Provisions
Tax
```

---

# 9. Operating Efficiency

## 9.1 Cost-to-Income Ratio

Metric key:

```text
cost_to_income
```

Lower is generally better, subject to growth investment.

Track:

```text
Current
YoY
3Y trend
Peer comparison
```

---

## 9.2 Operating Expense Growth

Metric key:

```text
opex_growth
```

Compare:

```text
Opex Growth
vs
Revenue/NII Growth
```

Persistent expense growth materially above income growth can indicate operating leverage deterioration.

---

# 10. Capital Strength

## 10.1 Capital Adequacy Ratio

Metric key:

```text
capital_adequacy_ratio
```

Track:

```text
Current CAR
Regulatory requirement
Buffer over requirement
Trend
Peer comparison
```

The attached framework treats CAR as the bank's safety cushion and highlights capital strength as a fundamental component of resilience.

---

## 10.2 CET1 Ratio

Metric key:

```text
cet1_ratio
```

Where available, prioritize CET1 over relying only on aggregate CAR.

Track:

```text
Current CET1
Trend
Regulatory minimum
Buffer
Peer comparison
```

---

## 10.3 Tier 1 Capital Ratio

Metric key:

```text
tier1_ratio
```

Track where available.

---

# 11. Deposit Franchise Quality

Where data is available, analyse:

```text
casa_ratio
deposit_growth
term_deposit_growth
retail_deposit_growth
wholesale_deposit_growth
```

The ideal analysis should determine:

```text
Is the bank growing deposits?

AND

Is it growing low-cost deposits?

AND

Is the funding mix improving or deteriorating?
```

Do not simply reward high deposit growth.

---

# 12. Other Income

Metric key:

```text
other_income_growth
```

Analyse:

```text
Other Income Growth
Other Income / Total Income
Fee Income Growth
Trading Income
Treasury Income
One-off gains
```

If PAT growth is driven disproportionately by volatile trading/treasury income, flag it.

---

# 13. Digital / Operating Franchise

Where reliable data is available, optionally track:

```text
digital_transaction_growth
digital_customer_growth
branch_growth
employee_growth
business_per_employee
profit_per_employee
```

These are secondary metrics.

They should NOT override:

```text
NIM
Asset Quality
ROA
Capital
Funding
```

---

# 14. Valuation

Valuation MUST be analysed separately from business quality.

## 14.1 Price-to-Book

Metric key:

```text
pb_ratio
```

P/B is the primary valuation metric for banks.

Do NOT use:

```text
Low P/B = automatically cheap
High P/B = automatically expensive
```

Instead evaluate:

```text
P/B
ROE
ROA
Growth
Asset Quality
Capital Quality
NIM
```

A bank with structurally higher ROE and better asset quality can rationally command a higher P/B.

---

## 14.2 P/E

Metric key:

```text
pe_ratio
```

Use as a secondary valuation metric.

P/E can be useful but should generally not replace P/B for bank valuation analysis.

---

# 15. Mandatory Trend Analysis

Every banking analysis must examine:

```text
QoQ
YoY
3Y
5Y
```

where data exists.

Minimum trend set:

```text
NIM
CASA
Deposit Growth
Loan Growth
GNPA
NNPA
PCR
Credit Cost
ROA
ROE
CAR
PAT Growth
P/B
```

The screener must avoid conclusions based solely on the latest quarter.

---

# 16. Peer Benchmarking

Every bank should be compared with relevant peers.

Peer comparison must be:

```text
same country
same regulatory environment
same broad business model
similar size where possible
```

Compare at minimum:

```text
NIM
CASA
Loan Growth
Deposit Growth
LDR
GNPA
NNPA
PCR
Credit Cost
ROA
ROE
CAR
P/B
P/E
```

The supplied framework explicitly requires peer-to-peer benchmarking because absolute scale can hide slowing momentum.

---

# 17. Red Flag Engine

Red flags must be based on:

```text
absolute deterioration
+
trend deterioration
+
peer divergence
+
internal inconsistency
```

NOT on arbitrary single-number thresholds alone.

---

## 17.1 Asset Quality Deterioration

Flag HIGH when:

```text
GNPA rises materially
AND
NNPA rises materially
AND/OR
Slippages rise materially
```

---

## 17.2 Growth / Asset Quality Divergence

Flag when:

```text
Loan Growth is very high
AND
GNPA is increasing materially
```

The supplied framework specifically identifies aggressive growth combined with rising GNPA as a red-flag condition.

---

## 17.3 Provisioning Erosion

Flag when:

```text
GNPA - NNPA gap narrows materially
```

without a convincing improvement in actual asset quality.

---

## 17.4 Funding Deterioration

Flag when:

```text
CASA declines
AND
term deposits grow rapidly
```

---

## 17.5 Margin Pressure

Flag when:

```text
NIM declines materially
AND
funding costs rise
```

---

## 17.6 Balance-Sheet Pressure

Flag when:

```text
Loan Growth > Deposit Growth
AND
LDR is elevated
```

---

## 17.7 Profitability Deterioration

Flag when:

```text
ROA declines
OR
ROE declines
```

especially when deterioration persists across multiple periods.

---

## 17.8 Capital Weakening

Flag when:

```text
CAR/CET1 declines materially
AND
loan growth remains high
```

---

# 18. Composite Investment Quality Framework

The system should evaluate five major dimensions.

## A. Growth

Includes:

```text
Loan Growth
Deposit Growth
NII Growth
PAT Growth
```

## B. Profitability

Includes:

```text
NIM
ROA
ROE
Cost-to-Income
```

## C. Asset Quality

Includes:

```text
GNPA
NNPA
PCR
Slippages
Credit Cost
Write-offs
```

## D. Balance Sheet Strength

Includes:

```text
CASA
LDR
CAR
CET1
Deposit Franchise
Funding Mix
```

## E. Valuation

Includes:

```text
P/B
P/E
```

Do not allow valuation to compensate for severe business-quality deterioration.

A cheap bank with deteriorating asset quality should NOT automatically rank highly.

---

# 19. Suggested Scoring Weights

Default weights:

```text
Growth                 15%
Profitability          25%
Asset Quality          25%
Balance Sheet Strength 20%
Valuation              15%
```

These are DEFAULT weights only.

They must be configurable.

The scoring engine must normalize scores when metrics are unavailable.

Example:

```text
Metric unavailable
→ N/A
→ excluded from denominator
→ no penalty
```

Never:

```text
N/A → 0
```

---

# 20. Data Hierarchy

The system must use the following source hierarchy.

## Tier 1 — Regulatory / Official

Highest priority.

### RBI

Use RBI for:

```text
Banking statistics
Regulatory data
Asset quality
Capital adequacy
System-level banking data
Regulatory definitions
```

RBI should be the preferred authority for definitions and regulatory banking statistics.

### NSE / BSE Corporate Filings

Use exchange filings for:

```text
Quarterly financial results
Annual financial results
Corporate announcements
XBRL filings
Investor disclosures
```

NSE provides financial-result filings and XBRL data, including a dedicated banking financial-results format.

### Company Investor Relations

Use the bank's official website for:

```text
Investor presentations
Annual reports
Quarterly results
Earnings presentations
Management commentary
Business metrics
CASA
Advances
Deposits
NPA
Capital ratios
Segment data
```

Company disclosures are particularly important for metrics that may not appear cleanly in standardized financial statements.

---

# 21. Tier 2 — High Quality Secondary Sources

Use for:

```text
Cross-checking
Historical datasets
Peer comparison
Market ratios
```

Potential sources:

```text
Screener
Moneycontrol
Trendlyne
MarketsMojo
Capital Market
Reuters
Bloomberg
S&P Capital IQ
LSEG
```

These should NOT override official company/regulatory filings when discrepancies exist.

---

# 22. Source Conflict Rule

If two sources disagree:

```text
Regulatory filing
    >
Exchange filing
    >
Company investor presentation
    >
Reputable financial-data provider
    >
General financial website
    >
Search result / article
```

The system must preserve:

```text
source
source_date
period
reported_value
normalized_value
calculation_method
```

Do NOT silently replace conflicting values.

---

# 23. Data Provenance

Every stored metric must have:

```text
company_id
metric_key
period
value
unit
source
source_url
source_document
source_date
retrieved_at
reported_or_calculated
calculation_formula
confidence
```

Example:

```json
{
  "metric": "casa_ratio",
  "value": 32.3,
  "unit": "%",
  "period": "2026-Q1",
  "reported_or_calculated": "reported",
  "source": "company_quarterly_results",
  "confidence": "HIGH"
}
```

---

# 24. Reported vs Calculated Metrics

The system must distinguish:

```text
REPORTED
CALCULATED
DERIVED
ESTIMATED
```

Example:

```text
ROA reported by company
→ REPORTED

Loan Growth calculated from current and prior period advances
→ CALCULATED

Loan Growth - Deposit Growth
→ DERIVED

Estimated normalized earnings
→ ESTIMATED
```

Never present a calculated value as though it were directly reported.

---

# 25. Missing Data Policy

If a metric cannot be obtained:

```text
value = N/A
```

Do NOT:

```text
value = 0
value = average
value = estimated without disclosure
```

unless the framework explicitly permits estimation.

Missing data must never automatically lower the company's score.

---

# 26. Unit Normalization

Normalize:

```text
₹
₹ crore
₹ lakh crore
%
bps
x
```

Internally store normalized values.

For percentage metrics:

```text
3.26%
```

must not accidentally become:

```text
0.0326%
```

or:

```text
326%
```

The system must explicitly store the unit.

---

# 27. AI Interpretation Rules

The AI MUST:

1. Read this document before analysing a bank.
2. Identify the company as a BANK before applying this framework.
3. Retrieve the latest available data.
4. Retrieve historical data.
5. Retrieve peer data.
6. Identify missing metrics.
7. Distinguish reported vs calculated values.
8. Explain important changes.
9. Identify red flags.
10. Separate business quality from valuation.

The AI MUST NOT:

```text
invent metrics
invent thresholds
invent financial values
treat N/A as zero
use generic industrial-company metrics as primary banking metrics
call a bank cheap solely because P/B is low
call a bank high quality solely because ROE is high
ignore asset quality
ignore funding quality
ignore capital adequacy
```

---

# 28. Required Output Structure

Every bank analysis must produce:

```text
1. Executive Summary

2. Banking Quality Score

3. Growth
   - Loan Growth
   - Deposit Growth
   - NII Growth
   - PAT Growth

4. Funding Quality
   - CASA
   - Term Deposits
   - Deposit Mix

5. Core Profitability
   - NIM
   - ROA
   - ROE
   - Cost-to-Income

6. Asset Quality
   - GNPA
   - NNPA
   - PCR
   - Slippages
   - Credit Cost
   - Write-offs

7. Balance Sheet Strength
   - LDR
   - CAR
   - CET1
   - Funding Strength

8. Peer Comparison

9. Valuation
   - P/B
   - P/E

10. Trend Analysis

11. Red Flags

12. Positive Signals

13. Key Things to Track Next Quarter

14. Final Investment Interpretation
```

---

# 29. Quarterly Tracking

Every new quarter should compare the latest data with the previous period.

The system should explicitly answer:

```text
Is NIM improving?

Is CASA improving?

Is deposit growth improving?

Is loan growth accelerating?

Is asset quality improving?

Are slippages increasing?

Is credit cost rising?

Is ROA improving?

Is ROE improving?

Is capital strength improving?

Is valuation becoming more attractive?

Is the original investment thesis strengthening or weakening?
```

This follows the framework's "Buy → Understand → Track → Review" philosophy.

---

# 30. Final Principle

The purpose of this framework is NOT to produce the highest numerical score.

The purpose is to determine:

```text
Is the bank's competitive advantage strengthening or weakening?

Is growth healthy or risky?

Is funding becoming cheaper or more expensive?

Is asset quality improving or deteriorating?

Is profitability structurally improving?

Is capital sufficient for future growth?

Is the stock valuation justified by the quality of the franchise?
```

The final output should transform:

```text
Raw Financial Data
        ↓
Banking Metrics
        ↓
Trends
        ↓
Peer Comparison
        ↓
Risk Signals
        ↓
Valuation
        ↓
Investment Thesis
```

into a clear, evidence-backed banking investment analysis.

---

# 31. Framework Governance

This file is the canonical banking framework.

Any proposed change must:

1. Modify this document first.
2. Increment the framework version.
3. Record the change.
4. Update the corresponding Python/config implementation.
5. Update tests.
6. Update AI prompts if required.

Python code MUST implement this document.

Python code must NOT silently redefine this document.

---

# 32. Version History

## v1.0

Initial canonical banking framework covering:

```text
Funding
CASA
Deposits
NIM
NII
Loan Growth
LDR
GNPA
NNPA
PCR
Credit Cost
Slippages
Write-offs
ROA
ROE
Cost-to-Income
CAR
CET1
Valuation
Peer Comparison
Trend Analysis
Red Flags
Data Provenance
Source Hierarchy
```
