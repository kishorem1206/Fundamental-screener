# Stage Screener: method, data and test results

The Stage Screener classifies every active stock with prices into one of Stan Weinstein's four stages from weekly prices. It is rules only, with no model. It reads no other score and feeds none. `stage_scores.stock_id` is the join key for any later Quality + Stage + Valuation screen.

Code: `backend/app/stages/`, `backend/app/routes/stages.py`, `frontend/src/components/StageScreener.tsx`, `StageDetail.tsx`, `StageChart.tsx`.

## What it reuses

| Need | Existing source |
|---|---|
| Universe | `stocks`: every active stock with stored prices |
| Prices | `price_bars_daily`: adjusted daily bars from 2023-09-26, about 160 weeks |
| Benchmark | `index_bars_daily`, Nifty 500, for every stock |
| EMA for MACD | The technical screener's `_ema_series` |
| Schedule | The daily launchd job, after CANSLIM |

The universe was the Nifty 500 at first and was widened to all stocks at the user's request on 31 Oct 2026.

New tables (migration 0052): `stage_scores` (latest, with conditions), `stage_history` (one row a stock a week), `stage_thresholds` (overrides), `stage_watchlist`. Stage changes are read from `stage_history`, so they need no table of their own.

## Weekly data

- A week runs Monday to Friday and is keyed by its Friday. It stays provisional until Friday's close.
- Open, high and low are scaled by adj_close / close, so a split leaves no false gap.
- Volume is compared as average daily volume, so a holiday week or an unfinished week is fair.
- Relative strength is Mansfield RS: stock ÷ Nifty 500, as a % above or below its own 52-week average. It needs 30 weeks.

## Classification

Each week is read in order and sees only that week and earlier.

1. **Is the stage possible?** This uses the 30-week average's direction, which side of it the price is on, and what came before. Stage 1 must follow a decline; Stage 3 must follow an advance.
2. **Confidence** is the weight of that stage's conditions that are met, out of those that could be read. Missing data drops a condition; it never counts as failed.
3. **Stability.** A running stage holds unless a rival beats it by 10 points, and a change must hold 2 weeks in a row. Only a breakout on volume into Stage 2 counts at once.
4. **Unclassified** when a stock has under 35 weeks of prices, no possible stage, a best confidence under 50, or no trade for 10 days.

| Stage | Conditions and weights |
|---|---|
| 1 Basing | Flat 30W average 25, follows a decline 20, defined range 20, no new low lately 15, volatility contracted 10, close near the average 10 |
| 2 Advancing | Close above the average 20, average rising 20, higher highs and lows 15, 10W above 30W 10, RS positive 10, RS improving 10, up weeks heavier 10, MACD above signal 5 |
| 3 Topping | Average flattened 20, follows an advance 20, range near the highs 15, RS weakening 15, failed new highs 10, down weeks heavier 10, close near the average 10 |
| 4 Declining | Mirror of Stage 2 |

Every threshold is in `app/stages/settings.py` and can be changed on the page.

**Stage 2 sub-stages,** checked in this order:
- Weakening: RS falling, and below the 10-week average or RS negative.
- Late: 30%+ above the 30-week average, or fading momentum after week 12.
- Early: within 12 weeks of coming from Stage 1 or Stage 4.
- Established: the rest.

**Stage 2 Opportunities:** Stage 2, above a rising average, RS improving, up weeks heavier, not Weakening. Stocks within 10% of the 52-week high or with a breakout in the last 8 weeks rank first.

**Transition watch:** 4 of the 5 checks for a stock's next stage.

## Test results

Run on 31 Oct 2026. Every week was classified from that week and earlier only, across all 2,613 stocks rather than only today's Nifty 500, so stocks that fell out of the index are included. Delisted stocks are still missing. The window is about two years, so these results are one market period, not a long-run record.

**Stability.** Before the stability rules, 28% of stages lasted 2 weeks or less. After, 11% do, and the median is 8 weeks.

**Return over the Nifty 500 in the next 13 weeks:**

| Group | Mean | Median | Beat the index |
|---|---:|---:|---:|
| Stage 1 | -0.5 | -4.9 | 36% |
| Stage 2 | +1.5 | -2.8 | 44% |
| Stage 3 | -0.2 | -2.7 | 43% |
| Stage 4 | +0.8 | -2.2 | 44% |
| Opportunity near a high | +3.3 | -0.8 | 48% |
| Opportunity, not near a high | -0.3 | -6.1 | 37% |
| Fresh Stage 1 → 2 entry | -0.9 | -5.5 | 38% |
| Fresh Stage 2 → 3 entry | -1.3 | -4.5 | 39% |

**What this means:**
- A stage describes a stock's trend. On this data it is a weak predictor of the next 13 weeks.
- Being near a high was the strongest thing tested, so those stocks rank first in Opportunities.
- A fresh Stage 1 → 2 entry did not beat the index in this window. Treat it as a stock to study, not a signal to buy.
- Limited to today's Nifty 500, Stage 4 looks better than Stage 2. That is survivorship bias: the stocks that fell the most are no longer in the index.
- The rules were not tuned to improve these numbers, which would only fit this one period.

Real timelines were read for BEL, ITC, Adani Ports, Reliance, Trent and Coforge. Long trends read correctly. Known weakness: the 30-week average lags, so a sharp rebound can stay in Stage 1 or 3 for weeks while the price rises (Coforge in 2025), and a choppy stock can still swap between Stage 1 and 4 (Trent in 2025).

## Limits

- Recent listings need 35 weeks of prices. Stocks with no stored prices are left out.
- 160 weeks of prices, so the first 34 weeks of each stock have no stage, and the first stage has no earlier stage to follow.
- Adjusted prices are restated on a split or dividend, so history is replayed on every run. Changing a threshold also rewrites past stages.
- Stage 3 is the hardest to read, and it has the lowest confidence on average.
