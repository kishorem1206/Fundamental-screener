"""Canonical Cash Flow field set (spec §4-5, §17, §24).

Two Screener-sourced ledger layers feed this engine:
- `cf_*` (from `ingest_cash_flow()`, already existed before this engine):
  the 4 top-level totals — operating/investing/financing/net cash flow —
  plus `free_cash_flow`.
- `cf_sched_{op,inv,fin}_*` (from `ingest_cash_flow_schedules()`, Milestone
  1 of this engine): the line-item breakdown behind each top-level total.

Field names vary slightly per company (confirmed live: Lenskart has an
"Exceptional CF items" row Maruti doesn't) — this module documents the
common/expected set; `snapshot.py`'s readers tolerate any additional
company-specific keys gracefully (never require an exact key set).
"""
from __future__ import annotations

# canonical field -> cf_sched_op_* ledger key suffix (after the shared
# "cf_sched_op_" prefix `screener_client.py` writes).
CFO_SCHEDULE_FIELDS: dict[str, str] = {
    "operating_profit": "profit_from_operations",
    "receivables_change": "receivables",
    "inventory_change": "inventory",
    "payables_change": "payables",
    "loans_advances_change": "loans_advances",
    "other_wc_change": "other_wc_items",
    "working_capital_change": "working_capital_changes",
    "taxes_paid": "direct_taxes",
    "exceptional_items": "exceptional_cf_items",  # not present for every company
}

CFI_SCHEDULE_FIELDS: dict[str, str] = {
    "fixed_assets_purchased": "fixed_assets_purchased",
    "fixed_assets_sold": "fixed_assets_sold",
    "investments_purchased": "investments_purchased",
    "investments_sold": "investments_sold",
    "interest_received": "interest_received",
    "dividends_received": "dividends_received",
    "share_redemption": "redemp_n_canc_of_shares",
    "acquisitions": "acquisition_of_companies",
    "other_investing": "other_investing_items",
}

CFF_SCHEDULE_FIELDS: dict[str, str] = {
    "borrowings_raised": "proceeds_from_borrowings",
    "borrowings_repaid": "repayment_of_borrowings",
    "interest_paid": "interest_paid_fin",
    "dividends_paid": "dividends_paid",
    "financial_liabilities": "financial_liabilities",
    "other_financing": "other_financing_items",
}

# canonical field -> cf_* top-level ledger key (already ingested before
# this engine existed).
TOP_LEVEL_FIELDS: dict[str, str] = {
    "cfo": "operating_cash_flow",
    "cfi": "investing_cash_flow",
    "cff": "financing_cash_flow",
    "net_cash_flow": "net_cash_flow",
    "free_cash_flow": "free_cash_flow",
}

# Fields the spec's master data model names that this app still has no
# source for — from any provider. Every dependent metric/flag resolves to
# null + a MISSING_INPUT/SOURCE_REQUIRED coverage status, never estimated.
NO_FX_ADJUSTMENT_REASON = (
    "No schedule line or top-level field carries an FX/currency-"
    "translation cash adjustment — confirmed absent for a Rupee-only "
    "domestic entity; the cash bridge reconciles without one for those "
    "companies. Genuinely multi-currency consolidated entities may show a "
    "real reconciliation gap here rather than a data gap."
)
NO_TRUE_BUYBACK_LINE_REASON = (
    "Screener's financing schedule has no line distinct from dividends "
    "for share buybacks specifically — 'Redemption/Cancellation of Shares' "
    "(investing schedule) is the closest proxy but conflates buybacks with "
    "other capital-reduction events, so it's surfaced as-is, never "
    "relabeled as a clean buyback figure."
)
NO_CREDIT_SALES_PURCHASES_REASON = (
    "Inherited from the Balance Sheet Analysis Engine's own documented "
    "gap — neither Screener nor yfinance separate credit sales/purchases "
    "from total revenue/purchases."
)
NO_TRUE_GROSS_MARGIN_REASON = (
    "Inherited from the P&L Analysis Engine's own documented dead end — "
    "Screener's P&L view has no material-cost/COGS line for any sector."
)

STRUCTURALLY_ABSENT: dict[str, str] = {
    "fx_adjustment": NO_FX_ADJUSTMENT_REASON,
    "true_buyback_line": NO_TRUE_BUYBACK_LINE_REASON,
    "credit_sales": NO_CREDIT_SALES_PURCHASES_REASON,
    "credit_purchases": NO_CREDIT_SALES_PURCHASES_REASON,
    "gross_margin": NO_TRUE_GROSS_MARGIN_REASON,
}
