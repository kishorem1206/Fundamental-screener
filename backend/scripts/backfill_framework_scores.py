"""Framework scores (FULL basis) for companies whose full analysis finished
before the framework existed — computed from each stock's latest completed
analysis as stored, without re-running it.

    cd backend && .venv/bin/python -m scripts.backfill_framework_scores
"""
from app.framework import engine, store
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import FundamentalAnalysis, Stock
from app.sectors.registry import get_framework


def main() -> None:
    db = get_db()
    try:
        done: set[str] = set()
        analyses = (db.query(FundamentalAnalysis).filter(FundamentalAnalysis.status == "COMPLETED")
                    .order_by(FundamentalAnalysis.created_at.desc()).all())
        for a in analyses:
            if a.stock_id in done or not a.scores or not a.metrics:
                continue
            stock = db.get(Stock, a.stock_id)
            if stock is None:
                continue
            name = get_framework(stock.sector or "", industry=stock.industry or "", basic_industry=stock.basic_industry or "").sector_name
            out = engine.score_company(db, stock.id, store.FULL, a.scores, a.metrics, a.financial_data or {}, name)
            db.commit()
            done.add(a.stock_id)
            print(f"  {stock.symbol:<12} fundamental {out['fundamental']['score']}  trend {out['trend']['trend']}")
        print(f"{len(done)} companies")
    finally:
        db.close()


if __name__ == "__main__":
    main()
