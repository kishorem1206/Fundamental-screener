"""Price store: parsing NSE's files, the Yahoo frame, upserts and benchmarks."""
import io
import zipfile
from datetime import date

import pandas as pd

from app.infrastructure.database.models import IndexBar, PriceBar, Stock
from app.prices import benchmarks, nse_bhavcopy, nse_indices, store, yahoo

INDEX_FILE = """Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value,Points Change,Change(%),Volume,Turnover (Rs. Cr.),P/E,P/B,Div Yield
Nifty 50,03-10-2025,24759.55,24904.8,24747.55,24894.25,57.95,.23,366929642,31409.06,22.01,3.4,1.33
Nifty IT,03-10-2025,33900.1,34100,33800,34050.5,10,.03,-,-,25.4,7.1,2.9
Nifty Dead Index,03-10-2025,-,-,-,-,-,-,-,-,-,-,-
"""


def test_index_file_rows_keep_valuation_and_skip_blank_indices():
    rows = nse_indices.parse(INDEX_FILE, "https://example/ind.csv")
    assert [r["index_name"] for r in rows] == ["Nifty 50", "Nifty IT"]
    nifty, it = rows
    assert nifty["bar_date"] == date(2025, 10, 3)
    assert (nifty["close"], nifty["pe"], nifty["pb"], nifty["div_yield"]) == (24894.25, 22.01, 3.4, 1.33)
    assert nifty["volume"] == 366929642 and nifty["source_url"] == "https://example/ind.csv"
    assert it["volume"] is None and it["turnover_cr"] is None  # a dash is "not published", never zero


def _bhavcopy(rows: list[str]) -> bytes:
    text = "TckrSymb,SctySrs,ClsPric\n" + "\n".join(rows) + "\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("bhav.csv", text)
    return buf.getvalue()


def test_bhavcopy_keeps_equity_series_only():
    closes = nse_bhavcopy.parse(_bhavcopy(["ITC,EQ,268.90", "SGBJUN28,GB,14739.50", "KROSS,BE,151.20"]))
    assert closes == {"ITC": 268.90, "KROSS": 151.20}


def test_yahoo_rows_fall_back_to_close_when_no_adjusted_close():
    frame = pd.DataFrame(
        {"Open": [10.0, 11.0, None], "High": [12.0, 12.0, None], "Low": [9.0, 10.0, None],
         "Close": [11.0, 11.5, None], "Adj Close": [10.5, None, None], "Volume": [1000, None, None]},
        index=pd.to_datetime(["2026-09-29", "2026-09-30", "2026-10-01"]),
    )
    rows = yahoo._rows("NSE:X", frame)
    assert len(rows) == 2  # the day with no close is dropped
    assert rows[0]["adj_close"] == 10.5 and rows[0]["volume"] == 1000
    assert rows[1]["adj_close"] == 11.5 and rows[1]["volume"] is None


def _stock(db, symbol="TESTPX") -> Stock:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    s = Stock(id=f"TEST:{symbol}", symbol=symbol, exchange="TEST", company_name=symbol, is_active=False, created_at=now, updated_at=now)
    db.add(s); db.flush()
    return s


def _bar(stock_id, day, close, adj=None):
    return {"stock_id": stock_id, "bar_date": day, "open": close, "high": close, "low": close,
            "close": close, "adj_close": adj or close, "volume": 1, "source": "TEST"}


def test_upsert_overwrites_the_same_day_and_reads_in_date_order(db):
    s = _stock(db)
    store.upsert_price_bars(db, [_bar(s.id, date(2026, 1, 2), 100), _bar(s.id, date(2026, 1, 1), 90)])
    store.upsert_price_bars(db, [_bar(s.id, date(2026, 1, 2), 101, adj=99)])
    assert store.closes(db, s.id) == [(date(2026, 1, 1), 90.0), (date(2026, 1, 2), 99.0)]
    assert store.closes(db, s.id, adjusted=False)[-1] == (date(2026, 1, 2), 101.0)
    assert store.closes(db, s.id, since=date(2026, 1, 2)) == [(date(2026, 1, 2), 99.0)]


def test_replacing_history_drops_days_the_new_series_does_not_have(db):
    s = _stock(db)
    store.upsert_price_bars(db, [_bar(s.id, date(2026, 1, 1), 200), _bar(s.id, date(2026, 1, 2), 210)])
    store.replace_price_history(db, s.id, [_bar(s.id, date(2026, 1, 2), 105)])  # after a 2-for-1 split
    assert store.closes(db, s.id) == [(date(2026, 1, 2), 105.0)]
    assert db.query(PriceBar).filter_by(stock_id=s.id).count() == 1


def test_index_upsert_and_read(db):
    rows = nse_indices.parse(INDEX_FILE.replace("Nifty 50", "Test Index 50"), "u")
    store.upsert_index_bars(db, rows)
    assert store.index_closes(db, "Test Index 50") == [(date(2025, 10, 3), 24894.25)]
    assert float(db.query(IndexBar).filter_by(index_name="Test Index 50").one().pe) == 22.01


def test_sector_benchmark_says_when_it_is_not_an_official_sector_index():
    assert benchmarks.sector_benchmark("Financial Services", "Banks") == {"index": "Nifty Bank", "kind": "official", "sector": "Financial Services"}
    assert benchmarks.sector_benchmark("Healthcare", "Healthcare Services")["index"] == "Nifty Healthcare Index"
    assert benchmarks.sector_benchmark("Power", "Power")["kind"] == "closest"
    assert benchmarks.sector_benchmark("Textiles", "Textiles & Apparels") == {"index": None, "kind": "peers", "sector": "Textiles"}
    assert benchmarks.sector_benchmark(None)["kind"] == "peers"
