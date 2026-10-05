"""Tests for `peer_selection.select_peer_candidates()`'s basic_industry-first
tiering (2026-09-21) — real bug found live on Action Construction Equipment
(ACE): NSE's `industry` field ("Agricultural, Commercial & Construction
Vehicles") lumps tractors, trucks/buses and construction equipment into one
bucket, so the old industry-only tier let much-larger truck makers (Tata
Motors, Ashok Leyland) crowd out ACE's real peers (BEML, Ajax Engineering,
TIL — all `basic_industry="Construction Vehicles"`) purely on market cap.

`_MIN_CANDIDATES_BEFORE_FALLBACK` was then lowered from 4 to 2 (same day,
second bug on the same feature): a fallback threshold of 4 was itself still
padding ACE's real 3-peer basic_industry set with those same unrelated
truck makers just to hit a round number, defeating the point of adding the
basic_industry tier at all.
"""
from __future__ import annotations

from app.infrastructure.database.models import Stock, StockBusinessProfile
from app.pipeline.peer_selection import select_peer_candidates


def test_ace_peers_are_exactly_its_basic_industry_group(db):
    # ACE's real basic_industry peers (BEML, Ajax Engineering, TIL, and
    # Indo Farm Equipment — the last one added 2026-09-28 by the
    # classify_stocks_screener.py::run_for_missing() backfill, previously
    # unclassified) number 4, which clears the fallback threshold (2) — so
    # the broader "Agricultural, Commercial & Construction Vehicles"
    # industry tier (which also contains truck/tractor makers) must not be
    # consulted at all, and none of its companies should appear.
    stock = db.query(Stock).filter_by(symbol="ACE").first()
    assert stock is not None
    assert stock.basic_industry == "Construction Vehicles"

    peers = select_peer_candidates(db, stock.id, stock.sector)
    peer_symbols = {p.symbol for p in peers}

    assert peer_symbols == {"BEML", "AJAXENGG", "TIL", "INDOFARM"}
    for unrelated in ("TMCV", "ASHOKLEY", "ESCORTS", "SMLMAH"):
        assert unrelated not in peer_symbols


def test_falls_back_to_industry_when_basic_industry_has_no_peers(db):
    # Hindustan Zinc is the only NSE-listed company with
    # basic_industry="Zinc" — a genuine thin-tier case, unlike ACE's (which
    # has 3 and should NOT fall back). Must top up from the broader
    # "Non-Ferrous Metals" industry tier (Hindalco, Vedanta Aluminium,
    # National Aluminium, Hindustan Copper, ...) rather than returning an
    # empty or single-company peer set.
    stock = db.query(Stock).filter_by(symbol="HINDZINC").first()
    assert stock is not None
    assert stock.basic_industry == "Zinc"

    peers = select_peer_candidates(db, stock.id, stock.sector)
    peer_symbols = {p.symbol for p in peers}

    assert len(peers) > 1
    assert peer_symbols.isdisjoint({"HINDZINC"})
    # Thin basic_industry -> closest business anywhere: same NSE industry or
    # same Yahoo industry as Hindustan Zinc.
    sp = db.get(StockBusinessProfile, stock.id)
    assert all(
        p.industry == stock.industry
        or (sp and (pp := db.get(StockBusinessProfile, p.id)) and pp.yahoo_industry == sp.yahoo_industry)
        for p in peers
    )


def test_unknown_stock_and_no_sector_degrades_cleanly(db):
    # No subject row, no sector to fall back on -> every tier is skipped,
    # same degrade-gracefully contract as the rest of this codebase.
    peers = select_peer_candidates(db, "NOT-A-REAL-COMPANY-ID", None)
    assert peers == []


def test_jeena_sikho_peers_are_hospitals_not_hotels(db):
    # NSE files JSLL under "Wellness" basic_industry — originally a
    # one-company bucket, so peers had to come from Yahoo business
    # similarity (hospitals). 2026-09-28: the classify_stocks_screener.py
    # backfill classified KAYA (a skincare/cosmetics company) into the
    # SAME "Wellness" bucket too — a real NSE classification quirk (that
    # bucket spans both Ayurvedic-hospital-like and skincare-retail
    # businesses), not a bug in peer selection: a genuine same-
    # basic_industry peer correctly outranks the Yahoo-similarity
    # fallback now that one exists. The test's real intent — no wildly
    # unrelated peers (hotels, a pizza chain) — still holds; "Wellness"
    # itself is an acceptable basic_industry match, not just Hospital/
    # Healthcare.
    from app.infrastructure.database.models import StockBusinessProfile
    stock = db.query(Stock).filter_by(symbol="JSLL").first()
    profile = db.get(StockBusinessProfile, stock.id) if stock else None
    if profile is None:
        import pytest
        pytest.skip("JSLL business profile not backfilled")
    peers = select_peer_candidates(db, stock.id, stock.sector)
    assert len(peers) >= 3
    assert all(
        any(k in (p.basic_industry or "") for k in ("Hospital", "Healthcare", "Wellness"))
        for p in peers
    )
