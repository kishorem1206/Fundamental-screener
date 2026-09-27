# Quick analysis (Yahoo Finance only)

A standalone package beside the full 20-stage pipeline. Nothing existing was
modified; it imports the same `compute_metrics`, `get_framework` and
`compute_scores`, so score differences come only from inputs, never formulas.

    python -m app.quick_analysis.fidelity                 # how close is it to the full pipeline?
    python -m app.quick_analysis.runner --limit 40        # score stocks live (paced, resumable)
    python -m app.quick_analysis.runner --csv out.csv     # whole universe (see "Yahoo rate limit")

## What was verified (2026-09-24)

**Consolidated only.** Yahoo's Indian statements are consolidated. Checked
against the Screener ledger for 18 analysed companies: wherever standalone and
consolidated revenue differ, Yahoo matches consolidated (Tanla: Yahoo 4,418 Cr
= consolidated 4,418; standalone 744). Standalone-only companies (Kross, GPT
Healthcare, Netweb) match their only statement. Two apparent misses are
definition differences, not statement type: Bajaj Finance (Yahoo revenue is
net of interest expense) and Pine Labs (0.88x).

**Sector handling.** The six scores use four scoring families (bank /
NBFC+insurance / fintech / everything else) plus one weight table per
framework. Sector `key_metrics` frameworks feed a separate `sector_score`, not
the six scores. The quick path calls the identical `get_framework()`: routing
matched the full pipeline for 18/18. The 1,610-stock universe routes to 36
frameworks; 81 "Generic" stocks use universal weights, as in the full pipeline.

## Fidelity vs the full pipeline (18 analysed companies)

The full pipeline = Yahoo metrics -> Screener overrides -> scores -> refinement
(+/-10 on profitability / balance sheet / cash flow from three engines that
read the Screener ledger). Error was split by cause:

| stage                                   | overall MAE | bias | max  | rank rho | same rating band | top-6 |
|-----------------------------------------|-------------|------|------|----------|------------------|-------|
| raw Yahoo-only                          | 3.3         | +3.0 | 5.3  | 0.97     | 12/18            | 6/6   |
| **+ approximated refinement (shipped)** | **1.6**     | +0.6 | 3.3  | **0.98** | 14/18            | 6/6   |

Per category (MAE vs the full final score, approximated): growth 2.6,
profitability 4.0, cash flow 5.1, balance sheet 1.3, efficiency 5.7,
valuation 2.9. All 18 companies are within 5 overall points.

* Missing Screener overrides cost little (cash flow 0.2, balance sheet 0.6 on
  the pre-refinement scores).
* Refinement was the main gap. The balance-sheet engine is an archetype label
  (STRONG/MIDDLE/WEAK) minus a flag penalty and is reproduced almost exactly
  (16/18 adjustments identical). Cash flow is looser.
* A leave-one-out profitability shift made results WORSE and was dropped.

## Known limits

* **Profitability** is unrefined: the P&L master score needs sector-peer margin
  percentiles. Once the universe is scored, peer percentiles computed from the
  quick scores themselves are the natural substitute (not built yet).
* **Efficiency** runs ~5.7 high: Screener's debtor/inventory days override
  Yahoo-derived ones in the full pipeline. A constant shift would fit the
  sample but isn't principled; left as is.
* **Calibrated constants**, fitted on 18 companies: `ASSUMED_BS_FLAG_PENALTY`
  (3.0) and `ASSUMED_CF_TRIGGERED_FLAGS` (2, deliberately below the best fit of
  4). Recalibrate as more full analyses accumulate.
* Yahoo has no long-term-investments line, so "STRONG" balance sheets are
  under-detected. Yahoo gives 4-5 fiscal years vs the ledger's ~12.
* Financial firms that route to "Generic" (asset managers, brokers) get
  industrial scoring, same as the full pipeline: parity, not correctness.
* Rating bands flip when a score sits within ~2 points of a boundary.

## Yahoo rate limit (important)

Yahoo throttles by IP. An unpaced 8-worker run scored 24 stocks in 5s (0.2s
each) but was cut off after ~322 stocks (~7 Yahoo calls each). The runner now
paces fetches (`--rate`, default 1.5 stocks/s), pauses ALL workers with
exponential backoff (60s -> 15min) on any 429, retries, and is resumable
(successes are cached 24h in Redis; failures are not). While throttled, the
full pipeline's own Yahoo stage on this machine will also fail.
