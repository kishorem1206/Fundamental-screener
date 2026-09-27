"""Yahoo Finance extended fundamental data — every "available, unused" item
from the 2026-09-13 yfinance API audit, all pulled from the same Ticker
object. Sector-agnostic (every listed company has these fields, unlike the
banking-specific BSE/NSE sources) and fully autonomous — unlike
analyst_consensus's IndMoney row, nothing here needs an agent-fetch step;
the backend calls yfinance directly like every other yfinance_client.py
function already does.

Every function here is independently gracefully-degrading: a company with
no news, no insider activity, or no analyst coverage yields an empty
result, not an error, matching every other ingestion path's contract.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    AnalystConsensus, CompanyNews, CompanySummary, CorporateAction,
    EarningsCalendar, ForwardEstimate, InsiderActivity,
)
from app.logger import logger

SOURCE = "YAHOO_FINANCE"


def _ticker(symbol: str, exchange: str = "NSE") -> yf.Ticker:
    suffix = ".BO" if exchange.upper() == "BSE" else ".NS"
    return yf.Ticker(f"{symbol}{suffix}")


def _to_float(v) -> float | None:
    try:
        if v is None or pd.isna(v):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


# ── Analyst consensus (targets + ratings) — Yahoo Finance's own analysts ───
# Reuses the analyst_consensus table (migration 0012) via source="YAHOO_FINANCE",
# side by side with any IndMoney row for the same company — never blended,
# every reader must keep attributing each row to its own source. Same
# "context only, never our own score" disclaimer applies here too.

def ingest_analyst_consensus_yahoo(db: Session, company_id: str, symbol: str, exchange: str = "NSE") -> dict | None:
    try:
        t = _ticker(symbol, exchange)
        info = t.info or {}
    except Exception as e:
        logger.warning("yfinance_extended: analyst consensus fetch failed", symbol=symbol, error=str(e))
        return None

    target_mean = _to_float(info.get("targetMeanPrice"))
    num_analysts = info.get("numberOfAnalystOpinions")
    if target_mean is None and num_analysts is None:
        return None

    current_price = _to_float(info.get("currentPrice") or info.get("regularMarketPrice"))
    upside_pct = None
    if target_mean is not None and current_price:
        upside_pct = round((target_mean - current_price) / current_price * 100, 2)

    fields = dict(
        num_analysts=int(num_analysts) if num_analysts is not None else None,
        sentiment=(info.get("recommendationKey") or "").upper() or None,
        target_price_mean=target_mean,
        target_price_low=_to_float(info.get("targetLowPrice")),
        target_price_high=_to_float(info.get("targetHighPrice")),
        price_at_capture=current_price,
        implied_upside_pct=upside_pct,
        source=SOURCE,
    )
    now = datetime.now(timezone.utc)
    existing = db.query(AnalystConsensus).filter_by(company_id=company_id, source=SOURCE).first()
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        existing.retrieved_at = now
        row = existing
    else:
        row = AnalystConsensus(id=str(uuid.uuid4()), company_id=company_id, retrieved_at=now, **fields)
        db.add(row)
    db.flush()
    return fields


# ── Forward estimates: EPS, revenue, growth ─────────────────────────────────

def ingest_forward_estimates(db: Session, company_id: str, symbol: str, exchange: str = "NSE") -> int:
    t = _ticker(symbol, exchange)
    now = datetime.now(timezone.utc)
    stored = 0

    def _store(metric_type: str, df: pd.DataFrame, growth_col: str | None):
        nonlocal stored
        if df is None or df.empty:
            return
        for period_label, row in df.iterrows():
            avg = _to_float(row.get("avg"))
            if avg is None and metric_type != "growth":
                continue
            fields = dict(
                avg=avg, low=_to_float(row.get("low")), high=_to_float(row.get("high")),
                num_analysts=int(row["numberOfAnalysts"]) if "numberOfAnalysts" in row and not pd.isna(row["numberOfAnalysts"]) else None,
                growth_pct=_to_float(row.get(growth_col)) * 100 if growth_col and _to_float(row.get(growth_col)) is not None else None,
                source=SOURCE,
            )
            existing = db.query(ForwardEstimate).filter_by(
                company_id=company_id, metric_type=metric_type, period_label=str(period_label)
            ).first()
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                existing.retrieved_at = now
            else:
                db.add(ForwardEstimate(
                    id=str(uuid.uuid4()), company_id=company_id, metric_type=metric_type,
                    period_label=str(period_label), retrieved_at=now, **fields,
                ))
            stored += 1

    try:
        _store("eps", t.earnings_estimate, "growth")
    except Exception as e:
        logger.warning("yfinance_extended: earnings_estimate failed", symbol=symbol, error=str(e))
    try:
        _store("revenue", t.revenue_estimate, "growth")
    except Exception as e:
        logger.warning("yfinance_extended: revenue_estimate failed", symbol=symbol, error=str(e))
    try:
        growth = t.growth_estimates
        if growth is not None and not growth.empty and "stockTrend" in growth.columns:
            for period_label, row in growth.iterrows():
                val = _to_float(row.get("stockTrend"))
                if val is None:
                    continue
                fields = dict(avg=None, low=None, high=None, num_analysts=None,
                               growth_pct=round(val * 100, 4), source=SOURCE)
                existing = db.query(ForwardEstimate).filter_by(
                    company_id=company_id, metric_type="growth", period_label=str(period_label)
                ).first()
                if existing:
                    for k, v in fields.items():
                        setattr(existing, k, v)
                    existing.retrieved_at = now
                else:
                    db.add(ForwardEstimate(
                        id=str(uuid.uuid4()), company_id=company_id, metric_type="growth",
                        period_label=str(period_label), retrieved_at=now, **fields,
                    ))
                stored += 1
    except Exception as e:
        logger.warning("yfinance_extended: growth_estimates failed", symbol=symbol, error=str(e))

    db.flush()
    return stored


# ── Insider activity (dated, named transactions) ────────────────────────────

def ingest_insider_activity(db: Session, company_id: str, symbol: str, exchange: str = "NSE", limit: int = 50) -> int:
    try:
        t = _ticker(symbol, exchange)
        df = t.insider_transactions
    except Exception as e:
        logger.warning("yfinance_extended: insider_transactions failed", symbol=symbol, error=str(e))
        return None
    if df is None or df.empty:
        return 0

    now = datetime.now(timezone.utc)
    stored = 0
    for _, row in df.head(limit).iterrows():
        start_date = row.get("Start Date")
        if start_date is None or pd.isna(start_date):
            continue
        date_str = str(start_date.date()) if hasattr(start_date, "date") else str(start_date)
        shares = _to_float(row.get("Shares"))
        existing = db.query(InsiderActivity).filter_by(
            company_id=company_id, transaction_date=date_str,
            insider_name=row.get("Insider"), shares=shares,
        ).first()
        if existing:
            continue
        db.add(InsiderActivity(
            id=str(uuid.uuid4()), company_id=company_id, transaction_date=date_str,
            insider_name=row.get("Insider"), position=row.get("Position"),
            transaction_text=row.get("Text"), shares=shares, value=_to_float(row.get("Value")),
            ownership_type=row.get("Ownership"), source=SOURCE, retrieved_at=now,
        ))
        stored += 1
    db.flush()
    return stored


# ── Corporate actions: dividends + splits ───────────────────────────────────

def ingest_corporate_actions(db: Session, company_id: str, symbol: str, exchange: str = "NSE") -> int:
    t = _ticker(symbol, exchange)
    now = datetime.now(timezone.utc)
    stored = 0

    try:
        for date_idx, amount in t.dividends.items():
            date_str = str(date_idx.date())
            existing = db.query(CorporateAction).filter_by(
                company_id=company_id, action_date=date_str, action_type="DIVIDEND"
            ).first()
            if existing:
                continue
            db.add(CorporateAction(
                id=str(uuid.uuid4()), company_id=company_id, action_date=date_str,
                action_type="DIVIDEND", value=float(amount), source=SOURCE, retrieved_at=now,
            ))
            stored += 1
    except Exception as e:
        logger.warning("yfinance_extended: dividends failed", symbol=symbol, error=str(e))

    try:
        for date_idx, ratio in t.splits.items():
            date_str = str(date_idx.date())
            existing = db.query(CorporateAction).filter_by(
                company_id=company_id, action_date=date_str, action_type="SPLIT"
            ).first()
            if existing:
                continue
            db.add(CorporateAction(
                id=str(uuid.uuid4()), company_id=company_id, action_date=date_str,
                action_type="SPLIT", value=float(ratio), source=SOURCE, retrieved_at=now,
            ))
            stored += 1
    except Exception as e:
        logger.warning("yfinance_extended: splits failed", symbol=symbol, error=str(e))

    db.flush()
    return stored


# ── News ─────────────────────────────────────────────────────────────────
# Real bug found 2026-09-13 while adding news to the PDF reports: yfinance's
# `.news` endpoint has no reliable per-item ticker linkage for Indian stocks
# — every item's `relatedTickers`/`finance.stockTickers` field came back
# None for TCS.NS, and most of the 10 items returned were generic market
# news (Rezolve AI/RZLV, Porsche, US H-1B policy) with zero relation to
# TCS. Since there's no structured relevance signal to filter on, this
# falls back to a deterministic keyword check against the company's own
# name/symbol — the same "never fabricate, degrade gracefully" contract as
# every other ingestion path, just applied as a relevance filter instead of
# a data-presence check.
_COMPANY_SUFFIX_RE = re.compile(r"\b(ltd|limited|inc|corp|corporation|plc|company|co)\.?\s*$", re.IGNORECASE)


def _is_relevant_news(title: str, summary: str | None, symbol: str, company_name: str | None) -> bool:
    text = f"{title} {summary or ''}".lower()
    if symbol and re.search(rf"\b{re.escape(symbol.lower())}\b", text):
        return True
    if company_name:
        core = _COMPANY_SUFFIX_RE.sub("", company_name).strip()
        if core and core.lower() in text:
            return True
    return False


def ingest_company_news(db: Session, company_id: str, symbol: str, exchange: str = "NSE",
                         limit: int = 10, company_name: str | None = None) -> int:
    try:
        t = _ticker(symbol, exchange)
        items = t.news or []
    except Exception as e:
        logger.warning("yfinance_extended: news failed", symbol=symbol, error=str(e))
        return 0

    now = datetime.now(timezone.utc)
    stored = 0
    skipped_irrelevant = 0
    for item in items[:limit]:
        content = item.get("content") or {}
        url = ((content.get("canonicalUrl") or {}).get("url")
               or (content.get("clickThroughUrl") or {}).get("url"))
        title = content.get("title")
        if not url or not title:
            continue
        summary = content.get("summary") or content.get("description")
        if not _is_relevant_news(title, summary, symbol, company_name):
            skipped_irrelevant += 1
            continue
        existing = db.query(CompanyNews).filter_by(company_id=company_id, url=url).first()
        if existing:
            continue
        published_at = None
        pub_date = content.get("pubDate")
        if pub_date:
            try:
                published_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except ValueError:
                pass
        db.add(CompanyNews(
            id=str(uuid.uuid4()), company_id=company_id, headline=title,
            summary=summary,
            provider=(content.get("provider") or {}).get("displayName"),
            url=url, published_at=published_at, source=SOURCE, retrieved_at=now,
        ))
        stored += 1
    db.flush()
    if skipped_irrelevant:
        logger.info("yfinance_extended: filtered irrelevant news", symbol=symbol,
                    stored=stored, skipped_irrelevant=skipped_irrelevant)
    return stored


# ── Earnings calendar (next earnings date + expected range) ────────────────

def ingest_earnings_calendar(db: Session, company_id: str, symbol: str, exchange: str = "NSE") -> dict | None:
    try:
        t = _ticker(symbol, exchange)
        cal = t.calendar or {}
    except Exception as e:
        logger.warning("yfinance_extended: calendar failed", symbol=symbol, error=str(e))
        return None
    if not cal:
        return None

    earnings_dates = cal.get("Earnings Date") or []
    next_earnings = str(earnings_dates[0]) if earnings_dates else None
    ex_div = cal.get("Ex-Dividend Date")

    fields = dict(
        next_earnings_date=next_earnings,
        ex_dividend_date=str(ex_div) if ex_div else None,
        expected_eps_avg=_to_float(cal.get("Earnings Average")),
        expected_eps_low=_to_float(cal.get("Earnings Low")),
        expected_eps_high=_to_float(cal.get("Earnings High")),
        expected_revenue_avg=_to_float(cal.get("Revenue Average")),
        expected_revenue_low=_to_float(cal.get("Revenue Low")),
        expected_revenue_high=_to_float(cal.get("Revenue High")),
        source=SOURCE,
    )
    now = datetime.now(timezone.utc)
    existing = db.query(EarningsCalendar).filter_by(company_id=company_id).first()
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        existing.retrieved_at = now
    else:
        db.add(EarningsCalendar(id=str(uuid.uuid4()), company_id=company_id, retrieved_at=now, **fields))
    db.flush()
    return fields


# ── Governance risk scores (stored on company_summary) ──────────────────────

def ingest_governance_risk(db: Session, company_id: str, symbol: str, exchange: str = "NSE") -> dict | None:
    try:
        t = _ticker(symbol, exchange)
        info = t.info or {}
    except Exception as e:
        logger.warning("yfinance_extended: governance risk fetch failed", symbol=symbol, error=str(e))
        return None

    risk_fields = {
        "audit_risk": info.get("auditRisk"), "board_risk": info.get("boardRisk"),
        "compensation_risk": info.get("compensationRisk"),
        "shareholder_rights_risk": info.get("shareHolderRightsRisk"),
        "overall_risk": info.get("overallRisk"),
    }
    if all(v is None for v in risk_fields.values()):
        return None

    now = datetime.now(timezone.utc)
    existing = db.query(CompanySummary).filter_by(company_id=company_id).first()
    if existing:
        existing.governance_risk = risk_fields
        existing.retrieved_at = now
    else:
        db.add(CompanySummary(
            id=str(uuid.uuid4()), company_id=company_id, governance_risk=risk_fields,
            source="SCREENER", retrieved_at=now,
        ))
    db.flush()
    return risk_fields


def ingest_all(db: Session, company_id: str, symbol: str, exchange: str = "NSE",
                company_name: str | None = None) -> dict:
    """Run every yfinance-extended ingestion function for one company.
    Each is independently wrapped — one failing (e.g. no analyst coverage
    for a small-cap) never blocks the others."""
    results = {}
    for name, fn in (
        ("analyst_consensus", ingest_analyst_consensus_yahoo),
        ("forward_estimates", ingest_forward_estimates),
        ("insider_activity", ingest_insider_activity),
        ("corporate_actions", ingest_corporate_actions),
        ("news", ingest_company_news),
        ("earnings_calendar", ingest_earnings_calendar),
        ("governance_risk", ingest_governance_risk),
    ):
        try:
            extra = {"company_name": company_name} if name == "news" else {}
            results[name] = fn(db, company_id, symbol, exchange, **extra)
        except Exception as e:
            logger.warning("yfinance_extended: ingest_all step failed", step=name, symbol=symbol, error=str(e))
            results[name] = None
    return results
