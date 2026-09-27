"""Investing Cash Flow — CFI breakdown (spec §17), asset-sale dependency
(spec §22), and unallocated-capital-drag detection (spec §23).
"""
from __future__ import annotations

_UNALLOCATED_CAPITAL_DRAG_THRESHOLD_PCT = 25.0  # spec §23's own number


def cfi_breakdown(cfi_period: dict[str, float | None]) -> dict:
    return {
        "fixed_assets_purchased": cfi_period.get("fixed_assets_purchased"),
        "fixed_assets_sold": cfi_period.get("fixed_assets_sold"),
        "investments_purchased": cfi_period.get("investments_purchased"),
        "investments_sold": cfi_period.get("investments_sold"),
        "interest_received": cfi_period.get("interest_received"),
        "dividends_received": cfi_period.get("dividends_received"),
        "share_redemption": cfi_period.get("share_redemption"),
        "acquisitions": cfi_period.get("acquisitions"),
        "other_investing": cfi_period.get("other_investing"),
    }


def asset_sale_dependency(cfi: float | None, fixed_assets_sold: float | None,
                           investments_sold: float | None) -> dict:
    """Spec §22: flags when CFI is positive primarily BECAUSE assets/
    investments were sold, not from an operating-linked investing gain —
    descriptive, never automatically negative (spec's own instruction)."""
    if cfi is None:
        return {"status": "MISSING_DATA", "triggered": False}
    liquidation_proceeds = (fixed_assets_sold or 0) + (investments_sold or 0)
    triggered = cfi > 0 and liquidation_proceeds > 0 and liquidation_proceeds >= cfi * 0.5
    return {
        "status": "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "triggered": triggered,
        "flag_id": "INVESTING_CASH_LIQUIDATION" if triggered else None,
        "cfi": cfi,
        "liquidation_proceeds": liquidation_proceeds,
    }


def unallocated_capital_drag(other_investing: float | None, annual_cfo: float | None) -> dict:
    """Spec §23: `Other Investing Items > 25% of Annual CFO` without clear
    disclosure — this app has no way to check "clear disclosures," so the
    flag is tagged `confidence=LOW` whenever it fires rather than treated
    as a confirmed finding, per the spec's own "only when disclosure is
    genuinely unavailable" qualifier (this app can't verify disclosure
    quality, so it never claims certainty here)."""
    if other_investing is None or not annual_cfo:
        return {"status": "MISSING_DATA", "triggered": False}
    ratio_pct = abs(other_investing) / abs(annual_cfo) * 100
    triggered = ratio_pct > _UNALLOCATED_CAPITAL_DRAG_THRESHOLD_PCT
    return {
        "status": "TRIGGERED" if triggered else "NOT_TRIGGERED",
        "triggered": triggered,
        "flag_id": "UNALLOCATED_CAPITAL_DRAG" if triggered else None,
        "ratio_pct": round(ratio_pct, 2),
        "threshold_pct": _UNALLOCATED_CAPITAL_DRAG_THRESHOLD_PCT,
        "confidence": "LOW" if triggered else "MEDIUM",
    }
