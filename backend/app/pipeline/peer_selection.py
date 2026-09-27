"""Peer-candidate selection — extracted from `orchestrator.py::_find_peers()`
so the P&L Analysis Engine's peer-percentile work
(`app/calculations/pl_intelligence/peer_engine.py`) can reuse the exact same
selection algorithm instead of re-implementing it. `_find_peers` itself now
calls this function too, so there is exactly one peer-selection
implementation in the codebase, not two that can silently drift apart.

`basic_industry`-first, `industry`-fallback, `sector`-fallback, market-cap-
desc, cap-at-6 (2026-09-21 — added the `basic_industry` tier; real bug found
live on Action Construction Equipment (ACE, a crane/construction-equipment
maker): NSE's `industry` field, "Agricultural, Commercial & Construction
Vehicles", lumps tractors, trucks/buses AND construction equipment into one
bucket. The old industry-first-only logic pulled in Tata Motors (Rs1.68
lakh-cr mkt cap) and Ashok Leyland (Rs9,900cr) — both truck/bus makers —
ahead of ACE's real peers (BEML, Ajax Engineering, TIL — all genuinely
`basic_industry="Construction Vehicles"`) purely because they're much larger
companies within that same coarse industry bucket. `basic_industry` is NSE's
finer classification tier (same one `app/sectors/registry.py::get_framework()`
already prefers first, for the identical reason) — trying it first means a
company's real business-model peers are never crowded out by unrelated,
larger companies that only share the broader industry code.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import Stock, StockBusinessProfile
from app.pipeline.business_similarity import similarity

# Below this many candidates, fall through to the next coarser tier to fill
# out the list — same threshold at every tier (basic_industry -> industry ->
# sector). Deliberately low (2026-09-21, lowered from 4): a genuine
# same-basic_industry peer set of even just 2-3 companies is more useful
# than padding it with a "same broader industry" company that's actually a
# different business (real bug found live: ACE, a crane/construction-
# equipment maker, has only 3 real basic_industry peers — BEML, Ajax
# Engineering, TIL — and a threshold of 4 was pulling in Tata Motors and
# Ashok Leyland, both truck/bus makers, just to hit a round number). Only
# fall back when the more specific tier is nearly empty.
_MIN_CANDIDATES_BEFORE_FALLBACK = 2

# Business-similarity ranking (2026-09-24): peers are the closest BUSINESS by
# Yahoo description (TF-IDF cosine) + same Yahoo industry; market cap is only
# a tie-break. Real gap: Jeena Sikho (Ayurvedic hospitals) is alone in NSE's
# "Wellness" basic_industry, so the old fallback compared it to hotels/pizza.
_SAME_YAHOO_INDUSTRY_BONUS = 0.5
_MIN_SIMILARITY = 0.12


def _rank_by_business(db: Session, subject: Stock, candidates: list[Stock]) -> list[Stock]:
    profiles = {p.stock_id: p for p in db.query(StockBusinessProfile)
                .filter(StockBusinessProfile.stock_id.in_([subject.id] + [c.id for c in candidates])).all()}
    sp = profiles.get(subject.id)

    def score(c: Stock) -> float:
        cp = profiles.get(c.id)
        if cp is None:
            return -1.0
        bonus = _SAME_YAHOO_INDUSTRY_BONUS if sp and sp.yahoo_industry and cp.yahoo_industry == sp.yahoo_industry else 0.0
        return similarity(db, subject.id, c.id) + bonus

    return sorted(candidates, key=lambda c: (score(c), float(c.market_cap or 0)), reverse=True)


def _business_matches(db: Session, subject: Stock, exclude: set[str]) -> list[Stock]:
    """Universe-wide same-Yahoo-industry (or clearly similar description) stocks."""
    sp = db.get(StockBusinessProfile, subject.id)
    if sp is None:
        return []
    pool = (db.query(Stock).join(StockBusinessProfile, StockBusinessProfile.stock_id == Stock.id)
            .filter(Stock.is_active == True, Stock.id != subject.id,  # noqa: E712
                    ~Stock.id.in_(exclude | {subject.id})).all())
    pool = [c for c in pool if similarity(db, subject.id, c.id) >= _MIN_SIMILARITY
            or (sp.yahoo_industry and db.get(StockBusinessProfile, c.id).yahoo_industry == sp.yahoo_industry)]
    return _rank_by_business(db, subject, pool)


def select_peer_candidates(db: Session, stock_id: str, sector: str | None) -> list[Stock]:
    """Up to 6 active peer `Stock` rows for `stock_id`: prefers the same
    `basic_industry` (most specific, up to 12 candidates by market cap desc),
    falls back to the same `industry` and then the same `sector` if fewer
    than 4 candidates were found at the more specific tier, deduplicated and
    capped at 6 to bound downstream fetch time. Tiers are additive (each
    fallback only tops up the list, never replaces what the more specific
    tier already found), so a genuine same-basic_industry peer is always
    ranked ahead of a same-industry-only one, regardless of market cap."""
    subject = db.query(Stock).filter(Stock.id == stock_id).first()
    subject_basic_industry = subject.basic_industry if subject else None
    subject_industry = subject.industry if subject else None

    peers_raw: list[Stock] = []

    if subject_basic_industry:
        same_bi = (
            db.query(Stock)
            .filter(Stock.is_active == True, Stock.id != stock_id,  # noqa: E712
                    Stock.basic_industry == subject_basic_industry)
            .order_by(Stock.market_cap.desc().nullslast())
            .limit(12).all()
        )
        peers_raw.extend(_rank_by_business(db, subject, same_bi) if db.get(StockBusinessProfile, stock_id) else same_bi)

    if len(peers_raw) < _MIN_CANDIDATES_BEFORE_FALLBACK and subject is not None:
        peers_raw.extend(_business_matches(db, subject, {p.id for p in peers_raw}))

    if len(peers_raw) < _MIN_CANDIDATES_BEFORE_FALLBACK and subject_industry:
        existing_ids = {p.id for p in peers_raw}
        same_ind = (
            db.query(Stock)
            .filter(Stock.is_active == True, Stock.id != stock_id,  # noqa: E712
                    Stock.industry == subject_industry, ~Stock.id.in_(existing_ids))
            .order_by(Stock.market_cap.desc().nullslast())
            .limit(12 - len(peers_raw)).all()
        )
        peers_raw.extend(same_ind)

    if len(peers_raw) < _MIN_CANDIDATES_BEFORE_FALLBACK and sector:
        existing_ids = {p.id for p in peers_raw}
        sector_extra = (
            db.query(Stock)
            .filter(Stock.is_active == True, Stock.id != stock_id,  # noqa: E712
                    Stock.sector == sector, ~Stock.id.in_(existing_ids))
            .order_by(Stock.market_cap.desc().nullslast())
            .limit(12 - len(peers_raw)).all()
        )
        peers_raw.extend(sector_extra)

    seen: set[str] = set()
    candidates: list[Stock] = []
    for p in peers_raw:
        if p.id not in seen:
            seen.add(p.id)
            candidates.append(p)
        if len(candidates) >= 6:
            break
    return candidates
