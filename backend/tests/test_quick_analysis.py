"""app/quick_analysis — Yahoo-only quick scoring. Formulas are imported from
the full pipeline, so these tests cover only what the package adds: the
never-raise bulk contract, refinement-approximation invariants, and the
Yahoo rate-limit pacer."""
from __future__ import annotations

import time

import pytest

from app.calculations.scoring import SECTOR_WEIGHTS, UNIVERSAL_WEIGHTS, recompute_overall
from app.infrastructure.database.models import FundamentalAnalysis, Stock
from app.quick_analysis.approx import approximate_refinement
from app.quick_analysis.runner import _Pacer, _is_throttled
from app.quick_analysis.scorer import classify, quick_score

CATS = ("growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation")


def test_quick_score_never_raises_on_empty_yahoo_data():
    result = quick_score("NOPE", {"error": "Too Many Requests"}, "Chemicals")
    assert result.error and result.scores == {}


def test_quick_score_reports_error_instead_of_raising_on_malformed_data():
    result = quick_score("BAD", {"income": {"revenue": "not-a-dict"}}, "Chemicals")
    assert result.error


def test_routing_matches_full_pipeline_framework_call():
    assert classify("Healthcare", "Pharmaceuticals", "Pharmaceuticals") == "Healthcare"


@pytest.fixture()
def analysed(db):
    """Any company with a stored full analysis + the Yahoo data it used."""
    for a in db.query(FundamentalAnalysis).filter(FundamentalAnalysis.status == "COMPLETED").limit(30):
        if a.financial_data and a.scores:
            return a, db.get(Stock, a.stock_id)
    pytest.skip("no completed analysis with stored Yahoo data in this database")


def test_approximation_recomputes_overall_from_its_own_categories(analysed):
    a, stock = analysed
    q = quick_score(stock.symbol, a.financial_data, stock.sector, stock.industry, stock.basic_industry)
    assert not q.error
    weights = SECTOR_WEIGHTS.get(q.sector_framework, UNIVERSAL_WEIGHTS)
    assert q.refined["overall"] == pytest.approx(recompute_overall({c: q.refined[c] for c in CATS}, weights))
    assert abs(sum(q.refined["weights"].values()) - 1.0) < 1e-9


def test_refinement_only_touches_balance_sheet_and_cash_flow_within_bound(analysed):
    a, stock = analysed
    q = quick_score(stock.symbol, a.financial_data, stock.sector, stock.industry, stock.basic_industry)
    for c in ("growth", "profitability", "efficiency", "valuation"):
        assert q.refined[c] == q.scores[c], f"{c} has no Yahoo-derivable refinement and must stay unrefined"
    for c in ("balance_sheet", "cash_flow"):
        assert abs(q.refined[c] - q.scores[c]) <= 10.0 + 0.11  # the full engine's own +/-10 cap (+ rounding)


def test_financial_institutions_get_no_balance_sheet_refinement(analysed):
    a, stock = analysed
    q = quick_score(stock.symbol, a.financial_data, stock.sector, stock.industry, stock.basic_industry)
    refined = approximate_refinement(q.scores, a.financial_data, q.metrics, "Banks")
    assert refined["balance_sheet"] == q.scores["balance_sheet"]


def test_throttle_detection():
    assert _is_throttled({"error": "Too Many Requests. Rate limited. Try after a while."})
    assert not _is_throttled({"error": "No data found, symbol may be delisted"})
    assert not _is_throttled({})


def test_pacer_spaces_turns_and_backs_off_exponentially(capsys):
    pacer = _Pacer(stocks_per_sec=20)  # 50 ms apart
    start = time.monotonic()
    pacer.wait_turn(); pacer.wait_turn(); pacer.wait_turn()
    assert time.monotonic() - start >= 0.09
    pacer.report_throttled(); first = pacer._backoff
    pacer.report_throttled()
    assert (first, pacer._backoff) == (120.0, 240.0)
    pacer.report_ok()
    assert pacer._backoff == 60.0


# ── storage: fa_quick_scores is separate from fa_company_scores ─────────────

from datetime import datetime, timedelta, timezone  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.infrastructure.database.models import CompanyScore, QuickScore as QuickScoreRow  # noqa: E402
from app.quick_analysis.scorer import QuickScore  # noqa: E402
from app.quick_analysis.store import METHOD_VERSION, recently_scored_ids, upsert_quick_score  # noqa: E402

_T0 = datetime(2026, 9, 24, tzinfo=timezone.utc)


def _fake_result(symbol: str, growth: float = 50.0, valuation: float = 30.0) -> QuickScore:
    refined = {"overall": 60.0, "growth": growth, "profitability": 60.0, "cash_flow": 55.0, "balance_sheet": 70.0,
               "efficiency": 45.0, "valuation": valuation, "overall_rating": "FAIR", "valuation_view": "FAIR",
               "weights": {"growth": 0.2}, "red_flags": [], "refinement": {"balance_sheet": {"adjustment": -10.0}}}
    return QuickScore(symbol, "Chemicals", refined, refined, {"latest_fy": "FY2026"})


def _stock(db, sid: str, sector: str = "ZZ Quick Sector") -> Stock:
    s = Stock(id=sid, symbol=sid.split(":")[1], exchange="TEST", company_name=f"{sid} Ltd", sector=sector,
              is_active=True, created_at=_T0, updated_at=_T0)
    db.add(s)
    db.flush()
    return s


def test_upsert_writes_quick_table_only_and_updates_in_place(db):
    _stock(db, "TEST:QSA")
    full_rows_before = db.query(CompanyScore).count()
    upsert_quick_score(db, "TEST:QSA", _fake_result("QSA", growth=40.0), scored_at=_T0)
    upsert_quick_score(db, "TEST:QSA", _fake_result("QSA", growth=75.0), scored_at=_T0 + timedelta(days=90))
    rows = db.query(QuickScoreRow).filter_by(stock_id="TEST:QSA").all()
    assert len(rows) == 1, "one row per company, updated in place"
    assert float(rows[0].growth) == 75.0 and rows[0].scored_at == _T0 + timedelta(days=90)
    assert (rows[0].method_version, rows[0].latest_fy) == (METHOD_VERSION, "FY2026")
    assert db.query(CompanyScore).count() == full_rows_before, "full-analysis score table must never be touched"


def test_failed_result_stores_nothing(db):
    _stock(db, "TEST:QSB")
    assert upsert_quick_score(db, "TEST:QSB", QuickScore("QSB", "Chemicals", {}, error="Too Many Requests")) is None
    assert db.query(QuickScoreRow).filter_by(stock_id="TEST:QSB").count() == 0


def test_recently_scored_ids_drives_resume(db):
    _stock(db, "TEST:QSC")
    upsert_quick_score(db, "TEST:QSC", _fake_result("QSC"), scored_at=datetime.now(timezone.utc) - timedelta(days=2))
    assert "TEST:QSC" in recently_scored_ids(db, max_age_days=7)
    assert "TEST:QSC" not in recently_scored_ids(db, max_age_days=1)


def test_quick_api_filters_the_quick_table_not_the_full_table(db, monkeypatch):
    class _Session:
        def __getattr__(self, name):
            return getattr(db, name)
        def close(self):
            pass
    monkeypatch.setattr("app.routes.company_scores.get_db", lambda: _Session())
    from app.main import app
    client = TestClient(app)
    for sid, growth in (("TEST:QSD", 90.0), ("TEST:QSE", 20.0)):
        _stock(db, sid)
        upsert_quick_score(db, sid, _fake_result(sid.split(":")[1], growth=growth), scored_at=_T0)
    body = client.get("/api/quick-scores", params={"sector": "ZZ Quick Sector", "min_growth": 80}).json()
    assert [r["symbol"] for r in body["results"]] == ["QSD"]
    assert body["results"][0]["sector_framework"] == "Chemicals" and body["results"][0]["latest_fy"] == "FY2026"
    assert client.get("/api/company-scores", params={"sector": "ZZ Quick Sector"}).json()["total"] == 0
