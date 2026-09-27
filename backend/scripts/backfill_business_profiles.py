"""Resumable, paced backfill of Yahoo business profiles for every active stock.
Skips stocks already stored; re-run to fill gaps. `--refresh` re-fetches all."""
from __future__ import annotations

import sys
import time

from app.infrastructure.database.client import get_session_factory
from app.infrastructure.database.models import Stock, StockBusinessProfile
from app.pipeline.business_profile import fetch_profile, store_profile

PER_SEC = 2.0


def main() -> None:
    refresh = "--refresh" in sys.argv
    db = get_session_factory()()
    have = set() if refresh else {r[0] for r in db.query(StockBusinessProfile.stock_id).all()}
    todo = [s for s in db.query(Stock).filter(Stock.is_active == True).all() if s.id not in have]  # noqa: E712
    print(f"{len(todo)} to fetch", flush=True)
    backoff = 60.0
    for i, s in enumerate(todo, 1):
        try:
            data = fetch_profile(s)
            backoff = 60.0
            if data:
                store_profile(db, s.id, data)
        except Exception as e:  # noqa: BLE001
            db.rollback()
            if "429" in str(e) or "Too Many" in str(e):
                print(f"  throttled; pausing {backoff:.0f}s", flush=True)
                time.sleep(backoff)
                backoff = min(backoff * 2, 900)
            else:
                print(f"  {s.symbol}: {e}", flush=True)
        if i % 50 == 0:
            print(f"  {i}/{len(todo)}", flush=True)
        time.sleep(1.0 / PER_SEC)
    print("done", flush=True)


if __name__ == "__main__":
    main()
