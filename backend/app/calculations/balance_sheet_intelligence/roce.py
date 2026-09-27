"""ROCE + DuPont decomposition (spec §37-39). Capital Employed methodology
is explicitly chosen and exposed, per spec §38's "do not silently mix
definitions" instruction: `Total Assets - Current Liabilities`, matching
`engine.py::roce_series()`'s existing formula exactly, so the new
Screener-sourced ROCE and the pre-existing yfinance-engine ROCE are a
genuine same-formula cross-check rather than two different numbers under
one label.

Both legal spec formulas (`Total Assets - Current Liabilities` and
`Equity + Long-Term Debt`) need a field Screener's condensed balance sheet
doesn't have (current liabilities, or a long-term/short-term debt split,
respectively) — there is no purely-Screener-sourced Capital Employed. This
module therefore cross-sources `current_liabilities` from the same
yfinance-based series `working_capital.py` already uses, explicitly
disclosed via `capital_employed_source`, never silently blended.
"""
from __future__ import annotations

CAPITAL_EMPLOYED_METHODOLOGY = "TOTAL_ASSETS_MINUS_CURRENT_LIABILITIES"


def compute_roce(total_assets: float | None, current_liabilities: float | None,
                  ebit: float | None, revenue: float | None) -> dict:
    capital_employed = None
    capital_employed_source = "UNAVAILABLE"
    if total_assets is not None and current_liabilities is not None:
        capital_employed = total_assets - current_liabilities
        capital_employed_source = "SCREENER_TOTAL_ASSETS_MINUS_YFINANCE_CURRENT_LIABILITIES"

    roce = None
    if capital_employed and ebit is not None:
        roce = round(ebit / capital_employed * 100, 2)

    ebit_margin = None
    if ebit is not None and revenue:
        ebit_margin = round(ebit / revenue * 100, 2)

    capital_employed_turnover = None
    if revenue is not None and capital_employed:
        capital_employed_turnover = round(revenue / capital_employed, 4)

    return {
        "capital_employed": capital_employed,
        "capital_employed_methodology": CAPITAL_EMPLOYED_METHODOLOGY,
        "capital_employed_source": capital_employed_source,
        "roce": roce,
        "ebit_margin": ebit_margin,
        "capital_employed_turnover": capital_employed_turnover,
    }


_DRIVER_TOLERANCE_PCT = 3.0  # a <3pp move counts as "flat" — mirrors pnl_engine.py's tolerance-banded direction style


def _direction(delta: float | None, tolerance: float = _DRIVER_TOLERANCE_PCT) -> str:
    if delta is None:
        return "UNKNOWN"
    if abs(delta) <= tolerance:
        return "FLAT"
    return "UP" if delta > 0 else "DOWN"


def classify_roce_driver(ebit_margin_delta: float | None, capital_turnover_delta_pct: float | None) -> str:
    """Spec §39's 4-way classification: was a ROCE change margin-led,
    turnover-led, both, or neither/mixed. Deltas are the caller's own
    period-over-period differences (percentage points for margin, % change
    for turnover) — this function only classifies, never computes them,
    keeping it a pure function like every other module here."""
    margin_dir = _direction(ebit_margin_delta)
    turnover_dir = _direction(capital_turnover_delta_pct)

    margin_up = margin_dir == "UP"
    turnover_up = turnover_dir == "UP"
    margin_flat = margin_dir == "FLAT"
    turnover_flat = turnover_dir == "FLAT"

    if margin_up and turnover_flat:
        return "MARGIN_DRIVEN"
    if turnover_up and margin_flat:
        return "TURNOVER_DRIVEN"
    if margin_up and turnover_up:
        return "BOTH"
    return "MIXED"


def roce_cross_check(screener_methodology_roce: float | None, yfinance_engine_roce: float | None,
                      screener_ratios_latest_roce: float | None) -> dict:
    """All three shown side by side, never silently reconciled — spec §37's
    own DuPont section doesn't ask for this, but the app's established
    "never silently pick a winner between two real sources" discipline
    (already applied to the cash-flow-bridge/P&L cascades earlier this
    session) applies here too."""
    values = [v for v in (screener_methodology_roce, yfinance_engine_roce, screener_ratios_latest_roce) if v is not None]
    max_divergence_pct = None
    if len(values) >= 2 and max(values) != 0:
        max_divergence_pct = round((max(values) - min(values)) / abs(max(values)) * 100, 2)
    return {
        "screener_methodology_roce": screener_methodology_roce,
        "yfinance_engine_roce": yfinance_engine_roce,
        "screener_ratios_latest_roce": screener_ratios_latest_roce,
        "max_divergence_pct": max_divergence_pct,
    }
