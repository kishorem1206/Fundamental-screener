"""Peer-engine tests (P&L Analysis Engine plan, Milestone 2) — Stage 31's
peer-test list: 1-company/2-company/missing-peer groups, percentile
correctness. `_percentile` is pure and tested directly with synthetic data;
`compute_peer_margin_percentiles` is exercised against real data for a
company with actual industry peers in the `stocks` table.
"""
from __future__ import annotations

from app.calculations.pl_intelligence.peer_engine import (
    _percentile,
    compute_peer_margin_percentiles,
)
from app.infrastructure.database.models import Stock


def test_percentile_no_peers_returns_none():
    assert _percentile(15.0, []) is None


def test_percentile_missing_subject_value_returns_none():
    assert _percentile(None, [10.0, 20.0]) is None


def test_percentile_single_peer_group():
    # subject beats the one peer -> 2nd of 2 -> 100th percentile
    assert _percentile(20.0, [10.0]) == 100
    # subject trails the one peer -> 1st of 2 -> 50th percentile
    assert _percentile(5.0, [10.0]) == 50


def test_percentile_two_company_peer_group():
    result = _percentile(15.0, [10.0, 20.0])
    # sorted [10, 15, 20] -> subject rank 2 of 3 -> 67th percentile
    assert result == 67


def test_percentile_top_of_group():
    assert _percentile(30.0, [10.0, 15.0, 20.0]) == 100


def test_compute_peer_margin_percentiles_real_company(db):
    stock = db.query(Stock).filter_by(symbol="MARUTI").first()
    assert stock is not None
    result = compute_peer_margin_percentiles(db, stock.id, stock.sector, "2025-03-31")
    assert result["period"] == "2025-03-31"
    assert result["statement_type"] == "CONSOLIDATED"
    assert "ebitda_margin" in result
    assert "pat_margin" in result
    for field in ("ebitda_margin", "pat_margin"):
        entry = result[field]
        assert set(entry.keys()) == {
            "company_value", "peer_median", "peer_mean", "peer_min", "peer_max", "percentile",
        }


def test_compute_peer_margin_percentiles_no_peers_degrades_cleanly(db):
    result = compute_peer_margin_percentiles(db, "NOT-A-REAL-COMPANY-ID", None, "2025-03-31")
    assert result["peer_count"] == 0
    for field in ("ebitda_margin", "pat_margin"):
        entry = result[field]
        assert entry["peer_median"] is None
        assert entry["percentile"] is None


# ── Yahoo peer-tab fallback (Jeena Sikho Lifecare, 2026-09-24) ──────────────

from datetime import datetime, timezone  # noqa: E402

from app.infrastructure.database import metric_store  # noqa: E402
from app.infrastructure.database.models import FundamentalAnalysis  # noqa: E402

_NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)
_BI = "ZZ Fallback Test Basic Industry"


def _mk_stock(db, sid: str) -> Stock:
    s = Stock(id=sid, symbol=sid.split(":")[1], exchange="TEST", company_name=f"{sid} Ltd", sector="ZZ Sector",
              industry="ZZ Industry", basic_industry=_BI, is_active=True, created_at=_NOW, updated_at=_NOW)
    db.add(s)
    db.flush()
    return s


def _analysis_with_peers(db, subject_id: str, peers: list[dict], company_metrics: dict) -> None:
    db.add(FundamentalAnalysis(
        id=f"FA-TEST-{subject_id}", stock_id=subject_id, status="COMPLETED", overall_progress=100,
        peers={"peers": peers, "company_metrics": company_metrics}, created_at=_NOW, updated_at=_NOW))
    db.flush()


def test_falls_back_to_peer_tab_margins_when_no_peer_has_ledger_data(db):
    _mk_stock(db, "TEST:FBSUBJ")
    for i in range(3):
        _mk_stock(db, f"TEST:FBPEER{i}")
    _analysis_with_peers(
        db, "TEST:FBSUBJ",
        peers=[{"ebitda_margin": 10.0, "pat_margin": 5.0}, {"ebitda_margin": 20.0, "pat_margin": 10.0},
               {"ebitda_margin": 30.0, "pat_margin": 15.0}],
        company_metrics={"ebitda_margin": 25.0, "pat_margin": 12.0},
    )
    result = compute_peer_margin_percentiles(db, "TEST:FBSUBJ", "ZZ Sector", "2026-03-31")
    assert result["peer_source"] == {"ebitda_margin": "YAHOO_PEER_TAB", "pat_margin": "YAHOO_PEER_TAB"}
    assert result["pat_margin"]["peer_median"] == 10.0
    assert result["pat_margin"]["company_value"] == 12.0          # subject margin also from the analysis
    assert result["pat_margin"]["percentile"] == 75               # 12 ranks 3rd of 4


def test_ledger_data_wins_over_the_fallback(db):
    _mk_stock(db, "TEST:LGSUBJ")
    _mk_stock(db, "TEST:LGPEER")
    for company, sales, pat in (("TEST:LGSUBJ", 100.0, 20.0), ("TEST:LGPEER", 100.0, 8.0)):
        for key, val in (("pnl_sales", sales), ("pnl_operating_profit", 30.0), ("pnl_depreciation", 5.0),
                         ("pnl_net_profit", pat)):
            metric_store.insert_metric_value(
                db, company_id=company, metric_key=key, period="2026-03-31", value=val, unit="cr",
                statement_type="CONSOLIDATED", source="SCREENER", source_tier=2,
                reported_or_calculated="REPORTED", confidence="MEDIUM", source_date=_NOW)
    _analysis_with_peers(db, "TEST:LGSUBJ", peers=[{"ebitda_margin": 99.0, "pat_margin": 99.0}],
                         company_metrics={"ebitda_margin": 1.0, "pat_margin": 1.0})
    result = compute_peer_margin_percentiles(db, "TEST:LGSUBJ", "ZZ Sector", "2026-03-31")
    assert result["peer_source"]["pat_margin"] == "LEDGER"
    assert result["pat_margin"]["peer_median"] == 8.0             # the ledger peer, not the 99.0 fallback peer


def test_no_ledger_and_no_analysis_still_degrades_to_none(db):
    _mk_stock(db, "TEST:NFSUBJ")
    _mk_stock(db, "TEST:NFPEER")
    result = compute_peer_margin_percentiles(db, "TEST:NFSUBJ", "ZZ Sector", "2026-03-31")
    assert result["pat_margin"]["percentile"] is None and result["pat_margin"]["peer_median"] is None
