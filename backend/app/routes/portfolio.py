"""Portfolio: holdings, analysis, Kite connection (read-only), Dhan / Upstox / Groww holdings
(read-only, tokens from backend/.env), CSV upload, manual entries, settings, AMFI NAVs."""
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
        from app.portfolio import amfi

        try:
            amfi.ensure_fresh(db)
        except Exception:  # noqa: BLE001 — funds then fall back to the name
            db.rollback()
        return importers.from_kite(db, holdings, mf, margins if isinstance(margins, dict) else None)
    finally:
        db.close()


@router.get("/brokers")
def brokers_status():
    """Which broker tokens are set in backend/.env (never the tokens themselves)."""
    from app.portfolio.brokers import BROKERS, configured

    have = configured()
    return [{"broker": k, "label": b["label"], "configured": have[k], "env": b["env"]} for k, b in BROKERS.items()]


@router.post("/broker/{broker}/sync")
def broker_sync(broker: str):
    """Reads that broker's holdings (read-only) and replaces its rows."""
    from app.portfolio.brokers import BrokerError, fetch

    try:
        holdings = fetch(broker)
    except BrokerError as exc:
        raise HTTPException(400, str(exc))
    db = get_db()
    try:
        from app.portfolio import amfi

        try:
            amfi.ensure_fresh(db)
        except Exception:  # noqa: BLE001 — funds then fall back to the name
            db.rollback()
        return importers.from_broker(db, broker.upper(), holdings)
    finally:
        db.close()


@router.post("/amfi/refresh")
def amfi_refresh():
    """Download AMFI's NAV file now (also done by Kite and broker syncs when older than a day)."""
    from app.portfolio import amfi

    db = get_db()
    try:
        return amfi.refresh(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"AMFI did not answer: {exc}")
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
    """Latest NSE close for every listed stock held, from NSE's bhavcopy server, and the latest
    AMFI NAV for every fund held by ISIN — for holdings that came from a CSV, a broker without a
    price feed, or were entered by hand."""
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
        from app.portfolio import amfi

        nav_date = None
        try:
            amfi.ensure_fresh(db)
            funds = [h for h in db.query(PortfolioHolding).all() if not h.stock_id and h.isin and h.quantity]
            for h in funds:
                f = amfi.lookup(db, h.isin)
                if f and f.nav is not None and not amfi.stale(f.nav_date):
                    h.last_price, h.value = f.nav, round(float(h.quantity) * float(f.nav), 2)
                    h.as_of = datetime.now(timezone.utc)
                    nav_date = max(nav_date or f.nav_date, f.nav_date)
                    updated += 1
        except Exception:  # noqa: BLE001 — stocks are still repriced
            db.rollback()
            funds = []
        db.commit()
        return {"updated": updated, "of": len(rows) + len(funds), "price_date": next((q.get("date") for q in prices.values()), None),
                "nav_date": nav_date.isoformat() if nav_date else None}
    finally:
        db.close()
