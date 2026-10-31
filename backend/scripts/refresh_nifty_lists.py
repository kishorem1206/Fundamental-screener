"""Refresh NSE's index constituent lists (Nifty 500 and the rest), for the
technical screener. NSE reviews them twice a year; a
run with no change writes nothing new.

    cd backend && .venv/bin/python -m scripts.refresh_nifty_lists
"""
from __future__ import annotations

from app.technical.services.nifty_index_ingestion_service import nifty_index_ingestion_service


def main() -> None:
    print("NIFTY LISTS:", {k: v for k, v in nifty_index_ingestion_service.ingest().items() if not isinstance(v, (list, dict))}, flush=True)


if __name__ == "__main__":
    main()
