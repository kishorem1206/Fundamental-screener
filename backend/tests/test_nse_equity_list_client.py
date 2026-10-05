"""Tests for `app/ingestion/nse_equity_list_client.py` — syncing `stocks`
against NSE's full EQUITY_L.csv (the ~950-company gap confirmed live,
2026-09-28: the existing universe was built from a market-cap>1000cr
Screener screen and never had NSE's smaller-cap listings at all)."""
from __future__ import annotations

from datetime import date, datetime, timezone

from app.infrastructure.database.models import Stock
from app.ingestion import nse_equity_list_client as ec


def _stock(db, symbol: str, sector: str | None = None) -> Stock:
    now = datetime.now(timezone.utc)
    s = Stock(id=f"NSE:{symbol}", symbol=symbol, exchange="NSE", company_name=f"{symbol} Ltd",
              sector=sector, is_active=True, created_at=now, updated_at=now)
    db.add(s)
    db.flush()
    return s


def test_parse_date_handles_dd_mon_yyyy():
    assert ec._parse_date("06-OCT-2008") == date(2008, 10, 6)


def test_parse_date_dash_is_none():
    assert ec._parse_date("-") is None
    assert ec._parse_date(None) is None


def test_sync_missing_stocks_skips_symbols_already_present(db, monkeypatch):
    _stock(db, "TESTEXIST")
    monkeypatch.setattr(ec, "fetch_equity_list", lambda: [
        {"SYMBOL": "TESTEXIST", "NAME OF COMPANY": "Test Exist Ltd", "SERIES": "EQ", "DATE OF LISTING": "01-JAN-2020"},
        {"SYMBOL": "TESTNEW", "NAME OF COMPANY": "Test New Ltd", "SERIES": "EQ", "DATE OF LISTING": "01-JAN-2020"},
    ])
    result = ec.sync_missing_stocks(db)
    assert result == {"fetched": 2, "added": 1}
    assert db.query(Stock).filter_by(symbol="TESTNEW").count() == 1
    # existing row's fields untouched (company_name not overwritten from the CSV)
    assert db.query(Stock).filter_by(symbol="TESTEXIST").one().company_name == "TESTEXIST Ltd"


def test_sync_missing_stocks_excludes_non_mainboard_series(db, monkeypatch):
    monkeypatch.setattr(ec, "fetch_equity_list", lambda: [
        {"SYMBOL": "TESTBZ", "NAME OF COMPANY": "Test BZ Ltd", "SERIES": "BZ", "DATE OF LISTING": "01-JAN-2020"},
        {"SYMBOL": "TESTBE", "NAME OF COMPANY": "Test BE Ltd", "SERIES": "BE", "DATE OF LISTING": "01-JAN-2020"},
    ])
    result = ec.sync_missing_stocks(db)
    assert result["added"] == 1
    assert db.query(Stock).filter_by(symbol="TESTBZ").count() == 0
    assert db.query(Stock).filter_by(symbol="TESTBE").count() == 1


def test_sync_missing_stocks_sets_listing_date_from_csv(db, monkeypatch):
    monkeypatch.setattr(ec, "fetch_equity_list", lambda: [
        {"SYMBOL": "TESTDATE", "NAME OF COMPANY": "Test Date Ltd", "SERIES": "EQ", "DATE OF LISTING": "15-MAR-2021"},
    ])
    ec.sync_missing_stocks(db)
    row = db.query(Stock).filter_by(symbol="TESTDATE").one()
    assert row.ipo_listing_date == date(2021, 3, 15)


def test_sync_missing_stocks_empty_fetch_is_a_clean_noop(db, monkeypatch):
    monkeypatch.setattr(ec, "fetch_equity_list", lambda: [])
    assert ec.sync_missing_stocks(db) == {"fetched": 0, "added": 0}
