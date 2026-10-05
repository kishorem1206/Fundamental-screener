from dataclasses import asdict
from typing import Literal
from fastapi import APIRouter, Query
from app.technical.services.classification_service import classification_service, StockListFilters
from app.technical.shared.errors import NotFoundError
from fastapi import HTTPException

router = APIRouter()

MarketCapEnum = Literal["LARGE_CAP", "MID_CAP", "SMALL_CAP", "MICRO_CAP", "NANO_CAP"]


@router.get("/stocks")
def list_stocks(
    universe_id: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    macro_sector: str | None = Query(default=None),
    market_cap_category: MarketCapEnum | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    filters = StockListFilters(
        universe_id=universe_id,
        sector=sector,
        macro_sector=macro_sector,
        market_cap_category=market_cap_category,
        limit=limit,
        offset=offset,
    )
    stocks = classification_service.list_stocks(filters)
    return {"stocks": [asdict(s) for s in stocks], "count": len(stocks), "limit": limit, "offset": offset}


@router.get("/stocks/{exchange}/{symbol}")
def get_stock(exchange: str, symbol: str):
    stock_id = f"{exchange.upper()}:{symbol.upper()}"
    try:
        stock = classification_service.get_stock(stock_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return {"stock": asdict(stock)}
