"""Turning a broker's holdings into `pf_holdings` rows.

A stock is matched to the app's `stocks` table by ISIN first, then by symbol.
A fund or ETF is looked up by ISIN in AMFI's daily NAV file
(app/portfolio/amfi.py): its asset class comes from AMFI's scheme category
and, when the broker gives no price, it is valued at that NAV. Only a fund
AMFI does not list is classed from its name (gold, debt, international,
else equity). Every row records how its class was decided; a manual entry
states its own class.

A listed stock with no price from the broker (Dhan's and Groww's holdings
APIs give none) is valued at its latest close in the app's price store.
"""
from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import PortfolioHolding, Stock

ASSET_CLASSES = ("EQUITY", "EQUITY_FUND", "DEBT", "GOLD", "CASH", "INTERNATIONAL", "OTHER")
_GOLD = re.compile(r"\bGOLD|SILVER\b", re.I)
_DEBT = re.compile(r"LIQUID|DEBT|GILT|BOND|MONEY MARKET|OVERNIGHT|CORPORATE|BANKING (&|AND) PSU|CREDIT RISK|DURATION|"
                   r"FIXED|TREASURY|SDL|ARBITRAGE|FLOATER|CPSE BOND|BHARAT BOND|LIQUIDBEES", re.I)
_INTL = re.compile(r"NASDAQ|S&P ?500|\bUS\b|U\.S\.|INTERNATIONAL|GLOBAL|OVERSEAS|WORLD|HANG SENG|JAPAN|CHINA|EMERGING|MAFANG|NYSE", re.I)


def classify_fund(name: str) -> str:
    if _GOLD.search(name):
        return "GOLD"
    if _DEBT.search(name):
        return "DEBT"
    if _INTL.search(name):
        return "INTERNATIONAL"
    return "EQUITY_FUND"


def _match(db: Session, isin: str | None, symbol: str | None) -> Stock | None:
    if isin:
        s = db.query(Stock).filter(Stock.isin == isin.strip().upper()).first()
        if s:
            return s
    if symbol:
        sym = symbol.strip().upper().replace("-EQ", "").replace("-BE", "")
        return db.query(Stock).filter(Stock.symbol == sym, Stock.is_active.is_(True)).first()
    return None


def _latest_close(db: Session, stock_id: str) -> float | None:
    from app.infrastructure.database.models import PriceBar

    bar = db.query(PriceBar).filter(PriceBar.stock_id == stock_id).order_by(PriceBar.bar_date.desc()).first()
    return float(bar.close) if bar else None


def _row(db: Session, source: str, *, symbol=None, isin=None, name=None, qty=None, avg=None, last=None, value=None,
         asset_class: str | None = None, raw=None, now=None) -> PortfolioHolding | None:
    from app.portfolio import amfi

    qty = float(qty) if qty not in (None, "") else None
    last = float(last) if last not in (None, "") else None
    stock = _match(db, isin, symbol) if asset_class in (None, "EQUITY") else None
    fund = amfi.lookup(db, isin) if stock is None else None
    priced = None
    if last is None and value in (None, "") and qty:
        if stock is not None:
            last, priced = _latest_close(db, stock.id), "latest close in the price store"
        elif fund is not None and fund.nav is not None:
            last, priced = float(fund.nav), f"AMFI NAV of {fund.nav_date}"
    value = float(value) if value not in (None, "") else (qty * last if qty is not None and last is not None else None)
    if not value:
        return None
    basis = "stated"
    if asset_class is None:
        if stock is not None:
            asset_class, basis = "EQUITY", "matched to a listed stock"
        elif fund is not None:
            asset_class, basis = fund.asset_class, fund.class_basis
            name = name if name and name != isin else fund.scheme_name
        else:
            asset_class, basis = classify_fund(f"{name or ''} {symbol or ''}"), "classified from the name (not in AMFI's list)"
    if priced:
        basis = f"{basis}; valued at the {priced}"
    return PortfolioHolding(
        id=str(uuid.uuid4()), source=source, stock_id=stock.id if stock else None, symbol=(symbol or (stock and stock.symbol)),
        isin=isin, name=(stock.company_name if stock and (not name or name == symbol) else name or symbol) or "unnamed", asset_class=asset_class,
        class_basis=basis, quantity=qty, avg_price=float(avg) if avg not in (None, "") else None, last_price=last,
        value=round(value, 2), as_of=now or datetime.now(timezone.utc), raw=raw,
    )


def replace_source(db: Session, sources: tuple[str, ...], rows: list[PortfolioHolding]) -> int:
    db.query(PortfolioHolding).filter(PortfolioHolding.source.in_(sources)).delete(synchronize_session=False)
    db.add_all(rows)
    db.commit()
    return len(rows)


def from_kite(db: Session, holdings: list[dict], mf: list[dict] | None, margins: dict | None) -> dict:
    now = datetime.now(timezone.utc)
    rows = []
    for h in holdings or []:
        qty = (h.get("quantity") or 0) + (h.get("t1_quantity") or 0)
        r = _row(db, "KITE", symbol=h.get("tradingsymbol"), isin=h.get("isin"), name=h.get("tradingsymbol"), qty=qty,
                 avg=h.get("average_price"), last=h.get("last_price") or h.get("close_price"), raw=h, now=now)
        if r:
            rows.append(r)
    for f in mf or []:
        # Kite's tradingsymbol for a mutual fund is its ISIN
        r = _row(db, "KITE_MF", symbol=f.get("tradingsymbol"), isin=f.get("tradingsymbol"), name=f.get("fund"),
                 qty=f.get("quantity"), avg=f.get("average_price"), last=f.get("last_price"), raw=f, now=now)
        if r:
            r.stock_id = None  # a fund is never a listed stock, even if a symbol happened to match
            rows.append(r)
    cash = None
    if margins:
        eq = margins.get("equity") or margins
        cash = ((eq.get("available") or {}).get("live_balance") if isinstance(eq.get("available"), dict) else None) or eq.get("net")
    if cash:
        rows.append(PortfolioHolding(id=str(uuid.uuid4()), source="KITE_CASH", name="Kite equity margin (cash)", asset_class="CASH",
                                     class_basis="broker cash balance", value=round(float(cash), 2), as_of=now, raw=None))
    n = replace_source(db, ("KITE", "KITE_MF", "KITE_CASH"), rows)
    return {"rows": n, "unmatched": [r.name for r in rows if r.asset_class == "EQUITY_FUND" and r.source == "KITE"]}


_ALIASES = {
    "symbol": ("symbol", "instrument", "tradingsymbol", "trading symbol", "scrip", "stock", "security", "name", "stock name"),
    "isin": ("isin", "isin code"),
    "qty": ("qty", "qty.", "quantity", "quantity available", "shares", "units", "net qty"),
    "avg": ("avg. cost", "avg cost", "average price", "avg price", "buy avg", "average cost", "avg. price"),
    "last": ("ltp", "last price", "current price", "market price", "previous closing price", "close", "cmp"),
    "value": ("cur. val", "current value", "market value", "present value", "value"),
}


def from_csv(db: Session, text: str, source: str = "CSV") -> dict:
    """Any holdings CSV with a symbol or ISIN column and either quantity and
    price or a value column (Dhan, Zerodha console, most brokers)."""
    lines = text.lstrip("﻿").splitlines()
    # skip any title lines above the header
    start = next((i for i, l in enumerate(lines) if any(a in l.lower() for a in ("symbol", "instrument", "isin", "scrip"))), 0)
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    cols = {}
    for field in reader.fieldnames or []:
        key = field.strip().lower()
        for want, names in _ALIASES.items():
            if key in names and want not in cols:
                cols[want] = field
    if "symbol" not in cols and "isin" not in cols:
        raise ValueError("no symbol or ISIN column found; expected one of: " + ", ".join(_ALIASES["symbol"] + _ALIASES["isin"]))
    now = datetime.now(timezone.utc)
    rows, skipped = [], 0

    def num(r, k):
        v = (r.get(cols[k]) or "").replace(",", "").replace("₹", "").strip() if k in cols else ""
        return v or None

    for r in reader:
        row = _row(db, source, symbol=(r.get(cols["symbol"]) or "").strip() if "symbol" in cols else None,
                   isin=(r.get(cols["isin"]) or "").strip() if "isin" in cols else None,
                   name=(r.get(cols["symbol"]) or "").strip() if "symbol" in cols else None,
                   qty=num(r, "qty"), avg=num(r, "avg"), last=num(r, "last"), value=num(r, "value"), raw=dict(r), now=now)
        if row:
            rows.append(row)
        else:
            skipped += 1
    n = replace_source(db, (source,), rows)
    return {"rows": n, "skipped": skipped, "matched_stocks": sum(1 for r in rows if r.stock_id)}


def from_broker(db: Session, source: str, holdings: list[dict]) -> dict:
    """Rows from app/portfolio/brokers.py (already in the common shape:
    symbol, isin, name, qty, avg, last). Replaces that broker's rows."""
    now = datetime.now(timezone.utc)
    rows, skipped = [], []
    for h in holdings:
        r = _row(db, source, symbol=h.get("symbol"), isin=h.get("isin"), name=h.get("name") or h.get("symbol"),
                 qty=h.get("qty"), avg=h.get("avg"), last=h.get("last"), raw=h.get("raw"), now=now)
        if r:
            rows.append(r)
        else:
            skipped.append(h.get("symbol") or h.get("isin"))
    n = replace_source(db, (source,), rows)
    return {"rows": n, "matched_stocks": sum(1 for r in rows if r.stock_id), "no_price": skipped}


def add_manual(db: Session, name: str, asset_class: str, value: float, symbol: str | None = None) -> PortfolioHolding:
    if asset_class not in ASSET_CLASSES:
        raise ValueError(f"asset class must be one of {', '.join(ASSET_CLASSES)}")
    stock = _match(db, None, symbol) if symbol and asset_class == "EQUITY" else None
    row = PortfolioHolding(id=str(uuid.uuid4()), source="MANUAL", stock_id=stock.id if stock else None, symbol=symbol,
                           name=name, asset_class=asset_class, class_basis="stated", value=round(float(value), 2),
                           as_of=datetime.now(timezone.utc))
    db.add(row)
    db.commit()
    return row
