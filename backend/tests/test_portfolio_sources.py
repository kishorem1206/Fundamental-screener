"""Phase B: AMFI NAV file and broker holdings parsers (app/portfolio/amfi.py, brokers.py). Offline."""
import httpx
import pytest

from app.portfolio import amfi, brokers

_NAV_2026 = """Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date

Open Ended Schemes(Debt Scheme - Liquid Fund)

HDFC Mutual Fund

119091;INF179KB1HK0;-;HDFC Liquid Fund;Direct Plan;Growth Option;5123.4567;29-Oct-2026

Open Ended Schemes(Other Scheme - Gold ETF)

Nippon India Mutual Fund

140088;INF204KB17I5;-;Nippon India ETF Gold BeES;-;-;98.12;29-Oct-2026

Open Ended Schemes(Other Scheme - Index Funds)

UTI Mutual Fund

120716;INF789F01XA0;INF789F01XB8;UTI Nifty 50 Index Fund;Direct Plan;IDCW;170.5;29-Oct-2026
"""

_NAV_OLD = """Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date

Open Ended Schemes(Overseas Fund of Funds - Fund of Funds investing overseas)

Motilal Oswal Mutual Fund

145552;INF247L01AP3;-;Motilal Oswal Nasdaq 100 FOF - Direct Growth;45.6;28-Oct-2026
"""


def test_amfi_file_both_layouts():
    rows = {r["isin"]: r for r in amfi.parse(_NAV_2026) + amfi.parse(_NAV_OLD)}
    assert rows["INF179KB1HK0"]["asset_class"] == "DEBT" and rows["INF179KB1HK0"]["nav"] == 5123.4567
    assert rows["INF179KB1HK0"]["fund_house"] == "HDFC Mutual Fund"
    assert rows["INF179KB1HK0"]["scheme_name"] == "HDFC Liquid Fund - Direct Plan - Growth Option"
    assert rows["INF204KB17I5"]["asset_class"] == "GOLD"
    # both ISINs of a payout / reinvestment scheme; index funds are classed from the name
    assert rows["INF789F01XB8"]["asset_class"] == "EQUITY_FUND" and "from the scheme name" in rows["INF789F01XB8"]["class_basis"]
    assert rows["INF247L01AP3"]["asset_class"] == "INTERNATIONAL" and str(rows["INF247L01AP3"]["nav_date"]) == "2026-10-28"


def test_amfi_category_beats_the_name():
    assert amfi.classify("Open Ended Schemes(Hybrid Scheme - Arbitrage Fund)", "XYZ Equity Advantage Fund")[0] == "DEBT"
    assert amfi.classify("Open Ended Schemes(Equity Scheme - Large Cap Fund)", "XYZ Bluechip Fund")[0] == "EQUITY_FUND"
    assert amfi.classify("Open Ended Schemes(Hybrid Scheme - Conservative Hybrid Fund)", "XYZ Fund")[0] == "DEBT"


def test_dhan_holdings_shape():
    rows = brokers.parse_dhan([{"exchange": "ALL", "tradingSymbol": "HDFCBANK", "securityId": "1333", "isin": "INE040A01034",
                                "totalQty": 10, "dpQty": 10, "t1Qty": 0, "availableQty": 10, "collateralQty": 0, "avgCostPrice": 1500.5}])
    assert rows[0]["symbol"] == "HDFCBANK" and rows[0]["qty"] == 10 and rows[0]["avg"] == 1500.5 and rows[0]["last"] is None


def test_upstox_holdings_shape():
    rows = brokers.parse_upstox({"status": "success", "data": [
        {"isin": "INE002A01018", "company_name": "RELIANCE INDUSTRIES LTD", "tradingsymbol": "RELIANCE", "quantity": 4,
         "t1_quantity": 1, "average_price": 2400, "last_price": 2900, "close_price": 2890}]})
    assert rows[0]["symbol"] == "RELIANCE" and rows[0]["qty"] == 5 and rows[0]["last"] == 2900
    with pytest.raises(brokers.BrokerError):
        brokers.parse_upstox({"status": "error", "errors": [{"message": "Invalid token"}]})


def test_groww_holdings_shape():
    rows = brokers.parse_groww({"status": "SUCCESS", "payload": {"holdings": [
        {"isin": "INE467B01029", "trading_symbol": "TCS", "quantity": 3, "average_price": 3500}]}})
    assert rows == [{"symbol": "TCS", "isin": "INE467B01029", "name": "TCS", "qty": 3.0, "avg": 3500.0, "last": None,
                     "raw": {"isin": "INE467B01029", "trading_symbol": "TCS", "quantity": 3, "average_price": 3500}}]


def test_missing_token_and_refused_token(monkeypatch):
    monkeypatch.setattr(brokers.config, "dhan_access_token", "")
    with pytest.raises(brokers.BrokerError, match="DHAN_ACCESS_TOKEN is not set"):
        brokers.fetch("dhan")
    monkeypatch.setattr(brokers.config, "upstox_access_token", "t")
    monkeypatch.setattr(brokers.httpx, "get", lambda *a, **k: httpx.Response(401, text="unauthorised"))
    with pytest.raises(brokers.BrokerError, match="refused"):
        brokers.fetch("upstox")
    monkeypatch.setattr(brokers.config, "dhan_access_token", "t")
    monkeypatch.setattr(brokers.httpx, "get", lambda *a, **k: httpx.Response(400, text='{"errorMessage":"No holdings available"}'))
    assert brokers.fetch("dhan") == []


def test_only_holdings_endpoints_are_called(monkeypatch):
    seen = []
    monkeypatch.setattr(brokers.config, "groww_access_token", "t")
    monkeypatch.setattr(brokers.httpx, "get", lambda url, **k: seen.append(url) or httpx.Response(200, json={"status": "SUCCESS", "payload": {"holdings": []}}))
    brokers.fetch("groww")
    assert seen == ["https://api.groww.in/v1/holdings/user"]
    assert not any(hasattr(brokers, n) for n in ("place_order", "modify_order", "cancel_order"))
