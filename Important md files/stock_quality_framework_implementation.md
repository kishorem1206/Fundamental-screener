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
industry structure, regulatory risk.

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
