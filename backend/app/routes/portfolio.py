"""Portfolio: holdings, analysis, Kite connection (read-only), CSV upload, manual entries, settings."""
from fastapi import APIRouter, Body, HTTPException, Request

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import PortfolioHolding
from app.portfolio import analysis, importers
from app.portfolio.kite_link import kite

router = APIRouter(prefix="/api/portfolio")


@router.get("")
def get_portfolio():
    db = get_db()
    try:
        return analysis.analyse(db)
    finally:
        db.close()


@router.get("/kite/status")
def kite_status():
    profile = kite.logged_in()
    return {"connected": profile is not None, "user": profile and {k: profile.get(k) for k in ("user_name", "user_id", "broker")}}


@router.post("/kite/login")
def kite_login():
    try:
        return {"login_url": kite.login_url()}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Could not reach Kite: {exc}")


@router.post("/kite/sync")
def kite_sync():
    """Reads holdings, mutual funds and the cash margin from Kite and replaces the Kite rows."""
    try:
        holdings = kite.call_json("get_holdings")
        mf = kite.call_json("get_mf_holdings")
        margins = kite.call_json("get_margins")
    except LookupError as exc:
        raise HTTPException(401, f"Kite is not logged in: {exc}. Use 'Connect Kite' first.")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Kite read failed: {exc}")
    holdings = holdings.get("data", holdings) if isinstance(holdings, dict) else holdings
    mf = mf.get("data", mf) if isinstance(mf, dict) else mf
    db = get_db()
    try:
        return importers.from_kite(db, holdings, mf, margins if isinstance(margins, dict) else None)
    finally:
        db.close()


@router.post("/import/csv")
async def import_csv(request: Request, source: str = "CSV"):
    """Body: the CSV text. `source` names the broker (e.g. DHAN_CSV) so a later upload replaces only that broker's rows."""
    text = (await request.body()).decode("utf-8", "replace")
    db = get_db()
    try:
        return importers.from_csv(db, text, source=source.upper())
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    finally:
        db.close()


@router.post("/manual")
def add_manual(name: str = Body(...), asset_class: str = Body(...), value: float = Body(...), symbol: str | None = Body(None)):
    db = get_db()
    try:
        row = importers.add_manual(db, name, asset_class.upper(), value, symbol)
        return {"id": row.id}
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    finally:
        db.close()


@router.delete("/holdings/{holding_id}")
def delete_holding(holding_id: str):
    db = get_db()
    try:
        n = db.query(PortfolioHolding).filter(PortfolioHolding.id == holding_id).delete()
        db.commit()
        return {"deleted": n}
    finally:
        db.close()


@router.get("/settings")
def get_settings():
    db = get_db()
    try:
        return analysis.settings(db)
    finally:
        db.close()


@router.put("/settings")
def put_settings(body: dict = Body(...)):
    db = get_db()
    try:
        return analysis.save_settings(db, body)
    finally:
        db.close()


@router.post("/reprice")
def reprice():
    """Latest NSE close for every listed stock held, from NSE's bhavcopy server — for holdings
    that came from a CSV or were entered by hand and so have no broker price feed."""
    from datetime import datetime, timezone

    from app.infrastructure.database.models import Stock
    from app.nse_mcp.client import NseMcpError, bhavcopy

    db = get_db()
    try:
        rows = [h for h in db.query(PortfolioHolding).all() if h.stock_id and h.quantity]
        symbols = sorted({db.get(Stock, h.stock_id).symbol for h in rows})
        prices = {}
        try:
            for i in range(0, len(symbols), 50):
                data = bhavcopy.call("get_bulk_quote", symbols=symbols[i:i + 50])
                prices.update({q["symbol"]: q for q in (data.get("quotes", []) if isinstance(data, dict) else [])})
        except NseMcpError as exc:
            raise HTTPException(502, f"NSE did not answer: {exc}")
        updated = 0
        for h in rows:
            q = prices.get(db.get(Stock, h.stock_id).symbol)
            if q and q.get("close"):
                h.last_price, h.value = q["close"], round(float(h.quantity) * q["close"], 2)
                h.as_of = datetime.now(timezone.utc)
                updated += 1
        db.commit()
        return {"updated": updated, "of": len(rows), "price_date": next((q.get("date") for q in prices.values()), None)}
    finally:
        db.close()
