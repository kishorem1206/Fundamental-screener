"""The "Balance Sheet House" (spec §9) — Sources of Funds vs. Applications
of Funds, side by side. Equal by construction (both total to `total_assets`,
confirmed to equal Screener's `total_liabilities` figure).

Two documented deviations from the spec's literal mock, both because the
underlying split genuinely doesn't exist in any source this app has (see
`canonical_fields.STRUCTURALLY_ABSENT`), not because they were skipped for
convenience:
  1. Sources shows ONE "Debt" row, not separate "Long-Term Debt"/
     "Short-Term Debt" rows — Screener's `borrowings` is one undifferentiated
     figure.
  2. Applications' "Cash" row is cross-sourced from the yfinance-based
     working-capital series (`cash_series`, passed in explicitly), not from
     Screener — Screener folds cash into `other_assets` with no separate
     line. The `cash_source` field on the output makes this explicit rather
     than silently blending two providers under one label.
"""
from __future__ import annotations

from app.calculations.balance_sheet_intelligence.canonical_fields import NO_ST_LT_DEBT_SPLIT_REASON


def compute_house(period: dict[str, float | None], cash_value: float | None = None) -> dict:
    """`period` is a flat single-period snapshot from
    `snapshot.period_snapshot()`. `cash_value` is the yfinance-sourced cash
    figure for the same (or nearest) period, passed in by the orchestrator
    — this module never fetches it itself (see module docstring)."""
    equity_capital = period.get("equity_capital") or 0
    reserves = period.get("reserves") or 0
    borrowings = period.get("borrowings") or 0
    deposits = period.get("deposits")  # bank-only
    other_liabilities = period.get("other_liabilities") or 0

    fixed_assets = period.get("fixed_assets") or 0
    cwip = period.get("capital_work_in_progress") or 0
    investments = period.get("investments") or 0
    other_assets_total = period.get("other_assets") or 0

    sources = [
        {"label": "Equity", "value": round(equity_capital + reserves, 2)},
        {"label": "Debt", "value": round(borrowings, 2), "note": NO_ST_LT_DEBT_SPLIT_REASON},
    ]
    if deposits is not None:
        sources.append({"label": "Deposits", "value": round(deposits, 2)})
    sources.append({"label": "Other Liabilities", "value": round(other_liabilities, 2)})

    # Applications: cash (cross-sourced) and receivables/inventory are not
    # separable from Screener's `other_assets` — shown as one "Other Assets
    # (incl. cash*)" row when no cross-sourced cash figure is available, or
    # cash pulled out as its own row (with the remainder correspondingly
    # reduced) when it is.
    applications = [
        {"label": "Fixed Assets", "value": round(fixed_assets, 2)},
        {"label": "CWIP", "value": round(cwip, 2)},
        {"label": "Investments", "value": round(investments, 2)},
    ]
    if cash_value is not None:
        other_assets_remainder = round(other_assets_total - cash_value, 2)
        applications.append({"label": "Cash", "value": round(cash_value, 2), "source": "YFINANCE"})
        applications.append({"label": "Other Assets", "value": other_assets_remainder})
        cash_source = "YFINANCE"
    else:
        applications.append({"label": "Other Assets (incl. cash)", "value": round(other_assets_total, 2)})
        cash_source = "UNAVAILABLE_FOR_PERIOD"

    return {
        "sources": sources,
        "applications": applications,
        "sources_total": round(sum(s["value"] for s in sources), 2),
        "applications_total": round(sum(a["value"] for a in applications), 2),
        "cash_source": cash_source,
    }
