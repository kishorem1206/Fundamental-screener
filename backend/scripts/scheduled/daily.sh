#!/bin/zsh
# Every evening, after NSE publishes the day's files: prices (India VIX and Nifty
# valuation on the Market & Macro page come from them), then macro, FPI and news.
JOB=daily
source "$(dirname "$0")/_common.sh"
$PY -m app.prices.runner
$PY -m app.macro.runner
echo "=== $(date '+%Y-%m-%d %H:%M:%S') $JOB done"
