"""Concall Intelligence data — read-only, frontend-facing. Reuses the same
`build_concall_report_data` both PDF paths already call (guidance,
credibility, promises, topic-sentiment, quarter-over-quarter change,
guidance consistency), plus the latest transcript's highlights row
(arthneeti.com primary, deterministic-generated fallback — see
app/ingestion/arthneeti_client.py). This is the Concall Intelligence
System's first frontend surface — everything here has existed in the PDF
reports since Stage C5/the Premium PDF System's B2/B3/B5, but nothing was
ever exposed to the frontend until now.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import ConcallHighlight, ConcallTranscript
from app.interpretation.concall_report_data import build_concall_report_data

router = APIRouter(prefix="/api/concall")


@router.get("/{company_id:path}")
def get_concall_intelligence(company_id: str):
    db = get_db()
    try:
        data = build_concall_report_data(db, company_id)
        highlights = None
        latest_transcript = (
            db.query(ConcallTranscript).filter_by(company_id=company_id)
            .order_by(ConcallTranscript.filing_date.desc()).first()
        )
        if latest_transcript is not None:
            row = db.query(ConcallHighlight).filter_by(transcript_id=latest_transcript.id).first()
            if row is not None:
                highlights = {"source": row.source, "source_url": row.source_url, "sections": row.sections}
        data["highlights"] = highlights
        return data
    finally:
        db.close()
