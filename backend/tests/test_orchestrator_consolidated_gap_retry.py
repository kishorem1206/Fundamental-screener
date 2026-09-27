"""Tests for `orchestrator._has_consolidated_rows()` — the gate that
decides whether a dual STANDALONE/CONSOLIDATED ingestion call gets the
long cache TTL or the short `_CONSOLIDATED_GAP_RETRY_TTL` retry window.

2026-09-22: this gating was extended to `ingest_balance_sheet`,
`ingest_cash_flow` and `ingest_quarterly_results` (previously only
`ingest_pnl_history`/`ingest_cash_flow_schedules`/`ingest_ratios` had it),
after the same "STANDALONE landed, CONSOLIDATED silently didn't, and the
cache key locked the gap in for a full day" bug turned up on GNFC for
`pnl_sales` specifically and the user asked for every ingestion path to be
checked, not just the one that happened to get noticed.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.pipeline.orchestrator import _has_consolidated_rows


def _row(statement_type):
    return SimpleNamespace(statement_type=statement_type)


def test_true_when_any_row_is_consolidated():
    rows = [_row("STANDALONE"), _row("CONSOLIDATED"), _row("STANDALONE")]
    assert _has_consolidated_rows(rows) is True


def test_false_when_only_standalone_present():
    """The exact GNFC shape: the dual-fetch loop succeeded for STANDALONE
    but CONSOLIDATED silently came back with nothing."""
    rows = [_row("STANDALONE"), _row("STANDALONE")]
    assert _has_consolidated_rows(rows) is False


def test_false_for_empty_list():
    assert _has_consolidated_rows([]) is False


def test_false_for_none():
    assert _has_consolidated_rows(None) is False


def test_ignores_rows_with_no_statement_type_attribute():
    rows = [SimpleNamespace(other_field=1), _row("CONSOLIDATED")]
    assert _has_consolidated_rows(rows) is True
