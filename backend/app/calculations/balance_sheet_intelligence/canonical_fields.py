"""Canonical Balance Sheet field set (spec §6-8 master data model).

Two sources feed this engine, per the user's explicit blend decision: Screener
(`app/ingestion/screener_client.py::ingest_balance_sheet()`) for the coarse
balance-sheet-house/net-worth/leverage/archetype layer, and the existing
yfinance-sourced `app/calculations/engine.py::MetricsCalculator` for
working-capital-specific fields Screener's condensed view doesn't separate
out. This module documents both mappings, and — just as important — the
fields no source has at all, so nothing downstream ever estimates them.
"""
from __future__ import annotations

# canonical field -> Screener's own `balance_sheet()` row key (already
# ingested by `screener_client.ingest_balance_sheet()`). Screener's "Total
# Liabilities" already sums to `total_assets` by construction — confirmed
# live for Maruti (148880 == 148880) — it's a sources-of-funds total that
# INCLUDES equity, not a pure external-liabilities figure; downstream code
# must subtract equity out to get external liabilities (see leverage.py's
# `liabilities_to_equity`).
CANONICAL_FIELD_TO_SCREENER_KEY: dict[str, str | None] = {
    "equity_capital": "equity_capital",
    "reserves": "reserves",
    "borrowings": "borrowings",  # HDFC-Bank-style filings use singular "borrowing" — see _BORROWINGS_KEY_ALIASES
    "deposits": "deposits",  # bank-only; absent for non-financial companies
    "other_liabilities": "other_liabilities",
    "total_liabilities": "total_liabilities",  # == sources of funds, == total_assets by construction
    "fixed_assets": "fixed_assets",  # NET PPE — Screener never separates gross block/accumulated depreciation
    "capital_work_in_progress": "capital_work_in_progress",
    "investments": "investments",
    "other_assets": "other_assets",  # catch-all: cash+receivables+inventory+everything else non-fixed/non-investment
    "total_assets": "total_assets",
}

# Screener's balance-sheet field-name convention isn't fully consistent
# across company types — confirmed live: HDFC Bank's row uses the singular
# "borrowing" where every non-bank company checked uses "borrowings".
BORROWINGS_KEY_ALIASES = ("borrowings", "borrowing")

# canonical field -> yfinance-sourced key already read by
# `engine.py::MetricsCalculator._bal_series()`. These are genuinely more
# granular than anything Screener exposes — the whole reason the user's
# blend decision keeps them as the working-capital source of truth instead
# of switching to Screener's latest-only `.ratios()` endpoint.
CANONICAL_FIELD_TO_YFINANCE_KEY: dict[str, str] = {
    "cash": "cash",
    "receivables": "receivables",
    "inventory": "inventory",
    "payables": "payables",
    "current_assets": "current_assets",
    "current_liabilities": "current_liabilities",
    "total_equity": "total_equity",
    "total_debt": "total_debt",
}

# canonical field -> the new cf_*-prefixed Screener cash-flow ledger keys
# (Milestone 1, `screener_client.ingest_cash_flow()`).
CANONICAL_FIELD_TO_CASH_FLOW_KEY: dict[str, str] = {
    "operating_cash_flow": "cf_operating_cash_flow",
    "investing_cash_flow": "cf_investing_cash_flow",
    "financing_cash_flow": "cf_financing_cash_flow",
    "net_cash_flow": "cf_net_cash_flow",
    "free_cash_flow": "cf_free_cash_flow",
}

# canonical field -> the bs_ratio_*-prefixed Screener ledger keys
# (`screener_client.ingest_ratios()`). Full multi-year history is ingested
# (every year Screener's Ratios tab has on record, via openscreener's
# `ratios_history()`) and read as such by `snapshot.screener_ratios_history()`
# — NOT latest-period-only (that was a real bug, fixed 2026-09-23).
CANONICAL_FIELD_TO_RATIOS_KEY: dict[str, str] = {
    "debtor_days": "bs_ratio_debtor_days",
    "inventory_days": "bs_ratio_inventory_days",
    "days_payable": "bs_ratio_days_payable",
    "cash_conversion_cycle": "bs_ratio_cash_conversion_cycle",
    "working_capital_days": "bs_ratio_working_capital_days",
    "roce_percent": "bs_ratio_roce_percent",
    "roe_percent": "bs_ratio_roe_percent",  # banks only — Screener's ratios() page has no roce_percent for a bank
}

# Fields the spec's master data model names that this app has NO source for
# — from any provider, not just Screener. Every dependent metric/flag must
# resolve to null + a MISSING_INPUT/SOURCE_REQUIRED coverage status here,
# never estimated. Grouped with a shared reason string per `coverage.py`'s
# consumption pattern (mirrors `pl_intelligence/canonical_fields.py`'s
# `NO_COGS_BREAKDOWN_REASON` style).
NO_AGING_DATA_REASON = (
    "Neither Screener.in nor yfinance expose AR/inventory/AP aging buckets "
    "(0-30/31-60/61-90/90+ days) anywhere — this needs annual-report note "
    "disclosures this app doesn't ingest. Aging-dependent diagnostics "
    "(receivables collection risk, slow-moving inventory, past-due "
    "payables) are never estimated from the closing balance alone."
)
NO_DEBT_MATURITY_REASON = (
    "No source gives a debt maturity schedule (<1Y/1-3Y/3-5Y/5-10Y/10Y+), "
    "and Screener's `borrowings` is one undifferentiated figure with no "
    "short-term-vs-long-term split at all. Debt-maturity-pressure "
    "diagnostics are never computed."
)
NO_RELATED_PARTY_REASON = (
    "Related-party loans / inter-corporate deposits require annual-report "
    "related-party-transaction note disclosures this app doesn't ingest — "
    "structurally absent, not merely unmapped."
)
NO_CONTINGENT_LIABILITIES_REASON = (
    "Contingent liabilities require annual-report note disclosures this "
    "app doesn't ingest — never estimated from the balance sheet alone."
)
NO_GROSS_PPE_REASON = (
    "Screener's `fixed_assets` is net PPE only — no gross block or "
    "accumulated depreciation line anywhere. Capex-linked diagnostics that "
    "need gross block growth substitute net fixed-assets growth instead, "
    "tagged confidence=LOW and explicitly labeled as a deviation."
)
NO_DISTINCT_ACCRUALS_REASON = (
    "Accrued expenses and deferred revenue are folded into Screener's "
    "aggregate `other_liabilities` line with no way to separate them out."
)
NO_CREDIT_SALES_PURCHASES_REASON = (
    "Neither source separates credit sales/credit purchases from total "
    "revenue/total purchases, and neither gives average (only closing) "
    "receivable/payable balances. DSO/DPO here use "
    "CLOSING_BALANCE_OVER_TOTAL_REVENUE — the spec's own documented "
    "fallback methodology, disclosed on every output, never presented as "
    "the average-balance/credit-sales formula."
)
NO_ST_LT_DEBT_SPLIT_REASON = (
    "Screener's `borrowings` is one undifferentiated figure — no "
    "short-term-vs-long-term split exists to build separate leverage House "
    "rows from."
)

STRUCTURALLY_ABSENT: dict[str, str] = {
    "ar_aging": NO_AGING_DATA_REASON,
    "inventory_aging": NO_AGING_DATA_REASON,
    "ap_aging": NO_AGING_DATA_REASON,
    "debt_maturity_schedule": NO_DEBT_MATURITY_REASON,
    "short_term_vs_long_term_debt_split": NO_ST_LT_DEBT_SPLIT_REASON,
    "related_party_loans": NO_RELATED_PARTY_REASON,
    "contingent_liabilities": NO_CONTINGENT_LIABILITIES_REASON,
    "gross_ppe": NO_GROSS_PPE_REASON,
    "accumulated_depreciation": NO_GROSS_PPE_REASON,
    "accrued_expenses": NO_DISTINCT_ACCRUALS_REASON,
    "deferred_revenue": NO_DISTINCT_ACCRUALS_REASON,
    "credit_sales": NO_CREDIT_SALES_PURCHASES_REASON,
    "credit_purchases": NO_CREDIT_SALES_PURCHASES_REASON,
}

# Financial institutions Screener also reports `deposits` for (bank-sector
# extra field, confirmed live for HDFC Bank) — sector_routing.py checks
# sector name against this set to decide whether to look for it.
FINANCIAL_INSTITUTION_SECTORS = {"Banks", "NBFCs", "Insurance", "Financial Services"}

# Sectors where physical inventory is a material, core part of the balance
# sheet story — user's explicit scope call (2026-09-20, prompted by GPT
# Healthcare, a hospital, showing "Inventory Turnover" as a data gap
# alongside genuinely missing items like AR aging): "everyone except
# inventory-core sectors" gets `inventory_turnover` relabeled NOT_APPLICABLE
# rather than MISSING_INPUT — see sector_routing.is_inventory_material().
# DIO/DPO/CCC (proxy-based, already PARTIAL not a hard gap) are untouched by
# this; only the COGS-dependent `inventory_turnover` metric changes label,
# since COGS itself is structurally absent from every source this app uses
# regardless of sector (STRUCTURALLY_ABSENT above) — the label change is
# about materiality, not about newly-available data.
INVENTORY_MATERIAL_SECTORS = {
    "Retail", "Fast Moving Consumer Goods", "Automobile", "Auto Ancillaries",
    "Capital Goods", "Industrials", "Defence", "Construction",
    "Chemicals", "Specialty Chemicals", "Cement", "Metals", "Mining",
    "Forest Materials", "Consumer Durables", "Textiles", "Electronics",
    "Oil & Gas", "Power", "Real Estate",
}

# The explicit "exempt" side of the same call — every other CURRENTLY-KNOWN
# sector_name (see `app/sectors/registry.py`'s full list) where inventory is
# real-but-immaterial or structurally absent. Kept as its own explicit set
# (not just "not in INVENTORY_MATERIAL_SECTORS") so a sector this app adds
# LATER and hasn't been reviewed for yet defaults to the conservative,
# gap-preserving answer (True, in `is_inventory_material()`) instead of
# silently getting exempted just for being unrecognized — this module's
# whole purpose is to never silently hide a gap.
INVENTORY_LIGHT_SECTORS = {
    "Aviation", "Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans", "Insurance",
    "Financial Services", "Fintech", "Hotels & Restaurants", "Information Technology", "Logistics",
    "Media & Entertainment", "Diversified", "Renewable Energy", "Services", "Telecom", "Utilities",
    "Infrastructure",
}

# Healthcare covers both hospital/diagnostics operators (no material
# inventory — drugs/consumables are a small operating cost, not a
# balance-sheet story) and pharma/device manufacturers (raw materials/WIP/
# finished goods ARE material) under one sector_name — `basic_industry`
# (NSE's own taxonomy; confirmed live values for sector="Healthcare":
# Biotechnology, Healthcare Research/Analytics & Technology, Healthcare
# Service Provider, Hospital, Medical Equipment & Supplies, Pharmaceuticals)
# disambiguates; see is_inventory_material().
HEALTHCARE_MANUFACTURING_BASIC_INDUSTRIES = {"Pharmaceuticals", "Biotechnology", "Medical Equipment & Supplies"}
