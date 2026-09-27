"""Sector framework metadata — Architecture v2 Stage 5. Exposes the
declarative "which metrics does this sector need" view
(SectorFramework.required_metric_ids(), derived from each sector's real
key_metrics() rather than a separate config file — see that method's
docstring in app/sectors/base.py for why).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.sectors.registry import get_framework, list_frameworks

router = APIRouter(prefix="/api/sectors")


@router.get("")
def list_sector_frameworks():
    """Every registered sector framework's name, aliases, and metric/red-flag counts."""
    return {"sectors": list_frameworks()}


@router.get("/{sector_name}/requirements")
def get_sector_requirements(sector_name: str):
    """Required metrics for one sector, grouped by category — e.g.
    {"asset_quality": ["gross_npa", "net_npa", ...], "capital": [...]}.
    Works for any of the 34 registered sectors, not just Banks — it's
    derived from the same base-class contract every sector implements."""
    framework = get_framework(sector_name)
    if framework.sector_name == "Generic" and sector_name.lower() != "generic":
        raise HTTPException(status_code=404, detail=f"Unknown sector '{sector_name}'")
    return {
        "sector_name": framework.sector_name,
        "required_metrics": framework.required_metric_ids(),
    }
