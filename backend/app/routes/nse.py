"""NSE's MCP servers: status, live quote, market breadth (app/nse_mcp/)."""
from datetime import date

from fastapi import APIRouter, HTTPException

from app.infrastructure.redis.client import cache_get_json, cache_set_json
from app.nse_mcp.client import BHAVCOPY, MARKET, NseMcpError, bhavcopy, market

router = APIRouter(prefix="/api/nse")


@router.get("/status")
def status():
    """Whether each server answers, and the tools it offers."""
    cached = cache_get_json("nse:status")
    if cached:
        return cached
    out = {}
    for name, client, url in (("bhavcopy", bhavcopy, BHAVCOPY), ("market", market, MARKET)):
        try:
            out[name] = {"url": url, "reachable": True, "tools": sorted(t["name"] for t in client.tools())}
        except Exception as exc:  # noqa: BLE001
            out[name] = {"url": url, "reachable": False, "error": str(exc)[:200]}
    cache_set_json("nse:status", out, 600)
    return out


@router.get("/quote/{symbol}")
def quote(symbol: str):
    """Live quote (refreshes each minute in market hours; the last close otherwise)."""
    key = f"nse:quote:{symbol.upper()}"
    cached = cache_get_json(key)
    if cached:
        return cached
    try:
        data = market.call("cm_get_stock_quote", symbol=symbol.upper())
    except NseMcpError as exc:
        raise HTTPException(502, f"NSE did not answer: {exc}")
    s = (data or {}).get("stock") if isinstance(data, dict) else None
    if not s:
        raise HTTPException(404, f"NSE has no live quote for '{symbol}'")
    out = {"symbol": s["symbol"], "series": s.get("series"), "last_price": s.get("lastTradedPrice"), "previous_close": s.get("preClosePrice"),
           "change": s.get("change"), "change_pct": s.get("perChange"), "open": s.get("openPrice"), "high": s.get("highPrice"),
           "low": s.get("lowPrice"), "volume": s.get("volume"), "week52_high": s.get("fiftyTwoWeekHigh"),
           "week52_low": s.get("fiftyTwoWeekLow"), "as_of": s.get("latestTimestamp"), "source": "NSE (cm-market MCP)"}
    cache_set_json(key, out, 60)
    return out


@router.get("/breadth")
def breadth(day: str | None = None):
    """Advances, declines and total volume across NSE for a trading day (default: the latest)."""
    day = day or date.today().isoformat()
    key = f"nse:breadth:{day}"
    cached = cache_get_json(key)
    if cached:
        return cached
    try:
        out = bhavcopy.call("get_market_breadth", date=day)
    except NseMcpError as exc:
        raise HTTPException(502, f"NSE did not answer: {exc}")
    cache_set_json(key, out, 1800)
    return out
