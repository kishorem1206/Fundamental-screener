"""Historical valuation endpoints — Architecture v2 Stage 4."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import BulkMetrics, Stock, ValuationHistory
from app.logger import logger

router = APIRouter(prefix="/api/valuation")


def _row_to_dict(row: ValuationHistory) -> dict:
    return {
        "period_end": row.period_end,
        "eps": float(row.eps) if row.eps is not None else None,
        "eps_source": row.eps_source,
        "price": float(row.price) if row.price is not None else None,
        "price_date": row.price_date,
        "pe": float(row.pe) if row.pe is not None else None,
        "book_value_per_share": float(row.book_value_per_share) if row.book_value_per_share is not None else None,
        "bvps_source": row.bvps_source,
        "pb": float(row.pb) if row.pb is not None else None,
    }


@router.get("/{company_id:path}/history")
def get_valuation_history(company_id: str):
    """Every fiscal year's historical P/E and P/B, oldest first."""
    db = get_db()
    try:
        rows = (
            db.query(ValuationHistory).filter_by(company_id=company_id)
            .order_by(ValuationHistory.period_end).all()
        )
        return {"company_id": company_id, "history": [_row_to_dict(r) for r in rows]}
    finally:
        db.close()


@router.get("/{company_id:path}/position")
def get_valuation_position(company_id: str):
    """Current P/E and (if available) P/B vs this company's own historical
    median/percentile. Current P/E is read from fa_bulk_metrics if present
    (Stage 2's cache), falling back to a live yfinance fetch."""
    from app.calculations.historical_valuation import compute_valuation_position

    db = get_db()
    try:
        stock = db.query(Stock).filter_by(id=company_id).first()
        if stock is None:
            raise HTTPException(status_code=404, detail=f"Stock {company_id} not found")

        bulk = db.query(BulkMetrics).filter_by(stock_id=company_id).first()
        current_pe = (bulk.metrics or {}).get("pe_ratio") if bulk else None
        current_pb = (bulk.metrics or {}).get("pb_ratio") if bulk else None
        if current_pe is None:
            from app.calculations.engine import compute_metrics
            from app.data.yfinance_client import fetch_financial_data
            try:
                metrics = compute_metrics(fetch_financial_data(stock.exchange, stock.symbol))
                current_pe = metrics.get("pe_ratio")
                current_pb = metrics.get("pb_ratio")
            except Exception as e:
                logger.warning("valuation: live pe fetch failed", company_id=company_id, error=str(e))

        return {
            "company_id": company_id,
            **compute_valuation_position(db, company_id, current_pe, current_pb),
        }
    except HTTPException:
        raise
    finally:
        db.close()


@router.post("/{company_id:path}/ingest")
def trigger_valuation_ingest(company_id: str):
    """Fetch/refresh historical P/E and P/B for one company, synchronously."""
    from app.ingestion.valuation_history_client import ingest_valuation_history

    db = get_db()
    try:
        stock = db.query(Stock).filter_by(id=company_id).first()
        if stock is None:
            raise HTTPException(status_code=404, detail=f"Stock {company_id} not found")
        result = ingest_valuation_history(db, company_id=company_id, symbol=stock.symbol, exchange=stock.exchange)
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.warning("valuation: ingest trigger failed", company_id=company_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
