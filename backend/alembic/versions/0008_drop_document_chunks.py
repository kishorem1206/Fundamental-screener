"""Drop fa_document_chunks: the qwen3-embedding/Ollama/pgvector RAG system it
backed was removed (see annual_report_ingestion.py's module docstring) —
Screener.in scraping now covers most of what semantic retrieval over annual
reports was built to reach, more directly and reliably, without the slow
NSE/Ollama-availability-dependent indexing step that stalled the pipeline.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-10
"""
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("fa_document_chunks_company_source_idx", "fa_document_chunks")
    op.drop_table("fa_document_chunks")


def downgrade() -> None:
    raise NotImplementedError(
        "The RAG system this table backed was deliberately removed; "
        "recreate via alembic/versions/0004_document_chunks.py if ever needed again."
    )
