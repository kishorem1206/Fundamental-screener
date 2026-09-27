"""Leverage ratios (spec §28, §35). `debt_to_equity` and
`liabilities_to_equity` are stored as genuinely separate metrics per the
spec's explicit instruction — the two source frameworks it merges use
different leverage concepts, and Screener's own "Total Liabilities" already
includes equity (confirmed in `integrity.py`), so `liabilities_to_equity`
must subtract equity out first or it would silently just re-measure
`(total_assets)/equity`, not external liabilities at all.

Interest Coverage is NOT recomputed here — spec §36 explicitly says it
belongs in the risk layer despite needing P&L inputs, and this codebase
already has it (`engine.py::interest_coverage_series()`, yfinance-sourced);
`working_capital.py`'s blend re-exposes it alongside the other reused
yfinance series rather than duplicating the formula in two places.
"""
from __future__ import annotations


def compute_leverage(
    equity_capital: float | None,
    reserves: float | None,
    borrowings: float | None,
    total_liabilities: float | None,
    total_assets: float | None,
    cash_value: float | None,
    ebitda: float | None,
) -> dict:
    """All Screener-sourced except `cash_value` (yfinance, explicitly
    cross-sourced and labeled) and `ebitda` (reused from
    `pl_intelligence/cascade.py`, not recomputed)."""
    total_equity = None
    if equity_capital is not None and reserves is not None:
        total_equity = equity_capital + reserves

    debt_to_equity = None
    if borrowings is not None and total_equity:
        debt_to_equity = round(borrowings / total_equity, 4)

    external_liabilities = None
    liabilities_to_equity = None
    if total_liabilities is not None and total_equity is not None:
        external_liabilities = total_liabilities - total_equity
        if total_equity:
            liabilities_to_equity = round(external_liabilities / total_equity, 4)

    debt_to_assets = None
    if borrowings is not None and total_assets:
        debt_to_assets = round(borrowings / total_assets, 4)

    debt_to_capital = None
    if borrowings is not None and total_equity is not None and (borrowings + total_equity):
        debt_to_capital = round(borrowings / (borrowings + total_equity), 4)

    net_debt = None
    net_debt_source = "UNAVAILABLE_FOR_PERIOD"
    if borrowings is not None:
        if cash_value is not None:
            net_debt = round(borrowings - cash_value, 2)
            net_debt_source = "YFINANCE_CASH"
        else:
            net_debt = round(borrowings, 2)
            net_debt_source = "BORROWINGS_ONLY_NO_CASH_FOR_PERIOD"

    net_debt_to_ebitda = None
    if net_debt is not None and ebitda and ebitda > 0:
        net_debt_to_ebitda = round(net_debt / ebitda, 4)

    return {
        "total_equity": total_equity,
        "external_liabilities": external_liabilities,
        "debt_to_equity": debt_to_equity,
        "liabilities_to_equity": liabilities_to_equity,
        "debt_to_assets": debt_to_assets,
        "debt_to_capital": debt_to_capital,
        "net_debt": net_debt,
        "net_debt_source": net_debt_source,
        "net_debt_to_ebitda": net_debt_to_ebitda,
        "net_cash_position": net_debt is not None and net_debt < 0,
    }
