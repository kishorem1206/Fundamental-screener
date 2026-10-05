from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock, Universe, UniverseMembership
from app.technical.shared.errors import NotFoundError


@dataclass
class StockRow:
    id: str
    symbol: str
    exchange: str
    company_name: str
    isin: str | None
    kite_instrument_token: int | None
    sector: str | None
    industry: str | None
    basic_industry: str | None
    macro_sector: str | None
    market_cap_category: str | None
    is_active: bool


@dataclass
class UniverseRow:
    id: str
    name: str
    description: str | None
    is_built_in: bool
    stock_count: int
    last_synced_at: datetime | None


@dataclass
class StockListFilters:
    universe_id: str | None = None
    sector: str | None = None
    macro_sector: str | None = None
    market_cap_category: str | None = None
    limit: int = 100
    offset: int = 0


def _to_stock_row(s: Stock) -> StockRow:
    return StockRow(
        id=s.id,
        symbol=s.symbol,
        exchange=s.exchange,
        company_name=s.company_name,
        isin=s.isin,
        kite_instrument_token=s.kite_instrument_token,
        sector=s.sector,
        industry=s.industry,
        basic_industry=s.basic_industry,
        macro_sector=s.macro_sector,
        market_cap_category=s.market_cap_category,
        is_active=s.is_active,
    )


class ClassificationService:
    def list_universes(self) -> list[UniverseRow]:
        db = get_db()
        try:
            rows = db.execute(select(Universe).order_by(Universe.name)).scalars().all()
            return [
                UniverseRow(
                    id=u.id,
                    name=u.name,
                    description=u.description,
                    is_built_in=u.is_built_in,
                    stock_count=u.stock_count,
                    last_synced_at=u.last_synced_at,
                )
                for u in rows
            ]
        finally:
            db.close()

    def get_universe_stocks(
        self, universe_id: str, limit: int = 500, offset: int = 0
    ) -> list[StockRow]:
        db = get_db()
        try:
            stmt = (
                select(Stock)
                .join(UniverseMembership, Stock.id == UniverseMembership.stock_id)
                .where(
                    and_(
                        UniverseMembership.universe_id == universe_id,
                        Stock.is_active.is_(True),
                    )
                )
                .order_by(Stock.symbol)
                .limit(limit)
                .offset(offset)
            )
            rows = db.execute(stmt).scalars().all()
            return [_to_stock_row(s) for s in rows]
        finally:
            db.close()

    def list_stocks(self, filters: StockListFilters) -> list[StockRow]:
        db = get_db()
        try:
            conditions = [Stock.is_active.is_(True)]
            if filters.sector is not None:
                conditions.append(Stock.sector == filters.sector)
            if filters.macro_sector is not None:
                conditions.append(Stock.macro_sector == filters.macro_sector)
            if filters.market_cap_category is not None:
                conditions.append(Stock.market_cap_category == filters.market_cap_category)

            if filters.universe_id is not None:
                stmt = (
                    select(Stock)
                    .join(UniverseMembership, Stock.id == UniverseMembership.stock_id)
                    .where(and_(*conditions, UniverseMembership.universe_id == filters.universe_id))
                    .order_by(Stock.symbol)
                    .limit(filters.limit)
                    .offset(filters.offset)
                )
            else:
                stmt = (
                    select(Stock)
                    .where(and_(*conditions))
                    .order_by(Stock.symbol)
                    .limit(filters.limit)
                    .offset(filters.offset)
                )

            rows = db.execute(stmt).scalars().all()
            return [_to_stock_row(s) for s in rows]
        finally:
            db.close()

    def get_stock(self, stock_id: str) -> StockRow:
        db = get_db()
        try:
            stmt = select(Stock).where(Stock.id == stock_id).limit(1)
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                raise NotFoundError("Stock", stock_id)
            return _to_stock_row(row)
        finally:
            db.close()


classification_service = ClassificationService()
