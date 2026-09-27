"""Common-size balance sheet (spec §10): every line item as a % of total
assets (both sides use the same denominator here, since Screener's
`total_liabilities` already equals `total_assets` by construction).
"""
from __future__ import annotations

_ASSET_FIELDS = ("fixed_assets", "capital_work_in_progress", "investments", "other_assets")
_LIABILITY_EQUITY_FIELDS = ("equity_capital", "reserves", "borrowings", "deposits", "other_liabilities")


def compute_common_size(period: dict[str, float | None]) -> dict[str, float | None]:
    """{field: pct_of_total_assets} for one period's flat snapshot (from
    `snapshot.period_snapshot()`). A field absent from the period (e.g.
    `deposits` for a non-bank) is simply omitted, not zeroed."""
    total_assets = period.get("total_assets")
    if not total_assets:
        return {}
    out: dict[str, float | None] = {}
    for field in _ASSET_FIELDS + _LIABILITY_EQUITY_FIELDS:
        value = period.get(field)
        if value is not None:
            out[field] = round(value / total_assets * 100, 2)
    return out


def historical_common_size(series_by_field: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """{period: {field: pct}} across every period with a `total_assets`
    value — feeds the Asset/Funding Composition stacked charts (spec UI
    §3-4)."""
    from app.calculations.balance_sheet_intelligence.snapshot import period_snapshot

    total_assets_series = series_by_field.get("total_assets", {})
    return {
        period: compute_common_size(period_snapshot(series_by_field, period))
        for period in sorted(total_assets_series)
    }
