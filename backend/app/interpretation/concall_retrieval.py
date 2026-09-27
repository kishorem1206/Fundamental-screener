"""Embedding + vector retrieval — Concall Intelligence System, Stage C2.
Builds `concall_chunks` from Stage C1's parsed utterances and answers
"what did management say about X" via pgvector cosine similarity — the
doc's explicit division of labor: this module is memory/retrieval only,
never a sentiment or guidance decision (that's Stage C3's job, and it's
Llama's, not this module's).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import ConcallChunk, ConcallTranscript, ConcallUtterance
from app.interpretation.embeddings import embed_text
from app.logger import logger


def embed_transcript(db: Session, transcript_id: str) -> int:
    """Embeds every utterance for one transcript that doesn't already have
    a chunk (idempotent — safe to re-run). Never raises — logs and returns
    the count that actually succeeded on partial failure."""
    already_embedded = {
        row[0] for row in db.query(ConcallChunk.utterance_id).filter_by(transcript_id=transcript_id).all()
    }
    utterances = (
        db.query(ConcallUtterance)
        .filter_by(transcript_id=transcript_id)
        .order_by(ConcallUtterance.sequence)
        .all()
    )
    transcript = db.query(ConcallTranscript).filter_by(id=transcript_id).first()
    if transcript is None:
        return 0

    now = datetime.now(timezone.utc)
    stored = 0
    for u in utterances:
        if u.id in already_embedded:
            continue
        vector = embed_text(u.text)
        if vector is None:
            continue
        db.add(ConcallChunk(
            id=str(uuid.uuid4()), company_id=transcript.company_id, transcript_id=transcript_id,
            utterance_id=u.id, speaker_role=u.speaker_role, section=u.section,
            chunk_text=u.text, embedding=vector, retrieved_at=now,
        ))
        stored += 1
    db.flush()
    logger.info("concall_retrieval: transcript embedded", transcript_id=transcript_id,
                stored=stored, already_had=len(already_embedded))
    return stored


def search_similar_chunks(
    db: Session, company_id: str, query_text: str, top_k: int = 8,
    speaker_role: str | None = None, section: str | None = None,
) -> list[dict]:
    """Cosine-similarity search over one company's embedded chunks — exact
    brute-force scan (see migration 0020's docstring on why there's no ANN
    index yet), fine at this data volume. Never raises — returns []
    on any failure, including an unembeddable query."""
    query_vector = embed_text(query_text)
    if query_vector is None:
        return []

    try:
        stmt = (
            select(ConcallChunk, ConcallChunk.embedding.cosine_distance(query_vector).label("distance"))
            .where(ConcallChunk.company_id == company_id)
        )
        if speaker_role is not None:
            stmt = stmt.where(ConcallChunk.speaker_role == speaker_role)
        if section is not None:
            stmt = stmt.where(ConcallChunk.section == section)
        stmt = stmt.order_by("distance").limit(top_k)
        rows = db.execute(stmt).all()
    except Exception as e:
        logger.warning("concall_retrieval: similarity search failed", company_id=company_id, error=str(e))
        return []

    return [
        {
            "chunk_text": chunk.chunk_text, "speaker_role": chunk.speaker_role,
            "section": chunk.section, "transcript_id": chunk.transcript_id,
            "similarity": round(1 - float(distance), 4),  # cosine_distance -> similarity
        }
        for chunk, distance in rows
    ]
