"""Holdings from broker APIs other than Kite — read only.

Each broker is called with the user's own access token from backend/.env
(never from the browser, never logged). Only the holdings endpoint is
called; nothing here can place, modify or cancel an order.

    DHAN_ACCESS_TOKEN    GET https://api.dhan.co/v2/holdings
                         header access-token; fields exchange, tradingSymbol,
                         securityId, isin, totalQty, dpQty, t1Qty,
                         availableQty, collateralQty, avgCostPrice (no price)
    UPSTOX_ACCESS_TOKEN  GET https://api.upstox.com/v2/portfolio/long-term-holdings
                         Authorization: Bearer; {"status", "data": [{isin,
                         company_name, trading_symbol | tradingsymbol,
                         quantity, t1_quantity, average_price, last_price,
                         close_price, …}]}
    GROWW_ACCESS_TOKEN   GET https://api.groww.in/v1/holdings/user
                         Authorization: Bearer, X-API-VERSION: 1.0;
                         {"status", "payload": {"holdings": [{isin,
                         trading_symbol, quantity, average_price, …}]}}
                         (no price); Groww's trade API is a paid subscription

A holding with no price from the broker is valued at the stock's latest
close in the app's price store, or a fund's AMFI NAV (importers._row).
Every row is returned in one shape: symbol, isin, name, qty, avg, last, raw.
"""
from __future__ import annotations

import httpx

from app.config import config

BROKERS = {
    "DHAN": {"label": "Dhan", "setting": "dhan_access_token", "env": "DHAN_ACCESS_TOKEN"},
    "UPSTOX": {"label": "Upstox", "setting": "upstox_access_token", "env": "UPSTOX_ACCESS_TOKEN"},
    "GROWW": {"label": "Groww", "setting": "groww_access_token", "env": "GROWW_ACCESS_TOKEN"},
}


class BrokerError(Exception):
    pass


def configured() -> dict[str, bool]:
    return {name: bool(getattr(config, b["setting"], "")) for name, b in BROKERS.items()}


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def parse_dhan(data) -> list[dict]:
    rows = data if isinstance(data, list) else (data or {}).get("data") or []
    out = []
    for h in rows:
        qty = _num(h.get("totalQty"))
        if qty is None:
            qty = (_num(h.get("dpQty")) or 0) + (_num(h.get("t1Qty")) or 0)
        out.append({"symbol": h.get("tradingSymbol"), "isin": h.get("isin"), "name": h.get("tradingSymbol"), "qty": qty,
                    "avg": _num(h.get("avgCostPrice")), "last": _num(h.get("lastTradedPrice") or h.get("ltp")), "raw": h})
    return out


def parse_upstox(data) -> list[dict]:
    if isinstance(data, dict) and data.get("status") not in (None, "success"):
        raise BrokerError(f"Upstox answered {data.get('status')}: {data.get('errors') or data.get('message')}")
    rows = (data or {}).get("data") or [] if isinstance(data, dict) else data or []
    out = []
    for h in rows:
        qty = (_num(h.get("quantity")) or 0) + (_num(h.get("t1_quantity")) or 0)
        out.append({"symbol": h.get("trading_symbol") or h.get("tradingsymbol"), "isin": h.get("isin"),
                    "name": h.get("company_name") or h.get("trading_symbol") or h.get("tradingsymbol"), "qty": qty,
                    "avg": _num(h.get("average_price")), "last": _num(h.get("last_price")) or _num(h.get("close_price")), "raw": h})
    return out


def parse_groww(data) -> list[dict]:
    if isinstance(data, dict) and data.get("status") not in (None, "SUCCESS"):
        raise BrokerError(f"Groww answered {data.get('status')}: {data.get('error') or data.get('message')}")
    rows = ((data or {}).get("payload") or {}).get("holdings") or [] if isinstance(data, dict) else []
    return [{"symbol": h.get("trading_symbol"), "isin": h.get("isin"), "name": h.get("trading_symbol"),
             "qty": _num(h.get("quantity")), "avg": _num(h.get("average_price")), "last": None, "raw": h} for h in rows]


def _get(url: str, headers: dict) -> object:
    try:
        r = httpx.get(url, headers={"Accept": "application/json", **headers}, timeout=30)
    except httpx.HTTPError as exc:
        raise BrokerError(f"could not reach {url.split('/')[2]}: {exc}") from exc
    if r.status_code in (401, 403):
        raise BrokerError("the access token was refused (expired or wrong) — generate a new one and update backend/.env")
    if r.status_code >= 400 and "no holding" in r.text.lower():  # Dhan answers an empty account with an error
        return []
    if r.status_code >= 400:
        raise BrokerError(f"{url.split('/')[2]} answered HTTP {r.status_code}: {r.text[:200]}")
    return r.json()


def fetch(broker: str) -> list[dict]:
    broker = broker.upper()
    if broker not in BROKERS:
        raise BrokerError(f"unknown broker '{broker}'; one of {', '.join(BROKERS)}")
    token = getattr(config, BROKERS[broker]["setting"], "")
    if not token:
        raise BrokerError(f"{BROKERS[broker]['env']} is not set in backend/.env")
    if broker == "DHAN":
        return parse_dhan(_get("https://api.dhan.co/v2/holdings", {"access-token": token, "Content-Type": "application/json"}))
    if broker == "UPSTOX":
        return parse_upstox(_get("https://api.upstox.com/v2/portfolio/long-term-holdings", {"Authorization": f"Bearer {token}"}))
    return parse_groww(_get("https://api.groww.in/v1/holdings/user", {"Authorization": f"Bearer {token}", "X-API-VERSION": "1.0"}))
