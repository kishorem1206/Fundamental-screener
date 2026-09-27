"""Canonical P&L field set (spec Stage 1 — normalization layer).

Screener.in is the only P&L source this codebase ingests (see
`app/ingestion/pnl_history_client.py`), so there is exactly one label
vocabulary to normalize, already collapsed into `_FIELD_MAP` there
(Screener's own field name -> one `pnl_*` ledger key, industrial and
banking vocabularies mapped onto the same key). A second
source-name-to-canonical-name dict-of-lists (as the spec's Stage 1 example
literally shows) would just duplicate that mapping for no reason — this
module instead documents which CANONICAL cascade field each existing
`pnl_*` ledger key represents, and is explicit about which canonical fields
have **no ledger key at all** because Screener's P&L view never reports
them (not merely "unmapped" — structurally absent from the source).
"""
from __future__ import annotations

# canonical cascade field -> pnl_* metric_key already ingested by
# pnl_history_client.py. `None` means: Screener does not report this line
# item in a form this codebase can derive — every reader must treat it as
# unavailable, never approximate it from something else.
CANONICAL_FIELD_TO_METRIC_KEY: dict[str, str | None] = {
    "revenue": "pnl_sales",
    "cogs": None,  # dead end #1 — no material-cost line on Screener's P&L
    "gross_profit": None,  # derived from cogs, so also always unavailable
    "opex": "pnl_expenses",  # Screener's one aggregate expense line
    "employee_cost": None,  # dead end #3 — no cost-line breakdown at all
    "operating_profit": "pnl_operating_profit",  # EBITDA proxy
    "depreciation": "pnl_depreciation",
    "finance_cost": "pnl_interest",
    "other_income": "pnl_other_income",
    "exceptional_items": None,  # not separately broken out by Screener
    "pbt": "pnl_pbt",
    "tax_pct": "pnl_tax_pct",
    "pat": "pnl_net_profit",
    "eps": "pnl_eps",
    "dividend_payout": "pnl_dividend_payout",
}

# Canonical fields with no ledger key, grouped by the underlying reason —
# used by cascade.py/cost_structure.py/earnings_quality.py to attach a
# consistent `reason` string wherever these resolve to null+LOW/UNAVAILABLE.
NO_COGS_BREAKDOWN_REASON = (
    "Screener.in's standard P&L view has no material-cost/COGS line for "
    "any sector checked — Gross Profit/Gross Margin cannot be reliably "
    "derived and is never estimated."
)
NO_COST_LINE_BREAKDOWN_REASON = (
    "Screener.in's P&L reports one aggregate 'Expenses' line with no "
    "employee-cost/material/power-fuel split — only aggregate OPEX-to-"
    "revenue is computable, not a specific cost driver's ratio."
)
NO_EXCEPTIONAL_ITEMS_REASON = (
    "Screener.in's P&L does not separately break out exceptional/"
    "one-off items from Other Income or PBT."
)
