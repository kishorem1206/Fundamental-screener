"""Business Intelligence Engine, phase 1 — `bie_facts` (sourced facts with a
document, direct URL and page/data-file locator) and citation columns on
`documents` (title, period, publication date, readable URL, link check).
`documents.company_id` becomes nullable so sector- and economy-level sources
can be archived too.

Revision ID: 0035
Revises: 0034
Create Date: 2026-10-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("documents", "company_id", existing_type=sa.String(), nullable=True)
    op.add_column("documents", sa.Column("title", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("period_end", sa.Date(), nullable=True))
    op.add_column("documents", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("content_type", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("human_url", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("link_status", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("link_checked_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "bie_facts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("fact_type", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("dimension", sa.String(), nullable=False, server_default=""),
        sa.Column("period_type", sa.String(), nullable=False, server_default="NA"),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("statement_type", sa.String(), nullable=False, server_default="NA"),
        sa.Column("value_num", sa.Numeric(28, 6), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("nature", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("locator_type", sa.String(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("locator", sa.Text(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("extraction_method", sa.String(), nullable=False),
        sa.Column("source_tier", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=True),
        sa.Column("formula", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(), nullable=False, server_default="UNVERIFIED"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("bie_facts_company_idx", "bie_facts", ["company_id", "fact_type", "key"])
    op.create_index("bie_facts_sector_idx", "bie_facts", ["scope", "sector", "fact_type"])
    op.create_index("bie_facts_document_idx", "bie_facts", ["document_id"])


def downgrade() -> None:
    op.drop_index("bie_facts_document_idx", table_name="bie_facts")
    op.drop_index("bie_facts_sector_idx", table_name="bie_facts")
    op.drop_index("bie_facts_company_idx", table_name="bie_facts")
    op.drop_table("bie_facts")
    for col in ("link_checked_at", "link_status", "human_url", "content_type", "published_at", "period_end", "title"):
        op.drop_column("documents", col)
    op.alter_column("documents", "company_id", existing_type=sa.String(), nullable=False)
