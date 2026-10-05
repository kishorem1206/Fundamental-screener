"""Weekly IPO universe refresh — entry point for the launchd job
(see HOW_TO_RUN.md's "Recent IPOs" section for the install command).

1. Re-fetches NSE's full public-issue archive + currently-open issues into
   `fa_ipo_issues` (every security type — see nse_ipo_client.py).
2. Promotes any mainboard (EQ/BE) issue listed within `--recent-months` of
   today into the `stocks` universe if it isn't there yet, and Yahoo-only
   quick-scores it.

Idempotent and safe to re-run any time: `ingest_ipo_issues` upserts by
(symbol, issue_start_date), and `promote_recent_ipos` only creates a
`stocks` row when one doesn't already exist (existing stocks just get
their `ipo_listing_date` backfilled and re-quick-scored).

    cd backend && .venv/bin/python -m scripts.update_ipo_universe
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.database.client import get_session_factory  # noqa: E402
from app.ingestion.nse_ipo_client import ingest_ipo_issues, promote_recent_ipos  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recent-months", type=int, default=24,
                    help="promote issues listed within this many months of today (default: 24)")
    args = ap.parse_args()

    db = get_session_factory()()
    print(f"[{date.today().isoformat()}] fetching NSE IPO issue archive...", flush=True)
    fetch_result = ingest_ipo_issues(db)
    db.commit()
    print(f"  {fetch_result}", flush=True)

    since = date.today() - timedelta(days=args.recent_months * 30)
    print(f"promoting mainboard issues listed since {since.isoformat()}...", flush=True)
    promote_result = promote_recent_ipos(db, since=since)
    print(f"  {promote_result}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
