"""fa_company_scores: upsert semantics + the combined-filter API. Uses a
synthetic fixture stock so real data is never touched (the `db` fixture
rolls everything back)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.models import CompanyScore, FundamentalAnalysis, Stock
from app.services.company_scores import upsert_company_score

_NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)


def _stock(db, sid: str, sector: str = "Chemicals") -> Stock:
    s = Stock(id=sid, symbol=sid.split(":")[1], exchange="TEST", company_name=f"{sid} Ltd",
              sector=sector, is_active=True, created_at=_NOW, updated_at=_NOW)
    db.add(s)
    db.flush()
    return s


def _analysis(db, aid: str, stock_id: str, **scores) -> FundamentalAnalysis:
    base = {"overall": 60.0, "growth": 50.0, "profitability": 60.0, "cash_flow": 55.0, "balance_sheet": 70.0,
            "efficiency": 45.0, "valuation": 30.0, "overall_rating": "FAIR", "valuation_view": "EXPENSIVE",
            "weights": {"growth": 0.2}, "red_flags": ["x"]}
    base.update(scores)
    a = FundamentalAnalysis(id=aid, stock_id=stock_id, status="COMPLETED", overall_progress=100,
                            scores=base, created_at=_NOW, updated_at=_NOW)
    db.add(a)
    db.flush()
    return a


def test_upsert_creates_row_with_all_scores(db):
    _stock(db, "TEST:SCA")
    a = _analysis(db, "FA-TEST-1", "TEST:SCA")
    row = upsert_company_score(db, a, scored_at=_NOW)
    assert row is not None
    assert (float(row.growth), float(row.valuation), row.overall_rating) == (50.0, 30.0, "FAIR")
    assert row.analysis_id == "FA-TEST-1" and row.scored_at == _NOW


def test_reanalysis_overwrites_same_row_with_new_date(db):
    _stock(db, "TEST:SCB")
    upsert_company_score(db, _analysis(db, "FA-TEST-2", "TEST:SCB", growth=40.0), scored_at=_NOW)
    later = _NOW + timedelta(days=90)
    upsert_company_score(db, _analysis(db, "FA-TEST-3", "TEST:SCB", growth=75.0), scored_at=later)
    rows = db.query(CompanyScore).filter_by(stock_id="TEST:SCB").all()
    assert len(rows) == 1, "one row per company, updated in place"
    assert float(rows[0].growth) == 75.0 and rows[0].scored_at == later and rows[0].analysis_id == "FA-TEST-3"


def test_older_analysis_never_overwrites_fresher_scores(db):
    _stock(db, "TEST:SCC")
    upsert_company_score(db, _analysis(db, "FA-TEST-4", "TEST:SCC", growth=80.0), scored_at=_NOW)
    result = upsert_company_score(db, _analysis(db, "FA-TEST-5", "TEST:SCC", growth=10.0), scored_at=_NOW - timedelta(days=30))
    assert result is None
    assert float(db.query(CompanyScore).filter_by(stock_id="TEST:SCC").one().growth) == 80.0


def test_analysis_without_scores_writes_nothing(db):
    _stock(db, "TEST:SCD")
    a = _analysis(db, "FA-TEST-6", "TEST:SCD")
    a.scores = {}
    assert upsert_company_score(db, a) is None
    assert db.query(CompanyScore).filter_by(stock_id="TEST:SCD").count() == 0


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


def test_api_combines_filters_with_and(db, client):
    for sid, growth, val in (("TEST:APA", 90.0, 20.0), ("TEST:APB", 90.0, 80.0), ("TEST:APC", 30.0, 20.0)):
        _stock(db, sid, sector="ZZ Test Sector")
        upsert_company_score(db, _analysis(db, f"FA-{sid}", sid, growth=growth, valuation=val), scored_at=_NOW)
    body = client.get("/api/company-scores", params={"sector": "ZZ Test Sector", "min_growth": 80, "max_valuation": 40}).json()
    assert [r["symbol"] for r in body["results"]] == ["APA"]
    single = client.get("/api/company-scores", params={"sector": "ZZ Test Sector", "min_growth": 80, "sort_by": "valuation", "order": "asc"}).json()
    assert [r["symbol"] for r in single["results"]] == ["APA", "APB"]


def test_api_rejects_typos_instead_of_returning_unfiltered(client):
    assert client.get("/api/company-scores", params={"min_growht": 5}).status_code == 400
    assert client.get("/api/company-scores", params={"min_growth": "abc"}).status_code == 400
    assert client.get("/api/company-scores", params={"sort_by": "nope"}).status_code == 400
