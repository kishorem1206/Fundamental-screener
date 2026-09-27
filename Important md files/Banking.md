The mentor explicitly treats **P/B as particularly important for Banking/Leverage**, while also emphasizing historical valuation, ROE/operating efficiency, EPS/profit growth, promoter behaviour and margin of safety.  The Demo Class also uses HDFC vs Karnataka Bank specifically to illustrate quality versus valuation/margin of safety. 

## Sector 1 — Banking

I'm starting with **Banks**, rather than NBFCs, because the accounting/business model is sufficiently different that I would make **Banks and NBFCs separate sector engines**.

### 1. What I want your engine to fetch from Screener.in

For banks, I would divide the data into **Core Screener**, **Derived**, and **External Banking Data**.

| Category           | Screener value                       | Importance    |
| ------------------ | ------------------------------------ | ------------- |
| Size               | Market Capitalization                | High          |
| Valuation          | P/E                                  | High          |
| Valuation          | Price to Book Value                  | **Very High** |
| Valuation          | Book Value                           | High          |
| Profitability      | ROE                                  | **Very High** |
| Profitability      | Average ROE 5Y                       | **Very High** |
| Profitability      | Average ROE 7Y/10Y                   | High          |
| Profitability      | ROA                                  | **Very High** |
| Profitability      | Average ROA 3Y/5Y                    | **Very High** |
| Growth             | Profit Growth 3Y                     | High          |
| Growth             | Profit Growth 5Y                     | **Very High** |
| Growth             | Profit Growth 10Y                    | High          |
| Growth             | EPS Growth 3Y/5Y                     | High          |
| Growth             | Sales/Total Income Growth 3Y/5Y      | Medium        |
| Shareholder        | Promoter Holding                     | High          |
| Shareholder        | Pledged Percentage                   | **Very High** |
| Valuation history  | Current P/E vs historical/median P/E | High          |
| Valuation history  | Current P/B vs historical P/B        | **Very High** |
| Shareholder return | Dividend Yield                       | Medium        |
| Dilution           | Number of shares / share-count trend | High          |

The mentor's broader framework supports looking at **EPS as the bridge between business growth and price appreciation**, historical P/E rather than current P/E alone, and promoter selling/pledging as important warning signals.  

### Important: metrics I would NOT use as primary bank filters

For your engine, this is just as important as what we include.

**Do not use these as generic banking-quality filters:**

* Debt-to-equity
* Interest coverage
* OPM
* EBITDA
* EV/EBITDA
* Gross margin
* Inventory days
* Debtor days

Why? A bank's business is fundamentally different: deposits and borrowings are part of the funding model, while interest income/expense is core operating activity. Applying manufacturing-company ratios to banks can produce nonsense.

The mentor himself stresses that different businesses need different analytical treatment and that sector comparison is necessary to identify the best-in-class company. 

---

# 2. Banking-specific data that Screener does NOT adequately provide

This is where your engine becomes much more powerful than a normal Screener query.

For every bank, I would additionally fetch:

### Asset quality

1. **Gross NPA % / GNPA**
2. **Net NPA % / NNPA**
3. **Provision Coverage Ratio**
4. **Slippage Ratio**
5. **Net slippages**
6. **Credit cost**
7. **Write-offs**
8. **Restructured loans**
9. **Special Mention Accounts / SMA**, where available
10. **Stressed assets**

RBI itself publishes bank-level asset-quality information including GNPA, NNPA, provisioning, slippage and related ratios. ([Reserve Bank of India][1])

### Profitability

11. **Net Interest Income — NII**
12. **Net Interest Margin — NIM**
13. **ROA**
14. **ROE**
15. **Pre-provision operating profit — PPOP**
16. **Credit cost**
17. **Cost-to-income ratio**
18. **Fee income growth**
19. **Other income / total income**

### Loan/deposit franchise

20. **Advances/loan growth**
21. **Deposit growth**
22. **CASA ratio**
23. **CASA growth**
24. **Credit-deposit ratio**
25. **Retail loan percentage**
26. **Corporate/wholesale loan percentage**
27. **Unsecured loan exposure**
28. **Sectoral loan concentration**
29. **Geographical concentration**

RBI's banking datasets specifically cover deposits, credit, CASA, sectoral deployment, CRAR, asset quality and other bank-wise indicators. ([Reserve Bank of India][1])

### Capital strength

30. **CRAR / Capital Adequacy Ratio**
31. **CET1**
32. **Tier 1 capital**
33. **Leverage ratio**
34. **Capital buffer over regulatory requirement**

These are particularly important because a bank can show excellent ROE while still having a weak capital position.

---

# 3. Promoter / management integrity layer

This should **NOT be treated as one simple "promoter integrity score."**

I'd make your engine collect evidence.

### Positive signals

* Promoter holding stable/increasing
* Promoter buying
* No promoter pledge
* No unexplained dilution
* Consistent dividend policy
* Clean auditor history
* No major regulatory action
* No unexplained related-party transactions
* Management remuneration reasonable relative to business
* Consistent capital allocation
* No repeated equity fundraising despite adequate internal capital

### Red flags

* Promoter selling repeatedly
* Promoter pledge increasing
* Sudden promoter holding changes
* Large preferential allotments
* Repeated warrants
* Excessive dilution
* Auditor resignation
* Qualified audit opinion
* Material weakness in internal controls
* Large related-party transactions
* Loans to promoter/group entities
* Guarantees to related parties
* Frequent related-party restructuring
* Regulatory penalties
* Fraud / misrepresentation allegations
* Frequent management/director resignations
* Sudden CFO/auditor changes
* Large unexplained contingent liabilities

This fits very closely with the mentor's warning that persistent promoter selling can indicate financial stress and that shareholder alignment is a fundamental management-quality consideration.  

---

# 4. Free sources I would connect to your engine

This is where I'd build a **source hierarchy** rather than relying on Moneycontrol-type aggregators.

### Tier 1 — Official sources

**RBI — most important for banks**

Use it for:

* GNPA
* NNPA
* Slippage
* Provisioning
* CRAR
* CASA
* Deposits
* Credit
* Sectoral exposure
* Bank-wise statistics

RBI explicitly makes bank-wise asset-quality and capital data available through its statistical databases. ([Reserve Bank of India][1])

[RBI](https://www.rbi.org.in/?utm_source=chatgpt.com)

---

**NSE**

Use for:

* Shareholding
* Promoter holding
* Promoter changes
* Corporate announcements
* Pledge information
* Exchange filings

NSE provides downloadable shareholding-pattern data, including promoter/promoter-group holdings. ([NSE India][2])

[NSE Shareholding Patterns](https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern?utm_source=chatgpt.com)

NSE also has a dedicated pledged-data section containing promoter shares encumbered and pledge percentages. ([NSE India][3])

[NSE Pledged Data](https://www.nseindia.com/companies-listing/corporate-filings-pledged-data?utm_source=chatgpt.com)

---

**BSE**

Useful as a second exchange-level source for:

* Shareholding
* Promoter pledge
* Corporate announcements
* Board changes
* Auditor-related disclosures

BSE's shareholding data includes shares pledged/otherwise encumbered. ([BSE India][4])

[BSE](https://www.bseindia.com/?utm_source=chatgpt.com)

---

### Tier 2 — Corporate/regulatory integrity

**MCA**

Use it for:

* Company master data
* Directors
* Charges
* Annual returns
* Financial statements
* Corporate filings
* Related-party information where available
* Director/signatory history

MCA's public-document system provides access to company filings, although some documents require payment. ([Ministry of Corporate Affairs][5])

[MCA](https://www.mca.gov.in/?utm_source=chatgpt.com)

For your automated engine, I'd treat MCA as an **investigation source**, rather than the first source for every stock.

---

**SEBI**

Use it for:

* Enforcement orders
* Regulatory violations
* Insider trading cases
* Market manipulation
* Fraud-related orders
* Promoter/director actions

SEBI provides searchable enforcement orders by entity/name/keywords. ([Securities and Exchange Board of India][6])

[SEBI Enforcement Orders](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&smid=133&ssid=9&utm_source=chatgpt.com)

---

### Tier 3 — Free secondary sources

For easier automated extraction / cross-checking:

* Screener.in
* Moneycontrol
* Tijori Finance
* Trendlyne free pages
* Investing.com
* StockEdge free data
* Company investor-relations websites
* Annual reports
* Investor presentations

But for your **integrity engine**, I'd prioritize:

**Company filing → NSE/BSE → RBI → SEBI → MCA**

rather than trusting a secondary website's interpretation.

---

# 5. The actual Banking screener logic

I would initially make the engine **two-stage**.

### Stage A — Quantitative fundamental filter

A bank should roughly satisfy:

```text
Market Capitalization > 5000 Cr

AND Average ROE 5Years >= 12%

AND Average ROA 5Years >= 1%

AND Profit Growth 5Years >= 10%

AND Profit Growth 10Years >= 10%

AND Pledged Percentage <= 5%

AND Price to Book Value < sector/historical threshold

AND Price to Earning < historical/peer threshold
```

But **I would NOT permanently hard-code P/B < X** for all banks.

Instead:

```text
Current P/B
        ↓
Compare against
        ↓
Bank's own historical P/B
        +
Peer-group median P/B
        +
ROE quality
```

That's much closer to the mentor's "valuation gravity" philosophy: current valuation must be compared with the historical valuation the market has previously accepted. 

---

# 6. Stage B — Banking quality filter

This should be separate:

```text
GNPA              → low / improving
NNPA              → low / improving
Slippage          → stable / declining
PCR               → healthy / improving
Credit Cost       → controlled
ROA               → stable/high
ROE               → stable/high
NIM               → stable
CASA              → healthy
Deposit Growth    → healthy
Loan Growth       → healthy
CRAR              → strong
CET1              → strong
Credit/Deposit    → reasonable
Unsecured Exposure → controlled
Concentration Risk → controlled
```

This is **not just a filter**. These should become the bank's **fundamental analysis payload**.

For example:

```text
HDFC Bank

ROA:              1.8%
ROE:              15.2%
NIM:              3.6%
GNPA:             1.2%
NNPA:             0.3%
PCR:              75%
CASA:             38%
Loan Growth:      12%
Deposit Growth:   14%
CRAR:             18%
P/B:              2.1x
Historical P/B:   2.7x
```

Then your engine can say:

> **High-quality bank + currently below historical P/B + healthy asset quality**

rather than simply:

> P/B < 2 → PASS.

That's a much more intelligent screener.

---

# 7. Banking-specific red-flag score

I'd also create a separate score:

```text
BANK_INTEGRITY_SCORE

Promoter pledge              -20
Increasing promoter pledge   -15
Promoter selling             -10
Auditor resignation          -20
Qualified audit opinion      -25
SEBI regulatory action       -25
Major related-party concern  -20
Rapid unexplained dilution   -15
Rising GNPA                  -10
Rising NNPA                  -10
Rising slippage              -10
Falling PCR                  -10
Weakening CRAR               -15
Aggressive unsecured growth  -10
```

**Important:** these numbers are my proposed engine design, **not thresholds taught by your mentor**. The mentor's material establishes the importance of promoter behaviour, debt/dilution, margin of safety and financial integrity; the numerical scoring system is something we're designing for your engine. 

---

# 8. Proposed `.md` file

Given your finalized screener schema — **one operator + one value per rule, AND logic, metric-specific values, and standardized 3Y/5Y growth fields** — I'd structure the actual file like this:

```md
# Sector: Banking

## Overview

Banking companies must be evaluated differently from non-financial businesses.

Primary focus:
- Return on Assets
- Return on Equity
- Asset quality
- Capital adequacy
- Deposit/loan growth
- Net Interest Margin
- Provisioning
- Price-to-Book
- Historical valuation
- Promoter integrity

Do not use manufacturing-style metrics such as:
- Debt-to-Equity
- EBITDA
- EV/EBITDA
- OPM
- Inventory Days
- Debtor Days

---

## Screening Logic

All rules use AND logic.

### Size

- Market Capitalization > 5000

### Profitability

- Average Return on Equity 5Years >= 12
- Average Return on Assets 5Years >= 1

### Growth

- Profit Growth 3Years >= 8
- Profit Growth 5Years >= 10
- Profit Growth 10Years >= 10
- EPS Growth 5Years >= 10

### Ownership

- Pledged Percentage <= 5

### Valuation

- Price to Book Value < 4
- Price to Earning < 30

---

## Fundamental Metrics

### Core Screener Metrics

- Market Capitalization
- Price
- Price to Earning
- Price to Book Value
- Book Value
- ROE
- Average ROE 5Years
- Average ROE 7Years
- Average ROE 10Years
- ROA
- Average ROA 3Years
- Average ROA 5Years
- Profit Growth 3Years
- Profit Growth 5Years
- Profit Growth 10Years
- EPS Growth 3Years
- EPS Growth 5Years
- Promoter Holding
- Pledged Percentage
- Dividend Yield
- Number of Shares
- Share-count growth

### Banking-Specific External Metrics

- Gross NPA
- Net NPA
- GNPA Ratio
- NNPA Ratio
- Provision Coverage Ratio
- Slippage Ratio
- Credit Cost
- Net Interest Income
- Net Interest Margin
- Pre-Provision Operating Profit
- Cost-to-Income Ratio
- Deposit Growth
- Loan/Advance Growth
- CASA Ratio
- CASA Growth
- Credit-Deposit Ratio
- Retail Loan Mix
- Corporate Loan Mix
- Unsecured Loan Mix
- Sector Concentration
- Geographical Concentration
- CRAR
- CET1
- Tier 1 Capital
- Leverage Ratio
- Restructured Loans
- Write-offs

---

## Management & Integrity Analysis

### Positive Signals

- Stable/increasing promoter holding
- Zero/low promoter pledge
- Promoter buying
- No unexplained dilution
- Clean audit reports
- Stable auditor
- No major regulatory action
- Reasonable related-party transactions
- Sensible management remuneration
- Consistent capital allocation

### Red Flags

- Rising promoter pledge
- Persistent promoter selling
- Auditor resignation
- Qualified audit opinion
- Regulatory enforcement
- Insider trading/manipulation action
- Large unexplained related-party transactions
- Promoter/group-company loans
- Excessive dilution
- Repeated preferential issues
- Rapid deterioration in asset quality
- Rising GNPA/NNPA
- Rising slippages
- Falling provision coverage
- Weakening capital adequacy
- Aggressive unsecured lending

---

## External Data Sources

### Primary Sources

1. RBI
   - Asset quality
   - CRAR
   - Capital ratios
   - Deposits
   - Credit
   - CASA
   - Sectoral credit
   - Slippage
   - Provisioning

2. NSE
   - Shareholding pattern
   - Promoter holding
   - Promoter pledge
   - Corporate filings
   - Corporate announcements

3. BSE
   - Shareholding
   - Promoter pledge
   - Corporate announcements
   - Exchange filings

4. SEBI
   - Enforcement orders
   - Regulatory violations
   - Insider trading
   - Market manipulation

5. MCA
   - Company master data
   - Directors
   - Charges
   - Annual returns
   - Financial filings

6. Company Investor Relations
   - Annual reports
   - Investor presentations
   - Quarterly results
   - Management commentary

### Secondary Sources

- Screener
- Moneycontrol
- Tijori Finance
- Trendlyne
- StockEdge
- Investing.com

---

## Valuation Framework

Do not evaluate P/B or P/E in isolation.

Compare:

1. Current P/B vs historical P/B
2. Current P/E vs historical P/E
3. Current P/B vs banking peer median
4. ROE vs P/B
5. ROA vs P/B
6. Growth vs valuation
7. Asset quality vs valuation

A high-quality bank can justify a premium P/B.

A low P/B bank is not automatically cheap.

---

## Output

The screener should produce:

- Fundamental Quality Score
- Asset Quality Score
- Capital Strength Score
- Growth Score
- Management Integrity Score
- Valuation Score
- Overall Banking Score
- Red Flag List
- Data Confidence
- Historical Valuation Position
- Peer Position

The final output should explain WHY the bank passed,
not merely show that it passed.
```

### One change I strongly recommend

Don't make **"P/B < 4"** the final banking rule yet. That's only a first-pass numeric boundary. The better engine will eventually calculate something like:

**Fair P/B relative to sustainable ROE → current P/B → historical P/B → peer P/B → margin of safety.**

That will be much closer to what your mentor is actually teaching than blindly screening at a fixed P/B.

Also, the mentor's core philosophy says the company should be understood through its actual business, financial statements and cash generation rather than surface-level numbers; Class 8 specifically stresses separating core operating income from other income. 

**For the next sector, we should keep exactly this structure but change the metrics—not just the thresholds.**

[1]: https://www.rbi.org.in/Scripts/bs_viewcontent.aspx?Id=624&utm_source=chatgpt.com "Database - Historical Data- Reserve Bank of India"
[2]: https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern?utm_source=chatgpt.com "Corporate Filings Shareholding Patterns - Equity, SME - NSE India"
[3]: https://www.nseindia.com/companies-listing/corporate-filings-pledged-data?utm_source=chatgpt.com "Corporate Filings Pledged Data - Equity, SME - NSE India"
[4]: https://www.bseindia.com/corporates/shpPromoterNGroup.aspx?qtrid=116.01&scripcd=539254&utm_source=chatgpt.com "Shareholding Pattern"
[5]: https://www.mca.gov.in/Ministry/pdf/MCAV2Release2_Help.pdf?utm_source=chatgpt.com "MCA21 Application - Online Help"
[6]: https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&smid=133&ssid=9&utm_source=chatgpt.com "SEBI | Orders"
