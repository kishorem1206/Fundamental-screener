"""Bulk jobs against NSE's MCP servers. See the package docstring.

    cd backend && .venv/bin/python -m app.nse_mcp.runner --actions [--symbols A,B] [--stale-days 30]
    cd backend && .venv/bin/python -m app.nse_mcp.runner --fill-prices
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import NseCorporateAction, PriceBar, Stock
from app.nse_mcp import corporate_actions, history


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--actions", action="store_true", help="read corporate actions for every active stock")
    ap.add_argument("--fill-prices", action="store_true", help="NSE price history for active stocks with none stored")
    ap.add_argument("--symbols", help="comma-separated symbols (default: every active stock)")
    ap.add_argument("--stale-days", type=float, default=30, help="skip stocks whose actions were read within this many days")
    a = ap.parse_args()
    db = get_db()
    try:
        q = db.query(Stock).filter(Stock.is_active.is_(True), Stock.exchange == "NSE")
        if a.symbols:
            q = q.filter(Stock.symbol.in_(a.symbols.split(",")))
        stocks = q.order_by(Stock.market_cap.desc().nullslast()).all()
        if a.actions:
            cutoff = datetime.now(timezone.utc) - timedelta(days=a.stale_days)
            fresh = {sid for sid, seen in db.query(NseCorporateAction.stock_id, func.max(NseCorporateAction.retrieved_at))
                     .group_by(NseCorporateAction.stock_id) if seen > cutoff}
            todo = [s for s in stocks if s.id not in fresh]
            total = errors = 0
            for i, s in enumerate(todo, 1):
                out = corporate_actions.ingest(db, s)
                total += out.get("actions", 0)
                errors += "error" in out
                if i % 50 == 0:
                    print(f"  ...{i}/{len(todo)} stocks, {total} actions, {errors} not answered", flush=True)
            print(f"ACTIONS DONE: {len(todo)} stocks read, {total} actions stored, {errors} not answered", flush=True)
        if a.fill_prices:
            have = {sid for (sid,) in db.query(PriceBar.stock_id).distinct()}
            for s in [s for s in stocks if s.id not in have]:
                print(f"  {s.symbol:<12} {history.fill(db, s)}", flush=True)
            print("PRICES DONE", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
