#!/bin/zsh
# Sunday: SEBI orders and rating letters, decisions with the current flags, analysts'
# estimates, corporate actions, new IPO listings, then NSE's index lists.
JOB=weekly
source "$(dirname "$0")/_common.sh"
$PY -m app.risk.runner --sebi --read-orders --credit --months 2 --refresh-decisions
$PY -m app.ingestion.estimate_revisions_client
$PY -m app.nse_mcp.runner --actions
$PY -m scripts.update_ipo_universe
$PY -m scripts.refresh_nifty_lists
echo "=== $(date '+%Y-%m-%d %H:%M:%S') $JOB done"
