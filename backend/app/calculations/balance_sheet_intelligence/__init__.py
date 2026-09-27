"""Balance Sheet Analysis Engine — implements `Important md files/
balance_sheet_analysis_engine_consolidated.md`'s 77-section spec, scoped to
what this app's two real data sources actually support (see
`canonical_fields.py` for the full accounting, and the plan this package
implements for the reasoning behind every deviation).

Computed fresh on every call, no persisted score table (unlike
`pl_intelligence`'s versioned Master Score) — nothing here is an expensive
LLM call worth caching, and the archetype/red-flag output is deterministic
and cheap to recompute from ledger data already present.

Two sources, blended per the user's explicit decision: Screener.in (12Y,
standalone+consolidated, already ingested) is the source for the coarse
balance-sheet-house/net-worth/leverage/archetype layer; the existing
yfinance-sourced `app/calculations/engine.py::MetricsCalculator` output
(passed in as `yfinance_metrics`, sourced from `FundamentalAnalysis.metrics`
— this package has no DB/network access of its own for it) stays the
source for working-capital ratios (DSO/DIO/DPO/CCC/Current/Quick/Cash
Ratio), which Screener's condensed balance sheet can't separate out at all.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.balance_sheet_intelligence import (
    archetype as archetype_module,
    common_size as common_size_module,
    coverage as coverage_module,
    historical_trends as trends_module,
    leverage as leverage_module,
    red_flags as red_flags_module,
    roce as roce_module,
    sector_routing,
    snapshot,
    sources_applications,
    working_capital as working_capital_module,
)
from app.calculations.balance_sheet_intelligence.integrity import integrity_by_period, validate_accounting_identity
from app.calculations.pl_intelligence.cascade import build_income_cascade
from app.calculations.statement_type_resolution import prefer_current_statement_type
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock

_STATEMENT_TYPE_FALLBACK_ORDER = ("CONSOLIDATED", "STANDALONE")


def _empty_result(statement_type: str, single_statement_source: bool = False) -> dict:
    return {
        "period": None, "statement_type": statement_type,
        "single_statement_source": single_statement_source,
        "balance_sheet_integrity": {"status": "MISSING_DATA"},
        "assets": {}, "liabilities": {}, "equity": {},
        "derived_metrics": {}, "house": {}, "common_size": {}, "historical_common_size": {},
        "working_capital": {}, "archetype": {}, "risk_flags": [],
        "historical_trends": {}, "coverage": coverage_module.compute_coverage_audit({}),
        "financial_institution_summary": None,
    }


def compute_balance_sheet_intelligence(
    db: Session,
    company_id: str,
    sector_name: str | None = None,
    yfinance_metrics: dict | None = None,
    statement_type: str | None = None,
) -> dict:
    """Orchestrates every module in this package into one combined dict for
    ONE company at its latest available Screener period. Never raises — a
    company with no Screener balance-sheet data at all returns a
    mostly-empty, `MISSING_DATA`-tagged shape, matching every other calc
    module's contract.

    `statement_type` is normally left `None` — the function then tries
    `_STATEMENT_TYPE_FALLBACK_ORDER` (CONSOLIDATED first) and picks
    whichever actually has data. Pass an explicit `"CONSOLIDATED"` or
    `"STANDALONE"` (the frontend's toggle, `app/routes/
    balance_sheet_intelligence.py`) to force exactly that one, with NO
    fallback — a user who deliberately asks for STANDALONE should see
    "not available" rather than being silently redirected back to
    CONSOLIDATED.

    Exception: when a company has NO consolidated data at all (confirmed
    live on Netweb Technologies / Bandhan Bank — 0 rows directly from
    Screener.in, not an ingestion gap; these companies have no subsidiaries
    to consolidate), `single_statement_source` below is True and the one
    real dataset is always served regardless of what was requested,
    labeled "CONSOLIDATED" in the output — for a subsidiary-less company,
    standalone figures already are what consolidated figures would be.
    Companies with genuine data on both sides are unaffected."""
    yfinance_metrics = yfinance_metrics or {}

    series_by_type = {
        candidate: snapshot.build_screener_balance_sheet_series(db, company_id, statement_type=candidate)
        for candidate in _STATEMENT_TYPE_FALLBACK_ORDER
    }
    has_data = {t: bool(s.get("total_assets")) for t, s in series_by_type.items()}
    single_statement_source = has_data["CONSOLIDATED"] != has_data["STANDALONE"]

    if single_statement_source:
        candidates = ("CONSOLIDATED",) if has_data["CONSOLIDATED"] else ("STANDALONE",)
    elif statement_type:
        candidates = (statement_type,)
    else:
        # Auto-detect: try whichever side is actually CURRENT first, not
        # just CONSOLIDATED-always-first — see statement_type_resolution.py.
        preferred = prefer_current_statement_type(
            {t: snapshot.latest_period(series_by_type[t]) for t in _STATEMENT_TYPE_FALLBACK_ORDER}
        )
        candidates = (preferred,) + tuple(t for t in _STATEMENT_TYPE_FALLBACK_ORDER if t != preferred)

    resolved_statement_type = None
    series = {}
    for candidate in candidates:
        if has_data[candidate]:
            resolved_statement_type = candidate
            series = series_by_type[candidate]
            break
    if resolved_statement_type is None:
        return _empty_result(statement_type or "CONSOLIDATED", single_statement_source)
    statement_type = resolved_statement_type
    output_statement_type = "CONSOLIDATED" if single_statement_source else statement_type

    period = snapshot.latest_period(series)
    if period is None:
        return _empty_result(output_statement_type, single_statement_source)
    p = snapshot.period_snapshot(series, period)

    # ── Golden rule: gate everything else on this period's integrity ───────
    integrity_result = validate_accounting_identity(p.get("total_assets"), p.get("total_liabilities"))
    if integrity_result["status"] == "BALANCE_SHEET_INTEGRITY_ERROR":
        return {
            "period": period, "statement_type": output_statement_type,
            "single_statement_source": single_statement_source,
            "balance_sheet_integrity": integrity_result,
            "assets": {}, "liabilities": {}, "equity": {},
            "derived_metrics": {}, "house": {}, "common_size": {}, "historical_common_size": {},
            "working_capital": {}, "archetype": {}, "risk_flags": [],
            "historical_trends": {}, "coverage": coverage_module.compute_coverage_audit({}),
            "financial_institution_summary": None,
        }

    stock = db.query(Stock).filter_by(id=company_id).first()
    sector = sector_name or (stock.sector if stock else None)
    is_bank = sector_routing.is_financial_institution(sector)
    # Financial institutions have no inventory concept at all (stronger than
    # "not material"); everyone else goes through the sector/basic_industry
    # materiality call (Healthcare split hospital-vs-pharma by basic_industry).
    is_inventory_material = (not is_bank) and sector_routing.is_inventory_material(
        sector, stock.basic_industry if stock else None
    )

    # ── Cross-source bridge: yfinance cash/current-liabilities, in Crores ──
    cash_series_yf = yfinance_metrics.get("cash_series") or {}
    cl_series_yf = yfinance_metrics.get("current_liabilities_series") or {}
    cash_value = snapshot.yfinance_value_in_crores(cash_series_yf, period)
    current_liabilities_value = snapshot.yfinance_value_in_crores(cl_series_yf, period)

    # ── EBIT/EBITDA/revenue, reused from pl_intelligence (not recomputed) ──
    cascade = build_income_cascade(db, company_id, statement_type=statement_type)
    pnl_statement_type = statement_type
    if not cascade:
        # The P&L ledger can have a genuinely different real statement type
        # than the balance sheet — real gap found live on TANLA
        # (2026-09-23, user's own report — "Balance sheet only 27%
        # available why"): this package resolved statement_type=CONSOLIDATED
        # from its OWN Screener balance-sheet series (real consolidated
        # data exists there), but TANLA's pnl_sales ledger only ever has
        # STANDALONE rows — no CONSOLIDATED P&L was ever ingested. Calling
        # build_income_cascade() with the balance sheet's resolved type
        # therefore silently came back empty, and every EBIT-derived
        # metric here (ROCE, interest coverage, EBIT margin) went missing
        # even though pl_intelligence's OWN single_statement_source
        # fallback (a different code path, same underlying data) finds
        # and correctly serves the real STANDALONE cascade. Trying the
        # other type before giving up mirrors that same fallback here.
        fallback_type = "STANDALONE" if statement_type == "CONSOLIDATED" else "CONSOLIDATED"
        cascade = build_income_cascade(db, company_id, statement_type=fallback_type)
        if cascade:
            pnl_statement_type = fallback_type
    cascade_period = period if period in cascade else (max(cascade.keys()) if cascade else None)
    ebit = cascade.get(cascade_period, {}).get("ebit") if cascade_period else None
    ebitda = cascade.get(cascade_period, {}).get("ebitda") if cascade_period else None
    revenue = cascade.get(cascade_period, {}).get("revenue") if cascade_period else None
    pat = cascade.get(cascade_period, {}).get("pat") if cascade_period else None

    # ── Withhold capital-employed-based ROCE when the P&L basis doesn't
    # match the balance sheet's (2026-09-23 fix, found alongside the
    # fallback above): when the P&L cascade fell back to `fallback_type`,
    # `p["total_assets"]` (built from the BALANCE SHEET's own resolved
    # `statement_type`) is on a DIFFERENT statement basis than
    # `ebit`/`ebitda`/`revenue` above. Blending them — e.g. CONSOLIDATED
    # total_assets (whole group, ~3730 Cr on TANLA) with STANDALONE ebit
    # (parent entity only, ~7 Cr) — produced a nonsensical ROCE of 0.28%
    # instead of the real ~25%, confirmed live on TANLA (FA-2026-000042).
    # A first attempt tried re-fetching total_assets on the FALLBACK
    # type's own basis instead — but `current_liabilities_value` (below)
    # is cross-sourced from yfinance with no statement-type tag of its
    # own, and confirmed live to be scaled to the CONSOLIDATED group, so
    # pairing IT with a STANDALONE total_assets instead produced a
    # NEGATIVE capital_employed — a different but equally wrong number.
    # Since which basis yfinance's current_liabilities actually matches
    # can't be determined here, the only safe choice when the P&L basis
    # genuinely diverges from the balance sheet's is to withhold ROCE/
    # capital_employed_turnover entirely (MISSING_INPUT, via
    # `total_assets=None` below) rather than guess a second time —
    # matching `roce.py`'s own stated discipline ("no silently mixed
    # definitions") over fabricating a number that LOOKS available.
    # `ebit_margin` (ebit/revenue, no balance-sheet input at all) is
    # unaffected and stays available either way — see the
    # cascade-fallback test this sits alongside.
    roce_total_assets = p.get("total_assets") if pnl_statement_type == statement_type else None
    # Real gap found live on TANLA alongside the fallback fix above
    # (2026-09-23): this was hardcoded None unconditionally further down
    # (coverage_facts["interest_expense"]) even though the same cascade
    # already carries it as "finance_cost" — interest_coverage showed
    # MISSING_INPUT for every company, not just ones needing the
    # statement-type fallback, since nothing ever populated this field.
    interest_expense = cascade.get(cascade_period, {}).get("finance_cost") if cascade_period else None

    house = sources_applications.compute_house(p, cash_value=cash_value)
    common_size = common_size_module.compute_common_size(p)
    historical_common_size = common_size_module.historical_common_size(series)
    # `net_debt_to_ebitda` pairs `p["borrowings"]` (on `statement_type`'s
    # basis) with `ebitda` (possibly on the fallback `pnl_statement_type`
    # basis) — same cross-type-blend risk as ROCE above. Every other
    # `leverage` field is a pure balance-sheet ratio and unaffected, so
    # only `ebitda` itself is withheld here rather than re-deriving a
    # second borrowings figure on the P&L's basis.
    leverage = leverage_module.compute_leverage(
        p.get("equity_capital"), p.get("reserves"), p.get("borrowings"),
        p.get("total_liabilities"), p.get("total_assets"), cash_value,
        ebitda if pnl_statement_type == statement_type else None,
    )
    roce = roce_module.compute_roce(roce_total_assets, current_liabilities_value, ebit, revenue)

    financial_institution_summary = sector_routing.financial_institution_summary(p) if is_bank else None

    working_capital: dict = {}
    if not is_bank:
        screener_ratios_history = snapshot.screener_ratios_history(db, company_id, statement_type)
        working_capital = working_capital_module.compute_working_capital_blend(
            yfinance_metrics, screener_ratios_history,
        )
        # Raw current-assets isn't exposed as its own `engine.py` series
        # (only the ratio is) — net/gross working-capital AMOUNTS therefore
        # pass `current_assets=None` rather than reverse-deriving it from
        # `current_ratio * current_liabilities` (would silently assume the
        # ratio's own rounding is exact).
        working_capital["amounts"] = working_capital_module.compute_working_capital_amounts(None, current_liabilities_value, revenue)

    # ── Historical trends (Screener series; cross-source lines kept out — a
    # multi-year yfinance series isn't reliably period-aligned to Screener's
    # own without per-period cross-lookups this function doesn't need for
    # trends of Screener-native lines) ──────────────────────────────────────
    trend_fields = ("fixed_assets", "capital_work_in_progress", "investments", "other_assets",
                     "borrowings", "other_liabilities", "reserves", "equity_capital")
    historical_trends = trends_module.compute_trends_for_lines({f: series.get(f, {}) for f in trend_fields})
    net_worth_series = {
        yr: (series.get("equity_capital", {}).get(yr, 0) or 0) + (series.get("reserves", {}).get(yr, 0) or 0)
        for yr in series.get("reserves", {})
    }
    historical_trends["net_worth"] = trends_module.compute_trends(net_worth_series)

    debt_pct_change_3y = historical_trends.get("borrowings", {}).get("3Y", {}).get("pct_change")
    cash_investments_pct_assets = None
    if common_size.get("investments") is not None:
        cash_pct = (cash_value / p["total_assets"] * 100) if cash_value and p.get("total_assets") else 0.0
        cash_investments_pct_assets = round(cash_pct + common_size.get("investments", 0.0), 2)
    wc_pct_revenue = working_capital.get("amounts", {}).get("working_capital_pct_revenue") if working_capital else None
    ccc_pct_change_3y = None
    cash_pct_change_3y = None  # cash is cross-sourced yfinance and not Screener-series-based; left unavailable for the 3Y trend here

    archetype = archetype_module.classify_archetype(
        cash_investments_pct_assets=cash_investments_pct_assets,
        debt_to_equity=leverage.get("debt_to_equity"),
        working_capital_pct_revenue=wc_pct_revenue,
        debt_pct_change_3y=debt_pct_change_3y,
        cash_pct_change_3y=cash_pct_change_3y,
        ccc_pct_change_3y=ccc_pct_change_3y,
    ) if not is_bank else {"classification": "NOT_APPLICABLE", "evidence": ["Financial institution — see financial_institution_summary"], "confidence": "UNAVAILABLE"}

    cfo_series = snapshot.build_cash_flow_series(db, company_id, statement_type).get("operating_cash_flow", {})
    cfo_latest = cfo_series.get(period)
    cfo_trend = trends_module.compute_trends(cfo_series, windows=(1, 3))
    cumulative_3y_cfo = None
    cfo_3y_periods = sorted(cfo_series.keys(), key=lambda pd: snapshot.fiscal_year(pd) or pd)[-3:]
    if len(cfo_3y_periods) == 3:
        cumulative_3y_cfo = sum(cfo_series[pd] for pd in cfo_3y_periods)
    pat_series = {pd: entry.get("pat") for pd, entry in cascade.items() if entry.get("pat") is not None}
    cumulative_3y_pat = None
    pat_3y_periods = sorted(pat_series.keys(), key=lambda pd: snapshot.fiscal_year(pd) or pd)[-3:]
    if len(pat_3y_periods) == 3:
        cumulative_3y_pat = sum(pat_series[pd] for pd in pat_3y_periods)

    risk_flags = red_flags_module.evaluate_all_flags({
        "period": period,
        "integrity_status": integrity_result["status"],
        "debt_to_equity": leverage.get("debt_to_equity"),
        "cfo_latest": cfo_latest,
        "cumulative_3y_cfo": cumulative_3y_cfo,
        "cumulative_3y_pat": cumulative_3y_pat,
        "cfo_pct_change": cfo_trend.get("1Y", {}).get("pct_change"),
        "equity_capital_growth_pct": historical_trends.get("equity_capital", {}).get("1Y", {}).get("pct_change"),
        "fixed_assets_growth_pct": historical_trends.get("fixed_assets", {}).get("1Y", {}).get("pct_change"),
        "borrowings_pct_change": historical_trends.get("borrowings", {}).get("1Y", {}).get("pct_change"),
        "dso_pct_change": (trends_module.compute_trends(working_capital["dso_series"], windows=(1,)).get("1Y", {}).get("pct_change")
                           if working_capital.get("dso_series") else None),
        "inventory_days_pct_change": (trends_module.compute_trends(working_capital["dio_series"], windows=(1,)).get("1Y", {}).get("pct_change")
                                       if working_capital.get("dio_series") else None),
        "ccc_pct_change": (trends_module.compute_trends(working_capital["ccc_series"], windows=(1,)).get("1Y", {}).get("pct_change")
                            if working_capital.get("ccc_series") else None),
    })

    # NSE annual-report note extraction (app/ingestion/
    # annual_report_ingestion.py's "ppe"/"other_liabilities" areas) — always
    # stored under STANDALONE (matching the existing banking-metric
    # convention; there's one such note per company/period, not a
    # statement-type-distinguished pair), independent of whichever
    # statement_type the Screener-sourced balance sheet above resolved to.
    # `get_latest_period_value` degrades gracefully to None when the
    # ingestion stage hasn't run/found anything for this company yet.
    gross_ppe_row = metric_store.get_latest_period_value(db, company_id, "gross_ppe", statement_type="STANDALONE")
    accumulated_depreciation_row = metric_store.get_latest_period_value(db, company_id, "accumulated_depreciation", statement_type="STANDALONE")
    accrued_expenses_row = metric_store.get_latest_period_value(db, company_id, "accrued_expenses", statement_type="STANDALONE")
    deferred_revenue_row = metric_store.get_latest_period_value(db, company_id, "deferred_revenue", statement_type="STANDALONE")
    gross_ppe_value = float(gross_ppe_row.value) if gross_ppe_row else None
    accumulated_depreciation_value = float(accumulated_depreciation_row.value) if accumulated_depreciation_row else None
    accrued_expenses_value = float(accrued_expenses_row.value) if accrued_expenses_row else None
    deferred_revenue_value = float(deferred_revenue_row.value) if deferred_revenue_row else None

    coverage_facts = {
        "cash": cash_value, "receivables": None, "inventory": None, "payables": None,
        "borrowings": p.get("borrowings"), "capital_work_in_progress": p.get("capital_work_in_progress"),
        "equity_capital": p.get("equity_capital"), "reserves": p.get("reserves"),
        "total_assets": p.get("total_assets"), "total_liabilities": p.get("total_liabilities"),
        "current_assets": None, "current_liabilities": current_liabilities_value,
        "ebit": ebit, "interest_expense": interest_expense,
        "gross_ppe": gross_ppe_value, "accrued_expenses": accrued_expenses_value,
        "deferred_revenue": deferred_revenue_value,
    }
    if not is_bank and working_capital:
        coverage_facts["receivables"] = working_capital.get("dso_series", {}).get(working_capital.get("latest_period"))
        coverage_facts["inventory"] = working_capital.get("dio_series", {}).get(working_capital.get("latest_period"))
        coverage_facts["payables"] = working_capital.get("dpo_series", {}).get(working_capital.get("latest_period"))
    coverage = coverage_module.compute_coverage_audit(coverage_facts, is_inventory_material=is_inventory_material, sector_name=sector)

    return {
        "period": period,
        "statement_type": output_statement_type,
        "single_statement_source": single_statement_source,
        "balance_sheet_integrity": integrity_result,
        "assets": {
            **{k: p.get(k) for k in ("fixed_assets", "capital_work_in_progress", "investments", "other_assets", "total_assets")},
            "gross_ppe": gross_ppe_value, "accumulated_depreciation": accumulated_depreciation_value,
        },
        "liabilities": {
            **{k: p.get(k) for k in ("borrowings", "other_liabilities", "deposits")},
            "accrued_expenses": accrued_expenses_value, "deferred_revenue": deferred_revenue_value,
        },
        "equity": {"equity_capital": p.get("equity_capital"), "reserves": p.get("reserves"), "total_equity": leverage.get("total_equity")},
        "derived_metrics": {**leverage, **roce},
        "house": house,
        "common_size": common_size,
        "historical_common_size": historical_common_size,
        "working_capital": working_capital,
        "archetype": archetype,
        "risk_flags": risk_flags,
        "historical_trends": historical_trends,
        "coverage": coverage,
        "financial_institution_summary": financial_institution_summary,
    }
