"""Raw source document provenance — Architecture v2 Stage 7. Metadata lives
in Postgres (documents table); bytes live in MinIO
(app/infrastructure/storage/minio_client.py).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Document

router = APIRouter(prefix="/api/documents")


def _row_to_dict(row: Document) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "document_type": row.document_type,
        "url": row.url,
        "sha256": row.sha256,
        "file_size": row.file_size,
        "retrieved_at": row.retrieved_at.isoformat(),
    }


@router.get("/{company_id:path}/{document_id}/download")
def download_document(company_id: str, document_id: str):
    """Fetch one document's actual bytes back out of MinIO. Registered
    BEFORE list_documents deliberately — a `:path` converter route matches
    greedily, so the more specific route must come first or FastAPI never
    reaches it (confirmed the hard way: list_documents was swallowing every
    /download request into its own company_id parameter)."""
    from app.infrastructure.storage.minio_client import get_document

    db = get_db()
    try:
        row = db.query(Document).filter_by(id=document_id, company_id=company_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Document not found")
        content = get_document(row.storage_key)
        if content is None:
            raise HTTPException(status_code=502, detail="Document metadata exists but bytes are unreachable in storage")
        return Response(content=content, media_type="application/pdf")
    finally:
        db.close()


@router.get("/{company_id:path}")
def list_documents(company_id: str):
    """Every raw source document on file for one company, newest first."""
    db = get_db()
    try:
        rows = (
            db.query(Document).filter_by(company_id=company_id)
            .order_by(Document.retrieved_at.desc()).all()
        )
        return {"company_id": company_id, "documents": [_row_to_dict(r) for r in rows]}
    finally:
        db.close()
