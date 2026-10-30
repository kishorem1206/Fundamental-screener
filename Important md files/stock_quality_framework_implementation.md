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

**Regulatory record** (added 2026-10-30, Phase A of the data-sources plan): SEBI
orders against the company over the last three years take up to 20 points off
the Business Quality score — a deduction, not a weighted part, so a clean
record changes nothing. See "Risk: SEBI orders and credit ratings" below.

Not measured anywhere, and shown as such: brand strength, customer
concentration, industry structure. Regulatory risk is listed as not measured
only while SEBI's orders have not been read. They are never guessed.
The "special situational logic" (a stock holding up while its sector is weak)
needs relative strength and arrives with phase 6.

## Quality Score (section 2) — built in phase 5

    Quality = 70% Fundamental Score + 30% Business Quality      (user's choice, 2026-10-06)

- Business Quality not measurable: Quality = Fundamental, and the formula says so.
- **Governance cap:** promoter pledge above 10% of the promoter holding, an
  NSE governance penalty of 10 points or more, or a serious SEBI order against
  the company in the last two years, caps Quality at 49, so the
  company cannot pass the core gate of 50 (section 17).
- Bands: 65+ strong (preferred), 50–64 good (investable gate), 40–49
  borderline (watch), below 40 weak, below 30 very weak.
- The Combined Score page sorts by Quality and shows Business Quality under it;
  opening a row shows every component, its weight, its figures and its source.

## Quantitative Score (section 5) — built in phase 6

"Are the measurable numbers getting better or worse?" Changes and statistical
behaviour only. Levels of growth, margins and returns stay in the Fundamental
Score; returns against benchmarks stay in Relative Strength (section 18).
Code: `backend/app/framework/quantitative.py`.

| Part | Weight (lender) | Measure | Source |
|---|---|---|---|
| Growth acceleration | 20% (25%) | Sales and profit growth of the last four quarters against the four before, minus the three-year rate | Screener quarterly results and annual statements |
| Margin change | 15% (10%) | Operating margin of the last four quarters against the four before, in points (net margin for a lender) | Screener quarterly results |
| Return change | 15% (20%) | ROCE (ROE for a lender) now against three years ago | Screener annual statements |
| Debt change | 10% (—) | Borrowings / net worth now against three years ago; debt-free throughout scores 85 | Screener annual statements |
| Volatility | 15% (15%) | Annualised daily volatility over one year | stored prices |
| Drawdown | 10% (10%) | Largest fall from a high over one year | stored prices |
| Risk-adjusted return | 15% (20%) | (one-year return − 6.5%) / volatility | stored prices |

Not measured: earnings revisions (analyst estimates exist for about 56
companies). Quality Score change over time arrives with Quality Momentum.

## Relative Strength Score (section 6) — built in phase 6

Price behaviour against the market, the sector and same-sector stocks.
Code: `backend/app/framework/relative_strength.py`, `price_stats.py`.

| Part | Weight | Measure |
|---|---|---|
| vs market | 25% | Compounded excess return over the Nifty 50 for 1, 3, 6 and 12 months (weights 10/20/30/40), each scaled to a one-year equivalent by the square root of time before scoring |
| vs sector | 25% | The same against the NSE sector index from `app/prices/benchmarks.py`; where NSE has no index for the sector, the median of same-sector stocks |
| Sector percentile | 15% | Rank of the 6- and 12-month return among same-sector stocks (Top 10% / 25% / 40% / 50% / Bottom 50%) |
| Resilience in market falls | 15% | Excess return during the Nifty 50's worst fall of the year (60%) and since its low (40%); needs a market fall of 5%+ |
| Drawdown vs market | 10% | Stock's largest fall of the year minus the index's |
| Near 52-week high | 10% | Last close / 52-week high (new-high participation) |

Needs at least three months of stored prices (six for the percentile, a year
for resilience and drawdown). Comparison with the user's holdings arrives with
the portfolio (phase 10).

**Special situational logic (section 3).** When the sector benchmark is down
over 6 or 12 months and the stock is 10%+ ahead of it, the result carries
`why_holding_up`: the business reasons found in the data (growth accelerating,
margins widening, debt falling, strong cash flow or balance sheet, durable
returns, resilient margins), or "the strength is price alone" when there are
none. It explains; it does not change any score.

## Technical Score (section 7) — built in phase 7

Price and volume structure and timing, on the stored daily bars (split-adjusted
closes, so a bonus issue is not a crash), using the technical screener's own
engines for RSI (Wilder, matches TradingView), MACD 12/26/9 and RSI divergence.
Code: `backend/app/framework/technical.py`. Checked against the screener: ITC
RSI 53.13 vs 53.14 live; MACD −1.292 / signal −1.731 / histogram 0.439 vs the
MACD scan's −1.286 / −1.722 / 0.436.

| Part | Weight | Measure |
|---|---|---|
| Trend structure | 20% | Last two swing highs and lows (5 bars each side, six months): higher highs and higher lows 95, tightening 60, widening 40, lower highs and lows 10; a close below the last swing low caps at 25, above the last swing high lifts to 75 |
| Moving averages | 20% | Close > 200-day (30), close > 50-day (25), 50 > 200 (25), 200-day rising over a month (20) |
| RSI (14) | 10% | 55–70 best; below 35 or above 78 marked down |
| MACD | 10% | Above signal (40), above zero (30), histogram rising (30) |
| Volume confirmation | 10% | Average volume on up days / down days over 50 days |
| Breakout / breakdown | 15% | Close above the prior 60-day high on 1.5× volume in the last 10 days scores 100; below the 60-day low scores 5; otherwise position in the range |
| Base / contraction | 10% | Last 20 days' range against the 60 before (tighter is better), weighted by closeness to the 52-week high |
| Reversal structure | 5% | Recent RSI divergence: bullish 85, bearish 15, none 50 |

Price recovery after a drawdown is measured once, in Relative Strength's
resilience. A strong Technical score never lifts a stock that fails the
Quality gate: the decision engine (phase 9) can only call it tactical.

## Valuation Score (section 8) — built in phase 7

Higher is cheaper. Code: `backend/app/framework/valuation.py`.

Market value: Screener's market cap on the day it was read, moved to the as-of
date by the split-adjusted close (so splits and bonuses cannot distort it);
the stocks table's market cap where Screener has not been read. Earnings: last
four quarters' Screener net profit, consolidated first. A quarter larger than
twice the other three combined (and over half the total) is treated as a
one-off and the other three are annualised (Vodafone Idea's ₹51,970 cr March
2026 quarter). Peers for multiples: the industry when it has 8+ listed
companies (banks with banks), else the sector.

| Part | Weight (lender) | Measure |
|---|---|---|
| P/E vs own history | 25% (15%) | Percentile of today's P/E among quarter-end P/Es over the stored three years |
| P/E vs industry | 20% (15%) | Percentile among industry peers with profits |
| P/B vs own history | — (25%) | As above, with Screener net worth |
| P/B vs industry | — (20%) | As above |
| PEG | 15% (10%) | P/E / three-year profit growth (Screener) |
| EV/EBITDA | 10% (—) | Yahoo (Screener shows no enterprise value) |
| Free-cash-flow yield | 15% (—) | Screener latest-year free cash flow / market cap |
| Deep report value | 15% (15%) | Deep report's blended value per share against the price, where built (7 companies) |

View: 65+ cheap, 40–64 fair, below 40 expensive. With Quality it gives the
section 8 reading: strong + cheap "potential high-conviction candidate",
strong + fair "investable if other conditions support", strong + expensive
"good business, poor entry price", weak + cheap "possible value trap", weak +
expensive "usually avoid". Earnings yield is not scored separately (it is the
inverse of P/E). Own history covers three years because the price store does;
a longer price backfill would extend it.

## Quality Momentum (section 10) — built in phase 8

Quality now against 6 and 12 months ago. Code: `backend/app/framework/momentum.py`.
Stored on `fw_scores` as `quality_change_6m`, `quality_change_12m` and
`quality_direction`, with both earlier readings in `detail.momentum`.

- **Recorded:** a stored Quality row within 20 days of the target date (rows
  are kept per day from 2026-10-05, so this takes over by itself in April and
  October 2027).
- **Reconstructed** (until then): Quality is rebuilt as at today, 6 months
  ago and 12 months ago from the Screener results published by each date —
  annual results count 60 days after the year end, quarterly results 45 days
  after the quarter end, shareholding as filed. Point-in-time metrics: growth
  from the annual years, margins from the last four published quarters
  (one-off quarter rule applied), returns, leverage and cash conversion from
  the latest published year, plus the existing quarterly growth score fed with
  the quarters published by then. The same method is used at all three dates;
  the earlier score shown is today's actual Quality minus the rebuilt change.
  Left out at all three dates because there is no history to replay: Yahoo-only
  inputs (dilution, dividend, working capital), NSE pledge events, concall
  guidance tracking.
- **Direction:** improving when the 12-month change is +5 or more (or the
  6-month change +3 or more without a 12-month fall); declining when the
  12-month change is −5 or less (or the 6-month change −3 or less without a
  12-month rise); otherwise stable.

Caveat: a one-off in a company's annual figures moves the rebuilt score too
(Vodafone Idea's FY2026 annual profit includes its one-off gain).

## Sector-relative quality (section 11) — built in phase 8

Rank of Quality within the stock's NSE sector, computed when read from every
stock's latest Quality (`backend/app/framework/sector_rank.py`): "#3 of 30"
with a Top 10% / 25% / 40% / 50% / Bottom 50% label. Sectors with fewer than
five scored stocks get no rank. Core-candidate rule for phase 9: Quality ≥ 50
and preferably Top 40% within the sector.

## Decision engine (sections 13, 15, 16, 17, 20, 21, 22) — built in phase 9

Fixed rules in `backend/app/framework/decision.py`; stored as `classification`
and `action` on `fw_scores`, with size, matrix row, gates, reasons and the
business interpretation in `detail.decision`. The language model writes the
explanation only (`explain.py`).

**Direction** used by the matrix: measured Quality Momentum (improving,
stable or declining); the business trend label only when momentum is unknown.

**Gates (section 17):** core = Quality 50+ with no governance red flag, no
balance-sheet score under 35, and no cash-flow score under 35 with free cash
flow declining. Preferred core adds Quality 65+, not declining, top 40% of the
sector. Recovery = Quality 40–49, improving, relative strength 60+, fair or
cheap, no flags. Tactical = Quality under 40 with technical 65+ and relative
strength 55+.

| Situation (checked in this order) | Classification | Action | Size |
|---|---|---|---|
| Core-gate red flag, Quality 40+ | Replacement Candidate | Replace | — |
| Tactical gate | Tactical Only | Add on confirmation, with an exit rule (last swing low / 50-day average) | Tactical only |
| Quality 65+, declining | Investable | Hold (do not add) | — |
| Quality 65+, expensive | Core Quality | Hold (good business, wait for price) | Small |
| Quality 65+, technical under 40 | Core Quality | Add on confirmation (good business, poor timing) | Small |
| Quality 65+, otherwise | Core Quality | Add gradually (technical 50+) or on confirmation | High if fair/cheap, RS 60+, Fundamental 65+ and preferred core; else Medium |
| Quality 50–64, improving | Investable | Add gradually / on confirmation | Medium (RS 55+) or Small |
| Quality 50–64, declining | Investable | Watch | — |
| Quality 50–64, stable | Investable | Hold (expensive or poor timing) / Add on confirmation | Small |
| Quality 40–49, recovery gate | Recovery Candidate | Add on confirmation | Small |
| Quality 40–49, declining | Replacement Candidate | Replace | — |
| Quality 40–49, otherwise | Improving / Watch | Watch | — |
| Quality under 30, or under 40 and declining | Avoid | Avoid | — |
| Quality 30–39 | Replacement Candidate | Replace | — |

Below the gate and cheap adds "possible value trap". Portfolio concentration,
sector exposure and asset allocation (section 13's second half, section 14)
come with the portfolio, phase 10.

**Section 20 output:** business interpretation (strong / weak components,
improving / deteriorating signals, performance against the Nifty 50, the
"holding up" reasons), best same-sector alternative (a stock passing the core
gate, ranked by readiness to buy then Quality — "better current opportunity",
kept apart from "better company"), and for Replacement Candidate, Improving /
Watch and Avoid a replacement view: score differences, valuation views and
risk (volatility, one-year drawdown).

**Explanation (section 21):** `POST /api/framework/{symbol}/explain`. gpt-oss
gets the scores, decision, gates and interpretation, and the section 21 agent
prompt. Its answer is rejected unless it names the stock's classification and
names no other classification, negates it or speaks of moving into it; then the
fixed-text explanation is used. Cached on the row by a hash of the inputs.

**Refresh:** each scoring decides that stock against its sector as it stands;
the quick runner re-decides every stock at the end of a run of 50+ stocks
(`app.framework.decisions.refresh_all`, no network calls).

## Portfolio (sections 12, 13, 14, and the end of 16) — built in phase 10

Code: `backend/app/portfolio/`. Page: **Portfolio**. Tables: `pf_holdings`,
`pf_settings` (migration 0041).

**Where holdings come from**
- **Kite** (`kite_link.py`): the backend opens its own session to Zerodha's
  hosted Kite MCP server. "Connect Kite" returns Kite's login link; after
  logging in, "Sync from Kite" reads holdings, mutual funds and the cash
  margin and replaces the Kite rows. Only reading tools can be called; order
  tools are refused in code. The session lasts until the backend restarts.
- **CSV** (`importers.from_csv`): any broker export with a symbol or ISIN
  column and quantity and price (or value) columns — Dhan, Zerodha console,
  others. Each upload replaces that broker's rows.
- **By hand**: gold, debt, cash, international, anything not in a broker.
- Stocks are matched to the app by ISIN, then symbol. Funds and ETFs get an
  asset class from their name (gold, debt, international, else equity fund),
  recorded as "classified from the name".

**Section 12 — is it better than what I already own?** Each held stock is set
against the best same-sector stock passing the core gate. Reported separately:
better company (Quality) and better current opportunity (average of relative
strength, technical and valuation). "Clearly better" needs the candidate to
pass the core gate, be no more than 5 Quality points and 10 Fundamental points
weaker, and either the holding fails the gate or the candidate's opportunity
score is 10+ higher. New-money candidates: not owned, Core Quality or
Investable, ready to buy, outside sectors at the limit, at most three per
sector, each compared with the weakest holding in its sector.

**Section 13 — position size.** Bands of the equity book (stocks + equity
funds): High 6–8%, Medium 4–5%, Small 2–3%, Tactical up to 1.5%. One size
smaller for volatility above 45% a year or correlation above 0.8 with the rest
of the portfolio. Caps: 10% per stock, 25% per sector (user settings). A
position above 10% of the stock's median daily traded value is flagged as slow
to exit.

**Section 14 — asset allocation.** Share of the total in each asset class
against the user's own targets (over / under by more than 5 points); no target,
no judgement. Portfolio volatility and worst one-year fall of the listed stocks
held at today's weights, against the user's drawdown tolerance (default 25%).

**Final action (section 16 order):** Replacement Candidate or Avoid with a
clearly better candidate → Replace with it; Avoid without one → Reduce;
Replacement Candidate without one → Watch (keep, look for a replacement);
above the per-stock cap → Reduce; an Add action at the top of its band or in a
sector at the limit → Hold; otherwise the decision engine's action, with the
amount that reaches the middle of the band.


## Integrated report — built in phase 11

`backend/app/reporting/integrated/` · `GET /api/framework/{symbol}/integrated-report.pdf`
· buttons on the full analysis and in an opened Combined Score row.

One PDF in three parts, with a cover (classification, action, six scores) and a
contents page giving each part's first page:

- **Part A — Stock Quality framework** (new, `framework.html.jinja`, in the deep
  report's stylesheet so the parts look alike): the decision and why, the
  explanation (gpt-oss if one is cached and passed the check, otherwise the
  rule-based text), business interpretation, "holding up" reasons, relative
  comparison (sector rank, Quality momentum, best same-sector alternative,
  replacement view, whether held), the six scores, and one table per score with
  every input, weight, figure and source.
- **Part B — editorial report**, exactly as `editorial_pdf_service.py` renders it
  (generated if the latest completed full analysis has none yet). Left out, with a
  note, when no full analysis has been run.
- **Part C — deep report**, exactly as `app/bie/report/render.py` renders it.
  Left out, with a note, when it has not been built.

Each part keeps its own footer and page numbering; the contents page gives the
page in the combined file.

## Section-by-section coverage of the spec

| Section | Where |
|---|---|
| 1 Core principle (separate scores) | `fw_scores` columns; Combined Score page |
| 2 Quality Score gate and bands | `quality.py`; decision engine |
| 3 Business Quality, special situational logic | `business_quality.py`; `relative_strength.why_holding_up` |
| 4 Fundamental Score, "double in" | `fundamental.py`, `inputs.py` |
| 5 Quantitative | `quantitative.py` |
| 6 Relative Strength | `relative_strength.py`, `price_stats.py`, `app/prices/` |
| 7 Technical | `technical.py` (technical screener engines) |
| 8 Valuation and its interpretation | `valuation.py` |
| 9 Trend | `trend.py` |
| 10 Quality Momentum | `momentum.py` |
| 11 Sector-relative quality | `sector_rank.py` |
| 12 Portfolio comparison | `portfolio/analysis.py` (`clearly_better`, candidates) |
| 13 Position sizing | `portfolio/analysis.py` (bands, volatility, correlation, liquidity, caps) |
| 14 Asset allocation | `portfolio/analysis.py` (targets, drawdown tolerance) |
| 15 Decision matrix | `decision.py` |
| 16 Agent decision flow | `decision.py` then `portfolio/analysis.py` (final action) |
| 17 Minimum gates | `decision.gates` |
| 18 Avoid double counting | one home per signal, noted in each module's docstring |
| 19 Sector-specific scoring | lender formulas throughout; 39 sector weight sets |
| 20 Output format | opened row on Combined Score; integrated report Part A |
| 21 Agent prompt | `explain.py` |
| 22 Final philosophy | rules: Quality first, never averaged, compare with what is owned |

Not measured anywhere (no source across the universe), and said so where they
would appear: earnings revisions, brand strength, customer concentration,
industry structure. (Regulatory risk is measured from SEBI's orders since
2026-10-30.)

## NSE's MCP servers as a data source (2026-10-06)

NSE publishes two MCP servers (https://www.nseindia.com/nse-mcp). The backend
uses them directly (`backend/app/nse_mcp/`, a small JSON-RPC client — the `mcp`
library's client fails against them) and they are also in `.mcp.json` for
Claude sessions.

| Server | Tools (13 each) | Used here for |
|---|---|---|
| `nse-bhavcopy` `https://mcp.nseindia.in/bhavcopy/cm/mcp` | `get_stock_history` (5 years, unadjusted, incl. SME), `get_corporate_actions`, `get_bulk_quote`, `get_ltp_by_date`, `get_market_breadth`, `get_52_week_high_low`, `get_volume_analysis`, `moving_average`, `compare_stocks`, `get_top_movers`, `get_top_by_volume`, `search_symbols`, `nse_lookup_symbol` | corporate actions; price history for stocks Yahoo lacks; repricing portfolio holdings; market breadth |
| `cm-market` `https://mcp.nseindia.in/cmmkt/mcp` | `cm_get_stock_quote`, `cm_get_equity_stocks`, `cm_get_sme_stocks`, `cm_get_bond_stocks`, `cm_get_call_auction_stocks`, `nse_get_market_movers`, `nse_get_gainers`, `nse_get_losers`, `cm_get_live_gainers`, `cm_get_live_losers`, `cm_get_live_market_data`, `cm_get_data_status` | live price on the Combined Score row |

**Gaps they fill**

- **Corporate actions** (`nse_corporate_actions`, migration 0042): NSE's own
  splits, bonuses and dividends with ex-dates and adjustment factors. Read
  from NSE's website feed first (`/api/corporates-corporateActions`, the same
  data the MCP tool serves, about a second per stock and dependable in bulk),
  with the MCP tool `get_corporate_actions` as the fallback: in testing the MCP
  tool often hung on a symbol's first fetch. The adjustment factor is worked
  out from NSE's wording ("Bonus 1:1" → 0.5; "Split From Rs 10 To Rs 2" → 0.2).
  - *Share dilution* (Fundamental): a share-count jump in a financial year NSE
    lists a split or bonus for is that event, confirmed by NSE, not dilution.
    The equity-based guess remains only for stocks whose actions are not read.
  - *Dividend sustainability* (Fundamental): the dividend is what NSE shows
    was actually paid in the last twelve months, restated to today's share
    count (a dividend before a later bonus is scaled by the bonus factor);
    payout = that dividend / trailing EPS. Yahoo's stated rate only when NSE's
    list has not been read. No dividend in twelve months on NSE's list → not scored.
- **Price history Yahoo does not have** (`history.py`): SME listings, InvITs,
  REITs and recent listings get NSE's own daily bars, adjusted here with NSE's
  factors (close for splits and bonuses; adjusted close also for dividends), so
  they get Relative Strength, Technical, Quantitative and Valuation scores too.
- **Live price** in an opened Combined Score row (`/api/nse/quote/{symbol}`,
  one-minute cache) and **Refresh prices (NSE)** on the Portfolio page for
  holdings that came from a CSV or were typed in.
- **Market breadth** (`/api/nse/breadth`).

**What they do not provide** (so these stay as they were): adjusted prices
(NSE's are raw, so Yahoo remains the main price source and NSE the check),
index history (already taken from NSE's daily index file), fundamentals,
enterprise value, analyst estimates.

**Behaviour to know:** NSE throttles a burst of calls for about a minute, and
the first fetch of a symbol can hang. Calls are spaced 1.5 s apart and retried.
The 500-row live-list tools time out; per-symbol quotes are used instead.

```bash
cd backend
.venv/bin/python -m app.nse_mcp.runner --actions       # corporate actions for every stock (about 1.5 hours first time; then monthly)
.venv/bin/python -m app.nse_mcp.runner --fill-prices   # NSE history for stocks with none stored
```

## Two changes to the older scores (2026-10-06, user's decisions)

**ROCE is Screener's own figure on every page.** `backend/app/calculations/screener_roce.py`
reads Screener's yearly "ROCE %" row (`bs_ratio_roce_percent`, consolidated when
it has two or more years, else standalone) and is the only source for: the Key
Metrics value, the ROCE series and trend label, 3- and 5-year averages, peak,
trough and cycle position (`screener_metrics_override.py`), the Balance Sheet
tab (which keeps its own Total Assets − Current Liabilities figure as
`roce_own_method`, for the DuPont split), and the framework's annual series
(Business Quality durability, Quantitative return change, Quality Momentum).
Before this, three formulas were in use and disagreed (Sigma Solve: 32.6%, 48%,
48.5%; Siemens Energy 29% against Screener's 68%). Screener publishes no ROCE
for banks and other lenders; they are scored on ROE and any computed ROCE is
labelled as computed. Stored full analyses were corrected by
`scripts/backfill_roce_and_direction.py`.

**Profitability is direction-aware.** `scoring.py::profitability_direction`:
the level sets the profitability score, then each return and margin's trend
label moves it — strongly improving +7, improving +4, stable 0, volatile −3,
deteriorating −10, strongly deteriorating −18 — weighted by the metric's own
weight (EBITDA margin 30%, PAT margin 20%, ROE 25%, ROCE 25%; ROE 50%, ROA 40%,
PAT margin 10% for lenders) over the labels available. No labels, no change.
The adjustment and its labels are stored as `scores.profitability_direction`
and shown under the score chart. Sigma Solve: −12, profitability 96.8 → 84.8,
Composite 90.6 → 87.4.

Note on double counting (framework section 18): direction now also touches the
Fundamental Score through this category, alongside the Quantitative Score's
return and margin change. This was chosen knowingly so the older Composite
Score stops rating a deteriorating business as if nothing had changed.


## Risk: SEBI orders and credit ratings (Phase A, 2026-10-30)

Code: `backend/app/risk/`. Tables: `sebi_orders`, `sebi_order_matches`,
`credit_ratings` (migration 0043).

**SEBI orders.** Source: sebi.gov.in → Enforcement → Orders, read through the
listing page's own AJAX call (25 orders a page, newest first; it answers only
inside the listing page's session). Read back to October 2021: 7,874 orders,
with 360 listed companies named at least once.
Titles are matched to companies by our name and NSE's official name
(EQUITY_L.csv), conservatively (`risk/names.py`): one- and two-word names must
read "X Limited/Ltd" after a joining word, the longer of two overlapping names
wins, "X Group companies" names every stock starting with X. Each match has a
role:

| Role | Title shape | Effect |
|---|---|---|
| NAMED | "in the matter of X Limited", "in respect of X Limited" | can be serious |
| GROUP | "in the matter of X Group companies" | as NAMED |
| MATTER | "in respect of Mr Y in the matter of X Limited" (others are the noticees) | small, capped |
| SCRIP | "trading in the scrip of X", "options at the BSE" (the company's shares or the exchange are the venue) | shown only |

Orders that name a company and can be adverse (FINAL, INTERIM, ORDER,
ADJUDICATION) are opened, because a title alone cannot say whether a case ended
in a penalty or was closed. The last six pages of the PDF are read, after
removing two things that otherwise give wrong answers: the running footer
(every page repeats the title, so the company's name is always "present") and
the recital (which quotes earlier orders and other authorities' penalties).
Long orders end in annexures, so the pages are read backwards to the last page
that decides something, and the six pages ending there are kept. Outcome:
DIRECTIONS (restraint, debarment), DISGORGEMENT (money given up, refunded or
impounded), COMPLIANCE (directions to do something, no restraint), PENALTY (with
the largest amount), DISPOSED, UNKNOWN (14 of 231, including preliminary-issue
orders that decide nothing yet).

| Grade | Rule | Points off Business Quality |
|---|---|---|
| SERIOUS | whole-time member / quasi-judicial order in the company's own matter with restraint directions (on the company or those running it), or disgorgement or a penalty of ₹1 crore or more on the company itself | 15, and a red flag if within 24 months |
| PENALTY | a smaller penalty on the company, or directions to comply | 6 |
| MATTER | directions or penalties on others in the company's matter | 4 (8 at most in all) |
| SETTLED | settlement order | 3 (6 at most in all) |
| NOTE | scrip trading, exemption, revocation, recovery, court, disposed, unread | 0 |

Deduction at most 20. A SERIOUS order within two years caps Quality at 49 and
fails the core gate ("governance: SEBI order …").

**Credit ratings** (report only: user's decision, 2026-10-30). Source: NSE
corporate announcements with subject "Credit Rating"; one query covers every
company for a month. The announcement carries only a generic line, so the rating
is read from the company's own letter (PDF, first four pages) by
`risk/rating_text.py`: agency (from the rating's prefix), long- and short-term
rating on the Indian scale, outlook or rating watch, action, previous rating,
instrument, rationale link. The action is read from the cover letter only,
because the agency rationale often attached after it contains "factors that could
lead to a downgrade". On the first fill 1,862 of 2,157 letters were read (86%);
ESG ratings, international agencies and scanned letters are stored unread. Letters
were read back 15 months.

**Credit ratings feed no score, gate, flag or classification.** They appear in
one place: section 06 of the Editorial Report (and so the integrated PDF),
as a table of what each agency says with links to the filing and rationale. A
test (`test_only_the_sebi_record_can_fail_the_gate`) holds this.

First fill, 2026-10-30: 12 stocks carry a SEBI red flag. Every flagged order was
checked by hand against its PDF; the parsers' tests record what those checks found.

**When it applies.** SEBI red flags are read fresh at every decision
(`decisions._apply` puts the current record in `detail.risk`), so a new order
changes the classification the next time decisions are refreshed — no
re-scoring. The Business Quality deduction and the Quality cap apply when a stock
is next scored. The stock detail on the Combined Score page shows the record with
links to each order.

    cd backend
    .venv/bin/python -m app.risk.runner --sebi --read-orders      # new orders since the last run, then read them
    .venv/bin/python -m app.risk.runner --credit --months 2       # recent rating letters
    .venv/bin/python -m app.risk.runner --refresh-decisions       # re-apply classifications with current flags

## Portfolio sources (Phase B, 2026-10-30)

**AMFI NAV** (`backend/app/portfolio/amfi.py`, table `amfi_navs`, migration
0044): AMFI's daily `NAVAll.txt` (about 18,000 ISINs). A fund or ETF held is
looked up by ISIN; its asset class comes from AMFI's scheme category (gold and
silver → GOLD, overseas → INTERNATIONAL, debt / liquid / gilt / arbitrage /
conservative hybrid → DEBT, equity and other hybrids → EQUITY_FUND); only
headings that do not say (index funds, other ETFs, domestic fund of funds) fall
back to the name. A fund with no broker price is valued at its NAV. Kite syncs,
broker syncs and "Refresh prices" refresh the file when it is a day old.

**Broker holdings** (`backend/app/portfolio/brokers.py`), read only, holdings
endpoint only, token from `backend/.env`:

| Broker | Endpoint | Token |
|---|---|---|
| Dhan | `GET https://api.dhan.co/v2/holdings` (no price: valued at the stored close) | `DHAN_ACCESS_TOKEN` |
| Upstox | `GET https://api.upstox.com/v2/portfolio/long-term-holdings` | `UPSTOX_ACCESS_TOKEN` |
| Groww | `GET https://api.groww.in/v1/holdings/user` (paid trade API; no price) | `GROWW_ACCESS_TOKEN` |

Portfolio page: a "Sync from …" button per broker, greyed out until its token
is set. Not tested against live accounts (no keys here); the parsers are tested
on the documented response shapes.


## Market & Macro and FPI flows (Phases C and D, 2026-10-30)

Context for reading the market. **Nothing here feeds a score, gate or
classification** (`test_flows_do_not_reach_any_score`). Code: `backend/app/macro/`;
page: `frontend/src/components/MacroPage.tsx`; tables `macro_points`,
`fpi_sector_flows` (migration 0046). The catalogue of series with labels, units
and sources is `macro/catalogue.py`.

| Series | Source | Note |
|---|---|---|
| GDP, IIP, CPI, WPI, FX reserves | MoSPI MCP, `mcp.mospi.gov.in` (no key) | CPI and IIP growth as published; GDP and WPI growth computed year on year. All India is state 99 in CPI's 2012 base and 1 in the 2024 base. FX reserves lag: the feed stops at June 2025 and the tile says so |
| Repo, SDF, MSF, CRR, SLR, call rate, 10-year G-sec, rupee | RBI home page, "Current Rates" | RBI shows only today, so these build up from 2026-10-30 |
| Yield curve | CCIL, through `bie/macro.py` | Already the deep report's risk-free rate (9Y-10Y bucket); plan item 6 needed no change |
| Nifty P/E, P/B, yield, India VIX | NSE index file, already stored | |
| CBOE VIX | CBOE CSV | |
| US 10-year, dollar index, Brent, gold | Yahoo | FRED's key-free CSV times out; its API needs a key |
| Long-run growth and inflation | World Bank; IMF projections from `bie/macro.py` | |
| FPI daily and monthly | NSDL `Monthly.aspx`, `Yearwise.aspx?RptType=6` | Daily: this month; monthly from January 2022 |
| FPI by sector | NSDL fortnightly static files, from August 2024 | Sector names match `stocks.sector`. "Consumer Cyclical" and "Other" have no NSDL row |

**Not available:** bank credit growth. RBI's DBIE has no feed this app can read,
and MoSPI's RBI dataset covers only the external sector.

**Sector flow:** net FPI equity investment over the last six fortnights (about
three months) as a share of FPI holdings in the sector, ranked. Shown on the Macro
page and on the opened stock next to Relative Strength; not scored, because
whether it predicts anything has not been tested.

    cd backend
    .venv/bin/python -m app.macro.runner              # daily
    .venv/bin/python -m app.macro.runner --history    # first fill


## Peers are like for like (2026-10-30, user's decisions)

Every comparison with "similar stocks" uses the **basic industry**. Where that has
too few stocks, **rank and Relative Strength fall back to the industry level**; the
broad sector is never used for a comparison (it put a shipbuilder against a
steel-tube maker). NSE's hierarchy is strictly nested, so a fallback never crosses
a sector.

| Comparison | Peers | Too few |
|---|---|---|
| Quality rank, the top-40% test (`sector_rank.py`) | basic industry with 5+ scored stocks, else industry | no rank (19 stocks) |
| Relative Strength peer percentile and peer median | basic industry with 5+ others with prices, else industry | part left out |
| Best alternative, "vs your holding" | basic industry only | "no holding in this industry": an industry-level match can again pair unrelated businesses |

Of 2,624 stocks 2,454 rank in their basic industry, 151 in their industry, 19 not at
all. Sector limits stay at sector level, because they are about concentration. The
"vs sector" Relative Strength part still uses NSE's sector index where one exists.
`scripts/recompute_relative_strength.py` recomputes that one score from stored prices.

## Phase E: Open in (2026-10-30)

A bar on every opened stock (`OpenInBar` in `CombinedScore.tsx`): Screener, NSE,
TradingView, Chartink, Trendlyne and MarketsMojo by direct address; BSE, Tickertape,
Moneycontrol and Tijori through a site-limited search, because their addresses need
an internal ID. MCA is left out: it blocks deep links.

**The cross-check column was not built.** Tickertape's scorecard API is unofficial and
its scores are locked behind its paid plan; Trendlyne's DVM needs its paid MCP. Reading
a paid score by polling an unofficial API across the universe is not something to
build on. With a Trendlyne subscription the same column could be added properly.

## Phase F: earnings revisions (2026-10-30)

`ingestion/estimate_revisions_client.py`, table `estimate_snapshots` (migration 0047).
Yahoo gives each consensus estimate as it stood 30 and 90 days ago, so revisions are
measurable at once rather than after months of our own snapshots; a dated snapshot is
kept each run anyway. Next year's estimate is read first (the current year goes blank
when a year rolls), a 0 counts as missing, and a move above 60% is left out as a split
or base reset.

**Earnings revisions are not in any score** (user's decision, 2026-10-30: they are
analysts' opinions, and external opinion does not enter a score here). They stay
"not measured" in the Quantitative Score. The stock page shows a context line: the
consensus EPS, its 90-day change, raised and cut counts, and the number of analysts.
First read: 865 stocks with estimates, 629 of them with three or more analysts.

    cd backend
    .venv/bin/python -m app.ingestion.estimate_revisions_client   # weekly

## Phase G: news breadth (2026-10-30)

`ingestion/news_feeds.py`, table `market_news`, run by the macro runner. Economic Times
and Mint RSS. A headline naming a listed company also gets a `company_news` row, so it
reaches the News tab and the report; the latest 15 show on the Market & Macro page.
Moneycontrol's RSS stopped in April 2024 and PIB's serve Hindi titles, so neither is
read. Feeds hold about a day, so the runner must run at least daily. Headlines feed no
score.


## Scheduled runs (2026-10-30)

Two `launchd` jobs, in `backend/scripts/scheduled/`:

| Job | When | Does |
|---|---|---|
| Daily | 20:30 every day | prices, then `app.macro.runner` (macro, FPI, news) |
| Weekly | Sunday 09:00 | SEBI orders, rating letters, decisions, estimates |

The project lives in `~/Downloads`, which macOS protects: a plain `launchd` shell job
fails with "can't open input file". So each job runs through a small app in
`~/Applications` (Screener Daily, Screener Weekly), which macOS asks once for access to
Downloads. Rebuilding an app makes it ask again.


## CANSLIM screen (2026-10-31)

`backend/app/canslim/`, `frontend/src/components/CanslimPage.tsx`, table `canslim_scores`
(migration 0048), route `/api/canslim/scores`. A separate read for every stock: it feeds
no framework score, gate or classification. Built from stored data only; the letter
rules are at the top of `canslim/score.py`.

Thresholds come from the user's CANSLIM notes, tightened with InCred Money's India guide.
Where they differ: L is computed as a real RS Rating ranked across every stock (the notes
listed it as a gap); I treats FII + DII above 70% as crowded, and 10-20% as fair; S uses
the 50-day average. CANSLIM averages the letters available and needs at least four.
Combined is 60% CANSLIM + 40% peer quality, the stock's Quality percentile among its peers.
The notes' reversal ranking was not built.
