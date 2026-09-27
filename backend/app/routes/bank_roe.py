"""ROE -> P/B diagnostics + precomputed scenarios for lenders (banks/NBFCs/HFCs/MFIs).

Backs the "ROE & Valuation" tab. The slider re-simulation runs client-side
(a TypeScript port of `simulate()`, like the mentor's own page — instant, and
it keeps working in the offline HTML export); this endpoint returns the
company's starting state, diagnostics and the five preset scenarios. All maths lives in
`app/calculations/bank_roe_engine.py` (a tested port of the mentor's
IDFC FIRST ROE simulator); this module only assembles inputs from the
yfinance snapshot, the Screener-sourced quarterly ledger and the historical
valuation table. Compute-on-read, no persistence.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.calculations import bank_roe_engine as eng
from app.data import yfinance_client
from app.infrastructure.database import metric_store
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock, ValuationHistory
from app.logger import logger
from app.sectors.registry import get_framework

router = APIRouter(prefix="/api/bank-roe")

# Lender frameworks whose economics are book-value / ROE driven. Insurance
# is deliberately excluded (embedded-value economics, not this model).
_LENDER_FRAMEWORKS = {"Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans"}
_RATIO_KEYS = ("cost_to_income_ratio", "credit_cost", "roa")


def _year_map(series) -> dict:
    return {fy: v for fy, v in (series or []) if v is not None}


def _assemble_inputs(db, stock: Stock) -> dict | None:
    data = yfinance_client.fetch_financial_data(stock.exchange, stock.symbol)
    market = data.get("market") or {}
    inc, bal = data.get("income") or {}, data.get("balance") or {}
    ni = inc.get("net_income") or {}
    if isinstance(ni, list):
        ni = _year_map(ni)

    quarterly = []
    for st in ("STANDALONE", "CONSOLIDATED"):  # a bank's own ROE: standalone first
        hist = metric_store.get_metric_history(db, stock.id, "qtr_net_profit", statement_type=st)
        rows = sorted({r.period: float(r.value) for r in hist if r.period != "TTM"}.items())
        if len(rows) >= 2:
            quarterly = rows
            break

    ratios = {}
    for k in _RATIO_KEYS:
        row = metric_store.get_latest_period_value(db, stock.id, k)
        if row is not None and row.confidence in ("HIGH", "MEDIUM"):
            ratios[k] = float(row.value)

    bvps_by_fy = {
        r.period_end: float(r.book_value_per_share)
        for r in db.query(ValuationHistory).filter_by(company_id=stock.id).all()
        if r.book_value_per_share is not None
    }

    return {
        "price": market.get("current_price"), "bvps": market.get("book_value"),
        "shares": market.get("shares_outstanding"), "payout_ratio": market.get("payout_ratio"),
        "trailing_eps": market.get("trailing_eps"),
        "equity": _year_map(bal.get("total_equity")) if isinstance(bal.get("total_equity"), list) else (bal.get("total_equity") or {}),
        "assets": _year_map(bal.get("total_assets")) if isinstance(bal.get("total_assets"), list) else (bal.get("total_assets") or {}),
        "net_income": ni, "quarterly_pat_cr": quarterly, "bvps_by_fy": bvps_by_fy, "ratios": ratios,
    }


def _load(company_id: str):
    db = get_db()
    stock = db.query(Stock).filter_by(id=company_id).first()
    if stock is None:
        db.close()
        raise HTTPException(status_code=404, detail=f"Stock {company_id} not found")
    fw = get_framework(stock.sector, stock.industry, stock.basic_industry)
    if fw.sector_name not in _LENDER_FRAMEWORKS:
        db.close()
        return None, None, fw.sector_name
    return db, stock, fw.sector_name


@router.get("/{company_id:path}")
def get_bank_roe(company_id: str):
    db, stock, sector_name = _load(company_id)
    if db is None:
        return {"available": False, "sector_name": sector_name,
                "reason": "ROE/P-B modelling applies to lenders (banks, NBFCs, HFCs, MFIs) only"}
    try:
        inputs = _assemble_inputs(db, stock)
        result = eng.compute_bank_roe_analysis(inputs or {})
        result["sector_name"] = sector_name
        return result
    except Exception as e:  # never 500 the tab on a data hiccup
        logger.warning("bank_roe: failed", company_id=company_id, error=str(e))
        return {"available": False, "sector_name": sector_name, "reason": "market/financial data unavailable right now"}
    finally:
        db.close()


def bank_roe_for_stock(db, stock: Stock) -> dict | None:
    """Engine result for a lender, or None for a non-lender / unavailable
    company. Shared by the REST route and the PDF report mapper so both
    surfaces show identical numbers. Never raises."""
    try:
        fw = get_framework(stock.sector, stock.industry, stock.basic_industry)
        if fw.sector_name not in _LENDER_FRAMEWORKS:
            return None
        result = eng.compute_bank_roe_analysis(_assemble_inputs(db, stock) or {})
        result["sector_name"] = fw.sector_name
        return result if result.get("available") else None
    except Exception as e:
        logger.warning("bank_roe: report entry failed", company_id=stock.id, error=str(e))
        return None
