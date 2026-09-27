# Fundamental Screener — Balance Sheet Analysis Engine
## Consolidated Implementation Specification
### Based on the Balance Sheet Analysis Engine + CFO Balance Sheet Analysis Guide

---

# 1. Purpose

Build a **dedicated Balance Sheet Analysis Engine** for the Fundamental Screener.

This specification is ONLY for Balance Sheet analysis.

It should analyze the balance sheet as:

- a structural representation of the business
- a source/application of funds
- a liquidity and solvency statement
- a working-capital system
- a capital-allocation system
- a risk-detection system
- a connected component of the three-statement model

The engine must go beyond displaying balance-sheet numbers.

It should answer:

> What does the company own?

> How is those assets funded?

> How much liquidity does the company have?

> Where is capital getting trapped?

> Are receivables/inventory/payables changing abnormally?

> Is debt increasing or decreasing?

> Can the company meet near-term obligations?

> Is capital being deployed productively?

> Is the balance sheet strengthening or weakening?

> Which line items require investigation?

---

# 2. Source Frameworks Incorporated

This specification combines two supplied frameworks:

### Framework A — Balance Sheet Analysis Engine / SOIC framework

Core concepts include:

- Sources vs Applications of Funds
- Net Worth / Book Value
- four Balance Sheet archetypes
- P&L ↔ Balance Sheet ↔ Cash Flow connectivity
- DuPont ROCE drivers
- Cash Conversion Cycle
- balance-sheet transformation
- de-leveraging
- capex expansion
- working-capital efficiency
- forensic red flags

The framework explicitly describes the Balance Sheet as a structural representation of financial resources and commitments and defines the accounting identity:

```text
Sources of Funds = Applications of Funds
Equity + Liabilities = Assets
```

It also identifies fixed assets, CWIP, investments, inventory, receivables and cash as key applications of funds. 

### Framework B — CFO Balance Sheet framework

The CFO framework adds:

- mandatory accounting-equation validation
- point-in-time analysis
- line-by-line risk analysis
- AR aging
- DSO
- inventory aging
- PPE utility/impairment
- AP aging
- DPO
- accrued-expense review
- deferred-revenue obligations
- debt maturity analysis
- liquidity
- leverage
- cash-vs-obligations analysis

The CFO framework explicitly states that analysis should begin only after verifying:

```text
Total Assets = Total Liabilities + Stockholders' Equity
```

---

# 3. Core Architecture

```text
                    SOURCE DATA
                        │
                        ↓
                DATA EXTRACTION
                        │
                        ↓
               DATA NORMALIZATION
                        │
                        ↓
             BALANCE SHEET DATASET
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
     INTEGRITY       RATIO        TREND ENGINE
     VALIDATOR       ENGINE
          │             │             │
          └─────────────┼─────────────┘
                        ↓
              WORKING CAPITAL ENGINE
                        ↓
                LIQUIDITY ENGINE
                        ↓
                LEVERAGE ENGINE
                        ↓
             CAPITAL EFFICIENCY ENGINE
                        ↓
                RISK ENGINE
                        ↓
             ARCHETYPE CLASSIFIER
                        ↓
               BALANCE SHEET
                 ANALYSIS OUTPUT
                        ↓
                 LLM EXPLANATION
                        ↓
                    UI / PDF
```

---

# 4. Golden Rule

**Never analyze a Balance Sheet before validating its accounting identity.**

```text
Total Assets
=
Total Liabilities + Equity
```

Implementation:

```python
difference = abs(
    total_assets -
    (total_liabilities + total_equity)
)
```

If difference exceeds the configured tolerance:

```text
BALANCE_SHEET_INTEGRITY_ERROR
```

The system must:

1. show the discrepancy
2. identify the affected period
3. identify the source
4. stop downstream analysis for that period if the discrepancy is material
5. not silently force-balance the statement

The CFO framework specifically makes this the first mandatory check. 

---

# 5. Point-in-Time Nature

The Balance Sheet is a **point-in-time snapshot**.

Every record must therefore contain:

```text
company
period_end
financial_year
quarter
statement_type
standalone/consolidated
currency
unit
source
```

Never compare values without checking:

```text
same company
same reporting basis
same unit
same currency
compatible periods
```

---

# 6. Balance Sheet Master Data Model

## 6.1 Assets

### Current Assets

```text
cash_and_cash_equivalents
bank_balances
short_term_investments
trade_receivables
inventory
other_current_assets
loans_and_advances_current
```

### Inventory Subcategories

Where available:

```text
raw_material_inventory
work_in_progress
finished_goods
stores_and_spares
other_inventory
```

### Non-Current Assets

```text
property_plant_equipment
capital_work_in_progress
intangible_assets
goodwill
long_term_investments
deferred_tax_assets
other_non_current_assets
```

---

# 7. Liabilities Master Data

## Current Liabilities

```text
trade_payables
short_term_borrowings
current_maturity_of_long_term_debt
accrued_expenses
other_current_liabilities
deferred_revenue
current_provisions
```

## Non-Current Liabilities

```text
long_term_borrowings
lease_liabilities
deferred_tax_liabilities
long_term_provisions
other_non_current_liabilities
```

---

# 8. Equity Master Data

```text
share_capital
securities_premium
retained_earnings
reserves
other_equity
minority_interest
```

Calculate:

```text
Total Equity
Net Worth / Book Value
```

The Balance Sheet framework defines net worth/book value as:

```text
Net Worth =
Total Assets - Total Outside Liabilities
```

and links it to share capital plus reserves/surplus.

---

# 9. Sources vs Applications of Funds

Create a visual Balance Sheet "House".

## Sources

```text
Equity
Retained Earnings
Debt
Trade Payables
Other Liabilities
```

## Applications

```text
PPE
CWIP
Investments
Inventory
Receivables
Cash
Other Assets
```

UI:

```text
                 BALANCE SHEET HOUSE

        SOURCES                  APPLICATIONS

        Equity  ───────────────→
        Debt    ───────────────→   PPE
        Payables ──────────────→   CWIP
        Other Liab ────────────→   Investments
                                   Inventory
                                   Receivables
                                   Cash
```

This is one of the primary visualizations from the supplied framework.

---

# 10. Common-Size Balance Sheet

For each line item calculate:

```text
Line Item / Total Assets
```

For liabilities and equity:

```text
Line Item / Total Liabilities + Equity
```

Example:

```text
Cash              12%
Receivables       18%
Inventory         14%
PPE               32%
Other Assets      24%
```

Track historical movement.

The CFO case study explicitly presents balance-sheet items both as absolute values and percentages of total assets/liabilities.

---

# 11. Line-by-Line Asset Analysis

Every major asset should have:

```text
absolute_value
%_of_assets
YoY_change
3Y_change
5Y_change
10Y_change
risk_indicators
related_ratios
source
confidence
```

---

# 12. Cash Analysis

Calculate:

```text
Cash / Total Assets
Cash / Current Liabilities
Cash / Revenue
Cash / Debt
```

Also:

```text
Cash + Liquid Investments
Gross Debt
Net Debt
```

Formula:

```text
Net Debt =
Total Debt - Cash & Liquid Investments
```

If negative:

```text
Net Cash Position
```

instead of treating it as normal positive net debt.

---

# 13. Cash vs Near-Term Obligations

Build a cash-liquidity view:

```text
Cash
+
Expected Near-Term AR Collections
vs
Immediate AP / Debt Obligations
```

Flag:

```text
NEAR_TERM_LIQUIDITY_PRESSURE
```

The CFO framework specifically describes matching available cash and expected AR collections against immediate AP obligations.

This must remain a **liquidity timing indicator**, not a prediction of default.

---

# 14. Receivables Analysis

Calculate:

```text
Trade Receivables
Receivables / Assets
Receivables / Revenue
Receivables Growth
Receivables Growth - Revenue Growth
```

Where required inputs exist:

```text
DSO
Receivables Turnover
```

Preferred formula:

```text
DSO =
Average Trade Receivables
/
Credit Sales
×
Days
```

Where average balances are unavailable:

```text
Closing Receivables
/
Credit Sales
×
Days
```

with methodology clearly disclosed.

The CFO framework gives DSO as:

```text
AR / Credit Sales × Days in Period
```

and emphasizes its role in assessing collection efficiency.

---

# 15. AR Aging

Where source data permits:

```text
Current
0–30 Days
31–60 Days
61–90 Days
90+ Days
```

Calculate:

```text
60+ AR / Total AR
90+ AR / Total AR
```

Risk indicators:

```text
AGING_DETERIORATION
COLLECTION_RISK
BAD_DEBT_RISK_INDICATOR
```

Suggested source-framework threshold:

```text
60+ Day AR > 15% of Total AR
```

should trigger an investigation flag.

Do not state that receivables are fraudulent or uncollectible solely from this threshold.

---

# 16. Receivables Ballooning Detection

Flag when:

```text
Receivables Growth
>
Revenue Growth
```

Stronger signal:

```text
Receivables Growth
>
Revenue Growth
for multiple periods
```

Strongest diagnostic:

```text
Receivables Growth > Revenue Growth
+
DSO increasing
+
CFO/PAT deteriorating
```

Output:

```text
WORKING_CAPITAL_COLLECTION_PRESSURE
```

---

# 17. Inventory Analysis

Calculate:

```text
Inventory / Assets
Inventory / Revenue
Inventory Growth
Inventory Growth - Revenue Growth
```

Where COGS and average inventory are available:

```text
Inventory Turnover =
COGS / Average Inventory
```

```text
Inventory Days =
365 / Inventory Turnover
```

Track:

```text
Inventory Turnover Trend
Inventory Days Trend
```

---

# 18. Inventory Aging

Where available:

```text
<30 Days
30–60 Days
60–90 Days
90–180 Days
180+ Days
```

Calculate:

```text
90+ Inventory / Total Inventory
```

Flag:

```text
SLOW_MOVING_INVENTORY
OBSOLESCENCE_RISK
INVENTORY_BUILDUP
```

The CFO framework specifically emphasizes inventory aging because book inventory does not necessarily equal realizable economic value.

---

# 19. PPE Analysis

Analyze:

```text
Gross PPE
Net PPE
Accumulated Depreciation
PPE Growth
PPE / Assets
PPE / Revenue
```

Also connect to:

```text
Capex
Depreciation
Revenue Growth
ROCE
Asset Turnover
```

Calculate:

```text
Fixed Asset Turnover =
Revenue / Average Net PPE
```

where data permits.

---

# 20. CWIP Analysis

Track:

```text
CWIP
CWIP / Gross Block
CWIP / Total Assets
CWIP Growth
```

Diagnostics:

```text
CWIP rising for multiple periods
+
revenue/capacity not improving
```

→

```text
CAPITAL_PROJECT_EXECUTION_RISK
```

Do not infer project failure without supporting evidence.

---

# 21. PPE / Capex Efficiency

Track:

```text
Capex
Depreciation
Gross Block
Net Block
Revenue
EBIT
ROCE
```

Useful relationships:

```text
Capex / Depreciation
Capex / Revenue
PPE Growth / Revenue Growth
```

Flag:

```text
PPE Growth materially above Revenue Growth
```

for investigation.

The supplied framework includes a capex-expansion screener using gross-block growth and ROCE.

---

# 22. Investment Analysis

Separate:

```text
Current Investments
Non-Current Investments
Strategic Investments
Other Investments
```

Where available.

Calculate:

```text
Investments / Assets
Investments / Equity
Cash + Investments / Assets
Cash + Investments / Market Cap
```

Investigate:

```text
large investments relative to core operating assets
rapid investment growth
related-party investments
ICDs / loans to related entities
```

---

# 23. Inter-Corporate Deposits / Related-Party Loans

Where available identify:

```text
ICDs
Loans to Subsidiaries
Loans to Associates
Loans to Promoters / Related Parties
Advances to Related Parties
```

Calculate:

```text
Related Party Loans / Net Worth
Related Party Loans / Assets
```

Source-framework warning:

```text
Loans to subsidiaries/sisters > 5% of Net Worth
```

→ investigation flag.

Label:

```text
RELATED_PARTY_CAPITAL_EXPOSURE
```

Do not automatically classify the transaction as wrongdoing.

---

# 24. Trade Payables

Calculate:

```text
Payables / Revenue
Payables / Current Liabilities
Payables Growth
```

Where inputs permit:

```text
DPO
Payables Turnover
```

Preferred:

```text
DPO =
Average Payables
/
Credit Purchases
× Days
```

The CFO framework explicitly defines DPO using credit purchases and payables.

---

# 25. AP Aging

Where available:

```text
Current
0–30
31–60
61–90
90+
```

Calculate:

```text
90+ AP / Total AP
```

Flag:

```text
PAST_DUE_PAYABLES
SUPPLIER_PAYMENT_PRESSURE
```

Important:

High DPO is not automatically positive.

It can indicate:

```text
supplier bargaining power
OR
cash-flow/payment stress
```

The engine should examine CFO, aging and liquidity context.

---

# 26. Accrued Expenses

Analyze:

```text
Accrued Expenses
Accrued Expenses / Revenue
Accrued Expenses / Current Liabilities
Growth
```

Flag:

```text
ACCRUAL_BUILDUP
```

when accruals rise unusually relative to operating activity.

The CFO framework requires review of accrual schedules to ensure obligations are properly recognized.

---

# 27. Deferred Revenue

Analyze:

```text
Deferred Revenue
Deferred Revenue / Revenue
Deferred Revenue Growth
Deferred Revenue / Current Liabilities
```

Interpret according to business model.

Also track:

```text
future performance obligations
```

The CFO framework specifically says deferred revenue represents customer prepayments for future delivery and requires checking fulfillment capability.

---

# 28. Debt Structure

Break total debt into:

```text
Short-Term Borrowings
Current Maturity of Long-Term Debt
Long-Term Borrowings
Lease Liabilities
```

Calculate:

```text
Gross Debt
Net Debt
Debt / Equity
Debt / Assets
Debt / Capital
Net Debt / Equity
Debt / EBITDA
Net Debt / EBITDA
```

Do not mix lease liabilities into debt without recording the methodology.

---

# 29. Debt Maturity Analysis

Where source data exists:

```text
<1 Year
1–3 Years
3–5 Years
5–10 Years
10+ Years
```

Calculate:

```text
Debt Due <1Y / Cash
Debt Due <1Y / CFO
Debt Due <1Y / FCF
```

Flag:

```text
MATURITY_CONCENTRATION
REFINANCING_RISK
NEAR_TERM_DEBT_PRESSURE
```

The CFO framework explicitly recommends reviewing 3-year, 5-year and 10-year maturity structures.

---

# 30. Equity Analysis

Track:

```text
Share Capital
Reserves
Retained Earnings
Other Equity
NCI
```

Calculate:

```text
Book Value
Book Value / Share
Equity Growth
Reserves Growth
```

Detect:

```text
equity dilution
large equity issuance
share buybacks
reserve movements
```

---

# 31. Net Worth

Calculate:

```text
Net Worth =
Total Assets - Total Outside Liabilities
```

Cross-check against:

```text
Share Capital + Reserves / Other Equity
```

Track:

```text
Net Worth Growth
Net Worth CAGR
Net Worth / Market Cap
```

---

# 32. Working Capital

Calculate:

```text
Gross Working Capital =
Current Assets

Net Working Capital =
Current Assets - Current Liabilities
```

Operating version:

```text
Operating Working Capital =
Receivables
+ Inventory
+ Other Operating Current Assets
- Payables
- Other Operating Current Liabilities
```

Track:

```text
Working Capital / Revenue
Working Capital Growth
Working Capital Days
```

---

# 33. Cash Conversion Cycle

Where inputs exist:

```text
CCC =
DSO + Inventory Days - DPO
```

Track:

```text
Current CCC
3Y Average
5Y Average
10Y Average
```

Visualize:

```text
DSO
DIO
DPO
CCC
```

The supplied Balance Sheet framework explicitly defines:

```text
CCC = Debtor Days + Inventory Days - Creditor Days
```

---

# 34. Liquidity Ratios

Minimum:

```text
Current Ratio =
Current Assets / Current Liabilities

Quick Ratio =
(Current Assets - Inventory) / Current Liabilities

Cash Ratio =
Cash / Current Liabilities
```

Also:

```text
Cash + Liquid Investments / Current Liabilities
```

Store methodology for every ratio.

---

# 35. Leverage Ratios

Calculate:

```text
Debt / Equity
Debt / Assets
Debt / Capital
Net Debt / Equity
Debt / EBITDA
Net Debt / EBITDA
```

Also:

```text
Liabilities / Equity
```

where useful.

Important:

The two supplied frameworks use different concepts for leverage:

- the Balance Sheet framework emphasizes Debt/Equity
- the CFO example uses Total Liabilities/Equity

Therefore store them as **separate metrics**:

```text
debt_to_equity
liabilities_to_equity
```

Do not substitute one for the other.

---

# 36. Interest Coverage

Although the calculation requires P&L inputs, this is part of the Balance Sheet risk layer.

Calculate:

```text
Interest Coverage =
EBIT / Interest Expense
```

Store:

```text
latest
3Y average
5Y trend
```

The CFO framework uses EBIT / Interest Expense and illustrates a 3.1x value.

---

# 37. Capital Efficiency / ROCE

ROCE should be decomposed.

Formula:

```text
ROCE =
EBIT / Capital Employed
```

DuPont:

```text
ROCE
=
(EBIT / Revenue)
×
(Revenue / Capital Employed)
```

Therefore:

```text
ROCE
=
EBIT Margin
×
Capital Employed Turnover
```

The supplied Balance Sheet framework explicitly identifies these two drivers.

UI:

```text
ROCE
  │
  ├── EBIT Margin
  │
  └── Capital Employed Turnover
          │
          ├── Fixed Assets
          └── Working Capital
```

The Balance Sheet module should show the capital-efficiency effect without duplicating the main P&L engine.

---

# 38. Capital Employed

Define the methodology explicitly.

Possible definition:

```text
Capital Employed =
Total Assets - Current Liabilities
```

or:

```text
Capital Employed =
Equity + Long-Term Debt
```

The application must choose one canonical methodology and expose it.

Do not silently mix definitions between companies.

---

# 39. ROCE Driver Analysis

Classify ROCE movement into:

```text
MARGIN_DRIVEN
TURNOVER_DRIVEN
BOTH
NEITHER / MIXED
```

Example:

```text
ROCE ↑
EBIT Margin ↑
Capital Turnover flat
```

→ margin-led improvement.

Example:

```text
ROCE ↑
EBIT Margin flat
Capital Turnover ↑
```

→ asset/capital-efficiency-led improvement.

This is a diagnostic explanation, not a ranking.

---

# 40. Balance Sheet Archetypes

Implement the four framework archetypes:

```text
STRONG
WEAK
MIDDLE
TRANSFORMING
```

Important:

These are **framework classifications**, not universal accounting categories.

The classifier should be configurable.

---

# 41. Strong Balance Sheet Signals

Potential signals from the supplied framework:

```text
High cash/liquid investments
Low or zero net debt
Low working-capital intensity
Internal-accrual-funded expansion
```

The source gives an illustrative "war chest" concept of cash/liquid investments around 30–40% of assets.

Do not hard-code this as a universal investment rule.

---

# 42. Weak Balance Sheet Signals

Potential signals:

```text
High leverage
Ballooning receivables
Ballooning inventory
Negative/weak cash generation
Frequent equity dilution
Short-term debt dependence
```

The source gives illustrative D/E ranges, but these should remain configurable and sector-aware.

---

# 43. Middle Balance Sheet

Potential signals:

```text
Manageable debt
Normal working capital
Balanced funding
Recent capex
Operating leverage still developing
```

Output:

```text
MIDDLE_BALANCE_SHEET
```

with supporting evidence.

---

# 44. Transforming Balance Sheet

Detect movement toward stronger structure:

```text
Debt declining
+
Cash increasing
+
CCC improving
+
Working Capital intensity declining
```

or:

```text
Post-IPO cleanup
+
Debt reduction
+
Balance Sheet strengthening
```

Output:

```text
TRANSFORMING_BALANCE_SHEET
```

Do not predict future transformation; identify historical/current evidence.

---

# 45. Balance Sheet Transformation Dashboard

Create:

```text
                  BALANCE SHEET TRANSFORMATION

Debt             ████████████ → █████
Cash             ████         → █████████
CCC              72 days      → 34 days
D/E              1.4x        → 0.6x
ROCE             14%         → 21%
```

Then show:

```text
What changed?
Why did it change?
Which balance-sheet components contributed?
```

---

# 46. Red Flag Engine

The engine must run before final analysis.

## Rule 1 — Accounting Imbalance

```text
Assets != Liabilities + Equity
```

→

```text
BALANCE_SHEET_INTEGRITY_ERROR
```

---

## Rule 2 — High Leverage

Illustrative framework threshold:

```text
Debt / Equity > 0.75x
```

or stronger configurable thresholds based on sector.

Output:

```text
HIGH_LEVERAGE
```

Do not call this "insolvency" automatically.

---

## Rule 3 — Very High Leverage

CFO framework guardrail:

```text
Debt / Equity > 3x
```

→

```text
HIGH_LEVERAGE_INVESTIGATION
```

This is an analytical guardrail, not a prediction.

---

## Rule 4 — CFO Divergence

Source framework:

```text
Cumulative 3Y CFO
<
50% of Cumulative 3Y Net Profit
```

→

```text
LOW_CASH_EARNINGS_CONVERSION
```

This should be handled in the cross-statement layer.

---

## Rule 5 — Receivables / Inventory Spike

```text
Receivables growth
OR
Inventory growth
```

materially above revenue growth.

Stronger source-framework signal:

```text
Receivables or Inventory
growing 2x faster than Sales
```

→

```text
WORKING_CAPITAL_DRAG
```

---

# 47. Rule 6 — Equity Dilution

Flag:

```text
Share Capital Growth
+
Weak/Zero CFO
```

Potential issue:

```text
EXTERNAL_FUNDING_DEPENDENCE
```

Investigate:

```text
rights issue
QIP
preferential allotment
ESOP
warrants
convertibles
```

---

# 48. Rule 7 — Related-Party Loans / ICDs

Illustrative threshold:

```text
Related-party loans / Net Worth > 5%
```

→

```text
RELATED_PARTY_EXPOSURE
```

Show:

```text
Amount
Counterparty category
% Net Worth
Trend
Source
```

---

# 49. Rule 8 — Contingent Liabilities

Calculate:

```text
Contingent Liabilities / Net Worth
Contingent Liabilities / Assets
```

Illustrative framework threshold:

```text
Contingent Liabilities > 10% of Net Worth
```

→

```text
CONTINGENT_LIABILITY_RISK
```

The UI must display the actual amount and nature of exposure where available.

---

# 50. Rule 9 — Capex Without Cash Generation

Flag:

```text
Gross Block Growth > 50%
AND
CFO negative
```

→

```text
UNPRODUCTIVE_CAPEX_INVESTIGATION
```

Do not conclude that capex is unproductive without additional evidence.

---

# 51. Rule 10 — Working Capital Stress

Potential combination:

```text
DSO ↑
+
Inventory Days ↑
+
CCC ↑
+
CFO ↓
```

→

```text
WORKING_CAPITAL_STRESS
```

This multi-signal approach is preferable to relying on a single ratio.

---

# 52. Rule 11 — Liquidity Pressure

Potential combination:

```text
Cash ↓
+
Current Liabilities ↑
+
Short-Term Debt ↑
```

→

```text
LIQUIDITY_PRESSURE
```

---

# 53. Rule 12 — Debt Maturity Pressure

```text
Debt due within 12 months
>
Cash + expected near-term operating liquidity
```

→

```text
MATURITY_LIQUIDITY_RISK
```

Only calculate when maturity data is available.

---

# 54. Data Availability / Coverage Audit

This is mandatory.

The engine must tell the development team which Balance Sheet metrics are actually supported by current data.

Statuses:

```text
AVAILABLE
CALCULABLE
PARTIAL
MISSING_INPUT
SOURCE_REQUIRED
NOT_APPLICABLE
INVALID
```

Example:

```text
Metric: Inventory Turnover

COGS                  ✓
Opening Inventory     ✓
Closing Inventory     ✓

Status:
AVAILABLE
```

Another example:

```text
Metric: DPO

Credit Purchases     ✗
Average Payables     ✓

Status:
MISSING_INPUT
```

---

# 55. Dependency Graph

Every metric must declare dependencies.

Example:

```text
Inventory Turnover
├── COGS
├── Opening Inventory
└── Closing Inventory
```

```text
DSO
├── Average Receivables
├── Credit Sales
└── Days
```

```text
DPO
├── Average Payables
├── Credit Purchases
└── Days
```

```text
CCC
├── DSO
├── Inventory Days
└── DPO
```

```text
ROCE
├── EBIT
├── Capital Employed
└── methodology
```

---

# 56. Source-Gap Report

The application should generate:

```text
BALANCE SHEET DATA COVERAGE

Metric                     Status
──────────────────────────────────────
Cash                       AVAILABLE
Receivables                AVAILABLE
AR Aging                   MISSING
DSO                        CALCULABLE
Inventory                  AVAILABLE
Inventory Aging            MISSING
Inventory Turnover         CALCULABLE
Payables                   AVAILABLE
AP Aging                   MISSING
DPO                        PARTIAL
Debt                       AVAILABLE
Debt Maturity              MISSING
CWIP                       AVAILABLE
Related Party Loans        PARTIAL
Contingent Liabilities     AVAILABLE
```

Then:

```text
SOURCE GAPS

1. AR Aging
   Required: aging bucket data
   Priority: HIGH

2. Inventory Aging
   Required: aging bucket data
   Priority: HIGH

3. Debt Maturity
   Required: maturity schedule
   Priority: MEDIUM
```

---

# 57. Data Lineage

Every balance-sheet number should retain:

```text
company
period
value
currency
unit
statement_type
standalone/consolidated
source
source_document
source_page
extraction_method
confidence
```

Every derived metric:

```text
metric
formula
inputs
input_sources
methodology_version
confidence
```

UI should support:

```text
Metric
 ↓
Formula
 ↓
Input values
 ↓
Source document
 ↓
Page
```

---

# 58. Historical Analysis

For each major Balance Sheet item:

```text
1Y
3Y
5Y
7Y
10Y
```

Calculate:

```text
absolute change
percentage change
CAGR where valid
historical average
historical median
peak
trough
```

Track:

```text
Cash
Receivables
Inventory
PPE
CWIP
Debt
Payables
Equity
Net Worth
Working Capital
```

---

# 59. Balance Sheet Trend Dashboard

Show:

```text
ASSET TREND

Cash              ↑
Receivables       ↑↑
Inventory         →
PPE               ↑
Investments       ↓

FUNDING TREND

Debt              ↓
Payables          →
Equity            ↑
Net Worth         ↑
```

Then explain the structural changes.

---

# 60. Peer Comparison

Where peer data exists:

```text
Company
Peer Median
Peer Average
Peer Percentile
```

For:

```text
D/E
Net Debt/EBITDA
Current Ratio
Quick Ratio
DSO
Inventory Days
DPO
CCC
ROCE
Asset Turnover
Working Capital / Revenue
Cash / Assets
```

Do not use peer benchmarks when the peer set is incompatible with the company's sector/business model.

---

# 61. Sector-Aware Balance Sheet Layer

The core engine remains universal.

Then add sector-specific modules.

## Manufacturing

```text
Inventory
Inventory Days
PPE
CWIP
Fixed Asset Turnover
DPO
CCC
```

## IT / Services

```text
Receivables
DSO
Cash
Investments
Deferred Revenue
Working Capital
```

## FMCG

```text
Inventory
Inventory Turnover
Receivables
Payables
CCC
```

## Capital-Intensive Businesses

```text
PPE
CWIP
Capex
Debt
Debt Maturity
ROCE
Asset Turnover
```

## Banks / NBFCs

Do NOT apply manufacturing-style:

```text
Inventory
DIO
DPO
CCC
```

as core metrics.

Use a dedicated financial-institution balance-sheet schema instead.

---

# 62. Financial Institution Exception

For:

```text
Banks
NBFCs
Insurance
Financial Services
```

create separate Balance Sheet modules.

Potential fields include:

```text
Loans
Deposits
Borrowings
Investments
Gross NPA
Net NPA
Provisions
Capital
Liquidity
Capital Adequacy
```

The universal Balance Sheet engine should route these companies into the appropriate sector-specific schema.

---

# 63. JSON Output Schema

Recommended structure:

```json
{
  "company_id": "ABC",
  "period": "FY2026",
  "statement_basis": "CONSOLIDATED",

  "balance_sheet_integrity": {
    "status": "VALID",
    "total_assets": 0,
    "total_liabilities_equity": 0,
    "difference": 0
  },

  "assets": {
    "cash": 0,
    "receivables": 0,
    "inventory": 0,
    "ppe": 0,
    "cwip": 0,
    "investments": 0
  },

  "liabilities": {
    "trade_payables": 0,
    "short_term_debt": 0,
    "long_term_debt": 0,
    "lease_liabilities": 0
  },

  "equity": {
    "share_capital": 0,
    "reserves": 0,
    "total_equity": 0
  },

  "derived_metrics": {
    "net_worth": 0,
    "net_debt": 0,
    "current_ratio": 0,
    "quick_ratio": 0,
    "cash_ratio": 0,
    "debt_to_equity": 0,
    "debt_to_assets": 0,
    "debt_to_capital": 0,
    "net_debt_to_ebitda": 0,
    "dso": 0,
    "inventory_days": 0,
    "dpo": 0,
    "ccc": 0,
    "roce": 0,
    "capital_turnover": 0
  },

  "aging": {
    "ar": {},
    "inventory": {},
    "ap": {}
  },

  "debt_maturity": {},

  "risk_flags": [],

  "archetype": {
    "classification": "",
    "evidence": []
  },

  "coverage": {},

  "data_quality": {},

  "lineage": {}
}
```

---

# 64. Risk Flag JSON

Each risk should be structured:

```json
{
  "flag_id": "AR_GROWTH_OUTPACING_REVENUE",
  "severity": "AMBER",
  "status": "TRIGGERED",
  "metric": "Receivables Growth",
  "threshold": "Revenue Growth",
  "actual": 0,
  "comparison": 0,
  "period": "FY2026",
  "evidence": [],
  "source": [],
  "confidence": "HIGH"
}
```

This makes the UI and PDF deterministic.

---

# 65. Do Not Let the LLM Calculate

Architecture:

```text
RAW DATA
   ↓
DETERMINISTIC CALCULATION
   ↓
VALIDATED METRICS
   ↓
DIAGNOSTIC ENGINE
   ↓
LLAMA
```

Llama can:

```text
explain
summarize
connect observations
describe risks
write narrative
```

Llama cannot:

```text
invent values
calculate missing ratios
guess missing source data
silently replace definitions
mix periods
mix standalone/consolidated numbers
```

---

# 66. LLM Input

Provide:

```json
{
  "balance_sheet": {},
  "historical_trends": {},
  "working_capital": {},
  "liquidity": {},
  "leverage": {},
  "capital_efficiency": {},
  "risk_flags": {},
  "archetype": {},
  "coverage": {},
  "data_quality": {}
}
```

Prompt the LLM to answer:

```text
1. What changed?
2. Why does it matter?
3. Which balance-sheet line items explain the change?
4. What cross-statement evidence supports it?
5. What requires further investigation?
6. Which important data is unavailable?
```

---

# 67. UI Structure

# Balance Sheet

## Section 1 — Balance Sheet Snapshot

Cards:

```text
Total Assets
Net Worth
Cash
Gross Debt
Net Debt
Working Capital
D/E
Current Ratio
ROCE
CCC
```

---

## Section 2 — Balance Sheet House

Visual:

```text
ASSETS
────────────────────────
Cash
Receivables
Inventory
PPE
CWIP
Investments
Other

FUNDING
────────────────────────
Equity
Long-Term Debt
Short-Term Debt
Payables
Other Liabilities
```

---

## Section 3 — Asset Composition

Historical stacked chart:

```text
Cash
Receivables
Inventory
PPE
Investments
Other
```

---

## Section 4 — Funding Composition

Historical chart:

```text
Equity
Debt
Payables
Other Liabilities
```

---

## Section 5 — Working Capital

Show:

```text
DSO
Inventory Days
DPO
CCC
```

with historical trend.

---

## Section 6 — Receivables

Show:

```text
AR
DSO
AR Growth
Revenue Growth
AR Aging
```

---

## Section 7 — Inventory

Show:

```text
Inventory
Inventory Days
Inventory Turnover
Inventory Aging
```

---

## Section 8 — Debt

Show:

```text
Gross Debt
Net Debt
D/E
Net Debt/EBITDA
Interest Coverage
Debt Maturity
```

---

## Section 9 — Capital Efficiency

Show:

```text
ROCE
EBIT Margin
Capital Turnover
```

---

## Section 10 — Risk Diagnostics

Only show triggered items.

Example:

```text
⚠ Receivables growth is exceeding revenue growth
⚠ DSO has increased materially
⚠ Short-term debt has increased
✓ Net debt has declined
✓ Balance Sheet remains balanced
```

---

## Section 11 — Balance Sheet Archetype

Display:

```text
STRONG
WEAK
MIDDLE
TRANSFORMING
```

with:

```text
Evidence
Metrics
Historical change
Confidence
```

---

## Section 12 — Data Coverage

```text
Balance Sheet Data Coverage: 94%

Available             82
Calculable             9
Partial                3
Missing                6
Source Required        4
```

---

# 68. PDF Layout

Recommended order:

```text
1. Balance Sheet Executive Snapshot

2. Balance Sheet House

3. Asset Composition

4. Funding Composition

5. Cash & Liquidity

6. Receivables & Aging

7. Inventory & Aging

8. Payables & Aging

9. Working Capital / CCC

10. Debt & Maturity

11. Equity / Net Worth

12. PPE / CWIP / Capital Deployment

13. ROCE Decomposition

14. Balance Sheet Archetype

15. Risk Diagnostics

16. Historical Transformation

17. Data Coverage & Missing Inputs
```

---

# 69. Visual Design Principle

Do not create a page full of ratio cards.

Use:

```text
BIG NUMBER
+
TREND
+
CONTEXT
+
EXPLANATION
```

Example:

```text
DSO

62 days
↑ from 48

Company 5Y Avg: 49
Peer Median: 55

Receivables are growing faster than revenue.
```

This creates analytical storytelling rather than a spreadsheet dump.

---

# 70. Recommended Charts

Minimum chart library:

```text
1. Asset Composition — stacked area/bar

2. Funding Composition — stacked area/bar

3. Cash vs Debt — line/bar

4. Receivables vs Revenue Growth — dual trend

5. Inventory vs Revenue Growth — dual trend

6. DSO / DIO / DPO — multi-line

7. CCC — line

8. Debt / EBITDA — line

9. Interest Coverage — line

10. ROCE Decomposition — driver tree

11. Net Worth — line

12. Working Capital / Revenue — line

13. Debt Maturity — bar
```

---

# 71. Screener Filters

Add Balance Sheet filters:

```text
Debt/Equity < X
Net Debt/EBITDA < X
Current Ratio > X
Quick Ratio > X
DSO < X
Inventory Days < X
CCC < X
ROCE > X
Cash/Assets > X
Working Capital/Revenue < X
Debt Growth < X
Receivables Growth < Revenue Growth
Inventory Growth < Revenue Growth
```

---

# 72. Balance Sheet Transformation Screeners

## Deleveraging

Framework example:

```text
Debt_Today < Debt_3Y_Ago
AND
ROCE_Today > ROCE_1Y_Ago
```

Add:

```text
Net Debt Today < Net Debt 3Y Ago
```

---

## Working Capital Improvement

```text
CCC_Today < CCC_3Y_Ago
AND
CFO_3Y_Avg > 0
```

---

## Capital Expansion

```text
Gross_Block_Today
>
1.5 × Gross_Block_1Y_Ago
```

Then investigate:

```text
ROCE
Revenue
CFO
Utilization
```

---

# 73. Data Quality Dashboard

Create a dedicated internal developer dashboard:

```text
BALANCE SHEET DATA QUALITY

Accounting Integrity       99.8%
Core Line Coverage         97%
Ratio Calculability        91%
Aging Coverage             42%
Debt Maturity Coverage     61%
Related Party Coverage     73%
```

Then:

```text
TOP SOURCE GAPS

1. AR Aging
2. Inventory Aging
3. Debt Maturity
4. Credit Purchases
5. Related-Party Loan Detail
```

This tells the engineering team exactly where to improve the data layer.

---

# 74. Implementation Stages

## Stage 1 — Existing-System Audit

Do not immediately build new sources.

Run the existing data through the Balance Sheet metric registry.

Output:

```text
AVAILABLE
CALCULABLE
PARTIAL
MISSING
```

---

## Stage 2 — Core Balance Sheet Data

Ensure availability of:

```text
Total Assets
Current Assets
Cash
Receivables
Inventory
PPE
CWIP
Investments
Current Liabilities
Payables
Short-Term Debt
Long-Term Debt
Equity
Reserves
```

---

## Stage 3 — Core Ratios

Implement:

```text
Current Ratio
Quick Ratio
Cash Ratio
D/E
Debt/Assets
Debt/Capital
Net Debt/Equity
Net Debt/EBITDA
```

---

## Stage 4 — Working Capital

Implement:

```text
DSO
DIO
DPO
CCC
```

and dependency auditing.

---

## Stage 5 — Deep Balance Sheet Data

Add:

```text
AR Aging
Inventory Aging
AP Aging
Debt Maturity
ICDs
Related Party Loans
Contingent Liabilities
Deferred Revenue
Accrued Expenses
CWIP
Lease Liabilities
```

---

## Stage 6 — Capital Efficiency

Implement:

```text
ROCE
Capital Employed
Capital Turnover
Fixed Asset Turnover
```

and DuPont decomposition.

---

## Stage 7 — Risk Engine

Implement:

```text
Accounting integrity
Liquidity
Receivables
Inventory
Payables
Debt
Maturity
Related parties
Contingent liabilities
Capex
Cash conversion
```

---

## Stage 8 — Archetype Classifier

Implement:

```text
Strong
Weak
Middle
Transforming
```

using configurable rules.

---

## Stage 9 — Historical Transformation

Add:

```text
3Y
5Y
7Y
10Y
```

and identify structural changes.

---

## Stage 10 — Peer Analysis

Add sector-compatible:

```text
Peer Median
Peer Average
Percentile
```

---

## Stage 11 — UI

Build the Balance Sheet dashboard.

---

## Stage 12 — PDF

Build the dedicated Balance Sheet report.

---

# 75. Definition of Done

```text
[ ] Balance Sheet master data model
[ ] Accounting equation validator
[ ] Common-size analysis
[ ] Sources vs Applications visualization
[ ] Cash analysis
[ ] Receivables analysis
[ ] AR aging
[ ] DSO
[ ] Inventory analysis
[ ] Inventory turnover
[ ] Inventory days
[ ] Inventory aging
[ ] Payables analysis
[ ] AP aging
[ ] DPO
[ ] Accrued expenses
[ ] Deferred revenue
[ ] PPE analysis
[ ] CWIP analysis
[ ] Capex linkage
[ ] Investment analysis
[ ] Related-party loans / ICD
[ ] Contingent liabilities
[ ] Debt structure
[ ] Debt maturity
[ ] Equity / Net Worth
[ ] Working Capital
[ ] CCC
[ ] Current Ratio
[ ] Quick Ratio
[ ] Cash Ratio
[ ] Debt/Equity
[ ] Debt/Assets
[ ] Debt/Capital
[ ] Net Debt/Equity
[ ] Net Debt/EBITDA
[ ] Interest Coverage
[ ] ROCE
[ ] Capital Turnover
[ ] DuPont ROCE
[ ] Historical trends
[ ] Peer analysis
[ ] Risk engine
[ ] Four archetype classifier
[ ] Transformation detection
[ ] Ratio dependency graph
[ ] Coverage audit
[ ] Source-gap report
[ ] Data lineage
[ ] Confidence scoring
[ ] UI dashboard
[ ] PDF report
```

---

# 76. Final Balance Sheet Analysis Output

The finished Balance Sheet engine should produce this analytical flow:

```text
BALANCE SHEET
      ↓
IS IT BALANCED?
      ↓
WHAT DOES THE COMPANY OWN?
      ↓
HOW IS IT FUNDED?
      ↓
HOW LIQUID IS IT?
      ↓
HOW MUCH CAPITAL IS TRAPPED IN
AR / INVENTORY?
      ↓
HOW MUCH SUPPLIER FINANCING EXISTS?
      ↓
HOW MUCH DEBT EXISTS?
      ↓
WHEN DOES THAT DEBT MATURE?
      ↓
IS NET WORTH GROWING?
      ↓
IS CAPITAL BEING DEPLOYED PRODUCTIVELY?
      ↓
IS ROCE IMPROVING?
      ↓
WHY IS ROCE CHANGING?
      ↓
IS THE BALANCE SHEET STRENGTHENING
OR DETERIORATING?
      ↓
WHAT RED FLAGS ARE PRESENT?
      ↓
WHICH DATA IS MISSING?
      ↓
WHAT REQUIRES FURTHER INVESTIGATION?
```

---

# 77. Most Important Engineering Principle

Do not build this as a collection of Balance Sheet ratios.

Build it as a **Balance Sheet Intelligence Engine**:

```text
LINE ITEMS
    ↓
STRUCTURE
    ↓
LIQUIDITY
    ↓
WORKING CAPITAL
    ↓
LEVERAGE
    ↓
CAPITAL DEPLOYMENT
    ↓
RETURNS
    ↓
HISTORICAL TRANSFORMATION
    ↓
RISK SIGNALS
    ↓
DATA CONFIDENCE
    ↓
ANALYTICAL NARRATIVE
```

The CFO framework's central philosophy is to examine individual Balance Sheet lines and identify the operational/financial risks associated with them. fileciteturn4file1L9-L21

The SOIC Balance Sheet framework complements this with the four archetypes, tri-statement connectivity, ROCE decomposition, CCC, screening logic and forensic red flags. fileciteturn4file0L6-L38

The result should therefore be a dedicated **Balance Sheet Analysis module**, not another generic ratio page.
