"""
Analysis pipeline orchestrator.
Runs all stages sequentially, updating PostgreSQL state at each step.
Financial calculations are fully deterministic Python — no LLM in this file.
"""
from __future__ import annotations
import traceback
import uuid
from datetime import datetime, timezone

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis, AnalysisStage, AgentRun
from app.data.yfinance_client import fetch_financial_data
from app.calculations.engine import compute_metrics
from app.calculations.scoring import compute_scores, compute_data_quality, compute_confidence
from app.sectors.registry import get_framework, list_frameworks
from app.sectors.base import metric_status
from app.sectors.banking_data_bridge import inject_banking_bridge
from app.sectors.ledger_bridge import inject_ledger_bridge
from app.sectors.framework_loader import load_framework_doc
from app.ingestion.banking_ingestion import ingest_bank_filing
from app.ingestion.annual_report_ingestion import ingest_annual_report
from app.ingestion.screener_client import ingest_balance_sheet as screener_ingest_balance_sheet
from app.ingestion.screener_client import ingest_cash_flow as screener_ingest_cash_flow
from app.ingestion.screener_client import ingest_cash_flow_schedules as screener_ingest_cash_flow_schedules
from app.ingestion.screener_client import ingest_ratios as screener_ingest_ratios
from app.ingestion.screener_client import ingest_quarterly_metrics as screener_ingest_quarterly_metrics
from app.ingestion.screener_client import ingest_company_summary as screener_ingest_company_summary
from app.interpretation.brand_extraction import ingest_company_brands
from app.ingestion.earnings_call_client import ingest_earnings_call_transcript
from app.ingestion.yfinance_extended_client import ingest_all as ingest_yfinance_extended
from app.ingestion.shareholding_client import ingest_shareholding
from app.ingestion.screener_shareholding_client import ingest_screener_shareholding
from app.ingestion.live_price import fetch_live_price
from app.ingestion.pnl_history_client import ingest_pnl_history
from app.ingestion.quarterly_results_client import ingest_quarterly_results
from app.ingestion.tradingview_segments_client import ingest_business_segments
from app.ingestion.news_search_client import ingest_news_search
from app.ingestion.indianapi_client import ingest_analyst_recommendations
from app.ingestion.trendlyne_client import ingest_research_reports
from app.ingestion.valuation_history_client import ingest_valuation_history
from app.llm.client import llm_client as default_llm_client
from app.infrastructure.redis.client import cache_get, cache_set
from app.logger import logger

_SCREENER_INGEST_TTL = 60 * 60 * 24  # 24h — same cadence as the BSE quarterly-filing ingest below
_BANKING_INGEST_TTL = 60 * 60 * 24  # 24h — don't re-scrape/re-OCR on every re-run
_ANNUAL_REPORT_TTL = 60 * 60 * 24 * 300  # ~300d — a company publishes one new annual report per fiscal year
# Real bug found live 2026-09-21 (Welspun Corp, GT Action Construction
# Equipment): the long TTLs above got set even when EVERY area's LLM
# extraction was skipped because the primary model (Groq) was rate-limited
# for the day and the fallback-LLM-unreliable guard correctly refused to
# store a small-model answer — so a company unlucky enough to be analyzed
# during a quota-exhausted window was locked out of ever retrying until the
# ~300-day/7-day TTL expired, long after the quota itself had reset. Used
# instead of the long TTL whenever `default_llm_client.last_used_fallback`
# is true right after the ingestion call returns — cheap to retry (a 429 +
# local Ollama fallback call costs nothing but time), so a short TTL just
# means the next analysis run within the same day gets a real second try
# once Groq's daily quota frees up, with no manual cache-clear needed.
_LLM_RATE_LIMITED_RETRY_TTL = 60 * 60 * 3  # 3h
_COMPANY_SUMMARY_TTL = 60 * 60 * 24 * 30  # 30d — Screener's about/key_points text rarely changes
_BUSINESS_SEGMENTS_TTL = 60 * 60 * 24 * 90  # ~90d — a company reports new segment splits once a quarter at most
_NEWS_SEARCH_TTL = 60 * 60 * 24  # 1d — news is genuinely time-sensitive, unlike the other ingestion TTLs above
_ANALYST_RECS_TTL = 60 * 60 * 24 * 7  # 7d — analyst rating distributions don't shift daily
_CONCALL_CHECK_TTL = 60 * 60 * 24 * 25  # ~25d — checks for a new quarterly filing about monthly; the expensive guidance-extraction step has its own extraction_status gate below, independent of this
_TRENDLYNE_TTL = 60 * 60 * 24 * 7  # 7d — new broker reports land a few times a month at most
_EARNINGS_CALL_TTL = 60 * 60 * 24 * 60  # 60d — roughly one quarter, matches the filing cadence
_SHAREHOLDING_TTL = 60 * 60 * 24 * 60  # 60d — NSE files this quarterly; pledge % is the governance-critical field
_SCREENER_SHAREHOLDING_TTL = 60 * 60 * 24 * 60  # 60d — same cadence, supplementary trend-depth source only
_PNL_HISTORY_TTL = 60 * 60 * 24  # 24h — same cadence as other Screener-sourced ingestion
_QUARTERLY_RESULTS_TTL = 60 * 60 * 24  # 24h — same cadence; new quarters land roughly every 3 months
# Longer than _QUARTERLY_RESULTS_TTL — this stage makes a real LLM call (the
# other quarterly stage is pure Screener + arithmetic), and a new Investor
# Presentation filing is quarterly-cadence (roughly every 3 months), so
# checking daily would be mostly wasted re-fetches. A week balances
# reasonable freshness against not re-hitting NSE/the LLM needlessly.
_QUARTERLY_SECTOR_KPI_TTL = 60 * 60 * 24 * 7  # 7 days
_BALANCE_SHEET_HISTORY_TTL = 60 * 60 * 24  # 24h — same cadence as other Screener-sourced ingestion
_CASH_FLOW_HISTORY_TTL = 60 * 60 * 24  # 24h — Balance Sheet Analysis Engine, Milestone 1
_CASH_FLOW_SCHEDULES_TTL = 60 * 60 * 24  # 24h — Cash Flow Analysis Engine, Milestone 1
_BS_RATIOS_TTL = 60 * 60 * 24  # 24h — Balance Sheet Analysis Engine, Milestone 1 (latest-period only, re-checked daily like the rest of Screener ingestion)
# Real bug found live on 3 separate companies (Tata Technologies, Coforge,
# Pine Labs), then again on a 4th (GNFC, 2026-09-22, user's explicit
# instruction to "correct it for each and every metric ingestion... check
# and update everywhere" after the same class of bug turned up in
# pnl_history alone): the STANDALONE/CONSOLIDATED dual-fetch loop inside
# every screener_client.py/pnl_history_client.py ingestion function that
# has one — `ingest_pnl_history`, `ingest_balance_sheet`, `ingest_cash_flow`,
# `ingest_cash_flow_schedules`, `ingest_ratios` — can succeed for STANDALONE
# and transiently fail for CONSOLIDATED alone (a single flaky scrape, not a
# real "this company has no consolidated financials" case — confirmed live:
# Pine Labs' and GNFC's CONSOLIDATED figures genuinely exist on Screener,
# just weren't ingested), but the cache key was set unconditionally either
# way, LOCKING IN the gap for the full 24h TTL — worse,
# `pl_intelligence`/`cash_flow_intelligence`'s own `single_statement_source`
# heuristic (built specifically to handle companies with GENUINELY no
# consolidated data, e.g. Netweb Technologies) then silently relabeled the
# incomplete STANDALONE-only ledger AS "Consolidated", masking the gap
# instead of surfacing it. A much shorter retry TTL specifically for a
# "STANDALONE succeeded, CONSOLIDATED came back with zero rows" result
# means the SAME DAY'S next analysis run gets a fresh shot at it — cheap
# insurance against a single flaky scrape, without permanently hammering
# Screener for a company that's genuinely standalone-only (those keep
# re-triggering this shorter retry too, since there's no way to distinguish
# "transient failure" from "genuinely absent" from the ledger alone — 4h
# keeps that cost to ~6 scrape attempts/day instead of 24, while still
# recovering same-day rather than needing a manual re-ingest like this bug
# has now needed 4 times). EVERY dual-statement-type ingestor in this
# pipeline must use this TTL-gating pattern — check this comment before
# adding a new one and wiring its cache_set call unconditionally.
_CONSOLIDATED_GAP_RETRY_TTL = 60 * 60 * 4  # 4h
_VALUATION_HISTORY_TTL = 60 * 60 * 24  # 24h — same cadence; also refreshes the current month's price point
_YFINANCE_EXTENDED_TTL = 60 * 60 * 24  # 24h — analyst targets/news/calendar are time-sensitive, unlike the above


STAGES = [
    ("company_identification",    "Company Identification",     5),
    ("financial_data_collection", "Financial Data Collection",  15),
    ("income_statement_analysis", "Income Statement Analysis",  25),
    ("balance_sheet_analysis",    "Balance Sheet Analysis",     35),
    ("cash_flow_analysis",        "Cash Flow Analysis",         45),
    ("ratio_calculations",        "Ratio Calculations",         55),
    ("metric_validation",         "Metric Validation",          60),
    ("sector_analysis",           "Sector Analysis",            68),
    ("peer_comparison",           "Peer Comparison",            75),
    ("risk_analysis",             "Risk Analysis",              80),
    ("scoring",                   "Scoring",                    85),
    ("ai_analysis",               "AI Investment Analysis",     92),
    ("report_blueprint",          "Business Interpretation",    93),
    ("pl_intelligence_scoring",   "P&L Intelligence Scoring",   94),
    ("balance_sheet_intelligence_scoring", "Balance Sheet Intelligence", 95),
    ("cash_flow_intelligence_scoring", "Cash Flow Intelligence",     96),
    ("quarterly_analysis",        "Quarterly Analysis",          97),
    ("quarterly_sector_kpis",     "Quarterly Sector KPIs",       98),
    ("score_refinement",          "Score Refinement",           99),
    ("report_generation",         "Report Generation",         100),
]
# Real bug found live 2026-09-22: quarterly_analysis/quarterly_sector_kpis
# were appended here (99/100) without renumbering the two stages already
# after them (score_refinement/report_generation), pushing those to
# 101/102 — `overall_progress` is read straight off this 3rd tuple element
# (see `_set_stage` below) with no clamping on either side (backend or
# AnalysisProgress.tsx's `{progress}%` / `width: ${progress}%`), so the
# dashboard's progress bar and percentage genuinely read past 100% during
# the pipeline's last two stages. Every value above must stay in [0, 100]
# and strictly increasing — check this whenever a stage is added or
# reordered, since nothing else enforces that invariant.


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _log_agent_run(
    db,
    analysis_id: str,
    stage_name: str,
    agent_name: str,
    status: str,
    started_at: datetime,
    duration_ms: int | None = None,
    token_count: int | None = None,
    model_used: str | None = None,
    input_summary: str | None = None,
    error: str | None = None,
):
    """Write one AgentRun audit row — best-effort, never raises."""
    try:
        row = AgentRun(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            stage_name=stage_name,
            agent_name=agent_name,
            status=status,
            duration_ms=duration_ms,
            token_count=token_count,
            model_used=model_used,
            input_summary=input_summary,
            error=error,
            started_at=started_at,
            completed_at=_now(),
        )
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()


def _has_consolidated_rows(rows: list) -> bool:
    """True if any row in an `ingest_*`/`ingest_pnl_history`-style return
    list is CONSOLIDATED — see `_CONSOLIDATED_GAP_RETRY_TTL`'s own comment
    for why this gates the cache TTL rather than being ignored."""
    return any(getattr(r, "statement_type", None) == "CONSOLIDATED" for r in (rows or []))


def _update_analysis(db, analysis: FundamentalAnalysis, **kwargs):
    for k, v in kwargs.items():
        setattr(analysis, k, v)
    analysis.updated_at = _now()
    db.commit()


def _set_stage(db, analysis: FundamentalAnalysis, stage_key: str, status: str,
               progress: int, message: str = "", result: dict | None = None, error: str | None = None):
    stage = db.query(AnalysisStage).filter_by(
        analysis_id=analysis.id, stage_name=stage_key
    ).first()
    if stage is None:
        stage = AnalysisStage(
            id=str(uuid.uuid4()),
            analysis_id=analysis.id,
            stage_name=stage_key,
        )
        db.add(stage)
    stage.status = status
    stage.progress = progress
    stage.message = message
    if result is not None:
        stage.result = result
    if error is not None:
        stage.error = error
    if status == "RUNNING" and stage.started_at is None:
        stage.started_at = _now()
    if status in ("COMPLETED", "FAILED"):
        stage.completed_at = _now()
    db.commit()

    # Update analysis current stage
    overall_progress = next((p for k, _, p in STAGES if k == stage_key), 0)
    analysis.current_stage = stage_key
    analysis.stage_progress = 100 if status == "COMPLETED" else 50
    analysis.overall_progress = overall_progress
    analysis.updated_at = _now()
    db.commit()


def run_analysis_pipeline(analysis_id: str, stock_id: str) -> None:
    """
    Full analysis pipeline. Runs synchronously inside a background task.
    Updates analysis record at every stage.
    """
    db = get_db()
    try:
        analysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
        if analysis is None:
            logger.error("Analysis not found", analysis_id=analysis_id)
            return

        _update_analysis(db, analysis, status="RUNNING", started_at=_now())

        # ── Stage 1: Company Identification ───────────────────────────────────
        _set_stage(db, analysis, "company_identification", "RUNNING", 10, "Identifying company")
        try:
            from app.infrastructure.database.models import Stock
            stock = db.query(Stock).filter_by(id=stock_id).first()
            if stock is None:
                raise ValueError(f"Stock {stock_id} not found in database")
            exchange, symbol = stock.id.split(":", 1)
            company_info = {
                "stock_id": stock.id,
                "symbol": stock.symbol,
                "exchange": stock.exchange,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "industry": stock.industry,
                "basic_industry": stock.basic_industry,
                "macro_sector": stock.macro_sector,
                "market_cap": float(stock.market_cap) if stock.market_cap else None,
                "market_cap_category": stock.market_cap_category,
                "isin": stock.isin,
            }
            # The deep report (app/bie: sourced facts from exchange filings, the sector-first PDF and the Excel model) is
            # built alongside every full analysis, on its own thread so it never holds this pipeline up or fails it.
            # A company built within the last week is left alone. Its progress shows on the dashboard's Deep Report page.
            try:
                from datetime import timedelta
                from app.bie.jobs import start_in_background
                company_info["deep_report"] = start_in_background(stock.symbol, if_older_than=timedelta(days=7))
            except Exception as deep_error:  # noqa: BLE001
                logger.warning("deep report build could not be started", symbol=stock.symbol, error=str(deep_error))
            # Fetched fresh here (not reused from Stage 2's cached financial
            # data, which can be hours old by report time) — see
            # app/ingestion/live_price.py's module docstring for why this is
            # Yahoo Finance, not Dhan/Kite, despite both being connected.
            try:
                company_info["current_price"] = fetch_live_price(stock.symbol, stock.exchange)
            except Exception as e:
                logger.warning("Live price fetch failed", stock_id=stock.id, error=str(e))
                company_info["current_price"] = None
            _update_analysis(db, analysis, company_info=company_info)
            _set_stage(db, analysis, "company_identification", "COMPLETED", 100,
                       f"Identified: {stock.company_name}", result=company_info)
        except Exception as e:
            _set_stage(db, analysis, "company_identification", "FAILED", 0, error=str(e))
            _update_analysis(db, analysis, status="FAILED", error_message=str(e), completed_at=_now())
            return

        # ── Stage 2: Financial Data Collection ────────────────────────────────
        _set_stage(db, analysis, "financial_data_collection", "RUNNING", 10,
                   f"Fetching financial data for {symbol}")
        _stage2_start = _now()
        try:
            financial_data = fetch_financial_data(exchange, symbol)
            if financial_data.get("error") and not any(
                financial_data.get(k) for k in ["income", "balance", "cash_flow"]
            ):
                raise ValueError(f"Failed to fetch financial data: {financial_data['error']}")
            _update_analysis(db, analysis, financial_data=financial_data)
            _set_stage(db, analysis, "financial_data_collection", "COMPLETED", 100,
                       "Financial data collected from yfinance")
            _log_agent_run(db, analysis_id, "financial_data_collection", "yfinance_client",
                           "COMPLETED", _stage2_start,
                           duration_ms=int((_now() - _stage2_start).total_seconds() * 1000),
                           input_summary=f"{exchange}:{symbol}")
        except Exception as e:
            _set_stage(db, analysis, "financial_data_collection", "FAILED", 0, error=str(e))
            _log_agent_run(db, analysis_id, "financial_data_collection", "yfinance_client",
                           "FAILED", _stage2_start, error=str(e))
            _update_analysis(db, analysis, status="FAILED", error_message=str(e), completed_at=_now())
            return

        # ── Stages 3-5: IS / BS / CF Analysis (mark as completed quickly) ─────
        for stage_key, stage_label, _ in [
            ("income_statement_analysis", "Income Statement Analysis", 25),
            ("balance_sheet_analysis", "Balance Sheet Analysis", 35),
            ("cash_flow_analysis", "Cash Flow Analysis", 45),
        ]:
            _set_stage(db, analysis, stage_key, "RUNNING", 50, f"Processing {stage_label}")
            _set_stage(db, analysis, stage_key, "COMPLETED", 100, f"{stage_label} complete")

        # ── Stage 6: Ratio Calculations ───────────────────────────────────────
        _set_stage(db, analysis, "ratio_calculations", "RUNNING", 10, "Computing financial ratios")
        try:
            metrics = compute_metrics(financial_data)
            _update_analysis(db, analysis, metrics=metrics)
            _set_stage(db, analysis, "ratio_calculations", "COMPLETED", 100,
                       f"Computed {len(metrics)} metric fields")
        except Exception as e:
            _set_stage(db, analysis, "ratio_calculations", "FAILED", 0, error=str(e))
            metrics = {}

        # ── Stage 7: Metric Validation ────────────────────────────────────────
        _set_stage(db, analysis, "metric_validation", "RUNNING", 10, "Validating metrics")
        try:
            validations = _validate_metrics(metrics, financial_data)
            _update_analysis(db, analysis, metric_validations=validations)
            _set_stage(db, analysis, "metric_validation", "COMPLETED", 100,
                       f"Validated {len(validations)} metrics")
        except Exception as e:
            validations = {}
            _set_stage(db, analysis, "metric_validation", "FAILED", 0, error=str(e))

        # ── Stage 8: Sector Analysis ──────────────────────────────────────────
        _set_stage(db, analysis, "sector_analysis", "RUNNING", 10, "Applying sector framework")
        try:
            sector = company_info.get("sector") or ""
            industry = company_info.get("industry") or ""
            basic_industry = company_info.get("basic_industry") or ""
            framework = get_framework(sector, industry=industry, basic_industry=basic_industry)
            sector_matched = framework.sector_name != "Generic"

            if framework.sector_name in ("Banks", "NBFCs"):
                # Architecture v2 Stage 8: generalized from Banks-only to also
                # cover NBFCs. No new ingestion code needed — confirmed live
                # that Screener.in uses the identical field shape (revenue/
                # interest/gross_npa/net_npa) for NBFCs as for banks (e.g.
                # Bajaj Finance), and BSE's OCR extraction prompt already asks
                # generically for CAR/GNPA/NNPA/ROA, not bank-specific wording.
                # NSE's annual-report locator simply won't find a CASA section
                # for an NBFC — same graceful "N/A, not crash" pattern already
                # used everywhere else in this pipeline. See
                # app/sectors/nbfc.py's NBFCSector._compute_special_metric for
                # the other half of this (reads the same bridge dict
                # BankingSector does — the metric_ids genuinely overlap).

                # Screener-first: fast (Playwright, no LLM), tried before any
                # BSE/NSE ingestion below. Covers gross_npa/net_npa/balance
                # sheet immediately; BSE OCR and NSE annual-report ingestion
                # still run unconditionally afterward since they're the only
                # source for CASA/PCR/slippage/CAR/ROA/CET1/Tier1/credit_cost
                # — see screener_client.py's module docstring for the full
                # rationale and the trust-tier reasoning (Screener stays
                # tier=2, so a primary filing still wins if both are present).
                # Balance sheet ingestion moved to the universal any-sector
                # block below (P&L Analysis System, Stage P0, 2026-09-13) —
                # every sector gets it now, not just Banks/NBFCs, so it's no
                # longer called from here (avoids a redundant double-fetch
                # under two different cache keys on a bank's first analysis).
                _screener_cache_key = f"screener_ingest:{stock.id}"
                if not cache_get(_screener_cache_key):
                    try:
                        screener_ingest_quarterly_metrics(db, company_id=stock.id, symbol=symbol)
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        logger.warning("Screener ingestion failed, continuing with BSE/NSE only",
                                       stock_id=stock.id, error=str(e))
                    cache_set(_screener_cache_key, "1", _SCREENER_INGEST_TTL)

                # 5-year OCR backfill (~15-20 Groq calls) is deliberately NOT
                # run here — it reliably collided with Groq's per-minute rate
                # limit and stalled a brand-new bank's first analysis on this
                # stage for many minutes (see banking_ingestion.py's
                # backfill_all_banks docstring, 2026-09-10). It now runs only
                # as its own bounded/resumable batch job, same pattern as the
                # NSE annual-report batch below — POST
                # /api/banking/backfill/ingest-batch, or a cron. This request
                # still gets current-quarter figures promptly via
                # ingest_bank_filing right below (one Groq call, not twenty).

                _ingest_cache_key = f"banking_ingest:{stock.id}"
                if not cache_get(_ingest_cache_key):
                    try:
                        ingest_bank_filing(db, company_id=stock.id, symbol=symbol)
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        logger.warning("Banking ingestion failed, continuing with what's stored",
                                       stock_id=stock.id, error=str(e))
                    cache_set(_ingest_cache_key, "1", _BANKING_INGEST_TTL)

                inject_banking_bridge(financial_data, db, stock.id)
            elif framework.sector_name in ("Housing Finance", "Microfinance", "Gold Loans"):
                # Same bridge as Banks/NBFCs above, minus the BSE-OCR-filing
                # ingestion call (that path's SEBI Reg-30 filing format is
                # bank/large-NBFC-specific, unvalidated for these smaller
                # sub-sectors) — just a read of whatever's already in the
                # ledger, including nim/cost_to_income_ratio from the
                # Investor Presentation cascade below (quarterly_sector_kpis
                # stage, `_SECTOR_CONFIG` in quarterly_operating_metrics_
                # ingestion.py covers all 3 of these sub-sectors too).
                inject_banking_bridge(financial_data, db, stock.id)

            # Universal, any sector (2026-09-16, moved out of the Banks-only
            # block above): fills CASA/PCR/slippage for banks (not disclosed
            # in BSE's quarterly filing, only the annual report's notes) and,
            # for every sector, Gross PPE + the Other Liabilities breakdown
            # (accrued expenses / deferred revenue) — see
            # annual_report_ingestion.py's module docstring for what's new
            # and why it was validated against Groq before generalizing past
            # banking. The bank-only areas simply find no matching pages for
            # a non-bank company and are skipped, at no extra cost.
            _annual_report_cache_key = f"annual_report:{stock.id}"
            if not cache_get(_annual_report_cache_key):
                try:
                    ingest_annual_report(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Annual report ingestion failed, continuing with what's stored",
                                   stock_id=stock.id, error=str(e))
                # Short retry TTL, not the long one, if the primary LLM was
                # rate-limited during this attempt — see _LLM_RATE_LIMITED_RETRY_TTL.
                _ar_ttl = _LLM_RATE_LIMITED_RETRY_TTL if default_llm_client.last_used_fallback else _ANNUAL_REPORT_TTL
                cache_set(_annual_report_cache_key, "1", _ar_ttl)

            # Universal, any sector (2026-09-12): Screener's company summary
            # (about + key_points, sometimes a real revenue-mix breakdown —
            # confirmed on TCS) and the BSE earnings-call transcript's raw
            # document. Both are sector-agnostic sources; only the transcript's
            # LLM *extraction* is sector-specific (IT-services KPIs only, so
            # far) — the transcript itself is still found/stored for every
            # sector, since the document alone is useful even without one.
            _summary_cache_key = f"company_summary:{stock.id}"
            if not cache_get(_summary_cache_key):
                try:
                    screener_ingest_company_summary(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Company summary ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_summary_cache_key, "1", _COMPANY_SUMMARY_TTL)

            # Any sector: structured brand extraction (Premium PDF System,
            # Stage B1, 2026-09-14) — from the company_summary.key_points
            # just ingested above. Silently produces nothing for companies
            # whose Key Points is only the free-preview stub (too short to
            # name any brand) — see brand_extraction.py's own length gate.
            _brands_cache_key = f"company_brands:{stock.id}"
            if not cache_get(_brands_cache_key):
                try:
                    ingest_company_brands(db, company_id=stock.id)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Brand extraction failed", stock_id=stock.id, error=str(e))
                cache_set(_brands_cache_key, "1", _COMPANY_SUMMARY_TTL)

            _transcript_cache_key = f"earnings_call_transcript:{stock.id}"
            if not cache_get(_transcript_cache_key):
                try:
                    ingest_earnings_call_transcript(
                        db, company_id=stock.id, symbol=symbol,
                        extract_it_metrics=(framework.sector_name == "Information Technology"),
                        extract_fintech_metrics=(framework.sector_name == "Fintech"),
                        extract_fmcg_metrics=(framework.sector_name == "Fast Moving Consumer Goods"),
                    )
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Earnings call transcript ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_transcript_cache_key, "1", _EARNINGS_CALL_TTL)

            # Any sector, fully autonomous (no agent-fetch step, unlike the
            # IndMoney analyst_consensus row) — analyst targets/ratings
            # (own row, source=YAHOO_FINANCE, never blended with IndMoney's),
            # forward EPS/revenue estimates, insider transactions, corporate
            # actions, news, earnings calendar, governance risk scores.
            _yfinance_ext_cache_key = f"yfinance_extended:{stock.id}"
            if not cache_get(_yfinance_ext_cache_key):
                try:
                    ingest_yfinance_extended(db, company_id=stock.id, symbol=symbol, exchange=stock.exchange,
                                              company_name=stock.company_name)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Yahoo Finance extended ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_yfinance_ext_cache_key, "1", _YFINANCE_EXTENDED_TTL)

            # Any sector: broader news search (Deep Research System, Stage
            # R2, 2026-09-14) — Google News RSS, additive to the Yahoo rows
            # ingest_yfinance_extended just stored above (own source tag,
            # deduped by URL against them). Short TTL since news is
            # genuinely time-sensitive, unlike the other ingestion steps.
            _news_search_cache_key = f"news_search:{stock.id}"
            if not cache_get(_news_search_cache_key):
                try:
                    ingest_news_search(db, company_id=stock.id, company_name=stock.company_name, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("News search ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_news_search_cache_key, "1", _NEWS_SEARCH_TTL)

            # Any sector: analyst rating distribution (IndianAPI.in Free
            # plan, 2026-09-14) — autonomously fills AnalystConsensus's
            # buy_pct/hold_pct/sell_pct fields (migration 0012), previously
            # only ever populated via a Claude session's IndMoney MCP call.
            # No-op (returns None immediately) if INDIANAPI_KEY isn't set.
            _analyst_recs_cache_key = f"analyst_recs_indianapi:{stock.id}"
            if not cache_get(_analyst_recs_cache_key):
                try:
                    ingest_analyst_recommendations(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("IndianAPI analyst recommendations ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_analyst_recs_cache_key, "1", _ANALYST_RECS_TTL)

            # Any sector: broker research-report history (Trendlyne, free
            # table only — 2026-09-14). Distinct from the analyst-rating
            # distribution above: that's a current-snapshot aggregate, this
            # is the dated history of individual broker calls (target
            # price, rating, whether it was later hit).
            _trendlyne_cache_key = f"trendlyne_reports:{stock.id}"
            if not cache_get(_trendlyne_cache_key):
                try:
                    ingest_research_reports(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Trendlyne research report ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_trendlyne_cache_key, "1", _TRENDLYNE_TTL)

            # Any sector: Concall Intelligence System (Stages C0-C5, built
            # earlier — 2026-09-14 finding: it was only ever wired up
            # manually, so only the 2 companies it was tested on had any
            # transcript data at all). Finds the most recent NSE-filed
            # transcript (many companies won't have one — that's a genuine
            # no-data case, not a failure) and runs the full pipeline:
            # ingest -> parse -> embed -> guidance extraction ->
            # credibility/promises. Each step is gated on the transcript's
            # own `extraction_status` (PENDING -> PARSED -> EXTRACTED), not
            # just the outer cache key, so re-running this for a company
            # whose latest transcript was already fully processed skips
            # straight to the cheap, deterministic credibility recompute —
            # it never re-pays for guidance extraction's real Groq/Llama
            # calls (confirmed live: ~90s with rate-limit retries) on a
            # transcript that hasn't changed.
            _concall_check_cache_key = f"concall_check:{stock.id}"
            if not cache_get(_concall_check_cache_key):
                try:
                    from app.ingestion.nse_concall_client import find_transcript_filings, ingest_transcript
                    from app.ingestion.concall_parser import parse_and_store_utterances
                    from app.interpretation.concall_retrieval import embed_transcript
                    from app.interpretation.guidance_extraction import (
                        extract_guidance_for_transcript, extract_topic_sentiment_for_transcript,
                    )
                    from app.interpretation.credibility import compute_credibility, sync_promises
                    from app.ingestion.arthneeti_client import ingest_concall_highlights
                    from app.interpretation.concall_highlights_fallback import generate_highlights_fallback
                    from app.infrastructure.database.models import ConcallHighlight

                    filings = find_transcript_filings(symbol, lookback_days=120)
                    if filings:
                        transcript = ingest_transcript(db, company_id=stock.id, symbol=symbol, filing=filings[0])
                        db.commit()
                        if transcript is not None:
                            if transcript.extraction_status == "PENDING":
                                parse_and_store_utterances(db, transcript)
                                db.commit()
                            if transcript.extraction_status == "PARSED":
                                embed_transcript(db, transcript.id)
                                db.commit()
                                extract_guidance_for_transcript(db, transcript.id)
                                db.commit()
                                # Premium PDF System, Stage B2 — same transcript,
                                # no extra fetch. Runs once, same as guidance
                                # extraction just above: this whole block is
                                # gated on extraction_status=="PARSED", and
                                # guidance extraction already advanced it to
                                # "EXTRACTED" by the time this line runs, so a
                                # later pipeline run for the same transcript
                                # never re-enters here (its own DB unique
                                # constraint on (transcript_id, topic) is a
                                # second line of defense, not the primary one).
                                extract_topic_sentiment_for_transcript(db, transcript.id)
                                db.commit()
                            if transcript.extraction_status == "EXTRACTED":
                                compute_credibility(db, stock.id)
                                sync_promises(db, transcript.id)
                                db.commit()
                                # Results & Concall Highlights (2026-09-15):
                                # arthneeti.com primary (already-AI-generated,
                                # free), our own deterministic synthesis from
                                # the extraction just above as secondary —
                                # gated on the transcript-unique row existing
                                # at all, not a cache TTL, since it's a single
                                # cheap write per transcript, not a recurring
                                # fetch.
                                existing_highlight = (
                                    db.query(ConcallHighlight)
                                    .filter_by(transcript_id=transcript.id)
                                    .first()
                                )
                                if existing_highlight is None:
                                    row = ingest_concall_highlights(
                                        db, transcript_id=transcript.id, company_id=stock.id,
                                        company_name=stock.company_name, quarter=transcript.quarter,
                                    )
                                    if row is None:
                                        sections = generate_highlights_fallback(db, transcript.id)
                                        if sections:
                                            db.add(ConcallHighlight(
                                                id=str(uuid.uuid4()), transcript_id=transcript.id,
                                                company_id=stock.id, source="GENERATED",
                                                sections=sections, source_url=None,
                                                retrieved_at=datetime.now(timezone.utc),
                                            ))
                                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Concall Intelligence ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_concall_check_cache_key, "1", _CONCALL_CHECK_TTL)

            # Any sector: governance/integrity layer (Architecture v2 Stage
            # 3) — was fully built (shareholding %, pledge %, deterministic
            # event detection) but never actually wired into the pipeline
            # before now, so it only had data for the 2 companies tested
            # manually. NSE is the sole pledge-% source (governance-critical
            # — see shareholding_client.py's module docstring); Screener is
            # supplementary trend depth only (no pledge field at all — see
            # migration 0016), stored in its own table, never blended in.
            _shareholding_cache_key = f"shareholding:{stock.id}"
            if not cache_get(_shareholding_cache_key):
                try:
                    ingest_shareholding(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("NSE shareholding ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_shareholding_cache_key, "1", _SHAREHOLDING_TTL)

            _screener_shareholding_cache_key = f"shareholding_screener:{stock.id}"
            if not cache_get(_screener_shareholding_cache_key):
                try:
                    ingest_screener_shareholding(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Screener shareholding ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_screener_shareholding_cache_key, "1", _SCREENER_SHAREHOLDING_TTL)

            # Any sector: multi-year balance sheet (P&L Analysis System,
            # Stage P0, 2026-09-13) — was previously Banks/NBFCs-only (see
            # the removed call above); every sector gets 12Y of Screener's
            # balance sheet now, needed for ROE and the P&L calc engine.
            #
            # Real gap found live on GNFC (2026-09-22, same class of bug as
            # pnl_history/cash_flow_schedules/ratios below, just never
            # applied here): this call's return value was discarded and the
            # cache always got the full 24h TTL regardless of whether
            # CONSOLIDATED actually landed — the exact same
            # "STANDALONE succeeded, CONSOLIDATED transiently failed, gap
            # locked in for a full day" bug _CONSOLIDATED_GAP_RETRY_TTL was
            # built for, just left unwired on this one and cash_flow below.
            _balance_sheet_cache_key = f"balance_sheet_history:{stock.id}"
            if not cache_get(_balance_sheet_cache_key):
                _bsh_rows = []
                try:
                    _bsh_rows = screener_ingest_balance_sheet(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Balance sheet history ingestion failed", stock_id=stock.id, error=str(e))
                _bsh_ttl = _BALANCE_SHEET_HISTORY_TTL if _has_consolidated_rows(_bsh_rows) else _CONSOLIDATED_GAP_RETRY_TTL
                cache_set(_balance_sheet_cache_key, "1", _bsh_ttl)

            # Any sector: multi-year cash flow (Balance Sheet Analysis Engine,
            # Milestone 1) — operating/investing/financing/net/free cash flow,
            # not previously ingested anywhere; needed for the new engine's
            # CFO-based red flags (CFO vs. PAT divergence, capex without cash
            # generation). Same gap-retry treatment as balance sheet above.
            _cash_flow_history_cache_key = f"cash_flow_history:{stock.id}"
            if not cache_get(_cash_flow_history_cache_key):
                _cfh_rows = []
                try:
                    _cfh_rows = screener_ingest_cash_flow(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Cash flow history ingestion failed", stock_id=stock.id, error=str(e))
                _cfh_ttl = _CASH_FLOW_HISTORY_TTL if _has_consolidated_rows(_cfh_rows) else _CONSOLIDATED_GAP_RETRY_TTL
                cache_set(_cash_flow_history_cache_key, "1", _cfh_ttl)

            # Any sector: Screener's cash-flow "Schedule" line-item
            # breakdown (Cash Flow Analysis Engine, Milestone 1) —
            # receivables/inventory/payables cash impact, gross debt
            # raised/repaid, capex, dividends. Undocumented internal
            # Screener endpoint (see screener_client.py's module comment
            # above `ingest_cash_flow_schedules`) — degrades gracefully if
            # it ever breaks, never fails this stage.
            _cash_flow_schedules_cache_key = f"cash_flow_schedules:{stock.id}"
            if not cache_get(_cash_flow_schedules_cache_key):
                _cfs_rows = []
                try:
                    _cfs_rows = screener_ingest_cash_flow_schedules(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Cash flow schedules ingestion failed", stock_id=stock.id, error=str(e))
                _cfs_ttl = _CASH_FLOW_SCHEDULES_TTL if _has_consolidated_rows(_cfs_rows) else _CONSOLIDATED_GAP_RETRY_TTL
                cache_set(_cash_flow_schedules_cache_key, "1", _cfs_ttl)

            # Any sector: Screener's own latest-period ratios (Balance Sheet
            # Analysis Engine, Milestone 1) — debtor/inventory/payable days,
            # CCC, ROCE/ROE. A same-methodology cross-check against the new
            # engine's own (mostly yfinance-sourced) working-capital series,
            # not its source of truth.
            _bs_ratios_cache_key = f"bs_ratios:{stock.id}"
            if not cache_get(_bs_ratios_cache_key):
                _ratios_rows = []
                try:
                    _ratios_rows = screener_ingest_ratios(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Screener ratios ingestion failed", stock_id=stock.id, error=str(e))
                _ratios_ttl = _BS_RATIOS_TTL if _has_consolidated_rows(_ratios_rows) else _CONSOLIDATED_GAP_RETRY_TTL
                cache_set(_bs_ratios_cache_key, "1", _ratios_ttl)

            # Any sector: multi-year P&L (P&L Analysis System, Stage P0,
            # 2026-09-13) — 12 years of Screener's standalone P&L, the core
            # input to the new P&L calculation engine (Stage P1).
            _pnl_history_cache_key = f"pnl_history:{stock.id}"
            if not cache_get(_pnl_history_cache_key):
                _pnl_rows = []
                try:
                    _pnl_rows = ingest_pnl_history(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("P&L history ingestion failed", stock_id=stock.id, error=str(e))
                _pnl_ttl = _PNL_HISTORY_TTL if _has_consolidated_rows(_pnl_rows) else _CONSOLIDATED_GAP_RETRY_TTL
                cache_set(_pnl_history_cache_key, "1", _pnl_ttl)

            # Any sector: multi-quarter P&L (Quarterly Report Extraction
            # Engine, Tier 1, 2026-09-20) — every quarter Screener has, not
            # just the latest, qtr_-prefixed to avoid colliding with the
            # pnl_ (annual) namespace above on a Q4/fiscal-year-end date.
            # Same dual STANDALONE/CONSOLIDATED loop, same gap-retry
            # treatment as pnl_history above — see _CONSOLIDATED_GAP_RETRY_TTL's
            # comment.
            _quarterly_results_cache_key = f"quarterly_results:{stock.id}"
            if not cache_get(_quarterly_results_cache_key):
                _qr_rows = []
                try:
                    _qr_rows = ingest_quarterly_results(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Quarterly results ingestion failed", stock_id=stock.id, error=str(e))
                _qr_ttl = _QUARTERLY_RESULTS_TTL if _has_consolidated_rows(_qr_rows) else _CONSOLIDATED_GAP_RETRY_TTL
                cache_set(_quarterly_results_cache_key, "1", _qr_ttl)

            # Any sector: business-segment revenue history (Deep Research
            # System, Stage R1, 2026-09-14) — sourced from TradingView's
            # financials-segments page, anchored to this company's own
            # pnl_sales history just ingested above (see
            # tradingview_segments_client.py's module docstring for why).
            _segments_cache_key = f"business_segments:{stock.id}"
            if not cache_get(_segments_cache_key):
                try:
                    ingest_business_segments(db, company_id=stock.id, symbol=symbol)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Business segment ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_segments_cache_key, "1", _BUSINESS_SEGMENTS_TTL)

            # Any sector: real historical P/E and P/B (Architecture v2 Stage
            # 4 — built earlier, never wired into the pipeline until now,
            # found while surveying for reuse during the P&L Analysis System
            # rollout). Also supplies real historical prices for the P&L
            # engine's Stock Price CAGR.
            _valuation_history_cache_key = f"valuation_history:{stock.id}"
            if not cache_get(_valuation_history_cache_key):
                try:
                    ingest_valuation_history(db, company_id=stock.id, symbol=symbol, exchange=stock.exchange)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.warning("Valuation history ingestion failed", stock_id=stock.id, error=str(e))
                cache_set(_valuation_history_cache_key, "1", _VALUATION_HISTORY_TTL)

            # Any sector: surface whatever's actually in the ledger for this
            # framework's declared non-yfinance metrics (e.g. IT Services'
            # attrition_rate/utilization_rate/deal_wins_tcv, now sourced from
            # the earnings-call transcript above) — see ledger_bridge.py.
            non_yfinance_ids = [m.name for m in framework.key_metrics() if not m.available_from_yfinance]
            if non_yfinance_ids:
                inject_ledger_bridge(financial_data, db, stock.id, non_yfinance_ids)

            # Screener.in as Primary Source of Truth (2026-09-16) — must run
            # HERE, not at the earlier "ratio_calculations" stage where
            # `metrics` was first computed: every Screener ingestion call
            # this depends on (balance sheet, cash flow, ratios, P&L
            # history, company summary) runs inside THIS stage's try block,
            # above this line, so no Screener ledger data exists yet at
            # "ratio_calculations" for a brand-new company's first analysis.
            # Overwrites specific `metrics` keys in place with Screener-
            # sourced equivalents (reusing pnl_engine.py, itself already
            # fully Screener-primary) — every key with no Screener source is
            # left untouched, so the original yfinance value silently stays
            # the fallback. Since `metrics` is the same dict reference used
            # below (key_metrics_list, sector_score) and later this run
            # (peer_comparison, scoring), overriding it here means every
            # downstream consumer automatically sees the Screener-sourced
            # values with no other code changes. Re-persists `analysis.metrics`
            # immediately after so later stages that re-read it from the DB
            # (pl_intelligence_scoring etc., via `analysis.metrics or {}`)
            # don't see stale pre-override values. Never fails the pipeline —
            # same degrade-gracefully contract as every other calc module.
            try:
                from app.calculations.screener_metrics_override import apply_screener_primary_overrides
                apply_screener_primary_overrides(metrics, db, stock.id, sector_name=framework.sector_name)
                _update_analysis(db, analysis, metrics=metrics)
            except Exception as e:
                logger.warning("Screener-primary metrics override failed, keeping yfinance values",
                               stock_id=stock.id, error=str(e))

            sector_risks = framework.identify_risks(metrics, financial_data)

            # Build key_metrics array with availability and computed status
            key_metrics_list = []
            available_metric_names = []
            unavailable_metric_names = []
            for sm in framework.key_metrics_for(basic_industry):
                # For metrics not available from yfinance, try the generic
                # ledger bridge first (app/sectors/ledger_bridge.py), then
                # fall back to sector-specific compute. Real bug found
                # 2026-09-12: this call site builds the actually-displayed
                # key_metrics list and was calling _compute_special_metric
                # directly, bypassing extract_sector_metrics() (and the
                # ledger-bridge check added there) entirely — a
                # deal_wins_tcv value genuinely on file in the ledger
                # (HIGH confidence, $3.6bn, from Infosys's real earnings
                # call transcript) still showed as N/A until this was fixed.
                if sm.available_from_yfinance:
                    val = metrics.get(sm.name)
                    available = True
                else:
                    ledger_bridge = (financial_data or {}).get("_ledger_metrics", {})
                    if sm.name in ledger_bridge:
                        val = ledger_bridge[sm.name]
                    else:
                        val = framework._compute_special_metric(sm.name, metrics, financial_data)
                    available = val is not None

                if available and val is not None:
                    available_metric_names.append(sm.name)
                else:
                    unavailable_metric_names.append(sm.name)

                entry = {
                    "name": sm.name,
                    "label": sm.label,
                    "value": round(val, 2) if isinstance(val, float) else val,
                    "unit": sm.unit,
                    "importance": sm.importance,
                    "direction": sm.direction,
                    "weight": sm.weight,
                    "description": sm.description,
                    "available": sm.available_from_yfinance or val is not None,
                    "na_message": sm.na_message if (not sm.available_from_yfinance and val is None) else None,
                    "applicable_to": sm.applicable_to,
                    "score": framework.score_key_metric(sm.name, val if isinstance(val, (int, float)) else None),
                    "status": metric_status(val if isinstance(val, (int, float)) else None, sm),
                }
                key_metrics_list.append(entry)

            # Build red_flags array
            red_flags_list = []
            for rule in framework.red_flag_rules():
                try:
                    triggered = framework._check_rule(rule, metrics, financial_data)
                except Exception:
                    triggered = False
                red_flags_list.append({
                    "name": rule.title,
                    "triggered": triggered,
                    "severity": rule.severity,
                    "message": rule.description if triggered else None,
                })

            sector_score = framework.compute_sector_score(metrics, financial_data)

            sector_analysis = {
                "sector_name": framework.sector_name,
                "framework": framework.sector_name,
                "framework_class": type(framework).__name__,
                "description": f"{framework.sector_name} sector analysis framework",
                "sector_matched": sector_matched,
                "sector_score": sector_score,
                "key_metrics": key_metrics_list,
                "available_metric_names": available_metric_names,
                "unavailable_metric_names": unavailable_metric_names,
                "red_flags": red_flags_list,
                "sector_risks": sector_risks,
                "sector_weights": framework.SECTOR_WEIGHTS,
            }
            _update_analysis(db, analysis, sector_analysis=sector_analysis)
            _set_stage(db, analysis, "sector_analysis", "COMPLETED", 100,
                       f"Applied {framework.sector_name} framework ({len(available_metric_names)} of "
                       f"{len(key_metrics_list)} metrics available)")
        except Exception as e:
            sector_analysis = {}
            _set_stage(db, analysis, "sector_analysis", "FAILED", 0, error=str(e))

        # ── Stage 9: Peer Comparison ──────────────────────────────────────────
        _set_stage(db, analysis, "peer_comparison", "RUNNING", 10, "Finding sector peers")
        try:
            peers = _find_peers(db, stock_id, sector, metrics, framework)
            _update_analysis(db, analysis, peers=peers)
            _set_stage(db, analysis, "peer_comparison", "COMPLETED", 100,
                       f"Compared with {len(peers.get('peers', []))} peers")

            # Merge sector-average comparison into the Sector Key Metrics
            # panel, now that peer data exists — can't happen at Stage 8's
            # key_metrics_list build time, since peer_comparison runs one
            # stage AFTER sector_analysis. Only sets sector_median/
            # sector_percentile for metric names PEER_METRICS actually
            # covers (see its comment above); every other row is left
            # without a comparison rather than fabricating one.
            try:
                sector_medians = peers.get("sector_medians") or {}
                company_percentiles = peers.get("company_percentiles") or {}
                if sector_medians and sector_analysis.get("key_metrics"):
                    for entry in sector_analysis["key_metrics"]:
                        median = sector_medians.get(entry["name"])
                        if median is not None:
                            entry["sector_median"] = median
                            entry["sector_percentile"] = company_percentiles.get(entry["name"])
                    _update_analysis(db, analysis, sector_analysis=sector_analysis)
            except Exception as e:
                logger.warning("Sector-median merge into key_metrics failed", stock_id=stock.id, error=str(e))
        except Exception as e:
            peers = {}
            _set_stage(db, analysis, "peer_comparison", "FAILED", 0, error=str(e))

        # ── Stage 10: Risk Analysis ───────────────────────────────────────────
        _set_stage(db, analysis, "risk_analysis", "RUNNING", 10, "Identifying risk flags")
        try:
            risks = _identify_universal_risks(metrics, financial_data)
            risks.extend(sector_risks if sector_risks else [])
            catalysts = _identify_catalysts(metrics, financial_data)
            _update_analysis(db, analysis, risks=risks, catalysts=catalysts)
            _set_stage(db, analysis, "risk_analysis", "COMPLETED", 100,
                       f"Identified {len(risks)} risks, {len(catalysts)} catalysts")
        except Exception as e:
            risks, catalysts = [], []
            _set_stage(db, analysis, "risk_analysis", "FAILED", 0, error=str(e))

        # ── Stage 11: Scoring ─────────────────────────────────────────────────
        _set_stage(db, analysis, "scoring", "RUNNING", 10, "Computing fundamental scores")
        try:
            # Real bug found while validating Architecture v2 Stage 8 (NBFC
            # generalization): this was passing the raw DB `sector` string
            # ("Financial Services" for both banks and NBFCs) instead of the
            # resolved framework name, so compute_scores' SECTOR_WEIGHTS
            # lookup (scoring.py) always missed and silently fell back to
            # UNIVERSAL_WEIGHTS — for every financial-sector analysis this
            # entire session, not just NBFCs (confirmed on HDFC Bank's
            # existing FA-2026-000010: scores.weights showed generic
            # cash_flow=0.17/balance_sheet=0.17 instead of Banks' own
            # cash_flow=0.05/balance_sheet=0.25, producing false red flags
            # like "High Debt-to-Equity" for NBFCs where 3x leverage is
            # actually healthy per nbfc.py's own thresholds).
            #
            # Quarterly Growth Score (2026-09-27) — merged into `metrics`
            # BEFORE compute_scores() so `scoring.py::_growth_score()` can
            # blend it with the annual CAGR-based score; see
            # quarterly_growth.py's docstring for why a multi-year CAGR
            # alone can hide a real recent slowdown. None (too few quarters
            # on record) leaves `metrics` untouched — _growth_score() falls
            # back to the annual score alone, same degrade-gracefully
            # contract as every other best-effort block in this stage.
            try:
                from app.calculations.quarterly_growth import compute_quarterly_growth
                qg = compute_quarterly_growth(db, stock.id)
                if qg is not None:
                    metrics["quarterly_growth_score"] = qg["score"]
                    metrics["quarterly_growth_pct"] = qg["growth_pct"]
                    metrics["quarterly_growth_basis"] = qg["basis"]
            except Exception as e:
                logger.warning("Quarterly growth score failed, using annual growth only",
                               stock_id=stock.id, error=str(e))

            # Bank/NBFC cost-to-income ratio + NIM (2026-09-27) — merged into
            # `metrics` so `scoring.py::_bank_efficiency_score()`/
            # `_nbfc_efficiency_score()` can score them instead of returning
            # a constant 50 regardless of data. Sourced from
            # `inject_banking_bridge()` (called earlier this stage) rather
            # than re-querying the ledger — same authoritative-value
            # resolution, no second DB round trip. `.get()` leaves `metrics`
            # untouched when absent, same degrade-gracefully fallback to a
            # neutral 50 the scorer functions already have.
            if framework.sector_name in ("Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans"):
                bridge = (financial_data or {}).get("_banking_authoritative_metrics", {})
                for key in ("cost_to_income_ratio", "nim"):
                    val = bridge.get(key)
                    if val is not None:
                        metrics[key] = val

            scores = compute_scores(metrics, sector=framework.sector_name)
            data_quality = compute_data_quality(financial_data, metrics)
            sector_matched = sector_analysis.get("sector_matched", False) if sector_analysis else False
            scores["sector_matched"] = sector_matched  # update in place after sector is known
            confidence = compute_confidence(data_quality, metrics, sector_matched)
            _update_analysis(
                db, analysis,
                metrics=metrics,  # re-persist: _growth_score() just mutated it with growth_score_annual/quarterly
                scores=scores,
                overall_score=scores["overall"],
                confidence_score=confidence,
                data_quality_score=data_quality,
                ai_rating=scores["overall_rating"],
                valuation_rating=scores["valuation_view"],
            )
            _set_stage(db, analysis, "scoring", "COMPLETED", 100,
                       f"Overall score: {scores['overall']}/100")
        except Exception as e:
            scores = {}
            _set_stage(db, analysis, "scoring", "FAILED", 0, error=str(e))

        # ── Stage 12: AI Analysis ─────────────────────────────────────────────
        _set_stage(db, analysis, "ai_analysis", "RUNNING", 10, "Running GPT-OSS 20B analysis")
        _ai_start = _now()
        _ai_tokens: int | None = None
        _ai_model: str | None = None
        try:
            from app.config import config
            _ai_model = config.llm_model
            ai_result = _run_ai_analysis(company_info, metrics, scores, sector_analysis, peers, risks, catalysts)
            if ai_result:
                _ai_tokens = ai_result.pop("_token_count", None)
                _update_analysis(db, analysis, ai_analysis=ai_result,
                                 model_version=_ai_model, prompt_version="v1")
                _update_analysis(db, analysis, ai_rating=ai_result.get("rating", scores.get("overall_rating")))
            _set_stage(db, analysis, "ai_analysis", "COMPLETED", 100, "AI analysis complete")
            _log_agent_run(db, analysis_id, "ai_analysis", "gpt_analyst", "COMPLETED",
                           _ai_start,
                           duration_ms=int((_now() - _ai_start).total_seconds() * 1000),
                           token_count=_ai_tokens, model_used=_ai_model,
                           input_summary=f"{company_info.get('company_name')} | score={scores.get('overall')}")
        except Exception as e:
            logger.warning("AI analysis failed, continuing without it", error=str(e))
            _set_stage(db, analysis, "ai_analysis", "FAILED", 0,
                       message="AI analysis unavailable — deterministic analysis remains complete",
                       error=str(e))
            _log_agent_run(db, analysis_id, "ai_analysis", "gpt_analyst", "FAILED",
                           _ai_start, model_used=_ai_model, error=str(e))

        # ── Stage 12.5: Report Blueprint (local-Llama modular interpretation,
        # Architecture: Llama Report Interpretation, Stage L1) — additive,
        # never touches ai_analysis above. A failure here (Ollama down, weak
        # output) leaves report_blueprint empty; renderers fall back to
        # ai_analysis's narrative fields, so nothing regresses. ──────────────
        _set_stage(db, analysis, "report_blueprint", "RUNNING", 10, "Generating business interpretation (local Llama)")
        _blueprint_start = _now()
        try:
            from app.interpretation.master_object import build_master_company_object
            from app.interpretation.llama_interpreter import generate_report_blueprint
            master_object = build_master_company_object(db, analysis)
            blueprint = generate_report_blueprint(master_object)
            _update_analysis(db, analysis, report_blueprint=blueprint)
            _set_stage(db, analysis, "report_blueprint", "COMPLETED", 100,
                       f"Generated {len(blueprint.get('sections', []))} interpretation sections")
            _log_agent_run(db, analysis_id, "report_blueprint", "local_llama_interpreter", "COMPLETED",
                           _blueprint_start,
                           duration_ms=int((_now() - _blueprint_start).total_seconds() * 1000),
                           model_used="llama3.2:3b",
                           input_summary=f"{company_info.get('company_name')} | sections={len(blueprint.get('sections', []))}")
        except Exception as e:
            logger.warning("Report blueprint generation failed, continuing without it", error=str(e))
            _set_stage(db, analysis, "report_blueprint", "FAILED", 0,
                       message="Local Llama interpretation unavailable — existing AI analysis remains complete",
                       error=str(e))
            _log_agent_run(db, analysis_id, "report_blueprint", "local_llama_interpreter", "FAILED",
                           _blueprint_start, model_used="llama3.2:3b", error=str(e))

        # ── Stage 12.6: P&L Intelligence Persistence — P&L Analysis Engine
        # Milestone 5. `compute_pl_intelligence()` is cheap, pure in-memory
        # arithmetic over already-ingested ledger rows (no network calls,
        # unlike report_blueprint's LLM pass above) — recomputed fresh here
        # rather than threading the master_object.py call's result across
        # stages, matching this orchestrator's existing self-contained-stage
        # pattern. Persists to the pl_* tables (point-in-time
        # reproducibility for Stage 32's backtesting) AND dual-writes the
        # screenable subset into the metric ledger (Stage 27's screener
        # filters). Never fails the overall pipeline — same additive,
        # best-effort discipline as report_blueprint above; a company with
        # no pnl_* ledger data yet just persists an empty/null-scored row
        # rather than raising. ──────────────────────────────────────────────
        _set_stage(db, analysis, "pl_intelligence_scoring", "RUNNING", 10, "Computing P&L Intelligence score")
        pli_result = None
        try:
            from app.calculations.pl_intelligence import compute_pl_intelligence
            from app.calculations.pl_intelligence.persistence import save_pl_score, sync_to_metric_ledger
            pli_sector_name = sector_analysis.get("sector_name") if sector_analysis else None
            pli_result = compute_pl_intelligence(db, stock.id, sector_name=pli_sector_name)
            if pli_result.get("period"):
                save_pl_score(db, stock.id, pli_result["period"], pli_result)
                sync_to_metric_ledger(db, stock.id, pli_result["period"], pli_result)
                db.commit()
                _set_stage(db, analysis, "pl_intelligence_scoring", "COMPLETED", 100,
                           f"P&L score: {pli_result.get('score', {}).get('master_pl_score')}")
            else:
                _set_stage(db, analysis, "pl_intelligence_scoring", "COMPLETED", 100,
                           "No pnl_* ledger data available yet — skipped")
        except Exception as e:
            db.rollback()
            logger.warning("P&L Intelligence scoring failed, continuing without it", error=str(e))
            _set_stage(db, analysis, "pl_intelligence_scoring", "FAILED", 0,
                       message="P&L Intelligence unavailable — existing analysis remains complete",
                       error=str(e))

        # ── Stage 12.7: Balance Sheet Intelligence — Balance Sheet Analysis
        # Engine. Blends Screener.in (net worth/leverage/archetype/common-
        # size, already ingested) with the yfinance-sourced `analysis.metrics`
        # (working-capital ratios Screener's condensed balance sheet can't
        # separate out — same dict the PDF's Working-Capital chart already
        # reads). Computed fresh every run (no persisted score table — see
        # the package's own __init__.py docstring for why), dual-writes the
        # screenable subset into the metric ledger (screener filters). Never
        # fails the overall pipeline — same best-effort discipline as
        # pl_intelligence_scoring above. ────────────────────────────────────
        _set_stage(db, analysis, "balance_sheet_intelligence_scoring", "RUNNING", 10, "Computing Balance Sheet Intelligence")
        bsi_result = None
        try:
            from app.calculations.balance_sheet_intelligence import compute_balance_sheet_intelligence
            from app.calculations.balance_sheet_intelligence.persistence import sync_to_metric_ledger as sync_bsi_to_metric_ledger
            bsi_sector_name = sector_analysis.get("sector_name") if sector_analysis else None
            bsi_result = compute_balance_sheet_intelligence(
                db, stock.id, sector_name=bsi_sector_name, yfinance_metrics=analysis.metrics or {},
            )
            if bsi_result.get("period"):
                sync_bsi_to_metric_ledger(db, stock.id, bsi_result["period"], bsi_result)
                db.commit()
                _set_stage(db, analysis, "balance_sheet_intelligence_scoring", "COMPLETED", 100,
                           f"Archetype: {bsi_result.get('archetype', {}).get('classification')}")
            else:
                _set_stage(db, analysis, "balance_sheet_intelligence_scoring", "COMPLETED", 100,
                           "No Screener balance-sheet data available yet — skipped")
        except Exception as e:
            db.rollback()
            logger.warning("Balance Sheet Intelligence scoring failed, continuing without it", error=str(e))
            _set_stage(db, analysis, "balance_sheet_intelligence_scoring", "FAILED", 0,
                       message="Balance Sheet Intelligence unavailable — existing analysis remains complete",
                       error=str(e))

        # ── Stage 12.8: Cash Flow Intelligence — Cash Flow Analysis Engine.
        # Primary-sourced from Screener's undocumented "schedules" API
        # (ingested earlier this run via `ingest_cash_flow_schedules()`),
        # cross-checked against yfinance's `analysis.metrics` FCF/cash series.
        # Reuses `bsi_result`'s `working_capital` DSO/DIO/DPO series (just
        # computed above, same run) as a receivables/inventory-growth proxy
        # rather than recomputing — this package has no balance-level series
        # of its own. Same never-fail-the-pipeline discipline as the two
        # intelligence stages above. ─────────────────────────────────────────
        _set_stage(db, analysis, "cash_flow_intelligence_scoring", "RUNNING", 10, "Computing Cash Flow Intelligence")
        cfi_result = None
        try:
            from app.calculations.cash_flow_intelligence import compute_cash_flow_intelligence
            from app.calculations.cash_flow_intelligence.persistence import sync_to_metric_ledger as sync_cfi_to_metric_ledger
            cfi_sector_name = sector_analysis.get("sector_name") if sector_analysis else None
            cfi_result = compute_cash_flow_intelligence(
                db, stock.id, sector_name=cfi_sector_name, yfinance_metrics=analysis.metrics or {},
                balance_sheet_intelligence_result=bsi_result,
            )
            if cfi_result.get("period"):
                sync_cfi_to_metric_ledger(db, stock.id, cfi_result["period"], cfi_result)
                db.commit()
                _set_stage(db, analysis, "cash_flow_intelligence_scoring", "COMPLETED", 100,
                           f"Archetype: {cfi_result.get('archetype', {}).get('classification')}")
            else:
                _set_stage(db, analysis, "cash_flow_intelligence_scoring", "COMPLETED", 100,
                           "No Screener cash-flow schedule data available yet — skipped")
        except Exception as e:
            db.rollback()
            logger.warning("Cash Flow Intelligence scoring failed, continuing without it", error=str(e))
            _set_stage(db, analysis, "cash_flow_intelligence_scoring", "FAILED", 0,
                       message="Cash Flow Intelligence unavailable — existing analysis remains complete",
                       error=str(e))

        # ── Stage 12.85: Quarterly Analysis — Quarterly Report Extraction
        # Engine, Tier 1. Screener-primary, zero LLM cost — runs for every
        # company (not sector-gated), unlike the banking-only
        # screener_ingest_quarterly_metrics latest-quarter call earlier in
        # this pipeline. Reads the qtr_* ledger rows ingest_quarterly_results
        # already wrote this run (financial_data_collection stage, above),
        # computes QoQ/YoY growth + margin trend + "what changed" flags —
        # pure in-memory arithmetic, no network/LLM call. Never fails the
        # overall pipeline — same best-effort discipline as the three
        # intelligence-scoring stages above. ────────────────────────────────
        _set_stage(db, analysis, "quarterly_analysis", "RUNNING", 10, "Computing Quarterly Analysis")
        try:
            from app.calculations.quarterly_intelligence import compute_quarterly_intelligence
            from app.calculations.quarterly_intelligence.persistence import sync_to_metric_ledger as sync_qtr_to_metric_ledger
            qtr_result = compute_quarterly_intelligence(db, stock.id)
            if qtr_result.get("period"):
                sync_qtr_to_metric_ledger(db, stock.id, qtr_result["period"], qtr_result)
                db.commit()
                _set_stage(db, analysis, "quarterly_analysis", "COMPLETED", 100,
                           f"Latest quarter: {qtr_result.get('period')}, {len(qtr_result.get('flags', []))} flag(s)")
            else:
                _set_stage(db, analysis, "quarterly_analysis", "COMPLETED", 100,
                           "No Screener quarterly-results data available yet — skipped")
        except Exception as e:
            db.rollback()
            logger.warning("Quarterly Analysis failed, continuing without it", error=str(e))
            _set_stage(db, analysis, "quarterly_analysis", "FAILED", 0,
                       message="Quarterly Analysis unavailable — existing analysis remains complete",
                       error=str(e))

        # ── Stage 12.86: Quarterly Sector KPIs — Quarterly Sector KPI
        # Extraction Engine (2026-09-20). Sourced from NSE quarterly
        # Investor Presentation filings, NOT annual reports — a genuinely
        # different document type than every other annual-report-sourced
        # area in this pipeline. Only runs for sectors with a configured
        # area (Automobile, Cement, Metals/Mining, Forest Materials so far
        # — see app/ingestion/quarterly_operating_metrics_ingestion.py's
        # _SECTOR_CONFIG); a no-op, not a failure, for every other sector.
        # Cache-gated at a WEEKLY cadence (not daily like the pure-Screener
        # quarterly stage above) since this makes a real LLM call and a new
        # presentation only lands ~4x/year. Never fails the overall
        # pipeline — same best-effort discipline as every stage above. ────
        _set_stage(db, analysis, "quarterly_sector_kpis", "RUNNING", 10, "Checking for a quarterly Investor Presentation")
        qtr_sector_kpi_sector_name = sector_analysis.get("sector_name") if sector_analysis else None
        _qtr_sector_kpi_cache_key = f"quarterly_sector_kpis:{stock.id}"
        if not cache_get(_qtr_sector_kpi_cache_key):
            try:
                from app.ingestion.quarterly_operating_metrics_ingestion import ingest_quarterly_operating_metrics
                qtr_kpi_rows = []
                if qtr_sector_kpi_sector_name:
                    qtr_kpi_rows = ingest_quarterly_operating_metrics(
                        db, company_id=stock.id, symbol=symbol, sector_name=qtr_sector_kpi_sector_name)
                db.commit()
                if qtr_kpi_rows:
                    _set_stage(db, analysis, "quarterly_sector_kpis", "COMPLETED", 100,
                               f"Extracted {len(qtr_kpi_rows)} quarterly sector KPI value(s)")
                else:
                    _set_stage(db, analysis, "quarterly_sector_kpis", "COMPLETED", 100,
                               "No quarterly Investor Presentation data available for this sector/company")
            except Exception as e:
                db.rollback()
                logger.warning("Quarterly Sector KPIs failed, continuing without it", error=str(e))
                _set_stage(db, analysis, "quarterly_sector_kpis", "FAILED", 0,
                           message="Quarterly Sector KPIs unavailable — existing analysis remains complete",
                           error=str(e))
            # Short retry TTL, not the 7-day one, if the primary LLM was
            # rate-limited during this attempt — see _LLM_RATE_LIMITED_RETRY_TTL.
            _qtr_kpi_ttl = _LLM_RATE_LIMITED_RETRY_TTL if default_llm_client.last_used_fallback else _QUARTERLY_SECTOR_KPI_TTL
            cache_set(_qtr_sector_kpi_cache_key, "1", _qtr_kpi_ttl)
        else:
            _set_stage(db, analysis, "quarterly_sector_kpis", "COMPLETED", 100,
                       "Checked recently — skipped (weekly cache)")

        # ── Stage 12.9: Score Refinement — the explicit "add the new
        # engines' metrics to the overall score" deliverable. Final stage:
        # re-reads `analysis.scores` (just persisted by the "scoring" stage
        # above) plus the three intelligence engines' already-computed
        # results (`pli_result`/`bsi_result`/`cfi_result`, all from this
        # same run) and blends them into the `profitability`/
        # `balance_sheet`/`cash_flow` category scores, then recomputes
        # `overall` via `scoring.recompute_overall()` using the SAME weight
        # dict `compute_scores()` already chose. Every blend is bounded
        # (+/-10 pts per category, see `score_refinement.py`'s own
        # docstring) and recorded in `scores["refinement"]` for
        # traceability. Also applies a bounded promoter-governance penalty
        # (2026-09-28, see `governance_scoring.py`) directly on `overall`,
        # from the `governance_events` the "shareholding" ingestion earlier
        # in this same run already detected (pledge/promoter-holding-
        # decline) — never re-derived here, just read and scored. Skips
        # cleanly if the "scoring" stage itself failed upstream (no
        # `analysis.scores` to refine) — never fails the overall
        # pipeline. ──────────────────────────────────────────────────
        _set_stage(db, analysis, "score_refinement", "RUNNING", 10, "Refining overall score with intelligence-engine signals")
        try:
            from app.calculations.governance_scoring import compute_governance_penalty
            from app.calculations.score_refinement import apply_score_refinement
            if analysis.scores:
                governance_result = compute_governance_penalty(db, stock.id)
                refined_scores = apply_score_refinement(analysis.scores, pli_result, bsi_result, cfi_result,
                                                          governance_result)
                _update_analysis(db, analysis, scores=refined_scores, overall_score=refined_scores["overall"],
                                  ai_rating=refined_scores.get("overall_rating"))
                pre = refined_scores.get("refinement", {}).get("pre_refinement_overall")
                _set_stage(db, analysis, "score_refinement", "COMPLETED", 100,
                           f"Overall score: {pre} -> {refined_scores['overall']}")
            else:
                _set_stage(db, analysis, "score_refinement", "COMPLETED", 100,
                           "No base scores available to refine — skipped")
        except Exception as e:
            db.rollback()
            logger.warning("Score refinement failed, continuing without it", error=str(e))
            _set_stage(db, analysis, "score_refinement", "FAILED", 0,
                       message="Score refinement unavailable — base scores remain in place",
                       error=str(e))

        # ── Persist the final scores to the screenable per-company table
        # (fa_company_scores) — after refinement so the stored numbers are
        # the exact ones shown on the report. Never fails the pipeline. ────
        try:
            from app.services.company_scores import upsert_company_score
            upsert_company_score(db, analysis)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning("Company score snapshot failed, continuing without it", error=str(e))

        # ── Stock Quality framework scores (app/framework/) from this
        # analysis's final scores and metrics. Never fails the pipeline. ──────
        try:
            from app.framework import engine as framework, store as framework_store
            from app.sectors.registry import get_framework as _fw_sector
            _fw_name = _fw_sector(stock.sector or "", industry=stock.industry or "",
                                  basic_industry=stock.basic_industry or "").sector_name
            framework.score_company(db, stock.id, framework_store.FULL, analysis.scores or {},
                                    analysis.metrics or {}, analysis.financial_data or {}, _fw_name)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning("Framework scores failed, continuing without them", error=str(e))

        # ── Stage 13: Report Generation ───────────────────────────────────────
        # A headless-Chromium snapshot of the Editorial Report tab itself
        # (2026-09-21, replacing the Node/PDFKit "equity-pdf-renderer" path
        # here too — see app/reporting/editorial_pdf_service.py's module
        # docstring for why, and app/routes/fundamental.py's on-demand
        # generate-report endpoint, which was switched to the same
        # renderer). Both call sites must stay in sync: this one is what
        # actually runs for every new analysis (the API endpoint's own call
        # only fires if report_path is still unset, which after this stage
        # it never is).
        _set_stage(db, analysis, "report_generation", "RUNNING", 10, "Generating PDF report")
        try:
            from app.reporting.editorial_pdf_service import generate_editorial_pdf
            report_path = generate_editorial_pdf(analysis_id, db)
            _update_analysis(db, analysis, report_path=report_path)
            _set_stage(db, analysis, "report_generation", "COMPLETED", 100, "PDF report ready")
        except Exception as e:
            logger.warning("PDF generation failed", error=str(e))
            _set_stage(db, analysis, "report_generation", "FAILED", 0, error=str(e))

        # ── Mark complete ─────────────────────────────────────────────────────
        _update_analysis(db, analysis,
                         status="COMPLETED",
                         overall_progress=100,
                         completed_at=_now())
        logger.info("Analysis completed", analysis_id=analysis_id,
                    score=analysis.overall_score)

    except Exception as e:
        logger.error("Analysis pipeline failed", analysis_id=analysis_id, error=str(e),
                     trace=traceback.format_exc())
        try:
            analysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
            if analysis:
                _update_analysis(db, analysis, status="FAILED",
                                 error_message=str(e), completed_at=_now())
        except Exception:
            pass
    finally:
        db.close()


# ── Helper functions ──────────────────────────────────────────────────────────

def _validate_metrics(metrics: dict, financial_data: dict) -> dict:
    """Basic metric validation — flags obviously wrong values."""
    validations = {}
    checks = {
        "ebitda_margin": lambda v: 0 <= v <= 100,
        "pat_margin": lambda v: -50 <= v <= 100,
        "roe": lambda v: -200 <= v <= 200,
        "roce": lambda v: -100 <= v <= 200,
        "debt_to_equity": lambda v: 0 <= v <= 20,
        "current_ratio": lambda v: 0 <= v <= 20,
        "interest_coverage": lambda v: -10 <= v <= 100,
    }
    for key, check in checks.items():
        val = metrics.get(key)
        if val is None:
            validations[key] = {"status": "NOT_APPLICABLE", "value": None}
        elif check(val):
            validations[key] = {"status": "VALID", "value": val, "confidence": 0.9}
        else:
            validations[key] = {"status": "WARNING", "value": val, "message": "Value outside normal range"}
    return validations


def _find_peers(db, stock_id: str, sector: str, metrics: dict, framework=None) -> dict:
    """
    Find sector peers and fetch their key financial metrics via yfinance.
    Computes sector median and percentile ranking for the subject company.
    Fetches up to 6 peers; skips any peer whose yfinance fetch fails (graceful degradation).

    Also pulls each peer's SECTOR-SPECIFIC key metrics (the same
    non-yfinance fields the Sector tab shows for the subject — e.g.
    hospitals' bed_occupancy_pct/arpob/alos_days/arpp, hotels'
    occupancy_rate/arr/revpar, telecom's arpu/churn_pct — see each
    `app/sectors/*.py`'s `key_metrics()`), using the SUBJECT's own resolved
    `framework` so every peer's column lines up on the same metric
    definitions even if a peer's own sector string would resolve slightly
    differently. Reads only whatever a peer already has on file in
    `metric_store` via the generic ledger bridge (`ledger_bridge.py`) —
    never triggers new extraction for a peer that hasn't itself been
    through this platform's pipeline, so an unanalyzed peer legitimately
    shows N/A here rather than a fabricated value.
    """
    from app.infrastructure.database.models import Stock
    from app.pipeline.peer_selection import select_peer_candidates
    from app.sectors.ledger_bridge import inject_ledger_bridge

    # Widened 2026-09-16 (cfo_to_pat/current_ratio/interest_coverage/
    # ebit_margin/pat_cagr_3y added) so the Sector Key Metrics panel's new
    # "vs sector average" column (see the merge step after this stage
    # completes, in the peer_comparison block below) covers every key
    # GenericSector.key_metrics() declares, not just the original subset —
    # still a fixed list, not every SectorFramework's full metric set (e.g.
    # ledger-bridge-only metrics like attrition_rate have no peer data;
    # that's a real gap, not a bug, since computing those for every peer
    # would mean re-running ledger-bridge extraction per peer).
    PEER_METRICS = [
        "revenue_cagr_3y", "pat_cagr_3y", "ebitda_margin", "ebit_margin", "pat_margin",
        "roce", "roe", "roa", "debt_to_equity",
        "net_debt_to_ebitda", "fcf_to_pat", "cfo_to_pat", "current_ratio",
        "interest_coverage", "pe_ratio", "pb_ratio", "ev_to_ebitda", "peg_ratio",
    ]

    # ── 1. Select candidate peers ─────────────────────────────────────────────
    # Prefer same industry (more specific), fall back to sector-wide — the
    # actual selection logic lives in peer_selection.py now (extracted so
    # the P&L Analysis Engine's peer-percentile work can reuse the exact
    # same algorithm instead of a second, potentially-drifting copy).
    subject = db.query(Stock).filter(Stock.id == stock_id).first()
    subject_industry = subject.industry if subject else None
    subject_basic_industry = subject.basic_industry if subject else None
    candidates = select_peer_candidates(db, stock_id, sector)

    # Sector-specific (non-yfinance) metric ids for the subject's own
    # resolved framework — e.g. hospitals' bed_occupancy_pct/arpob/
    # alos_days/arpp (see pharma.py). Every peer is read against these SAME
    # ids/framework so the comparison table's columns line up, even if a
    # peer's own sector string would independently resolve slightly
    # differently. Filtered by the SUBJECT's own basic_industry
    # (key_metrics_for) so a hospital's peer table doesn't carry pharma-only
    # columns (R&D/revenue, ANDA pipeline, ...) or vice versa.
    sector_metric_ids = [m.name for m in framework.key_metrics_for(subject_basic_industry) if not m.available_from_yfinance] if framework else []

    # ── 2. Fetch metrics for each peer ───────────────────────────────────────
    peers_with_metrics: list[dict] = []
    for p in candidates:
        try:
            fin_data = fetch_financial_data(p.exchange, p.symbol)
            peer_m = compute_metrics(fin_data)
            peer_sector_metrics: dict[str, float | None] = {k: None for k in sector_metric_ids}
            if sector_metric_ids and framework:
                try:
                    ledger_stub = inject_ledger_bridge({}, db, p.id, sector_metric_ids)
                    extracted = framework.extract_sector_metrics(peer_m, ledger_stub)
                    peer_sector_metrics = {k: extracted.get(k) for k in sector_metric_ids}
                except Exception as exc:
                    logger.warning("Peer sector-metric extraction failed for %s: %s", p.id, exc)
            peers_with_metrics.append({
                "stock_id": p.id,
                "company_name": p.company_name,
                "symbol": p.symbol,
                "exchange": p.exchange,
                "market_cap": float(p.market_cap) if p.market_cap else None,
                **{k: peer_m.get(k) for k in PEER_METRICS},
                "sector_metrics": peer_sector_metrics,
            })
        except Exception as exc:
            logger.warning("Peer fetch failed for %s: %s", p.id, exc)
            peers_with_metrics.append({
                "stock_id": p.id,
                "company_name": p.company_name,
                "symbol": p.symbol,
                "exchange": p.exchange,
                "market_cap": float(p.market_cap) if p.market_cap else None,
                **{k: None for k in PEER_METRICS},
                "sector_metrics": {k: None for k in sector_metric_ids},
            })

    # ── 3. Compute sector median + percentile for subject ─────────────────────
    import statistics

    def _peer_values(key: str, sector_specific: bool = False) -> list[float]:
        if sector_specific:
            return [p["sector_metrics"].get(key) for p in peers_with_metrics if p["sector_metrics"].get(key) is not None]
        return [p[key] for p in peers_with_metrics if p.get(key) is not None]

    def _percentile(subject_val: float | None, peer_vals: list[float],
                    higher_is_better: bool = True) -> int | None:
        if subject_val is None or not peer_vals:
            return None
        all_vals = sorted(peer_vals + [subject_val])
        rank = all_vals.index(subject_val) + 1
        pct = round((rank / len(all_vals)) * 100)
        return pct if higher_is_better else (100 - pct)

    # Metrics where lower = better (for percentile direction). The generic
    # set is hardcoded (always the same two); sector-specific metrics derive
    # this from each SectorMetric's own declared `direction` instead of a
    # second hand-maintained list — e.g. hospitals' `fda_483_count` is
    # lower_is_better, `alos_days` is neutral (treated as higher_is_better
    # for ranking purposes, same as every other "neutral" metric here).
    LOWER_IS_BETTER = {"debt_to_equity", "net_debt_to_ebitda"}
    if framework:
        LOWER_IS_BETTER |= {m.name for m in framework.key_metrics() if m.direction == "lower_is_better"}

    sector_medians: dict[str, float | None] = {}
    company_percentiles: dict[str, int | None] = {}
    for key in PEER_METRICS:
        peer_vals = _peer_values(key)
        sector_medians[key] = round(statistics.median(peer_vals), 2) if peer_vals else None
        company_percentiles[key] = _percentile(
            metrics.get(key), peer_vals,
            higher_is_better=(key not in LOWER_IS_BETTER),
        )

    # Subject's own sector-specific values, computed via the identical
    # ledger-first path used for every peer above — so the percentile rank
    # compares like with like. (The Sector tab's own display may show a
    # richer value for some metrics via a sector's `_compute_special_metric`
    # fallback that needs the full `financial_data` dict this function
    # doesn't have — that's fine for that tab; here, subject and peers must
    # share one computation path or the ranking wouldn't be apples-to-apples.)
    company_sector_metrics: dict[str, float | None] = {k: None for k in sector_metric_ids}
    if sector_metric_ids and framework:
        try:
            ledger_stub = inject_ledger_bridge({}, db, stock_id, sector_metric_ids)
            extracted = framework.extract_sector_metrics(metrics, ledger_stub)
            company_sector_metrics = {k: extracted.get(k) for k in sector_metric_ids}
        except Exception as exc:
            logger.warning("Subject sector-metric extraction failed for %s: %s", stock_id, exc)

    for key in sector_metric_ids:
        peer_vals = _peer_values(key, sector_specific=True)
        sector_medians[key] = round(statistics.median(peer_vals), 2) if peer_vals else None
        company_percentiles[key] = _percentile(
            company_sector_metrics.get(key), peer_vals,
            higher_is_better=(key not in LOWER_IS_BETTER),
        )

    return {
        "sector": sector,
        "industry": subject_industry,
        "peer_count": len(peers_with_metrics),
        "peers": peers_with_metrics,
        "company_metrics": {**{k: metrics.get(k) for k in PEER_METRICS}, **company_sector_metrics},
        "sector_medians": sector_medians,
        "company_percentiles": company_percentiles,
        "sector_metric_ids": sector_metric_ids,
    }


def _identify_universal_risks(metrics: dict, financial_data: dict) -> list[dict]:
    """Identify universal financial risk flags from calculated metrics."""
    risks = []

    # High leverage
    de = metrics.get("debt_to_equity")
    if de is not None and de > 2.0:
        risks.append({
            "severity": "HIGH",
            "category": "BALANCE_SHEET",
            "title": "High Debt-to-Equity",
            "description": f"D/E ratio of {de:.2f}x is elevated and increases financial risk.",
            "evidence": {"debt_to_equity": de, "threshold": 2.0},
            "confidence": 0.9,
        })

    # Weak interest coverage
    ic = metrics.get("interest_coverage")
    if ic is not None and ic < 2.0:
        risks.append({
            "severity": "HIGH" if ic < 1.0 else "MEDIUM",
            "category": "BALANCE_SHEET",
            "title": "Weak Interest Coverage",
            "description": f"Interest coverage of {ic:.1f}x is concerning — earnings barely cover interest.",
            "evidence": {"interest_coverage": ic},
            "confidence": 0.88,
        })

    # Negative/very low ROCE
    roce = metrics.get("roce")
    if roce is not None and roce < 8:
        risks.append({
            "severity": "MEDIUM",
            "category": "PROFITABILITY",
            "title": "Low Capital Returns (ROCE)",
            "description": f"ROCE of {roce:.1f}% is below cost of capital estimates.",
            "evidence": {"roce": roce},
            "confidence": 0.85,
        })

    # Deteriorating ROCE trend
    roce_trend = metrics.get("roce_trend")
    _roce_vals = [v for v in (metrics.get("roce_series") or {}).values() if v is not None][-3:]
    _roce_falling_streak = len(_roce_vals) == 3 and _roce_vals[0] > _roce_vals[1] > _roce_vals[2]
    if roce_trend in ("STRONGLY_DETERIORATING", "DETERIORATING") and _roce_falling_streak:
        risks.append({
            "severity": "MEDIUM",
            "category": "PROFITABILITY",
            "title": "Declining ROCE Trend",
            "description": "ROCE has been consistently declining, suggesting deteriorating capital efficiency.",
            "evidence": {"roce_trend": roce_trend, "roce_series": metrics.get("roce_series")},
            "confidence": 0.8,
        })

    # Negative FCF
    fcf = metrics.get("fcf_latest")
    if fcf is not None and fcf < 0:
        risks.append({
            "severity": "MEDIUM",
            "category": "CASH_FLOW",
            "title": "Negative Free Cash Flow",
            "description": "Negative FCF means the company is consuming cash — watch capex cycle.",
            "evidence": {"fcf_latest": fcf},
            "confidence": 0.85,
        })

    # Poor cash conversion
    fcf_pat = metrics.get("fcf_to_pat")
    if fcf_pat is not None and fcf_pat < 30:
        risks.append({
            "severity": "LOW",
            "category": "CASH_FLOW",
            "title": "Low Cash Conversion",
            "description": f"FCF/PAT of {fcf_pat:.0f}% suggests accounting profits are not converting to cash.",
            "evidence": {"fcf_to_pat": fcf_pat},
            "confidence": 0.78,
        })

    # High valuation
    pe = metrics.get("pe_ratio")
    if pe is not None and pe > 50:
        risks.append({
            "severity": "MEDIUM",
            "category": "VALUATION",
            "title": "Very High Valuation",
            "description": f"P/E of {pe:.1f}x prices in significant growth — disappointing earnings could cause sharp correction.",
            "evidence": {"pe_ratio": pe},
            "confidence": 0.82,
        })

    return risks


def _identify_catalysts(metrics: dict, financial_data: dict) -> list[dict]:
    """Identify positive catalysts."""
    catalysts = []

    # Improving ROCE
    roce_trend = metrics.get("roce_trend")
    if roce_trend in ("IMPROVING", "STRONGLY_IMPROVING"):
        catalysts.append({
            "type": "COMPANY_SPECIFIC",
            "title": "Improving Capital Efficiency",
            "description": "ROCE trend is improving — suggests better capital allocation or operating leverage.",
            "confidence": 0.82,
        })

    # Strong FCF
    fcf_pat = metrics.get("fcf_to_pat")
    if fcf_pat and fcf_pat > 80:
        catalysts.append({
            "type": "STRUCTURAL",
            "title": "Strong Cash Generation",
            "description": f"FCF/PAT of {fcf_pat:.0f}% enables dividends, buybacks, or debt reduction.",
            "confidence": 0.85,
        })

    # Strong growth
    rev_cagr = metrics.get("revenue_cagr_3y")
    if rev_cagr and rev_cagr > 15:
        catalysts.append({
            "type": "GROWTH",
            "title": "Strong Revenue Growth Momentum",
            "description": f"Revenue CAGR of {rev_cagr:.1f}% over 3 years demonstrates sustained demand.",
            "confidence": 0.88,
        })

    # Debt reduction
    de_trend = metrics.get("debt_trend")
    if de_trend in ("IMPROVING", "STRONGLY_IMPROVING"):
        catalysts.append({
            "type": "BALANCE_SHEET",
            "title": "Deleveraging",
            "description": "Debt-to-equity ratio has been declining — improving balance sheet strength.",
            "confidence": 0.80,
        })

    # Margin expansion
    ebitda_trend = metrics.get("ebitda_margin_trend")
    if ebitda_trend in ("IMPROVING", "STRONGLY_IMPROVING"):
        catalysts.append({
            "type": "PROFITABILITY",
            "title": "Margin Expansion",
            "description": "EBITDA margins are on an improving trajectory — operating leverage at play.",
            "confidence": 0.82,
        })

    return catalysts


def _run_ai_analysis(company_info: dict, metrics: dict, scores: dict,
                     sector_analysis: dict, peers: dict, risks: list, catalysts: list) -> dict:
    """Call GPT-OSS 20B for structured investment analysis."""
    from app.llm.client import llm_client

    # Build sector-aware metrics context for the LLM
    framework_name = sector_analysis.get("framework_class", "GenericSector") if sector_analysis else "GenericSector"
    sector_name = sector_analysis.get("sector_name", "Generic") if sector_analysis else "Generic"
    unavailable_metrics = sector_analysis.get("unavailable_metric_names", []) if sector_analysis else []
    available_metrics = sector_analysis.get("available_metric_names", []) if sector_analysis else []

    is_financial = sector_name in {"Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans", "Insurance"}
    is_bank = sector_name == "Banks"

    # Build metric summary appropriate to the sector
    if is_bank:
        # Pull from sector_analysis["key_metrics"] rather than the generic yfinance
        # `metrics` dict — this is where the ingested banking-specific figures
        # (NIM/GNPA/NNPA/CASA/credit_cost/CAR/cost_to_income/PCR/slippage) actually
        # live, per app/sectors/banking_data_bridge.py. Falling back to `metrics`
        # here would silently drop every one of them from the LLM's context.
        key_metrics_summary = {
            entry["name"]: entry["value"]
            for entry in (sector_analysis.get("key_metrics") or [])
            if entry.get("available") and entry.get("value") is not None
        }
    elif is_financial:
        key_metrics_summary = {
            "revenue_cagr_3y": metrics.get("revenue_cagr_3y"),
            "pat_cagr_3y": metrics.get("pat_cagr_3y"),
            "roe": metrics.get("roe"),
            "roa": metrics.get("roa"),
            "pat_margin": metrics.get("pat_margin"),
            "debt_to_equity": metrics.get("debt_to_equity"),
            "interest_coverage": metrics.get("interest_coverage"),
            "pe_ratio": metrics.get("pe_ratio"),
            "pb_ratio": metrics.get("pb_ratio"),
        }
    else:
        key_metrics_summary = {
            "revenue_cagr_3y": metrics.get("revenue_cagr_3y"),
            "ebitda_margin": metrics.get("ebitda_margin"),
            "pat_margin": metrics.get("pat_margin"),
            "roce": metrics.get("roce"),
            "roe": metrics.get("roe"),
            "fcf_to_pat": metrics.get("fcf_to_pat"),
            "debt_to_equity": metrics.get("debt_to_equity"),
            "pe_ratio": metrics.get("pe_ratio"),
            "ev_to_ebitda": metrics.get("ev_to_ebitda"),
            "pb_ratio": metrics.get("pb_ratio"),
            "interest_coverage": metrics.get("interest_coverage"),
        }

    # Remove N/A metrics from LLM context to avoid hallucination
    key_metrics_summary = {k: v for k, v in key_metrics_summary.items() if v is not None}

    context = {
        "company": {
            "name": company_info.get("company_name"),
            "sector": company_info.get("sector"),
            "industry": company_info.get("industry"),
        },
        "sector_framework": sector_name,
        "framework_class": framework_name,
        "is_financial_sector": is_financial,
        "scores": scores,
        "key_metrics": key_metrics_summary,
        "unavailable_metrics": unavailable_metrics[:10],  # context cap
        "trends": {
            "roce_trend": metrics.get("roce_trend"),
            "ebitda_margin_trend": metrics.get("ebitda_margin_trend"),
            "pat_margin_trend": metrics.get("pat_margin_trend"),
            "debt_trend": metrics.get("debt_trend"),
            "fcf_trend": metrics.get("fcf_trend"),
        },
        "risks_count": len(risks),
        "high_risks": [r for r in risks if r.get("severity") == "HIGH"],
        "catalysts": catalysts,
        "years_of_data": metrics.get("data_years", 0),
    }

    import json

    # Sector-specific instructions for the LLM
    sector_instruction = ""
    if is_bank:
        framework_doc = load_framework_doc("Banks")
        # Framework doc runs ~20K chars; a full paste would dominate context and cost.
        # Sections 1-19 (scope, philosophy, metrics, red flags, scoring) are what an
        # interpretation pass actually needs — 20+ (data hierarchy/provenance/output
        # structure) govern the ingestion pipeline itself, not this prompt.
        framework_excerpt = framework_doc[:9000] if framework_doc else ""
        sector_instruction = f"""
IMPORTANT — This is a Bank (framework: {framework_name}). The canonical banking
analysis framework this company must be evaluated against follows. Its metric
definitions, interpretation rules, and red-flag conditions take precedence over
generic financial-sector heuristics:

{framework_excerpt}

FINANCIAL SECTOR RULES:
- Do NOT use EBITDA margin, asset turnover, inventory days, or FCF/PAT as primary metrics.
- Leverage (D/E) for banks is naturally higher than industrial companies — do not flag it as a red flag unless it exceeds bank-specific thresholds.
- Each metric in key_metrics below may carry differing reliability: some are directly reported by the bank/exchange, others are calculated or estimated from a single quarter's filing. Treat estimated figures (e.g. credit_cost, cost_to_income_ratio) with appropriate hedging rather than as certain.
- Some metrics marked in unavailable_metrics are not sourced yet (e.g. CASA, PCR, slippage ratio require investor-presentation data not yet ingested) — acknowledge gaps where relevant; do not invent values.
"""
    elif is_financial:
        sector_instruction = f"""
IMPORTANT — This is a {sector_name} company (framework: {framework_name}).
FINANCIAL SECTOR RULES:
- Do NOT use EBITDA margin, asset turnover, inventory days, or FCF/PAT as primary metrics — these do NOT apply to {sector_name}.
- For NBFCs: focus on ROE, ROA, AUM growth, NIM, credit cost, collection efficiency, leverage, capital adequacy. Do NOT mention CASA or deposit growth.
- For Insurance: focus on combined ratio, loss ratio, solvency, VNB margin, premium growth, persistency.
- Leverage (D/E) for {sector_name} is naturally higher than industrial companies — do not flag it as a red flag unless it exceeds sector-specific thresholds.
- Some metrics marked in unavailable_metrics are not in yfinance — acknowledge gaps where relevant; do not invent values.
"""

    system_prompt = f"""You are a professional equity research analyst specializing in Indian stock markets.
You ONLY interpret pre-calculated quantitative data — you never invent financial values.
All numbers provided are deterministic Python calculations, not your estimates.
{sector_instruction}
Respond ONLY with valid JSON matching the exact schema requested."""

    user_prompt = f"""Analyze this stock based on the following pre-calculated quantitative data:

{json.dumps(context, indent=2)}

Respond with a JSON object in this EXACT schema (all text fields in 1-3 sentences max):
{{
  "rating": "STRONG|GOOD|FAIR|WEAK|POOR",
  "conviction": "HIGH|MEDIUM|LOW",
  "confidence": 0.0-1.0,
  "business_quality": 0-100,
  "growth_quality": 0-100,
  "financial_quality": 0-100,
  "valuation_view": "CHEAP|ATTRACTIVE|FAIR|EXPENSIVE|VERY_EXPENSIVE",
  "executive_summary": "1-2 sentence overall assessment of the investment opportunity",
  "business_quality_assessment": "1-2 sentences on business model quality, moat, and competitive position",
  "financial_health_summary": "1-2 sentences on balance sheet strength, leverage, and cash generation",
  "growth_outlook": "1-2 sentences on growth trajectory and sustainability based on the data",
  "valuation_commentary": "1-2 sentences on current valuation vs what the data suggests is fair",
  "investment_thesis": ["key thesis point 1", "key thesis point 2", "key thesis point 3"],
  "bull_case": ["bull point 1", "bull point 2", "bull point 3"],
  "bear_case": ["bear point 1", "bear point 2", "bear point 3"],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "key_catalysts": ["catalyst 1", "catalyst 2"],
  "monitoring_points": ["metric 1 to watch", "metric 2 to watch", "metric 3 to watch"]
}}

Base your analysis ONLY on the quantitative data provided. Do not invent company facts.
If data is insufficient for a conclusion, say so explicitly in the relevant fields."""

    result = llm_client.chat_json(system_prompt, user_prompt)

    # Attach token count for audit logging (orchestrator pops this before saving)
    result["_token_count"] = getattr(llm_client, "last_token_count", None)

    # Ensure required fields exist
    defaults = {
        "rating": scores.get("overall_rating", "FAIR"),
        "conviction": "MEDIUM",
        "confidence": 0.7,
        "business_quality": 70,
        "growth_quality": 70,
        "financial_quality": 70,
        "valuation_view": scores.get("valuation_view", "FAIR"),
        "executive_summary": None,
        "business_quality_assessment": None,
        "financial_health_summary": None,
        "growth_outlook": None,
        "valuation_commentary": None,
        "investment_thesis": [],
        "bull_case": [],
        "bear_case": [],
        "key_risks": [],
        "key_catalysts": [],
        "monitoring_points": [],
    }
    for k, v in defaults.items():
        if k not in result:
            result[k] = v

    return result
