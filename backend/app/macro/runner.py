"""Bring every macro and FPI series up to date.

    cd backend && .venv/bin/python -m app.macro.runner              # daily
    cd backend && .venv/bin/python -m app.macro.runner --history    # first fill: FPI by month and sector, five years of global series

RBI's page keeps no history, so rates, the dollar rate and the G-sec yield
start from the first run; run this daily to build them up.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

from app.infrastructure.database.client import get_db


def _step(name: str, fn):
    try:
        print(f"{name}:", fn(), flush=True)
    except Exception as exc:  # noqa: BLE001 — one source down must not stop the others
        print(f"{name}: FAILED {str(exc)[:160]}", flush=True)


def refresh(db, history: bool = False) -> None:
    from app.bie.macro import ingest_macro
    from app.ingestion import news_feeds
    from app.macro import fpi, sources

    since = date.today() - timedelta(days=(5 * 366 if history else 30))
    _step("MoSPI", lambda: sources.ingest_mospi(db))
    _step("RBI", lambda: sources.ingest_rbi(db))
    _step("CCIL and IMF", lambda: ingest_macro(db))
    _step("Index file", lambda: sources.ingest_indices(db))
    _step("CBOE", lambda: sources.ingest_cboe(db, since))
    _step("Yahoo", lambda: sources.ingest_yahoo(db, since))
    _step("World Bank", lambda: sources.ingest_world_bank(db))
    _step("FPI daily", lambda: fpi.ingest_daily(db))
    _step("FPI by month", lambda: fpi.ingest_yearly(db, 5 if history else 1))
    _step("FPI by sector", lambda: fpi.ingest_sectors(db, 72 if history else 4))
    _step("News feeds", lambda: news_feeds.ingest(db))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", action="store_true", help="first fill")
    a = ap.parse_args()
    db = get_db()
    try:
        refresh(db, a.history)
    finally:
        db.close()


if __name__ == "__main__":
    main()
