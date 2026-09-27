"""Source status endpoint — Architecture v2 Stage 6 (reframed). See
app/sources/registry.py's module docstring for why this exists instead of
RBI/SEBI/MCA ingestion adapters.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.sources.registry import get_source, list_sources

router = APIRouter(prefix="/api/sources")


@router.get("")
def list_all_sources():
    """Every known data source's type, trust tier, and current reachability
    status — including ones that are BLOCKED or RESTRICTED right now."""
    return {"sources": list_sources()}


@router.get("/{source_id}")
def get_one_source(source_id: str):
    source = get_source(source_id.upper())
    if source is None:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source_id}'")
    from dataclasses import asdict
    return asdict(source)
