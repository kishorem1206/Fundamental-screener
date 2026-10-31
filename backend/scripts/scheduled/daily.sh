#!/bin/zsh
# Every evening: prices, the day-after results re-reads (Quick Screener, Combined Score
# and decisions for stocks that reported), price-based scores for every stock, CANSLIM,
# stages and convergence, macro, FPI and news, then full analyses for stocks whose new quarter has landed.
JOB=daily
source "$(dirname "$0")/_common.sh"
$PY -m app.prices.runner
$PY -m app.results.runner
$PY -m app.results.estimates
$PY -m scripts.refresh_price_scores
$PY -m app.canslim.runner
$PY -m app.stages.runner
$PY -m app.convergence.runner
$PY -m app.macro.runner
$PY -m app.results.full_analysis
echo "=== $(date '+%Y-%m-%d %H:%M:%S') $JOB done"
