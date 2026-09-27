"""Fundamental P&L Analysis Engine — "P&L Intelligence" (new, additive layer).

Implements the deep P&L intelligence spec (`Important md files/
fundamental_pl_analysis_engine_spec.md`): standalone-vs-consolidated
comparison, peer margin percentiles, margin headroom, revenue/PAT doubling
velocity, earnings quality (EQI), operating-leverage/interest-trap
diagnostics, and a weighted M1-M5 P&L Master Score.

Deliberately a **separate package** from `app/calculations/pnl_engine.py`
(Stage 0's boundary — "do not break the existing fundamental engine"):
`pnl_engine.py` and its 4 existing call sites are untouched by this work.
Everything in this package is read here for the first time by
`app/interpretation/master_object.py`'s `pl_intelligence` key, purely
additive alongside the existing `pnl_analysis` key.

Two structural dead ends recur through every module in this package and are
always handled the same way — `value: None` + a `LOW`/`UNAVAILABLE`
confidence tag, never a fabricated number (spec Rule 4):

- **True Gross Margin/COGS**: Screener.in's P&L view has no material-cost
  line for any sector (confirmed by `pnl_engine.py`'s own pre-existing
  `expense_structure` stub). `cascade.py::build_income_cascade()` hardcodes
  `gross_profit`/`gross_margin` to `(None, "LOW")` for every period.
- **True per-segment P&L margin**: `BusinessSegment` has revenue only, no
  profit column — SOTP (Stage 24) can only ever be an approximation via
  standalone/consolidated deltas, never a fabricated segment margin.

A third dead end, discovered while building this package: Screener's
`pnl_expenses` is one aggregate OPEX line with no employee-cost/material/
power-fuel split, so `cost_structure.py`'s employee-cost-ratio and any rule
that wants to compare "employee cost growth vs revenue growth" specifically
also degrade to `None`/`UNAVAILABLE` — only aggregate OPEX-to-revenue is
computable.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.pl_intelligence.cascade import build_income_cascade
from app.calculations.pl_intelligence.cost_structure import (
    compute_cost_ratio_deltas,
    compute_cost_ratios,
)
from app.calculations.pl_intelligence.diagnostics import (
    earnings_bridge,
    margin_cascade_break,
    margin_stability_score,
    operating_leverage,
)
from app.calculations.pl_intelligence.doubling_velocity import (
    cagr_doubling,
    classify_doubling_speed,
    compare_doubling_velocity,
    empirical_doubling,
)
from app.calculations.pl_intelligence.earnings_quality import (
    compute_eqi,
    compute_non_core_income_ratios,
)
from app.calculations.pl_intelligence.margin_headroom import (
    compute_headroom,
    interpret_headroom_and_growth,
)
from app.calculations.pl_intelligence.margin_trends import classify_margin_direction
from app.calculations.statement_type_resolution import prefer_current_statement_type
from app.calculations.pl_intelligence.peer_engine import (
    compute_fintech_peer_percentiles,
    compute_peer_margin_percentiles,
)
from app.calculations.pl_intelligence.rules import evaluate_all_rules
from app.calculations.pl_intelligence.scoring import (
    compute_master_score,
    score_m1_sector_margin_percentile,
    score_m2_margin_headroom,
    score_m3_doubling_velocity,
    score_m4_eqi,
    score_m5_csr,
)
from app.calculations.pl_intelligence.standalone_consolidated import (
    compute_csr,
    compute_pat_structural_ratio,
    flag_conglomerate,
    subsidiary_contribution,
)
from app.infrastructure.database.models import Stock


def _doubling_for(series: dict, cagr_pct: float | None) -> dict:
    """Prefers the empirical doubling (an actual historical doubling that
    happened), falls back to the CAGR-based theoretical estimate when the
    series hasn't empirically doubled yet but the trend is positive —
    never fabricates a doubling that hasn't happened AND has no supporting
    positive trend."""
    empirical = empirical_doubling(series)
    if empirical is not None:
        return {**empirical, "method": "EMPIRICAL", "speed": classify_doubling_speed(empirical["doubling_years"])}
    theoretical_years = cagr_doubling(cagr_pct)
    if theoretical_years is not None:
        return {"doubling_years": theoretical_years, "method": "CAGR_THEORETICAL",
                "speed": classify_doubling_speed(theoretical_years)}
    return {"doubling_years": None, "method": None, "speed": None}


def _cagr_from_series(series: dict) -> float | None:
    """Whole-series CAGR (oldest to newest fiscal value) — a lightweight
    local computation (this package deliberately doesn't import
    `pnl_engine.py`'s own CAGR windows, per the Stage 0 boundary)."""
    items = sorted((p, v) for p, v in series.items() if v is not None)
    if len(items) < 2:
        return None
    (_, start), (_, end) = items[0], items[-1]
    years = len(items) - 1
    if start <= 0 or years <= 0:
        return None
    return round(((end / start) ** (1.0 / years) - 1.0) * 100, 2)


def compute_pl_intelligence(db: Session, company_id: str, sector_name: str | None = None,
                             statement_type: str | None = None, allow_fallback: bool = True) -> dict:
    """Orchestrates every Milestone 1-4 module into one combined dict for
    ONE company, at its latest available fiscal period. Never raises — a
    company with no `pnl_*` ledger data at all just returns a mostly-empty,
    `UNAVAILABLE`-tagged shape, matching every other calc module's
    contract. This is the function `master_object.py` calls to populate
    `master["pl_intelligence"]`, purely additive alongside the existing
    `pnl_analysis` key `compute_pnl_analysis()` (the older, separate
    engine) already populates.

    Real bug found live-testing Tata Technologies: `pnl_*` ledger rows had
    only ever been ingested under STANDALONE for this company (zero
    CONSOLIDATED rows), so the CONSOLIDATED default here returned an
    entirely empty result despite real STANDALONE data existing — same
    "engine defaults to CONSOLIDATED but the fallback never checks
    STANDALONE" bug class fixed the same day in
    `cash_flow_intelligence/__init__.py`'s statement-type selection.
    Falls back to the other statement type if the requested one has no
    cascade data — no caller passes `statement_type` explicitly today, so
    this is a strict improvement over the previous always-CONSOLIDATED
    behavior.

    `allow_fallback=False` (the frontend's explicit Consolidated/Standalone
    toggle, `app/routes/pl_intelligence.py`) disables this — a user who
    deliberately asks for STANDALONE should see "not available" rather
    than being silently redirected back to CONSOLIDATED. The PDF path
    (`equity_report_mapper.py`) always leaves this at its `True` default,
    then separately checks `result["statement_type"] == "CONSOLIDATED"`
    and omits the section rather than rendering a fallback.

    Real gap found live on Netweb Technologies / Bandhan Bank: some
    companies have NO consolidated ledger data at all (confirmed directly
    against Screener.in — 0 rows, not an ingestion failure, structurally
    absent since these companies have no subsidiaries to consolidate). For
    those, `allow_fallback=False` correctly-but-unhelpfully reported "not
    available" the moment a user clicked the Consolidated pill, even though
    the one real dataset (STANDALONE) IS, for a subsidiary-less company,
    what consolidated figures would be anyway. `single_statement_source`
    below detects this (exactly one of the two types has any data) and, in
    that case only, ignores whatever was requested and always serves the
    one real dataset labeled "CONSOLIDATED" — internal `statement_type`
    still resolves to the REAL type throughout (peer percentiles below are
    keyed by it), only the output label changes. Companies with genuine
    data on both sides are completely unaffected."""
    consolidated_cascade = build_income_cascade(db, company_id, statement_type="CONSOLIDATED")
    standalone_cascade = build_income_cascade(db, company_id, statement_type="STANDALONE")
    consolidated_ok = bool(consolidated_cascade)
    standalone_ok = bool(standalone_cascade)
    single_statement_source = consolidated_ok != standalone_ok

    if single_statement_source:
        statement_type = "CONSOLIDATED" if consolidated_ok else "STANDALONE"
        cascade = consolidated_cascade if consolidated_ok else standalone_cascade
    elif statement_type is None:
        # Auto-detect: prefer whichever side is actually CURRENT, not just
        # whichever happens to be nonempty — see statement_type_resolution.py.
        statement_type = prefer_current_statement_type({
            "CONSOLIDATED": max(consolidated_cascade.keys()) if consolidated_cascade else None,
            "STANDALONE": max(standalone_cascade.keys()) if standalone_cascade else None,
        })
        cascade = consolidated_cascade if statement_type == "CONSOLIDATED" else standalone_cascade
    else:
        cascade = consolidated_cascade if statement_type == "CONSOLIDATED" else standalone_cascade
        if not cascade and allow_fallback:
            fallback_statement_type = "STANDALONE" if statement_type == "CONSOLIDATED" else "CONSOLIDATED"
            fallback_cascade = standalone_cascade if fallback_statement_type == "STANDALONE" else consolidated_cascade
            if fallback_cascade:
                statement_type = fallback_statement_type
                cascade = fallback_cascade
    if not cascade:
        empty_score = compute_master_score(None, None, None, None, None)
        return {
            "period": None,
            "statement_type": "CONSOLIDATED" if single_statement_source else statement_type,
            "single_statement_source": single_statement_source,
            "score": empty_score, "margins": {}, "peer_percentiles": {}, "fintech_peer_percentiles": None,
            "margin_headroom": {}, "doubling": {}, "earnings_quality": {},
            "non_core_income": {}, "structure": {}, "diagnostics": {},
            "diagnostic_flags": [], "cascade": {},
        }

    periods = sorted(cascade.keys())
    period = periods[-1]
    prior_period = periods[-2] if len(periods) > 1 else None
    latest = cascade[period]

    stock = db.query(Stock).filter_by(id=company_id).first()
    sector = sector_name or (stock.sector if stock else None)

    cost_ratios = compute_cost_ratios(latest)
    cost_ratio_deltas = (compute_cost_ratio_deltas(cost_ratios, compute_cost_ratios(cascade[prior_period]))
                          if prior_period else {})

    eqi = compute_eqi(latest)
    non_core_income = compute_non_core_income_ratios(latest)

    csr = compute_csr(db, company_id, period)
    pat_structural = compute_pat_structural_ratio(db, company_id, period)
    subsidiary = subsidiary_contribution(db, company_id, period)
    conglomerate = flag_conglomerate(db, company_id)
    structure = {**csr, **pat_structural, **subsidiary, **conglomerate}

    peer_percentiles = compute_peer_margin_percentiles(db, company_id, sector, period, statement_type)
    pat_margin_peer = peer_percentiles.get("pat_margin", {})

    # Fintech-only addition (2026-09-17): GTV growth / take rate peer
    # percentiles, alongside the generic margin ones above — never raises
    # (mirrors this whole package's degrade-gracefully contract), since a
    # sector-lookup typo here shouldn't take down the rest of the P&L
    # intelligence computation for every other sector.
    fintech_peer_percentiles = None
    if sector == "Fintech":
        try:
            fintech_peer_percentiles = compute_fintech_peer_percentiles(db, company_id, sector)
        except Exception:
            fintech_peer_percentiles = None
    headroom = compute_headroom(latest.get("pat_margin"), pat_margin_peer.get("peer_max"))

    revenue_series = {p: c.get("revenue") for p, c in cascade.items()}
    pat_series = {p: c.get("pat") for p, c in cascade.items()}
    pat_margin_series = {p: c.get("pat_margin") for p, c in cascade.items()}
    ebitda_margin_series = {p: c.get("ebitda_margin") for p, c in cascade.items()}

    revenue_cagr = _cagr_from_series(revenue_series)
    pat_cagr = _cagr_from_series(pat_series)
    bridge = earnings_bridge(cascade)
    latest_bridge = bridge[-1] if bridge else {}
    revenue_growth_pct = latest_bridge.get("revenue_growth")

    headroom_interpretation = interpret_headroom_and_growth(headroom.get("classification"), revenue_growth_pct)

    revenue_doubling = _doubling_for(revenue_series, revenue_cagr)
    pat_doubling = _doubling_for(pat_series, pat_cagr)
    doubling = {
        "revenue": revenue_doubling,
        "pat": pat_doubling,
        # Pre-computed, never left for the LLM to derive — see
        # doubling_velocity.py::compare_doubling_velocity's docstring for
        # the real hallucination this prevents.
        "velocity_comparison": compare_doubling_velocity(
            revenue_doubling.get("doubling_years"), pat_doubling.get("doubling_years")),
    }

    pat_margin_trend = classify_margin_direction(pat_margin_series)
    ebitda_margin_trend = classify_margin_direction(ebitda_margin_series)

    leverage = operating_leverage(revenue_growth_pct, latest_bridge.get("ebitda_growth"), latest_bridge.get("pat_growth"))
    cascade_break = margin_cascade_break(latest.get("ebitda_margin"), latest.get("pat_margin"),
                                          cost_ratios.get("finance_cost_to_revenue_pct"))
    stability = margin_stability_score(pat_margin_series)

    m1 = score_m1_sector_margin_percentile(pat_margin_peer.get("percentile"))
    m2 = score_m2_margin_headroom(headroom_interpretation)
    m3 = score_m3_doubling_velocity(doubling["revenue"].get("doubling_years"))
    m4 = score_m4_eqi(eqi.get("eqi"))
    m5 = score_m5_csr(csr.get("csr_band"))
    score = compute_master_score(m1, m2, m3, m4, m5)

    facts = {
        "revenue_growth_pct": revenue_growth_pct,
        "pat_growth_pct": latest_bridge.get("pat_growth"),
        "current_pat_margin": latest.get("pat_margin"),
        "avg_5y_pat_margin": stability.get("avg_5y"),
        "current_margin": latest.get("pat_margin"),
        "peer_peak_margin": pat_margin_peer.get("peer_max"),
        "margin_trend": pat_margin_trend,
        "eqi": eqi.get("eqi"),
        "csr": csr.get("csr"),
        "ebitda_margin": latest.get("ebitda_margin"),
        "pat_margin": latest.get("pat_margin"),
        "finance_cost_to_revenue_pct": cost_ratios.get("finance_cost_to_revenue_pct"),
        "ebitda_margin_trend": ebitda_margin_trend,
        "opex_to_revenue_delta_pp": cost_ratio_deltas.get("delta_opex_to_revenue_pct"),
    }
    diagnostic_flags = evaluate_all_rules(facts)

    return {
        "period": period,
        "statement_type": "CONSOLIDATED" if single_statement_source else statement_type,
        "single_statement_source": single_statement_source,
        "cascade": cascade,
        "cost_ratios": cost_ratios,
        "cost_ratio_deltas": cost_ratio_deltas,
        "margins": {
            "ebitda_margin": latest.get("ebitda_margin"),
            "ebit_margin": latest.get("ebit_margin"),
            "pat_margin": latest.get("pat_margin"),
            "margin_direction": pat_margin_trend,
            "ebitda_margin_direction": ebitda_margin_trend,
            "stability": stability,
        },
        "peer_percentiles": peer_percentiles,
        "fintech_peer_percentiles": fintech_peer_percentiles,
        "margin_headroom": {**headroom, "interpretation": headroom_interpretation},
        "doubling": doubling,
        "earnings_quality": eqi,
        "non_core_income": non_core_income,
        "structure": structure,
        "earnings_bridge": bridge,
        "diagnostics": {
            "operating_leverage": leverage,
            "margin_cascade_break": cascade_break,
        },
        "diagnostic_flags": diagnostic_flags,
        "score": score,
    }
