"""Shared helper for the CONSOLIDATED/STANDALONE auto-detect path used by
`pl_intelligence`, `balance_sheet_intelligence` and `cash_flow_intelligence`'s
`compute_*` orchestrators.

Real bug found live on GPT Healthcare (2026-09-20): its Screener CONSOLIDATED
balance sheet and P&L stop at FY2022 (it deconsolidated a subsidiary), while
STANDALONE runs current through FY2026. Every one of these three modules'
auto-detect path only checked "does this statement type have ANY data" —
never which one is more CURRENT — so a stale-but-nonempty CONSOLIDATED side
was always preferred over a current STANDALONE one, silently. This is why
GPT Healthcare's default (no explicit toggle) view showed a 4-year-old
balance sheet with `cash`/`current_liabilities` reading MISSING_INPUT (the
cross-sourced yfinance series only go back to FY2023).

This only applies to the auto-detect path — a company with data on only one
side (`single_statement_source`) and an explicit frontend-toggle request
both bypass this entirely, unchanged.
"""
from __future__ import annotations


def prefer_current_statement_type(latest_period_by_type: dict[str, str | None]) -> str:
    """`latest_period_by_type` is {"CONSOLIDATED": "2022-03-31"|None,
    "STANDALONE": "2026-03-31"|None} — each side's own latest period (ISO
    date strings sort correctly by date). Returns whichever is later;
    CONSOLIDATED wins on a tie or when both are None, preserving this
    codebase's existing "prefer CONSOLIDATED" default for the common case
    where both sides are equally current."""
    consolidated, standalone = latest_period_by_type.get("CONSOLIDATED"), latest_period_by_type.get("STANDALONE")
    if standalone and (not consolidated or standalone > consolidated):
        return "STANDALONE"
    return "CONSOLIDATED"
