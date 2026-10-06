"""Portfolio (framework sections 12-14): importers, comparison rule, analysis."""
import pytest

from app.portfolio import analysis, importers
from app.portfolio.kite_link import KiteLink

ZERODHA_CSV = """Holdings statement as on 2026-10-05
Instrument,Qty.,Avg. cost,LTP,Cur. val,P&L,Net chg.,Day chg.
PIDILITIND,40,1300.00,1487.70,59508.00,7508.00,14.44,0.5
ITC,600,400.00,268.90,161340.00,-78660.00,-32.77,1.2
VOLTAS,50,1500.00,1135.00,56750.00,-18250.00,-24.33,-0.4
IDEA,20000,8.00,7.80,156000.00,-4000.00,-2.5,3.1
GOLDBEES,500,60.00,95.00,47500.00,17500.00,58.3,0.2
LIQUIDBEES,10,1000.00,1000.00,10000.00,0,0,0
"""


def test_fund_names_decide_the_asset_class():
    assert importers.classify_fund("Nippon India ETF Gold BeES") == "GOLD"
    assert importers.classify_fund("HDFC Liquid Fund - Direct") == "DEBT"
    assert importers.classify_fund("Motilal Oswal Nasdaq 100 FOF") == "INTERNATIONAL"
    assert importers.classify_fund("Parag Parikh Flexi Cap Fund") == "EQUITY_FUND"


def test_zerodha_console_csv_is_read_and_matched_to_stocks(db):
    out = importers.from_csv(db, ZERODHA_CSV, source="CSV_TEST")
    assert out["rows"] == 6 and out["matched_stocks"] == 4
    from app.infrastructure.database.models import PortfolioHolding
    gold = db.query(PortfolioHolding).filter_by(source="CSV_TEST", symbol="GOLDBEES").one()
    assert gold.asset_class == "GOLD" and float(gold.value) == 47500.0
    # a second upload from the same source replaces, never duplicates
    assert importers.from_csv(db, ZERODHA_CSV, source="CSV_TEST")["rows"] == 6
    assert db.query(PortfolioHolding).filter_by(source="CSV_TEST").count() == 6


def test_csv_without_a_symbol_or_isin_column_is_refused(db):
    with pytest.raises(ValueError):
        importers.from_csv(db, "a,b\n1,2\n")


def test_candidate_must_be_clearly_better():
    held = {"quality": 70, "fundamental": 70, "relative_strength": 30, "technical": 30, "valuation": 40}
    much_better_now = {"classification": "Core Quality", "quality": 68, "fundamental": 66, "relative_strength": 70, "technical": 60, "valuation": 50}
    assert analysis.clearly_better(held, "Core Quality", much_better_now)[0]
    weaker_business = {**much_better_now, "quality": 55}
    assert not analysis.clearly_better(held, "Core Quality", weaker_business)[0]
    failing = {**much_better_now, "classification": "Replacement Candidate"}
    assert not analysis.clearly_better(held, "Core Quality", failing)[0]
    slightly_better = {**much_better_now, "relative_strength": 35, "technical": 35, "valuation": 42}
    assert not analysis.clearly_better(held, "Core Quality", slightly_better)[0]
    assert analysis.clearly_better({**held, "quality": 35}, "Replacement Candidate", {**slightly_better, "quality": 60})[0]


def test_kite_link_refuses_order_tools():
    with pytest.raises(PermissionError):
        KiteLink().call("place_order", {"tradingsymbol": "ITC"})
    with pytest.raises(PermissionError):
        KiteLink().call("modify_gtt_order", {})


def test_analysis_of_a_sample_portfolio(db):
    from app.infrastructure.database.models import PortfolioHolding

    db.query(PortfolioHolding).delete()
    importers.from_csv(db, ZERODHA_CSV, source="CSV_TEST")
    importers.add_manual(db, "Sovereign gold bonds", "GOLD", 50000)
    importers.add_manual(db, "PPF", "DEBT", 150000)
    analysis.save_settings(db, {"targets": {"EQUITY": 60, "DEBT": 25, "GOLD": 10}})
    out = analysis.analyse(db)
    assert out["total"] == pytest.approx(691098.0)
    classes = {a["asset_class"]: a for a in out["allocation"]}
    assert classes["EQUITY"]["target_pct"] == 60 and classes["EQUITY"]["status"] in ("over", "under", "on target")
    stocks = {h["symbol"]: h for h in out["holdings"] if h.get("framework")}
    assert set(stocks) >= {"PIDILITIND", "ITC", "VOLTAS", "IDEA"}
    assert all(h["final_action"] in analysis._READY for h in stocks.values())
    assert stocks["IDEA"]["final_action"] in ("Replace", "Watch", "Reduce")  # below the gate
    # ITC is 23% of the equity book here: above the default 10% per-stock limit
    assert stocks["ITC"]["pct_of_equity"] > 10 and stocks["ITC"]["final_action"] == "Reduce"
    assert "volatility_pct" in out["risk"] or "reason" in out["risk"]
