"""Bulk jobs for the regulatory record and credit ratings.

    cd backend && .venv/bin/python -m app.risk.runner --sebi [--since 2021-10-01]
    cd backend && .venv/bin/python -m app.risk.runner --read-orders
    cd backend && .venv/bin/python -m app.risk.runner --credit [--months 15]
    cd backend && .venv/bin/python -m app.risk.runner --rematch
    cd backend && .venv/bin/python -m app.risk.runner --refresh-decisions

--sebi stops at the first page already stored, so a later run reads only
new orders. --refresh-decisions re-applies the classification to every
stock's latest scores with the current red flags (seconds; no re-scoring).
The Business Quality deduction and the Quality cap take effect the next time
a stock is scored.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

from app.infrastructure.database.client import get_db


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sebi", action="store_true", help="read SEBI's orders listing and match titles to companies")
    ap.add_argument("--since", default="2021-10-01", help="oldest order date to read (default 2021-10-01)")
    ap.add_argument("--full", action="store_true", help="with --sebi: do not stop at the first page already stored")
    ap.add_argument("--read-orders", action="store_true", help="open matched orders and read their outcome")
    ap.add_argument("--rematch", action="store_true", help="match every stored order title again")
    ap.add_argument("--credit", action="store_true", help="read credit rating letters filed with NSE")
    ap.add_argument("--reparse-credit", action="store_true", help="read every stored rating letter again")
    ap.add_argument("--months", type=int, default=15, help="with --credit: months back from today")
    ap.add_argument("--refresh-decisions", action="store_true", help="re-apply classifications with current red flags")
    a = ap.parse_args()
    db = get_db()
    try:
        if a.sebi:
            from app.risk import sebi_orders
            print("SEBI:", sebi_orders.ingest(db, date.fromisoformat(a.since), stop_at_known=not a.full), flush=True)
        if a.rematch:
            from app.risk import sebi_orders
            print("REMATCH:", sebi_orders.rematch(db), flush=True)
        if a.read_orders:
            from app.risk import sebi_orders
            print("ORDERS READ:", sebi_orders.read_outcomes(db), flush=True)
        if a.credit:
            from app.risk import credit_ratings
            start = date.today() - timedelta(days=int(a.months * 30.5))
            print("CREDIT:", credit_ratings.ingest(db, start, log=lambda m: print(m, flush=True)), flush=True)
        if a.reparse_credit:
            from app.risk import credit_ratings
            print("REPARSED:", credit_ratings.reparse(db, log=lambda m: print(m, flush=True)), flush=True)
        if a.refresh_decisions:
            from app.framework.decisions import refresh_all
            print("DECISIONS:", refresh_all(db), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
