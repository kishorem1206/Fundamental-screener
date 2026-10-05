"""Reads and writes for the two price tables."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import IndexBar, PriceBar

_CHUNK = 5000


def _upsert(db: Session, model, rows: list[dict], keys: tuple[str, str]) -> int:
    for start in range(0, len(rows), _CHUNK):
        chunk = rows[start:start + _CHUNK]
        stmt = insert(model).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=list(keys),
            set_={c: stmt.excluded[c] for c in chunk[0] if c not in keys},
        )
        db.execute(stmt)
    return len(rows)


def upsert_price_bars(db: Session, rows: list[dict]) -> int:
    return _upsert(db, PriceBar, rows, ("stock_id", "bar_date")) if rows else 0


def upsert_index_bars(db: Session, rows: list[dict]) -> int:
    return _upsert(db, IndexBar, rows, ("index_name", "bar_date")) if rows else 0


def replace_price_history(db: Session, stock_id: str, rows: list[dict]) -> int:
    """A split, bonus or dividend restates every earlier adjusted price, so the
    stock's whole series is swapped for the freshly adjusted one."""
    db.query(PriceBar).filter(PriceBar.stock_id == stock_id).delete(synchronize_session=False)
    return upsert_price_bars(db, rows)


def closes(db: Session, stock_id: str, since: date | None = None, adjusted: bool = True) -> list[tuple[date, float]]:
    column = PriceBar.adj_close if adjusted else PriceBar.close
    q = db.query(PriceBar.bar_date, column).filter(PriceBar.stock_id == stock_id)
    if since:
        q = q.filter(PriceBar.bar_date >= since)
    return [(d, float(v)) for d, v in q.order_by(PriceBar.bar_date)]


def bars(db: Session, stock_id: str, since: date | None = None) -> list[PriceBar]:
    q = db.query(PriceBar).filter(PriceBar.stock_id == stock_id)
    if since:
        q = q.filter(PriceBar.bar_date >= since)
    return q.order_by(PriceBar.bar_date).all()


def index_closes(db: Session, index_name: str, since: date | None = None) -> list[tuple[date, float]]:
    q = db.query(IndexBar.bar_date, IndexBar.close).filter(IndexBar.index_name == index_name)
    if since:
        q = q.filter(IndexBar.bar_date >= since)
    return [(d, float(v)) for d, v in q.order_by(IndexBar.bar_date)]


def last_price_dates(db: Session) -> dict[str, date]:
    return dict(db.query(PriceBar.stock_id, func.max(PriceBar.bar_date)).group_by(PriceBar.stock_id))


def index_dates(db: Session) -> set[date]:
    return {d for (d,) in db.query(IndexBar.bar_date).distinct()}


def coverage(db: Session) -> dict:
    stocks, bars_n, first, last = db.query(
        func.count(func.distinct(PriceBar.stock_id)), func.count(), func.min(PriceBar.bar_date), func.max(PriceBar.bar_date)
    ).one()
    indices, ibars, ifirst, ilast = db.query(
        func.count(func.distinct(IndexBar.index_name)), func.count(), func.min(IndexBar.bar_date), func.max(IndexBar.bar_date)
    ).one()
    return {
        "stocks": {"count": stocks, "bars": bars_n, "first": first, "last": last},
        "indices": {"count": indices, "bars": ibars, "first": ifirst, "last": ilast},
    }
