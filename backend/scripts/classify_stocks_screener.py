"""One-off script: for every (symbol, name, market_cap) resolved from
Screener.in's Market-cap-1000+ screen, fetch that company's own page and
extract the 4-level classification breadcrumb shown under "Peer comparison"
(Macro-economic Sector / Sector / Industry / Basic Industry — Screener's own
taxonomy, matches NSE's official Industry Classification Structure), then
upsert into `stocks` directly.

Writes to `stocks`, not a separate table, since 2026-09-17: this script
originally wrote to `fa_stock_classification`, a dedicated table that was
retired once `stocks` was expanded to cover the same ~1610-company universe
(migration 0028) — keeping two copies in sync required a manual script
(the since-deleted classify_missing_stocks.py) every time one drifted from
the other. `stocks` is the single source of truth now; re-running this
script (e.g. to pick up a new listing or a reclassification) upserts
straight into it, matching every other stock's own row shape — new symbols
get inserted with exchange='NSE' (matching this app's only-NSE convention
today), existing ones only have their classification/market-cap columns
touched, never their `id`/`exchange`/`is_active`/`isin`/etc.

Not part of the FastAPI app's request path — this is a standalone backfill,
run manually. Uses the persistent authenticated WebKit profile at
cache/screener_profile (no login needed for this data, but reuses the same
browser session already set up this session).
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlalchemy as sa
from playwright.sync_api import sync_playwright

from app.infrastructure.database.client import get_db

PROFILE_DIR = str(Path(__file__).resolve().parent.parent / "cache" / "screener_profile")
SYMBOL_NAME_MAP = Path(__file__).resolve().parent.parent / "cache" / "screener_symbol_name_map.json"
MCAP_DATA = Path(__file__).resolve().parent.parent / "cache" / "screener_mcap_gt_1000.json"
PROGRESS_FILE = Path(__file__).resolve().parent.parent / "cache" / "classification_progress.json"


# Real bug found live 2026-09-16: for a page with no real "Peer comparison"
# breadcrumb (e.g. ICICIB22, an ETF — not a company, so Screener's page
# never renders the taxonomy widget at all), the naive "find the label,
# grab the next 400 chars" approach picked up nearby unrelated UI chrome
# text ("EDIT COLUMNS", "Loading peers table ...", "Detailed Comparison
# with:") and silently stored it as if it were a real classification —
# garbage in `fa_stock_classification`, not a crash, so it went unnoticed
# until a manual spot-check. Reject any segment containing UI-chrome
# markers rather than trust every 4-part split.
_UI_CHROME_MARKERS = ("EDIT COLUMNS", "Loading", "Detailed Comparison", "...", ":")


def parse_breadcrumb(text: str) -> tuple[str, str, str, str] | None:
    idx = text.find("Peer comparison")
    if idx < 0:
        return None
    segment = text[idx + len("Peer comparison"):idx + len("Peer comparison") + 400]
    part_idx = segment.find("Part of")
    if part_idx > 0:
        segment = segment[:part_idx]
    # Segments are separated by multiple spaces/newlines in the rendered text.
    import re
    parts = [p.strip() for p in re.split(r"\s{2,}|\n+", segment) if p.strip()]
    if len(parts) < 4:
        return None
    result = tuple(parts[:4])
    if any(marker in part for part in result for marker in _UI_CHROME_MARKERS):
        return None
    return result


def run(limit: int | None = None, resume: bool = True):
    with open(SYMBOL_NAME_MAP) as f:
        symbol_to_name = json.load(f)
    with open(MCAP_DATA) as f:
        mcap_rows = json.load(f)

    name_to_mcap = {}
    for row in mcap_rows:
        try:
            name_to_mcap[row["company"]] = float(row["market_cap_cr"].replace(",", ""))
        except (ValueError, KeyError):
            continue

    done = set()
    if resume and PROGRESS_FILE.exists():
        done = set(json.loads(PROGRESS_FILE.read_text()))

    symbols = [s for s in symbol_to_name if s not in done]
    if limit:
        symbols = symbols[:limit]

    db = get_db()
    processed, failed = 0, 0
    with sync_playwright() as p:
        context = p.webkit.launch_persistent_context(PROFILE_DIR, headless=True)
        page = context.new_page()

        for i, symbol in enumerate(symbols):
            name = symbol_to_name[symbol]
            try:
                page.goto(f"https://www.screener.in/company/{symbol}/", timeout=20000)
                page.wait_for_timeout(600)
                text = page.locator("body").inner_text(timeout=5000)
                breadcrumb = parse_breadcrumb(text)
                if not breadcrumb:
                    failed += 1
                    print(f"[{i+1}/{len(symbols)}] {symbol}: no breadcrumb found", flush=True)
                    continue
                macro, sector, industry, basic = breadcrumb

                # 5-tier thresholds (2026-09-17) — matches the live UPDATE run
                # against `stocks` the same day; keep both in sync if these
                # ever change.
                market_cap_cr = name_to_mcap.get(name)
                market_cap = market_cap_cr * 1e7 if market_cap_cr is not None else None
                if market_cap is None:
                    category = None
                elif market_cap >= 112770 * 1e7:  # ~AMFI rank-100 cutoff (Sep 2026)
                    category = "LARGE_CAP"
                elif market_cap >= 37564 * 1e7:  # ~AMFI rank-250 cutoff
                    category = "MID_CAP"
                else:
                    category = "SMALL_CAP"  # rank 251+ (all remaining)

                db.execute(
                    sa.text(
                        """
                        INSERT INTO stocks
                            (id, symbol, exchange, company_name, market_cap, market_cap_category,
                             macro_sector, sector, industry, basic_industry, is_active, created_at, updated_at)
                        VALUES ('NSE:'||:symbol, :symbol, 'NSE', :company_name, :market_cap, :category,
                                :macro_sector, :sector, :industry, :basic_industry, true, :now, :now)
                        ON CONFLICT (id) DO UPDATE SET
                            company_name = EXCLUDED.company_name,
                            market_cap = EXCLUDED.market_cap,
                            market_cap_category = EXCLUDED.market_cap_category,
                            macro_sector = EXCLUDED.macro_sector,
                            sector = EXCLUDED.sector,
                            industry = EXCLUDED.industry,
                            basic_industry = EXCLUDED.basic_industry,
                            updated_at = EXCLUDED.updated_at
                        """
                    ),
                    {
                        "symbol": symbol,
                        "company_name": name,
                        "market_cap": market_cap,
                        "category": category,
                        "macro_sector": macro,
                        "sector": sector,
                        "industry": industry,
                        "basic_industry": basic,
                        "now": datetime.now(timezone.utc),
                    },
                )
                db.commit()
                processed += 1
                done.add(symbol)
                if (i + 1) % 25 == 0:
                    PROGRESS_FILE.write_text(json.dumps(sorted(done)))
                    print(f"[{i+1}/{len(symbols)}] progress saved ({processed} ok, {failed} failed)", flush=True)
            except Exception as e:
                failed += 1
                print(f"[{i+1}/{len(symbols)}] {symbol}: ERROR {e}", flush=True)
                db.rollback()
            time.sleep(2.5)  # slowed down after repeated rate-limit-looking blocks at 0.4s pace

        context.close()

    PROGRESS_FILE.write_text(json.dumps(sorted(done)))
    db.close()
    print(f"DONE. processed={processed} failed={failed} total_done={len(done)}")


MISSING_PROGRESS_FILE = Path(__file__).resolve().parent.parent / "cache" / "classification_progress_missing.json"


def run_for_missing(limit: int | None = None, resume: bool = True):
    """Same breadcrumb scrape as `run()`, but sources symbols straight from
    `stocks` (whichever active rows have no `basic_industry` yet) instead
    of the static `screener_symbol_name_map.json` snapshot — that map was
    built from the original market-cap>1000cr screen, so it has ZERO
    overlap with the ~1,000 smaller-cap/newly-added stocks this backfill
    targets (confirmed live, 2026-09-28: 1,016 stocks missing
    basic_industry, 0 of them in the map). Feasibility spot-checked first
    on 15 of the smallest/most obscure candidates — 15/15 had a real
    breadcrumb, so Screener's classification coverage isn't the limiting
    factor here.

    Only touches macro_sector/sector/industry/basic_industry — market_cap/
    market_cap_category are left as whatever Yahoo-based classification
    already set (see nse_equity_list_client.py/nse_ipo_client.py), no
    `screener_mcap_gt_1000.json` lookup needed for this batch. Own progress
    file (`MISSING_PROGRESS_FILE`), separate from `run()`'s, so the two
    backfills never step on each other's resume state."""
    from app.infrastructure.database.models import Stock

    db = get_db()
    rows = (
        db.query(Stock.symbol, Stock.company_name)
        .filter(Stock.is_active.is_(True), Stock.basic_industry.is_(None))
        .all()
    )
    symbol_to_name = {sym: name for sym, name in rows}

    done = set()
    if resume and MISSING_PROGRESS_FILE.exists():
        done = set(json.loads(MISSING_PROGRESS_FILE.read_text()))

    symbols = [s for s in symbol_to_name if s not in done]
    if limit:
        symbols = symbols[:limit]
    print(f"{len(symbols)} symbols to classify ({len(done)} already done)", flush=True)

    processed, failed = 0, 0
    with sync_playwright() as p:
        context = p.webkit.launch_persistent_context(PROFILE_DIR, headless=True)
        page = context.new_page()

        for i, symbol in enumerate(symbols):
            name = symbol_to_name[symbol]
            try:
                page.goto(f"https://www.screener.in/company/{symbol}/", timeout=20000)
                page.wait_for_timeout(600)
                text = page.locator("body").inner_text(timeout=5000)
                breadcrumb = parse_breadcrumb(text)
                if not breadcrumb:
                    failed += 1
                    print(f"[{i+1}/{len(symbols)}] {symbol}: no breadcrumb found", flush=True)
                    done.add(symbol)
                    continue
                macro, sector, industry, basic = breadcrumb

                db.execute(
                    sa.text(
                        """
                        UPDATE stocks SET
                            macro_sector = :macro_sector,
                            sector = :sector,
                            industry = :industry,
                            basic_industry = :basic_industry,
                            updated_at = :now
                        WHERE id = 'NSE:'||:symbol
                        """
                    ),
                    {
                        "symbol": symbol,
                        "macro_sector": macro,
                        "sector": sector,
                        "industry": industry,
                        "basic_industry": basic,
                        "now": datetime.now(timezone.utc),
                    },
                )
                db.commit()
                processed += 1
                done.add(symbol)
                if (i + 1) % 25 == 0:
                    MISSING_PROGRESS_FILE.write_text(json.dumps(sorted(done)))
                    print(f"[{i+1}/{len(symbols)}] progress saved ({processed} ok, {failed} failed)", flush=True)
            except Exception as e:
                failed += 1
                done.add(symbol)  # a page-level failure (404, timeout) won't resolve on retry either
                print(f"[{i+1}/{len(symbols)}] {symbol}: ERROR {e}", flush=True)
                db.rollback()
            time.sleep(2.5)  # same pacing run() settled on after rate-limit-looking blocks at 0.4s

        context.close()

    MISSING_PROGRESS_FILE.write_text(json.dumps(sorted(done)))
    db.close()
    print(f"DONE. processed={processed} failed={failed} total_done={len(done)}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--missing"]
    lim = int(args[0]) if args else None
    if "--missing" in sys.argv:
        run_for_missing(limit=lim)
    else:
        run(limit=lim)
