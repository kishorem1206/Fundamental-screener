"""shareholding + governance_events: Architecture v2 Stage 3 — the
integrity/governance layer. Sourced from NSE's shareholding-pattern API
(app/ingestion/shareholding_client.py): promoter_pct/public_pct from
/api/corporate-share-holdings-master, pledge_pct parsed out of each
quarter's linked XBRL filing. governance_events holds deterministic,
evidence-backed flags derived from shareholding trends (promoter holding
declining, pledge present/increasing) — never an LLM-inferred conclusion,
per Architecture v2 chatgpt.md's "every flag must point to evidence" rule.

Deliberately two tables, not the four named in the original roadmap sketch:
pledge_pct lives as a column on `shareholding` rather than a separate
`pledges` table (same filing, same quarter — a join table would be pure
overhead), and `promoter_transactions` (individual buy/sell disclosures) is
out of scope here entirely — it's a different NSE filing type (insider
trading / SAST disclosures), deferred rather than half-built.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shareholding",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id", sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("period_end", sa.String(), nullable=False),  # ISO date string, matches fa_metric_data_points.period
        sa.Column("promoter_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("public_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("pledge_pct", sa.Numeric(6, 3), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period_end", name="shareholding_company_period_uq"),
    )
    op.create_index("shareholding_company_idx", "shareholding", ["company_id", "period_end"])

    op.create_table(
        "governance_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "company_id", sa.String(),
            sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        # PROMOTER_HOLDING_DECLINE | PLEDGE_PRESENT | PLEDGE_INCREASE
        sa.Column("severity", sa.String(), nullable=False),  # HIGH | MEDIUM | LOW
        sa.Column("event_date", sa.String(), nullable=False),  # period_end this event was detected on
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="NSE_SHAREHOLDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "event_type", "event_date", name="governance_events_dedup_uq"),
    )
    op.create_index("governance_events_company_idx", "governance_events", ["company_id"])


def downgrade() -> None:
    op.drop_index("governance_events_company_idx", "governance_events")
    op.drop_table("governance_events")
    op.drop_index("shareholding_company_idx", "shareholding")
    op.drop_table("shareholding")
