# Financial Services — Fundamental Analysis Framework

> **Report-value extraction:** when fetching values from NSE/BSE annual or
> quarterly reports for this sector (notes-to-accounts, KPI tables, segment
> disclosures), always work through the two dedicated extraction engines
> first — [`Annual_Report_Fetching_Extraction_Engine.md`](../Annual_Report_Fetching_Extraction_Engine.md)
> and [`Quarterly_Report_Fetching_Extraction_Engine.md`](../Quarterly_Report_Fetching_Extraction_Engine.md) —
> rather than building one-off extraction logic. Check their Area
> Registries (`backend/app/ingestion/annual_report_ingestion.py` and
> `backend/app/ingestion/quarterly_results_client.py`) for an existing
> area before adding a new one.

**Version:** 2.0  
**Primary Market:** India  
**Macro Sector:** Financial Services  
**Sector:** Financial Services  

## Industries in this sector

```text
Financial Services
└── Financial Services
    ├── Finance
    ├── Capital Markets
    ├── Insurance
    ├── Banks
    └── Financial Technology (Fintech)
```

> This is a standalone sector-value framework covering every industry classified under **Financial Services → Financial Services**. The framework keeps industry-specific economics separate rather than applying one generic financial-ratio model to every company.

---

# 1. OBJECTIVE

Analyse a financial-services company through:

1. Business model
2. Revenue / income engine
3. Customer and asset growth
4. Unit economics
5. Risk-adjusted earnings
6. Asset quality where relevant
7. Capital requirements
8. Liquidity
9. Cash generation where meaningful
10. Operating leverage
11. Competitive advantage
12. Management and capital allocation
13. Governance
14. Regulatory risk
15. Peer position
16. Historical valuation
17. Valuation
18. Data confidence

The engine MUST NOT use generic manufacturing metrics across financial businesses.

The core analytical principle is:

```text
BUSINESS MODEL
      ↓
CUSTOMER / AUM / LOAN / VOLUME GROWTH
      ↓
MONETIZATION
      ↓
OPERATING COST
      ↓
RISK / CREDIT / CLAIMS COST
      ↓
PROFITABILITY
      ↓
CAPITAL EFFICIENCY
      ↓
BALANCE SHEET / CAPITAL
      ↓
VALUATION
```

---

# 2. INDUSTRY CLASSIFICATION

Every company must first be classified into:

```text
Finance
Capital Markets
Insurance
Banks
Financial Technology (Fintech)
```

A company may have multiple business models internally, but the engine must identify the primary economic engine.

## 2.1 Finance

Potential models:

- NBFC
- Housing finance
- Consumer finance
- Vehicle finance
- SME finance
- Microfinance
- Gold finance
- Infrastructure finance
- Corporate lending
- Leasing
- Factoring
- Specialized finance

Core chain:

```text
AUM
↓
Yield
↓
Cost of Funds
↓
Spread
↓
Credit Cost
↓
Opex
↓
ROA
↓
ROE
```

## 2.2 Capital Markets

Potential models:

- Brokerage
- Exchange
- Depository
- Investment banking
- Wealth management
- Asset management
- Portfolio management
- Stock broking
- Market infrastructure

Core chain:

```text
Market Activity
↓
Trading / Client Activity
↓
Volume
↓
Take Rate
↓
Revenue
↓
Operating Leverage
↓
PAT
```

## 2.3 Insurance

Potential models:

- Life insurance
- General insurance
- Health insurance
- Reinsurance
- Insurance distribution

Core chain:

```text
Premium
↓
Claims
↓
Expenses
↓
Underwriting Result
+
Investment Income
↓
Profitability
```

## 2.4 Banks

Classify where possible:

- Universal bank
- Private bank
- Public-sector bank
- Small finance bank
- Regional bank
- Foreign bank / subsidiary where relevant

Core chain:

```text
Deposits
↓
Loans
↓
Yield
↓
NIM
↓
Pre-Provision Profit
↓
Credit Cost
↓
PAT
↓
ROA / ROE
```

## 2.5 Financial Technology (Fintech)

Potential models:

- Payments
- Digital lending
- Wealthtech
- Insurtech
- Broking technology
- Financial marketplaces
- Payment infrastructure
- Financial SaaS
- Embedded finance

Core chain:

```text
Users
↓
Transactions / TPV
↓
Take Rate
↓
Revenue
↓
Contribution Margin
↓
Operating Leverage
↓
FCF / PAT
```

---

# 3. DATA PERIODS

Maintain:

### Annual

- Current FY
- 3Y history
- 5Y history
- 10Y history where available

### Quarterly

- Latest quarter
- Previous quarter
- YoY quarter
- 8-quarter history
- 12-quarter history where available

### TTM

```text
TTM = latest four reported quarters
```

Use TTM for current profitability and valuation where appropriate.

---

# 4. BUSINESS QUALITY

Capture:

- Primary business
- Revenue model
- Customer type
- Geography
- Product mix
- Distribution model
- Regulatory licence
- Technology dependence
- Recurring vs market-linked income
- Secured vs unsecured exposure
- Asset-light vs balance-sheet-intensive model

Calculate:

```text
Recurring_Revenue_%
Market_Linked_Revenue_%
Top_Product_Concentration
Top_Geography_Concentration
Top_Customer_Concentration
```

---

# 5. BANKING FRAMEWORK

## 5.1 Deposits

Track:

- Deposit growth
- CASA
- CASA ratio
- Retail deposits
- Bulk deposits
- Deposit cost
- Average deposits
- Deposit mix

Core questions:

```text
Are deposits growing?
Is the funding mix improving?
Is cost of deposits rising?
Is deposit growth keeping pace with loan growth?
```

## 5.2 Loans

Track:

- Loan growth
- Retail loans
- Corporate loans
- SME
- Agriculture
- Housing
- Vehicle
- Unsecured
- Credit card
- Personal loans
- Sectoral concentration

Calculate:

```text
Loan_Growth
Credit_Deposit_Ratio
Retail_Loan_%
Unsecured_Loan_%
```

## 5.3 NIM

Track:

- NII
- NIM
- Yield on advances
- Cost of deposits
- Cost of funds
- Spread

Core chain:

```text
Loan Yield
-
Funding Cost
=
Spread
```

Do not interpret NIM without understanding the funding and asset mix.

## 5.4 Asset Quality

Track:

- GNPA
- NNPA
- Slippage
- Net slippage
- Provision coverage ratio
- Credit cost
- Write-offs
- Restructured loans
- SMA / stressed assets where available

Core chain:

```text
Loan Growth
↓
Slippages
↓
GNPA / NNPA
↓
Provisioning
↓
Credit Cost
↓
PAT
```

## 5.5 Capital

Track:

- CET1
- CRAR
- Tier 1
- Capital adequacy
- Risk-weighted assets
- Capital raise
- Dilution

Calculate:

```text
CET1_Buffer
Capital_Requirement
Loan_Growth_vs_Capital_Growth
```

## 5.6 Banking Profitability

Track:

- NII growth
- PPOP
- Other income
- Operating expenses
- Cost-to-income
- Credit cost
- ROA
- ROE

Analyse:

```text
ROA = Operating Profit after Risk Costs / Average Assets
```

and:

```text
ROE = Profit / Average Equity
```

Do not attribute high ROE to business quality without checking leverage and credit cost.

---

# 6. FINANCE / NBFC FRAMEWORK

Track:

- AUM
- Disbursements
- Loan growth
- Yield
- Cost of funds
- Spread
- NIM
- Credit cost
- Opex / AUM
- ROA
- ROE
- GNPA
- NNPA
- Provision coverage
- Stage 2 / Stage 3 assets where applicable
- Collection efficiency
- Write-offs

Core equation:

```text
AUM Growth =
Existing Portfolio Growth
+
New Disbursements
-
Runoff
```

Unit economics:

```text
Yield
-
Cost of Funds
=
Spread
-
Credit Cost
-
Opex
=
Pre-tax Economic Return
```

Separate secured and unsecured lending.

---

# 7. CAPITAL MARKETS FRAMEWORK

Track:

- Market share
- Trading volume
- Active clients
- New clients
- Demat accounts
- Orders
- AUM
- Brokerage
- Revenue/client
- Revenue/order
- Take rate
- Subscription revenue
- Investment-banking revenue
- Wealth-management revenue
- Market-linked revenue
- Recurring revenue

Core equation:

```text
Revenue =
Client Activity
×
Volume
×
Take Rate
```

Stress-test:

```text
Market Volume -20%
Market Volume -30%
Market Volume -40%
```

Then assess revenue, EBITDA and PAT sensitivity.

---

# 8. ASSET MANAGEMENT FRAMEWORK

Track:

- Total AUM
- Equity AUM
- Debt AUM
- Passive AUM
- Active AUM
- SIP AUM
- Net inflows
- Gross inflows
- Outflows
- Market movement
- Yield on AUM
- Expense ratio
- Distribution cost
- Operating margin

Separate:

```text
Market-driven AUM Growth
vs
Net-flow-driven AUM Growth
```

Core chain:

```text
AUM
↓
Yield on AUM
↓
Revenue
↓
Operating Margin
↓
PAT
↓
ROE
```

---

# 9. INSURANCE FRAMEWORK

Track:

- GWP
- NWP
- New business premium
- Renewal premium
- Policies
- Premium/customer
- Claims
- Loss ratio
- Expense ratio
- Combined ratio
- VNB
- VNB margin
- Persistency
- Solvency
- Investment income

## 9.1 General Insurance

Core metric:

```text
Combined Ratio =
Loss Ratio + Expense Ratio
```

Analyse:

```text
Premium
→ Claims
→ Expenses
→ Underwriting Profit/Loss
→ Investment Income
```

## 9.2 Life Insurance

Track:

- APE
- VNB
- VNB margin
- Persistency
- Product mix
- Protection share
- ULIP share
- Savings share
- Distribution channel
- Embedded value
- Solvency

Separate growth from profitability.

High premium growth does not automatically mean high economic value creation.

---

# 10. FINTECH FRAMEWORK

Track:

- Active users
- Registered users
- Transactions
- TPV
- Take rate
- Revenue
- Revenue/user
- Merchant count
- AUM
- Lending
- Credit losses
- CAC
- LTV
- Contribution margin
- EBITDA
- FCF

Core chain:

```text
Users
↓
Activity
↓
TPV / Transactions
↓
Monetization
↓
Contribution
↓
Operating Costs
↓
FCF
```

Calculate:

```text
Revenue_per_User
Revenue_per_Transaction
TPV_Monetization
CAC
LTV
LTV_to_CAC
Contribution_per_User
```

A high-growth fintech should not be evaluated using revenue CAGR alone.

---

# 11. UNIT ECONOMICS

## Lending

```text
Yield
Cost of Funds
Spread
Credit Cost
Opex / AUM
ROA
ROE
```

## Insurance

```text
Premium / Customer
Claims Ratio
Expense Ratio
Combined Ratio
VNB / Customer
```

## Brokerage

```text
Revenue / Client
Revenue / Order
Take Rate
CAC
```

## Asset Management

```text
Revenue / AUM
Yield on AUM
Cost / AUM
```

## Fintech

```text
Revenue / User
Contribution / User
CAC
LTV
TPV Monetization
```

---

# 12. GROWTH ANALYSIS

Decompose growth into:

- Customer growth
- Loan growth
- AUM growth
- Disbursement growth
- Trading-volume growth
- Market-share gains
- Premium growth
- New business
- Net inflows
- TPV growth
- Take-rate changes
- Pricing
- Acquisitions

Core equations:

```text
Lending:
AUM Growth = Portfolio Growth + New Disbursement - Runoff

Capital Markets:
Revenue Growth = Volume + Take Rate + Client Growth + Mix

Insurance:
Premium Growth = New Business + Renewals + Price/Mix

Fintech:
Revenue Growth = Users + Activity + Monetization
```

---

# 13. RISK-ADJUSTED EARNINGS

Financial services must be analysed through risk-adjusted earnings.

Track:

- Credit risk
- Liquidity risk
- Interest-rate risk
- Market risk
- Insurance underwriting risk
- Concentration risk
- Operational risk
- Regulatory risk
- Technology / cyber risk

For lenders:

```text
Gross Growth
-
Credit Losses
=
Risk-Adjusted Growth
```

For insurers:

```text
Premium Growth
+
Investment Income
-
Claims
-
Expenses
=
Economic Earnings
```

For capital markets:

```text
Revenue Growth
-
Market Cycle Dependency
=
Recurring Earnings Quality
```

---

# 14. CONCENTRATION ANALYSIS

Track:

- Borrower concentration
- Sector concentration
- Geography
- Product
- Customer
- Depositor
- Insurance product
- Distribution channel
- Revenue source
- Market segment

Calculate:

```text
Top_5_Exposure
Top_Product_%
Top_Geography_%
Top_Customer_%
```

High concentration should trigger deeper analysis rather than an automatic pass/fail.

---

# 15. OPERATING EFFICIENCY

Track:

### Banks / Finance

- Cost-to-income
- Opex/AUM
- Branch productivity
- Employee productivity
- Cost per account

### Capital Markets

- Revenue/client
- Revenue/employee
- Cost/revenue
- Operating leverage

### Insurance

- Expense ratio
- Premium/employee
- Distribution cost

### Fintech

- CAC
- Revenue/user
- Contribution/user
- Employee cost/revenue

---

# 16. CASH FLOW AND FUNDING

Cash-flow analysis must be industry-specific.

## Banks / NBFCs

Do not use manufacturing-style CFO/PAT interpretation mechanically.

Focus on:

- Funding sources
- Borrowings
- Deposits
- Securitisation
- Collections
- Disbursements
- Liquidity
- ALM
- Capital adequacy

## Capital Markets / Asset Management

Focus on:

- Operating cash flow
- Fee income
- Recurring vs market-linked revenue
- FCF
- Capital requirements

## Insurance

Focus on:

- Premium collections
- Claims payments
- Investment cash flows
- Operating cash flows
- Capital requirements

## Fintech

Focus strongly on:

- CFO
- FCF
- Contribution margin
- Cash burn
- Working capital
- Funding requirement

---

# 17. BALANCE SHEET

Track industry-specific balance-sheet strength.

### Banks

- Deposits
- Loans
- Investments
- GNPA
- NNPA
- Provisions
- Capital
- CET1
- CRAR

### NBFCs

- AUM
- Borrowings
- Cash
- Liquidity
- Net worth
- Asset quality
- ALM

### Insurance

- Investments
- Reserves
- Policy liabilities
- Solvency
- Embedded value

### Capital Markets

- Cash
- Investments
- Client-related liabilities
- Capital employed

### Fintech

- Cash
- Debt
- Equity
- Restricted cash
- Working capital
- Funding runway

---

# 18. CAPITAL EFFICIENCY

Track:

- ROA
- ROE
- ROIC where meaningful
- ROTE where meaningful
- Incremental ROE
- Incremental ROA

For banks and lenders:

```text
ROE = ROA × Financial Leverage
```

Analyse whether high ROE comes from:

- Strong operating economics
- High leverage
- Low provisions
- Temporary income
- Low capital allocation requirements

For asset-light businesses, emphasize incremental ROIC/ROE and FCF.

---

# 19. MANAGEMENT & CAPITAL ALLOCATION

Track:

- Dividend
- Buybacks
- Equity issuance
- Acquisitions
- Branch expansion
- Technology investment
- Provisioning policy
- Risk appetite
- Capital raising
- Capital deployment
- Subsidiary investments

Evaluate:

- Growth discipline
- Underwriting discipline
- Capital allocation
- Provision conservatism
- Regulatory compliance
- Dilution discipline

---

# 20. CONCALL & GUIDANCE INTELLIGENCE

Extract:

- Credit growth guidance
- Deposit growth
- NIM outlook
- Credit-cost outlook
- Asset-quality outlook
- AUM growth
- Disbursement guidance
- VNB growth
- Margin guidance
- Market-share objectives
- Capex / technology investment
- Capital requirements
- User / TPV targets for fintech

Store:

```text
Guidance
→ Actual
→ Variance
→ Management Explanation
```

Calculate:

```text
Guidance_Accuracy
Guidance_Raise_Count
Guidance_Cut_Count
Execution_vs_Guidance
```

Do not treat management guidance as reported data.

---

# 21. GOVERNANCE

Track:

- Promoter holding
- Promoter pledge
- Promoter transactions
- Related parties
- Auditor changes
- Regulatory actions
- RBI actions
- SEBI actions
- IRDAI actions where relevant
- Management remuneration
- Capital raising
- Dilution
- Subsidiary transactions

For lenders specifically investigate:

- Underwriting discipline
- Related-party exposure
- Evergreening indicators
- Restructuring
- Write-off policy
- Collection practices

---

# 22. COMPETITIVE ADVANTAGE

Assess:

- Low-cost funding
- Distribution
- Branch network
- Customer acquisition
- Brand
- Data advantage
- Technology
- Underwriting capability
- Cost of funds
- Scale
- Switching costs
- Network effects
- Regulatory licences
- Market infrastructure

Differentiate:

```text
Structural Advantage
vs
Temporary Scale Benefit
```

---

# 23. PEER COMPARISON

Select peers by business model.

## Banks

Compare:

- Loan growth
- Deposit growth
- NIM
- CASA
- GNPA
- NNPA
- PCR
- Credit cost
- ROA
- ROE
- CET1
- P/B

## Finance / NBFC

Compare:

- AUM growth
- Yield
- Cost of funds
- Spread
- Credit cost
- Opex/AUM
- ROA
- ROE
- Asset quality
- P/B
- P/E

## Insurance

Compare:

- Premium growth
- VNB
- VNB margin
- Persistency
- Combined ratio
- Solvency
- P/EV

## Capital Markets

Compare:

- Active clients
- Market share
- Revenue/client
- AUM
- Take rate
- Operating margin
- FCF

## Fintech

Compare:

- Users
- TPV
- Take rate
- Revenue/user
- CAC
- LTV
- Contribution margin
- FCF

Use peer median and percentile where sufficient data exists.

---

# 24. VALUATION FRAMEWORK

Valuation must be industry-specific.

## Banks

Primary:

- P/B
- P/E
- ROE-adjusted P/B
- Historical P/B
- Peer P/B

Core relationship:

```text
Current P/B
vs
Historical P/B
vs
Peer P/B
vs
Sustainable ROE
```

Do not hard-code a universal P/B threshold.

## Finance / NBFC

Use:

- P/B
- P/E
- ROE-adjusted P/B
- EV/EBITDA only where meaningful

## Insurance

Use:

- P/EV
- P/B
- P/E
- VNB-based approaches

## Capital Markets

Use:

- P/E
- EV/EBITDA where meaningful
- P/AUM
- FCF yield

## Fintech

Use:

- P/S
- EV/Sales
- P/E when profitable
- FCF yield
- Unit-economics-based valuation

Avoid valuation based solely on revenue growth.

---

# 25. HISTORICAL VALUATION

Track:

- Current P/E
- Historical P/E
- Current P/B
- Historical P/B
- Current P/EV
- Historical P/EV
- Current EV/EBITDA
- Historical EV/EBITDA
- FCF yield

Compare valuation with:

```text
Growth
Profitability
ROE / ROIC
Risk
Asset Quality
Cash Generation
Capital Requirements
Business Quality
```

---

# 26. POSITIVE SIGNALS

Potential positive signals:

- Sustainable customer growth
- Market-share gains
- Strong asset growth with controlled risk
- Stable/improving NIM or spreads
- Improving asset quality
- Controlled credit costs
- Strong capital adequacy
- High-quality deposits / funding
- Strong VNB growth
- Improving persistency
- Rising AUM with net inflows
- Strong recurring revenue
- Improving fintech unit economics
- High FCF conversion
- Strong ROE / ROIC
- Disciplined capital allocation

All signals must be evidence-based.

---

# 27. RED FLAGS

High-priority investigation flags:

### Lending

- Rapid unsecured growth
- GNPA increase
- NNPA increase
- Slippage increase
- Credit-cost spike
- Falling PCR
- Weak collection efficiency
- Asset-liability mismatch
- Excessive leverage

### Insurance

- Combined ratio deterioration
- Persistency deterioration
- Solvency deterioration
- Aggressive product mix
- Weak VNB margin

### Capital Markets

- Revenue heavily dependent on market volumes
- Client concentration
- Falling market share
- Take-rate compression
- High operating-cost growth

### Fintech

- User growth without monetization
- TPV growth without revenue growth
- CAC rising faster than LTV
- Negative contribution margin
- Persistent cash burn
- Repeated equity dilution
- Credit losses rising rapidly

### Governance

- Promoter pledge
- Persistent promoter selling
- Auditor resignation
- Qualified audit
- Regulatory enforcement
- Large related-party transactions
- Excessive dilution
- Complex unexplained subsidiaries

---

# 28. CAUSAL ANALYSIS ENGINE

The system must answer **why** the metric changed.

## If revenue increased

Determine whether growth came from:

```text
Customers
+
AUM / Loans
+
Trading Volume
+
Premium
+
Pricing
+
Take Rate
+
Market Share
+
Acquisition
```

## If margins increased

Determine whether:

```text
Operating Leverage
+
Pricing
+
Mix
+
Lower Funding Cost
+
Lower Credit Cost
+
Lower Claims
+
Lower CAC
```

caused the improvement.

## If PAT increased

Separate:

```text
Core Operating Growth
+
Lower Risk Cost
+
Other Income
+
Treasury / Market Gains
+
Tax Changes
+
One-off Items
```

## If ROE increased

Determine whether it came from:

```text
ROA ↑
+
Leverage ↑
+
Capital Reduction
+
Lower Credit Cost
+
Temporary Income
```

---

# 29. SCENARIO ANALYSIS

Produce:

## Bull Case

Potential combination:

```text
Customer Growth ↑
AUM / Volume ↑
Monetization Stable/↑
Risk Costs Controlled
Operating Leverage ↑
ROE / ROIC ↑
```

## Base Case

```text
Moderate Growth
Stable Monetization
Normal Risk Costs
Stable Capital Requirements
```

## Bear Case

Potential combination:

```text
Growth ↓
Funding Cost ↑
Credit Cost ↑
Claims ↑
Market Volumes ↓
Take Rate ↓
CAC ↑
Capital Requirement ↑
```

Scenarios must expose assumptions rather than rely on unsupported forecasts.

---

# 30. SCORING ARCHITECTURE

Maintain separate dimensions:

```text
Business Quality
Growth Quality
Operating Quality
Risk Quality
Financial Quality
Capital Efficiency
Competitive Advantage
Management / Governance
Valuation
Data Confidence
```

Weights should be configurable by industry.

### Suggested starting weights

| Dimension | Banks | Finance/NBFC | Insurance | Capital Markets | Fintech |
|---|---:|---:|---:|---:|---:|
| Business Quality | 10% | 10% | 10% | 10% | 10% |
| Growth Quality | 15% | 15% | 15% | 15% | 15% |
| Operating Quality | 10% | 10% | 10% | 15% | 15% |
| Risk Quality | 20% | 20% | 20% | 10% | 15% |
| Financial Quality | 15% | 15% | 15% | 15% | 15% |
| Capital Efficiency | 10% | 10% | 10% | 10% | 10% |
| Competitive Advantage | 5% | 5% | 5% | 5% | 5% |
| Management / Governance | 5% | 5% | 5% | 5% | 5% |
| Valuation | 10% | 10% | 10% | 15% | 10% |

These are starting parameters, not immutable rules.

Do not allow one ratio to dominate the entire analysis.

---

# 31. DATA QUALITY

Every metric must contain:

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

Allowed data types:

```text
REPORTED
CALCULATED
ESTIMATED
MANAGEMENT-DISCLOSED
THIRD-PARTY
```

Confidence:

```text
HIGH
MEDIUM
LOW
```

Never silently mix reported, calculated and estimated values.

---

# 32. SOURCE HIERARCHY

Preferred source order:

1. Annual Report
2. Quarterly Results
3. Investor Presentation
4. Earnings / Concall Transcript
5. Company filings
6. NSE / BSE filings
7. RBI for banking / lending data
8. IRDAI for insurance data
9. SEBI for regulatory / capital-market information
10. Company investor-relations website
11. Reliable financial databases
12. Third-party research

For critical metrics, prioritize primary disclosures.

If sources conflict:

```text
Identify discrepancy
↓
Prefer primary source
↓
Record both where material
↓
Do not silently overwrite
```

---

# 33. AGENT ARCHITECTURE

```text
Company Identification Agent
        ↓
Industry Classification Agent
        ↓
Financial Data Agent
        ↓
Industry KPI Agent
        ↓
Business Quality Agent
        ↓
Growth Agent
        ↓
Risk / Asset Quality Agent
        ↓
Working Capital / Funding Agent
        ↓
Cash Flow Agent
        ↓
Capital Efficiency Agent
        ↓
Management / Concall Agent
        ↓
Governance Agent
        ↓
Competitive Advantage Agent
        ↓
Peer Comparison Agent
        ↓
Historical Valuation Agent
        ↓
Valuation Agent
        ↓
Causal Analysis Agent
        ↓
Red Flag Agent
        ↓
Scoring Agent
        ↓
Final Fundamental Analysis
```

The **Industry KPI Agent** must dynamically select the correct metrics:

```text
Bank → NIM / GNPA / NNPA / CASA / CET1
NBFC → AUM / Yield / CoF / Spread / Credit Cost
Insurance → GWP / VNB / Persistency / Combined Ratio / Solvency
Capital Markets → Clients / Volume / Take Rate / AUM
Fintech → Users / TPV / Take Rate / CAC / LTV
```

---

# 34. DATABASE STRUCTURE

## Company

```text
company_id
company_name
macro_sector
sector
industry
business_model
market_cap
```

## Financial Metrics

```text
company_id
metric_name
value
period
unit
source
data_type
confidence
```

## Industry Metrics

```text
company_id
industry
metric_name
value
period
unit
source
confidence
```

## Banking Metrics

```text
company_id
deposits
loan_book
casa
nim
gnpa
nnpa
pcr
credit_cost
roa
roe
cet1
crar
```

## Finance / NBFC Metrics

```text
company_id
aum
disbursement
yield
cost_of_funds
spread
credit_cost
gnpa
nnpa
roa
roe
```

## Insurance Metrics

```text
company_id
gwp
nwp
ape
vnb
vnb_margin
persistency
loss_ratio
expense_ratio
combined_ratio
solvency
```

## Capital Markets Metrics

```text
company_id
active_clients
market_share
volume
aum
revenue_per_client
take_rate
subscription_revenue
fcf
```

## Fintech Metrics

```text
company_id
active_users
transactions
tpv
take_rate
revenue_per_user
cac
ltv
contribution_margin
fcf
```

## Guidance

```text
company_id
date
metric
guidance
period
actual
variance
explanation
```

## Valuation

```text
company_id
date
valuation_metric
value
historical_percentile
peer_percentile
```

## Red Flags

```text
company_id
date
flag_type
severity
evidence
source
```

---

# 35. FINAL SCREENER OUTPUT

```text
Company:
Macro Sector: Financial Services
Sector: Financial Services
Industry:
Business Model:

BUSINESS QUALITY             XX/100
GROWTH QUALITY               XX/100
OPERATING QUALITY            XX/100
RISK QUALITY                 XX/100
FINANCIAL QUALITY            XX/100
CAPITAL EFFICIENCY           XX/100
COMPETITIVE ADVANTAGE        XX/100
MANAGEMENT / GOVERNANCE      XX/100
VALUATION                    XX/100

DATA CONFIDENCE:

KEY POSITIVES
1.
2.
3.
4.
5.

KEY CONCERNS
1.
2.
3.
4.
5.

RED FLAGS
1.
2.
3.

INDUSTRY ENGINE
- Primary KPI:
- Growth:
- Monetization:
- Risk:
- Capital:

FINANCIAL ENGINE
- Revenue / Income:
- PAT:
- ROA:
- ROE:
- ROIC where meaningful:

RISK ENGINE
- Asset Quality / Claims / Market Risk:
- Risk Cost:
- Capital:

CASH / FUNDING ENGINE
- CFO / Funding:
- FCF where meaningful:
- Liquidity:
- Debt / Deposits:

MANAGEMENT / GUIDANCE
- Guidance:
- Actual:
- Variance:
- Guidance Accuracy:

VALUATION
- Primary Multiple:
- Historical Position:
- Peer Position:

INVESTMENT THESIS

BULL CASE

BASE CASE

BEAR CASE

WHAT WOULD BREAK THE THESIS

METRICS TO MONITOR NEXT QUARTER
```

---

# 36. IMPLEMENTATION PRINCIPLE

Do NOT build the Financial Services screener as:

```text
IF ROE > X
AND PE < Y
AND Growth > Z
THEN PASS
```

Instead:

```text
RAW DATA
   ↓
NORMALIZATION
   ↓
INDUSTRY CLASSIFICATION
   ↓
INDUSTRY-SPECIFIC KPIs
   ↓
TREND ANALYSIS
   ↓
RISK-ADJUSTED ANALYSIS
   ↓
PEER COMPARISON
   ↓
CAUSAL ANALYSIS
   ↓
RED FLAGS
   ↓
SCORING
   ↓
HISTORICAL VALUATION
   ↓
FINAL ANALYSIS
```

The engine's primary job is to explain:

> **What is driving the company's economics?**

> **Is growth creating risk-adjusted value or merely increasing reported size?**

> **Are profitability and capital efficiency sustainable?**

> **How does the company compare with relevant business-model peers?**

> **What does the current valuation assume about future earnings and risk?**

---

# 37. CORE FUNDAMENTAL QUESTION

For Financial Services, the central question is:

> **Can the company sustainably grow its customers, assets, transactions or premiums while maintaining strong unit economics, controlling risk, allocating capital efficiently and generating attractive returns on the capital required by its business model?**

The backbone is:

```text
CUSTOMERS / DEPOSITS / USERS
          ↓
LOANS / AUM / VOLUME / PREMIUM
          ↓
MONETIZATION
          ↓
OPERATING COST
          ↓
RISK COST
          ↓
PROFIT
          ↓
CAPITAL EFFICIENCY
          ↓
BALANCE SHEET / CAPITAL
          ↓
VALUATION
```
