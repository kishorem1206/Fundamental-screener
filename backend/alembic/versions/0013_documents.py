"""documents: metadata for raw source files stored durably in MinIO —
Architecture v2 Stage 7. The actual bytes live in object storage
(app/infrastructure/storage/minio_client.py); this table is queryable
provenance — which document backs a given company's ingested values, with
a sha256 to detect if a source ever silently changes its file.

Closes a real gap found while scoping this stage: BSE filing PDFs
previously only existed in Redis with a 24h TTL (app/ingestion/bse_client.py)
and were unrecoverable after that — an extracted GNPA/NNPA/CAR value could
never be re-verified against its actual source PDF past a day. NSE annual
reports were already durable on local disk but with no checksum or
queryable metadata; this unifies both into one durable, queryable store.

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id", sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("source", sa.String(), nullable=False),  # matches app/sources/registry.py ids
        sa.Column("document_type", sa.String(), nullable=False),  # ANNUAL_REPORT | QUARTERLY_FILING | XBRL
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("sha256", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="documents_storage_key_uq"),
    )
    op.create_index("documents_company_idx", "documents", ["company_id", "document_type"])


def downgrade() -> None:
    op.drop_index("documents_company_idx", "documents")
    op.drop_table("documents")
