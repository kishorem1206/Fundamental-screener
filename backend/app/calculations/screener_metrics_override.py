"""Screener.in as Primary Source of Truth for `analysis.metrics` — a
post-processing layer over `engine.py::MetricsCalculator.compute_all()`'s
already-computed output. Per the user's explicit instruction ("Screener
website primary source for all values, yfinance fallback if not
available"), this overwrites specific keys of the yfinance-computed
`metrics` dict IN PLACE with Screener-sourced equivalents, reusing the
Screener-primary engines already built this session
(`pnl_engine.py`, `balance_sheet_intelligence/{leverage,roce,snapshot}.py`)
rather than recomputing anything.

`engine.py::MetricsCalculator` itself is intentionally left completely
untouched — every key with no genuine Screener source below is simply never
touched here, so its original yfinance-computed value silently remains the
fallback. This also means `scoring.py` and all 34 `app/sectors/*.py`
frameworks need zero code changes: they read `analysis.metrics` by the same
key names regardless of which function last wrote them.

Formula-mismatch policy (e.g. ROE: Screener/pnl_engine.py uses AVERAGE
shareholders' equity, engine.py used CLOSING equity; interest coverage:
Screener/pnl_engine.py uses (PBT+Interest)/Interest, engine.py used
EBIT/Interest): overridden outright, trusting Screener's own number, never
reverse-engineered to match engine.py's old formula — that's the literal
reading of "Screener is the primary source of truth for the value," and
avoids inventing a third, novel number nobody asked for. Every touched key
is recorded in `metrics["_metric_sources"]` (mirrors
`app/sectors/ledger_bridge.py`'s `_ledger_metrics` internal-bookkeeping-key
convention) so the formula actually in effect is never silently hidden.

Never raises — any failure to reach/parse Screener data for one metric
leaves that key at its original yfinance value, matching every other calc
module's degrade-gracefully contract.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.logger import logger

# Metrics with NO Screener source anywhere in this codebase today — listed
# explicitly (mirrors `balance_sheet_intelligence/canonical_fields.py::
# STRUCTURALLY_ABSENT`'s style) so a genuine gap is documented, not silently
# glossed over. Not read by any code path; purely a reference for humans
# auditing this module (and for the docs pass, Milestone 5).
SCREENER_NOT_AVAILABLE: dict[str, str] = {
    "gross_margin": "No material/COGS breakdown anywhere in Screener's P&L view (same gap pl_intelligence/cascade.py already documents).",
    "roa": "No Screener source for Net Income/Total Assets.",
    "roic": "No Screener-sourced ROIC/DuPont decomposition anywhere this session.",
    "asset_turnover": "No Screener source.",
    "is_cyclical": "Cyclicality (coefficient-of-variation/peak-trough) not computed from Screener data.",
    "piotroski": "Piotroski F-Score not recomputed from Screener inputs this rollout.",
    "forward_pe": "No forward-estimate data on Screener's summary ratios strip (trailing P/E and book value only).",
    "ev_to_ebitda": "No enterprise-value data on Screener's summary ratios strip.",
    "ev_to_sales": "No enterprise-value data on Screener's summary ratios strip.",
    "peg_ratio": "No direct Screener PEG figure to override with — but see "
                 "`_recompute_peg_ratio_after_override()` below: whenever pe_ratio IS overridden, "
                 "peg_ratio is recomputed from that overridden P/E so the two stay consistent, "
                 "rather than left at engine.py's stale pre-override value.",
    "earnings_yield": "Depends on trailing P/E only insofar as engine.py derives it — kept yfinance-sourced for consistency with the other EV-family metrics above, which stay yfinance-only.",
    "ev_to_fcf": "No enterprise-value data on Screener's summary ratios strip.",
    "p_fcf": "No enterprise-value data on Screener's summary ratios strip.",
    "fcf_yield": "cash_flow_intelligence has Screener-sourced FCF but no FCF/MarketCap ratio matching this key's exact shape yet — deferred to a follow-up milestone.",
    "fcf_cagr_3y": "cash_flow_intelligence never computes a CAGR on cash-flow figures that can cross zero (documented rule already in conversion.py) — deferred.",
    "fcf_margin": "No single-year FCF/Revenue ratio computed from Screener data yet — deferred.",
    "fcf_to_pat": "No single-year FCF/PAT ratio computed from Screener data yet (cash_flow_intelligence only has a cumulative multi-year conversion ratio) — deferred.",
    "cfo_to_pat": "Same as fcf_to_pat above — deferred.",
    "current_ratio": "Screener's .ratios() endpoint structurally has no current/quick/cash ratio at all — confirmed live. Matches working_capital.py's own existing, documented decision to stay 100% yfinance here.",
    "quick_ratio": "Same as current_ratio above.",
    "cash_ratio": "Same as current_ratio above.",
    "implied_pe_series": "No Screener equivalent — a yfinance current-price/EPS-history-specific methodology.",
    "normalized_eps": "No Screener equivalent computed this rollout.",
}


def _set(metrics: dict, sources: dict, key: str, value, source: str = "SCREENER") -> None:
    """Only overwrites when `value` is a real number — never replaces a
    working yfinance value with a Screener-sourced None (that would make
    the fallback WORSE than doing nothing, the opposite of this module's
    purpose)."""
    if value is None:
        return
    metrics[key] = value
    sources[key] = source


_GROWTH_WIDGET_METRIC_KEYS = {
    ("revenue_cagr", "10y"): "screener_revenue_cagr_10y",
    ("revenue_cagr", "5y"): "screener_revenue_cagr_5y",
    ("revenue_cagr", "3y"): "screener_revenue_cagr_3y",
    ("pat_cagr", "10y"): "screener_pat_cagr_10y",
    ("pat_cagr", "5y"): "screener_pat_cagr_5y",
    ("pat_cagr", "3y"): "screener_pat_cagr_3y",
}


def _apply_pnl_overrides(metrics: dict, sources: dict, db: Session, company_id: str, sector_name: str | None) -> None:
    """P&L-sourced overrides (CAGRs, PAT margin, ROE, interest coverage) —
    all reused, never recomputed, from `pnl_engine.py::compute_pnl_analysis()`,
    itself already fully Screener-primary (reads exclusively from the
    `pnl_*` ledger, populated by `pnl_history_client.py` scraping Screener's
    `.profit_loss()`).

    CAGR windows get a THIRD tier ahead of `pnl_engine.py`'s own calculation:
    Screener's own displayed "Compounded Sales/Profit Growth" widget value
    (`pnl_history_client.py`'s `screener_revenue_cagr_*`/`screener_pat_cagr_*`
    ledger rows), read via `_sr_value`-style latest-snapshot lookup. This
    matters specifically for `pat_cagr` on a loss-to-profit turnaround
    (Pine Labs, live 2026-09-16): `pnl_engine.py::_cagr_window` returns None
    whenever a window endpoint is <= 0, but Screener's widget still shows a
    number for that case — trusting it outright beats leaving the panel
    blank. `pnl_engine.py`'s own calculated CAGR remains the fallback for
    any window/company the widget scrape didn't cover (e.g. "10y" for most
    companies, since Screener only shows that column past a 10-year listing
    history)."""
    from app.calculations.pnl_engine import compute_pnl_analysis
    from app.infrastructure.database import metric_store

    try:
        for (engine_key, window), widget_metric_key in _GROWTH_WIDGET_METRIC_KEYS.items():
            row = metric_store.get_latest_period_value(db, company_id, widget_metric_key, statement_type="CONSOLIDATED")
            if row is not None and row.value is not None:
                _set(metrics, sources, f"{engine_key}_{window}", float(row.value), source="SCREENER_WIDGET")
    except Exception as e:
        # Isolated from the pnl_engine.py calculated fallback below — a DB
        # hiccup reading the widget snapshot must not block the calculated
        # CAGR from still being applied.
        logger.warning("screener_metrics_override: growth widget lookup failed, "
                        "falling back to pnl_engine's calculated CAGR", company_id=company_id, error=str(e))

    pnl = compute_pnl_analysis(db, company_id, sector_name=sector_name)
    if not pnl or not pnl.get("growth"):
        return

    growth = pnl.get("growth") or {}
    for engine_key, pnl_growth_key in (
        ("revenue_cagr", "sales_cagr"), ("pat_cagr", "profit_cagr"), ("eps_cagr", "eps_cagr"),
    ):
        windows = growth.get(pnl_growth_key) or {}
        # Only 3y/5y/10y overridden — pnl_engine.py's 7y window has no
        # engine.py counterpart key to overwrite (no `revenue_cagr_7y`
        # anywhere in scoring.py/SectorMetric declarations/types.ts).
        for window in ("3y", "5y", "10y"):
            key = f"{engine_key}_{window}"
            # Widget value (set above) already wins when present — never
            # let the calculated fallback clobber it.
            if key in sources and sources[key] == "SCREENER_WIDGET":
                continue
            _set(metrics, sources, key, windows.get(window))

    npm_current = (pnl.get("margins") or {}).get("npm", {}).get("current")
    _set(metrics, sources, "pat_margin", npm_current)

    roe_latest = (pnl.get("roe") or {}).get("latest")
    _set(metrics, sources, "roe", roe_latest)

    interest_coverage_latest = (pnl.get("interest_coverage") or {}).get("latest")
    _set(metrics, sources, "interest_coverage", interest_coverage_latest)


def _apply_balance_sheet_overrides(metrics: dict, sources: dict, db: Session, company_id: str, sector_name: str | None) -> None:
    """ROCE, D/E, net-debt/EBITDA, EBITDA/EBIT margin, and the latest-period
    DSO/DIO flip — all reused from `balance_sheet_intelligence`'s own
    already-computed output.

    Deliberately calls the package's full `compute_balance_sheet_intelligence()`
    orchestrator here (not just `leverage.compute_leverage()`/`roce.compute_roce()`
    directly, as first considered) — replicating its statement-type-fallback
    + period-selection + EBIT/EBITDA-cascade-reuse logic independently in
    this module would risk silent drift from the real implementation for a
    performance saving (one extra read-only, no-LLM, no-network function
    call) its own docstring already calls negligible ("nothing here is an
    expensive LLM call worth caching"). `yfinance_metrics=metrics` reuses
    the SAME dict this function is overriding — `compute_balance_sheet_intelligence()`
    only READS `cash_series`/`current_liabilities_series` off it, never
    mutates it."""
    from app.calculations.balance_sheet_intelligence import compute_balance_sheet_intelligence
    from app.calculations.pl_intelligence.cascade import build_income_cascade

    bsi = compute_balance_sheet_intelligence(db, company_id, sector_name=sector_name, yfinance_metrics=metrics)
    if not bsi or not bsi.get("period"):
        return

    dm = bsi.get("derived_metrics") or {}
    _set(metrics, sources, "roce", dm.get("roce"))
    try:
        _apply_roce_history(metrics, sources, db, company_id)
    except Exception as e:  # best-effort; the yfinance series stays if Screener history is unavailable
        logger.warning("ROCE history override skipped", company_id=company_id, error=str(e))
    _set(metrics, sources, "debt_to_equity", dm.get("debt_to_equity"))
    _set(metrics, sources, "net_debt_to_ebitda", dm.get("net_debt_to_ebitda"))

    wc_cross_check = (bsi.get("working_capital") or {}).get("latest_cross_check") or {}
    _set(metrics, sources, "inventory_days", (wc_cross_check.get("dio") or {}).get("screener_latest"))
    _set(metrics, sources, "receivable_days", (wc_cross_check.get("dso") or {}).get("screener_latest"))

    cascade = build_income_cascade(db, company_id, statement_type=bsi["statement_type"])
    period = bsi["period"]
    cascade_period = cascade.get(period) or {}
    ebitda, ebit, revenue = cascade_period.get("ebitda"), cascade_period.get("ebit"), cascade_period.get("revenue")
    if revenue:
        if ebitda is not None:
            _set(metrics, sources, "ebitda_margin", round(ebitda / revenue * 100, 2))
        if ebit is not None:
            _set(metrics, sources, "ebit_margin", round(ebit / revenue * 100, 2))


def _apply_roce_history(metrics: dict, sources: dict, db: Session, company_id: str) -> None:
    """ROCE series + trend from Screener's own yearly ROCE row (consolidated
    first), replacing the yfinance-derived series. Real bug found on Force
    Motors: the yfinance series (FY23 13.6 -> FY25 37.1 -> FY26 33.8) tripped a
    "consistently declining" risk while Screener's ROCE (24 -> 30 -> 36) only
    rose."""
    from app.calculations.engine import trend_direction
    from app.infrastructure.database import metric_store

    for statement_type in ("CONSOLIDATED", "STANDALONE"):
        series: dict[str, float] = {}
        history = metric_store.get_metric_history(db, company_id, "bs_ratio_roce_percent", statement_type=statement_type)
        for period in sorted({r.period for r in history if r.period and r.period != "TTM"}):
            winner, _ = metric_store.get_authoritative_value(
                db, company_id, "bs_ratio_roce_percent", period, statement_type=statement_type)
            if winner is not None and winner.value is not None:
                series[f"FY{period[:4]}"] = float(winner.value)
        if len(series) >= 2:
            recent = dict(list(series.items())[-5:])
            _set(metrics, sources, "roce_series", recent)
            _set(metrics, sources, "roce_trend", trend_direction(list(recent.values())[-3:]))  # last 3 FYs: a long turnaround series would read as "volatile"
            return


def _sr_value(db: Session, company_id: str, metric_key: str) -> float | None:
    """Reads the most recent `sr_*` summary-ratio snapshot (Milestone 1's
    ingestion, statement_type="CONSOLIDATED" — a fixed label for these).

    Correction (2026-09-21): this used to claim Screener's summary-ratios
    strip "isn't standalone/consolidated-specific" — disproven live on
    Apollo Hospitals (`screener_client.py::ingest_company_summary()`'s
    docstring has the full writeup): P/E was 83.0 fetched standalone vs.
    62.3 fetched consolidated, matching Screener's own consolidated page
    exactly. The ingestion side now fetches the consolidated page for real,
    so the "CONSOLIDATED" label here is accurate rather than a name
    slapped on standalone-sourced data. Uses `get_latest_period_value()`,
    the same "most recent value on record" primitive `ledger_bridge.py`
    already uses, since these rows are snapshot-dated (today's date)
    rather than fiscal-year-dated."""
    from app.infrastructure.database import metric_store

    row = metric_store.get_latest_period_value(db, company_id, metric_key, statement_type="CONSOLIDATED")
    return float(row.value) if row is not None and row.value is not None else None


def _apply_valuation_overrides(metrics: dict, sources: dict, db: Session, company_id: str) -> None:
    """P/E, P/B, market cap, dividend yield — from Screener's `summary()`
    "top ratios" strip (`sr_*` ledger keys, Milestone 1)."""
    pe = _sr_value(db, company_id, "sr_pe_ratio")
    _set(metrics, sources, "pe_ratio", pe)

    # Real bug found live-testing this exact milestone (same unit-mismatch
    # class as the -364-billion-Capital-Employed and 994,094,028%-FCF-
    # divergence bugs documented elsewhere this session): `sr_market_cap`
    # is ingested in Crores (matching every other sr_*/pnl_*/bs_* ledger
    # row), but `metrics["market_cap"]` is a yfinance-native RAW-RUPEE
    # figure — confirmed by `AnalysisDashboard.tsx`'s `mc / 1e7` display
    # conversion and `master_object.py`'s `company_info.get("market_cap")
    # or metrics.get("market_cap")` fallback (interchangeable = same
    # units). Writing Crores in unconverted would have displayed a market
    # cap off by 7 orders of magnitude (e.g. "₹0 Cr" for a real ₹3.8
    # lakh-Cr company). Convert back to raw Rupees to match the key's
    # existing, established unit convention.
    market_cap_cr = _sr_value(db, company_id, "sr_market_cap")
    market_cap_rupees = market_cap_cr * 1e7 if market_cap_cr is not None else None
    _set(metrics, sources, "market_cap", market_cap_rupees)

    dividend_yield = _sr_value(db, company_id, "sr_dividend_yield")
    _set(metrics, sources, "dividend_yield", dividend_yield)

    current_price = _sr_value(db, company_id, "sr_current_price")
    book_value = _sr_value(db, company_id, "sr_book_value")
    # Derived from ONE Screener snapshot (not yfinance's live price) so
    # pb_ratio stays internally consistent with market_cap/pe_ratio above,
    # all anchored to the same moment rather than mixing sources.
    if current_price is not None and book_value:
        _set(metrics, sources, "pb_ratio", round(current_price / book_value, 4))


def _recompute_peg_ratio_after_override(metrics: dict, sources: dict) -> None:
    """PEG = P/E / EPS 3-Year CAGR, meaningful only when both are positive
    — same formula and guard as `engine.py::MetricsCalculator.peg_ratio()`.

    Must run AFTER `_apply_valuation_overrides()` has (possibly) replaced
    `metrics["pe_ratio"]` with Screener's consolidated-basis figure:
    `engine.py` computes its own `peg_ratio` once, up front, from its own
    pre-override yfinance `trailing_pe` — leaving that stale value in place
    would silently show a PEG built from a P/E the report no longer
    displays. Same class of stale/inconsistent-number bug the Apollo
    Hospitals P/E investigation found live (2026-09-21: standalone-sourced
    83.0x P/E persisted under a "CONSOLIDATED" label, vs. the real 62.3x
    consolidated figure — see `screener_client.py::ingest_company_summary()`
    and `_sr_value()`'s docstrings above for the full writeup).

    Only touches `peg_ratio` when `pe_ratio` was actually overridden this
    run (`"pe_ratio" in sources`) — when Screener had no P/E to offer,
    `engine.py`'s own PEG is already internally consistent with its own
    `pe_ratio` and is left untouched, matching this module's "never touch
    a key with no genuine Screener-sourced replacement" contract."""
    if "pe_ratio" not in sources:
        return
    pe = metrics.get("pe_ratio")
    eps_growth_3y = metrics.get("eps_cagr_3y")
    if pe is None or eps_growth_3y is None or pe <= 0 or eps_growth_3y <= 0:
        metrics["peg_ratio"] = None
        sources.pop("peg_ratio", None)
        return
    _set(metrics, sources, "peg_ratio", round(pe / eps_growth_3y, 2), source="CALCULATED_FROM_SCREENER_PE")


def apply_screener_primary_overrides(
    metrics: dict,
    db: Session,
    company_id: str,
    sector_name: str | None = None,
) -> dict:
    """Mutates and returns `metrics` (the already-computed
    `MetricsCalculator.compute_all()` output) in place. Call this AFTER all
    Screener ingestion for this pipeline run has completed (the
    "sector_analysis" stage's ingestion block in orchestrator.py) — calling
    it any earlier (e.g. at the "ratio_calculations" stage, where
    `compute_metrics()` itself runs) would find no fresh Screener ledger
    data yet for a brand-new company's first analysis."""
    if metrics is None:
        return metrics

    sources: dict[str, str] = metrics.get("_metric_sources") or {}

    try:
        _apply_pnl_overrides(metrics, sources, db, company_id, sector_name)
    except Exception as e:
        logger.warning("screener_metrics_override: P&L overrides failed, keeping yfinance values",
                        company_id=company_id, error=str(e))

    try:
        _apply_balance_sheet_overrides(metrics, sources, db, company_id, sector_name)
    except Exception as e:
        logger.warning("screener_metrics_override: balance sheet overrides failed, keeping yfinance values",
                        company_id=company_id, error=str(e))

    try:
        _apply_valuation_overrides(metrics, sources, db, company_id)
    except Exception as e:
        logger.warning("screener_metrics_override: valuation overrides failed, keeping yfinance values",
                        company_id=company_id, error=str(e))

    try:
        _recompute_peg_ratio_after_override(metrics, sources)
    except Exception as e:
        logger.warning("screener_metrics_override: PEG recompute failed, keeping engine.py's original value",
                        company_id=company_id, error=str(e))

    if sources:
        metrics["_metric_sources"] = sources
    return metrics
