"""Archiving of source documents for the Business Intelligence Engine: every
file a fact is read from is stored in MinIO with a checksum and a
`documents` row carrying what a citation needs (title, date, direct URL).
"""
from __future__ import annotations

import hashlib
import re
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import Document
from app.infrastructure.storage.minio_client import get_document, put_document
from app.logger import logger


def archive(
    db: Session,
    *,
    company_id: str | None,
    source: str,
    document_type: str,
    url: str,
    content: bytes,
    content_type: str,
    title: str,
    period_end: date | None = None,
    published_at: datetime | None = None,
    human_url: str | None = None,
) -> Document | None:
    """Store `content` and return its `documents` row, or None if storage is
    unavailable (the caller then cannot cite the file and must skip its
    facts). The same URL with the same bytes returns the existing row; the
    same URL with changed bytes gets a new row, so an earlier citation keeps
    pointing at what was actually read."""
    sha256 = hashlib.sha256(content).hexdigest()
    existing = db.query(Document).filter_by(url=url, sha256=sha256).first()
    if existing is not None:
        existing.title = existing.title or title
        existing.period_end = existing.period_end or period_end
        existing.published_at = existing.published_at or published_at
        existing.human_url = existing.human_url or human_url
        existing.content_type = existing.content_type or content_type
        return existing

    basename = re.sub(r"[^A-Za-z0-9._-]", "_", url.split("?")[0].rstrip("/").rsplit("/", 1)[-1])[:80] or "document"
    owner = (company_id or "global").replace(":", "_")
    storage_key = f"bie/{owner}/{document_type}/{sha256[:16]}_{basename}"
    if put_document(storage_key, content, content_type=content_type) is None:
        logger.warning("bie: could not archive document", url=url)
        return None
    row = Document(
        id=str(uuid.uuid4()), company_id=company_id, source=source, document_type=document_type,
        url=url, sha256=sha256, storage_key=storage_key, file_size=len(content),
        retrieved_at=datetime.now(timezone.utc), title=title, period_end=period_end,
        published_at=published_at, content_type=content_type, human_url=human_url,
    )
    db.add(row)
    db.flush()
    return row


def content_of(document: Document) -> bytes | None:
    """The archived bytes — what verification re-reads, never the live URL."""
    return get_document(document.storage_key)


def record_link_check(document: Document, status: int | None) -> None:
    document.link_status = status
    document.link_checked_at = datetime.now(timezone.utc)
