"""Technical screener tables — the Stock screener app merged into this one.

Both apps always shared one database, so on the existing database every one of
these tables is already there (created by the old app's own migrations) and
this revision changes nothing. It exists so that a database built from this
app's migrations alone ends up with them too.

Revision ID: 0037
Revises: 0036
Create Date: 2026-10-05
"""
from alembic import op

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None

TABLES = (
    "universes", "universe_memberships", "indicator_definitions", "screen_definitions",
    "chat_sessions", "chat_messages", "index_categories", "nifty_indices", "ingestion_runs",
    "source_files", "staging_index_constituents", "index_constituents", "data_provenance_log",
)


def upgrade() -> None:
    from app.infrastructure.database.models import Base

    op.execute("ALTER TABLE stocks ADD COLUMN IF NOT EXISTS kite_instrument_token BIGINT")
    op.execute("ALTER TABLE stocks ADD COLUMN IF NOT EXISTS tradingview_symbol VARCHAR")
    Base.metadata.create_all(op.get_bind(), tables=[Base.metadata.tables[t] for t in TABLES], checkfirst=True)


def downgrade() -> None:
    # The tables predate this revision on every database that ran the old app,
    # and hold saved screens and chat history: never dropped from here.
    pass
