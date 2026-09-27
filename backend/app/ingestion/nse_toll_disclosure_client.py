"""Monthly toll-revenue disclosures (road operators, e.g. IRB Infrastructure).

IRB files a "project-wise toll revenue" update on NSE every month with a group
total and the year-ago month (INR million). A deterministic parse (no LLM) turns
these into `mth_svc_toll_revenue` rows and, once all three months of a fiscal
quarter are on file, a `qtr_svc_toll_revenue` roll-up with YoY growth.

The figure is GROSS collection across wholly-owned, JV and InvIT project SPVs
(some added during the year), so growth is not like-for-like; it is stored
under CONSOLIDATED with that caveat in the provenance text.
"""
from __future__ import annotations

import calendar
import io
import re
from datetime import datetime, timedelta, timezone

import pdfplumber
from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.ingestion import nse_client
from app.logger import logger

_ANNOUNCEMENTS_URL = "https://www.nseindia.com/api/corporate-announcements"
_MONTH_RE = re.compile(r"Toll\s+(?:Revenue|Collection)\s+for\s+(?:the\s+month\s+of\s+)?([A-Za-z]+)\s+(\d{4})", re.I)
_TOTAL_RE = re.compile(r"Total\s*:?\s*([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)")
_SOURCE = "NSE_COMPANY_DISCLOSURE"


def parse_toll_disclosure(text: str) -> dict | None:
    """-> {"month_end": "YYYY-MM-DD", "current_cr", "prior_cr"} or None. Units are
    INR million in the filing; only accepted when the table says so."""
    m, t = _MONTH_RE.search(text), _TOTAL_RE.search(text)
    if not m or not t or "million" not in text.lower():
        return None
    try:
        month = list(calendar.month_name).index(m.group(1).capitalize())
        year = int(m.group(2))
        cur, prior = (float(g.replace(",", "")) / 10 for g in t.groups())
    except (ValueError, IndexError):
        return None
    return {"month_end": f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}",
            "current_cr": round(cur, 1), "prior_cr": round(prior, 1)}


def _find_filings(symbol: str, session, lookback_days: int) -> list[dict]:
    to = datetime.now()
    params = {"index": "equities", "symbol": symbol,
              "from_date": (to - timedelta(days=lookback_days)).strftime("%d-%m-%Y"), "to_date": to.strftime("%d-%m-%Y")}
    try:
        r = session.get(_ANNOUNCEMENTS_URL, params=params, timeout=20)
        r.raise_for_status()
        rows = r.json() or []
    except Exception as e:
        logger.warning("nse_toll_disclosure_client: search failed", symbol=symbol, error=str(e))
        return []
    return [x for x in rows if x.get("attchmntFile") and re.search(r"toll (revenue|collection)", (x.get("attchmntText") or ""), re.I)]


def _quarter_rollups(db: Session, company_id: str, url: str, now) -> list:
    out = []
    for year in {int(p[:4]) for p in _month_periods(db, company_id)}:
        for q_end_month in (3, 6, 9, 12):
            months = [q_end_month - 2, q_end_month - 1, q_end_month]
            cur, prior = [], []
            for mo in months:
                end = f"{year}-{mo:02d}-{calendar.monthrange(year, mo)[1]:02d}"
                c = metric_store.get_authoritative_value(db, company_id, "mth_svc_toll_revenue", end, statement_type="CONSOLIDATED")[0]
                p = metric_store.get_authoritative_value(db, company_id, "mth_svc_toll_revenue_yoy_prior", end, statement_type="CONSOLIDATED")[0]
                cur.append(c), prior.append(p)
            if any(x is None for x in cur + prior):
                continue
            period = f"{year}-{q_end_month:02d}-{calendar.monthrange(year, q_end_month)[1]:02d}"
            total, prior_total = sum(float(x.value) for x in cur), sum(float(x.value) for x in prior)
            for key, val, unit, kind, formula in (
                ("qtr_svc_toll_revenue", total, "INR Cr", "CALCULATED", "sum of the three monthly group totals"),
                ("qtr_svc_toll_revenue_yoy_prior", prior_total, "INR Cr", "CALCULATED", "sum of the year-ago months"),
                ("qtr_svc_toll_growth_yoy", (total - prior_total) / prior_total * 100, "%", "CALCULATED",
                 "(quarter toll - year-ago quarter toll) / year-ago quarter toll * 100"),
            ):
                row = metric_store.insert_metric_value(
                    db, company_id=company_id, metric_key=key, period=period, value=round(val, 2), unit=unit,
                    statement_type="CONSOLIDATED", source=_SOURCE, source_tier=1, reported_or_calculated=kind,
                    confidence="HIGH", calculation_formula=formula, source_url=url,
                    source_document="NSE monthly project-wise toll revenue disclosures (gross, group + InvIT SPVs; assets added during the year, so growth is not like-for-like)",
                    source_date=now)
                if row is not None:
                    out.append(row)
    return out


def _month_periods(db: Session, company_id: str) -> list[str]:
    return [r.period for r in metric_store.get_metric_history(db, company_id, "mth_svc_toll_revenue", statement_type="CONSOLIDATED")]


def ingest_monthly_toll_revenue(db: Session, company_id: str, symbol: str, lookback_days: int = 200) -> list:
    """Stores monthly + quarterly toll revenue for a road operator. [] when the
    company files no such disclosures. Never raises."""
    inserted: list = []
    try:
        session = nse_client._session()
        filings = _find_filings(symbol, session, lookback_days)
        now = datetime.now(timezone.utc)
        last_url = None
        for f in filings:
            try:
                blob = session.get(f["attchmntFile"], timeout=45).content
                with pdfplumber.open(io.BytesIO(blob)) as pdf:
                    text = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
            except Exception:
                continue
            parsed = parse_toll_disclosure(text)
            if parsed is None:
                continue
            last_url = f["attchmntFile"]
            for key, val in (("mth_svc_toll_revenue", parsed["current_cr"]), ("mth_svc_toll_revenue_yoy_prior", parsed["prior_cr"])):
                row = metric_store.insert_metric_value(
                    db, company_id=company_id, metric_key=key, period=parsed["month_end"], value=val, unit="INR Cr",
                    statement_type="CONSOLIDATED", source=_SOURCE, source_tier=1, reported_or_calculated="REPORTED",
                    confidence="HIGH", source_url=f["attchmntFile"],
                    source_document="NSE monthly project-wise toll revenue disclosure (INR million converted to crore)",
                    source_date=now, raw_reported_value=str(val))
                if row is not None:
                    inserted.append(row)
        if last_url:
            inserted += _quarter_rollups(db, company_id, last_url, now)
    except Exception as e:
        logger.warning("nse_toll_disclosure_client: ingestion failed", symbol=symbol, error=str(e))
    return inserted
