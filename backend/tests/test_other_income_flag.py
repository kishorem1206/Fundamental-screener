"""Tests for `app/quick_analysis/other_income_flag.py` — the other-income
dependency signal (2026-09-28, explicit user request, surfaced by I S T
Limited: Other Income was 78-88% of PBT across its last 3 quarters, and
Yahoo's own quarterly data was perfectly sufficient for growth scoring, so
`screener_quarterly_fallback.py`'s growth fallback never triggered — this
check needs its OWN ingest-on-miss trigger, not a free ride on that one).

Uses synthetic per-test stock rows (a real ledger-populated fixture like
NSE:MARUTI carries genuine committed data from other tests/analyses this
session, which would let a "must return None" test pass for the wrong
reason if it silently fell through to that real data instead of the
synthetic rows this test sets up)."""
from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock
from app.quick_analysis import other_income_flag as oif


def _synthetic_company_id(db, symbol: str) -> str:
    now = datetime.now(timezone.utc)
    stock_id = f"TEST:{symbol}"
    db.add(Stock(id=stock_id, symbol=symbol, exchange="TEST", company_name=f"{symbol} Ltd",
                 is_active=True, created_at=now, updated_at=now))
    db.flush()
    return stock_id


def _insert(db, company_id, metric_key, period, value, statement_type="CONSOLIDATED"):
    metric_store.insert_metric_value(
        db, company_id=company_id, metric_key=metric_key, period=period, value=value,
        unit="cr", statement_type=statement_type, source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )


def test_reads_the_ledger_first_and_skips_ingestion_when_already_populated(monkeypatch, db):
    company_id = _synthetic_company_id(db, "OITEST1")
    _insert(db, company_id, "qtr_other_income", "2026-06-30", 87.0)
    _insert(db, company_id, "qtr_pbt", "2026-06-30", 99.0)

    def _boom(*a, **k):
        raise AssertionError("must not fetch Screener when the ledger already has enough data")
    monkeypatch.setattr("openscreener.Stock", _boom)

    result = oif.compute_other_income_dependency(db, company_id, "OITEST1")
    assert result is not None
    assert result["ratio"] == round(87.0 / 99.0, 3)
    assert result["flagged"] is True
    assert result["period_type"] == "quarterly"


def test_ingests_on_a_genuine_ledger_miss_then_reads_it_back(monkeypatch, db):
    class _FakeStock:
        def __init__(self, symbol, consolidated):
            assert consolidated is True

        def quarterly_results(self):
            return [{"date": "Jun 2026", "sales": 683.83, "expenses": 245.85,
                      "operating_profit": 16.0, "other_income": 87.0, "profit_before_tax": 99.0,
                      "net_profit": -4.06, "eps": -0.31}]

    monkeypatch.setattr("openscreener.Stock", _FakeStock)
    monkeypatch.setattr("app.ingestion.screener_client._SCREENER_REQUEST_DELAY_SECONDS", 0, raising=False)
    company_id = _synthetic_company_id(db, "OITEST2")

    result = oif.compute_other_income_dependency(db, company_id, "OITEST2")
    assert result is not None
    assert result["flagged"] is True
    # confirms persistence: the ingested rows landed in the ledger
    rows = metric_store.get_metric_history(db, company_id, "qtr_other_income", statement_type="CONSOLIDATED")
    assert len(rows) >= 1


def test_below_threshold_is_not_flagged(db):
    company_id = _synthetic_company_id(db, "OITEST3")
    _insert(db, company_id, "qtr_other_income", "2026-06-30", 5.0)
    _insert(db, company_id, "qtr_pbt", "2026-06-30", 100.0)
    result = oif.compute_other_income_dependency(db, company_id, "OITEST3")
    assert result is not None
    assert result["flagged"] is False
    assert result["proxy_score"] == 90.0  # top band, ratio well under 10%


def test_negative_pbt_quarter_is_skipped_not_treated_as_a_ratio(db, monkeypatch):
    company_id = _synthetic_company_id(db, "OITEST4")
    _insert(db, company_id, "qtr_other_income", "2026-06-30", 10.0)
    _insert(db, company_id, "qtr_pbt", "2026-06-30", -5.0)  # a loss quarter

    def _boom(*a, **k):
        raise AssertionError("a negative-PBT quarter must not trigger a Screener fetch either")
    monkeypatch.setattr("openscreener.Stock", _boom)
    assert oif.compute_other_income_dependency(db, company_id, "OITEST4") is None


def test_falls_back_to_annual_when_no_quarterly_data(db):
    company_id = _synthetic_company_id(db, "OITEST5")
    _insert(db, company_id, "pnl_other_income", "2026-03-31", 40.0)
    _insert(db, company_id, "pnl_pbt", "2026-03-31", 100.0)
    result = oif.compute_other_income_dependency(db, company_id, "OITEST5")
    assert result is not None
    assert result["period_type"] == "annual"
    assert result["ratio"] == 0.4


def test_none_on_ingest_failure_never_raises(monkeypatch, db):
    class _RaisingStock:
        def __init__(self, symbol, consolidated):
            raise ConnectionError("Screener unreachable")
    monkeypatch.setattr("openscreener.Stock", _RaisingStock)
    company_id = _synthetic_company_id(db, "OITEST6")
    assert oif.compute_other_income_dependency(db, company_id, "OITEST6") is None
