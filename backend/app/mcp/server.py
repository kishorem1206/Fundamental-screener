"""MCP server layer — Architecture v2 Stage 1.

Exposes read-only tools over the existing platform (Stage 0's metric
registry, the provenance ledger, the analysis pipeline) via the Model
Context Protocol. Every tool here wraps existing code — no new business
logic, no data-layer changes; this stage is purely "give the platform an
MCP interface," per Architecture v2 chatgpt.md's core thesis that MCP
should sit above the source of truth, not be it.

Mounted into the FastAPI app at /mcp (see app/main.py's `app.mount(...)`)
rather than run as a separate stdio process — this deployment already runs
as one long-lived HTTP service, so an HTTP-transport MCP endpoint reachable
by any MCP-over-HTTP client fits it better than a second process to manage.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from mcp.server.mcpserver import MCPServer

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import AnalysisStage, FundamentalAnalysis, Stock
from app.infrastructure.database import metric_store
from app.logger import logger
from app.metrics.registry import metrics_for_sector
from app.pipeline.orchestrator import STAGES, run_analysis_pipeline
from app.services.full_analysis_service import analysis_to_dict as _analysis_to_dict

mcp_server = MCPServer(
    name="fundamental-screener",
    version="0.1.0",
    instructions=(
        "Read-only tools over an Indian-equities (NSE/BSE) fundamental-analysis "
        "platform. Every returned value carries its own source, period, and "
        "confidence — never treat two values for the same metric as directly "
        "comparable unless their periods and statement_type match."
    ),
)


def _lookup_stock(db, symbol: str) -> Stock | None:
    """Resolve a bare symbol ("HDFCBANK") or a full stock_id ("NSE:HDFCBANK")."""
    if ":" in symbol:
        return db.query(Stock).filter_by(id=symbol).first()
    return db.query(Stock).filter_by(symbol=symbol.upper(), is_active=True).first()


def _latest_completed(db, stock_id: str) -> FundamentalAnalysis | None:
    return (
        db.query(FundamentalAnalysis)
        .filter_by(stock_id=stock_id, status="COMPLETED")
        .order_by(FundamentalAnalysis.created_at.desc())
        .first()
    )


def _bank_category_metrics(db, stock_id: str, category: str) -> dict:
    """Every Banks-sector metric in `category` (per Stage 0's registry),
    read straight from the provenance ledger's authoritative value — works
    even if analyze_stock has never been called for this stock."""
    ids = [m.id for m in metrics_for_sector("Banks") if m.category == category]
    out = {}
    for metric_id in ids:
        row = metric_store.get_latest_period_value(db, stock_id, metric_id)
        if row is None:
            continue
        out[metric_id] = {
            "value": float(row.value),
            "unit": row.unit,
            "period": row.period,
            "statement_type": row.statement_type,
            "source": row.source,
            "confidence": row.confidence,
            "numeric_confidence": metric_store.numeric_confidence(row),
            "source_document": row.source_document,
            "retrieved_at": row.retrieved_at.isoformat(),
        }
    return out


@mcp_server.tool()
def get_company_profile(symbol: str) -> dict:
    """Identity and classification for one NSE-listed stock — accepts a bare
    symbol ("HDFCBANK") or a full stock_id ("NSE:HDFCBANK")."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        return {
            "stock_id": stock.id,
            "symbol": stock.symbol,
            "exchange": stock.exchange,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "industry": stock.industry,
            "basic_industry": stock.basic_industry,
            "macro_sector": stock.macro_sector,
            "market_cap_cr": float(stock.market_cap) if stock.market_cap is not None else None,
            "market_cap_category": stock.market_cap_category,
            "isin": stock.isin,
        }
    finally:
        db.close()


@mcp_server.tool()
def get_financials(symbol: str) -> dict:
    """Raw yfinance-sourced financial statements from the most recent
    completed analysis for this stock. Returns an error asking to call
    analyze_stock first if none exists yet."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        analysis = _latest_completed(db, stock.id)
        if analysis is None:
            return {"error": f"No completed analysis for {stock.symbol} yet — call analyze_stock first"}
        return {
            "stock_id": stock.id,
            "analysis_id": analysis.id,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "financial_data": analysis.financial_data,
        }
    finally:
        db.close()


@mcp_server.tool()
def get_ratios(symbol: str) -> dict:
    """All 135+ deterministically-computed metric fields (growth, margins,
    returns, leverage, valuation, cyclicality) from the most recent completed
    analysis for this stock."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        analysis = _latest_completed(db, stock.id)
        if analysis is None:
            return {"error": f"No completed analysis for {stock.symbol} yet — call analyze_stock first"}
        return {
            "stock_id": stock.id,
            "analysis_id": analysis.id,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "metrics": analysis.metrics,
        }
    finally:
        db.close()


@mcp_server.tool()
def get_valuation(symbol: str) -> dict:
    """Valuation-category metrics only (P/E, P/B, EV/EBITDA, PEG, dividend
    yield, etc. — per Stage 0's metric registry), from the most recent
    completed analysis for this stock."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        analysis = _latest_completed(db, stock.id)
        if analysis is None:
            return {"error": f"No completed analysis for {stock.symbol} yet — call analyze_stock first"}
        sector_name = (analysis.company_info or {}).get("sector") or "Generic"
        valuation_ids = {m.id for m in metrics_for_sector(sector_name) if m.category == "valuation"}
        metrics = analysis.metrics or {}
        return {
            "stock_id": stock.id,
            "analysis_id": analysis.id,
            "valuation": {k: v for k, v in metrics.items() if k in valuation_ids} or {
                k: metrics.get(k) for k in
                ("pe_ratio", "forward_pe", "pb_ratio", "ev_to_ebitda", "ev_to_sales",
                 "peg_ratio", "dividend_yield", "earnings_yield")
                if k in metrics
            },
        }
    finally:
        db.close()


@mcp_server.tool()
def get_bank_asset_quality(symbol: str) -> dict:
    """Gross/Net NPA, Provision Coverage Ratio, slippage ratio, credit cost
    for a bank — read directly from the provenance ledger (no analysis run
    required), each value carrying its own source/period/confidence."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "metrics": _bank_category_metrics(db, stock.id, "asset_quality"),
        }
    finally:
        db.close()


@mcp_server.tool()
def get_bank_capital(symbol: str) -> dict:
    """Capital Adequacy Ratio (CRAR), CET1, Tier 1 for a bank — read directly
    from the provenance ledger, each value carrying its own source/period/
    confidence."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "metrics": _bank_category_metrics(db, stock.id, "capital"),
        }
    finally:
        db.close()


@mcp_server.tool()
def get_bank_funding(symbol: str) -> dict:
    """CASA ratio for a bank — read directly from the provenance ledger.
    Only one metric today (deposit-mix components like current/savings split
    aren't disclosed by any ingested source yet), kept as its own tool since
    banking.md treats funding quality as a distinct disclosure area."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "metrics": _bank_category_metrics(db, stock.id, "funding"),
        }
    finally:
        db.close()


@mcp_server.tool()
def get_shareholding(symbol: str) -> dict:
    """Promoter/public/pledge % history for one stock (Architecture v2
    Stage 3, NSE shareholding-pattern filings) — sector-agnostic, works for
    any listed company, not just banks. Newest period first."""
    from app.infrastructure.database.models import Shareholding
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = (
            db.query(Shareholding).filter_by(company_id=stock.id)
            .order_by(Shareholding.period_end.desc()).all()
        )
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "shareholding": [
                {
                    "period_end": r.period_end,
                    "promoter_pct": float(r.promoter_pct) if r.promoter_pct is not None else None,
                    "public_pct": float(r.public_pct) if r.public_pct is not None else None,
                    "pledge_pct": float(r.pledge_pct) if r.pledge_pct is not None else None,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@mcp_server.tool()
def get_shareholding_trend_screener(symbol: str) -> dict:
    """Supplementary promoter/FII/DII/public holding history from
    Screener.in — kept separate from get_shareholding's NSE data, never
    blended. Materially deeper history than NSE (years back to 2017 on
    Screener vs NSE's 2022-on window) plus an FII/DII split NSE doesn't
    provide, but Screener's shareholding section has NO pledge % field at
    all — for pledge tracking use get_shareholding (NSE), never this tool.
    Returns both quarterly and yearly series, newest period first."""
    from app.infrastructure.database.models import ShareholdingScreener
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = (
            db.query(ShareholdingScreener).filter_by(company_id=stock.id)
            .order_by(ShareholdingScreener.period_end.desc()).all()
        )
        out = {"quarterly": [], "yearly": []}
        for r in rows:
            entry = {
                "period_end": r.period_end,
                "promoter_pct": float(r.promoter_pct) if r.promoter_pct is not None else None,
                "fii_pct": float(r.fii_pct) if r.fii_pct is not None else None,
                "dii_pct": float(r.dii_pct) if r.dii_pct is not None else None,
                "public_pct": float(r.public_pct) if r.public_pct is not None else None,
                "shareholder_count": r.shareholder_count,
            }
            out.setdefault(r.frequency, []).append(entry)
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "disclaimer": "Source: Screener.in — supplementary trend data only, no pledge % field.",
            **out,
        }
    finally:
        db.close()


@mcp_server.tool()
def get_governance_events(symbol: str) -> dict:
    """Deterministic, evidence-backed governance flags for one stock
    (promoter holding decline, pledge present/increase) — every event
    carries the exact prior/current values that triggered it, never an
    inferred conclusion. Newest first."""
    from app.infrastructure.database.models import GovernanceEvent
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = (
            db.query(GovernanceEvent).filter_by(company_id=stock.id)
            .order_by(GovernanceEvent.event_date.desc()).all()
        )
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "events": [
                {
                    "event_type": r.event_type, "severity": r.severity, "event_date": r.event_date,
                    "description": r.description, "evidence": r.evidence,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@mcp_server.tool()
def get_historical_valuation(symbol: str) -> dict:
    """Current P/E (and P/B, if available) versus this specific company's
    own historical median/percentile — not an absolute cutoff. `years_of_data`
    in the response states exactly how much history this is based on, since
    it's rarely a true 10 years for Indian stocks (see
    app/ingestion/valuation_history_client.py's module docstring)."""
    from app.calculations.engine import compute_metrics
    from app.calculations.historical_valuation import compute_valuation_position
    from app.data.yfinance_client import fetch_financial_data
    from app.infrastructure.database.models import BulkMetrics

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}

        bulk = db.query(BulkMetrics).filter_by(stock_id=stock.id).first()
        current_pe = (bulk.metrics or {}).get("pe_ratio") if bulk else None
        current_pb = (bulk.metrics or {}).get("pb_ratio") if bulk else None
        if current_pe is None:
            try:
                metrics = compute_metrics(fetch_financial_data(stock.exchange, stock.symbol))
                current_pe, current_pb = metrics.get("pe_ratio"), metrics.get("pb_ratio")
            except Exception as e:
                logger.warning("mcp: get_historical_valuation live pe fetch failed", symbol=symbol, error=str(e))

        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            **compute_valuation_position(db, stock.id, current_pe, current_pb),
        }
    finally:
        db.close()


@mcp_server.tool()
def get_sector_requirements(sector_name: str) -> dict:
    """Required metrics for one sector (e.g. "Banks", "NBFCs", "IT Services"),
    grouped by category — Architecture v2 Stage 5. Derived live from that
    sector's real scoring code, not a separate config file that could drift
    out of sync with it."""
    from app.sectors.registry import get_framework

    framework = get_framework(sector_name)
    if framework.sector_name == "Generic" and sector_name.lower() != "generic":
        return {"error": f"Unknown sector '{sector_name}'"}
    return {
        "sector_name": framework.sector_name,
        "required_metrics": framework.required_metric_ids(),
    }


@mcp_server.tool()
def list_data_sources() -> dict:
    """Every data source this platform knows about, with its type, trust
    tier, and current reachability status (ACTIVE/PARTIAL/BLOCKED/
    RESTRICTED) — including RBI, SEBI, and MCA, which are currently blocked
    (see each entry's `notes` for exactly why, and `verified_at` for when
    that was last checked). A blocked source is reported honestly here
    rather than silently returning nothing with no explanation."""
    from app.sources.registry import list_sources
    return {"sources": list_sources()}


@mcp_server.tool()
def get_analyst_consensus(symbol: str) -> dict:
    """Third-party analyst sentiment/target-price snapshots for this stock,
    keyed by source (e.g. "INDMONEY", "YAHOO_FINANCE") — a stock can have
    more than one; they are never merged into a single number, each stays
    attributed to its own provider. Context only — NEVER part of this
    platform's own score, sector analysis, or AI rating; this platform
    derives its own conclusions independently from primary financial data.
    IndMoney's row only updates via an agent session (POST
    /api/analyst-consensus/{id}); Yahoo Finance's row is fully autonomous,
    refreshed by every analysis run."""
    from app.infrastructure.database.models import AnalystConsensus

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = db.query(AnalystConsensus).filter_by(company_id=stock.id).all()
        by_source = {}
        for row in rows:
            by_source[row.source] = {
                "num_analysts": row.num_analysts, "sentiment": row.sentiment,
                "buy_pct": float(row.buy_pct) if row.buy_pct is not None else None,
                "hold_pct": float(row.hold_pct) if row.hold_pct is not None else None,
                "sell_pct": float(row.sell_pct) if row.sell_pct is not None else None,
                "target_price_mean": float(row.target_price_mean) if row.target_price_mean is not None else None,
                "target_price_low": float(row.target_price_low) if row.target_price_low is not None else None,
                "target_price_high": float(row.target_price_high) if row.target_price_high is not None else None,
                "implied_upside_pct": float(row.implied_upside_pct) if row.implied_upside_pct is not None else None,
                "retrieved_at": row.retrieved_at.isoformat(),
                "disclaimer": (
                    f"Third-party opinion from {row.source}, for context only — "
                    "not part of this platform's own analysis or score."
                ),
            }
        return {"stock_id": stock.id, "symbol": stock.symbol, "by_source": by_source}
    finally:
        db.close()


@mcp_server.tool()
def get_forward_estimates(symbol: str) -> dict:
    """Consensus EPS/revenue estimates and growth estimates, by period
    (0q/+1q/0y/+1y/LTG) — Yahoo Finance analysts."""
    from app.infrastructure.database.models import ForwardEstimate

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = db.query(ForwardEstimate).filter_by(company_id=stock.id).all()
        by_metric: dict[str, list[dict]] = {}
        for r in rows:
            by_metric.setdefault(r.metric_type, []).append({
                "period_label": r.period_label,
                "avg": float(r.avg) if r.avg is not None else None,
                "low": float(r.low) if r.low is not None else None,
                "high": float(r.high) if r.high is not None else None,
                "num_analysts": r.num_analysts,
                "growth_pct": float(r.growth_pct) if r.growth_pct is not None else None,
            })
        return {"stock_id": stock.id, "symbol": stock.symbol, "source": "YAHOO_FINANCE", "estimates": by_metric}
    finally:
        db.close()


@mcp_server.tool()
def get_insider_activity(symbol: str) -> dict:
    """Dated, named insider transactions — Yahoo Finance. Distinct from
    get_shareholding (NSE aggregate promoter %); this is individual,
    dated transactions."""
    from app.infrastructure.database.models import InsiderActivity

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = (
            db.query(InsiderActivity).filter_by(company_id=stock.id)
            .order_by(InsiderActivity.transaction_date.desc()).all()
        )
        return {
            "stock_id": stock.id, "symbol": stock.symbol, "source": "YAHOO_FINANCE",
            "transactions": [
                {
                    "date": r.transaction_date, "insider_name": r.insider_name,
                    "position": r.position, "text": r.transaction_text,
                    "shares": float(r.shares) if r.shares is not None else None,
                    "value": float(r.value) if r.value is not None else None,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@mcp_server.tool()
def get_corporate_actions(symbol: str) -> dict:
    """Dividend/split history — Yahoo Finance."""
    from app.infrastructure.database.models import CorporateAction

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = (
            db.query(CorporateAction).filter_by(company_id=stock.id)
            .order_by(CorporateAction.action_date.desc()).all()
        )
        return {
            "stock_id": stock.id, "symbol": stock.symbol, "source": "YAHOO_FINANCE",
            "actions": [{"date": r.action_date, "type": r.action_type, "value": float(r.value)} for r in rows],
        }
    finally:
        db.close()


@mcp_server.tool()
def get_company_news(symbol: str) -> dict:
    """Recent news headlines — Yahoo Finance (aggregates Reuters and other
    wire services)."""
    from app.infrastructure.database.models import CompanyNews

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = (
            db.query(CompanyNews).filter_by(company_id=stock.id)
            .order_by(CompanyNews.published_at.desc()).all()
        )
        return {
            "stock_id": stock.id, "symbol": stock.symbol, "source": "YAHOO_FINANCE",
            "news": [
                {
                    "headline": r.headline, "summary": r.summary, "provider": r.provider,
                    "url": r.url, "published_at": r.published_at.isoformat() if r.published_at else None,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@mcp_server.tool()
def get_earnings_calendar(symbol: str) -> dict:
    """Next earnings date + expected EPS/revenue range — Yahoo Finance
    ("future schedules")."""
    from app.infrastructure.database.models import EarningsCalendar

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        row = db.query(EarningsCalendar).filter_by(company_id=stock.id).first()
        if row is None:
            return {"stock_id": stock.id, "symbol": stock.symbol, "calendar": None}
        return {
            "stock_id": stock.id, "symbol": stock.symbol, "source": "YAHOO_FINANCE",
            "calendar": {
                "next_earnings_date": row.next_earnings_date,
                "ex_dividend_date": row.ex_dividend_date,
                "expected_eps_avg": float(row.expected_eps_avg) if row.expected_eps_avg is not None else None,
                "expected_eps_low": float(row.expected_eps_low) if row.expected_eps_low is not None else None,
                "expected_eps_high": float(row.expected_eps_high) if row.expected_eps_high is not None else None,
                "expected_revenue_avg": float(row.expected_revenue_avg) if row.expected_revenue_avg is not None else None,
                "expected_revenue_low": float(row.expected_revenue_low) if row.expected_revenue_low is not None else None,
                "expected_revenue_high": float(row.expected_revenue_high) if row.expected_revenue_high is not None else None,
            },
        }
    finally:
        db.close()


@mcp_server.tool()
def list_documents(symbol: str) -> dict:
    """Raw source documents on file for one stock (BSE filing PDFs, NSE
    annual reports) — Architecture v2 Stage 7. Each entry carries a sha256
    so a value's source PDF can be re-verified later, not just trusted on
    faith. Bytes live in MinIO; this lists metadata only (use
    GET /api/documents/{company_id}/{document_id}/download for the actual file)."""
    from app.infrastructure.database.models import Document

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        rows = (
            db.query(Document).filter_by(company_id=stock.id)
            .order_by(Document.retrieved_at.desc()).all()
        )
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "documents": [
                {
                    "source": r.source, "document_type": r.document_type, "url": r.url,
                    "sha256": r.sha256, "file_size": r.file_size,
                    "retrieved_at": r.retrieved_at.isoformat(),
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@mcp_server.tool()
def get_company_summary(symbol: str) -> dict:
    """Screener.in's free-text company description and key_points (which
    for many companies includes a real revenue-mix breakdown, e.g. TCS's
    BFSI/Consumer Business/Healthcare %). Sector-agnostic. Returns
    {"summary": null} if nothing has been captured yet."""
    from app.infrastructure.database.models import CompanySummary

    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        row = db.query(CompanySummary).filter_by(company_id=stock.id).first()
        if row is None:
            return {"stock_id": stock.id, "symbol": stock.symbol, "summary": None}
        return {
            "stock_id": stock.id, "symbol": stock.symbol,
            "summary": {
                "about": row.about, "key_points": row.key_points,
                "source": row.source, "retrieved_at": row.retrieved_at.isoformat(),
            },
        }
    finally:
        db.close()


@mcp_server.tool()
def analyze_stock(symbol: str, force_refresh: bool = False) -> dict:
    """Run (or reuse) the full fundamental-analysis pipeline for one stock —
    sector-aware scoring, provenance-tracked metrics, risks/catalysts, AI
    narrative. Returns the most recent COMPLETED analysis unless
    force_refresh=True or none exists yet, in which case a fresh pipeline
    run executes synchronously before returning (typically a few seconds to
    ~2 minutes, depending on how much ingestion is already cached)."""
    db = get_db()
    try:
        stock = _lookup_stock(db, symbol)
        if stock is None:
            return {"error": f"Stock '{symbol}' not found"}
        stock_id, display_symbol = stock.id, stock.symbol
        analysis = None if force_refresh else _latest_completed(db, stock_id)
    finally:
        db.close()

    if analysis is None:
        db = get_db()
        try:
            year = datetime.now().year
            seq_val = db.execute(sa.text("SELECT nextval('fa_analysis_seq')")).scalar()
            analysis_id = f"FA-{year}-{seq_val:06d}"
            db.add(FundamentalAnalysis(
                id=analysis_id, stock_id=stock_id, status="QUEUED", overall_progress=0,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            ))
            db.commit()
            for stage_key, _, _ in STAGES:
                db.add(AnalysisStage(
                    id=str(uuid.uuid4()), analysis_id=analysis_id,
                    stage_name=stage_key, status="PENDING", progress=0,
                ))
            db.commit()
        finally:
            db.close()

        logger.info("mcp: analyze_stock running fresh pipeline", analysis_id=analysis_id, stock_id=stock_id)
        run_analysis_pipeline(analysis_id, stock_id)  # same sync function background_tasks.add_task calls

        db = get_db()
        try:
            analysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
            if analysis is None:
                return {"error": f"Analysis {analysis_id} vanished after running — this should never happen"}
            result = _analysis_to_dict(analysis)
            result.update({
                "metrics": analysis.metrics, "scores": analysis.scores,
                "sector_analysis": analysis.sector_analysis, "peers": analysis.peers,
                "risks": analysis.risks or [], "catalysts": analysis.catalysts or [],
                "ai_analysis": analysis.ai_analysis,
            })
            return result
        finally:
            db.close()

    db = get_db()
    try:
        analysis = db.query(FundamentalAnalysis).filter_by(id=analysis.id).first()
        result = _analysis_to_dict(analysis)
        result.update({
            "metrics": analysis.metrics, "scores": analysis.scores,
            "sector_analysis": analysis.sector_analysis, "peers": analysis.peers,
            "risks": analysis.risks or [], "catalysts": analysis.catalysts or [],
            "ai_analysis": analysis.ai_analysis,
        })
        return result
    finally:
        db.close()


def mcp_asgi_app():
    """The mountable ASGI app — internal route path set to "/" so the parent
    FastAPI app's mount prefix (app.mount("/mcp", ...) in app/main.py) is the
    entire effective URL, not "/mcp/mcp"."""
    return mcp_server.streamable_http_app(streamable_http_path="/")
