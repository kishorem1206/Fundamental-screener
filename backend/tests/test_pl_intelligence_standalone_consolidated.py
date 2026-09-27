"""CSR + subsidiary-contribution tests (P&L Analysis Engine plan,
Milestone 2). Uses Maruti (NSE:MARUTI, dual-statement-type re-ingested in
Milestone 1) as the real-data fixture, plus pure boundary-value tests for
the CSR band classifier."""
from __future__ import annotations

from datetime import datetime, timezone

from app.calculations.pl_intelligence.standalone_consolidated import (
    _classify_csr,
    compute_csr,
    compute_pat_structural_ratio,
    flag_conglomerate,
    subsidiary_contribution,
)
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock

_STANDALONE_ONLY_FIXTURE_COMPANY = "TEST:CSR_STANDALONE_ONLY_FIXTURE"


def _fixture_company_id(db) -> str:
    stock = db.query(Stock).filter_by(symbol="MARUTI").first()
    assert stock is not None
    return stock.id


def _ensure_standalone_only_fixture_stock(db) -> None:
    if db.get(Stock, _STANDALONE_ONLY_FIXTURE_COMPANY) is not None:
        return
    now = datetime.now(timezone.utc)
    db.add(Stock(
        id=_STANDALONE_ONLY_FIXTURE_COMPANY, symbol="CSR_STANDALONE_ONLY_FIXTURE", exchange="TEST",
        company_name="CSR Standalone-Only Fixture Co.", sector="Automobile and Auto Components",
        is_active=True, created_at=now, updated_at=now,
    ))
    db.flush()


def _insert_standalone_only(db, period: str, value: float) -> None:
    _ensure_standalone_only_fixture_stock(db)
    metric_store.insert_metric_value(
        db, company_id=_STANDALONE_ONLY_FIXTURE_COMPANY, metric_key="pnl_sales", period=period, value=value,
        unit="cr", statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM", source_date=datetime.now(timezone.utc),
    )


def test_csr_band_boundaries():
    assert _classify_csr(0.95) == "PRIMARILY_PARENT_DOMESTIC"
    assert _classify_csr(0.81) == "PRIMARILY_PARENT_DOMESTIC"
    assert _classify_csr(0.80) == "MATERIAL_SUBSIDIARY_CONTRIBUTION"
    assert _classify_csr(0.65) == "MATERIAL_SUBSIDIARY_CONTRIBUTION"
    assert _classify_csr(0.50) == "MATERIAL_SUBSIDIARY_CONTRIBUTION"
    assert _classify_csr(0.40) == "SIGNIFICANT_GROUP_CONTRIBUTION"
    assert _classify_csr(0.30) == "SIGNIFICANT_GROUP_CONTRIBUTION"
    assert _classify_csr(0.15) == "CONSOLIDATED_STRUCTURE_DOMINATES"


def test_compute_csr_unavailable_for_nonexistent_company(db):
    result = compute_csr(db, "NOT-A-REAL-COMPANY-ID", "2025-03-31")
    assert result["csr"] is None
    assert result["confidence"] == "UNAVAILABLE"


def test_compute_csr_real_data(db):
    company_id = _fixture_company_id(db)
    result = compute_csr(db, company_id, "2025-03-31")
    assert result["confidence"] == "HIGH"
    assert result["csr"] is not None
    assert result["standalone_revenue"] is not None
    assert result["consolidated_revenue"] is not None
    # Maruti's standalone and consolidated revenue are very close (no large
    # foreign subsidiary, unlike e.g. Tata Motors/JLR) — CSR should sit
    # near 1.0, firmly in the PRIMARILY_PARENT_DOMESTIC band.
    assert 0.9 < result["csr"] <= 1.05
    assert result["csr_band"] == "PRIMARILY_PARENT_DOMESTIC"
    assert result["consolidated_ever_reported"] is True


def test_compute_csr_consolidated_ever_reported_false_for_genuine_standalone_only_company(db):
    """Regression test for a real gap found live on Kross Ltd (2026-09-24,
    user's own report — "why is consolidated revenue not being injected,
    we have that in Screener right?"): confirmed live that Screener
    genuinely has NO consolidated financial statements for Kross at all
    (a single-entity manufacturer, no subsidiaries) — `confidence:
    "UNAVAILABLE"` alone can't tell a caller whether that's this permanent
    structural fact or just an ordinary transient ingestion gap.
    `consolidated_ever_reported` must be False when the ledger has NO
    CONSOLIDATED pnl_sales row for this company across ANY period."""
    _insert_standalone_only(db, "2025-03-31", 600.0)
    _insert_standalone_only(db, "2026-03-31", 673.0)
    result = compute_csr(db, _STANDALONE_ONLY_FIXTURE_COMPANY, "2026-03-31")
    assert result["standalone_revenue"] == 673.0
    assert result["consolidated_revenue"] is None
    assert result["confidence"] == "UNAVAILABLE"
    assert result["consolidated_ever_reported"] is False


def test_compute_csr_consolidated_ever_reported_true_even_when_this_period_missing(db):
    """A company that DOES have consolidated data for other periods, just
    not this exact one, must still report `consolidated_ever_reported:
    True` — checked across the full history, not just the requested
    period, so this stays distinct from the genuine standalone-only case
    above."""
    company_id = _fixture_company_id(db)  # MARUTI — has real CONSOLIDATED history
    result = compute_csr(db, company_id, "1999-03-31")  # a period with no data on record at all
    assert result["consolidated_revenue"] is None
    assert result["consolidated_ever_reported"] is True


def test_compute_pat_structural_ratio_real_data(db):
    company_id = _fixture_company_id(db)
    result = compute_pat_structural_ratio(db, company_id, "2025-03-31")
    assert result["confidence"] == "HIGH"
    assert result["pat_structural_ratio"] is not None


def test_subsidiary_contribution_real_data(db):
    company_id = _fixture_company_id(db)
    result = subsidiary_contribution(db, company_id, "2025-03-31")
    assert result["confidence"] in ("MEDIUM", "UNAVAILABLE")
    assert "segment_count" in result
    assert isinstance(result["segment_names"], list)


def test_subsidiary_contribution_unavailable_for_nonexistent_company(db):
    result = subsidiary_contribution(db, "NOT-A-REAL-COMPANY-ID", "2025-03-31")
    assert result["subsidiary_revenue"] is None
    assert result["confidence"] == "UNAVAILABLE"
    assert result["segment_count"] == 0


def test_flag_conglomerate_no_segments(db):
    result = flag_conglomerate(db, "NOT-A-REAL-COMPANY-ID")
    assert result == {"is_conglomerate": False, "segment_count": 0, "segment_sector_count": 0,
                       "sotp_required": False, "segment_names": []}


def test_flag_conglomerate_filters_immaterial_segments_real_data(db):
    # Regression test: Maruti has 9 raw BusinessSegment rows, but only
    # "Vehicles" (72.8%) and "Spare Parts..." (20.6%) clear the 10%
    # materiality bar — the rest (Scrap, Fiscal Incentive, etc.) are
    # trivial revenue sub-lines, not real diversified business lines.
    # Before the materiality filter was added, this incorrectly flagged
    # a pure-play car manufacturer as a conglomerate.
    company_id = _fixture_company_id(db)
    result = flag_conglomerate(db, company_id)
    assert result["is_conglomerate"] is False
    assert result["segment_count"] < 3
    assert "Vehicles" in result["segment_names"]
    assert "Scrap" not in result["segment_names"]
    assert "Fiscal Incentive" not in result["segment_names"]
