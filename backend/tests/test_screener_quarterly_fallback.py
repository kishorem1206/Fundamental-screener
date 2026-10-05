"""Tests for `app/quick_analysis/screener_quarterly_fallback.py` — the
Screener consolidated-quarterly fallback used when Yahoo's own quarterly
data (`quick_analysis/quarterly_growth.py`) is empty or too thin (2026-09-28,
explicit user request, surfaced by WeWork India: Yahoo had a gap at
2025-06-30 so no quarterly growth score was computable from Yahoo alone —
Screener's own consolidated quarterly_results() has the real numbers).

DB-first, ingest-on-miss (2026-09-28 follow-up correction — the first
version fetched Screener live on every call; re-reads the ledger first now,
only ingesting on a genuine miss, so a repeat call for the same company
never re-fetches). Uses a test-only company created inside the rolled-back test transaction, monkeypatching `openscreener.Stock`.
"""
from __future__ import annotations

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock
from app.quick_analysis import screener_quarterly_fallback as sqf


def _fixture_company_id(db, symbol: str = "MARUTI") -> str:
    """A test-only company with an empty ledger, created inside the test's
    rolled-back transaction. (Until 2026-10-06 this used the real NSE:MARUTI,
    which only worked while MARUTI happened to have no Screener quarters
    stored — the Screener-first quick run fills them in for every company.)"""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    stock_id = f"TEST:QFB{symbol}"
    if db.get(Stock, stock_id) is None:
        db.add(Stock(id=stock_id, symbol=symbol, exchange="TEST", company_name=symbol, is_active=False,
                     created_at=now, updated_at=now))
        db.flush()
    return stock_id


class _FakeStock:
    """12 quarters (2 full recent-vs-prior 4Q block comparisons), sales
    growing, net_profit and eps both declining in the most recent 4 —
    same shape as the real WeWork case this feature was built for."""

    def __init__(self, symbol: str, consolidated: bool):
        self.symbol = symbol
        self.consolidated = consolidated
        assert consolidated is True, "must request CONSOLIDATED only, never STANDALONE"

    def quarterly_results(self):
        quarters = [
            ("Jun 2024", 400.0, 40.0, 8.0), ("Sep 2024", 420.0, 50.0, 10.0),
            ("Dec 2024", 440.0, 60.0, 12.0), ("Mar 2025", 460.0, 70.0, 14.0),
            ("Jun 2025", 500.0, 20.0, 4.0), ("Sep 2025", 520.0, 10.0, 2.0),
            ("Dec 2025", 540.0, 5.0, 1.0), ("Mar 2026", 560.0, -5.0, -1.0),
        ]
        return [{"date": d, "sales": s, "net_profit": p, "eps": e} for d, s, p, e in quarters] + [
            {"date": "TTM", "sales": 9999.0, "net_profit": 999.0, "eps": 99.0},
        ]


class _EmptyStock:
    def __init__(self, symbol: str, consolidated: bool):
        pass

    def quarterly_results(self):
        return []


class _RaisingStock:
    def __init__(self, symbol: str, consolidated: bool):
        raise ConnectionError("Screener unreachable")


def test_reads_the_ledger_first_and_skips_ingestion_when_already_populated(monkeypatch, db):
    """The core DB-first behaviour: if `fa_metric_data_points` already has
    enough qtr_* rows, `openscreener.Stock` must never even be constructed."""
    company_id = _fixture_company_id(db)
    periods = ["2024-06-30", "2024-09-30", "2024-12-31", "2025-03-31",
               "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31"]
    for i, period in enumerate(periods):
        for metric_key, base in (("qtr_sales", 400.0), ("qtr_net_profit", 40.0 - i * 5), ("qtr_eps", 8.0 - i)):
            metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=metric_key, period=period, value=base + i * 20,
                unit="cr", statement_type="CONSOLIDATED", source="SCREENER", source_tier=2,
                reported_or_calculated="REPORTED", confidence="MEDIUM",
            )

    def _boom(*a, **k):
        raise AssertionError("must not fetch Screener when the ledger already has enough data")
    monkeypatch.setattr("openscreener.Stock", _boom)

    result = sqf.compute_quarterly_growth_from_screener(db, company_id, "MARUTI")
    assert result is not None
    assert result["quarters_used"] == 8


def test_ingests_on_a_genuine_ledger_miss_then_scores_from_it(monkeypatch, db):
    monkeypatch.setattr("openscreener.Stock", _FakeStock)
    monkeypatch.setattr("app.ingestion.screener_client._SCREENER_REQUEST_DELAY_SECONDS", 0, raising=False)
    company_id = _fixture_company_id(db)

    result = sqf.compute_quarterly_growth_from_screener(db, company_id, "MARUTI")
    assert result is not None
    assert result["quarters_used"] == 8
    assert result["growth_pct"]["revenue"] > 0   # sales kept growing
    assert result["growth_pct"]["pat"] < 0       # but profit fell hard
    assert result["score"] < 60.0                # must NOT read as a strong-growth quarter

    # the ingested rows are now in the ledger — confirms the "persist so a
    # repeat scan never re-fetches" half of this feature.
    rows = metric_store.get_metric_history(db, company_id, "qtr_sales", statement_type="CONSOLIDATED")
    assert len(rows) >= 8


def test_ttm_row_is_excluded_from_the_series(monkeypatch, db):
    monkeypatch.setattr("openscreener.Stock", _FakeStock)
    monkeypatch.setattr("app.ingestion.screener_client._SCREENER_REQUEST_DELAY_SECONDS", 0, raising=False)
    company_id = _fixture_company_id(db)
    result = sqf.compute_quarterly_growth_from_screener(db, company_id, "MARUTI")
    assert result is not None
    # If TTM (sales=9999) leaked into the series it would dominate every ratio.
    assert result["growth_pct"]["revenue"] < 100


def test_none_when_screener_has_too_few_quarters(monkeypatch, db):
    monkeypatch.setattr("openscreener.Stock", _EmptyStock)
    monkeypatch.setattr("app.ingestion.screener_client._SCREENER_REQUEST_DELAY_SECONDS", 0, raising=False)
    company_id = _fixture_company_id(db)
    assert sqf.compute_quarterly_growth_from_screener(db, company_id, "MARUTI") is None


def test_none_on_fetch_failure_never_raises(monkeypatch, db):
    monkeypatch.setattr("openscreener.Stock", _RaisingStock)
    company_id = _fixture_company_id(db)
    assert sqf.compute_quarterly_growth_from_screener(db, company_id, "MARUTI") is None
