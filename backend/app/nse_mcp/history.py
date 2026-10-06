"""Daily price history from NSE's bhavcopy server for stocks the price store
has nothing on (Yahoo does not carry them: SME listings, recent listings).

NSE's prices are unadjusted, so they are adjusted here with NSE's own
corporate actions: `close` for splits and bonuses, `adj_close` also for
dividends (each earlier price scaled by (previous close − dividend) /
previous close) — the same two series Yahoo provides for every other stock.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.infrastructure.database.models import NseCorporateAction, Stock
from app.nse_mcp import corporate_actions
from app.nse_mcp.client import NseMcpError, bhavcopy
from app.prices import store

SOURCE = "NSE"


def fetch_raw(symbol: str, since: date) -> list[dict]:
    """Unadjusted bars, oldest first, back to `since` (three months per call)."""
    out, end = [], "today"
    for _ in range(40):
        try:
            chunk = bhavcopy.call("get_stock_history", symbol=symbol, months=3, endDate=end)
        except Exception:  # noqa: BLE001 — keep what was read so far
            break
        rows = chunk.get("data", []) if isinstance(chunk, dict) else []
        if not rows:
            break
        out.extend(rows)
        nxt = chunk.get("next_end_date")
        if not nxt or date.fromisoformat(nxt) < since:
            break
        end = nxt
    seen, bars = set(), []
    for r in sorted(out, key=lambda r: r["date"]):
        if r["date"] not in seen and date.fromisoformat(r["date"]) >= since and (r.get("close") or 0) > 0:
            seen.add(r["date"])
            bars.append(r)
    return bars


def adjust(stock_id: str, raw: list[dict], actions: list[NseCorporateAction]) -> list[dict]:
    """Rows for `price_bars_daily`, adjusted backwards from the latest bar."""
    changes = {a.ex_date: float(a.adjustment_factor) for a in corporate_actions.share_changes(actions)}
    dividends: dict[date, float] = {}
    for a in actions:
        if a.dividend_per_share is not None:
            dividends[a.ex_date] = dividends.get(a.ex_date, 0.0) + float(a.dividend_per_share)
    rows, split_factor, total_factor = [], 1.0, 1.0
    for i in range(len(raw) - 1, -1, -1):  # newest to oldest
        r = raw[i]
        day = date.fromisoformat(r["date"])
        rows.append({
            "stock_id": stock_id, "bar_date": day,
            "open": r.get("open") and r["open"] * split_factor, "high": r.get("high") and r["high"] * split_factor,
            "low": r.get("low") and r["low"] * split_factor, "close": r["close"] * split_factor,
            "adj_close": r["close"] * total_factor,
            "volume": int(r["volume"] / split_factor) if r.get("volume") else None, "source": SOURCE,
        })
        # an action with this ex-date applies to every earlier bar
        if day in changes:
            split_factor *= changes[day]
            total_factor *= changes[day]
        if day in dividends and i > 0:
            prev = raw[i - 1]["close"]
            if prev > dividends[day] > 0:
                total_factor *= (prev - dividends[day]) / prev
    return list(reversed(rows))


def fill(db: Session, stock: Stock, years: int = 3) -> dict:
    """Replaces the stock's stored history with NSE's. Never raises."""
    if not corporate_actions.for_stock(db, stock.id):
        corporate_actions.ingest(db, stock)
    raw = fetch_raw(stock.symbol, date.today() - timedelta(days=365 * years + 10))
    if not raw:
        return {"bars": 0, "reason": "NSE's server has no history for this symbol"}
    rows = adjust(stock.id, raw, corporate_actions.for_stock(db, stock.id))
    store.replace_price_history(db, stock.id, rows)
    db.commit()
    return {"bars": len(rows), "from": raw[0]["date"], "to": raw[-1]["date"], "series": raw[-1].get("series")}
