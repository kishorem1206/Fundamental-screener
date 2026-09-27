"""Cascading Macro Sector -> Sector -> Industry -> Basic Industry screening
over `stocks` (all ~1610 stocks classified via Screener.in,
scripts/classify_stocks_screener.py).

`fa_stock_classification` — the table this module used to query — was
retired 2026-09-17: it was a separate, ~1610-row shadow copy of the same
classification data, requiring a manual sync script (scripts/
classify_missing_stocks.py) to stay in sync with `stocks`. Since `stocks`
was expanded to the same ~1610-company universe (imported directly from
fa_stock_classification's data), there was no longer a reason to keep two
copies — `stocks` is now the single source of truth for every company this
app knows about, classification included. Every stock returned here already
has a real `stocks.id`, so the old LEFT JOIN + `analyzable` distinction
(used to flag companies known to Screener's classification but absent from
the smaller, curated `stocks` table) no longer applies — every row is
analyzable by construction now.

Descriptions come from fa_industry_taxonomy.definition (NSE's official
Industry Classification Structure reference data, migration 0007), keyed by
basic_industry — the only level that carries its own definition text.
"""
from fastapi import APIRouter, BackgroundTasks, Query
from sqlalchemy import bindparam, text

from app.infrastructure.database.client import get_db
from app.logger import logger

router = APIRouter(prefix="/api/screening")


@router.get("/taxonomy")
def get_taxonomy():
    """Every distinct (macro_sector, sector, industry, basic_industry)
    combination actually present in `stocks` — i.e. only branches that have
    at least one real stock, not the full NSE reference taxonomy (some of
    which has no classified stock yet). Frontend derives each dropdown's
    options from this single list based on the levels already chosen,
    rather than round-tripping per level."""
    db = get_db()
    try:
        rows = db.execute(text(
            """
            SELECT DISTINCT macro_sector, sector, industry, basic_industry
            FROM stocks
            WHERE is_active = true
              AND macro_sector IS NOT NULL
              AND sector IS NOT NULL
              AND industry IS NOT NULL
              AND basic_industry IS NOT NULL
            ORDER BY macro_sector, sector, industry, basic_industry
            """
        )).all()
        return {
            "combinations": [
                {
                    "macro_sector": r.macro_sector,
                    "sector": r.sector,
                    "industry": r.industry,
                    "basic_industry": r.basic_industry,
                }
                for r in rows
            ]
        }
    finally:
        db.close()


@router.get("/stocks")
def screen_stocks(
    macro_sector: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    basic_industry: str | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=2000),
):
    """Filtered stock list from `stocks` (the full ~1610-stock universe).
    Every row already has a real `stocks.id`, so `analyzable` is always
    true now — kept in the response shape for frontend backward
    compatibility rather than dropped. Also returns, for every
    basic_industry present in the result, its definition from
    fa_industry_taxonomy — the frontend groups stocks under their
    basic_industry and shows this description above each group.
    """
    db = get_db()
    try:
        clauses = [
            "is_active = true",
            "macro_sector IS NOT NULL",
            "sector IS NOT NULL",
            "industry IS NOT NULL",
            "basic_industry IS NOT NULL",
        ]
        params: dict = {"limit": limit}
        if macro_sector:
            clauses.append("macro_sector = :macro_sector")
            params["macro_sector"] = macro_sector
        if sector:
            clauses.append("sector = :sector")
            params["sector"] = sector
        if industry:
            clauses.append("industry = :industry")
            params["industry"] = industry
        if basic_industry:
            clauses.append("basic_industry = :basic_industry")
            params["basic_industry"] = basic_industry
        where = " AND ".join(clauses)

        rows = db.execute(
            text(
                f"""
                SELECT symbol, company_name, market_cap,
                       macro_sector, sector, industry, basic_industry,
                       id AS stock_id, exchange
                FROM stocks
                WHERE {where}
                ORDER BY basic_industry, market_cap DESC NULLS LAST, company_name
                LIMIT :limit
                """
            ),
            params,
        ).all()

        stocks = [
            {
                "symbol": r.symbol,
                "company_name": r.company_name,
                "market_cap_cr": float(r.market_cap) / 1e7 if r.market_cap is not None else None,
                "macro_sector": r.macro_sector,
                "sector": r.sector,
                "industry": r.industry,
                "basic_industry": r.basic_industry,
                "stock_id": r.stock_id,
                "exchange": r.exchange,
                "analyzable": True,
            }
            for r in rows
        ]

        basic_industries = sorted({s["basic_industry"] for s in stocks})
        descriptions: dict[str, str | None] = {}
        if basic_industries:
            stmt = text(
                "SELECT basic_industry, definition FROM fa_industry_taxonomy "
                "WHERE basic_industry IN :names"
            ).bindparams(bindparam("names", expanding=True))
            def_rows = db.execute(stmt, {"names": basic_industries}).all()
            descriptions = {r.basic_industry: r.definition for r in def_rows}

        return {"stocks": stocks, "count": len(stocks), "descriptions": descriptions}
    finally:
        db.close()


# ── Declarative rule-based screening (Architecture v2 Stage 2) ─────────────
# Distinct from the taxonomy browser above: this evaluates real metric
# thresholds (app/screening/rules.yaml) via app/screening/engine.py, over
# the whole active stock universe (app/screening/bulk_metrics.py's cache) —
# not just a sector/industry filter.

@router.get("/rules")
def list_screening_rules():
    """Every declarative rule set available to /run/{name}."""
    from app.screening.engine import list_rule_sets
    return {"rule_sets": list_rule_sets()}


@router.get("/run/{rule_set_name}")
def run_screening_rule(rule_set_name: str, limit: int = Query(default=2000, ge=1, le=5000)):
    """Evaluate one rule set against every stock it applies to — PASS/FAIL/
    INSUFFICIENT_DATA per stock, with the per-rule values that produced it."""
    from app.screening.engine import evaluate_rule_set
    db = get_db()
    try:
        return evaluate_rule_set(db, rule_set_name, limit=limit)
    finally:
        db.close()


def _run_bulk_metrics_batch(max_companies_per_run: int):
    from app.screening.bulk_metrics import refresh_bulk_metrics
    db = get_db()
    try:
        result = refresh_bulk_metrics(db, max_companies_per_run=max_companies_per_run)
        logger.info("bulk-metrics batch finished via API trigger", **result)
    finally:
        db.close()


@router.post("/bulk-metrics/refresh-batch")
def trigger_bulk_metrics_batch(background_tasks: BackgroundTasks, max_companies: int = 50):
    """Kick off the fa_bulk_metrics refresh batch in the background — bounded
    to `max_companies` per call and resumable (already-fresh stocks skipped
    via a 24h staleness check). Meant to be called repeatedly (a daily cron,
    or manually) until the whole active universe (~884 stocks) is covered;
    the declarative screening engine can only evaluate stocks that have a
    row here (or fall back to the provenance ledger for banking-specific
    metrics)."""
    background_tasks.add_task(_run_bulk_metrics_batch, max_companies)
    return {"status": "started", "max_companies": max_companies}
