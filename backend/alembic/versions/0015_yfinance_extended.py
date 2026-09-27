"""Yahoo Finance extended fundamental data — every "available, unused" item
from the 2026-09-13 audit of yfinance's Ticker API surface, all sourced
from the same yfinance object so they share one ingestion module
(app/ingestion/yfinance_extended_client.py):
  - forward_estimates: consensus EPS/revenue estimates by period, and
    growth estimates (stock vs. index) — nothing like this existed before.
  - insider_activity: dated, named insider transactions (distinct from
    Stage 3's NSE shareholding-pattern aggregate %, which is holding
    percentages, not individual transactions).
  - corporate_actions: dividend/split history.
  - company_news: recent headlines with source attribution.
  - earnings_calendar: next earnings date + expected EPS/revenue range —
    "future schedules" per explicit request.

analyst_consensus (migration 0012) is reused as-is for Yahoo Finance's own
analyst targets/ratings — its `source` column already supports multiple
providers side by side (IndMoney vs. YAHOO_FINANCE), no schema change
needed; every reader must keep attributing each row to its actual source,
never blending sources into one number.

company_summary (migration 0014) gets a `governance_risk` JSON column for
yfinance's auditRisk/boardRisk/compensationRisk/shareHolderRightsRisk/
overallRisk scores — five small numbers, not worth a whole table.

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("company_summary", sa.Column("governance_risk", sa.JSON(), nullable=True))

    op.create_table(
        "forward_estimates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_type", sa.String(), nullable=False),  # eps | revenue | growth
        sa.Column("period_label", sa.String(), nullable=False),  # 0q | +1q | 0y | +1y | LTG
        sa.Column("avg", sa.Numeric(20, 4), nullable=True),
        sa.Column("low", sa.Numeric(20, 4), nullable=True),
        sa.Column("high", sa.Numeric(20, 4), nullable=True),
        sa.Column("num_analysts", sa.Integer(), nullable=True),
        sa.Column("growth_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="YAHOO_FINANCE"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "metric_type", "period_label", name="forward_estimates_uq"),
    )
    op.create_index("forward_estimates_company_idx", "forward_estimates", ["company_id"])

    op.create_table(
        "insider_activity",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_date", sa.String(), nullable=False),
        sa.Column("insider_name", sa.String(), nullable=True),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("transaction_text", sa.Text(), nullable=True),
        sa.Column("shares", sa.Numeric(20, 2), nullable=True),
        sa.Column("value", sa.Numeric(20, 2), nullable=True),
        sa.Column("ownership_type", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="YAHOO_FINANCE"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "transaction_date", "insider_name", "shares", name="insider_activity_uq"),
    )
    op.create_index("insider_activity_company_idx", "insider_activity", ["company_id", "transaction_date"])

    op.create_table(
        "corporate_actions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_date", sa.String(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),  # DIVIDEND | SPLIT
        sa.Column("value", sa.Numeric(20, 6), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="YAHOO_FINANCE"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "action_date", "action_type", name="corporate_actions_uq"),
    )
    op.create_index("corporate_actions_company_idx", "corporate_actions", ["company_id", "action_date"])

    op.create_table(
        "company_news",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="YAHOO_FINANCE"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "url", name="company_news_uq"),
    )
    op.create_index("company_news_company_idx", "company_news", ["company_id", "published_at"])

    op.create_table(
        "earnings_calendar",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("next_earnings_date", sa.String(), nullable=True),
        sa.Column("ex_dividend_date", sa.String(), nullable=True),
        sa.Column("expected_eps_avg", sa.Numeric(14, 4), nullable=True),
        sa.Column("expected_eps_low", sa.Numeric(14, 4), nullable=True),
        sa.Column("expected_eps_high", sa.Numeric(14, 4), nullable=True),
        sa.Column("expected_revenue_avg", sa.Numeric(20, 2), nullable=True),
        sa.Column("expected_revenue_low", sa.Numeric(20, 2), nullable=True),
        sa.Column("expected_revenue_high", sa.Numeric(20, 2), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="YAHOO_FINANCE"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("earnings_calendar")
    op.drop_index("company_news_company_idx", "company_news")
    op.drop_table("company_news")
    op.drop_index("corporate_actions_company_idx", "corporate_actions")
    op.drop_table("corporate_actions")
    op.drop_index("insider_activity_company_idx", "insider_activity")
    op.drop_table("insider_activity")
    op.drop_index("forward_estimates_company_idx", "forward_estimates")
    op.drop_table("forward_estimates")
    op.drop_column("company_summary", "governance_risk")
