"""Shared query/compute layer for the Premium PDF System's remaining
stages (B1, B4, B6, B7) plus the arthneeti highlights block — mirrors
`concall_report_data.py`'s role for B2/B3/B5 (already handled there and not
duplicated here) and `pnl_engine.py`'s role for the P&L section: one
function both renderers (ReportLab `report_service.py` and the Jinja/HTML
banking path's `data_builder.py`) call, so the two PDF paths can't drift
out of parity. Computed fresh at render time — nothing here is persisted
beyond what its own ingestion module already stored.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import CompanyBrand, ConcallHighlight, ConcallTranscript, FundamentalAnalysis
from app.interpretation.peer_price_performance import compute_rebased_performance
from app.interpretation.price_chart import build_price_charts
from app.reporting.change_log import build_change_log
from app.reporting.source_ledger import build_source_ledger

_MAX_PEERS_IN_CHART = 4
_CHART_POINTS = 14  # a daily 1Y series (~250 points) is illegible at report
# width in either renderer — downsampled once here so both stay in sync.


def _downsample(points: list[dict], n: int = _CHART_POINTS) -> list[dict]:
    if len(points) <= n:
        return points
    step = len(points) / n
    return [points[int(i * step)] for i in range(n)]


def _brands(db: Session, company_id: str) -> list[dict]:
    rows = db.query(CompanyBrand).filter_by(company_id=company_id).order_by(
        CompanyBrand.market_share_pct.desc().nullslast(), CompanyBrand.brand_name
    ).all()
    return [
        {
            "brand_name": r.brand_name, "category": r.category, "ownership": r.ownership,
            "market_share_pct": float(r.market_share_pct) if r.market_share_pct is not None else None,
            "market_share_context": r.market_share_context, "license_expiry": r.license_expiry,
        }
        for r in rows
    ]


def _concall_highlights(db: Session, company_id: str) -> dict | None:
    """Latest transcript's highlight sections, whichever source produced
    them (ARTHNEETI primary, GENERATED fallback — see
    `app/ingestion/arthneeti_client.py`'s module docstring)."""
    latest_transcript = (
        db.query(ConcallTranscript).filter_by(company_id=company_id)
        .order_by(ConcallTranscript.filing_date.desc()).first()
    )
    if latest_transcript is None:
        return None
    row = db.query(ConcallHighlight).filter_by(transcript_id=latest_transcript.id).first()
    if row is None:
        return None
    return {"source": row.source, "source_url": row.source_url, "sections": row.sections}


def _peer_performance(company_info: dict, peers_field: dict | None, period: str = "1y") -> dict:
    subject = {
        "name": company_info.get("company_name"), "symbol": company_info.get("symbol"),
        "exchange": company_info.get("exchange") or "NSE",
    }
    peer_list = (peers_field or {}).get("peers") or []
    peers = [
        {"name": p.get("company_name"), "symbol": p.get("symbol"), "exchange": p.get("exchange") or "NSE"}
        for p in peer_list[:_MAX_PEERS_IN_CHART]
    ]
    if not subject["symbol"]:
        return {"period": period, "series": []}
    result = compute_rebased_performance(subject, peers, period=period)
    for s in result["series"]:
        s["points"] = _downsample(s["points"])
    return result


def build_premium_extras(db: Session, company_id: str, analysis: FundamentalAnalysis) -> dict:
    """Never raises as a whole — each piece is independently best-effort,
    matching every other renderer-facing builder in this codebase (a
    missing brand list or peer-price fetch failure doesn't blank the rest
    of the report)."""
    company_info = analysis.company_info or {}
    out = {"brands": [], "peer_performance": {"period": "1y", "series": []},
           "source_ledger": [], "change_log": None, "concall_highlights": None,
           "price_chart": {"1y": [], "5y": []}}
    try:
        out["brands"] = _brands(db, company_id)
    except Exception:
        pass
    try:
        out["peer_performance"] = _peer_performance(company_info, analysis.peers)
    except Exception:
        pass
    try:
        out["source_ledger"] = build_source_ledger(db, company_id)
    except Exception:
        pass
    try:
        out["change_log"] = build_change_log(db, analysis)
    except Exception:
        pass
    try:
        out["concall_highlights"] = _concall_highlights(db, company_id)
    except Exception:
        pass
    try:
        out["price_chart"] = build_price_charts(company_info.get("symbol"), company_info.get("exchange") or "NSE")
    except Exception:
        pass
    return out
