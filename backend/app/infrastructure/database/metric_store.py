"""Provenance-aware store for sector metrics that don't come from yfinance.

Implements the source hierarchy and conflict rule from
sector_frameworks/banking.md sections 20-22: values from different sources are
never overwritten, only appended; the authoritative value for a
(company, metric, period) is resolved at read time by lowest source_tier,
tie-broken by highest confidence, tie-broken again by most recent retrieval.

The confidence tie-break matters once two sources share a tier: since
2026-09-10, Screener.in (tier=2) and a BSE-OCR-derived CALCULATED figure
(also tier=2 for cost_to_income_ratio) can both land for the same period.
Recency alone would let whichever one happened to be *inserted* later win,
even if it's the worse (LOW-confidence) one — confirmed on real data: a
LOW-confidence BSE-derived cost_to_income_ratio landing 8 seconds after a
MEDIUM-confidence Screener one silently became "authoritative" and then got
filtered out entirely by banking_data_bridge.py's confidence gate, turning a
real value into an N/A. Sorting by confidence before recency fixes this.

Every read/write also takes `statement_type` (STANDALONE default, or
CONSOLIDATED) — a distinct axis from source/tier. Two genuinely different
numbers (e.g. Infosys FY2026 total assets: 1,25,701 Cr standalone vs 1,54,288
Cr consolidated) must never compete as if one superseded the other; callers
pick which one they want, defaulting to STANDALONE since that's what every
BSE/NSE-sourced row already is.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import MetricDataPoint

VALID_SOURCES = {
    "RBI",
    "BSE_RESULTS_API",     # BSE's structured TabResults_PAR/w snapshot (tagged fields, e.g. CAR%)
    "BSE_FILING_OCR",      # OCR + LLM extraction from BSE's official SEBI-format results PDF
    "NSE_ANNUAL_REPORT",   # text extraction (real text layer, no OCR) from NSE's annual report PDF
    "NSE_XBRL",            # documented but unverified from this environment — NSE blocks datacenter IPs
    "BSE_EARNINGS_CALL",   # text extraction (real text layer, no OCR) from a BSE-filed earnings-call
                            # transcript (Reg 30 disclosure) — sector-agnostic source, not IT-only
    "NSE_COMPANY_DISCLOSURE",  # structured company disclosures filed on NSE (e.g. monthly toll revenue), parsed without an LLM
    "PPAC_REPORT",  # PPAC monthly Snapshot of India's Oil & Gas data (LNG terminals, gas pipelines)
    "CEA_REPORT",  # Central Electricity Authority monthly Executive Summary (all-India sector PLF benchmark)
    "TRAI_REPORT",  # TRAI monthly telecom subscription report (regulator; operator market shares)
    "NSE_RESULTS_FILING",  # NSE outcome-of-board-meeting results filing (operating-KPI tables for telecom)
    "NSE_PRESS_RELEASE",  # NSE results press release via the quarterly KPI cascade (company-authored, structured)
    "NSE_CONCALL",  # earnings-call transcript (NSE) via the quarterly KPI cascade; MEDIUM confidence (prose, often rounded)
    "NSE_INVESTOR_PRESENTATION",  # text extraction (real text layer, no OCR) from a quarterly Investor
                                   # Presentation filed via NSE's corporate-announcements API — same
                                   # text-quality tier as NSE_ANNUAL_REPORT/BSE_EARNINGS_CALL, a
                                   # genuinely different document type (Quarterly Sector KPI Extraction
                                   # Engine, app/ingestion/quarterly_operating_metrics_ingestion.py)
    "COMPANY_IR",
    "SCREENER", "MONEYCONTROL", "CALCULATED", "MANUAL",
}
VALID_REPORTED_OR_CALCULATED = {"REPORTED", "CALCULATED", "DERIVED", "ESTIMATED"}
VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
VALID_STATEMENT_TYPES = {"STANDALONE", "CONSOLIDATED"}
DEFAULT_STATEMENT_TYPE = "STANDALONE"

_CONFIDENCE_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

# Architecture v2 Stage 0: a numeric confidence float alongside the existing
# HIGH/MEDIUM/LOW categorical field — additive only, nothing reads this yet.
# Scale matches Architecture v2 chatgpt.md's authority-level scheme (repo
# root): 1.00 regulator/exchange/company primary, 0.95 audited annual report
# or a corroborated human entry, 0.85 reputable third-party aggregator or an
# OCR pass over a primary filing, 0.70 a purely calculated/derived figure,
# floored at 0.20 (the doc's "LLM inference" floor — this app never inserts
# anything that uncertain, but numeric_confidence() should never claim less
# trust than the doc's own bottom bucket implies is meaningless).
_SOURCE_BASE_CONFIDENCE: dict[str, float] = {
    "RBI": 1.00, "BSE_RESULTS_API": 1.00, "NSE_XBRL": 1.00, "COMPANY_IR": 1.00,
    "NSE_ANNUAL_REPORT": 0.95, "BSE_EARNINGS_CALL": 0.95, "MANUAL": 0.95,
    "NSE_INVESTOR_PRESENTATION": 0.95, "NSE_CONCALL": 0.85, "NSE_PRESS_RELEASE": 0.95, "NSE_COMPANY_DISCLOSURE": 0.95, "NSE_RESULTS_FILING": 0.95, "TRAI_REPORT": 0.95, "CEA_REPORT": 0.95, "PPAC_REPORT": 0.95,
    "BSE_FILING_OCR": 0.85, "SCREENER": 0.85, "MONEYCONTROL": 0.85,
    "CALCULATED": 0.70,
}
_CONFIDENCE_DISCOUNT: dict[str, float] = {"HIGH": 0.0, "MEDIUM": 0.10, "LOW": 0.25}
_MIN_NUMERIC_CONFIDENCE = 0.20

# Plausibility guard (2026-09-13): a real, recurring failure mode — BSE OCR
# has twice now misread a figure by orders of magnitude and produced a
# "percentage" like 428,234% (Federal Bank, gross_npa) or 31,173% (HDFC
# Bank, earlier this project) instead of the true ~1-2%. Both times the
# garbage value landed at tier=1 and silently outranked a correct tier=2
# Screener value in get_authoritative_value() — tier is checked before
# confidence, so even a LOW-confidence tier=1 row still wins over a
# MEDIUM-confidence tier=2 one. Downgrading confidence alone can't fix
# this; the value must never be inserted at all. Bounds are deliberately
# generous (no real banking ratio approaches 1000%, even a bad quarter's
# cost-to-income or credit-cost) so this only ever catches genuine
# scale/misread errors, never a legitimate extreme ratio.
_PERCENT_PLAUSIBILITY_BOUND = 1000.0


def _implausibility_reason(unit: str, value: float) -> str | None:
    """None if `value` passes the plausibility check for `unit`, else a
    human-readable reason it didn't."""
    if unit == "%" and abs(value) > _PERCENT_PLAUSIBILITY_BOUND:
        return f"{value}% exceeds the {_PERCENT_PLAUSIBILITY_BOUND}% plausibility bound for a percentage metric"
    return None


def numeric_confidence(row: MetricDataPoint) -> float:
    """A 0.20-1.00 confidence float for one ledger row, derived from its
    existing (source, confidence) fields — not a new stored column, so this
    is purely additive and every existing call site is unaffected. The
    categorical HIGH/MEDIUM/LOW field remains authoritative for the
    tier-then-confidence-then-recency resolver in get_authoritative_value();
    this is a presentation-layer float for callers (MCP tools, later stages)
    that want the doc's numeric scale instead."""
    base = _SOURCE_BASE_CONFIDENCE.get(row.source, 0.50)
    discount = _CONFIDENCE_DISCOUNT.get(row.confidence, 0.10)
    return round(max(_MIN_NUMERIC_CONFIDENCE, base - discount), 2)


def insert_metric_value(
    db: Session,
    *,
    company_id: str,
    metric_key: str,
    period: str,
    value: float,
    unit: str,
    source: str,
    source_tier: int,
    reported_or_calculated: str,
    confidence: str,
    statement_type: str = DEFAULT_STATEMENT_TYPE,
    source_url: str | None = None,
    source_document: str | None = None,
    source_date: datetime | None = None,
    calculation_formula: str | None = None,
    raw_reported_value: str | None = None,
) -> MetricDataPoint | None:
    """Returns the inserted row, or None if `value` failed the plausibility
    guard (logged as a warning, never inserted) — callers must handle a
    None return the same way they already handle "field wasn't in the
    extraction result at all" (skip, don't append, keep going). Never
    raises for an implausible value; ValueError is reserved for genuine
    programmer errors (an invalid source/confidence/etc — a value bounds
    check is a data-quality event, not a code-contract violation)."""
    if source not in VALID_SOURCES:
        raise ValueError(f"Unknown source '{source}', expected one of {VALID_SOURCES}")
    if reported_or_calculated not in VALID_REPORTED_OR_CALCULATED:
        raise ValueError(
            f"Unknown reported_or_calculated '{reported_or_calculated}', "
            f"expected one of {VALID_REPORTED_OR_CALCULATED}"
        )
    if confidence not in VALID_CONFIDENCE:
        raise ValueError(f"Unknown confidence '{confidence}', expected one of {VALID_CONFIDENCE}")
    if statement_type not in VALID_STATEMENT_TYPES:
        raise ValueError(f"Unknown statement_type '{statement_type}', expected one of {VALID_STATEMENT_TYPES}")

    reason = _implausibility_reason(unit, value)
    if reason is not None:
        from app.logger import logger
        logger.warning(
            "metric_store: rejected implausible value, not inserted",
            company_id=company_id, metric_key=metric_key, period=period,
            value=value, unit=unit, source=source, reason=reason,
            raw_reported_value=raw_reported_value,
        )
        return None

    row = MetricDataPoint(
        id=str(uuid.uuid4()),
        company_id=company_id,
        metric_key=metric_key,
        period=period,
        value=value,
        unit=unit,
        statement_type=statement_type,
        source=source,
        source_tier=source_tier,
        source_url=source_url,
        source_document=source_document,
        source_date=source_date,
        retrieved_at=datetime.now(timezone.utc),
        reported_or_calculated=reported_or_calculated,
        calculation_formula=calculation_formula,
        confidence=confidence,
        raw_reported_value=raw_reported_value,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    return row


def get_metric_history(
    db: Session,
    company_id: str,
    metric_key: str,
    period: str | None = None,
    statement_type: str | None = DEFAULT_STATEMENT_TYPE,
) -> list[MetricDataPoint]:
    """All rows for a (company, metric[, period][, statement_type]), newest
    retrieval first. Pass statement_type=None to see both standalone and
    consolidated rows together (e.g. for an explicit side-by-side display)."""
    stmt = select(MetricDataPoint).where(
        MetricDataPoint.company_id == company_id,
        MetricDataPoint.metric_key == metric_key,
    )
    if period is not None:
        stmt = stmt.where(MetricDataPoint.period == period)
    if statement_type is not None:
        stmt = stmt.where(MetricDataPoint.statement_type == statement_type)
    stmt = stmt.order_by(MetricDataPoint.retrieved_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_authoritative_value(
    db: Session,
    company_id: str,
    metric_key: str,
    period: str,
    statement_type: str | None = None,
) -> tuple[MetricDataPoint | None, list[MetricDataPoint]]:
    """Resolve the winning value for a (company, metric, period, statement_type).

    Returns (winner, superseded_rows). Resolution: lowest source_tier wins;
    ties broken by highest confidence (HIGH > MEDIUM > LOW); remaining ties
    broken by most recent retrieved_at. Never silently drops conflicting
    data — superseded rows remain in the ledger and are returned for audit.
    Standalone and consolidated never compete against each other within one
    resolution — a caller wanting both explicitly calls this twice, once
    per statement_type.

    `statement_type=None` (the default): tries CONSOLIDATED first, falls
    back to STANDALONE only when CONSOLIDATED has nothing for this
    (company, metric, period). Real gap found live, repeatedly, across
    many call sites (2026-09-23, user's explicit instruction after the
    same class of bug recurred four separate times this session): every
    caller that omitted this argument silently got STANDALONE, whether or
    not that was ever the intent — most of the time it wasn't. A general
    "give me this company's value" call almost always means the
    consolidated (whole-group) figure; pass an explicit "STANDALONE" (or
    "CONSOLIDATED") for a genuine single-type lookup with no fallback —
    e.g. pl_intelligence/balance_sheet_intelligence/cash_flow_intelligence's
    own side-by-side comparisons, which must never silently redirect."""
    if statement_type is None:
        for candidate_type in ("CONSOLIDATED", "STANDALONE"):
            winner, superseded = get_authoritative_value(db, company_id, metric_key, period, statement_type=candidate_type)
            if winner is not None:
                return winner, superseded
        return None, []

    candidates = get_metric_history(db, company_id, metric_key, period, statement_type=statement_type)
    if not candidates:
        return None, []
    winner = min(
        candidates,
        key=lambda r: (r.source_tier, _CONFIDENCE_RANK.get(r.confidence, 99), -r.retrieved_at.timestamp()),
    )
    superseded = [r for r in candidates if r.id != winner.id]
    return winner, superseded


def get_both_statement_types(
    db: Session, company_id: str, metric_key: str, period: str
) -> dict[str, MetricDataPoint | None]:
    """Convenience for "show both, relevantly" call sites (e.g. a report
    section comparing standalone vs consolidated): {"STANDALONE": ..., "CONSOLIDATED": ...}."""
    return {
        st: get_authoritative_value(db, company_id, metric_key, period, statement_type=st)[0]
        for st in VALID_STATEMENT_TYPES
    }


def get_latest_period_value(
    db: Session,
    company_id: str,
    metric_key: str,
    statement_type: str | None = None,
) -> MetricDataPoint | None:
    """Authoritative value for the most recent *fiscal* period on record,
    within one statement_type.

    Deliberately NOT "whichever period was most recently retrieved" — a
    backfill processes filings in whatever order the source returns them,
    not fiscal order, so wall-clock retrieval time and fiscal recency can
    disagree. Confirmed on real data: HDFC Bank's 2024-03-31 period got
    inserted after 2026-06-30 during a backfill, so sorting by retrieved_at
    picked a year-old period as "latest." Periods are ISO date strings
    (YYYY-MM-DD), so max() sorts correctly by actual date.

    `statement_type=None` (the default): tries CONSOLIDATED first, falls
    back to STANDALONE only when CONSOLIDATED has no rows at all for this
    (company, metric) — same rationale and same 2026-09-23 fix as
    `get_authoritative_value()` above; most callers omitting this argument
    wanted the company's real consolidated figure, not STANDALONE by
    accident. Pass an explicit type for a genuine single-type lookup."""
    if statement_type is None:
        for candidate_type in ("CONSOLIDATED", "STANDALONE"):
            row = get_latest_period_value(db, company_id, metric_key, statement_type=candidate_type)
            if row is not None:
                return row
        return None

    all_rows = get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    if not all_rows:
        return None
    latest_period = max(r.period for r in all_rows)
    winner, _ = get_authoritative_value(db, company_id, metric_key, latest_period, statement_type=statement_type)
    return winner
