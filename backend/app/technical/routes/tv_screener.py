from typing import Any

from fastapi import APIRouter, Query as QueryParam
from pydantic import BaseModel, Field

from app.technical.services.tv_screener_service import tv_screener_service

router = APIRouter(prefix="/tv", tags=["tradingview"])


class TVScanRequest(BaseModel):
    markets:     list[str]            = ["india"]
    columns:     list[str]            = ["name", "close", "change", "volume", "market_cap_basic"]
    # Filter tree: leaf {field, op, value, value2} or group {op: "and"|"or", children: [...]}.
    # value / value2 may be {"field": "other_column"} to compare two columns.
    filters:     dict[str, Any] | None = None
    sort_by:     str | None           = "market_cap_basic"
    ascending:   bool                 = False
    limit:       int                  = Field(default=100, ge=1, le=1000)
    offset:      int                  = Field(default=0, ge=0)
    tickers:     list[str]            = []
    index:       str | None           = None
    asset_scope: str                  = "all"   # all | stock | etf | fund | dr
    use_cache:   bool                 = True


@router.get("/markets")
def list_markets():
    return tv_screener_service.markets()


@router.get("/fields")
def list_fields(market: str = QueryParam("america")):
    return tv_screener_service.fields(market)


@router.get("/presets")
def list_presets():
    return tv_screener_service.presets()


@router.post("/scan")
def scan(body: TVScanRequest):
    return tv_screener_service.scan(
        markets=body.markets, columns=body.columns, filters=body.filters, sort_by=body.sort_by,
        ascending=body.ascending, limit=body.limit, offset=body.offset, tickers=body.tickers,
        index=body.index, asset_scope=body.asset_scope, use_cache=body.use_cache,
    )
