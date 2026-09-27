"""fa_quick_scores.growth_annual / growth_quarterly — filtering, sorting,
and the /api/company-scores 400-on-typo contract must NOT accept these
QuickScore-only fields (they're not real columns on CompanyScore)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.models import QuickScore, Stock

_NOW = datetime(2026, 9, 27, tzinfo=timezone.utc)


def _stock(db, sid: str, sector: str = "ZZ Quick Test Sector") -> Stock:
    s = Stock(id=sid, symbol=sid.split(":")[1], exchange="TEST", company_name=f"{sid} Ltd",
              sector=sector, is_active=True, created_at=_NOW, updated_at=_NOW)
    db.add(s)
    db.flush()
    return s


def _quick_score(db, sid: str, stock_id: str, growth: float, growth_annual: float,
                  growth_quarterly: float | None) -> QuickScore:
    row = QuickScore(
        id=sid, stock_id=stock_id, growth=growth, growth_annual=growth_annual,
        growth_quarterly=growth_quarterly, overall=60.0, profitability=60.0, cash_flow=60.0,
        balance_sheet=60.0, efficiency=60.0, valuation=60.0, overall_rating="FAIR",
        valuation_view="FAIR", method_version="quick-v1", scored_at=_NOW, created_at=_NOW, updated_at=_NOW,
    )
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


def test_quick_scores_row_includes_both_growth_components(db, client):
    _stock(db, "TEST:QGA")
    _quick_score(db, "qs-a", "TEST:QGA", growth=50.0, growth_annual=90.0, growth_quarterly=20.0)
    body = client.get("/api/quick-scores", params={"q": "QGA"}).json()
    assert len(body["results"]) == 1
    assert body["results"][0]["growth_annual"] == 90.0
    assert body["results"][0]["growth_quarterly"] == 20.0


def test_quick_scores_null_growth_quarterly_when_too_few_yahoo_quarters(db, client):
    _stock(db, "TEST:QGB")
    _quick_score(db, "qs-b", "TEST:QGB", growth=90.0, growth_annual=90.0, growth_quarterly=None)
    body = client.get("/api/quick-scores", params={"q": "QGB"}).json()
    assert body["results"][0]["growth_quarterly"] is None


def test_quick_scores_can_filter_and_sort_by_growth_quarterly(db, client):
    for sid, gq in (("TEST:QGC", 90.0), ("TEST:QGD", 20.0), ("TEST:QGE", 55.0)):
        _stock(db, sid)
        _quick_score(db, f"qs-{sid}", sid, growth=70.0, growth_annual=70.0, growth_quarterly=gq)
    body = client.get("/api/quick-scores", params={
        "sector": "ZZ Quick Test Sector", "min_growth_quarterly": 50, "sort_by": "growth_quarterly", "order": "asc",
    }).json()
    assert [r["symbol"] for r in body["results"]] == ["QGE", "QGC"]


def test_full_company_scores_route_rejects_growth_annual_as_a_typo(client):
    # growth_annual/growth_quarterly are QuickScore-only columns — the full
    # /api/company-scores route (CompanyScore model) must still 400 on them,
    # not silently accept an unfiltered/broken query.
    assert client.get("/api/company-scores", params={"min_growth_annual": 50}).status_code == 400
    assert client.get("/api/company-scores", params={"sort_by": "growth_quarterly"}).status_code == 400
