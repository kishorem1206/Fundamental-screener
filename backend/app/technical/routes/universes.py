from dataclasses import asdict
from fastapi import APIRouter, Query, HTTPException
from app.technical.services.classification_service import classification_service

router = APIRouter()


@router.get("/universes")
def list_universes():
    data = classification_service.list_universes()
    serialized = []
    for u in data:
        d = asdict(u)
        if d.get("last_synced_at") is not None:
            d["last_synced_at"] = d["last_synced_at"].isoformat()
        serialized.append(d)
    return {"universes": serialized, "count": len(serialized)}


@router.get("/universes/{universe_id}/stocks")
def get_universe_stocks(
    universe_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    stocks = classification_service.get_universe_stocks(universe_id, limit, offset)
    return {
        "universe_id": universe_id,
        "stocks": [asdict(s) for s in stocks],
        "count": len(stocks),
        "limit": limit,
        "offset": offset,
    }
