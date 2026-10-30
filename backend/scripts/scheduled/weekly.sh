#!/bin/zsh
# Sunday: SEBI orders and rating letters, decisions with the current flags, then
# analysts' estimates (about an hour).
JOB=weekly
source "$(dirname "$0")/_common.sh"
$PY -m app.risk.runner --sebi --read-orders --credit --months 2 --refresh-decisions
$PY -m app.ingestion.estimate_revisions_client
echo "=== $(date '+%Y-%m-%d %H:%M:%S') $JOB done"
