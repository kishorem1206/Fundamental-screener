"""Screener consolidated-quarterly fallback for quick analysis's quarterly
growth score (2026-09-28, explicit user request) — used only when Yahoo's
own quarterly data (`quick_analysis/quarterly_growth.py`) comes back empty
or insufficient (fewer than 5 real quarters, or the WeWork-shaped gap where
the current quarter's year-ago base is missing). CONSOLIDATED only, by
explicit scope — no standalone fallback here, and if Screener doesn't have
enough quarters either, this returns None and the caller is left with no
quarterly growth score at all (annual-only), exactly as if Yahoo alone had
been tried.

DB-first, ingest-on-miss (2026-09-28 follow-up correction — the first
version of this module fetched Screener live on every call, every scan;
the user pointed out that's needlessly slow on a repeat scan). Reads the
`qtr_*` ledger first (`app.calculations.quarterly_growth.compute_quarterly_growth()`
— the SAME function the full pipeline uses); only on a genuine miss does it
call `quarterly_results_client.py::ingest_quarterly_results()` (the
existing, already-tested Screener ingestion path — persists to
`fa_metric_data_points`, both statement types, same as a full analysis
would) and then re-read from the now-populated ledger. A later manual
re-scan of the same company finds the ledger already populated and never
re-fetches Screener at all, until the whole scoring run is re-triggered."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.quarterly_growth import compute_quarterly_growth as _compute_from_ledger
from app.logger import logger


def compute_quarterly_growth_from_screener(db: Session, company_id: str, symbol: str, screener_pacer=None) -> dict | None:
    """None on any fetch failure or insufficient data (from the ledger OR
    from a fresh Screener ingest) — never raises. Commits after a fresh
    ingest (matching every other ingestion call site's convention); rolls
    back and returns None if the ingest itself fails.

    `screener_pacer` (optional — an `app.quick_analysis.runner._Pacer`
    instance, shared across a bulk run's worker threads): paces the ingest
    call below. Real 429s confirmed live 2026-09-29 without this — a
    `--force` full rescore fires this fallback for nearly every company,
    and 4 worker threads hitting Screener with no shared pacing is the
    exact failure mode the Yahoo-side `_Pacer` already exists to prevent."""
    result = _compute_from_ledger(db, company_id, statement_type="CONSOLIDATED", allow_fallback=False)
    if result is not None:
        return result

    if screener_pacer is not None:
        screener_pacer.wait_turn()
    try:
        from app.ingestion.quarterly_results_client import ingest_quarterly_results
        ingest_quarterly_results(db, company_id=company_id, symbol=symbol)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("quick_analysis: Screener quarterly fallback ingest failed", symbol=symbol, error=str(e))
        return None

    return _compute_from_ledger(db, company_id, statement_type="CONSOLIDATED", allow_fallback=False)
