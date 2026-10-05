# Stock Quality framework — how it is implemented

Spec: `stock_quality_portfolio_replacement_agent_framework.md` (22 sections).
Code: `backend/app/framework/`. This file is updated as each phase lands.

The framework's scores are the headline scores of the app. The older six
category scores (`backend/app/calculations/scoring.py`) are unchanged and feed
into them. The scores are stored separately and never averaged into one number.

## Where scores are stored

Table `fw_scores`: one row per stock, per day, per basis.

- `basis` is `QUICK` (Yahoo statements, whole universe, written by the quick
  scorer) or `FULL` (written at the end of a full analysis). A reader prefers
  `FULL` unless the quick row is from a later financial year.
- Rows from earlier days are kept, which is what Quality Momentum (section 10)
  will read.
- `detail` holds every input behind every score.

API: `GET /api/framework/scores` (table) and `GET /api/framework/{symbol}`
(one stock with all inputs). Page: **Combined Score**.

Refresh: scores are written whenever the quick scorer or a full analysis runs.

```bash
cd backend
.venv/bin/python -m app.quick_analysis.runner --limit 3000 --force   # whole universe
.venv/bin/python -m scripts.backfill_framework_scores                # FULL rows from stored analyses
```

## Fundamental Score (section 4) — built in phase 4

"Are the financial numbers strong?" Hard financial data only: no valuation, no price.

| Share | Component | Section 4 inputs it covers | Source |
|---|---|---|---|
| 80% | growth | revenue, PAT, EPS growth | existing category score |
| | profitability | ROE, ROCE, operating margin, net margin | existing category score |
| | cash_flow | free cash flow, CFO/PAT | existing category score |
| | balance_sheet | debt/equity, interest cover, balance-sheet strength | existing category score |
| | efficiency | (add-on: not on the framework's list, counted at half its sector weight) | existing category score |
| 8% | earnings consistency | earnings consistency | share of quarters in profit and ahead of the same quarter last year, from stored Screener quarters (about 13); Yahoo annual profit when none are stored |
| 5% | working-capital trend | working capital trend | direction of the cash conversion cycle and of working capital to revenue |
| 4% | share dilution | share dilution | yearly growth in share count, derived as net profit / basic EPS; split and bonus years excluded |
| 3% | dividend sustainability | dividend sustainability | payout ratio and free-cash-flow cover of the dividend |

Rules:

- The 80% is split using the sector's own weights (39 sector weight sets),
  with the valuation weight removed and the rest rescaled. Banks, NBFCs and
  insurers keep their own formulas (section 19); working-capital trend and
  free-cash-flow cover are not applied to them.
- An input that does not apply or has no data is left out and the remaining
  weights are rescaled. It is never scored as 50. `coverage` reports the share
  of weight that was scored; below 50% no score is given.
- **"Double in" (section 4):** years for revenue and profit to double are
  reported. When profit growth is mostly a recovery from a depressed margin
  (starting margin under 60% of the usual margin since, and profit growing
  more than twice as fast as sales plus 10 points), the growth component is
  capped at 70.
- Bands: 65+ strong, 50–64 good, 40–49 borderline, 30–39 weak, under 30 very weak.

**Screener first (2026-10-06).** Like the full analysis, the quick scorer now
reads each company's Screener page first and Yahoo only fills gaps: the
runner reads the standalone and consolidated pages once per company
(`backend/app/ingestion/screener_pages.py`, about 1.2 s apart), the existing
Screener ingests store about 12 years of annual P&L, balance sheet, cash flow,
ratios, quarterly results, shareholding and the top-ratio strip, and the full
analysis's own `apply_screener_primary_overrides()` replaces Yahoo figures
wherever Screener has them. A company read within the last week is not read
again. `--no-screener` gives the old Yahoo-only run.

**Long-run growth.** With Screener's history, 3-, 5- and 10-year growth rates
are available. The growth component is 70% the existing growth score (3-year
rates and the recent quarters) and 30% the 5-year sales, profit and EPS rates,
scored on the same thresholds. "Double in" uses the 5-year rate (3-year when
the company has less history) and reports all three.

## Trend (section 9) — built in phase 4

The direction of the business, not of the price. Each signal votes up, flat or down:
returns (ROCE; ROE for lenders), net margin, operating margin, debt, free cash
flow, and whether recent quarterly sales growth is ahead of or behind the
multi-year rate. Lenders are read on returns, net margin and growth only.

| Label | Rule |
|---|---|
| Improving | improving signals lead by 2 or more and are more than double the declining ones |
| Declining | the mirror image |
| Cyclical | margins swing widely (or two or more signals are volatile) and the signals point both ways with no clear lead |
| Stable | everything else |
| Insufficient data | fewer than 3 signals readable (2 for a lender) |

Not yet included: earnings revisions (analyst estimates are stored for only
about 56 companies).


## Business Quality (section 3) — built in phase 5

"Is this a good business?" Measured from Screener's annual statements
(consolidated when Screener has five or more consolidated years, otherwise
standalone; never mixed) and shareholding, NSE pledge data, and the concall
guidance tracker. Code: `backend/app/framework/business_quality.py`.

| Part | Weight (lender) | Measure |
|---|---|---|
| Durability of returns | 25% (35%) | Last up to 10 years: share of years with ROCE 15%+ (ROE 14%+ for a lender) and the median. ROCE = (PBT + interest) / average (equity + reserves + borrowings). A year with negative net worth counts as zero. |
| Margin resilience | 20% (—) | Worst operating margin of the decade divided by the median one — pricing power shows as margins that hold up |
| Predictability | 15% (20%) | Share of years without a loss or a profit fall of more than 20%; three or more such years marks the business cyclical |
| Capital allocation | 15% (20%) | Extra operating profit over five years divided by extra capital employed (extra profit / extra net worth for a lender). Profit growing with no capital added scores 90; still loss-making scores 5 |
| Promoter behaviour | 15% (15%) | Change in promoter holding over three years (Screener), less twice the NSE pledge / promoter-selling penalty where NSE data has been read. Not scored for widely held companies with no promoter |
| Management credibility | 10% (10%) | Share of tracked guidance kept or raised rather than cut (concall analysis; only where it has run) |

Not measured anywhere, and shown as such: brand strength, customer
concentration, industry structure, regulatory risk. They are never guessed.
The "special situational logic" (a stock holding up while its sector is weak)
needs relative strength and arrives with phase 6.

## Quality Score (section 2) — built in phase 5

    Quality = 70% Fundamental Score + 30% Business Quality      (user's choice, 2026-10-06)

- Business Quality not measurable: Quality = Fundamental, and the formula says so.
- **Governance cap:** promoter pledge above 10% of the promoter holding, or an
  NSE governance penalty of 10 points or more, caps Quality at 49, so the
  company cannot pass the core gate of 50 (section 17).
- Bands: 65+ strong (preferred), 50–64 good (investable gate), 40–49
  borderline (watch), below 40 weak, below 30 very weak.
- The Combined Score page sorts by Quality and shows Business Quality under it;
  opening a row shows every component, its weight, its figures and its source.
