"""The golden rule (spec §4): never analyze a balance sheet before
validating `Total Assets == Total Liabilities + Equity`.

Screener's own `total_liabilities` row is confirmed (live-tested against
Maruti: 148880 == 148880) to already equal `total_assets` by construction —
it's Screener's own sources-of-funds total, which already includes equity,
not an independently-derived external-liabilities figure. This check
therefore mostly validates Screener's own scrape/parse consistency for a
period (catches a digit-misread or a row that failed to parse) rather than
providing an independent cross-check the way the spec's CFO framework
intends when a filing's own liabilities+equity are summed from separate
line items — documented here so nobody downstream mistakes a VALID result
for "we independently verified this filing balances."
"""
from __future__ import annotations

_DEFAULT_TOLERANCE_PCT = 0.5  # spec doesn't name a number; 0.5% catches real scrape errors without flagging rounding noise


def validate_accounting_identity(
    total_assets: float | None,
    total_liabilities_and_equity: float | None,
    tolerance_pct: float = _DEFAULT_TOLERANCE_PCT,
) -> dict:
    """Returns the spec §63 `balance_sheet_integrity` shape. `status` is
    `"MISSING_DATA"` (not an error) when either side is absent — a
    genuinely unbalanced filing is different from a filing this app simply
    doesn't have data for yet, and the two must never look the same to a
    downstream consumer deciding whether to gate on this."""
    if total_assets is None or total_liabilities_and_equity is None:
        return {
            "status": "MISSING_DATA",
            "total_assets": total_assets,
            "total_liabilities_equity": total_liabilities_and_equity,
            "difference": None,
            "difference_pct": None,
        }

    difference = total_assets - total_liabilities_and_equity
    denom = abs(total_assets) if total_assets else None
    difference_pct = abs(difference) / denom * 100 if denom else None

    is_valid = difference_pct is not None and difference_pct <= tolerance_pct
    return {
        "status": "VALID" if is_valid else "BALANCE_SHEET_INTEGRITY_ERROR",
        "total_assets": total_assets,
        "total_liabilities_equity": total_liabilities_and_equity,
        "difference": round(difference, 2),
        "difference_pct": round(difference_pct, 4) if difference_pct is not None else None,
    }


def integrity_by_period(total_assets_series: dict[str, float], total_liabilities_series: dict[str, float],
                         tolerance_pct: float = _DEFAULT_TOLERANCE_PCT) -> dict[str, dict]:
    """Per-period integrity check across every period both series have a
    value for — spec §5's point-in-time discipline means every period gets
    its own independent check, not just the latest."""
    periods = sorted(set(total_assets_series) | set(total_liabilities_series))
    return {
        period: validate_accounting_identity(
            total_assets_series.get(period), total_liabilities_series.get(period), tolerance_pct,
        )
        for period in periods
    }
