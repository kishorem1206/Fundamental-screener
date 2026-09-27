"""Third-party analyst consensus — store + serve only, never computed here.

The backend has no direct HTTP path to IndMoney (only reachable via an MCP
connector inside a Claude session) — so unlike every other ingestion path
in this app, there is no autonomous fetch function here. An agent session
calls the IndMoney MCP tool, then POSTs the result to this endpoint. See
alembic/versions/0012_analyst_consensus.py for the full rationale, most
importantly: this is external opinion, never blended into this platform's
own deterministic scoring or presented as a source of truth.
"""
from __future__ import annotations

from datetime import datetime, timezone

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import AnalystConsensus, Stock

router = APIRouter(prefix="/api/analyst-consensus")

_DISCLAIMER = (
    "Third-party analyst consensus, for context only. Not part of this "
    "platform's own deterministic score, sector analysis, or AI rating — "
    "this platform's own analysis is derived independently from primary "
    "financial data."
)


class AnalystConsensusEntry(BaseModel):
    num_analysts: int | None = None
    sentiment: str | None = None
    buy_pct: float | None = None
    hold_pct: float | None = None
    sell_pct: float | None = None
    target_price_mean: float | None = None
    target_price_low: float | None = None
    target_price_high: float | None = None
    price_at_capture: float | None = None
    implied_upside_pct: float | None = None
    source: str = "INDMONEY"


def _row_to_dict(row: AnalystConsensus) -> dict:
    return {
        "num_analysts": row.num_analysts,
        "sentiment": row.sentiment,
        "buy_pct": float(row.buy_pct) if row.buy_pct is not None else None,
        "hold_pct": float(row.hold_pct) if row.hold_pct is not None else None,
        "sell_pct": float(row.sell_pct) if row.sell_pct is not None else None,
        "target_price_mean": float(row.target_price_mean) if row.target_price_mean is not None else None,
        "target_price_low": float(row.target_price_low) if row.target_price_low is not None else None,
        "target_price_high": float(row.target_price_high) if row.target_price_high is not None else None,
        "price_at_capture": float(row.price_at_capture) if row.price_at_capture is not None else None,
        "implied_upside_pct": float(row.implied_upside_pct) if row.implied_upside_pct is not None else None,
        "source": row.source,
        "retrieved_at": row.retrieved_at.isoformat(),
        "disclaimer": _DISCLAIMER,
    }


@router.get("/{company_id:path}")
def get_analyst_consensus(company_id: str):
    """Every analyst-consensus source on file for this company, keyed by
    source — a stock can have both an IndMoney row (agent-fetched) and a
    Yahoo Finance row (autonomous) at once; they are never merged into one
    number, each stays clearly attributed to where it came from."""
    db = get_db()
    try:
        rows = db.query(AnalystConsensus).filter_by(company_id=company_id).all()
        by_source = {row.source: _row_to_dict(row) for row in rows}
        return {"company_id": company_id, "by_source": by_source}
    finally:
        db.close()


@router.post("/{company_id:path}")
def store_analyst_consensus(company_id: str, entry: AnalystConsensusEntry):
    """Store a snapshot fetched by an agent session via the IndMoney MCP
    tool. Upserts — one row per (company, source), matching the "latest
    snapshot" semantics every other bulk-cache table in this app uses."""
    db = get_db()
    try:
        stock = db.query(Stock).filter_by(id=company_id).first()
        if stock is None:
            raise HTTPException(status_code=404, detail=f"Stock {company_id} not found")

        now = datetime.now(timezone.utc)
        existing = db.query(AnalystConsensus).filter_by(company_id=company_id, source=entry.source).first()
        fields = entry.model_dump()
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            existing.retrieved_at = now
        else:
            db.add(AnalystConsensus(id=str(uuid.uuid4()), company_id=company_id, retrieved_at=now, **fields))
        db.commit()
        return {"status": "stored", "company_id": company_id}
    except HTTPException:
        db.rollback()
        raise
    finally:
        db.close()
