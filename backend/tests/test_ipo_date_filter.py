"""`ipo_only` / `ipo_since` filters on /api/quick-scores and
/api/company-scores — "recent IPOs only" plus a user-chosen listing-date
cutoff (2026-09-28 follow-up: a fixed toggle wasn't enough, the user wanted
to pick the date)."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.models import QuickScore, Stock


def _stock(db, symbol: str, ipo_listing_date: date | None) -> Stock:
    now = datetime.now(timezone.utc)
    s = Stock(id=f"NSE:{symbol}", symbol=symbol, exchange="TEST", company_name=f"{symbol} Ltd",
              sector="ZZ IPO Test Sector", is_active=True, ipo_listing_date=ipo_listing_date,
              created_at=now, updated_at=now)
    db.add(s)
    db.flush()
    return s


def _quick_score(db, symbol: str) -> QuickScore:
    now = datetime.now(timezone.utc)
    row = QuickScore(id=f"qs-{symbol}", stock_id=f"NSE:{symbol}", overall=60.0, growth=60.0,
                      profitability=60.0, cash_flow=60.0, balance_sheet=60.0, efficiency=60.0,
                      valuation=60.0, overall_rating="FAIR", valuation_view="FAIR",
                      method_version="quick-v1", scored_at=now, created_at=now, updated_at=now)
    db.add(row)
    db.flush()
    return row


@pytest.fixture()
def client(db, monkeypatch):
    class _Session:
        def __getattr__(self, name):
            return getattr(db, name)
        def close(self):
            pass
    monkeypatch.setattr("app.routes.company_scores.get_db", lambda: _Session())
    from app.main import app
    return TestClient(app)


def test_ipo_only_excludes_non_ipo_stocks(db, client):
    _stock(db, "TESTIPOA", date(2026, 1, 15)); _quick_score(db, "TESTIPOA")
    _stock(db, "TESTNOTIPO", None); _quick_score(db, "TESTNOTIPO")
    body = client.get("/api/quick-scores", params={"sector": "ZZ IPO Test Sector", "ipo_only": "true"}).json()
    assert [r["symbol"] for r in body["results"]] == ["TESTIPOA"]


def test_ipo_since_filters_to_listings_on_or_after_the_date(db, client):
    _stock(db, "TESTEARLY", date(2025, 1, 1)); _quick_score(db, "TESTEARLY")
    _stock(db, "TESTLATE", date(2026, 6, 1)); _quick_score(db, "TESTLATE")
    body = client.get("/api/quick-scores", params={
        "sector": "ZZ IPO Test Sector", "ipo_since": "2026-01-01",
    }).json()
    assert [r["symbol"] for r in body["results"]] == ["TESTLATE"]


def test_ipo_since_rejects_bad_date_format(client):
    assert client.get("/api/quick-scores", params={"ipo_since": "not-a-date"}).status_code == 400


def test_ipo_since_also_works_on_full_company_scores_route(db, client):
    from datetime import date as _date
    from app.infrastructure.database.models import CompanyScore, FundamentalAnalysis
    now = datetime.now(timezone.utc)
    _stock(db, "TESTFULLIPO", _date(2026, 3, 1))
    a = FundamentalAnalysis(id="FA-TEST-IPO", stock_id="NSE:TESTFULLIPO", status="COMPLETED",
                            overall_progress=100, scores={"overall": 60.0}, created_at=now, updated_at=now)
    db.add(a); db.flush()
    db.add(CompanyScore(id="cs-testfullipo", stock_id="NSE:TESTFULLIPO", analysis_id="FA-TEST-IPO",
                         overall=60.0, growth=60.0, profitability=60.0, cash_flow=60.0, balance_sheet=60.0,
                         efficiency=60.0, valuation=60.0, overall_rating="FAIR", valuation_view="FAIR",
                         scored_at=now, created_at=now, updated_at=now))
    db.flush()
    body = client.get("/api/company-scores", params={"sector": "ZZ IPO Test Sector", "ipo_only": "true"}).json()
    assert [r["symbol"] for r in body["results"]] == ["TESTFULLIPO"]
