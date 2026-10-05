"""
Stock Index Classification Service.

Queries PostgreSQL to answer:
  - Which Nifty indices does stock X currently belong to?
  - Which stocks are in Nifty index Y?
  - Historical membership at a given date
  - List all known indices (with optional category filter)

Never scrapes the website.  The LLM must never hallucinate membership — it should
call this service and return its result verbatim.
"""

from datetime import date
from sqlalchemy import text

from app.infrastructure.database.client import get_db


class StockIndexClassificationService:

    def stock_indices(
        self,
        symbol: str,
        as_of: date | None = None,
        category: str | None = None,
    ) -> dict:
        """
        Return all Nifty indices the stock belongs to.

        as_of=None  → current membership (effective_to IS NULL)
        as_of=<date> → membership active on that date
        category     → filter to a specific IndexCategory id (e.g. "SECTORAL")
        """
        db = get_db()
        try:
            as_of_date = as_of or date.today()

            # Resolve stock
            stock_row = db.execute(
                text("SELECT id, symbol, company_name FROM stocks WHERE symbol = :sym AND exchange = 'NSE' LIMIT 1"),
                {"sym": symbol.strip().upper()},
            ).fetchone()
            if not stock_row:
                return {"error": f"Stock '{symbol}' not found in database"}

            stock_id, stock_symbol, company_name = stock_row

            # Query memberships
            q = """
                SELECT
                    ni.id            AS index_id,
                    ni.index_name,
                    ic2.id           AS cat_id,
                    ic2.name         AS cat_name,
                    ic.weight,
                    ic.effective_from,
                    ic.effective_to
                FROM index_constituents ic
                JOIN nifty_indices ni ON ni.id = ic.index_id
                JOIN index_categories ic2 ON ic2.id = ni.category_id
                WHERE ic.stock_id = :stock_id
                  AND ic.effective_from <= :as_of
                  AND (ic.effective_to IS NULL OR ic.effective_to >= :as_of)
            """
            params: dict = {"stock_id": stock_id, "as_of": as_of_date}
            if category:
                q += " AND ic2.id = :cat"
                params["cat"] = category.upper()
            q += " ORDER BY ic2.name, ni.index_name"

            rows = db.execute(text(q), params).fetchall()

            # Group by category
            by_cat: dict[str, list[dict]] = {}
            for r in rows:
                cat_key = r[2].lower().replace("_", "-")  # "broad-market", "sectoral"
                if cat_key not in by_cat:
                    by_cat[cat_key] = []
                entry: dict = {"name": r[1], "index_id": r[0]}
                if r[4] is not None:
                    entry["weight"] = float(r[4])
                entry["effective_from"] = r[5].isoformat() if r[5] else None
                if r[6]:
                    entry["effective_to"] = r[6].isoformat()
                by_cat[cat_key].append(entry)

            # Get data freshness
            freshness_row = db.execute(text("""
                SELECT MAX(completed_at) FROM ingestion_runs
                WHERE status IN ('SUCCESS','PARTIAL_SUCCESS') AND dry_run = false
            """)).fetchone()
            data_as_of = freshness_row[0].date().isoformat() if freshness_row and freshness_row[0] else None

            return {
                "symbol": stock_symbol,
                "company_name": company_name,
                "data_as_of": data_as_of,
                "queried_date": as_of_date.isoformat(),
                "source": "NSE Indices",
                "indices": by_cat,
            }
        finally:
            db.close()

    def index_constituents(
        self,
        index_code: str,
        as_of: date | None = None,
    ) -> dict:
        """
        Return all stocks currently (or historically) in a given index.

        index_code: slug like "nifty-bank" or "nifty-50"
        """
        db = get_db()
        try:
            as_of_date = as_of or date.today()

            idx_row = db.execute(
                text("""
                    SELECT ni.id, ni.index_name, ic.name AS cat_name
                    FROM nifty_indices ni
                    JOIN index_categories ic ON ic.id = ni.category_id
                    WHERE ni.index_code = :code
                """),
                {"code": index_code.lower()},
            ).fetchone()
            if not idx_row:
                return {"error": f"Index '{index_code}' not found in database"}

            idx_id, idx_name, cat_name = idx_row

            rows = db.execute(text("""
                SELECT s.symbol, s.company_name, s.market_cap_category,
                       ic.weight, ic.effective_from, ic.effective_to
                FROM index_constituents ic
                JOIN stocks s ON s.id = ic.stock_id
                WHERE ic.index_id = :idx_id
                  AND ic.effective_from <= :as_of
                  AND (ic.effective_to IS NULL OR ic.effective_to >= :as_of)
                ORDER BY s.symbol
            """), {"idx_id": idx_id, "as_of": as_of_date}).fetchall()

            constituents = []
            for r in rows:
                entry: dict = {
                    "symbol": r[0],
                    "company_name": r[1],
                    "market_cap_category": r[2],
                }
                if r[3] is not None:
                    entry["weight"] = float(r[3])
                entry["effective_from"] = r[4].isoformat() if r[4] else None
                if r[5]:
                    entry["effective_to"] = r[5].isoformat()
                constituents.append(entry)

            freshness_row = db.execute(text("""
                SELECT MAX(completed_at) FROM ingestion_runs
                WHERE status IN ('SUCCESS','PARTIAL_SUCCESS') AND dry_run = false
            """)).fetchone()
            data_as_of = freshness_row[0].date().isoformat() if freshness_row and freshness_row[0] else None

            return {
                "index": idx_name,
                "index_code": index_code,
                "category": cat_name,
                "data_as_of": data_as_of,
                "queried_date": as_of_date.isoformat(),
                "total": len(constituents),
                "constituents": constituents,
            }
        finally:
            db.close()

    def list_indices(self, category: str | None = None) -> list[dict]:
        """Return all known indices, optionally filtered by category."""
        db = get_db()
        try:
            q = """
                SELECT ni.id, ni.index_name, ic.id AS cat_id, ic.name AS cat_name,
                       ni.is_active, ni.source_url
                FROM nifty_indices ni
                JOIN index_categories ic ON ic.id = ni.category_id
            """
            params: dict = {}
            if category:
                q += " WHERE ic.id = :cat"
                params["cat"] = category.upper()
            q += " ORDER BY ic.name, ni.index_name"
            rows = db.execute(text(q), params).fetchall()
            return [
                {
                    "index_id": r[0],
                    "name": r[1],
                    "category_id": r[2],
                    "category": r[3],
                    "is_active": r[4],
                    "source_url": r[5],
                }
                for r in rows
            ]
        finally:
            db.close()

    def index_intersection(self, index_a: str, index_b: str) -> dict:
        """Return stocks present in both index_a and index_b (current membership)."""
        db = get_db()
        try:
            today = date.today()

            def _get_stock_ids(code: str) -> tuple[str, str, set[str]]:
                idx_row = db.execute(
                    text("SELECT id, index_name FROM nifty_indices WHERE index_code = :c"),
                    {"c": code.lower()},
                ).fetchone()
                if not idx_row:
                    return code, code, set()
                idx_id, idx_name = idx_row
                rows = db.execute(text("""
                    SELECT stock_id FROM index_constituents
                    WHERE index_id = :idx AND effective_from <= :d AND (effective_to IS NULL OR effective_to >= :d)
                """), {"idx": idx_id, "d": today}).fetchall()
                return idx_id, idx_name, {r[0] for r in rows}

            _, name_a, ids_a = _get_stock_ids(index_a)
            _, name_b, ids_b = _get_stock_ids(index_b)
            common_ids = ids_a & ids_b

            symbols: list[dict] = []
            if common_ids:
                rows = db.execute(
                    text("SELECT symbol, company_name FROM stocks WHERE id = ANY(:ids) ORDER BY symbol"),
                    {"ids": list(common_ids)},
                ).fetchall()
                symbols = [{"symbol": r[0], "company_name": r[1]} for r in rows]

            return {
                "index_a": name_a,
                "index_b": name_b,
                "common_count": len(symbols),
                "common_stocks": symbols,
            }
        finally:
            db.close()


stock_index_classification_service = StockIndexClassificationService()
