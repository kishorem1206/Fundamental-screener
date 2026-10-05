from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.technical.services.rsi_momentum_service import rsi_momentum_service

router = APIRouter(tags=["rsi-momentum"])


class RSIMomentumScanRequest(BaseModel):
    universe: str = "NIFTY_500"
    lookback_days: int = Field(default=20, ge=5, le=100)
    threshold: float = Field(default=60.0, ge=30.0, le=90.0)
    signals: list[str] = []   # empty = return all signals
    limit: int = Field(default=200, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


@router.post("/rsi-momentum/scan")
def scan_rsi_momentum(body: RSIMomentumScanRequest):
    return rsi_momentum_service.scan(
        universe=body.universe,
        lookback_days=body.lookback_days,
        threshold=body.threshold,
        signals=body.signals or None,
        limit=body.limit,
        offset=body.offset,
    )
