"""
Nifty Index Data Ingestion Service.

Downloads constituent CSVs from niftyindices.com, validates them, computes diffs
against the current active index_constituents, and updates the DB transactionally
with full historical membership tracking (effective_from / effective_to dates).

PostgreSQL is the source of truth.  The LLM/API layer must never invent membership.

Workflow:
  1. Seed index_categories + nifty_indices catalog (idempotent, skipped when already present)
  2. Create an ingestion_run record
  3. For each active index:
     a. Download CSV → record in source_files
     b. Parse + normalize rows → insert into staging_index_constituents
     c. Validate (sanity checks — e.g. sudden 0-stock result)
  4. Diff: compute NEW / REMOVED / UNCHANGED for each index
  5. If dry_run=True: return diff, do not commit
  6. Otherwise: in one transaction —
     - Close removed memberships (effective_to = today)
     - Insert new memberships (effective_from = today)
     - Mark ingestion_run SUCCESS
     - Commit
  7. Return change_report
"""

import csv
import hashlib
import io
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, timezone

import httpx
from sqlalchemy import text

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import (
    IndexCategory, NiftyIndex, IngestionRun, SourceFile,
    StagingIndexConstituent, IndexConstituent, Stock,
)
from app.logger import logger


# ---------------------------------------------------------------------------
# Index catalog bootstrap — seeded once, then managed via DB
# ---------------------------------------------------------------------------

_INDEX_CATEGORIES = [
    ("BROAD_MARKET",  "Broad Market",  "Broad market indices covering large, mid, small segments"),
    ("SECTORAL",      "Sectoral",      "Sector-specific indices (Bank, IT, Pharma, etc.)"),
    ("THEMATIC",      "Thematic",      "Theme-based indices (Defence, Digital, Manufacturing)"),
    ("STRATEGY",      "Strategy",      "Factor/strategy indices (Quality, Alpha, Low Volatility)"),
    ("FIXED_INCOME",  "Fixed Income",  "Debt and bond indices"),
    ("HYBRID",        "Hybrid",        "Hybrid asset class indices"),
]

_BASE = "https://www.niftyindices.com/IndexConstituent"

_INITIAL_INDICES = [
    # (id/slug, name, category_id, csv_filename)
    ("nifty-50",               "Nifty 50",                    "BROAD_MARKET", "ind_nifty50list.csv"),
    ("nifty-next-50",          "Nifty Next 50",               "BROAD_MARKET", "ind_niftynext50list.csv"),
    ("nifty-100",              "Nifty 100",                   "BROAD_MARKET", "ind_nifty100list.csv"),
    ("nifty-midcap-150",       "Nifty Midcap 150",            "BROAD_MARKET", "ind_niftymidcap150list.csv"),
    ("nifty-smallcap-250",     "Nifty Smallcap 250",          "BROAD_MARKET", "ind_niftysmallcap250list.csv"),
    ("nifty-500",              "Nifty 500",                   "BROAD_MARKET", "ind_nifty500list.csv"),
    ("nifty-total-market",     "Nifty Total Market",          "BROAD_MARKET", "ind_niftytotalmarket_list.csv"),
    ("nifty-bank",             "Nifty Bank",                  "SECTORAL",     "ind_niftybanklist.csv"),
    ("nifty-it",               "Nifty IT",                    "SECTORAL",     "ind_niftyitlist.csv"),
    ("nifty-financial-services","Nifty Financial Services",   "SECTORAL",     "ind_niftyfinancelist.csv"),
    ("nifty-fmcg",             "Nifty FMCG",                  "SECTORAL",     "ind_niftyfmcglist.csv"),
    ("nifty-pharma",           "Nifty Pharma",                "SECTORAL",     "ind_niftypharmalist.csv"),
    ("nifty-auto",             "Nifty Auto",                  "SECTORAL",     "ind_niftyautolist.csv"),
    ("nifty-metal",            "Nifty Metal",                 "SECTORAL",     "ind_niftymetallist.csv"),
    ("nifty-energy",           "Nifty Energy",                "SECTORAL",     "ind_niftyenergylist.csv"),
    ("nifty-media",            "Nifty Media",                 "SECTORAL",     "ind_niftymedialist.csv"),
    ("nifty-realty",           "Nifty Realty",                "SECTORAL",     "ind_niftyrealtylist.csv"),
    ("nifty-private-bank",     "Nifty Private Bank",          "SECTORAL",     "ind_nifty_privatebanklist.csv"),
    ("nifty-psu-bank",         "Nifty PSU Bank",              "SECTORAL",     "ind_niftypsubanklist.csv"),
    ("nifty-healthcare",       "Nifty Healthcare Index",      "SECTORAL",     "ind_niftyhealthcarelist.csv"),
    ("nifty-oil-gas",          "Nifty Oil & Gas",             "SECTORAL",     "ind_niftyoilgaslist.csv"),
    ("nifty-india-defence",    "Nifty India Defence",         "THEMATIC",     "ind_niftyindiadefence_list.csv"),
    ("nifty-india-digital",    "Nifty India Digital",         "THEMATIC",     "ind_niftyindiadigital_list.csv"),
    ("nifty-india-manufacturing", "Nifty India Manufacturing","THEMATIC",     "ind_niftyindiamanufacturing_list.csv"),
    ("nifty-100-esg",          "Nifty100 ESG",                "STRATEGY",     "ind_nifty100esg_list.csv"),
    ("nifty-alpha-50",         "Nifty Alpha 50",              "STRATEGY",     "ind_nifty_Alpha_Index.csv"),
    ("nifty-quality-30",       "Nifty100 Quality 30",         "STRATEGY",     "ind_nifty100Quality30list.csv"),
    ("nifty-high-beta-50",     "Nifty High Beta 50",          "STRATEGY",     "ind_niftyhighbeta50_list.csv"),
    ("nifty-low-vol-30",       "Nifty Low Volatility 30",     "STRATEGY",     "ind_Nifty100LowVolatility30list.csv"),
    # Sector benchmarks used by app/prices/benchmarks.py (added 2026-10-05).
    ("nifty-consumer-durables","Nifty Consumer Durables",     "SECTORAL",     "ind_niftyconsumerdurableslist.csv"),
    ("nifty-chemicals",        "Nifty Chemicals",             "SECTORAL",     "ind_niftychemicals_list.csv"),
    ("nifty-capital-markets",  "Nifty Capital Markets",       "SECTORAL",     "ind_niftycapitalmarkets_list.csv"),
    ("nifty-infrastructure",   "Nifty Infrastructure",        "THEMATIC",     "ind_niftyinfralist.csv"),
    ("nifty-india-consumption","Nifty India Consumption",     "THEMATIC",     "ind_niftyconsumptionlist.csv"),
    ("nifty-transportation-logistics", "Nifty Transportation & Logistics", "THEMATIC", "ind_niftytransportationandlogistics_list.csv"),
]

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.niftyindices.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Reject ingestion if new count is less than this fraction of old count
_SANITY_MIN_RATIO = 0.5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_symbol(raw: str) -> str:
    return raw.strip().upper()


def _normalize_isin(raw: str) -> str:
    return raw.strip().upper()


def _normalize_company(raw: str) -> str:
    return raw.strip()


def _parse_row(row: dict) -> tuple[str, str, str, str | None]:
    """Return (symbol, isin, company_name, weight_str | None)."""
    symbol = _normalize_symbol(
        row.get("Symbol") or row.get("SYMBOL") or row.get("Ticker") or ""
    )
    isin = _normalize_isin(
        row.get("ISIN Code") or row.get("ISIN") or row.get("isin") or ""
    )
    company = _normalize_company(
        row.get("Company Name") or row.get("company_name") or ""
    )
    weight_raw = row.get("Weight (%)") or row.get("Weight") or row.get("weight")
    return symbol, isin, company, weight_raw


def _parse_weight(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw.strip().rstrip("%"))
    except (ValueError, AttributeError):
        return None


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _log_unknown_columns(headers: list[str], known: set[str], index_id: str) -> None:
    unknown = [h for h in headers if h not in known]
    if unknown:
        logger.warning("Unknown CSV columns", index_id=index_id, columns=unknown)


_KNOWN_HEADERS = {
    "Company Name", "company_name", "Industry", "industry", "Sector",
    "Symbol", "SYMBOL", "Ticker", "Series", "series",
    "ISIN Code", "ISIN", "isin", "Weight (%)", "Weight", "weight",
}


# ---------------------------------------------------------------------------
# Ingestion result dataclass
# ---------------------------------------------------------------------------

@dataclass
class IndexDiff:
    index_id: str
    index_name: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    unchanged: int = 0
    records_read: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class NiftyIndexIngestionService:

    def seed_catalog(self) -> dict:
        """Idempotently insert index_categories and nifty_indices rows if missing."""
        db = get_db()
        now = datetime.now(timezone.utc)
        cats_added = 0
        indices_added = 0
        try:
            for cat_id, cat_name, cat_desc in _INDEX_CATEGORIES:
                if not db.get(IndexCategory, cat_id):
                    db.add(IndexCategory(id=cat_id, name=cat_name, description=cat_desc,
                                         created_at=now, updated_at=now))
                    cats_added += 1
            db.flush()

            for idx_id, idx_name, cat_id, csv_file in _INITIAL_INDICES:
                existing = db.get(NiftyIndex, idx_id)
                # NSE renames these files now and then; a corrected name in the
                # list above must reach a catalog row seeded with the old one.
                if existing and existing.source_url != f"{_BASE}/{csv_file}":
                    existing.source_url = f"{_BASE}/{csv_file}"
                    existing.updated_at = now
                if not existing:
                    db.add(NiftyIndex(
                        id=idx_id,
                        index_name=idx_name,
                        index_code=idx_id,
                        category_id=cat_id,
                        source_url=f"{_BASE}/{csv_file}",
                        is_active=True,
                        first_seen_at=now,
                        created_at=now,
                        updated_at=now,
                    ))
                    indices_added += 1
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return {"categories_added": cats_added, "indices_added": indices_added}

    def ingest(self, dry_run: bool = False, index_ids: list[str] | None = None) -> dict:
        """
        Run full ingestion.

        dry_run=True  → download + validate + compute diff but do NOT commit to DB.
        index_ids     → restrict to specific indices (default: all active).
        """
        db = get_db()
        now = datetime.now(timezone.utc)
        today = now.date()
        run_id = str(uuid.uuid4())

        # ---- Create ingestion_run record ----
        run = IngestionRun(
            id=run_id,
            started_at=now,
            status="RUNNING",
            dry_run=dry_run,
            files_discovered=0,
            files_downloaded=0,
            files_processed=0,
            records_read=0,
            records_inserted=0,
            records_updated=0,
            records_removed=0,
            records_unchanged=0,
            created_at=now,
        )
        db.add(run)
        db.commit()

        log = logger.bind(ingestion_run_id=run_id, dry_run=dry_run)
        log.info("Ingestion run started")

        # ---- Load active indices ----
        q = "SELECT id, index_name, source_url FROM nifty_indices WHERE is_active = true"
        params: dict = {}
        if index_ids:
            q += " AND id = ANY(:ids)"
            params["ids"] = index_ids
        active_indices = db.execute(text(q), params).fetchall()

        run.files_discovered = len(active_indices)
        db.commit()

        diffs: list[IndexDiff] = []
        total_downloaded = 0
        total_processed = 0
        total_read = 0

        for idx_row in active_indices:
            idx_id, idx_name, source_url = idx_row
            diff = IndexDiff(index_id=idx_id, index_name=idx_name)

            if not source_url:
                diff.error = "No source_url configured"
                diff.warnings.append("Skipped — no source_url")
                diffs.append(diff)
                continue

            # ---- Download CSV ----
            file_id = str(uuid.uuid4())
            filename = source_url.split("/")[-1]
            sf = SourceFile(
                id=file_id,
                filename=filename,
                source_url=source_url,
                index_id=idx_id,
                ingestion_run_id=run_id,
                processing_status="PENDING",
                created_at=now,
            )
            db.add(sf)
            db.flush()

            raw_content: bytes | None = None
            try:
                with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                    resp = client.get(source_url, headers=_HTTP_HEADERS)
                resp.raise_for_status()
                raw_content = resp.content
                file_hash = _sha256(raw_content)
                sf.file_hash = file_hash
                sf.file_size = len(raw_content)
                sf.downloaded_at = datetime.now(timezone.utc)
                db.flush()
                total_downloaded += 1
                log.info("Downloaded CSV", index_id=idx_id, bytes=len(raw_content))
            except Exception as e:
                sf.processing_status = "ERROR"
                sf.error_message = str(e)
                db.commit()
                diff.error = f"Download failed: {e}"
                log.error("CSV download failed", index_id=idx_id, error=str(e))
                diffs.append(diff)
                continue

            # ---- Parse CSV ----
            try:
                text_content = raw_content.decode("utf-8-sig").strip()
                rows = list(csv.DictReader(io.StringIO(text_content)))
                if not rows:
                    raise ValueError("CSV is empty")
                headers = list(rows[0].keys())
                _log_unknown_columns(headers, _KNOWN_HEADERS, idx_id)
            except Exception as e:
                sf.processing_status = "ERROR"
                sf.error_message = f"Parse error: {e}"
                db.commit()
                diff.error = f"Parse failed: {e}"
                diffs.append(diff)
                continue

            # ---- Load staging ----
            staging_rows: list[StagingIndexConstituent] = []
            for row in rows:
                symbol, isin, company, weight_raw = _parse_row(row)
                if not symbol:
                    continue
                weight = _parse_weight(weight_raw)

                # Try to resolve to existing stock
                resolved_id: str | None = None
                if isin:
                    sid_row = db.execute(
                        text("SELECT id FROM stocks WHERE isin = :isin AND exchange = 'NSE' LIMIT 1"),
                        {"isin": isin},
                    ).fetchone()
                    if sid_row:
                        resolved_id = sid_row[0]
                if resolved_id is None:
                    sid_row = db.execute(
                        text("SELECT id FROM stocks WHERE symbol = :sym AND exchange = 'NSE' LIMIT 1"),
                        {"sym": symbol},
                    ).fetchone()
                    if sid_row:
                        resolved_id = sid_row[0]

                is_valid = bool(symbol and isin)
                validation_error: str | None = None
                if not symbol:
                    is_valid = False
                    validation_error = "Missing symbol"
                elif not isin:
                    is_valid = False
                    validation_error = "Missing ISIN"

                sr = StagingIndexConstituent(
                    ingestion_run_id=run_id,
                    index_id=idx_id,
                    raw_symbol=symbol,
                    raw_company_name=company or None,
                    raw_isin=isin or None,
                    resolved_stock_id=resolved_id,
                    weight=weight,
                    is_valid=is_valid,
                    validation_error=validation_error,
                    created_at=now,
                )
                staging_rows.append(sr)
                db.add(sr)

            db.flush()
            diff.records_read = len(staging_rows)
            total_read += len(staging_rows)

            # ---- Sanity check ----
            cur_count_row = db.execute(
                text("""
                    SELECT COUNT(*) FROM index_constituents
                    WHERE index_id = :idx AND effective_to IS NULL
                """),
                {"idx": idx_id},
            ).fetchone()
            cur_count = cur_count_row[0] if cur_count_row else 0
            valid_staging = sum(1 for r in staging_rows if r.is_valid and r.resolved_stock_id)

            if cur_count > 0 and valid_staging < cur_count * _SANITY_MIN_RATIO:
                msg = (
                    f"Sanity check failed: had {cur_count} active members, "
                    f"new valid={valid_staging} < {_SANITY_MIN_RATIO * 100:.0f}% threshold"
                )
                sf.processing_status = "ERROR"
                sf.error_message = msg
                db.commit()
                diff.error = msg
                diff.warnings.append(msg)
                log.warning("Sanity check failed", index_id=idx_id, cur=cur_count, new=valid_staging)
                diffs.append(diff)
                continue

            # ---- Compute diff ----
            cur_members_rows = db.execute(
                text("""
                    SELECT ic.stock_id, s.symbol
                    FROM index_constituents ic
                    JOIN stocks s ON s.id = ic.stock_id
                    WHERE ic.index_id = :idx AND ic.effective_to IS NULL
                """),
                {"idx": idx_id},
            ).fetchall()
            cur_members: dict[str, str] = {r[0]: r[1] for r in cur_members_rows}  # stock_id → symbol
            cur_stock_ids = set(cur_members.keys())

            new_stock_ids: set[str] = {
                r.resolved_stock_id for r in staging_rows
                if r.is_valid and r.resolved_stock_id
            }

            added_ids = new_stock_ids - cur_stock_ids
            removed_ids = cur_stock_ids - new_stock_ids
            unchanged_ids = new_stock_ids & cur_stock_ids

            # Resolve symbols for report
            def _symbols_for_ids(ids: set[str]) -> list[str]:
                if not ids:
                    return []
                rows_sym = db.execute(
                    text("SELECT id, symbol FROM stocks WHERE id = ANY(:ids)"),
                    {"ids": list(ids)},
                ).fetchall()
                return sorted(r[1] for r in rows_sym)

            diff.added = _symbols_for_ids(added_ids)
            diff.removed = _symbols_for_ids(removed_ids)
            diff.unchanged = len(unchanged_ids)

            sf.effective_date = today
            sf.processing_status = "OK"
            sf.processed_at = datetime.now(timezone.utc)
            db.flush()
            total_processed += 1

            log.info(
                "Diff computed",
                index_id=idx_id,
                added=len(added_ids),
                removed=len(removed_ids),
                unchanged=len(unchanged_ids),
            )

            if not dry_run:
                # Close removed memberships
                if removed_ids:
                    db.execute(
                        text("""
                            UPDATE index_constituents
                            SET effective_to = :today
                            WHERE index_id = :idx
                              AND stock_id = ANY(:ids)
                              AND effective_to IS NULL
                        """),
                        {"today": today, "idx": idx_id, "ids": list(removed_ids)},
                    )

                # Insert new memberships
                staging_by_stock: dict[str, StagingIndexConstituent] = {
                    r.resolved_stock_id: r for r in staging_rows
                    if r.is_valid and r.resolved_stock_id and r.resolved_stock_id in added_ids
                }
                for stock_id, sr in staging_by_stock.items():
                    db.add(IndexConstituent(
                        index_id=idx_id,
                        stock_id=stock_id,
                        weight=sr.weight,
                        effective_from=today,
                        effective_to=None,
                        ingestion_run_id=run_id,
                        created_at=now,
                    ))

            diffs.append(diff)

        # ---- Build change report ----
        change_report = {
            "run_id": run_id,
            "dry_run": dry_run,
            "date": today.isoformat(),
            "indices": [
                {
                    "index_id": d.index_id,
                    "index_name": d.index_name,
                    "records_read": d.records_read,
                    "added": d.added,
                    "removed": d.removed,
                    "unchanged": d.unchanged,
                    "error": d.error,
                    "warnings": d.warnings,
                }
                for d in diffs
            ],
            "totals": {
                "files_discovered": len(active_indices),
                "files_downloaded": total_downloaded,
                "files_processed": total_processed,
                "records_read": total_read,
                "records_inserted": sum(len(d.added) for d in diffs),
                "records_removed": sum(len(d.removed) for d in diffs),
                "records_unchanged": sum(d.unchanged for d in diffs),
            },
        }

        # ---- Finalize run ----
        error_count = sum(1 for d in diffs if d.error)
        if error_count == 0:
            final_status = "SUCCESS"
        elif error_count < len(diffs):
            final_status = "PARTIAL_SUCCESS"
        else:
            final_status = "FAILED"

        run.completed_at = datetime.now(timezone.utc)
        run.status = final_status if not dry_run else "SUCCESS"
        run.files_discovered = len(active_indices)
        run.files_downloaded = total_downloaded
        run.files_processed = total_processed
        run.records_read = total_read
        run.records_inserted = sum(len(d.added) for d in diffs)
        run.records_removed = sum(len(d.removed) for d in diffs)
        run.records_unchanged = sum(d.unchanged for d in diffs)
        run.change_report = change_report

        if dry_run:
            db.rollback()
            log.info("Dry run complete — rolled back all changes")
        else:
            db.commit()
            log.info("Ingestion committed", status=final_status)

        db.close()
        return change_report

    def last_run_status(self) -> dict | None:
        """Return status of the most recent ingestion_run (excluding dry runs)."""
        db = get_db()
        try:
            row = db.execute(text("""
                SELECT id, started_at, completed_at, status, dry_run,
                       files_discovered, files_processed,
                       records_inserted, records_removed, records_unchanged
                FROM ingestion_runs
                WHERE dry_run = false
                ORDER BY started_at DESC
                LIMIT 1
            """)).fetchone()
            if not row:
                return None
            return {
                "run_id": row[0],
                "started_at": row[1].isoformat() if row[1] else None,
                "completed_at": row[2].isoformat() if row[2] else None,
                "status": row[3],
                "dry_run": row[4],
                "files_discovered": row[5],
                "files_processed": row[6],
                "records_inserted": row[7],
                "records_removed": row[8],
                "records_unchanged": row[9],
            }
        finally:
            db.close()


nifty_index_ingestion_service = NiftyIndexIngestionService()
