"""Cash Flow Analysis Engine — implements `Important md files/
cash_flow_analysis_engine_standalone.md`'s 68-section spec, primary-sourced
from Screener.in's undocumented "schedules" API (see
`app/ingestion/screener_client.py::ingest_cash_flow_schedules()` for the
discovery writeup), with yfinance as an explicit cross-check layer only —
never silently preferred over Screener, same discipline as
`balance_sheet_intelligence`'s own cross-source blend.

Computed fresh on every call, no persisted score table — matches
`balance_sheet_intelligence`'s own no-cache-needed reasoning (cheap,
deterministic, ledger-backed).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.balance_sheet_intelligence.historical_trends import compute_trends
from app.calculations.balance_sheet_intelligence.snapshot import yfinance_value_in_crores
from app.calculations.cash_flow_intelligence import (
    archetype as archetype_module,
    conversion as conversion_module,
    coverage as coverage_module,
    financing as financing_module,
    fcf as fcf_module,
    forensic_patterns,
    investing as investing_module,
    reconciliation as reconciliation_module,
    red_flags as red_flags_module,
    snapshot,
    volatility as volatility_module,
    working_capital_impact as wc_impact_module,
)
from app.calculations.pl_intelligence.cascade import build_income_cascade
from app.calculations.statement_type_resolution import prefer_current_statement_type

_STATEMENT_TYPE_FALLBACK_ORDER = ("CONSOLIDATED", "STANDALONE")


def _empty_result(statement_type: str, single_statement_source: bool = False) -> dict:
    return {
        "period": None, "statement_type": statement_type,
        "single_statement_source": single_statement_source,
        "reconciliation": {"cfo_bridge": {}, "cfo_bridge_check": {"status": "MISSING_DATA"}, "cash_bridge": {"status": "MISSING_DATA"}},
        "working_capital_impact": {}, "investing": {}, "financing": {},
        "free_cash_flow": {}, "conversion": {}, "volatility": {"classification": "INSUFFICIENT_DATA"},
        "forensic_patterns": forensic_patterns.evaluate_all_patterns({}),
        "archetype": {"classification": "MIXED", "evidence": [], "confidence": "UNAVAILABLE"},
        "risk_flags": red_flags_module.evaluate_all_flags({}),
        "historical_trends": {}, "coverage": coverage_module.compute_coverage_audit({}),
    }


def compute_cash_flow_intelligence(
    db: Session,
    company_id: str,
    yfinance_metrics: dict | None = None,
    sector_name: str | None = None,
    balance_sheet_intelligence_result: dict | None = None,
    statement_type: str | None = None,
) -> dict:
    """Orchestrates every module in this package into one combined dict for
    ONE company at its latest available Screener period. Never raises — a
    company with no Screener cash-flow schedule data at all returns a
    mostly-empty, MISSING_DATA-tagged shape, matching every other calc
    module's contract in this codebase.

    `balance_sheet_intelligence_result` is optional — when the orchestrator
    has already computed it earlier in the pipeline (it runs one stage
    before this one), its `working_capital` DSO/DIO series are reused here
    as a directional proxy for receivables/inventory growth (this package
    has no direct receivables/inventory BALANCE series of its own, only
    their cash-flow-impact schedule lines) rather than recomputed.

    `statement_type` is normally left `None` — the function then picks
    whichever of CONSOLIDATED/STANDALONE actually has schedule data (see
    below). Pass an explicit `"CONSOLIDATED"` or `"STANDALONE"` (the
    frontend's toggle, `app/routes/cash_flow_intelligence.py`) to force
    exactly that one, with NO fallback to the other.

    Exception: when a company has NO consolidated data at all (confirmed
    live on Netweb Technologies / Bandhan Bank — 0 rows directly from
    Screener.in, not an ingestion gap; no subsidiaries to consolidate),
    `single_statement_source` below is True and the one real dataset is
    always served regardless of what was requested, labeled "CONSOLIDATED"
    in the output. Companies with genuine data on both sides — including
    the Tata Technologies case below, where both sides have SOME data but
    only one has schedule coverage — are unaffected."""
    yfinance_metrics = yfinance_metrics or {}
    forced_statement_type = statement_type

    top_level_by_type = {
        candidate: snapshot.build_top_level_series(db, company_id, candidate)
        for candidate in _STATEMENT_TYPE_FALLBACK_ORDER
    }
    has_top_level = {t: bool(s.get("cfo")) for t, s in top_level_by_type.items()}
    single_statement_source = has_top_level["CONSOLIDATED"] != has_top_level["STANDALONE"]

    # Real bug found live-testing Tata Technologies: Screener's schedule
    # fetch can succeed for one statement_type and silently fail/be absent
    # for the other (confirmed: CONSOLIDATED had all 8 top-level cf_*
    # periods but ZERO cf_sched_* rows, STANDALONE had both) — a
    # statement_type chosen purely from the top-level series being present
    # then produces an almost-entirely-empty result (CFO bridge, working
    # capital impact, investing/financing breakdown, conversion all read
    # blank) despite real schedule data existing under the OTHER statement
    # type. Prefer whichever statement_type has BOTH top-level AND
    # schedule data; only fall back to a top-level-only match (the old
    # behavior — still useful for FCF/cash-bridge-only output) if neither
    # candidate has schedule coverage.
    statement_type = None
    top_level: dict[str, dict[str, float]] = {}
    if single_statement_source:
        statement_type = "CONSOLIDATED" if has_top_level["CONSOLIDATED"] else "STANDALONE"
        top_level = top_level_by_type[statement_type]
    elif forced_statement_type:
        # A forced choice (the frontend toggle) gets NO fallback — the
        # caller explicitly wants to see this exact statement_type, or be
        # told it's unavailable, never silently redirected to the other.
        if has_top_level[forced_statement_type]:
            statement_type = forced_statement_type
            top_level = top_level_by_type[forced_statement_type]
        if statement_type is None:
            return _empty_result(forced_statement_type, single_statement_source)
    else:
        # Auto-detect: try whichever side is actually CURRENT first, not
        # just CONSOLIDATED-always-first — see statement_type_resolution.py.
        preferred = prefer_current_statement_type(
            {t: snapshot.latest_period(top_level_by_type[t]) for t in _STATEMENT_TYPE_FALLBACK_ORDER}
        )
        preference_order = (preferred,) + tuple(t for t in _STATEMENT_TYPE_FALLBACK_ORDER if t != preferred)
        top_level_only_fallback: tuple[str, dict[str, dict[str, float]]] | None = None
        for candidate in preference_order:
            if not has_top_level[candidate]:
                continue
            candidate_series = top_level_by_type[candidate]
            if top_level_only_fallback is None:
                top_level_only_fallback = (candidate, candidate_series)
            candidate_cfo_schedule = snapshot.build_cfo_schedule_series(db, company_id, candidate)
            if candidate_cfo_schedule.get("operating_profit") or candidate_cfo_schedule.get("working_capital_change"):
                statement_type = candidate
                top_level = candidate_series
                break
        if statement_type is None:
            if top_level_only_fallback is None:
                return _empty_result("CONSOLIDATED", single_statement_source)
            statement_type, top_level = top_level_only_fallback

    output_statement_type = "CONSOLIDATED" if single_statement_source else statement_type

    period = snapshot.latest_period(top_level)
    if period is None:
        return _empty_result(output_statement_type, single_statement_source)

    sorted_periods = sorted(top_level.get("cfo", {}).keys())
    prior_period = sorted_periods[-2] if len(sorted_periods) >= 2 else None

    cfo_schedule = snapshot.build_cfo_schedule_series(db, company_id, statement_type)
    cfi_schedule = snapshot.build_cfi_schedule_series(db, company_id, statement_type)
    cff_schedule = snapshot.build_cff_schedule_series(db, company_id, statement_type)

    p_top = snapshot.period_snapshot(top_level, period)
    p_cfo = snapshot.period_snapshot(cfo_schedule, period)
    p_cfi = snapshot.period_snapshot(cfi_schedule, period)
    p_cff = snapshot.period_snapshot(cff_schedule, period)

    cascade = build_income_cascade(db, company_id, statement_type=statement_type)
    revenue_series = {p: entry.get("revenue") for p, entry in cascade.items() if entry.get("revenue") is not None}
    pat_series = {p: entry.get("pat") for p, entry in cascade.items() if entry.get("pat") is not None}

    # ── Reconciliation ──────────────────────────────────────────────────────
    cfo_bridge = reconciliation_module.cfo_bridge(p_cfo)
    cfo_bridge_check = reconciliation_module.cfo_bridge_check(cfo_bridge.get("computed_cfo"), p_top.get("cfo"))

    cash_series_yf = yfinance_metrics.get("cash_series") or {}
    opening_cash = yfinance_value_in_crores(cash_series_yf, prior_period) if prior_period else None
    closing_cash = yfinance_value_in_crores(cash_series_yf, period)
    cash_bridge = reconciliation_module.cash_bridge(opening_cash, p_top.get("cfo"), p_top.get("cfi"), p_top.get("cff"), closing_cash)

    # ── Working capital impact ──────────────────────────────────────────────
    wc_impact = wc_impact_module.working_capital_impact(p_cfo)
    revenue_trend = compute_trends(revenue_series, windows=(1,))
    revenue_growth_pct = revenue_trend.get("1Y", {}).get("pct_change")

    bs_working_capital = (balance_sheet_intelligence_result or {}).get("working_capital") or {}
    dso_series = bs_working_capital.get("dso_series") or {}
    dio_series = bs_working_capital.get("dio_series") or {}
    dpo_series = bs_working_capital.get("dpo_series") or {}
    # DSO/DIO/DPO trend is a directional proxy for balance growth, not the
    # balance itself — this package has no receivables/inventory/payables
    # BALANCE series of its own (only their cash-flow-impact lines above).
    receivables_growth_pct = compute_trends(dso_series, windows=(1,)).get("1Y", {}).get("pct_change") if dso_series else None
    inventory_growth_pct = compute_trends(dio_series, windows=(1,)).get("1Y", {}).get("pct_change") if dio_series else None
    payables_growth_pct = compute_trends(dpo_series, windows=(1,)).get("1Y", {}).get("pct_change") if dpo_series else None

    receivables_drag = wc_impact_module.receivables_cash_drag(receivables_growth_pct, revenue_growth_pct)
    inventory_drag = wc_impact_module.inventory_cash_drag(inventory_growth_pct, revenue_growth_pct)
    payables_support = wc_impact_module.payables_cash_support(p_cfo.get("payables_change"))

    # ── Investing ────────────────────────────────────────────────────────────
    cfi_breakdown = investing_module.cfi_breakdown(p_cfi)
    asset_sale_dependency = investing_module.asset_sale_dependency(p_top.get("cfi"), p_cfi.get("fixed_assets_sold"), p_cfi.get("investments_sold"))
    unallocated_drag = investing_module.unallocated_capital_drag(p_cfi.get("other_investing"), p_top.get("cfo"))

    # ── Financing ────────────────────────────────────────────────────────────
    cff_breakdown = financing_module.cff_breakdown(p_cff)
    debt_financing = financing_module.debt_financing_analysis(p_cff.get("borrowings_raised"), p_cff.get("borrowings_repaid"))
    dividend_analysis = financing_module.dividend_analysis(p_cff.get("dividends_paid"), p_top.get("cfo"), p_top.get("free_cash_flow"))
    buyback_analysis = financing_module.buyback_analysis(p_cfi.get("share_redemption"), p_top.get("free_cash_flow"), p_top.get("cfo"))

    # ── Free cash flow ───────────────────────────────────────────────────────
    fcf_check = fcf_module.compute_fcf(p_top.get("free_cash_flow"), p_top.get("cfo"), p_cfi.get("fixed_assets_purchased"))
    fcf_quality = fcf_module.classify_fcf_quality(top_level.get("free_cash_flow", {}))
    fcf_cross_check = snapshot.yfinance_cross_check(yfinance_metrics, p_top.get("free_cash_flow"), "fcf_series", period)

    # ── Conversion ───────────────────────────────────────────────────────────
    conversion_ratio = conversion_module.cfo_operating_profit_ratio(p_top.get("cfo"), p_cfo.get("operating_profit"))
    prior_conversion_ratio = None
    if prior_period:
        p_cfo_prior = snapshot.period_snapshot(cfo_schedule, prior_period)
        p_top_prior = snapshot.period_snapshot(top_level, prior_period)
        prior_ratio_result = conversion_module.cfo_operating_profit_ratio(p_top_prior.get("cfo"), p_cfo_prior.get("operating_profit"))
        prior_conversion_ratio = prior_ratio_result.get("ratio_pct")
    conversion_trend = conversion_module.classify_conversion_trend(conversion_ratio.get("ratio_pct"), prior_conversion_ratio)
    cumulative_conversion = conversion_module.cumulative_conversion(
        top_level.get("cfo", {}), cfo_schedule.get("operating_profit", {}), pat_series, years=3,
    )

    # ── Volatility ───────────────────────────────────────────────────────────
    volatility = volatility_module.classify_cfo_volatility(top_level.get("cfo", {}))

    # ── Forensic patterns ────────────────────────────────────────────────────
    cfo_trend = compute_trends(top_level.get("cfo", {}), windows=(1,))
    operating_profit_trend = compute_trends(cfo_schedule.get("operating_profit", {}), windows=(1,))
    capex_abs = abs(p_cfi["fixed_assets_purchased"]) if p_cfi.get("fixed_assets_purchased") is not None else None
    forensic_facts = {
        "operating_profit_growth_pct": operating_profit_trend.get("1Y", {}).get("pct_change"),
        "cfo_growth_pct": cfo_trend.get("1Y", {}).get("pct_change"),
        "conversion_declining": conversion_trend == "DETERIORATING_CASH_CONVERSION",
        "receivables_growth_pct": receivables_growth_pct,
        "revenue_growth_pct": revenue_growth_pct,
        "inventory_growth_pct": inventory_growth_pct,
        "inventory_turnover_declining": (inventory_growth_pct or 0) > (revenue_growth_pct or 0) if inventory_growth_pct is not None and revenue_growth_pct is not None else False,
        "payables_growth_pct": payables_growth_pct,
        "cfo": p_top.get("cfo"),
        "capex_abs": capex_abs,
        "borrowings_raised": p_cff.get("borrowings_raised"),
        "equity_raised": None,  # spec item with no source in either provider — never fabricated
        "cff": p_top.get("cff"),
        "cfi": p_top.get("cfi"),
        "fixed_assets_sold": p_cfi.get("fixed_assets_sold"),
        "investments_sold": p_cfi.get("investments_sold"),
    }
    patterns = forensic_patterns.evaluate_all_patterns(forensic_facts)

    # ── Archetype ────────────────────────────────────────────────────────────
    capex_to_cfo_pct = round(capex_abs / p_top["cfo"] * 100, 2) if capex_abs and p_top.get("cfo") else None
    asset_liquidation_triggered = asset_sale_dependency.get("triggered", False) or any(
        pat["pattern_id"] == "NON_OPERATING_CASH_SUPPORT" and pat["status"] == "TRIGGERED" for pat in patterns
    )
    dividends_or_buybacks_present = bool(p_cff.get("dividends_paid")) or buyback_analysis.get("status") == "PARTIAL"
    archetype = archetype_module.classify_cash_flow_archetype(
        cfo_volatility_classification=volatility.get("classification"),
        fcf_quality_classification=fcf_quality.get("classification"),
        latest_conversion_pct=conversion_ratio.get("ratio_pct"),
        capex_to_cfo_pct=capex_to_cfo_pct,
        debt_classification=debt_financing.get("classification"),
        asset_liquidation_triggered=asset_liquidation_triggered,
        dividends_or_buybacks_present=dividends_or_buybacks_present,
    )

    # ── Red flags ────────────────────────────────────────────────────────────
    risk_flags = red_flags_module.evaluate_all_flags({
        "period": period,
        "current_conversion_pct": conversion_ratio.get("ratio_pct"),
        "prior_conversion_pct": prior_conversion_ratio,
        "other_investing": p_cfi.get("other_investing"),
        "annual_cfo": p_top.get("cfo"),
        "cfo_volatility_classification": volatility.get("classification"),
        "fcf_quality_classification": fcf_quality.get("classification"),
        "reconciliation_status": cash_bridge.get("status"),
        "reconciliation_difference_pct": cash_bridge.get("difference_pct"),
    })

    # ── Historical trends ────────────────────────────────────────────────────
    trend_fields = {"cfo": top_level.get("cfo", {}), "cfi": top_level.get("cfi", {}),
                     "cff": top_level.get("cff", {}), "free_cash_flow": top_level.get("free_cash_flow", {})}
    historical_trends = {field: compute_trends(series) for field, series in trend_fields.items() if series}

    # ── Coverage audit ───────────────────────────────────────────────────────
    coverage_facts = {
        "cfo": p_top.get("cfo"), "cfi": p_top.get("cfi"), "cff": p_top.get("cff"),
        "net_cash_flow": p_top.get("net_cash_flow"), "free_cash_flow": p_top.get("free_cash_flow"),
        "operating_profit": p_cfo.get("operating_profit"), "pat": pat_series.get(period),
        "receivables_change": p_cfo.get("receivables_change"), "inventory_change": p_cfo.get("inventory_change"),
        "payables_change": p_cfo.get("payables_change"), "taxes_paid": p_cfo.get("taxes_paid"),
        "fixed_assets_purchased": p_cfi.get("fixed_assets_purchased"), "fixed_assets_sold": p_cfi.get("fixed_assets_sold"),
        "investments_purchased": p_cfi.get("investments_purchased"), "investments_sold": p_cfi.get("investments_sold"),
        "interest_received": p_cfi.get("interest_received"), "borrowings_raised": p_cff.get("borrowings_raised"),
        "borrowings_repaid": p_cff.get("borrowings_repaid"), "interest_paid": p_cff.get("interest_paid"),
        "dividends_paid": p_cff.get("dividends_paid"), "opening_cash": opening_cash, "closing_cash": closing_cash,
    }
    coverage = coverage_module.compute_coverage_audit(coverage_facts)

    return {
        "period": period,
        "statement_type": output_statement_type,
        "single_statement_source": single_statement_source,
        "reconciliation": {
            "cfo_bridge": cfo_bridge,
            "cfo_bridge_check": cfo_bridge_check,
            "cash_bridge": cash_bridge,
        },
        "working_capital_impact": {
            **wc_impact,
            "receivables_cash_drag": receivables_drag,
            "inventory_cash_drag": inventory_drag,
            "payables_cash_support": payables_support,
        },
        "investing": {
            "breakdown": cfi_breakdown,
            "asset_sale_dependency": asset_sale_dependency,
            "unallocated_capital_drag": unallocated_drag,
        },
        "financing": {
            "breakdown": cff_breakdown,
            "debt_financing": debt_financing,
            "dividend_analysis": dividend_analysis,
            "buyback_analysis": buyback_analysis,
        },
        "free_cash_flow": {
            "reconciliation": fcf_check,
            "quality": fcf_quality,
            "yfinance_cross_check": fcf_cross_check,
        },
        "conversion": {
            "latest": conversion_ratio,
            "prior_ratio_pct": prior_conversion_ratio,
            "trend": conversion_trend,
            "cumulative_3y": cumulative_conversion,
        },
        "volatility": volatility,
        "forensic_patterns": patterns,
        "archetype": archetype,
        "risk_flags": risk_flags,
        "historical_trends": historical_trends,
        "coverage": coverage,
    }
