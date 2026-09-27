"""Run the quick (Yahoo-only) scorer over stocks, storing each result to
`fa_quick_scores` the moment it finishes (one by one — a crash or Ctrl-C loses
nothing already scored).

    cd backend && .venv/bin/python -m app.quick_analysis.runner --limit 2000   # whole universe, biggest companies first
    cd backend && .venv/bin/python -m app.quick_analysis.runner --symbols TANLA,KROSS --force
    cd backend && .venv/bin/python -m app.quick_analysis.runner --limit 40 --no-store --csv out.csv

Resumable: stocks scored within `--fresh-days` (default 7) are skipped, and
Yahoo responses are Redis-cached for 24h. Fundamentals only change when a
quarter is reported, so weekly refreshes are plenty.
"""
from __future__ import annotations

import argparse
import csv
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.data.yfinance_client import fetch_financial_data
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock
from app.quick_analysis.scorer import QuickScore, SCORE_KEYS, quick_score
from app.quick_analysis.store import recently_scored_ids, upsert_quick_score


_RATE_LIMIT_MARKERS = ("too many requests", "rate limited", "429")
_MAX_ATTEMPTS = 6


class _Pacer:
    """Shared politeness gate. Yahoo throttles by IP: an unpaced 8-worker run
    was cut off after ~320 stocks (each stock costs ~7 Yahoo calls). This
    spaces stock fetches to `stocks_per_sec` and, on any rate-limit response,
    pauses EVERY worker (exponential backoff 60s -> 15min) before retrying,
    so one throttled request never turns into a storm of throttled retries."""

    def __init__(self, stocks_per_sec: float):
        self._interval = 1.0 / stocks_per_sec
        self._lock = threading.Lock()
        self._next_slot = 0.0
        self._pause_until = 0.0
        self._backoff = 60.0

    def wait_turn(self) -> None:
        with self._lock:
            now = time.monotonic()
            slot = max(self._next_slot, self._pause_until, now)
            self._next_slot = slot + self._interval
        delay = slot - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def report_throttled(self) -> None:
        with self._lock:
            self._pause_until = max(self._pause_until, time.monotonic() + self._backoff)
            print(f"  ! Yahoo rate-limited — all workers pausing {self._backoff:.0f}s")
            self._backoff = min(self._backoff * 2, 900.0)

    def report_ok(self) -> None:
        with self._lock:
            self._backoff = 60.0


def _is_throttled(data: dict) -> bool:
    err = (data.get("error") or "").lower()
    return bool(err) and any(m in err for m in _RATE_LIMIT_MARKERS)


def _one(stock: Stock, pacer: _Pacer) -> tuple[Stock, QuickScore, float]:
    started = time.monotonic()
    data: dict = {}
    for _ in range(_MAX_ATTEMPTS):
        pacer.wait_turn()
        data = fetch_financial_data(stock.exchange, stock.symbol)  # Redis-cached: a resumed run skips finished stocks
        if not _is_throttled(data):
            pacer.report_ok()
            break
        pacer.report_throttled()
    result = quick_score(stock.symbol, data, stock.sector, stock.industry, stock.basic_industry)
    return stock, result, time.monotonic() - started


def run(stocks: list[Stock], workers: int = 4, stocks_per_sec: float = 1.5,
        store: bool = True) -> list[tuple[Stock, QuickScore, float]]:
    out = []
    pacer = _Pacer(stocks_per_sec)
    stored = 0
    write_failures = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one, s, pacer) for s in stocks]
        for i, fut in enumerate(as_completed(futures), 1):
            stock, result, secs = fut.result()
            out.append((stock, result, secs))
            if store and not result.error:
                session = get_db()  # short-lived session per write: results land one by one
                try:
                    stored += upsert_quick_score(session, stock.id, result) is not None
                except Exception as e:  # noqa: BLE001 — one bad write must never stop the rest of the run
                    session.rollback()
                    write_failures += 1
                    print(f"  ! could not store {stock.symbol}: {type(e).__name__}: {str(e).splitlines()[0][:120]}", flush=True)
                finally:
                    session.close()
            if i % 25 == 0:
                print(f"  ...{i}/{len(stocks)} processed, {stored} stored, {write_failures} write failures", flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", help="comma-separated NSE symbols")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rate", type=float, default=1.5, help="target stocks/second across all workers (uncached stocks)")
    ap.add_argument("--csv", help="write results to this CSV path")
    ap.add_argument("--no-store", action="store_true", help="score only; don't write to fa_quick_scores")
    ap.add_argument("--force", action="store_true", help="re-score even stocks scored recently")
    ap.add_argument("--fresh-days", type=float, default=7.0, help="skip stocks scored within this many days")
    args = ap.parse_args()

    db = get_db()
    try:
        q = db.query(Stock).filter(Stock.is_active.is_(True))
        if args.symbols:
            q = q.filter(Stock.symbol.in_([s.strip().upper() for s in args.symbols.split(",")]))
        if not args.force and not args.no_store:
            skip = recently_scored_ids(db, args.fresh_days)
            if skip:
                q = q.filter(Stock.id.notin_(skip))
                print(f"skipping {len(skip)} stocks already scored within {args.fresh_days:g} days (use --force to redo)")
        stocks = q.order_by(Stock.market_cap.desc().nulls_last(), Stock.symbol).limit(args.limit).all()
        db.expunge_all()
    finally:
        db.close()

    wall = time.monotonic()
    results = run(stocks, args.workers, args.rate, store=not args.no_store)
    wall = time.monotonic() - wall
    ok = [r for r in results if not r[1].error]
    print(f"\n{len(ok)}/{len(results)} scored in {wall:.0f}s wall ({wall / max(len(results), 1):.2f}s/stock)")
    for stock, r, secs in sorted(results, key=lambda t: t[0].symbol):
        if r.error:
            print(f"  {stock.symbol:12} ERROR {r.error[:70]}")
        else:
            sc = r.refined
            print(f"  {stock.symbol:12} {r.sector_framework:24} overall {sc['overall']:5.1f} "
                  + " ".join(f"{k[:4]} {sc[k]:3.0f}" for k in SCORE_KEYS[:-1]) + f"  ({secs:.1f}s)")

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["symbol", "framework", *SCORE_KEYS, "rating", "valuation_view", "error"])
            for stock, r, _ in results:
                sc = r.refined or {}
                w.writerow([stock.symbol, r.sector_framework, *[sc.get(k) for k in SCORE_KEYS],
                            sc.get("overall_rating"), sc.get("valuation_view"), r.error])


if __name__ == "__main__":
    main()
