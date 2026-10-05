from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal

from app.technical.services.rsi_divergence_service import rsi_divergence_service

router = APIRouter(tags=["rsi-divergence"])

DivergenceTypeParam = Literal["REGULAR_BULLISH", "REGULAR_BEARISH", "HIDDEN_BULLISH", "HIDDEN_BEARISH"]
TimeframeParam      = Literal["1H", "4H", "1D", "1W"]


class RSIDivergenceScanRequest(BaseModel):
    universe:           str                       = "NIFTY_500"
    timeframe:          TimeframeParam            = "1D"
    pivot_left:         int                       = Field(default=3,    ge=1,   le=10)
    pivot_right:        int                       = Field(default=3,    ge=1,   le=10)
    max_recency_bars:   int                       = Field(default=10,   ge=1,   le=30)
    min_bars_between:   int                       = Field(default=5,    ge=2,   le=50)
    max_bars_between:   int                       = Field(default=50,   ge=5,   le=50)
    min_rsi_change:     float                     = Field(default=1.0,  ge=0.0, le=20.0)
    min_price_chg_pct:  float                     = Field(default=0.1,  ge=0.0, le=10.0)
    max_pivot_rsi:      float | None              = Field(default=40.0, ge=0.0, le=100.0)
    min_pivot_rsi:      float | None              = Field(default=None, ge=0.0, le=100.0)
    require_rsi_rising: bool                      = False
    div_types:          list[DivergenceTypeParam] = ["REGULAR_BULLISH"]
    limit:              int                       = Field(default=100,  ge=1,   le=500)
    offset:             int                       = Field(default=0,    ge=0)


@router.post("/rsi-divergence/scan")
def scan_rsi_divergence(body: RSIDivergenceScanRequest):
    return rsi_divergence_service.scan(
        universe=body.universe,
        timeframe=body.timeframe,
        pivot_left=body.pivot_left,
        pivot_right=body.pivot_right,
        max_recency_bars=body.max_recency_bars,
        min_bars_between=body.min_bars_between,
        max_bars_between=body.max_bars_between,
        min_rsi_change=body.min_rsi_change,
        min_price_chg_pct=body.min_price_chg_pct,
        max_pivot_rsi=body.max_pivot_rsi,
        min_pivot_rsi=body.min_pivot_rsi,
        require_rsi_rising=body.require_rsi_rising,
        div_types=list(body.div_types),  # type: ignore[arg-type]
        limit=body.limit,
        offset=body.offset,
    )
