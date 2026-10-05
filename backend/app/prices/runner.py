"""Fill and refresh the price store.

    cd backend && .venv/bin/python -m app.prices.runner              # daily update: new days only
    cd backend && .venv/bin/python -m app.prices.runner --years 3    # first fill / full re-read
    cd backend && .venv/bin/python -m app.prices.runner --check      # compare stored closes with NSE's bhavcopy

Safe to re-run: every write is an upsert, and days already stored are skipped.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock
from app.prices import nse_bhavcopy, nse_indices, store, yahoo


def run(years: int | None = None, symbols: list[str] | None = None, indices: bool = True, stocks: bool = True) -> dict:
    db = get_db()
    try:
        out: dict = {}
        if indices:
            have = store.index_dates(db)
            since = date.today() - timedelta(days=365 * (years or 3) + 10) if years or not have else max(have) - timedelta(days=7)
            out["indices"] = nse_indices.ingest(db, since)
        if stocks:
            q = db.query(Stock).filter(Stock.is_active.is_(True))
            if symbols:
                q = q.filter(Stock.symbol.in_(symbols))
            universe = q.order_by(Stock.market_cap.desc().nullslast()).all()
            progress = lambda done, empty: print(f"  stocks stored {done}, no data {empty}", flush=True)
            out["stocks"] = yahoo.backfill(db, universe, years=years, on_batch=progress) if years else yahoo.update(db, universe)
        out["coverage"] = store.coverage(db)
        return out
    finally:
        db.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, help="re-read this many years of history instead of only the new days")
    ap.add_argument("--symbols", help="comma-separated NSE symbols (default: every active stock)")
    ap.add_argument("--no-indices", action="store_true")
    ap.add_argument("--no-stocks", action="store_true")
    ap.add_argument("--check", action="store_true", help="only compare stored closes with NSE's official bhavcopy")
    a = ap.parse_args()
    if a.check:
        db = get_db()
        try:
            result = nse_bhavcopy.compare(db)
        finally:
            db.close()
    else:
        result = run(a.years, a.symbols.split(",") if a.symbols else None, not a.no_indices, not a.no_stocks)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
