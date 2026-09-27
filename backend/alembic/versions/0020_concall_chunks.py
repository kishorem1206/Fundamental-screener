"""Concall Intelligence System, Stage C2 — embedded chunks + vector index.
pgvector was already installed and enabled in this Postgres instance
before this migration (docker-compose's postgres image is `pgvector/
pgvector:pg16`, extension confirmed active via `pg_extension` on
2026-09-13) — `CREATE EXTENSION IF NOT EXISTS` here is a no-op safety net,
not new infrastructure.

Revision ID: 0020
Revises: 0019
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "concall_chunks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transcript_id", sa.String(), sa.ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("utterance_id", sa.String(), sa.ForeignKey("concall_utterances.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("speaker_role", sa.String(), nullable=False),
        sa.Column("section", sa.String(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(4096), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("concall_chunks_company_idx", "concall_chunks", ["company_id"])
    # Real limitation found live-applying this migration (2026-09-14):
    # pgvector's HNSW/IVFFlat indexes cap at 2000 dimensions, but
    # `qwen3-embedding` produces 4096-dim vectors — `CREATE INDEX ... USING
    # hnsw` fails outright ("column cannot have more than 2000 dimensions
    # for hnsw index"). No ANN index is created here as a result. At this
    # system's actual data volume (a few hundred chunks per company, low
    # thousands total for a long while) an exact brute-force `<=>` scan is
    # fast enough — deliberately not adding index complexity (a `halfvec`
    # cast, which pgvector 0.8.6 does support up to 4000 dims, or reducing
    # embedding dimensionality) before it's actually needed.


def downgrade() -> None:
    op.drop_index("concall_chunks_company_idx", "concall_chunks")
    op.drop_table("concall_chunks")
