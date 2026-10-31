# Investment Convergence: audit and plan

Written before any code changed, as the brief asks. The comparison and test results are at the end.

## 1. The main finding

The Combined Score page has **no combined score**. It shows six scores side by side and a rules-based decision. That was deliberate. The framework says the agent "must not make decisions using one score alone", and the page says the scores are "never averaged".

So there is no formula to preserve or fix. The plan adds a number without giving up that rule: **the combined score only ranks stocks. Gates alone decide the classification.** A high number cannot make a stock High Priority.

## 2. Audit

| Component | What exists | What is missing | Plan |
|---|---|---|---|
| Fundamental Score | `framework/fundamental.py`: growth, profitability, cash flow, balance sheet, efficiency, plus 20% new inputs, by sector weight. No valuation inside | Nothing | Reuse unchanged |
| Quality Score | `framework/quality.py`: 70% Fundamental + 30% Business Quality, capped at 49 on a governance red flag | Nothing | Reuse. It is the first dimension, because it already contains Fundamental |
| Technical Score | `framework/technical.py`: daily trend structure, 50- and 200-day averages, RSI, MACD, volume, breakout, base, reversal. No benchmark returns inside | No weekly stage | Reuse unchanged |
| Combined Score | `CombinedScore.tsx`, `/api/framework/scores`: six scores, no blend | A number to rank by, reward/risk, stage | Enhance this page. No new page |
| Decision engine | `framework/decision.py`: seven classifications, action, size | Stage, reward/risk | Keep unchanged. The new classification sits beside it |
| CANSLIM | `app/canslim`: 7 letters, separate page, feeds nothing | Nothing | Shown for reference only. Its letters repeat Fundamental (C, A), Relative Strength (N, L) and the market (M), so scoring it would double-count |
| Stage Analysis | `app/stages`: four stages, sub-stages, confidence, history | Not on this page | Read its results. The engine stays unchanged |
| Relative Strength | `framework/relative_strength.py`: against the **Nifty 50**, sector, peers, resilience, drawdown, near high | Nifty 500 windows, direction | Reuse the score. Add 1, 3, 6 and 12 month figures against the Nifty 500 as new display fields |
| Valuation | `framework/valuation.py`: P/E and P/B against own history and peers, PEG, EV/EBITDA, FCF yield, deep report value. Lenders use P/B | Margin of safety is only shown inside the components | Reuse unchanged. Show margin of safety where a deep report exists |
| Risk/Reward | **Nothing.** Only an exit rule for Tactical stocks in `decision.py` | All of it | New: `app/convergence/risk_reward.py` |
| Market direction | CANSLIM's M, Market & Macro page | Not on this page | One context line. It changes no score, because it would move every stock equally |
| History | `fw_scores` keeps one row per stock per day, but only 4 dates exist, and the daily price refresh overwrites the latest row | Stage, reward/risk, combined score, classification changes | New daily table. Read older dates from `fw_scores` and `stage_history` |

**Kept out, by earlier decisions of yours:** credit ratings (Editorial Report only), earnings revisions, FPI flows and macro. They will not enter the score, the gates or the written assessment.

## 3. Double-counting

| Overlap | Handling |
|---|---|
| Quality contains Fundamental | Only Quality is weighted. Fundamental is displayed |
| Technical and Stage both read trend, averages and volume | They share one dimension, so trend counts once |
| Stage conditions include relative strength | The Stage part uses only the stage label, not its RS conditions. RS counts in its own dimension |
| Relative Strength and Technical | No overlap: Technical holds no benchmark returns |
| Valuation and Fundamental | No overlap: Fundamental holds no valuation |
| Quantitative Score | Displayed, not weighted. It is not one of the five dimensions and it overlaps with Fundamental and Relative Strength |

## 4. Proposed formula, version 1.0

There is no existing formula to compare against. Every weight is configurable on the page.

| Dimension | Weight | Source | Status |
|---|---:|---|---|
| Fundamental Quality | 35% | Quality Score | Existing |
| Technical Stage | 25% | 60% Technical + 40% stage fit | Enhanced |
| Relative Strength | 15% | Relative Strength Score | Existing |
| Valuation | 15% | Valuation Score | Existing |
| Risk/Reward | 10% | Reward/risk ratio mapped to 0-100 | New |

**Why these weights:** they follow the framework's order, quality first. Risk/Reward is lowest because it is new and untested.

**Stage fit:** Established 90, Early 85, Late 65, Weakening 50, Stage 1 50, Stage 3 30, Stage 4 10. An unclassified stock has no stage fit, so the dimension falls back to Technical alone.

A dimension with no data is dropped and the rest are reweighted. Below 70% of the weight, there is no combined score.

## 5. Reward/risk

Everything is calculated from stored prices. It is a rule of thumb, not a forecast.

- **Invalidation:** the nearest structural level at least 5% under the price: last daily swing low, 3% under the 30-week average, or the 20-week low.
- **Target:** the 30-week average if the price is under it. Otherwise the 52-week high if that is 5%+ above. Otherwise a measured move: the 20-week range added on top.
- **Entry zone:** Stage 2, a pullback between the 30- and 10-week averages. Stage 1, just above resistance. Stages 3 and 4 have none.
- **Ratio:** upside ÷ downside from the current price.

## 6. Classification

Checked in this order. The number decides nothing until the gates pass.

| Class | Rule |
|---|---|
| Not Rated | No Quality, no combined score, or the stock stopped trading |
| Low Priority | Fails the core gate on a red flag, or Quality under 40 |
| Watchlist or Low Priority | Quality 40-49: Watchlist only if in healthy Stage 2 |
| Caution | Stage 3 or Stage 4, even with strong Quality |
| Early Opportunity | Early Stage 2, or Stage 1 on transition watch, and reward/risk not poor |
| High Priority | Established Stage 2, Quality 65+, combined 70+, reward/risk 2+, valuation Fair or Cheap, RS 60+ and improving, Quality not declining, confidence not Low |
| Strong Candidate | Stage 2, not Weakening, combined 60+, reward/risk 1.5+ |
| Watchlist | Everything else that passes the core gate |

**Warnings** that do not change the class on their own: Expensive valuation, Quality declining, Late Stage 2.

**Confidence** starts at 100 and falls for missing dimensions, thin fundamental coverage, a new result not yet read, an open week and a low-confidence stage.

## 7. What stays unchanged

The six scores and their formulas, the seven decision classes, `fw_scores`, the Stage engine, CANSLIM and every existing API field. All additions are new tables and new fields. The method is versioned, and each row records its version.

## 8. Results after building

Run on 31 Oct 2026, prices to 30 Oct, method 1.0. Code: `backend/app/convergence/`, `frontend/src/components/ConvergencePanel.tsx`, `CombinedScore.tsx`, `backend/app/routes/framework.py`. Tables: `convergence_scores`, `convergence_history`, `convergence_settings` (migration 0053).

| Class | Stocks |
|---|---:|
| High Priority | 1 |
| Strong Candidate | 71 |
| Early Opportunity | 54 |
| Watchlist | 822 |
| Caution | 566 |
| Low Priority | 808 |
| Not Rated | 302 |

Not Rated: 278 have too little data, mostly recent listings; 24 have stopped trading.

Two rules were tightened after reading real stocks. "Not Expensive" passed stocks with no valuation at all, so High Priority now needs Fair or Cheap. It also now needs relative strength improving, as the brief's objective says. Together they took High Priority from 4 stocks to 1. The market is in correction, so a very short list is expected.

### Old against new

- **Ranking:** the rank correlation between Quality and Combined is 0.69. Only 6 of the top 50 stocks by Quality are in the top 50 by Combined. Combined is a different ranking, not a refinement of the old one.
- **The two classifications can disagree.** The decision engine does not read the stage. Of 516 Core Quality stocks with an add action, 214 are now Caution (Stage 3 or 4) and 214 Watchlist. Infosys reads Core Quality, Add gradually, and also Caution, Stage 4. This is left in place so nothing existing changes. Whether the action should respect the stage is the user's decision.

| Stock | Quality | Combined | Class | Stage | Decision |
|---|---:|---:|---|---|---|
| Coforge | 84.4 | 77.2 | Early Opportunity | Early Stage 2 | Core Quality, Add gradually |
| Trent | 76.6 | 72.2 | Strong Candidate | Established Stage 2 | Core Quality, Add gradually |
| Adani Ports | 69.9 | 72.0 | Strong Candidate | Established Stage 2 | Investable, Hold |
| TCS | 81.7 | 68.0 | Watchlist | Stage 1 | Core Quality, Add gradually |
| Infosys | 83.3 | 67.1 | Caution | Stage 4 | Core Quality, Add gradually |
| Bajaj Finance | 87.4 | 56.4 | Caution | Stage 3 | Core Quality, Add on confirmation |
| HDFC Bank | 74.2 | 51.0 | Caution | Stage 4 | Core Quality, Add on confirmation |
| Reliance | 66.4 | 49.9 | Caution | Stage 4 | Core Quality, Add on confirmation |

### Historical test

The method **cannot be properly tested yet**. `fw_scores` holds only four dates, so there is one usable start date. This is the 6 Oct stored scores with the stage at the 2 Oct close, measured to 30 Oct against the Nifty 500, which rose 0.2%. Most stocks lagged badly in that window.

| Class | Stocks | Mean, points | Median, points | Beat the index |
|---|---:|---:|---:|---:|
| High Priority | 3 | +1.3 | -1.0 | 33% |
| Strong Candidate | 92 | -3.4 | -5.2 | 38% |
| Caution | 519 | -4.8 | -5.1 | 22% |
| Low Priority | 761 | -6.1 | -6.6 | 20% |
| Watchlist | 832 | -6.3 | -6.6 | 21% |
| Early Opportunity | 90 | -6.4 | -8.1 | 19% |

One four-week window is not evidence, and three stocks prove nothing. Strong Candidate did better than the broad classes, and Early Opportunity did worst, in line with the Stage Screener's finding on fresh Stage 1 to 2 moves. The weights have not been tuned to this. `convergence_history` now records every day, so a real test becomes possible as it builds.

### Limits

- Reward/risk uses chart levels and has never been tested on its own.
- Stage 4 stocks can show a high ratio, because the 30-week average is far above the price. The gates keep them out.
- No gate checks liquidity, so small, thinly traded stocks can qualify.
- History before 31 Oct has no reward/risk, combined score or class.
- Changing the weights rebuilds today's read only. Earlier days keep the version they were recorded with.
