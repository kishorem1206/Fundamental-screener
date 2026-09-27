"""Sector routing (spec §61-62): Banks/NBFCs/Insurance skip
inventory/DIO/DPO/CCC entirely — the spec's explicit instruction, since
those concepts don't apply to a financial institution's balance sheet.

A full dedicated bank/NBFC balance-sheet schema (spec §62: Gross NPA, Net
NPA, Provisions, Capital, Capital Adequacy) is explicitly OUT OF SCOPE for
this engine — that surface already belongs to this app's existing banking
framework (`app/sectors/banking_data_bridge.py` and the fields
`screener_client.py::ingest_quarterly_metrics()` already ingests:
`gross_npa`, `net_npa`, `cost_to_income_ratio`). This module only routes
and reuses what's already there, never rebuilds it.
"""
from __future__ import annotations

from app.calculations.balance_sheet_intelligence.canonical_fields import (
    FINANCIAL_INSTITUTION_SECTORS,
    HEALTHCARE_MANUFACTURING_BASIC_INDUSTRIES,
    INVENTORY_LIGHT_SECTORS,
)


def is_financial_institution(sector_name: str | None) -> bool:
    return bool(sector_name) and sector_name in FINANCIAL_INSTITUTION_SECTORS


def is_inventory_material(sector_name: str | None, basic_industry: str | None = None) -> bool:
    """False -> `coverage.py` labels `inventory_turnover` NOT_APPLICABLE
    instead of MISSING_INPUT (2026-09-20 scope call: exempt every
    CURRENTLY-KNOWN sector except the ones where inventory is core to the
    business — see `INVENTORY_MATERIAL_SECTORS`/`INVENTORY_LIGHT_SECTORS`'s
    docstrings). Healthcare is split by `basic_industry` since it covers
    both hospitals (not material) and pharma/device manufacturers (material)
    under one sector_name. A sector_name this app doesn't yet recognize
    (None, or genuinely new) defaults to True — inventory stays a real,
    visible gap rather than being silently exempted on a guess."""
    if not sector_name:
        return True
    if sector_name == "Healthcare":
        return basic_industry in HEALTHCARE_MANUFACTURING_BASIC_INDUSTRIES
    if sector_name in INVENTORY_LIGHT_SECTORS:
        return False
    return True


def financial_institution_summary(period: dict[str, float | None]) -> dict:
    """Thinner summary for a bank/NBFC period — Screener's own
    bank-specific field (`deposits`) plus whatever this app's existing
    banking-sector ledger fields already provide. Inventory/DIO/DPO/CCC are
    never computed for these companies (see module docstring)."""
    return {
        "deposits": period.get("deposits"),
        "borrowings": period.get("borrowings"),
        "investments": period.get("investments"),
        "total_assets": period.get("total_assets"),
        "note": "Financial institution — inventory/DIO/DPO/CCC not applicable (spec §61); "
                "see the existing banking framework for NPA/CAR/provisioning metrics.",
    }
