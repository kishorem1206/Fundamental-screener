"""Quarterly Report Extraction Engine — compute layer (Tier 1). Pure
in-memory arithmetic over `qtr_*` ledger rows that
`app/ingestion/quarterly_results_client.py` already wrote — no LLM call, no
network call, same "cheap, pure arithmetic" characterization
`pl_intelligence`'s own package docstring gives that package's compute-on-
read contract.

Computes QoQ/YoY growth, an OPM/net-margin trend classification (reusing
`pl_intelligence/margin_trends.py::classify_margin_direction()`), and a
small deterministic "what changed" flag set — see the Recent-Quarter
Red-Flag Inputs section of "Important md files/
Quarterly_Report_Fetching_Extraction_Engine.md" for the upstream spec this
flag set is a first, deliberately small slice of.

Deferred (Tier 2, not built here): BSE quarterly-results-PDF + OCR + LLM
extraction for segment-level/guidance data not on Screener's quarterly
table (Screener's quarterly view has no segment breakdown, no management
guidance text, no seasonality commentary — only the same aggregate P&L
line items `pnl_history_client.py` already reads for annual data, mirrored
at quarterly cadence). Needs OCR machinery (BSE's results filings are
scanned images, no text layer, unlike NSE annual reports) and is
banking-gated today (`app/ingestion/bse_client.py` is only called from
`banking_ingestion.py`). Revisit once a real need for segment-level
quarterly data surfaces.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.quarterly_intelligence.flags import compute_flags
from app.calculations.quarterly_intelligence.growth import qoq_delta_pp, qoq_growth, yoy_growth
from app.calculations.quarterly_intelligence.margin_trend import compute_margin_trend, net_margin_series
from app.calculations.quarterly_intelligence.series import quarter_series

_TRACKED_FIELDS = {
    "sales": "qtr_sales", "expenses": "qtr_expenses", "operating_profit": "qtr_operating_profit",
    "opm": "qtr_opm", "other_income": "qtr_other_income", "interest": "qtr_interest",
    "depreciation": "qtr_depreciation", "pbt": "qtr_pbt", "tax_pct": "qtr_tax_pct",
    "net_profit": "qtr_net_profit", "eps": "qtr_eps",
}
_GROWTH_FIELDS = ("sales", "net_profit", "operating_profit")


def _trim(series: dict[str, float], n: int) -> dict[str, float]:
    periods = sorted(series.keys())[-n:]
    return {p: series[p] for p in periods}


def compute_quarterly_intelligence(
    db: Session, company_id: str, statement_type: str = "CONSOLIDATED", n_quarters: int = 8,
    allow_fallback: bool = True,
) -> dict:
    """Returns `{}`-shaped-but-populated dict (never raises — a company
    with no `qtr_*` data yet just gets an empty `period`, matching every
    other calc module's contract). Falls back to STANDALONE when
    CONSOLIDATED has no data (e.g. a standalone-only company) — same "no
    real toggle to offer" concept `pl_intelligence` already handles for its
    own single-statement companies, flagged via `single_statement_source`.
    `allow_fallback=False` (the frontend's explicit toggle,
    `app/routes/quarterly_intelligence.py`) disables this — a user who
    deliberately asks for STANDALONE should see "not available" rather than
    a silently-swapped CONSOLIDATED result, same contract
    `pl_intelligence`'s own `allow_fallback` param enforces."""
    raw = {field: quarter_series(db, company_id, key, statement_type) for field, key in _TRACKED_FIELDS.items()}
    single_statement_source = False
    if not raw["sales"] and allow_fallback and statement_type != "STANDALONE":
        statement_type = "STANDALONE"
        raw = {field: quarter_series(db, company_id, key, statement_type) for field, key in _TRACKED_FIELDS.items()}
        single_statement_source = True

    if not raw["sales"]:
        return {"period": None, "statement_type": statement_type, "single_statement_source": single_statement_source,
                "quarters_available": 0, "series": {}, "qoq": {}, "yoy": {}, "margin_trend": {}, "flags": [],
                "latest_quarter": {}}

    latest_period = max(raw["sales"].keys())
    quarters_available = len(raw["sales"])

    qoq = {field: qoq_growth(raw[field]) for field in _GROWTH_FIELDS}
    yoy = {field: yoy_growth(raw[field]) for field in _GROWTH_FIELDS}
    qoq_opm = qoq_delta_pp(raw["opm"])

    net_margin = net_margin_series(raw["sales"], raw["net_profit"])
    trailing_opm = _trim(raw["opm"], n_quarters)
    trailing_net_margin = _trim(net_margin, n_quarters)
    margin_trend = compute_margin_trend(trailing_opm, trailing_net_margin)

    flags = compute_flags(
        qoq_sales_growth=qoq["sales"], qoq_opm=qoq_opm,
        other_income=raw["other_income"], pbt=raw["pbt"], tax_pct=raw["tax_pct"],
    )
    trailing_periods = set(sorted(raw["sales"].keys())[-n_quarters:])
    flags = [f for f in flags if f["period"] in trailing_periods]

    latest_quarter = {field: series.get(latest_period) for field, series in raw.items()}

    return {
        "period": latest_period,
        "statement_type": statement_type,
        "single_statement_source": single_statement_source,
        "quarters_available": quarters_available,
        "series": {field: _trim(series, n_quarters) for field, series in raw.items()},
        "qoq": {**{field: _trim(qoq[field], n_quarters) for field in _GROWTH_FIELDS}, "opm_delta_pp": _trim(qoq_opm, n_quarters)},
        "yoy": {field: _trim(yoy[field], n_quarters) for field in _GROWTH_FIELDS},
        "margin_trend": margin_trend,
        "flags": flags,
        "latest_quarter": latest_quarter,
    }
