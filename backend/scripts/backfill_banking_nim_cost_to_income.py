"""One-off backfill: NIM + Cost-to-Income Ratio for every Bank/NBFC/Housing
Finance/Microfinance/Gold Loans stock, via the new Investor-Presentation-
cascade extraction (quarterly_operating_metrics_ingestion.py's "banking"
prompt, 2026-09-27) — the pilot BSE-OCR path (banking_ingestion.py) only
ever covered ~9 companies; this is a second, much broader-coverage source
for the same two metric keys.

Resumable: skips a company if it already has a `nim` or `cost_to_income_ratio`
row from this run's source (NSE_INVESTOR_PRESENTATION/NSE_RESULTS_PRESS_RELEASE/
NSE_CONCALL) less than `--skip-fresher-than-hours` old. Re-run to pick up
companies that failed (no usable filing, sparse deck, etc.) on a prior pass.

    cd backend && .venv/bin/python -m scripts.backfill_banking_nim_cost_to_income
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.database.client import get_session_factory  # noqa: E402
from app.infrastructure.database.models import Stock  # noqa: E402
from app.ingestion.quarterly_operating_metrics_ingestion import ingest_quarterly_operating_metrics  # noqa: E402
from app.sectors.registry import get_framework  # noqa: E402

_TARGET_SECTORS = ("Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans")
_FRESH_SOURCES = ("NSE_INVESTOR_PRESENTATION", "NSE_RESULTS_PRESS_RELEASE", "NSE_CONCALL")


def _already_fresh(db, company_id: str, cutoff: datetime) -> bool:
    from sqlalchemy import text
    row = db.execute(
        text(
            "select 1 from fa_metric_data_points where company_id=:cid "
            "and metric_key in ('nim','cost_to_income_ratio') and source = ANY(:sources) "
            "and source_date >= :cutoff limit 1"
        ),
        {"cid": company_id, "sources": list(_FRESH_SOURCES), "cutoff": cutoff},
    ).first()
    return row is not None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between companies")
    ap.add_argument("--skip-fresher-than-hours", type=float, default=24.0)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    db = get_session_factory()()
    stocks = db.query(Stock).filter(Stock.is_active.is_(True)).all()
    targets = []
    for s in stocks:
        fw = get_framework(s.sector, industry=s.industry, basic_industry=s.basic_industry)
        if fw.sector_name in _TARGET_SECTORS:
            targets.append((s, fw.sector_name))
    if args.limit:
        targets = targets[: args.limit]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.skip_fresher_than_hours)
    print(f"{len(targets)} financial-sector stocks in universe", flush=True)

    done = skipped = failed = got_nim = got_cti = 0
    for i, (stock, sector_name) in enumerate(targets, 1):
        if _already_fresh(db, stock.id, cutoff):
            skipped += 1
            continue
        try:
            rows = ingest_quarterly_operating_metrics(db, company_id=stock.id, symbol=stock.symbol, sector_name=sector_name)
            db.commit()
            by_key = {r.metric_key for r in rows}
            if "nim" in by_key:
                got_nim += 1
            if "cost_to_income_ratio" in by_key:
                got_cti += 1
            done += 1
            print(f"[{i}/{len(targets)}] {stock.symbol} ({sector_name}): {sorted(by_key) or 'nothing found'}", flush=True)
        except Exception as e:  # noqa: BLE001 — one bad company must never stop the batch
            db.rollback()
            failed += 1
            print(f"[{i}/{len(targets)}] {stock.symbol}: ERROR {type(e).__name__}: {e}", flush=True)
        time.sleep(args.delay)

    print(f"done: {done} processed, {skipped} already fresh, {failed} errored | "
          f"nim found for {got_nim}, cost_to_income for {got_cti}", flush=True)


if __name__ == "__main__":
    main()
