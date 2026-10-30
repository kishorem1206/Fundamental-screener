"""Stores the decision engine's result on each stock's latest `fw_scores` row,
and finds the best same-sector alternative (section 20's "vs best same-sector
alternative" and the replacement recommendation).

`refresh_all()` re-decides every stock from its stored scores in one pass —
run after a universe scoring run so every sector rank (and so every gate that
uses it) reflects the whole sector scored together. No network calls.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.framework import sector_rank, store
from app.framework.decision import decide, interpretation
from app.infrastructure.database.models import FrameworkScore, Stock

_SCORES = ("quality", "fundamental", "business_quality", "quantitative", "relative_strength", "technical", "valuation")
_ACTION_ORDER = {"Add gradually": 0, "Add on confirmation": 1, "Hold": 2, "Watch": 3}


def values(row: FrameworkScore) -> dict:
    out = {k: float(v) if (v := getattr(row, k)) is not None else None for k in _SCORES}
    out.update(valuation_view=row.valuation_view, trend=row.trend, quality_direction=row.quality_direction,
               quality_change_12m=float(row.quality_change_12m) if row.quality_change_12m is not None else None)
    return out


def _sector_latest(db: Session, sector: str) -> list[FrameworkScore]:
    ids = [sid for (sid,) in db.query(Stock.id).filter(Stock.sector == sector, Stock.is_active.is_(True))]
    if not ids:
        return []
    newest = (db.query(FrameworkScore.stock_id, func.max(FrameworkScore.as_of).label("as_of"))
              .filter(FrameworkScore.stock_id.in_(ids)).group_by(FrameworkScore.stock_id).subquery())
    rows = (db.query(FrameworkScore).join(newest, (FrameworkScore.stock_id == newest.c.stock_id)
                                         & (FrameworkScore.as_of == newest.c.as_of)).all())
    best: dict[str, FrameworkScore] = {}
    for r in rows:
        if r.stock_id not in best or r.basis == store.FULL:
            best[r.stock_id] = r
    return list(best.values())


def _apply(row: FrameworkScore, rank: dict | None, risk: dict | None = None) -> dict:
    """`risk`: the stock's current regulatory record (app/risk/record.py),
    read fresh at every decision so a new SEBI order counts without re-scoring."""
    if risk is not None:
        row.detail = {**(row.detail or {}), "risk": risk}
    d = decide(values(row), row.detail or {}, rank)
    row.classification, row.action = d["classification"], d["action"]
    row.detail = {**(row.detail or {}), "decision": {**d, "sector_rank": rank, "interpretation": interpretation(row.detail or {})}}
    return d


def _rank_rows(rows: list[FrameworkScore], stocks: dict[str, Stock]) -> list[tuple]:
    return [(r.stock_id, s.basic_industry, s.industry, float(r.quality) if r.quality is not None else None)
            for r in rows if (s := stocks.get(r.stock_id)) is not None]


def decide_one(db: Session, stock_id: str) -> dict | None:
    """Decision for one stock's latest row, ranked against its sector as it stands. Does not commit."""
    stock = db.get(Stock, stock_id)
    row = store.latest(db, stock_id)
    if row is None or stock is None:
        return None
    peers = _sector_latest(db, stock.sector) if stock.sector else [row]
    ranks = sector_rank.ranks(_rank_rows(peers, {r.stock_id: db.get(Stock, r.stock_id) for r in peers}))
    return _apply(row, ranks.get(stock_id), _risk(db, {stock_id}).get(stock_id))


def _risk(db: Session, stock_ids: set[str]) -> dict[str, dict]:
    from app.risk.record import for_all, for_stock

    try:
        if len(stock_ids) == 1:
            (sid,) = stock_ids
            return {sid: for_stock(db, sid)}
        return for_all(db, stock_ids)
    except Exception:  # noqa: BLE001 — tables not migrated yet: decide without them
        db.rollback()
        return {}


def refresh_all(db: Session) -> dict:
    stocks = {s.id: s for s in db.query(Stock).filter(Stock.is_active.is_(True))}
    latest = [r for r in store.latest_for_all(db) if r.stock_id in stocks]
    ranks = sector_rank.ranks(_rank_rows(latest, stocks))
    risk = _risk(db, {r.stock_id for r in latest})
    counts: dict[str, int] = {}
    for r in latest:
        d = _apply(r, ranks.get(r.stock_id), risk.get(r.stock_id))
        counts[d["classification"] or "unscored"] = counts.get(d["classification"] or "unscored", 0) + 1
    db.commit()
    return counts


def best_alternative(db: Session, stock: Stock, exclude: str) -> dict | None:
    """The strongest current opportunity in the same basic industry: a stock
    passing the core gate, ranked by how ready it is to buy (add gradually, add
    on confirmation, hold) and then by Quality — "better current opportunity",
    which the framework keeps apart from "better company" (section 12). Like
    for like: a shipbuilder is not replaced by a defence electronics maker just
    because both sit in Capital Goods, so a narrow industry may have no alternative."""
    if not stock.sector or not stock.basic_industry:
        return None
    same = {sid for (sid,) in db.query(Stock.id).filter(Stock.basic_industry == stock.basic_industry, Stock.is_active.is_(True))}
    rows = [r for r in _sector_latest(db, stock.sector) if r.stock_id in same and r.stock_id != exclude and r.quality is not None
            and r.classification in ("Core Quality", "Investable") and r.action in _ACTION_ORDER]
    if not rows:
        return None
    best = min(rows, key=lambda r: (_ACTION_ORDER[r.action], -float(r.quality)))
    other = db.get(Stock, best.stock_id)
    return {"stock_id": best.stock_id, "symbol": other.symbol, "company_name": other.company_name,
            "classification": best.classification, "action": best.action, **values(best)}


def replacement(mine: dict, alt: dict, my_detail: dict, alt_row: FrameworkScore | None) -> dict:
    """Section 20's replacement recommendation: where the alternative is better, score by score."""
    def diff(key):
        a, b = mine.get(key), alt.get(key)
        return None if a is None or b is None else round(b - a, 1)

    def risk(detail):
        q = ((detail or {}).get("quantitative") or {}).get("components") or {}
        return {"volatility_pct": (q.get("volatility") or {}).get("annualised_pct"),
                "max_fall_1y_pct": (q.get("drawdown") or {}).get("max_fall_pct")}

    better = [k.replace("_", " ") for k in ("fundamental", "quality", "relative_strength", "technical", "valuation")
              if (diff(k) or 0) >= 5]
    return {
        "existing": mine.get("symbol"), "candidate": alt["symbol"],
        "differences": {k: diff(k) for k in ("fundamental", "quality", "quantitative", "relative_strength", "technical", "valuation")},
        "valuation": {"existing": mine.get("valuation_view"), "candidate": alt.get("valuation_view")},
        "risk": {"existing": risk(my_detail), "candidate": risk(alt_row.detail if alt_row else None)},
        "why_better": better or ["no score better by 5 points or more: not a clear improvement"],
    }
