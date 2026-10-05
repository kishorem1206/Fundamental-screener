"""Phase 2 — management commentary as sourced facts. The concall system
already extracts guidance statements from earnings-call transcripts
(`management_guidance`); this brings each one into `bie_facts` as
MANAGEMENT_GUIDANCE, located on its page of the archived transcript. A
statement that cannot be found verbatim in the archived PDF is left out.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.bie.annual_report_extract import page_texts
from app.bie.documents import content_of
from app.bie.evidence import record_fact
from app.infrastructure.database.models import BieFact, ConcallTranscript, Document, ManagementGuidance


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def import_guidance(db: Session, company_id: str) -> dict:
    db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.fact_type == "guidance").delete(synchronize_session=False)
    rows = (db.query(ManagementGuidance, ConcallTranscript).join(ConcallTranscript, ConcallTranscript.id == ManagementGuidance.transcript_id)
            .filter(ManagementGuidance.company_id == company_id).all())
    pages_by_doc: dict[str, list[str]] = {}
    documents: dict[str, Document] = {}
    written = skipped = 0
    for guidance, transcript in rows:
        doc = db.get(Document, transcript.document_id) if transcript.document_id else None
        if doc is None or not doc.url:
            skipped += 1
            continue
        if doc.id not in pages_by_doc:
            content = content_of(doc)
            pages_by_doc[doc.id] = [_squash(t) for t in page_texts(content)] if content else []
            doc.title = doc.title or f"Earnings call transcript, {transcript.quarter or transcript.call_date or ''}".strip(", ")
        statement = re.sub(r"\s+", " ", guidance.statement).strip()
        # Locate by the opening words: a long statement can straddle a page break.
        probe = _squash(statement)[:70]
        page = next((i for i, text in enumerate(pages_by_doc[doc.id]) if probe and probe in text), None)
        if page is None:
            skipped += 1
            continue
        quote = statement[:70]
        record_fact(
            db, scope="COMPANY", company_id=company_id, fact_type="guidance", key=guidance.metric,
            dimension=f"{transcript.quarter or ''} {guidance.id[:8]}".strip(), value_text=statement[:1500],
            value_num=float(guidance.target_value) if guidance.target_value is not None else None, unit=guidance.unit,
            attributes={"for_period": guidance.period, "speaker_role": guidance.speaker_role, "status": guidance.status,
                        "certainty": guidance.certainty, "category": guidance.category, "quarter": transcript.quarter,
                        "call_date": str(transcript.call_date) if transcript.call_date else None,
                        "target_low": float(guidance.target_low) if guidance.target_low is not None else None,
                        "target_high": float(guidance.target_high) if guidance.target_high is not None else None},
            nature="MANAGEMENT_GUIDANCE", document=doc, locator_type="PAGE", page=page + 1, quote=quote,
            extraction_method="LLM_EXTRACT_QUOTE_LOCATED", source_tier=1, confidence="MEDIUM", replace=False,
        )
        documents[doc.id] = doc
        written += 1
    return {"facts": written, "not_located": skipped, "documents": list(documents.values())}
