"""Single DB-reading entry point for this package (mirrors
`pl_intelligence/cascade.py`'s role) — every other module here is a pure
function operating on the dicts this module returns, no DB access of its
own, matching how `pl_intelligence/cost_structure.py`/`margin_trends.py`
etc. take already-fetched series as parameters rather than querying
directly.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.calculations.balance_sheet_intelligence.canonical_fields import (
    BORROWINGS_KEY_ALIASES,
    CANONICAL_FIELD_TO_CASH_FLOW_KEY,
    CANONICAL_FIELD_TO_RATIOS_KEY,
    CANONICAL_FIELD_TO_SCREENER_KEY,
)
from app.infrastructure.database import metric_store

_VALID_STATEMENT_TYPES = {"STANDALONE", "CONSOLIDATED"}


def _require_statement_type(statement_type: str) -> None:
    if statement_type not in _VALID_STATEMENT_TYPES:
        raise ValueError(f"statement_type must be one of {_VALID_STATEMENT_TYPES}, got {statement_type!r}")


def _series(db: Session, company_id: str, metric_key: str, statement_type: str) -> dict[str, float]:
    """{period: authoritative_value} — same tier/confidence/recency
    resolution every other ledger reader in this codebase uses."""
    history = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    periods = sorted({row.period for row in history if row.period != "TTM"})
    out: dict[str, float] = {}
    for period in periods:
        winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
        if winner is not None and winner.value is not None:
            out[period] = float(winner.value)
    return out


def _borrowings_series(db: Session, company_id: str, statement_type: str) -> dict[str, float]:
    """Screener uses "borrowings" for most companies but "borrowing"
    (singular) for at least HDFC Bank — confirmed live. Try both, merge
    whichever periods each has data for (a company is never scraped under
    both names in the same run, but the alias fallback keeps this robust
    if Screener's own naming convention drifts)."""
    merged: dict[str, float] = {}
    for key in BORROWINGS_KEY_ALIASES:
        merged.update(_series(db, company_id, key, statement_type))
    return merged


def build_screener_balance_sheet_series(db: Session, company_id: str, statement_type: str) -> dict[str, dict[str, float]]:
    """{canonical_field: {period: value}} for every Screener-sourced
    balance-sheet field. `statement_type` has no default — enforces "never
    mix standalone/consolidated" at the signature, same discipline as
    `pl_intelligence/cascade.py`."""
    _require_statement_type(statement_type)
    out: dict[str, dict[str, float]] = {}
    for field, screener_key in CANONICAL_FIELD_TO_SCREENER_KEY.items():
        if field == "borrowings":
            out[field] = _borrowings_series(db, company_id, statement_type)
        elif screener_key is not None:
            out[field] = _series(db, company_id, screener_key, statement_type)
    return out


def build_cash_flow_series(db: Session, company_id: str, statement_type: str) -> dict[str, dict[str, float]]:
    """{canonical_field: {period: value}} for every new cf_*-prefixed
    Screener cash-flow field (Milestone 1)."""
    _require_statement_type(statement_type)
    return {
        field: _series(db, company_id, metric_key, statement_type)
        for field, metric_key in CANONICAL_FIELD_TO_CASH_FLOW_KEY.items()
    }


def screener_ratios_history(db: Session, company_id: str, statement_type: str) -> dict[str, dict[str, float]]:
    """{canonical_field: {period: value}} for EVERY year Screener's
    `.ratios()` endpoint has on record — not just the latest one.

    Rewritten 2026-09-23 (explicit user report, screenshot of Screener's own
    Ratios tab showing 11 years of Debtor Days/CCC/ROCE%): this used to
    return only the single latest period per field, on the mistaken
    assumption Screener's `.ratios()` page itself only ever exposes the
    latest year. It doesn't — `ingest_ratios()` was already rewritten
    earlier this session to fetch every year via `openscreener`'s
    `ratios_history()` (the vendored parser used to silently discard all
    but the last item; see `ratios_parser.py`), so the ledger has genuinely
    had the full multi-year history sitting in it all along — this function
    just wasn't reading past the latest point. `working_capital.py` now
    merges this full history year-by-year against yfinance's own series
    (Screener winning every year it covers), instead of only ever
    overriding the single latest point.

    Falls back to the OTHER statement type, per field, when the requested
    one has no `.ratios()` rows on record for that field at all. Real gap
    found live on GNFC (2026-09-22, user's own report — "we have working
    capital ratios in screener right? why are you missing?"):
    `statement_type` here is whatever `compute_balance_sheet_intelligence()`
    resolved OVERALL (CONSOLIDATED, via the single_statement_source
    relabeling this codebase already uses for a company with only one real
    dataset — see `pl_intelligence/__init__.py`'s own docstring for that
    mechanism), but `ingest_ratios()`'s CONSOLIDATED fetch can fail
    independently of whichever ingestion resolved that overall label. GNFC
    had all 6 `bs_ratio_*` rows on record tagged STANDALONE only, so a
    strict CONSOLIDATED-only lookup here silently returned `{}`, and every
    downstream working-capital/ROCE cross-check field showed "Not
    disclosed" even though the real numbers were sitting in the ledger
    under the other tag. This never fabricates a number — it only widens
    which tag is accepted when the first one is completely empty (checked
    per field, not once for the whole result — a company can genuinely
    have some fields on one side and some on the other), matching the same
    statement-type-agnostic resilience `pl_intelligence`'s own
    `allow_fallback`/`single_statement_source` handling already applies
    elsewhere in this codebase."""
    _require_statement_type(statement_type)
    fallback_type = "STANDALONE" if statement_type == "CONSOLIDATED" else "CONSOLIDATED"
    out: dict[str, dict[str, float]] = {}
    for field, metric_key in CANONICAL_FIELD_TO_RATIOS_KEY.items():
        series = _series(db, company_id, metric_key, statement_type)
        if not series:
            series = _series(db, company_id, metric_key, fallback_type)
        if series:
            out[field] = series
    return out
    return out


def latest_period(series_by_field: dict[str, dict[str, float]]) -> str | None:
    """The most recent period with at least `total_assets` on record — the
    one field every downstream calculation needs, so it's the natural
    anchor for "what counts as the latest period" across this whole
    package."""
    ta = series_by_field.get("total_assets", {})
    return max(ta.keys()) if ta else None


def period_snapshot(series_by_field: dict[str, dict[str, float]], period: str) -> dict[str, float | None]:
    """{canonical_field: value_at_period} — a flat single-period slice of
    `build_screener_balance_sheet_series()`'s output, the shape
    `integrity.py`/`common_size.py`/`sources_applications.py`/`leverage.py`
    operate on."""
    return {field: values.get(period) for field, values in series_by_field.items()}


_YEAR_RE = re.compile(r"(\d{4})")


def fiscal_year(period: str) -> str | None:
    """Screener's balance-sheet periods are ISO dates ("2026-03-31");
    yfinance-sourced series (via `engine.py`'s `MetricsCalculator`, read
    from `FundamentalAnalysis.metrics`) label the same fiscal year
    "FY2026" — confirmed live these refer to the identical fiscal year, not
    an off-by-one. Every cross-source lookup between the two (ROCE's
    Capital Employed, the House's cash row, the working-capital blend's
    cross-check) matches on this shared 4-digit year rather than an exact
    string, since neither format is a substring of the other."""
    match = _YEAR_RE.search(period)
    return match.group(1) if match else None


def value_at_fiscal_year(series: dict[str, float], screener_period: str) -> float | None:
    """Look up a yfinance-sourced series (keyed "FY2026"-style) using a
    Screener period (keyed "2026-03-31"-style) — see `fiscal_year()`."""
    year = fiscal_year(screener_period)
    if year is None:
        return None
    for key, value in series.items():
        if fiscal_year(key) == year:
            return value
    return None


def yfinance_value_in_crores(series: dict[str, float], screener_period: str) -> float | None:
    """Same lookup as `value_at_fiscal_year()`, PLUS the Rupees-to-Crores
    conversion every other cross-source blend in this codebase already
    applies (`equity_report_mapper.py`'s `/ 1e7` on `pnl_engine.py`'s
    yfinance-sourced PAT/CFO/FCF figures, same convention). Real bug found
    live: `current_liabilities_series()`/`cash_series()` from
    `engine.py::MetricsCalculator` are raw Rupees (yfinance's own unit),
    while every Screener-sourced balance-sheet figure this package reads is
    already in Crores — mixing the two without this conversion produced a
    Capital Employed of -364 BILLION and a garbage negative ROCE the first
    time this was tested end to end. Use this (never `value_at_fiscal_year`
    directly) for any yfinance ABSOLUTE-VALUE figure (cash, current
    liabilities, total debt, total equity) blended with Screener data;
    `value_at_fiscal_year` alone stays correct for RATIO/DAY-COUNT yfinance
    series (DSO, DIO, DPO, CCC, Current Ratio, ...), which need no unit
    conversion at all."""
    raw = value_at_fiscal_year(series, screener_period)
    return raw / 1e7 if raw is not None else None
