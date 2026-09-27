"""Intra-sector peer engine (spec Stage 5, Stage 23).

Peer *selection* reuses `app/pipeline/peer_selection.py::select_peer_candidates()`
verbatim (the same industry-first/sector-fallback algorithm `orchestrator.py`'s
existing yfinance-based peer comparison already uses) — this module only adds
what didn't exist before: margin percentiles computed from the `pnl_*`
ledger (via `cascade.py`), not from yfinance, so a company's PAT-margin/
EBITDA-margin standing is measured against the same Screener-sourced figures
the rest of this P&L engine uses, not a separate data source.

`compute_fintech_peer_percentiles()` (2026-09-17) is a second, parallel
function rather than a generalization of `compute_peer_margin_percentiles()`
— its metrics (gtv_growth, take_rate) live in `metric_store`'s ledger
(sourced from earnings-call-transcript extraction, see
`app/ingestion/earnings_call_client.py`), not in the `pnl_*` cascade, so it
needs a different per-company lookup (`metric_store.get_latest_period_value`
instead of `build_income_cascade`) and has no fiscal `period` to key off —
these are snapshot-dated management-commentary figures, not period-end
financial-statement figures.
"""
from __future__ import annotations

import statistics

from sqlalchemy.orm import Session

from app.calculations.pl_intelligence.cascade import build_income_cascade
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import FundamentalAnalysis, Stock
from app.pipeline.peer_selection import select_peer_candidates

_MARGIN_FIELDS = ("ebitda_margin", "pat_margin")
_FINTECH_FIELDS = ("gtv_growth", "take_rate")


def select_pl_peers(db: Session, stock_id: str, sector: str | None) -> list[Stock]:
    return select_peer_candidates(db, stock_id, sector)


def _margin_at_period(db: Session, company_id: str, period: str, statement_type: str) -> dict[str, float | None]:
    cascade = build_income_cascade(db, company_id, statement_type=statement_type)
    entry = cascade.get(period, {})
    return {field: entry.get(field) for field in _MARGIN_FIELDS}


def _percentile(subject_val: float | None, peer_vals: list[float]) -> int | None:
    """Higher margin = better, always, for every field this module computes
    — matches `orchestrator.py::_find_peers`'s identical formula (kept
    intentionally the same shape so a "percentile" means the same thing
    everywhere in this app)."""
    if subject_val is None or not peer_vals:
        return None
    all_vals = sorted(peer_vals + [subject_val])
    rank = all_vals.index(subject_val) + 1
    return round((rank / len(all_vals)) * 100)


def _analysis_peer_margins(db: Session, stock_id: str) -> tuple[dict[str, list[float]], dict[str, float | None]]:
    """Peer + subject EBITDA/PAT margins from the company's latest COMPLETED
    analysis — the Yahoo-sourced (consolidated) numbers the Peers tab shows,
    captured at analysis time by the `peer_comparison` stage. Used ONLY as a
    fallback: the ledger path above needs every peer's own Screener P&L
    history ingested, which is only true for peers that were themselves
    analysed. Real gap found live on Jeena Sikho Lifecare (2026-09-24, user's
    report — "I can see peers in the Peers tab but it's not injecting in
    P&L"): all 6 peers were listed, none had ledger data, so the whole
    Peer Benchmark card (and M1/M2 of the Master P&L Score) came back empty."""
    analysis = (
        db.query(FundamentalAnalysis)
        .filter(FundamentalAnalysis.stock_id == stock_id, FundamentalAnalysis.status == "COMPLETED")
        .order_by(FundamentalAnalysis.created_at.desc())
        .first()
    )
    peers_blob = (analysis.peers or {}) if analysis is not None else {}
    peer_values: dict[str, list[float]] = {field: [] for field in _MARGIN_FIELDS}
    for peer in (peers_blob.get("peers") or []):
        for field in _MARGIN_FIELDS:
            v = peer.get(field)
            if isinstance(v, (int, float)):
                peer_values[field].append(float(v))
    company = peers_blob.get("company_metrics") or {}
    subject = {f: (float(company[f]) if isinstance(company.get(f), (int, float)) else None) for f in _MARGIN_FIELDS}
    return peer_values, subject


def compute_peer_margin_percentiles(
    db: Session, stock_id: str, sector: str | None, period: str, statement_type: str = "CONSOLIDATED",
) -> dict:
    """Sector median/mean/min/max + the subject company's rank and
    percentile, for EBITDA margin and PAT margin, at one fiscal `period`.
    Peers with no cascade data for that period (e.g. not yet re-ingested
    under both statement types) are simply excluded from the peer
    population, not treated as a 0% margin."""
    peers = select_pl_peers(db, stock_id, sector)
    subject_margins = _margin_at_period(db, stock_id, period, statement_type)

    peer_margins: dict[str, list[float]] = {field: [] for field in _MARGIN_FIELDS}
    for peer in peers:
        margins = _margin_at_period(db, peer.id, period, statement_type)
        for field in _MARGIN_FIELDS:
            if margins[field] is not None:
                peer_margins[field].append(margins[field])

    result: dict = {"peer_count": len(peers), "period": period, "statement_type": statement_type,
                    "peer_source": {}}
    fallback_values: dict[str, list[float]] | None = None
    fallback_subject: dict[str, float | None] = {}
    for field in _MARGIN_FIELDS:
        vals = peer_margins[field]
        subject_val = subject_margins[field]
        result["peer_source"][field] = "LEDGER"
        if not vals:
            # No peer has ledger data for this margin — fall back to the
            # Yahoo peer margins already captured for the Peers tab.
            if fallback_values is None:
                fallback_values, fallback_subject = _analysis_peer_margins(db, stock_id)
            if fallback_values[field]:
                vals = fallback_values[field]
                subject_val = subject_val if subject_val is not None else fallback_subject.get(field)
                result["peer_source"][field] = "YAHOO_PEER_TAB"
        result[field] = {
            "company_value": subject_val,
            "peer_median": round(statistics.median(vals), 2) if vals else None,
            "peer_mean": round(statistics.mean(vals), 2) if vals else None,
            "peer_min": round(min(vals), 2) if vals else None,
            "peer_max": round(max(vals), 2) if vals else None,
            "percentile": _percentile(subject_val, vals),
        }
    return result


def _latest_fintech_value(db: Session, company_id: str, metric_key: str) -> float | None:
    # STANDALONE, not CONSOLIDATED — real bug caught live 2026-09-17:
    # `earnings_call_client.py::ingest_earnings_call_transcript()` never
    # passes `statement_type` to `insert_metric_value()`, so these rows
    # land under `metric_store.DEFAULT_STATEMENT_TYPE` ("STANDALONE") by
    # default. That default is arguably a mislabel — earnings-call
    # commentary isn't genuinely standalone-vs-consolidated scoped, it's
    # one company-wide management figure — but matching where the data
    # actually is beats querying a statement_type it was never written
    # under and silently getting nothing back.
    row = metric_store.get_latest_period_value(db, company_id, metric_key, statement_type="STANDALONE")
    return float(row.value) if row is not None and row.value is not None else None


def compute_fintech_peer_percentiles(db: Session, stock_id: str, sector: str | None) -> dict:
    """Same shape and same "excluded, not zero" degrade-gracefully contract
    as `compute_peer_margin_percentiles()`, for `gtv_growth`/`take_rate` —
    the two Fintech-specific metrics `app/sectors/fintech.py` declares as
    ledger-sourced. Peers with no earnings-call extraction on file yet
    (the common case until each peer has been individually analyzed with
    `extract_fintech_metrics=True`) are simply excluded from the peer
    population, exactly like a peer missing cascade data for a given period
    in the margin-percentile function above."""
    peers = select_pl_peers(db, stock_id, sector)
    subject_values = {field: _latest_fintech_value(db, stock_id, field) for field in _FINTECH_FIELDS}

    peer_values: dict[str, list[float]] = {field: [] for field in _FINTECH_FIELDS}
    for peer in peers:
        for field in _FINTECH_FIELDS:
            v = _latest_fintech_value(db, peer.id, field)
            if v is not None:
                peer_values[field].append(v)

    result: dict = {"peer_count": len(peers)}
    for field in _FINTECH_FIELDS:
        vals = peer_values[field]
        subject_val = subject_values[field]
        result[field] = {
            "company_value": subject_val,
            "peer_median": round(statistics.median(vals), 2) if vals else None,
            "peer_mean": round(statistics.mean(vals), 2) if vals else None,
            "peer_min": round(min(vals), 2) if vals else None,
            "peer_max": round(max(vals), 2) if vals else None,
            "percentile": _percentile(subject_val, vals),
        }
    return result
