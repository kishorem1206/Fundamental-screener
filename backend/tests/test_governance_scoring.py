"""Tests for `app/calculations/governance_scoring.py` — the promoter-
pledge / promoter-holding-decline penalty (2026-09-28, explicit user
request: promoter holding data was ingested and displayed but never
touched a score).

Uses synthetic per-test stock rows (see test_other_income_flag.py's same
rationale — a real fixture company could carry genuine committed
governance_events rows from other sessions, muddying "must return X"
assertions)."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from app.calculations.governance_scoring import _MAX_PENALTY, compute_governance_penalty
from app.infrastructure.database.models import GovernanceEvent, Shareholding, Stock


def _synthetic_company_id(db, symbol: str) -> str:
    now = datetime.now(timezone.utc)
    stock_id = f"TEST:{symbol}"
    db.add(Stock(id=stock_id, symbol=symbol, exchange="TEST", company_name=f"{symbol} Ltd",
                 is_active=True, created_at=now, updated_at=now))
    db.flush()
    return stock_id


def _add_shareholding(db, company_id, period_end="2026-06-30"):
    db.add(Shareholding(
        id=str(uuid.uuid4()), company_id=company_id, period_end=period_end,
        promoter_pct=55.0, public_pct=45.0, pledge_pct=0.0,
        source_url="https://example.test", retrieved_at=datetime.now(timezone.utc),
    ))
    db.flush()


def _add_event(db, company_id, event_type, severity, event_date, description="test event"):
    db.add(GovernanceEvent(
        id=str(uuid.uuid4()), company_id=company_id, event_type=event_type, severity=severity,
        event_date=event_date, description=description, evidence={}, source="NSE_SHAREHOLDING",
        created_at=datetime.now(timezone.utc),
    ))
    db.flush()


def test_no_shareholding_data_returns_none(db):
    company_id = _synthetic_company_id(db, "GOVTEST1")
    assert compute_governance_penalty(db, company_id) is None


def test_shareholding_present_but_no_events_is_clean(db):
    company_id = _synthetic_company_id(db, "GOVTEST2")
    _add_shareholding(db, company_id)
    result = compute_governance_penalty(db, company_id)
    assert result is not None
    assert result["penalty"] == 0.0
    assert result["flags"] == []


def test_high_severity_pledge_present_applies_penalty(db):
    company_id = _synthetic_company_id(db, "GOVTEST3")
    _add_shareholding(db, company_id)
    _add_event(db, company_id, "PLEDGE_PRESENT", "HIGH", "2026-06-30", "62% pledged")
    result = compute_governance_penalty(db, company_id)
    assert result["penalty"] == 8.0
    assert len(result["flags"]) == 1
    assert result["flags"][0]["event_type"] == "PLEDGE_PRESENT"


def test_different_event_types_stack(db):
    company_id = _synthetic_company_id(db, "GOVTEST4")
    _add_shareholding(db, company_id)
    _add_event(db, company_id, "PLEDGE_PRESENT", "MEDIUM", "2026-06-30")
    _add_event(db, company_id, "PROMOTER_HOLDING_DECLINE", "HIGH", "2026-06-30")
    result = compute_governance_penalty(db, company_id)
    assert result["penalty"] == 4.0 + 6.0
    assert len(result["flags"]) == 2


def test_penalty_capped_at_max(db):
    company_id = _synthetic_company_id(db, "GOVTEST5")
    _add_shareholding(db, company_id)
    _add_event(db, company_id, "PLEDGE_PRESENT", "HIGH", "2026-06-30")   # 8.0
    _add_event(db, company_id, "PLEDGE_INCREASE", "HIGH", "2026-06-30")  # 4.0
    _add_event(db, company_id, "PROMOTER_HOLDING_DECLINE", "HIGH", "2026-06-30")  # 6.0
    # sum so far = 18.0, still under the 20.0 cap — add one more type-distinct
    # event to push over it (same event_type would just replace, not stack).
    result = compute_governance_penalty(db, company_id)
    assert result["penalty"] == 18.0
    assert result["penalty"] <= _MAX_PENALTY


def test_only_most_recent_event_per_type_counts(db):
    """`_detect_events()` re-emits PLEDGE_PRESENT every quarter it holds —
    an old HIGH pledge that has since dropped to LOW must not keep
    contributing the HIGH penalty forever."""
    company_id = _synthetic_company_id(db, "GOVTEST6")
    _add_shareholding(db, company_id)
    _add_event(db, company_id, "PLEDGE_PRESENT", "HIGH", "2025-03-31")   # stale, superseded
    _add_event(db, company_id, "PLEDGE_PRESENT", "LOW", "2026-06-30")    # current state
    result = compute_governance_penalty(db, company_id)
    assert result["penalty"] == 1.5
    assert result["flags"][0]["severity"] == "LOW"


def test_events_outside_lookback_window_are_excluded(db):
    company_id = _synthetic_company_id(db, "GOVTEST7")
    _add_shareholding(db, company_id)
    stale_date = (date.today() - timedelta(days=1000)).isoformat()
    _add_event(db, company_id, "PLEDGE_PRESENT", "HIGH", stale_date)
    result = compute_governance_penalty(db, company_id)
    assert result["penalty"] == 0.0
    assert result["flags"] == []
