"""Master Company Data Object — Stage L0 of the Llama Report Interpretation
Architecture (see `Sector md files/Summary.md`, section 6).

This is a read-only assembly layer: it invents nothing and fetches nothing
new. Every field is pulled from data that already exists elsewhere in this
app (the `FundamentalAnalysis` row's JSON columns, plus the governance/
market-intelligence tables added 2026-09-13) and reshaped into the object
Summary.md's interpretation layer expects. Sections the app has no real
data source for yet (order book, capacity, capex) are left explicitly
`"not_available": true` rather than inferred or fabricated from prose —
see Summary.md section 4's "Llama SHOULD NOT invent missing data" rule,
which applies just as much to this assembly step as to the LLM calls that
will consume it.

`business.about`/`business.key_points` (Screener.in prose) are tagged
`"structured": false` so a prompt never mistakes that prose for verified
numeric fields. `business.segments`, however, IS real structured data as
of the Deep Research System's Stage R1 (2026-09-14) — real per-segment
revenue history from TradingView, with growth %/revenue-mix % computed
here in Python (see `_business_segments()`), not left for the model to
derive. Previously always an empty placeholder; customers/geographies/
products remain unfilled (no source for those yet).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import (
    AnalystConsensus, BusinessSegment, CompanyNews, CompanySummary, CorporateAction,
    EarningsCalendar, ForwardEstimate, FundamentalAnalysis, GovernanceEvent,
    InsiderActivity, Shareholding, ShareholdingScreener,
)


def _row(obj, *fields) -> dict:
    return {f: getattr(obj, f) for f in fields}


def _num(v):
    """JSON-safe float (Decimal -> float), preserving None."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sector_metrics_with_provenance(db: Session, company_id: str, key_metrics: list[dict]) -> list[dict]:
    """Attach source/confidence/period to each sector key_metric that has a
    real ledger row (non-yfinance metrics only — yfinance-derived ones are
    tagged with a fixed source since they're read from the metrics dict,
    not the ledger)."""
    out = []
    for m in key_metrics or []:
        entry = dict(m)
        if m.get("value") is not None:
            row = metric_store.get_latest_period_value(db, company_id, m["name"])
            if row is not None:
                entry["source"] = row.source
                entry["confidence"] = row.confidence
                entry["period"] = row.period
                entry["reported_or_calculated"] = row.reported_or_calculated
            else:
                entry["source"] = "YAHOO_FINANCE"
                entry["confidence"] = "MEDIUM"
        out.append(entry)
    return out


def _business_segments(db: Session, company_id: str) -> list[dict]:
    """Real per-segment revenue history (Deep Research System, Stage R1 —
    TradingView, see tradingview_segments_client.py) — growth % and
    revenue-mix % computed here in Python, not left for the LLM to derive,
    matching this codebase's standing rule that Llama never does numeric
    comparison itself (see e.g. pnl_engine.py's `_direction()`). Fills what
    was, until now, always an explicitly-empty placeholder (see this
    module's docstring)."""
    rows = (
        db.query(BusinessSegment).filter_by(company_id=company_id)
        .order_by(BusinessSegment.segment_name, BusinessSegment.fiscal_year).all()
    )
    by_segment: dict[str, list[BusinessSegment]] = {}
    for r in rows:
        by_segment.setdefault(r.segment_name, []).append(r)

    latest_year = max((r.fiscal_year for r in rows), default=None)
    total_latest_revenue = sum(
        float(r.revenue) for r in rows if r.fiscal_year == latest_year
    ) if latest_year else 0

    out = []
    for name, segment_rows in by_segment.items():
        latest = segment_rows[-1]
        prior = segment_rows[-2] if len(segment_rows) > 1 else None
        yoy_growth_pct = None
        if prior and float(prior.revenue):
            yoy_growth_pct = round((float(latest.revenue) - float(prior.revenue)) / float(prior.revenue) * 100, 2)
        # Only meaningful when this segment's own latest figure IS from the
        # company's latest reporting period — a segment that stopped being
        # separately disclosed (e.g. folded into "Other") has a stale
        # `latest.fiscal_year`, and dividing that old figure by the current
        # period's total would produce a nonsensical, misleadingly small %.
        revenue_mix_pct = (
            round(float(latest.revenue) / total_latest_revenue * 100, 2)
            if total_latest_revenue and latest.fiscal_year == latest_year else None
        )
        out.append({
            "segment_name": name,
            "latest_fiscal_year": latest.fiscal_year,
            "latest_revenue": _num(latest.revenue),
            "prior_fiscal_year": prior.fiscal_year if prior else None,
            "prior_revenue": _num(prior.revenue) if prior else None,
            "yoy_growth_pct": yoy_growth_pct,
            "revenue_mix_pct": revenue_mix_pct,
            "currency": latest.currency,
        })
    return out


def build_master_company_object(db: Session, analysis: FundamentalAnalysis) -> dict:
    """Assemble the Summary.md section-6 shaped object for one completed
    (or in-progress) analysis. Safe to call at any pipeline stage after
    company_info is set — later sections simply come back empty/absent if
    that stage hasn't populated them yet."""
    company_info = analysis.company_info or {}
    company_id = company_info.get("stock_id") or analysis.stock_id
    financial_data = analysis.financial_data or {}
    metrics = analysis.metrics or {}
    sector_analysis = analysis.sector_analysis or {}
    scores = analysis.scores or {}

    summary_row = db.query(CompanySummary).filter_by(company_id=company_id).first()

    shareholding_rows = (db.query(Shareholding).filter_by(company_id=company_id)
                         .order_by(Shareholding.period_end.desc()).limit(8).all())
    shareholding_screener_rows = (db.query(ShareholdingScreener).filter_by(company_id=company_id, frequency="quarterly")
                                  .order_by(ShareholdingScreener.period_end.desc()).limit(8).all())
    governance_events = (db.query(GovernanceEvent).filter_by(company_id=company_id)
                        .order_by(GovernanceEvent.event_date.desc()).limit(10).all())
    analyst_consensus_rows = db.query(AnalystConsensus).filter_by(company_id=company_id).all()
    forward_estimate_rows = db.query(ForwardEstimate).filter_by(company_id=company_id).all()
    earnings_calendar_row = db.query(EarningsCalendar).filter_by(company_id=company_id).first()
    corporate_action_rows = (db.query(CorporateAction).filter_by(company_id=company_id)
                             .order_by(CorporateAction.action_date.desc()).limit(8).all())
    news_rows = (db.query(CompanyNews).filter_by(company_id=company_id)
                .order_by(CompanyNews.published_at.desc()).limit(8).all())
    insider_rows = (db.query(InsiderActivity).filter_by(company_id=company_id)
                    .order_by(InsiderActivity.transaction_date.desc()).limit(10).all())

    from app.calculations.pnl_engine import compute_pnl_analysis
    pnl_analysis = compute_pnl_analysis(db, company_id, sector_name=sector_analysis.get("sector_name"))

    # P&L Analysis Engine ("P&L Intelligence") — a separate, additive
    # module alongside the existing pnl_analysis above (Stage 0 boundary:
    # the older engine is untouched). See app/calculations/pl_intelligence/.
    from app.calculations.pl_intelligence import compute_pl_intelligence
    pl_intelligence = compute_pl_intelligence(db, company_id, sector_name=sector_analysis.get("sector_name"))

    # Stage 21's management-commentary retrieval — reuses the EXISTING
    # concall pgvector embedding search as-is (no new embedding code).
    # Done here, at object-assembly time (db already in scope), rather than
    # in context_builder.py, which is deliberately pure dict-slicing with
    # no DB access of its own — the retrieved excerpts just ride along on
    # the master object like every other field.
    try:
        from app.interpretation.concall_retrieval import search_similar_chunks
        pl_intelligence["management_commentary"] = {
            "margin_headroom": search_similar_chunks(
                db, company_id, "Why did margin decline or expand? Cost pressure or pricing commentary", top_k=3),
            "earnings_quality": search_similar_chunks(
                db, company_id, "Other income, dividend income, investment gains, one-off items", top_k=3),
        }
    except Exception:
        pl_intelligence["management_commentary"] = {"margin_headroom": [], "earnings_quality": []}

    # Balance Sheet Analysis Engine — a separate, additive module (see
    # app/calculations/balance_sheet_intelligence/). Blends Screener.in
    # (net worth/leverage/archetype/common-size) with the existing
    # yfinance-sourced `metrics` (already computed above, same dict the
    # PDF's Working-Capital chart reads) for working-capital ratios
    # Screener's condensed balance sheet can't separate out.
    from app.calculations.balance_sheet_intelligence import compute_balance_sheet_intelligence
    balance_sheet_intelligence = compute_balance_sheet_intelligence(
        db, company_id, sector_name=sector_analysis.get("sector_name"), yfinance_metrics=metrics,
    )

    # Cash Flow Analysis Engine — a separate, additive module (see
    # app/calculations/cash_flow_intelligence/). Primary-sourced from
    # Screener.in's undocumented "schedules" API, cross-checked against
    # yfinance; reuses balance_sheet_intelligence's own working_capital
    # DSO/DIO/DPO series (just computed above) as a receivables/inventory-
    # growth proxy rather than recomputing.
    from app.calculations.cash_flow_intelligence import compute_cash_flow_intelligence
    cash_flow_intelligence = compute_cash_flow_intelligence(
        db, company_id, sector_name=sector_analysis.get("sector_name"), yfinance_metrics=metrics,
        balance_sheet_intelligence_result=balance_sheet_intelligence,
    )

    key_metrics = _sector_metrics_with_provenance(db, company_id, sector_analysis.get("key_metrics") or [])

    sources = {}
    for m in key_metrics:
        if m.get("source"):
            sources.setdefault(m["source"], 0)
            sources[m["source"]] += 1

    obj = {
        "company": {
            "name": company_info.get("company_name"),
            "symbol": company_info.get("symbol"),
            "exchange": company_info.get("exchange"),
            "sector": company_info.get("sector"),
            "industry": company_info.get("industry"),
            "macro_sector": company_info.get("macro_sector"),
            # company_info's own market_cap is frequently null (confirmed on
            # ITC, 2026-09-15) — metrics.market_cap is Yahoo-derived and
            # almost always present; report_service.py's cover page already
            # falls back the same way. Without this, the blueprint LLM (told
            # never to estimate a missing value) correctly but misleadingly
            # writes "market capitalization is not available" right next to
            # a report that shows it on the cover.
            "market_cap": _num(company_info.get("market_cap") or metrics.get("market_cap")),
            "current_price": company_info.get("current_price"),
        },
        "business": {
            "about": summary_row.about if summary_row else None,
            "key_points": summary_row.key_points if summary_row else None,
            "structured": False,  # about/key_points prose only — segments below IS real structured data
            "segments": _business_segments(db, company_id),
            "products": [], "customers": [], "geographies": [], "revenue_mix": [],
        },
        "operations": {
            "production": [], "capacity": [], "utilisation": [], "technology_mix": [],
            "not_available": True,
        },
        "orders": {
            "order_book": {}, "order_pipeline": {},
            "not_available": True,
        },
        "expansion": {
            "items": [],
            "not_available": True,
        },
        "financials": {
            "income": financial_data.get("income"),
            "balance": financial_data.get("balance"),
            "cash_flow": financial_data.get("cash_flow"),
            "market": financial_data.get("market"),
        },
        "ratios": {k: _num(v) for k, v in (metrics or {}).items() if isinstance(v, (int, float))},
        "valuation": {
            "pe_ratio": _num(metrics.get("pe_ratio")),
            "pb_ratio": _num(metrics.get("pb_ratio")),
            "ev_to_ebitda": _num(metrics.get("ev_to_ebitda")),
            "fcf_yield": _num(metrics.get("fcf_yield")),
            "dividend_yield": _num(metrics.get("dividend_yield")),
        },
        "shareholding": {
            "nse": [
                {
                    "period_end": r.period_end,
                    "promoter_pct": _num(r.promoter_pct), "public_pct": _num(r.public_pct),
                    "pledge_pct": _num(r.pledge_pct),
                }
                for r in shareholding_rows
            ],
            "screener_supplementary": [
                {
                    "period_end": r.period_end, "promoter_pct": _num(r.promoter_pct),
                    "fii_pct": _num(r.fii_pct), "dii_pct": _num(r.dii_pct),
                }
                for r in shareholding_screener_rows
            ],
            "events": [
                {
                    "event_type": r.event_type, "severity": r.severity,
                    "event_date": r.event_date, "description": r.description,
                }
                for r in governance_events
            ],
        },
        "management": {
            "insider_activity": [
                {
                    "transaction_date": r.transaction_date, "insider_name": r.insider_name,
                    "position": r.position, "transaction_text": r.transaction_text,
                    "shares": _num(r.shares),
                }
                for r in insider_rows
            ],
            "not_available": ["commentary", "auditor_history", "related_party_transactions"],
        },
        "guidance": {
            "analyst_consensus": [
                {
                    "source": r.source, "num_analysts": r.num_analysts, "sentiment": r.sentiment,
                    "target_price_mean": _num(r.target_price_mean), "target_price_low": _num(r.target_price_low),
                    "target_price_high": _num(r.target_price_high), "implied_upside_pct": _num(r.implied_upside_pct),
                }
                for r in analyst_consensus_rows
            ],
            "forward_estimates": [
                {
                    "metric_type": r.metric_type, "period_label": r.period_label,
                    "avg": _num(r.avg), "low": _num(r.low), "high": _num(r.high),
                    "num_analysts": r.num_analysts,
                }
                for r in forward_estimate_rows
            ],
            "earnings_calendar": {
                "next_earnings_date": earnings_calendar_row.next_earnings_date,
                "ex_dividend_date": earnings_calendar_row.ex_dividend_date,
                "expected_eps_avg": _num(earnings_calendar_row.expected_eps_avg),
            } if earnings_calendar_row else None,
            "management_guidance_documents": "not_available",
        },
        "sector": {
            "name": sector_analysis.get("sector_name"),
            "framework_class": sector_analysis.get("framework_class"),
            "sector_score": sector_analysis.get("sector_score"),
            "key_metrics": key_metrics,
            "red_flags": sector_analysis.get("red_flags") or [],
        },
        "risks": analysis.risks or [],
        "catalysts": analysis.catalysts or [],
        "corporate_actions": [
            {"action_date": r.action_date, "action_type": r.action_type, "value": _num(r.value)}
            for r in corporate_action_rows
        ],
        "news": [
            {
                "headline": r.headline, "provider": r.provider,
                "published_at": r.published_at.isoformat() if r.published_at else None,
            }
            for r in news_rows
        ],
        "scores": {
            "overall_score": _num(analysis.overall_score),
            "confidence_score": _num(analysis.confidence_score),
            "data_quality_score": _num(analysis.data_quality_score),
            "component_scores": scores,
        },
        "sources": [{"source": k, "fact_count": v} for k, v in sorted(sources.items(), key=lambda kv: -kv[1])],
        "pnl_analysis": pnl_analysis,
        "pl_intelligence": pl_intelligence,
        "balance_sheet_intelligence": balance_sheet_intelligence,
        "cash_flow_intelligence": cash_flow_intelligence,
    }
    return obj
