from datetime import date, datetime
from sqlalchemy import (
    Date,
    String, Boolean, Integer, BigInteger, Numeric, Text,
    DateTime, JSON, ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


# Read-only mirror of existing stocks table (no new columns added)
class Stock(Base):
    __tablename__ = "stocks"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    exchange: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    isin: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    basic_industry: Mapped[str | None] = mapped_column(String, nullable=True)
    macro_sector: Mapped[str | None] = mapped_column(String, nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    market_cap_category: Mapped[str | None] = mapped_column(String, nullable=True)
    market_cap_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FundamentalAnalysis(Base):
    __tablename__ = "fa_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True)                 # FA-2026-000001
    stock_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="QUEUED")
    # QUEUED | RUNNING | COMPLETED | FAILED | CANCELLED
    current_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    stage_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Summary scores
    overall_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    data_quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    ai_rating: Mapped[str | None] = mapped_column(String, nullable=True)
    valuation_rating: Mapped[str | None] = mapped_column(String, nullable=True)

    # All analysis data stored as JSON
    company_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    financial_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)    # raw yfinance
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)           # calculated metrics
    metric_validations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)            # component scores
    sector_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    peers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    catalysts: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)      # LLM output
    report_blueprint: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # local-Llama modular narrative (Stage L1)
    report_path: Mapped[str | None] = mapped_column(String, nullable=True)

    model_version: Mapped[str | None] = mapped_column(String, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("fa_analyses_stock_idx", "stock_id"),
        Index("fa_analyses_status_idx", "status"),
        Index("fa_analyses_created_idx", "created_at"),
        Index("fa_analyses_stock_created_idx", "stock_id", "created_at"),
    )


class AgentRun(Base):
    __tablename__ = "fa_agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        String, ForeignKey("fa_analyses.id", ondelete="CASCADE"), nullable=False
    )
    stage_name: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="RUNNING")
    # RUNNING | COMPLETED | FAILED | SKIPPED
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("fa_agent_runs_analysis_idx", "analysis_id"),
        Index("fa_agent_runs_stage_idx", "analysis_id", "stage_name"),
    )


class BulkMetrics(Base):
    """Whole-universe cache of compute_metrics() output — Architecture v2
    Stage 2. One row per stock, refreshed by app/screening/bulk_metrics.py's
    bounded batch job. Deliberately separate from FundamentalAnalysis.metrics
    (same shape, but that only exists for the ~15 stocks that have gone
    through a full 13-stage analysis) — this table exists so the declarative
    screening engine has real breadth to run rules against."""

    __tablename__ = "fa_bulk_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    stock_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("fa_bulk_metrics_stock_idx", "stock_id"),
    )


class CompanyScore(Base):
    """Latest score snapshot per company — one row per stock, upserted after
    every completed analysis (app/services/company_scores.py). Exists because
    the six category scores + overall otherwise live only inside each
    analysis's `scores` JSON, and a full analysis takes minutes per stock —
    this table makes the whole analysed universe filterable/sortable by any
    one score or a combination in a single indexed query. `scored_at` is the
    date the scores were computed; `latest_quarter_end` is the newest
    quarterly result in the ledger at that time, so a stale row (company has
    reported a newer quarter since) is detectable. Fundamentals only move
    when a quarter is reported, so re-analysing simply overwrites the row
    with fresher numbers and a new date."""

    __tablename__ = "fa_company_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    stock_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    analysis_id: Mapped[str | None] = mapped_column(String, nullable=True)
    overall: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    growth: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    profitability: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    cash_flow: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    balance_sheet: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    efficiency: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    valuation: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    overall_rating: Mapped[str | None] = mapped_column(String, nullable=True)
    valuation_view: Mapped[str | None] = mapped_column(String, nullable=True)
    weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    red_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latest_quarter_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("fa_company_scores_overall_idx", "overall"),
        Index("fa_company_scores_growth_idx", "growth"),
        Index("fa_company_scores_profitability_idx", "profitability"),
        Index("fa_company_scores_cash_flow_idx", "cash_flow"),
        Index("fa_company_scores_balance_sheet_idx", "balance_sheet"),
        Index("fa_company_scores_efficiency_idx", "efficiency"),
        Index("fa_company_scores_valuation_idx", "valuation"),
    )


class StockBusinessProfile(Base):
    """Yahoo business description + industry per stock — used only by peer
    selection (app/pipeline/peer_selection.py) to find same-business peers."""
    __tablename__ = "fa_stock_business_profile"

    stock_id: Mapped[str] = mapped_column(String, ForeignKey("stocks.id", ondelete="CASCADE"), primary_key=True)
    yahoo_industry: Mapped[str | None] = mapped_column(String, nullable=True)
    yahoo_sector: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuickScore(Base):
    """Yahoo-only quick-analysis scores (app/quick_analysis/) — deliberately a
    SEPARATE table from `fa_company_scores` (full-pipeline scores): the two are
    produced by different methods with different accuracy (see
    app/quick_analysis/README.md) and must never be clubbed. One row per
    company, upserted each time the quick analysis is re-run; `scored_at` is
    the date, `latest_fy` the newest fiscal year in the Yahoo data used."""

    __tablename__ = "fa_quick_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    stock_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    sector_framework: Mapped[str | None] = mapped_column(String, nullable=True)
    overall: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    growth: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    # The two components blended into `growth` above (scoring.py's
    # `_growth_score()`) — stored separately (2026-09-27) so the Quick
    # Screener can filter/sort on either one, not just the blend. Full-
    # pipeline `fa_company_scores` has no equivalent columns yet — these
    # live only here.
    growth_annual: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    growth_quarterly: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    profitability: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    cash_flow: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    balance_sheet: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    efficiency: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    valuation: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    overall_rating: Mapped[str | None] = mapped_column(String, nullable=True)
    valuation_view: Mapped[str | None] = mapped_column(String, nullable=True)
    weights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    red_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    refinement: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latest_fy: Mapped[str | None] = mapped_column(String, nullable=True)
    method_version: Mapped[str] = mapped_column(String, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("fa_quick_scores_overall_idx", "overall"),
        Index("fa_quick_scores_growth_idx", "growth"),
        Index("fa_quick_scores_profitability_idx", "profitability"),
        Index("fa_quick_scores_cash_flow_idx", "cash_flow"),
        Index("fa_quick_scores_balance_sheet_idx", "balance_sheet"),
        Index("fa_quick_scores_efficiency_idx", "efficiency"),
        Index("fa_quick_scores_valuation_idx", "valuation"),
    )


class Shareholding(Base):
    """One (company, quarter) shareholding-pattern snapshot from NSE —
    Architecture v2 Stage 3. promoter_pct/public_pct come straight from
    NSE's summary API; pledge_pct is parsed out of that quarter's linked
    XBRL filing (see app/ingestion/shareholding_client.py)."""

    __tablename__ = "shareholding"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    period_end: Mapped[str] = mapped_column(String, nullable=False)
    promoter_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    public_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    pledge_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("shareholding_company_idx", "company_id", "period_end"),
        UniqueConstraint("company_id", "period_end", name="shareholding_company_period_uq"),
    )


class ShareholdingScreener(Base):
    """Supplementary promoter/FII/DII/public holding history from
    Screener.in (app/ingestion/screener_shareholding_client.py) — kept in
    its own table, never merged into `Shareholding`. Screener's own
    shareholding section has no pledge % field at all (confirmed by
    grepping openscreener's source, 2026-09-13), so it can never be
    authoritative for governance flags — it exists only to extend
    promoter/public trend depth beyond NSE's current 2022-on window (back
    to Mar 2017 on Screener) and to add the FII/DII split NSE's summary API
    doesn't expose. `frequency` distinguishes quarterly vs yearly rows
    since Screener reports both independently, not one derived from the
    other."""

    __tablename__ = "shareholding_screener"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    period_end: Mapped[str] = mapped_column(String, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False)  # "quarterly" | "yearly"
    promoter_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    fii_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    dii_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    public_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    shareholder_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("shareholding_screener_company_idx", "company_id", "period_end"),
        UniqueConstraint(
            "company_id", "period_end", "frequency",
            name="shareholding_screener_company_period_freq_uq",
        ),
    )


class GovernanceEvent(Base):
    """A deterministic, evidence-backed governance flag derived from
    shareholding trends — Architecture v2 Stage 3. Never an LLM-inferred
    conclusion; `evidence` always carries the exact values that produced it."""

    __tablename__ = "governance_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    event_date: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="NSE_SHAREHOLDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("governance_events_company_idx", "company_id"),
        UniqueConstraint("company_id", "event_type", "event_date", name="governance_events_dedup_uq"),
    )


class ValuationHistory(Base):
    """One fiscal year's real historical P/E and P/B — Architecture v2
    Stage 4. Genuinely different from engine.py's implied_pe_series()
    (which divides CURRENT price by historical EPS as a cheap proxy): this
    uses the actual price at the time, from a real monthly price series.
    Each year's eps/book_value_per_share is taken from whichever source had
    it (Screener.in preferred for depth, yfinance filling gaps) — tracked
    per-field via eps_source/bvps_source, not a single hard-picked source."""

    __tablename__ = "valuation_history"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    period_end: Mapped[str] = mapped_column(String, nullable=False)
    eps: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    eps_source: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    price_date: Mapped[str | None] = mapped_column(String, nullable=True)
    pe: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    book_value_per_share: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    bvps_source: Mapped[str | None] = mapped_column(String, nullable=True)
    pb: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("valuation_history_company_idx", "company_id", "period_end"),
        UniqueConstraint("company_id", "period_end", name="valuation_history_company_period_uq"),
    )


class AnalystConsensus(Base):
    """Third-party analyst sentiment/target-price snapshot (e.g. IndMoney).
    Deliberately separate from MetricDataPoint's fact ledger — this is
    external OPINION, never blended into this platform's own deterministic
    scoring or treated as a source of truth. See migration 0012's docstring
    for the full rationale, including why ingestion here is agent-fetched
    (via an MCP connector only a Claude session can reach) rather than an
    autonomous backend batch job like every other source in this app."""

    __tablename__ = "analyst_consensus"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    num_analysts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String, nullable=True)
    buy_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    hold_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    sell_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    target_price_mean: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_price_low: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_price_high: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_at_capture: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    implied_upside_pct: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="INDMONEY")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("analyst_consensus_company_idx", "company_id"),
        UniqueConstraint("company_id", "source", name="analyst_consensus_company_source_uq"),
    )


class Document(Base):
    """Metadata for a raw source file durably stored in MinIO —
    Architecture v2 Stage 7. The actual bytes live in object storage
    (app/infrastructure/storage/minio_client.py); this row is queryable
    provenance, with a sha256 to detect if a source ever silently changes
    its file."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    sha256: Mapped[str] = mapped_column(String, nullable=False)
    storage_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("documents_company_idx", "company_id", "document_type"),
    )


class ConcallTranscript(Base):
    """One earnings-call transcript filing — Concall Intelligence System,
    Stage C0. The raw PDF lives in the existing `documents`/MinIO storage
    (`document_id` FK); this row is the transcript-specific metadata layer
    (quarter, call date, named management participants) parsed from the
    transcript's own cover page. `management_participants` here is a
    best-effort summary parsed in C0 — Stage C1's speaker/role parser
    builds its own authoritative name→role map per utterance and doesn't
    depend on this field being perfect."""

    __tablename__ = "concall_transcripts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    quarter: Mapped[str | None] = mapped_column(String, nullable=True)  # "Q1 FY27"
    call_date: Mapped[str | None] = mapped_column(String, nullable=True)  # ISO date
    filing_date: Mapped[str | None] = mapped_column(String, nullable=True)  # ISO date
    management_participants: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="NSE")
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    # PENDING | PARSED (Stage C1) | EXTRACTED (Stage C3)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("concall_transcripts_company_idx", "company_id", "call_date"),
    )


class ConcallUtterance(Base):
    """One speaker turn from a parsed transcript — Concall Intelligence
    System, Stage C1. Deterministic regex parsing only (app/ingestion/
    concall_parser.py), no LLM here — `speaker_role`/`section` are exactly
    what make Stage C3's guidance extraction safe to restrict to management
    utterances only, so an analyst's question can never become "guidance"."""

    __tablename__ = "concall_utterances"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    transcript_id: Mapped[str] = mapped_column(
        String, ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker_name: Mapped[str] = mapped_column(String, nullable=False)
    speaker_role: Mapped[str] = mapped_column(String, nullable=False)
    # CEO | CFO | Deputy MD | COO | Chairman | Management | Analyst | Moderator
    section: Mapped[str] = mapped_column(String, nullable=False)  # opening_remarks | qa
    text: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("concall_utterances_transcript_idx", "transcript_id", "sequence"),
    )


class ConcallChunk(Base):
    """One embedded chunk (currently one per utterance — see app/ingestion/
    concall_parser.py's utterance granularity, merged-paragraph chunking is
    a possible future refinement, not needed yet) — Concall Intelligence
    System, Stage C2. pgvector was already installed and enabled in this
    Postgres instance before this stage started (confirmed live via
    `pg_extension`, docker-compose's postgres image is `pgvector/pgvector:
    pg16`) — no new infrastructure, just a new table using it. Embedded
    with `qwen3-embedding` (app/interpretation/embeddings.py) — see that
    module's docstring for why, not EmbeddingGemma as the source doc names."""

    __tablename__ = "concall_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    transcript_id: Mapped[str] = mapped_column(
        String, ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False
    )
    utterance_id: Mapped[str] = mapped_column(
        String, ForeignKey("concall_utterances.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    speaker_role: Mapped[str] = mapped_column(String, nullable=False)
    section: Mapped[str] = mapped_column(String, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(4096), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("concall_chunks_company_idx", "company_id"),
    )


class ManagementGuidance(Base):
    """One structured guidance/outlook statement extracted from a
    management utterance — Concall Intelligence System, Stage C3. Local-
    Llama-extracted (app/interpretation/guidance_extraction.py), restricted
    to CEO/CFO/Management-role utterances only (never an analyst's
    question — enforced upstream by the extraction call site, not by this
    schema). `status`/`change_midpoint` are computed deterministically in
    Python by comparing against `previous_guidance_id`, never assigned by
    the LLM — matches the doc's explicit "Llama never does the numerical
    comparison" rule, same principle already applied in the P&L system."""

    __tablename__ = "management_guidance"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    transcript_id: Mapped[str] = mapped_column(
        String, ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False
    )
    utterance_id: Mapped[str] = mapped_column(
        String, ForeignKey("concall_utterances.id", ondelete="CASCADE"), nullable=False
    )
    quarter: Mapped[str | None] = mapped_column(String, nullable=True)
    speaker_role: Mapped[str] = mapped_column(String, nullable=False)

    metric: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "EBITDA_margin"
    category: Mapped[str | None] = mapped_column(String, nullable=True)  # Financial | Operating | Capital Allocation | Business
    period: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "FY27"
    guidance_type: Mapped[str] = mapped_column(String, nullable=False)  # quantitative | qualitative

    target_low: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)
    target_high: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)
    target_value: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)

    statement: Mapped[str] = mapped_column(Text, nullable=False)  # verbatim source text
    tone: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)  # high | medium | low
    certainty: Mapped[str | None] = mapped_column(String, nullable=True)  # explicit | conditional | aspirational
    conditional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    status: Mapped[str] = mapped_column(String, nullable=False, default="NEW")
    # NEW | REITERATED | UPGRADED | DOWNGRADED | WITHDRAWN | ACHIEVED | MISSED | PARTIALLY_ACHIEVED
    previous_guidance_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("management_guidance.id", ondelete="SET NULL"), nullable=True
    )
    change_midpoint: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)

    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("management_guidance_company_metric_idx", "company_id", "metric", "period"),
    )


class ManagementCredibility(Base):
    """Deterministic guidance-consistency summary per (company, metric) —
    Concall Intelligence System, Stage C4. Computed purely in Python from
    `ManagementGuidance.status` history (app/interpretation/credibility.py)
    — no LLM involved. This is the CONSISTENCY signal (how often guidance
    for this metric was reiterated vs revised), not the doc's full "hit
    rate vs actual reported results" — that needs cross-referencing against
    real subsequent P&L figures (app/calculations/pnl_engine.py) via a
    metric-name mapping bridge that doesn't exist yet, deliberately left as
    future work rather than approximated."""

    __tablename__ = "management_credibility"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String, nullable=False)
    guidance_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upgraded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    downgraded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reiterated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_status: Mapped[str | None] = mapped_column(String, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "metric", name="management_credibility_company_metric_uq"),
    )


class ManagementPromise(Base):
    """One non-numerical forward commitment ("we will launch the new plant
    in Q3") — Concall Intelligence System, Stage C4. Populated
    deterministically from Stage C3's already-extracted qualitative
    `ManagementGuidance` rows (no new LLM call — the qualitative/promise
    distinction in the source doc is fuzzy anyway, "not every important
    statement is numerical"). `status` starts PENDING; verifying it against
    what actually happened needs either a subsequent quarter's transcript
    explicitly following up or real reported data — genuinely future work,
    not implemented this stage (see doc §22/41's own verification_metric
    field, which needs the same P&L cross-reference bridge noted on
    ManagementCredibility above)."""

    __tablename__ = "management_promises"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    guidance_id: Mapped[str] = mapped_column(
        String, ForeignKey("management_guidance.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    promise: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    target_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    # PENDING | ON_TRACK | ACHIEVED | DELAYED | MISSED | PARTIALLY_ACHIEVED | CANCELLED
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("management_promises_company_idx", "company_id"),
    )


class CompanySummary(Base):
    """Screener.in's free-text company description + revenue-mix-style
    key_points, one row per company. Used both as MCP/API context and
    injected into the HTML/PDF report's company overview section.
    governance_risk (2026-09-13) holds yfinance's audit/board/compensation/
    shareholder-rights/overall risk scores (1-10, Yahoo's own scale) —
    five small numbers, not worth a separate table."""

    __tablename__ = "company_summary"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    governance_risk: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="SCREENER")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessSegment(Base):
    """Per-segment revenue, one row per company+segment+fiscal_year —
    Deep Research System, Stage R1. Genuinely new: nothing in this codebase
    extracted business-segment-level revenue before this (confirmed via a
    full-codebase grep — only unfulfilled `na_message` placeholders existed
    in several sector files, e.g. automobile.py/pharma.py/chemicals.py).
    Sourced from TradingView's financials-segments page (see
    app/ingestion/tradingview_segments_client.py) — free, no login wall,
    confirmed live to return a genuine multi-year per-segment revenue table
    (not just a current-quarter snapshot)."""

    __tablename__ = "business_segments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    segment_name: Mapped[str] = mapped_column(String, nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "2025" (calendar year TradingView reports under)
    revenue: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="INR")
    source: Mapped[str] = mapped_column(String, nullable=False, default="TRADINGVIEW")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("business_segments_company_idx", "company_id"),
        UniqueConstraint(
            "company_id", "segment_name", "fiscal_year",
            name="business_segments_company_segment_year_uq",
        ),
    )


class BrokerResearchReport(Base):
    """Dated individual broker research-report history (Trendlyne, free
    metadata table — 2026-09-14). Deliberately distinct from
    AnalystConsensus: that table is a current-snapshot aggregate (mean
    target, buy/hold/sell %), this is the actual dated history of who
    called what, when, and whether the target was later hit — not
    reproducible from any source already in this app. The underlying PDF
    report text is login-gated on Trendlyne and NOT scraped here; only the
    free table row (broker, date, rating, target, price-at-reco) is."""

    __tablename__ = "broker_research_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    report_date: Mapped[str] = mapped_column(String, nullable=False)  # ISO date
    broker_name: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[str | None] = mapped_column(String, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    ltp_at_capture: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_at_reco: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    change_since_reco_pct: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    upside_pct: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    reco_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    target_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    report_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="TRENDLYNE")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("broker_research_reports_company_idx", "company_id"),
        UniqueConstraint(
            "company_id", "report_date", "broker_name",
            name="broker_research_reports_company_date_broker_uq",
        ),
    )


class CompanyBrand(Base):
    """Structured brand-level facts — Premium PDF System, Stage B1
    (2026-09-14). Extracted from CompanySummary.key_points (the full,
    logged-in Screener.in text — see screener_client.py's
    _fetch_full_key_points), the only source in this codebase that
    mentions individual brand names/market shares. Previously only
    available as unstructured prose; every field here must be literally
    traceable back to that source text (see brand_extraction.py's
    validation, reusing blueprint_validator.py's numeric-grounding check)."""

    __tablename__ = "company_brands"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    brand_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    ownership: Mapped[str | None] = mapped_column(String, nullable=True)  # "owned" | "licensed"
    market_share_pct: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    market_share_context: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "in Kerala", "of liquid dishwash"
    license_expiry: Mapped[str | None] = mapped_column(String, nullable=True)
    source_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="SCREENER")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("company_brands_company_idx", "company_id"),
        UniqueConstraint("company_id", "brand_name", name="company_brands_company_brand_uq"),
    )


class ConcallTopicSentiment(Base):
    """Per-topic management tone — Premium PDF System, Stage B2
    (2026-09-14). A controlled vocabulary of topics (not the freeform
    concall-guidance metrics ManagementGuidance already tracks) — see
    guidance_extraction.py's _TOPIC_SENTIMENT list. One row per
    transcript+topic actually discussed; a topic never brought up in a
    given call has no row (never fabricated as "Neutral")."""

    __tablename__ = "concall_topic_sentiment"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    transcript_id: Mapped[str] = mapped_column(
        String, ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String, nullable=False)
    sentiment: Mapped[str] = mapped_column(String, nullable=False)  # POSITIVE | NEUTRAL | NEGATIVE | MIXED
    evidence_utterance_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("concall_utterances.id", ondelete="SET NULL"), nullable=True
    )
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("concall_topic_sentiment_transcript_idx", "transcript_id"),
        Index("concall_topic_sentiment_company_idx", "company_id"),
        UniqueConstraint("transcript_id", "topic", name="concall_topic_sentiment_transcript_topic_uq"),
    )


class ConcallHighlight(Base):
    """Results & Concall Highlights narrative bullets — one set per
    transcript. `source="ARTHNEETI"` (2026-09-15 user directive: prefer
    arthneeti.com's already-AI-generated highlights over paying for our own
    LLM pass to re-derive the same narrative) when arthneeti.com has a
    matching page for this company+quarter; `source="GENERATED"` — a
    deterministic Python synthesis from our own already-extracted
    ConcallTopicSentiment/ManagementGuidance rows, no LLM call — when it
    doesn't (company not covered, slug/page not found, fetch failed).
    Never both: one row per transcript, whichever source actually produced
    it."""

    __tablename__ = "concall_highlights"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    transcript_id: Mapped[str] = mapped_column(
        String, ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String, nullable=False)  # ARTHNEETI | GENERATED
    sections: Mapped[list] = mapped_column(JSON, nullable=False)  # [{"heading": str, "bullets": [str, ...]}]
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("concall_highlights_company_idx", "company_id"),
    )


class ForwardEstimate(Base):
    """Consensus EPS/revenue estimates and growth estimates, by period
    ("0q"/"+1q"/"0y"/"+1y"/"LTG") — Yahoo Finance analysts, 2026-09-13.
    Nothing like this existed in the platform before this."""

    __tablename__ = "forward_estimates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    metric_type: Mapped[str] = mapped_column(String, nullable=False)
    period_label: Mapped[str] = mapped_column(String, nullable=False)
    avg: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)
    low: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)
    high: Mapped[float | None] = mapped_column(Numeric(20, 4), nullable=True)
    num_analysts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    growth_pct: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="YAHOO_FINANCE")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("forward_estimates_company_idx", "company_id"),
        UniqueConstraint("company_id", "metric_type", "period_label", name="forward_estimates_uq"),
    )


class InsiderActivity(Base):
    """Dated, named insider transactions — Yahoo Finance, 2026-09-13.
    Distinct from Stage 3's NSE shareholding-pattern data (aggregate %,
    not individual transactions)."""

    __tablename__ = "insider_activity"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    transaction_date: Mapped[str] = mapped_column(String, nullable=False)
    insider_name: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[str | None] = mapped_column(String, nullable=True)
    transaction_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    shares: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    value: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    ownership_type: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="YAHOO_FINANCE")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("insider_activity_company_idx", "company_id", "transaction_date"),
        UniqueConstraint("company_id", "transaction_date", "insider_name", "shares", name="insider_activity_uq"),
    )


class CorporateAction(Base):
    """Dividend/split history — Yahoo Finance, 2026-09-13."""

    __tablename__ = "corporate_actions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    action_date: Mapped[str] = mapped_column(String, nullable=False)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="YAHOO_FINANCE")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("corporate_actions_company_idx", "company_id", "action_date"),
        UniqueConstraint("company_id", "action_date", "action_type", name="corporate_actions_uq"),
    )


class CompanyNews(Base):
    """Recent news headlines with source attribution — Yahoo Finance,
    2026-09-13 (Yahoo aggregates from Reuters and other wire services)."""

    __tablename__ = "company_news"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="YAHOO_FINANCE")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("company_news_company_idx", "company_id", "published_at"),
        UniqueConstraint("company_id", "url", name="company_news_uq"),
    )


class EarningsCalendar(Base):
    """Next earnings date + expected EPS/revenue range — "future schedules,"
    Yahoo Finance, 2026-09-13. One row per company, upserted."""

    __tablename__ = "earnings_calendar"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    next_earnings_date: Mapped[str | None] = mapped_column(String, nullable=True)
    ex_dividend_date: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_eps_avg: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    expected_eps_low: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    expected_eps_high: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    expected_revenue_avg: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    expected_revenue_low: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    expected_revenue_high: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="YAHOO_FINANCE")
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MetricDataPoint(Base):
    """Append-only provenance ledger for sector-specific metric values that don't
    come from yfinance (e.g. banking metrics sourced from NSE XBRL filings).

    Conflicting values from different sources are never overwritten — both rows
    are kept and `get_authoritative_value()` resolves by source_tier at read time.
    See sector_frameworks/banking.md section 20-26 for the source hierarchy this
    schema implements.
    """

    __tablename__ = "fa_metric_data_points"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(
        String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    metric_key: Mapped[str] = mapped_column(String, nullable=False)          # e.g. "casa_ratio"
    period: Mapped[str] = mapped_column(String, nullable=False)              # e.g. "2026-Q1", "FY2026"
    value: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)                # "%", "bps", "x", "cr"
    statement_type: Mapped[str] = mapped_column(String, nullable=False, default="STANDALONE")
    # STANDALONE | CONSOLIDATED — a distinct axis from source/tier. Every BSE/NSE-sourced
    # row is standalone by construction (both extraction prompts say so explicitly);
    # Screener.in-sourced rows can be either, so a query must pick one rather than let
    # two genuinely different numbers for the same metric_key/period silently compete.

    source: Mapped[str] = mapped_column(String, nullable=False)
    # RBI | BSE_RESULTS_API | BSE_FILING_OCR | NSE_ANNUAL_REPORT | NSE_XBRL | COMPANY_IR | SCREENER | MONEYCONTROL | CALCULATED | MANUAL
    source_tier: Mapped[int] = mapped_column(Integer, nullable=False)        # 1 (regulatory/exchange) .. 5
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_document: Mapped[str | None] = mapped_column(String, nullable=True)
    source_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    reported_or_calculated: Mapped[str] = mapped_column(String, nullable=False)
    # REPORTED | CALCULATED | DERIVED | ESTIMATED
    calculation_formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String, nullable=False)          # HIGH | MEDIUM | LOW
    raw_reported_value: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("fa_metric_points_company_metric_idx", "company_id", "metric_key", "statement_type"),
        Index("fa_metric_points_company_metric_period_idx", "company_id", "metric_key", "period", "statement_type"),
    )


class AnalysisStage(Base):
    __tablename__ = "fa_analysis_stages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        String, ForeignKey("fa_analyses.id", ondelete="CASCADE"), nullable=False
    )
    stage_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    # PENDING | RUNNING | COMPLETED | FAILED | SKIPPED
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("fa_stages_analysis_idx", "analysis_id"),
    )


### `StockClassification` (`fa_stock_classification`, migration 0006) removed
### 2026-09-17 (migration 0028 drops the table). It was a separate ~1610-row
### shadow copy of the same sector/industry/basic_industry/macro_sector data
### now carried directly on `Stock` — `stocks` was expanded to the same
### ~1610-company universe and became the single source of truth, so the
### second copy (and the manual sync scripts that used to keep it aligned)
### was retired rather than maintained forever. See `app/routes/screening.py`
### and `app/sectors/classification_map.py` for the callers that used to
### depend on this table; both now read `Stock` directly.


class PlScoreComponents(Base):
    """M1-M5 weighted P&L Master Score, one row per (company, period,
    statement_type, algorithm_version) — P&L Analysis Engine, Milestone 3
    (`app/calculations/pl_intelligence/scoring.py`). Point-in-time
    persisted (unlike `pnl_engine.py`'s compute-on-read pattern) so a score
    stays reproducible under its `algorithm_version` even as the ledger
    grows — see migration 0027's docstring."""

    __tablename__ = "pl_score_components"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    statement_type: Mapped[str] = mapped_column(String, nullable=False, default="CONSOLIDATED")
    m1_sector_margin_percentile: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    m1_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    m2_margin_headroom: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    m2_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    m3_revenue_doubling_years: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    m3_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    m4_eqi: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    m4_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    m5_csr: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    m5_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    master_pl_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    classification: Mapped[str | None] = mapped_column(String, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String, nullable=False)
    data_version: Mapped[str | None] = mapped_column(String, nullable=True)
    peer_group_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("pl_score_components_company_idx", "company_id"),
        UniqueConstraint(
            "company_id", "period", "statement_type", "algorithm_version",
            name="pl_score_components_company_period_version_uq",
        ),
    )


class PlDiagnostics(Base):
    """One row per fired rule-based flag (`app/calculations/
    pl_intelligence/rules.py`), P&L Analysis Engine Milestone 3."""

    __tablename__ = "pl_diagnostics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    flag: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str | None] = mapped_column(String, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("pl_diagnostics_company_idx", "company_id"),
    )


class PlTrends(Base):
    """Margin-trend snapshot (spec Stage 4-7) — P&L Analysis Engine
    Milestone 3."""

    __tablename__ = "pl_trends"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    statement_type: Mapped[str] = mapped_column(String, nullable=False, default="CONSOLIDATED")
    gross_margin: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    gross_margin_confidence: Mapped[str] = mapped_column(String, nullable=False, default="LOW")
    ebitda_margin: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    ebit_margin: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    pat_margin: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    margin_direction: Mapped[str | None] = mapped_column(String, nullable=True)
    revenue_doubling_years: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    pat_doubling_years: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("pl_trends_company_idx", "company_id"),
    )


class PlStructuralAnalysis(Base):
    """Standalone-vs-consolidated + conglomerate/SOTP flags (spec Stage
    8-9, 24) — P&L Analysis Engine Milestone 3."""

    __tablename__ = "pl_structural_analysis"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    csr: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    csr_band: Mapped[str | None] = mapped_column(String, nullable=True)
    subsidiary_revenue_share: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    is_conglomerate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    segment_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    segment_sector_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sotp_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    algorithm_version: Mapped[str] = mapped_column(String, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("pl_structural_analysis_company_idx", "company_id"),
    )


class PlIncomeQuality(Base):
    """EQI + aggregate non-core income ratios (spec Stage 10-11) — P&L
    Analysis Engine Milestone 3."""

    __tablename__ = "pl_income_quality"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    eqi: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    core_operating_income: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_income: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    other_income_to_pat_pct: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    non_core_decomposition_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    algorithm_version: Mapped[str] = mapped_column(String, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("pl_income_quality_company_idx", "company_id"),
    )
