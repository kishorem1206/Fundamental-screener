"""Recompute only the Quantitative Score for every stock's latest row, from
stored data (no Screener reads, no other score touched), then refresh decisions.

    cd backend && .venv/bin/python -m scripts.recompute_quantitative
"""
from __future__ import annotations

from app.framework import price_stats, store
from app.framework.decisions import refresh_all
from app.framework.fundamental import LENDER_FRAMEWORKS
from app.framework.quantitative import compute_quantitative
from app.framework.screener_series import annual
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock


def main() -> None:
    db = get_db()
    try:
        active = {s.id for s in db.query(Stock.id).filter(Stock.is_active.is_(True))}
        rows = [r for r in store.latest_for_all(db) if r.stock_id in active]
        end = price_stats.as_of(db)
        changed = 0
        for i, row in enumerate(rows, 1):
            q = compute_quantitative(db, row.stock_id, annual(db, row.stock_id), row.sector_framework in LENDER_FRAMEWORKS, end)
            before = float(row.quantitative) if row.quantitative is not None else None
            row.quantitative = q["score"]
            row.detail = {**(row.detail or {}), "quantitative": q}
            changed += before != q["score"]
            if i % 200 == 0:
                db.commit()
                print(f"  ...{i}/{len(rows)} ({changed} changed)", flush=True)
        db.commit()
        print(f"QUANTITATIVE: {len(rows)} stocks, {changed} changed", flush=True)
        print("DECISIONS:", refresh_all(db), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
