"""fa_document_chunks: embedded text chunks for semantic retrieval over annual
reports (qwen3-embedding via local Ollama, 4096-dim vectors, pgvector)

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 4096  # qwen3-embedding's native output dimension


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "fa_document_chunks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id",
            sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(), nullable=False),
        # NSE_ANNUAL_REPORT for now — same source-tagging convention as fa_metric_data_points
        sa.Column("source_document", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("context_before", sa.Text(), nullable=True),
        sa.Column("core_text", sa.Text(), nullable=False),
        sa.Column("context_after", sa.Text(), nullable=True),
        sa.Column("embedded_text", sa.Text(), nullable=False),
        # context_before + core_text + context_after, verbatim what was embedded
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "fa_document_chunks_company_source_idx",
        "fa_document_chunks",
        ["company_id", "source_type", "period"],
    )
    # No ANN index (ivfflat/hnsw) — at this scale (~1-2k chunks/company),
    # a plain sequential <=> scan is fast enough and exact, not approximate.


def downgrade() -> None:
    op.drop_index("fa_document_chunks_company_source_idx", "fa_document_chunks")
    op.drop_table("fa_document_chunks")
