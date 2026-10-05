from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal

from app.technical.services.macd_service import macd_service

router = APIRouter(tags=["macd"])

SourceType  = Literal["Close", "Open", "High", "Low", "HL2", "HLC3", "OHLC4"]
MAType      = Literal["EMA", "SMA"]
TFType      = Literal["1H", "4H", "1D", "1W"]

HistFilter  = Literal["STRONG_BULLISH", "BULLISH_FADING", "STRONG_BEARISH", "BEARISH_FADING", "POSITIVE", "NEGATIVE"]
CrossFilter = Literal["BULLISH", "BEARISH", "BULLISH_BELOW_ZERO", "BULLISH_ABOVE_ZERO", "BEARISH_ABOVE_ZERO", "BEARISH_BELOW_ZERO"]


class MACDScanRequest(BaseModel):
    universe:           str                    = "NIFTY_500"
    source:             SourceType             = "Close"
    fast:               int                    = Field(default=12,  ge=2,  le=50)
    slow:               int                    = Field(default=26,  ge=3,  le=200)
    signal_period:      int                    = Field(default=9,   ge=1,  le=50)
    osc_ma_type:        MAType                 = "EMA"
    sig_ma_type:        MAType                 = "EMA"
    timeframe:          TFType                 = "1D"
    hist_filters:       list[HistFilter]       = []
    cross_filters:      list[CrossFilter]      = []
    cross_bars:         int                    = Field(default=5,   ge=1,  le=50)
    crossover_lookback: int                    = Field(default=20,  ge=1,  le=50)
    limit:              int                    = Field(default=300, ge=1,  le=1000)
    offset:             int                    = Field(default=0,   ge=0)


class MACDChartRequest(BaseModel):
    exchange:      str        = "NSE"
    symbol:        str
    source:        SourceType = "Close"
    fast:          int        = Field(default=12, ge=2,  le=50)
    slow:          int        = Field(default=26, ge=3,  le=200)
    signal_period: int        = Field(default=9,  ge=1,  le=50)
    osc_ma_type:   MAType     = "EMA"
    sig_ma_type:   MAType     = "EMA"
    timeframe:     TFType     = "1D"
    num_bars:      int        = Field(default=80, ge=20, le=300)


@router.post("/macd/scan")
def scan_macd(body: MACDScanRequest):
    return macd_service.scan(
        universe=body.universe,
        source=body.source,
        fast=body.fast,
        slow=body.slow,
        signal=body.signal_period,
        osc_ma=body.osc_ma_type,
        sig_ma=body.sig_ma_type,
        timeframe=body.timeframe,
        hist_filters=list(body.hist_filters),
        cross_filters=list(body.cross_filters),
        cross_bars=body.cross_bars,
        crossover_lookback=body.crossover_lookback,
        limit=body.limit,
        offset=body.offset,
    )


@router.post("/macd/chart")
def macd_chart(body: MACDChartRequest):
    data = macd_service.get_chart_data(
        exchange=body.exchange,
        symbol=body.symbol,
        source=body.source,
        fast=body.fast,
        slow=body.slow,
        signal=body.signal_period,
        osc_ma=body.osc_ma_type,
        sig_ma=body.sig_ma_type,
        timeframe=body.timeframe,
        num_bars=body.num_bars,
    )
    if data is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Could not compute MACD series for this stock")
    return data
