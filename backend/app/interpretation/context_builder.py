"""Context Builder — Stage L0, second half. Summary.md section 19: don't
blindly send the whole Master Company Object to every prompt. Each report
section gets only the slice it actually needs, so a 3B local model isn't
drowning in irrelevant JSON on every call.

Section ids here match the modular prompt files planned for Stage L1
(`app/interpretation/prompts/`) — this module has no LLM dependency itself,
it's pure dict slicing so it can be unit-verified without a model running.
"""
from __future__ import annotations

_MAX_RISKS = 5
_MAX_CATALYSTS = 5
_MAX_NEWS = 5


def _trim(items: list, n: int) -> list:
    return (items or [])[:n]


def _slim_metrics(key_metrics: list[dict]) -> list[dict]:
    """Sector key_metrics carry weight/importance/description/na_message —
    useful for the scoring engine, pure noise for a small local model being
    asked to write 2-3 sentences of interpretation. Real reliability issue
    found 2026-09-13: llama3.2:3b sometimes just echoes one raw input dict
    back as its "answer" when a context has ~8 of these bulky objects in a
    row — trimmed to the 5 fields interpretation actually needs, and
    unavailable metrics (value is None) dropped entirely rather than shown
    as another object to wade through."""
    out = []
    for m in key_metrics or []:
        if m.get("value") is None:
            continue
        out.append({
            "name": m.get("name"), "label": m.get("label"),
            "value": m.get("value"), "unit": m.get("unit"), "status": m.get("status"),
        })
    return out


def build_context(master: dict, section_id: str) -> dict:
    company = master.get("company", {})
    sector = master.get("sector", {})

    if section_id == "company_snapshot":
        return {
            "company": company,
            "business": master.get("business"),
            "sector_name": sector.get("name"),
        }

    if section_id == "business_model":
        return {
            "company": company,
            "business": master.get("business"),
            "operations": master.get("operations"),
            "orders": master.get("orders"),
            "sector_name": sector.get("name"),
        }

    if section_id == "growth_drivers":
        return {
            "company": company,
            "sector_key_metrics": _slim_metrics(sector.get("key_metrics")),
            "guidance": {
                "forward_estimates": master.get("guidance", {}).get("forward_estimates"),
            },
            "catalysts": _trim(master.get("catalysts"), _MAX_CATALYSTS),
            "expansion": master.get("expansion"),
        }

    if section_id == "financial_interpretation":
        ratios = master.get("ratios") or {}
        focus_keys = (
            "revenue_cagr_3y", "pat_cagr_3y", "eps_cagr_3y", "gross_margin", "ebitda_margin",
            "pat_margin", "roce", "roe", "roic", "nim", "roa",
        )
        return {
            "company": company,
            "ratios": {k: ratios[k] for k in focus_keys if k in ratios and ratios[k] is not None},
            "sector_key_metrics": _slim_metrics(sector.get("key_metrics")),
        }

    if section_id == "balance_sheet_interpretation":
        return {
            "company": company,
            "balance_sheet": (master.get("financials") or {}).get("balance"),
            "leverage_ratios": {
                k: v for k, v in (master.get("ratios") or {}).items()
                if k in ("debt_to_equity", "net_debt_to_ebitda", "interest_coverage", "current_ratio")
            },
            "shareholding": master.get("shareholding"),
        }

    if section_id == "cashflow_interpretation":
        return {
            "company": company,
            "cash_flow": (master.get("financials") or {}).get("cash_flow"),
            "cash_ratios": {
                k: v for k, v in (master.get("ratios") or {}).items()
                if k in ("fcf_to_pat", "cfo_to_pat", "fcf_yield")
            },
        }

    if section_id == "valuation_interpretation":
        return {
            "company": company,
            "valuation": master.get("valuation"),
            "analyst_consensus": master.get("guidance", {}).get("analyst_consensus"),
        }

    if section_id == "risk_analysis":
        return {
            "company": company,
            "risks": _trim(master.get("risks"), _MAX_RISKS),
            "governance_events": master.get("shareholding", {}).get("events"),
            "sector_red_flags": [f for f in (sector.get("red_flags") or []) if f.get("triggered")],
        }

    if section_id == "sector_analysis":
        return {
            "company": company,
            "sector_name": sector.get("name"),
            "sector_score": sector.get("sector_score"),
            "key_metrics": _slim_metrics(sector.get("key_metrics")),
        }

    if section_id == "segment_performance":
        return {
            "company": company,
            "segments": master.get("business", {}).get("segments"),
        }

    if section_id == "recent_developments":
        return {
            "company": company,
            "recent_news": _trim(master.get("news"), _MAX_NEWS),
        }

    if section_id == "final_conclusion":
        return {
            "company": company,
            "scores": master.get("scores"),
            "valuation": master.get("valuation"),
            "top_risks": _trim(master.get("risks"), 3),
            "top_catalysts": _trim(master.get("catalysts"), 3),
            "sector_name": sector.get("name"),
            "recent_news": _trim(master.get("news"), _MAX_NEWS),
        }

    if section_id.startswith("pnl_"):
        return _pnl_context(master, section_id)

    if section_id.startswith("pl_"):
        return _pl_intelligence_context(master, section_id)

    if section_id.startswith("bs_"):
        return _balance_sheet_intelligence_context(master, section_id)

    if section_id.startswith("cf_"):
        return _cash_flow_intelligence_context(master, section_id)

    raise ValueError(f"Unknown interpretation section_id: {section_id!r}")


def _recent_years(series: dict, n: int = 5) -> dict:
    """Last `n` fiscal years plus TTM if present — the full 12-year table
    is too much for every P&L prompt; each one gets the recent window plus
    the already-computed CAGR/average stats for longer-term context."""
    fiscal = sorted((k for k in (series or {}) if k != "TTM"))
    keep = set(fiscal[-n:])
    return {k: v for k, v in (series or {}).items() if k in keep or k == "TTM"}


def _pnl_context(master: dict, section_id: str) -> dict:
    company = master.get("company", {})
    pnl = master.get("pnl_analysis") or {}
    growth = pnl.get("growth") or {}
    common = {"company": company, "years_of_data": pnl.get("years_of_data")}

    if section_id == "pnl_sales_growth":
        return {
            **common,
            "sales_recent": _recent_years((pnl.get("table") or {}).get("sales")),
            "sales_cagr": growth.get("sales_cagr"),
            "sales_ttm_growth": growth.get("sales_ttm_growth"),
            "sales_yoy_recent": _recent_years(growth.get("sales_yoy")),
            "long_vs_short_trend": growth.get("long_vs_short_trend"),
            "consistency": pnl.get("consistency"),
        }

    if section_id == "pnl_profit_growth":
        return {
            **common,
            "pbt_cagr": growth.get("pbt_cagr"),
            "profit_cagr": growth.get("profit_cagr"),
            "profit_ttm_growth": growth.get("profit_ttm_growth"),
            "sales_cagr": growth.get("sales_cagr"),
            "profit_yoy_recent": _recent_years(growth.get("profit_yoy")),
            "profit_vs_sales_direction_5y": growth.get("profit_vs_sales_direction_5y"),
        }

    if section_id == "pnl_margin_analysis":
        return {**common, "margins": pnl.get("margins")}

    if section_id == "pnl_earnings_quality":
        return {
            **common,
            "interest_coverage": pnl.get("interest_coverage"),
            "other_income_dependency": pnl.get("other_income_dependency"),
            "depreciation": pnl.get("depreciation"),
            "inflection_points": pnl.get("inflection_points"),
        }

    if section_id == "pnl_eps_analysis":
        return {
            **common,
            "eps_cagr": growth.get("eps_cagr"),
            "eps_yoy_recent": _recent_years(growth.get("eps_yoy")),
            "profit_cagr": growth.get("profit_cagr"),
            "eps_vs_profit_direction_5y": growth.get("eps_vs_profit_direction_5y"),
        }

    if section_id == "pnl_conclusion":
        return {
            **common,
            "quality_score": pnl.get("quality_score"),
            "red_flags": pnl.get("red_flags"),
            "positive_signals": pnl.get("positive_signals"),
            "roe": {k: v for k, v in (pnl.get("roe") or {}).items() if k != "by_year"},
            "dividend": pnl.get("dividend"),
            "stock_price_cagr": pnl.get("stock_price_cagr"),
        }

    raise ValueError(f"Unknown P&L interpretation section_id: {section_id!r}")


def _commentary_excerpts(pli: dict, topic: str) -> list[str]:
    """Trims retrieved concall chunks to just the text a small local model
    needs — same rationale as `_slim_metrics` above: raw retrieval dicts
    carry similarity/section/transcript_id fields that are useful for
    debugging, not for a model being asked to write 2-3 sentences."""
    chunks = (pli.get("management_commentary") or {}).get(topic) or []
    return [c["chunk_text"] for c in chunks if c.get("chunk_text")]


def _pl_intelligence_context(master: dict, section_id: str) -> dict:
    company = master.get("company", {})
    pli = master.get("pl_intelligence") or {}
    common = {"company": company, "period": pli.get("period"), "statement_type": pli.get("statement_type")}

    if section_id == "pl_peer_positioning":
        return {**common, "peer_percentiles": pli.get("peer_percentiles")}

    if section_id == "pl_standalone_consolidated":
        return {**common, "structure": pli.get("structure")}

    if section_id == "pl_margin_headroom":
        return {
            **common,
            "margin_headroom": pli.get("margin_headroom"),
            "management_commentary": _commentary_excerpts(pli, "margin_headroom"),
        }

    if section_id == "pl_doubling_velocity":
        return {
            **common,
            "doubling": pli.get("doubling"),
            "operating_leverage": (pli.get("diagnostics") or {}).get("operating_leverage"),
        }

    if section_id == "pl_earnings_quality_v2":
        return {
            **common,
            "earnings_quality": pli.get("earnings_quality"),
            "non_core_income": pli.get("non_core_income"),
            "management_commentary": _commentary_excerpts(pli, "earnings_quality"),
        }

    raise ValueError(f"Unknown P&L Intelligence interpretation section_id: {section_id!r}")


def _balance_sheet_intelligence_context(master: dict, section_id: str) -> dict:
    company = master.get("company", {})
    bsi = master.get("balance_sheet_intelligence") or {}
    common = {"company": company, "period": bsi.get("period"), "statement_type": bsi.get("statement_type")}

    if section_id == "bs_structure_and_liquidity":
        return {
            **common,
            "balance_sheet_integrity": bsi.get("balance_sheet_integrity"),
            "house": bsi.get("house"),
            "common_size": bsi.get("common_size"),
        }

    if section_id == "bs_working_capital":
        return {**common, "working_capital": bsi.get("working_capital")}

    if section_id == "bs_leverage_and_roce":
        return {**common, "derived_metrics": bsi.get("derived_metrics")}

    if section_id == "bs_archetype_and_risk":
        triggered_flags = [f for f in (bsi.get("risk_flags") or []) if f.get("status") == "TRIGGERED"]
        return {**common, "archetype": bsi.get("archetype"), "triggered_risk_flags": triggered_flags}

    if section_id == "bs_coverage_summary":
        coverage = bsi.get("coverage") or {}
        from app.calculations.balance_sheet_intelligence.coverage import top_source_gaps
        return {
            **common,
            "coverage_pct": coverage.get("coverage_pct"),
            "top_source_gaps": top_source_gaps(coverage) if coverage.get("metrics") else [],
        }

    raise ValueError(f"Unknown Balance Sheet Intelligence interpretation section_id: {section_id!r}")


def _cash_flow_intelligence_context(master: dict, section_id: str) -> dict:
    company = master.get("company", {})
    cfi = master.get("cash_flow_intelligence") or {}
    common = {"company": company, "period": cfi.get("period"), "statement_type": cfi.get("statement_type")}

    if section_id == "cf_reconciliation_and_conversion":
        reconciliation = cfi.get("reconciliation") or {}
        return {
            **common,
            "cfo_bridge": reconciliation.get("cfo_bridge"),
            "cfo_bridge_check": reconciliation.get("cfo_bridge_check"),
            "conversion": cfi.get("conversion"),
        }

    if section_id == "cf_working_capital_and_investing":
        return {
            **common,
            "working_capital_impact": cfi.get("working_capital_impact"),
            "investing": cfi.get("investing"),
        }

    if section_id == "cf_financing_and_fcf":
        return {
            **common,
            "financing": cfi.get("financing"),
            "free_cash_flow": cfi.get("free_cash_flow"),
        }

    if section_id == "cf_archetype_and_risk":
        triggered_flags = [f for f in (cfi.get("risk_flags") or []) if f.get("status") == "TRIGGERED"]
        triggered_patterns = [p for p in (cfi.get("forensic_patterns") or []) if p.get("status") == "TRIGGERED"]
        return {
            **common,
            "archetype": cfi.get("archetype"),
            "triggered_risk_flags": triggered_flags,
            "triggered_forensic_patterns": triggered_patterns,
        }

    if section_id == "cf_coverage_summary":
        coverage = cfi.get("coverage") or {}
        from app.calculations.cash_flow_intelligence.coverage import top_source_gaps
        return {
            **common,
            "coverage_pct": coverage.get("coverage_pct"),
            "top_source_gaps": top_source_gaps(coverage) if coverage.get("metrics") else [],
        }

    raise ValueError(f"Unknown Cash Flow Intelligence interpretation section_id: {section_id!r}")
