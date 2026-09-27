"""Premium PDF System, Stages B1-B2 — structured brand facts (extracted
from Screener.in's full Key Points text) and per-topic concall management
tone (a controlled vocabulary, distinct from ManagementGuidance's freeform
metrics).

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_brands",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("ownership", sa.String(), nullable=True),
        sa.Column("market_share_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("market_share_context", sa.String(), nullable=True),
        sa.Column("license_expiry", sa.String(), nullable=True),
        sa.Column("source_excerpt", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="SCREENER"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "brand_name", name="company_brands_company_brand_uq"),
    )
    op.create_index("company_brands_company_idx", "company_brands", ["company_id"])

    op.create_table(
        "concall_topic_sentiment",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("transcript_id", sa.String(), sa.ForeignKey("concall_transcripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("sentiment", sa.String(), nullable=False),
        sa.Column("evidence_utterance_id", sa.String(), sa.ForeignKey("concall_utterances.id", ondelete="SET NULL"), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transcript_id", "topic", name="concall_topic_sentiment_transcript_topic_uq"),
    )
    op.create_index("concall_topic_sentiment_transcript_idx", "concall_topic_sentiment", ["transcript_id"])
    op.create_index("concall_topic_sentiment_company_idx", "concall_topic_sentiment", ["company_id"])


def downgrade() -> None:
    op.drop_index("concall_topic_sentiment_company_idx", "concall_topic_sentiment")
    op.drop_index("concall_topic_sentiment_transcript_idx", "concall_topic_sentiment")
    op.drop_table("concall_topic_sentiment")
    op.drop_index("company_brands_company_idx", "company_brands")
    op.drop_table("company_brands")
