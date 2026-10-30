"""Compute CANSLIM for every active stock from stored data (a few minutes, nothing fetched).

    cd backend && .venv/bin/python -m app.canslim.runner
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.canslim import score as sc
from app.framework import price_stats, sector_rank, store
from app.prices.benchmarks import MARKET
from app.framework.screener_series import annual, cagr, quarterly
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import CanslimScore, ShareholdingScreener, Stock

_YEAR_DAYS = 370


def _prices(db, end) -> dict[str, tuple[list[float], list[float]]]:
    out: dict[str, tuple[list[float], list[float]]] = {}
    for sid, close, volume in db.execute(text(
            "select stock_id, close, volume from price_bars_daily where bar_date > :s and bar_date <= :e order by stock_id, bar_date"),
            {"s": end - timedelta(days=_YEAR_DAYS), "e": end}):
        c, v = out.setdefault(sid, ([], []))
        c.append(float(close))
        if volume is not None:
            v.append(float(volume))
    return out


def _holdings(db) -> dict[str, tuple[float | None, float | None]]:
    latest: dict[str, ShareholdingScreener] = {}
    for r in db.query(ShareholdingScreener).filter(ShareholdingScreener.frequency == "quarterly"):
        if (r.company_id not in latest or r.period_end > latest[r.company_id].period_end) and (r.fii_pct is not None or r.dii_pct is not None):
            latest[r.company_id] = r
    return {sid: (float(r.fii_pct) if r.fii_pct is not None else None, float(r.dii_pct) if r.dii_pct is not None else None) for sid, r in latest.items()}


def run(db, log=print) -> dict:
    end = price_stats.as_of(db)
    stocks = db.query(Stock).filter(Stock.is_active.is_(True)).all()
    prices, holdings = _prices(db, end), _holdings(db)
    ratings = sc.rs_ratings(price_stats.universe_returns(end))
    m = sc.market([v for _, v in price_stats.index_year(MARKET, end)], end)
    ids = {s.id: s for s in stocks}
    ranks = sector_rank.ranks([(r.stock_id, ids[r.stock_id].basic_industry, ids[r.stock_id].industry, float(r.quality) if r.quality is not None else None)
                               for r in store.latest_for_all(db) if r.stock_id in ids])
    now = datetime.now(timezone.utc)
    scored = 0
    for i, s in enumerate(stocks, 1):
        series, closes_vols = annual(db, s.id), prices.get(s.id, ([], []))
        letters = {"c": sc.letter_c(quarterly(db, s.id)),
                   "a": sc.letter_a(series, cagr(series, "net_profit", 3), cagr(series, "net_profit", 5)),
                   "n": sc.letter_n(closes_vols[0]), "s": sc.letter_s(closes_vols[1]), "l": sc.letter_l(ratings.get(s.id)),
                   "i": sc.letter_i(*holdings.get(s.id, (None, None))), "m": m}
        rank = ranks.get(s.id)
        peer = round(100 - rank["top_pct"], 1) if rank else None
        out = sc.blend(letters, peer)
        row = {"stock_id": s.id, "as_of": end, **{k: p.get("score") for k, p in letters.items()}, **out, "peer_quality": peer,
               "detail": {**letters, "peer": rank}, "computed_at": now}
        stmt = insert(CanslimScore).values(**row)
        db.execute(stmt.on_conflict_do_update(index_elements=["stock_id"], set_={k: stmt.excluded[k] for k in row if k != "stock_id"}))
        scored += out["canslim"] is not None
        if i % 300 == 0:
            db.commit()
            log(f"  ...{i}/{len(stocks)}")
    db.commit()
    return {"stocks": len(stocks), "with_canslim": scored, "as_of": end.isoformat(), "market": m["text"]}


def main() -> None:
    db = get_db()
    try:
        print("CANSLIM:", run(db, log=lambda m: print(m, flush=True)), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
