"""NSE corporate actions: store them, and answer the two questions the
Fundamental Score asks — which financial years had a split or bonus (so a
jump in the share count is not mistaken for dilution), and what dividend per
share was paid over the last twelve months on today's share base."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import NseCorporateAction, Stock
from app.nse_mcp.client import NseMcpError, bhavcopy

_RUPEES = re.compile(r"R[se]\.?\s*([0-9]+(?:\.[0-9]+)?)\s*/?-?\s*Per\s+Sh", re.I)
YEARS = 5


def dividend_in(purpose: str) -> float | None:
    """Rupees per share named in NSE's purpose text; several dividends on one line are added."""
    if "dividend" not in purpose.lower():
        return None
    amounts = [float(x) for x in _RUPEES.findall(purpose)]
    return round(sum(amounts), 4) if amounts else None


_BONUS = re.compile(r"bonus\D{0,12}(\d+)\s*:\s*(\d+)", re.I)
_SPLIT = re.compile(r"from\s+R[se]\.?\s*([0-9.]+)\s*/?-?.*?to\s+R[se]\.?\s*([0-9.]+)", re.I | re.S)


def classify(purpose: str) -> tuple[str, float]:
    """(action type, adjustment factor) from NSE's purpose text. "Bonus 1:1"
    is one new share for each held, so earlier prices halve (0.5); a split
    "From Rs 10 To Rs 2" leaves a fifth (0.2)."""
    text = purpose.lower()
    m = _BONUS.search(purpose)
    if m and "bonus" in text and "debenture" not in text and "ncrps" not in text:
        new, held = float(m.group(1)), float(m.group(2))
        if new > 0 and held > 0:
            return "BONUS", held / (new + held)
    m = _SPLIT.search(purpose)
    if m and any(w in text for w in ("split", "sub-division", "subdivision", "consolidation")):
        old, new = float(m.group(1)), float(m.group(2))
        if old > 0 and new > 0 and old != new:
            return "SPLIT", new / old
    return ("DIVIDEND" if dividend_in(purpose) is not None else "OTHER"), 1.0


_website = None


def _from_website(symbol: str, since: date, today: date) -> list[dict]:
    """NSE's own corporate-actions feed (the source NSE's MCP tool also reads),
    through the paced NSE session the deep report uses."""
    global _website
    from urllib.parse import quote

    from app.bie.nse_filings import NseFilings

    if _website is None:
        _website = NseFilings()
    rows = _website._json(f"corporates-corporateActions?index=equities&symbol={quote(symbol)}"
                          f"&from_date={since:%d-%m-%Y}&to_date={today:%d-%m-%Y}")
    out = []
    for r in rows or []:
        try:
            ex = datetime.strptime(r["exDate"], "%d-%b-%Y").date()
        except (KeyError, ValueError):
            continue
        purpose = (r.get("subject") or "").strip()
        kind, factor = classify(purpose)
        out.append({"exDate": ex.isoformat(), "purpose": purpose, "actionType": kind, "adjustmentFactor": factor})
    return out


def ingest(db: Session, stock: Stock, years: int = YEARS) -> dict:
    """Never raises. NSE's website feed first (quick and dependable); NSE's MCP
    tool when that fails. A symbol with no actions is reported, not an error."""
    today = date.today()
    since = today - timedelta(days=365 * years)
    via = "NSE website"
    try:
        actions = _from_website(stock.symbol, since, today)
    except Exception as first:  # noqa: BLE001
        via = "NSE MCP"
        try:
            data = bhavcopy.call("get_corporate_actions", symbol=stock.symbol, fromDate=since.isoformat(), toDate=today.isoformat())
            actions = data.get("actions", []) if isinstance(data, dict) else []
        except Exception as exc:  # noqa: BLE001 — a bulk run must outlive any one symbol
            return {"error": f"website: {str(first)[:80]}; MCP: {str(exc)[:80]}"}
    now = datetime.now(timezone.utc)
    rows = {}
    for a in actions:
        if a.get("exDate"):
            purpose = (a.get("purpose") or "").strip()[:500]
            rows[(a["exDate"], purpose)] = {
                "stock_id": stock.id, "ex_date": date.fromisoformat(a["exDate"]), "purpose": purpose,
                "action_type": a.get("actionType") or "OTHER", "adjustment_factor": float(a.get("adjustmentFactor") or 1.0),
                "dividend_per_share": dividend_in(purpose), "retrieved_at": now}
    rows = list(rows.values())
    if rows:
        stmt = insert(NseCorporateAction).values(rows)
        db.execute(stmt.on_conflict_do_update(
            index_elements=["stock_id", "ex_date", "purpose"],
            set_={c: stmt.excluded[c] for c in ("action_type", "adjustment_factor", "dividend_per_share", "retrieved_at")}))
    db.commit()
    return {"actions": len(rows), "via": via}


def for_stock(db: Session, stock_id: str) -> list[NseCorporateAction]:
    return (db.query(NseCorporateAction).filter(NseCorporateAction.stock_id == stock_id)
            .order_by(NseCorporateAction.ex_date).all())


def share_changes(actions: list[NseCorporateAction]) -> list[NseCorporateAction]:
    return [a for a in actions if a.action_type in ("SPLIT", "BONUS") and abs(float(a.adjustment_factor) - 1.0) > 1e-9]


def split_or_bonus_financial_years(actions: list[NseCorporateAction]) -> dict[str, str]:
    """{"FY2026": "Bonus 1:1 (2025-09-23)"} — Indian financial year, April to March."""
    out = {}
    for a in share_changes(actions):
        fy = a.ex_date.year + (1 if a.ex_date.month >= 4 else 0)
        out[f"FY{fy}"] = f"{a.purpose} ({a.ex_date.isoformat()})"
    return out


def dividends_last_12_months(actions: list[NseCorporateAction], today: date | None = None) -> dict | None:
    """Dividend per share over the last year, restated to today's share count:
    a dividend paid before a later split or bonus is multiplied by that
    event's adjustment factor."""
    today = today or date.today()
    changes = share_changes(actions)
    paid = [a for a in actions if a.dividend_per_share is not None and today - timedelta(days=365) < a.ex_date <= today]
    if not paid:
        return None
    total, items = 0.0, []
    for a in paid:
        factor = 1.0
        for c in changes:
            if c.ex_date > a.ex_date:
                factor *= float(c.adjustment_factor)
        total += float(a.dividend_per_share) * factor
        items.append({"ex_date": a.ex_date.isoformat(), "per_share": float(a.dividend_per_share), "purpose": a.purpose,
                      **({"restated_per_share": round(float(a.dividend_per_share) * factor, 4)} if factor != 1.0 else {})})
    return {"per_share": round(total, 4), "payments": items, "source": "NSE corporate actions"}
