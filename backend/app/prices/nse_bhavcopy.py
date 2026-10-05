"""NSE's daily bhavcopy — the exchange's official close of every listed
security — used to check the stored closes, not to build history (it is not
adjusted for splits or bonuses).

    https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, timedelta

import httpx
from sqlalchemy.orm import Session

from app.infrastructure.database.models import PriceBar, Stock
from app.prices.nse_indices import HEADERS

URL = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{:%Y%m%d}_F_0000.csv.zip"
_EQUITY_SERIES = ("EQ", "BE", "BZ", "SM", "ST")
_TOLERANCE = 0.002  # 0.2%, or five paise on a low-priced stock


def parse(payload: bytes) -> dict[str, float]:
    """{symbol: official close} for equity series."""
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        text = z.read(z.namelist()[0]).decode("utf-8", "replace")
    out = {}
    for r in csv.DictReader(io.StringIO(text)):
        if r.get("SctySrs") in _EQUITY_SERIES and r.get("ClsPric"):
            out.setdefault(r["TckrSymb"].strip(), float(r["ClsPric"]))
    return out


def fetch(day: date) -> dict[str, float] | None:
    """None when there is no file for that day (holiday or not yet published)."""
    with httpx.Client(headers=HEADERS, timeout=40, follow_redirects=True) as client:
        r = client.get(URL.format(day))
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return parse(r.content)


def compare(db: Session, day: date | None = None) -> dict:
    """Stored close against NSE's official close for one trading day (default:
    the most recent day NSE has published)."""
    official = None
    if day is None:
        day = date.today()
        for _ in range(7):
            official = fetch(day)
            if official:
                break
            day -= timedelta(days=1)
    else:
        official = fetch(day)
    if not official:
        return {"day": day, "available": False}
    stored = dict(
        db.query(Stock.symbol, PriceBar.close).join(PriceBar, PriceBar.stock_id == Stock.id)
        .filter(PriceBar.bar_date == day, Stock.exchange == "NSE")
    )
    agree, differ, not_in_nse = 0, [], 0
    for symbol, close in stored.items():
        close = float(close)
        if symbol not in official:
            not_in_nse += 1
        elif abs(close - official[symbol]) <= max(_TOLERANCE * official[symbol], 0.05):
            agree += 1
        else:
            differ.append({"symbol": symbol, "stored": round(close, 2), "nse": official[symbol]})
    active = db.query(Stock).filter(Stock.is_active.is_(True), Stock.exchange == "NSE").count()
    return {
        "day": day, "available": True, "source_url": URL.format(day),
        "compared": agree + len(differ), "agree": agree, "differ": sorted(differ, key=lambda d: d["symbol"]),
        "stored_but_not_in_nse_file": not_in_nse, "active_stocks_without_a_bar": active - len(stored),
    }
