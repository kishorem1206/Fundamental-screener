"""Builds the template context for the banking HTML/PDF report.

The only place in app/reporting/ that touches the database or performs any
aggregation. Per banking_stock_analysis_report.md section 47 (separation of
responsibilities), this module computes nothing that amounts to investment
analysis — it marshals numbers already produced upstream (metrics, scores,
ai_analysis) and does simple deterministic aggregation (grouping already-scored
metrics into report categories, formatting values, building chart series).
Verdict/thesis/narrative text always comes from ai_analysis, never invented here.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import FundamentalAnalysis
from app.infrastructure.database import metric_store
from app.sectors.registry import get_framework
from app.sectors import banking_data_bridge
from app.reporting import charts

# ── Report category -> metric key groupings ────────────────────────────────
# Mirrors the report spec's own section structure (12-20), not a new taxonomy.
_CATEGORY_METRICS = {
    "growth": ["revenue_cagr_3y", "pat_cagr_3y"],
    "funding": ["casa_ratio"],
    "profitability": ["roe", "roa", "pat_margin", "nim"],
    "asset_quality": ["gross_npa", "net_npa", "provision_coverage_ratio", "credit_cost", "slippage_ratio"],
    "capital": ["capital_adequacy_ratio"],
    "efficiency": ["cost_to_income_ratio"],
    "valuation": ["pb_ratio", "pe_ratio"],
}
_CATEGORY_LABELS = {
    "growth": "Growth", "funding": "Funding", "profitability": "Profitability",
    "asset_quality": "Asset Quality", "capital": "Capital Strength",
    "efficiency": "Efficiency", "valuation": "Valuation",
}

_TREND_METRICS = [
    "nim", "casa_ratio", "gross_npa", "net_npa", "provision_coverage_ratio",
    "credit_cost", "roa", "roe", "capital_adequacy_ratio", "pat_cagr_3y",
]

_RATING_TO_VERDICT = {
    "STRONG": "Strong", "GOOD": "Attractive", "FAIR": "Watch",
    "WEAK": "Caution", "POOR": "High Risk",
}

_SEVERITY_PENALTY = {"HIGH": 25, "MEDIUM": 10, "LOW": 5}

# ai_analysis list fields occasionally come back from the LLM with malformed
# nested content (e.g. a stray "bear_case", ":", or a stringified Python list
# literal leaking in as its own list item) rather than clean prose bullets.
# The renderer must not silently invent replacement content, but it also
# shouldn't reproduce obvious parsing artifacts — this is a narrow filter for
# the artifact shapes actually observed, not content editing.
_KNOWN_ARTIFACT_TOKENS = {
    "bull_case", "bear_case", "key_risks", "key_catalysts", "monitoring_points",
    "investment_thesis", ":", "",
}


def _clean_points(items: list) -> list[str]:
    cleaned = []
    for item in items or []:
        text = str(item).strip()
        if not text or text in _KNOWN_ARTIFACT_TOKENS:
            continue
        if text.startswith("[") and text.endswith("]"):
            continue
        cleaned.append(text)
    return cleaned


def fmt(value, unit: str = "", decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):,.{decimals}f}{unit}"
    except (TypeError, ValueError):
        return "N/A"


_fmt = fmt  # internal alias used throughout this module


def _short_period(period: str) -> str:
    """"2026-06-30" -> "Jun'26" for compact chart x-axis labels."""
    try:
        d = datetime.fromisoformat(period)
        return d.strftime("%b'%y")
    except ValueError:
        return period


def _metric_label_map(framework) -> dict[str, dict]:
    return {m.name: {"label": m.label, "unit": m.unit, "direction": m.direction} for m in framework.key_metrics()}


def _trend_series(db: Session, company_id: str, metric_key: str) -> list[tuple[str, float | None]]:
    """Chronological (period_label, value) pairs — one authoritative value per
    distinct period, resolved the same way live scoring is (lowest source_tier,
    latest retrieval wins on ties, CONSOLIDATED preferred per period since
    2026-09-23 — see get_authoritative_value()'s own docstring). Empty/short
    history renders as an explicit "insufficient historical data" chart
    state, never fabricated.

    `statement_type=None` here (get_metric_history's own "show both types"
    contract) so the period LIST is the union of whatever either statement
    type covers — real gap found alongside the main 2026-09-23 fix: pulling
    the period list from STANDALONE rows only, then resolving each period's
    VALUE with a CONSOLIDATED-preferring lookup, would silently miss any
    period that only exists on the CONSOLIDATED side (common — a company's
    consolidated history often starts years after its standalone one)."""
    history = metric_store.get_metric_history(db, company_id, metric_key, statement_type=None)
    periods = sorted({row.period for row in history})
    points = []
    for period in periods:
        winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period)
        points.append((_short_period(period), float(winner.value) if winner else None))
    return points


def _category_score(framework, values: dict, keys: list[str]) -> float | None:
    scores = [framework.score_key_metric(k, values.get(k)) for k in keys]
    scores = [s for s in scores if s is not None]
    return round(sum(scores) / len(scores), 1) if scores else None


def _verdict_label(ai_rating: str | None) -> str:
    return _RATING_TO_VERDICT.get((ai_rating or "").upper(), "Neutral")


def _risk_quality_score(risks: list[dict]) -> float | None:
    """Deterministic transform, not new analysis: 100 minus a severity-weighted
    penalty per triggered risk, floored at 0."""
    if not risks:
        return 100.0
    penalty = sum(_SEVERITY_PENALTY.get(r.get("severity"), 5) for r in risks)
    return max(0.0, 100.0 - penalty)


def build_report_context(analysis_id: str, db: Session) -> dict:
    analysis: FundamentalAnalysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
    if analysis is None:
        raise ValueError(f"Analysis {analysis_id} not found")

    company = analysis.company_info or {}
    metrics = analysis.metrics or {}
    market = (analysis.financial_data or {}).get("market") or {}
    scores = analysis.scores or {}
    ai = analysis.ai_analysis or {}
    risks = analysis.risks or []
    catalysts = analysis.catalysts or []
    sector_analysis = analysis.sector_analysis or {}
    peers_data = analysis.peers or {}

    company_id = company.get("stock_id") or analysis.stock_id
    sector = company.get("sector") or ""
    industry = company.get("industry") or ""
    framework = get_framework(sector, industry=industry)
    metric_meta = _metric_label_map(framework)

    # Screener.in's about/key_points (2026-09-12) — sector-agnostic, not
    # banking-specific despite living in this banking-report data builder;
    # every Screener.in company page has this.
    from app.infrastructure.database.models import CompanySummary
    summary_row = db.query(CompanySummary).filter_by(company_id=company_id).first()

    # Fetched fresh at render time, not reused from the analysis run's
    # (potentially hours-old) financial_data snapshot — see
    # app/ingestion/live_price.py's module docstring.
    from app.ingestion.live_price import fetch_live_price
    live_price = fetch_live_price(company.get("symbol") or "", company.get("exchange") or "NSE")
    if live_price is None and market.get("current_price") is not None:
        live_price = {"price": market.get("current_price"), "change_pct": None,
                       "previous_close": None, "day_high": None, "day_low": None, "as_of": None}

    # Governance/ownership (Architecture v2 Stage 3, wired into the pipeline
    # 2026-09-13) + Yahoo Finance market intelligence (2026-09-13) — see
    # ARCHITECTURE.md's matching dated entries for full rationale.
    from app.infrastructure.database.models import (
        Shareholding, ShareholdingScreener, GovernanceEvent, AnalystConsensus,
        ForwardEstimate, CorporateAction, CompanyNews, EarningsCalendar,
    )
    shareholding_rows = (db.query(Shareholding).filter_by(company_id=company_id)
                         .order_by(Shareholding.period_end.desc()).limit(8).all())
    shareholding_screener_rows = (db.query(ShareholdingScreener).filter_by(company_id=company_id, frequency="quarterly")
                                  .order_by(ShareholdingScreener.period_end.desc()).limit(8).all())
    governance_events_rows = (db.query(GovernanceEvent).filter_by(company_id=company_id)
                              .order_by(GovernanceEvent.event_date.desc()).limit(10).all())
    analyst_consensus_rows = db.query(AnalystConsensus).filter_by(company_id=company_id).all()
    forward_estimate_rows = db.query(ForwardEstimate).filter_by(company_id=company_id).all()
    earnings_calendar_row = db.query(EarningsCalendar).filter_by(company_id=company_id).first()
    corporate_action_rows = (db.query(CorporateAction).filter_by(company_id=company_id)
                             .order_by(CorporateAction.action_date.desc()).limit(8).all())
    company_news_rows = (db.query(CompanyNews).filter_by(company_id=company_id)
                         .order_by(CompanyNews.published_at.desc()).limit(8).all())

    banking_values = banking_data_bridge.build_banking_bridge(db, company_id)
    # key_metrics from sector_analysis already resolves bridge-vs-yfinance
    # priority (see banking.py._compute_special_metric) — reuse those values
    # rather than re-deriving priority logic here.
    key_metrics_by_name = {m["name"]: m for m in (sector_analysis.get("key_metrics") or [])}
    all_values = {name: entry.get("value") for name, entry in key_metrics_by_name.items()}

    category_scores = {
        cat: _category_score(framework, all_values, keys)
        for cat, keys in _CATEGORY_METRICS.items()
    }

    def metric_card(name: str) -> dict:
        entry = key_metrics_by_name.get(name, {})
        meta = metric_meta.get(name, {})
        return {
            "key": name,
            "label": meta.get("label", name),
            "value": entry.get("value"),
            "display": _fmt(entry.get("value"), meta.get("unit", "")),
            "unit": meta.get("unit", ""),
            "available": entry.get("available", False),
            "na_message": entry.get("na_message"),
            "status": entry.get("status"),
            "score": entry.get("score"),
        }

    trend_charts = {}
    for key in _TREND_METRICS:
        points = _trend_series(db, company_id, key)
        meta = metric_meta.get(key, {})
        has_history = len([v for _, v in points] if points else []) >= 2 and any(v is not None for _, v in points)
        trend_charts[key] = {
            "label": meta.get("label", key),
            "svg": charts.line_chart([{"label": meta.get("label", key), "points": points}],
                                      unit=meta.get("unit", "%")) if has_history else None,
            "has_history": has_history,
        }

    # ── Peer comparison ──────────────────────────────────────────────────────
    peer_rows = []
    subject_row = {
        "company_name": company.get("company_name"), "is_subject": True,
        "roe": all_values.get("roe"), "roa": all_values.get("roa"),
        "pb_ratio": all_values.get("pb_ratio"), "pe_ratio": all_values.get("pe_ratio"),
        "nim": all_values.get("nim"), "casa_ratio": all_values.get("casa_ratio"),
        "gross_npa": all_values.get("gross_npa"), "net_npa": all_values.get("net_npa"),
        "capital_adequacy_ratio": all_values.get("capital_adequacy_ratio"),
    }
    peer_rows.append(subject_row)
    for p in (peers_data.get("peers") or []):
        peer_rows.append({
            "company_name": p.get("company_name"), "is_subject": False,
            "roe": p.get("roe"), "roa": p.get("roa"),
            "pb_ratio": p.get("pb_ratio"), "pe_ratio": p.get("pe_ratio"),
            # Banking-specific fields are only ingested for the analyzed company,
            # not (yet) for peers — honest N/A rather than a fabricated figure.
            "nim": None, "casa_ratio": None, "gross_npa": None, "net_npa": None,
            "capital_adequacy_ratio": None,
        })

    scatter_points = [
        {"label": r["company_name"], "x": r.get("pb_ratio"), "y": r.get("roe"), "highlight": r["is_subject"]}
        for r in peer_rows
    ]

    # ── Red flags / positive signals ────────────────────────────────────────
    red_flags = [
        {"severity": r.get("severity"), "title": r.get("title"), "description": r.get("description")}
        for r in risks
    ]
    positive_signals = [
        {"title": c.get("title"), "description": c.get("description")}
        for c in catalysts
    ]

    # ── Data quality / provenance ───────────────────────────────────────────
    available_names = sector_analysis.get("available_metric_names") or []
    unavailable_names = sector_analysis.get("unavailable_metric_names") or []
    total_metrics = len(available_names) + len(unavailable_names)
    provenance_rows = []
    for name in available_names:
        row = metric_store.get_latest_period_value(db, company_id, name)
        if row is not None:
            provenance_rows.append({
                "metric": metric_meta.get(name, {}).get("label", name),
                "source": row.source, "confidence": row.confidence,
                "reported_or_calculated": row.reported_or_calculated,
                "period": row.period, "source_document": row.source_document,
                "source_url": row.source_url,
            })

    # P&L Analysis System, Stage P3 — computed fresh here (not persisted
    # separately), same "fetch fresh at render time" pattern as live_price.
    # The blueprint's 6 pnl_-prefixed narrative sections are split out from
    # the general "Business & Interpretation" list so they render in their
    # own dedicated P&L section instead — see banking_report.html.jinja.
    from app.calculations.pnl_engine import compute_pnl_analysis
    # Real bug found 2026-09-13: `sector` here is company_info's macro
    # sector ("Financial Services"), not the framework's actual sector name
    # ("Banks") that pnl_engine's _FINANCIAL_SECTORS gate checks against —
    # using it silently disabled the bank-specific interest/other-income
    # flag gating for every bank in this report path (not report_service.py,
    # which was already correct). Use sector_analysis["sector_name"] instead,
    # matching master_object.py's own call.
    pnl_analysis = compute_pnl_analysis(
        db, company_id, sector_name=sector_analysis.get("sector_name")
    ) if company_id else {}
    all_blueprint_sections = (analysis.report_blueprint or {}).get("sections") or []
    narrative_sections = [s for s in all_blueprint_sections if not s.get("id", "").startswith("pnl_")]
    pnl_narrative_sections = [s for s in all_blueprint_sections if s.get("id", "").startswith("pnl_")]

    # Concall Intelligence System, Stage C5 — deterministic extraction/
    # tracking data from Stages C0-C4, computed fresh at render time (same
    # pattern as pnl_analysis above). No narrative LLM stage exists for
    # this yet, so this renders the real data as-is.
    from app.interpretation.concall_report_data import build_concall_report_data
    concall_data = build_concall_report_data(db, company_id) if company_id else {"latest_transcript": None}

    # Premium PDF System, Stages B1/B4/B6/B7 — same shared builder
    # report_service.py's ReportLab path uses, so both PDF paths render the
    # same underlying data. B2/B3/B5 come from concall_data above instead.
    from app.reporting.premium_report_data import build_premium_extras
    premium_extras = build_premium_extras(db, company_id, analysis) if company_id else {}

    peer_perf_series = (premium_extras.get("peer_performance") or {}).get("series") or []
    peer_perf_svg = None
    if len(peer_perf_series) >= 2:
        peer_perf_svg = charts.line_chart(
            [
                {"label": s["name"], "points": [(p["date"][5:], p["value"]) for p in s["points"]],
                 "color": "var(--gold)" if s.get("is_subject") else None}
                for s in peer_perf_series
            ],
            unit="", width=680, height=280,
        )

    def _downsample_pts(pts: list[dict], n: int = 24) -> list[dict]:
        if len(pts) <= n:
            return pts
        step = len(pts) / n
        return [pts[int(i * step)] for i in range(n)]

    price_chart_raw = premium_extras.get("price_chart") or {"1y": [], "5y": []}
    price_charts = {}
    for window in ("1y", "5y"):
        pts = _downsample_pts(price_chart_raw.get(window) or [])
        price_charts[window] = charts.line_chart(
            [{"label": window.upper(), "points": [(p["date"][5:], p["close"]) for p in pts]}],
            unit="", width=390, height=220,
        ) if len(pts) >= 2 else None

    now = datetime.now(timezone.utc)
    return {
        "generated_at": now.strftime("%B %d, %Y"),
        "analysis_id": analysis_id,
        "blueprint": {"sections": narrative_sections},
        "pnl_analysis": pnl_analysis,
        "pnl_narrative_sections": pnl_narrative_sections,
        "concall": concall_data,
        "company": {
            "name": company.get("company_name") or "Unknown Company",
            "ticker": company.get("symbol") or "",
            "exchange": company.get("exchange") or "",
            "sector": sector,
            "sub_sector": industry,
            "market_cap": _fmt((company.get("market_cap") or market.get("market_cap") or 0) / 1e7 or None, "", 0),
            "price": _fmt(live_price.get("price")) if live_price else _fmt(market.get("current_price")),
            "price_change_pct": live_price.get("change_pct") if live_price else None,
            "price_as_of": (live_price.get("as_of") or "")[:16].replace("T", " ") if live_price else None,
            # yfinance_client.py's market.week52_high/low (2026-09-14) — real
            # data, fetched for every analysis already, never actually
            # rendered anywhere until now (same gap pattern as About/Key
            # Points/News/Calendar found earlier this session).
            "week52_high": _fmt(market.get("week52_high")) if market.get("week52_high") is not None else None,
            "week52_low": _fmt(market.get("week52_low")) if market.get("week52_low") is not None else None,
            "pe_ratio": _fmt(all_values.get("pe_ratio"), "x") if all_values.get("pe_ratio") is not None else None,
            "about": summary_row.about if summary_row else None,
            "key_points": summary_row.key_points if summary_row else None,
        },
        "governance": {
            "shareholding": [
                {
                    "period_end": r.period_end,
                    "promoter_pct": r.promoter_pct, "public_pct": r.public_pct, "pledge_pct": r.pledge_pct,
                }
                for r in shareholding_rows
            ],
            "shareholding_screener": [
                {
                    "period_end": r.period_end, "promoter_pct": r.promoter_pct,
                    "fii_pct": r.fii_pct, "dii_pct": r.dii_pct,
                }
                for r in shareholding_screener_rows
            ],
            "events": [
                {
                    "event_type": r.event_type, "severity": r.severity,
                    "event_date": r.event_date, "description": r.description,
                }
                for r in governance_events_rows
            ],
        },
        "market_intel": {
            "analyst_consensus": [
                {
                    "source": r.source, "num_analysts": r.num_analysts, "sentiment": r.sentiment,
                    "target_price_mean": r.target_price_mean, "target_price_low": r.target_price_low,
                    "target_price_high": r.target_price_high, "implied_upside_pct": r.implied_upside_pct,
                }
                for r in analyst_consensus_rows
            ],
            "forward_estimates": [
                {
                    "metric_type": r.metric_type, "period_label": r.period_label,
                    "avg": r.avg, "low": r.low, "high": r.high, "num_analysts": r.num_analysts,
                }
                for r in forward_estimate_rows
            ],
            "earnings_calendar": {
                "next_earnings_date": earnings_calendar_row.next_earnings_date,
                "ex_dividend_date": earnings_calendar_row.ex_dividend_date,
                "expected_eps_avg": earnings_calendar_row.expected_eps_avg,
                "expected_eps_low": earnings_calendar_row.expected_eps_low,
                "expected_eps_high": earnings_calendar_row.expected_eps_high,
            } if earnings_calendar_row else None,
            "corporate_actions": [
                {"action_date": r.action_date, "action_type": r.action_type, "value": r.value}
                for r in corporate_action_rows
            ],
            "news": [
                {
                    "headline": r.headline, "provider": r.provider, "url": r.url,
                    "published_at": r.published_at.strftime("%Y-%m-%d") if r.published_at else None,
                }
                for r in company_news_rows
            ],
        },
        "verdict": {
            "label": _verdict_label(ai.get("rating")),
            "headline": ai.get("executive_summary"),
            "score": float(analysis.overall_score) if analysis.overall_score is not None else None,
            "conviction": ai.get("conviction"),
        },
        "snapshot_cards": [
            {"label": "Overall Score", "value": analysis.overall_score, "display": _fmt(analysis.overall_score, "/100", 0)},
            {"label": "Business Quality", "value": ai.get("business_quality"), "display": _fmt(ai.get("business_quality"), "/100", 0)},
            {"label": "Risk Quality", "value": _risk_quality_score(risks), "display": _fmt(_risk_quality_score(risks), "/100", 0)},
            {"label": "Valuation", "value": None, "display": ai.get("valuation_view") or "N/A"},
            {"label": "Growth", "value": category_scores.get("growth"), "display": _fmt(category_scores.get("growth"), "/100", 0)},
        ],
        "scorecard": [
            {"category": _CATEGORY_LABELS[cat], "score": category_scores.get(cat),
             "score_bar_svg": charts.score_bar(category_scores.get(cat))}
            for cat in _CATEGORY_METRICS
        ],
        "growth": {
            "metrics": [metric_card(k) for k in ["revenue_cagr_3y", "pat_cagr_3y"]],
            "narrative": ai.get("growth_outlook"),
        },
        "funding": {
            "metrics": [metric_card(k) for k in ["casa_ratio"]],
            "casa_trend": trend_charts.get("casa_ratio"),
        },
        "profitability": {
            "metrics": [metric_card(k) for k in ["nim", "roa", "roe", "pat_margin"]],
            "nim_trend": trend_charts.get("nim"),
            "roa_roe_trend": {
                "svg": charts.line_chart([
                    {"label": "ROA", "points": _trend_series(db, company_id, "roa")},
                    {"label": "ROE", "points": _trend_series(db, company_id, "roe")},
                ], unit="%"),
            },
            "narrative": ai.get("financial_health_summary"),
        },
        "asset_quality": {
            "metrics": [metric_card(k) for k in ["gross_npa", "net_npa", "provision_coverage_ratio", "credit_cost", "slippage_ratio"]],
            "gnpa_nnpa_trend": {
                "svg": charts.line_chart([
                    {"label": "GNPA", "points": _trend_series(db, company_id, "gross_npa")},
                    {"label": "NNPA", "points": _trend_series(db, company_id, "net_npa")},
                ], unit="%"),
            },
            "credit_cost_trend": trend_charts.get("credit_cost"),
        },
        "capital": {
            "metrics": [metric_card(k) for k in ["capital_adequacy_ratio"]],
            "car_trend": trend_charts.get("capital_adequacy_ratio"),
            "narrative": None,
        },
        "efficiency": {
            "metrics": [metric_card(k) for k in ["cost_to_income_ratio"]],
        },
        "historical_trend": {k: trend_charts[k] for k in _TREND_METRICS},
        "peers": {
            "rows": peer_rows,
            "scatter_svg": charts.scatter_chart(scatter_points, x_label="P/B", y_label="ROE (%)"),
        },
        "valuation": {
            "metrics": [metric_card(k) for k in ["pb_ratio", "pe_ratio"]],
            "narrative": ai.get("valuation_commentary"),
        },
        "red_flags": red_flags,
        "positive_signals": positive_signals,
        "thesis": {
            "points": _clean_points(ai.get("investment_thesis")),
            "bull_case": _clean_points(ai.get("bull_case")),
            "bear_case": _clean_points(ai.get("bear_case")),
        },
        "what_could_change": {
            "more_bullish": _clean_points(ai.get("bull_case")),
            "more_cautious": _clean_points((ai.get("bear_case") or []) + (ai.get("key_risks") or [])),
        },
        "what_to_track": _clean_points(ai.get("monitoring_points")),
        "data_quality": {
            "metrics_analysed": total_metrics,
            "metrics_available": len(available_names),
            "metrics_unavailable": len(unavailable_names),
            "confidence_score": float(analysis.confidence_score) if analysis.confidence_score is not None else None,
            "data_quality_score": float(analysis.data_quality_score) if analysis.data_quality_score is not None else None,
            "provenance": provenance_rows,
        },
        "framework_version": "banking.md v1.0",
        "renderer_version": "1.0",
        "brands": premium_extras.get("brands") or [],
        "concall_highlights": premium_extras.get("concall_highlights"),
        "peer_performance": {"svg": peer_perf_svg, "series": peer_perf_series},
        "source_ledger": premium_extras.get("source_ledger") or [],
        "change_log": premium_extras.get("change_log"),
        "price_charts": price_charts,
    }
