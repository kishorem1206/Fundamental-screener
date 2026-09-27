"""Sources & Evidence ledger — Premium PDF System, Stage B6. No new
ingestion: every row aggregated here already carries source/date metadata
from when it was originally stored (metric_store's per-row source/tier/
source_date, and the source/retrieved_at fields every other ingestion
module in this codebase already tags its rows with). This just groups that
already-tracked provenance into one list for the PDF's "Sources & Evidence"
page (pdf generation.md §17/Page 14).

Tier follows the same hierarchy metric_store.py already documents:
1 = regulatory/exchange/company filing, 2 = high-quality secondary
(financial press, aggregators reading real filings), 3 = context/industry.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    AnalystConsensus, BrokerResearchReport, BusinessSegment, CompanyNews,
    CompanySummary, ConcallTranscript, MetricDataPoint,
)

# Fallback tier for a source that only ever appears outside metric_store
# (which is the only table carrying an explicit numeric tier already).
_DEFAULT_TIER = {
    "NSE": 1, "SCREENER": 2, "TRENDLYNE": 3, "GOOGLE_NEWS": 2,
    "YAHOO_FINANCE": 2, "INDIANAPI": 2, "TRADINGVIEW": 3, "INDMONEY": 2,
}


def build_source_ledger(db: Session, company_id: str) -> list[dict]:
    """Never raises the caller shouldn't have to guard — any single
    table's aggregation failing just omits that row type rather than
    failing the whole ledger (matches every renderer in this codebase
    treating missing data as absence, not a hard error)."""
    ledger: list[dict] = []

    def add(source: str, source_type: str, used_for: str, tier: int,
             date_from, date_to, count: int) -> None:
        if count == 0:
            return
        ledger.append({
            "source": source, "type": source_type, "used_for": used_for, "tier": tier,
            "date_from": str(date_from) if date_from else None,
            "date_to": str(date_to) if date_to else None,
            "fact_count": count,
        })

    try:
        rows = (
            db.query(
                MetricDataPoint.source, MetricDataPoint.source_tier,
                func.min(MetricDataPoint.source_date), func.max(MetricDataPoint.source_date),
                func.count(),
            )
            .filter_by(company_id=company_id)
            .group_by(MetricDataPoint.source, MetricDataPoint.source_tier)
            .all()
        )
        for source, tier, dmin, dmax, count in rows:
            add(source, "Financial data / filing", "Sector metrics & ratios", tier, dmin, dmax, count)
    except Exception:
        pass

    try:
        summary = db.query(CompanySummary).filter_by(company_id=company_id).first()
        if summary:
            add("Screener.in", "Company description", "Business overview, brands, key points",
                _DEFAULT_TIER["SCREENER"], summary.retrieved_at, summary.retrieved_at, 1)
    except Exception:
        pass

    try:
        news_rows = (
            db.query(CompanyNews.source, func.min(CompanyNews.published_at), func.max(CompanyNews.published_at), func.count())
            .filter_by(company_id=company_id).group_by(CompanyNews.source).all()
        )
        for source, dmin, dmax, count in news_rows:
            add(source, "News", "Recent developments", _DEFAULT_TIER.get(source, 3), dmin, dmax, count)
    except Exception:
        pass

    try:
        broker_rows = (
            db.query(func.min(BrokerResearchReport.report_date), func.max(BrokerResearchReport.report_date), func.count())
            .filter_by(company_id=company_id).first()
        )
        if broker_rows and broker_rows[2]:
            add("Trendlyne", "Broker research metadata", "Analyst ratings history",
                _DEFAULT_TIER["TRENDLYNE"], broker_rows[0], broker_rows[1], broker_rows[2])
    except Exception:
        pass

    try:
        transcripts = db.query(ConcallTranscript).filter_by(company_id=company_id).order_by(ConcallTranscript.filing_date).all()
        if transcripts:
            add("NSE (corporate announcements)", "Earnings call transcript",
                "Management guidance & commentary", 1,
                transcripts[0].filing_date, transcripts[-1].filing_date, len(transcripts))
    except Exception:
        pass

    try:
        seg_count = db.query(func.count()).select_from(BusinessSegment).filter_by(company_id=company_id).scalar()
        if seg_count:
            add("TradingView", "Segment financials", "Business segment revenue", _DEFAULT_TIER["TRADINGVIEW"], None, None, seg_count)
    except Exception:
        pass

    try:
        consensus_rows = db.query(AnalystConsensus).filter_by(company_id=company_id).all()
        for r in consensus_rows:
            add(r.source, "Analyst consensus", "Target price & rating distribution",
                _DEFAULT_TIER.get(r.source, 2), r.retrieved_at, r.retrieved_at, 1)
    except Exception:
        pass

    ledger.sort(key=lambda r: (r["tier"], r["source"]))
    return ledger
