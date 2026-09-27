"""Tests for `balance_sheet_intelligence.coverage`/`sector_routing`
(Balance Sheet Analysis Engine, Milestone 5) — the mandatory coverage audit
is the highest-value test in this whole plan: it locks down that every
structurally-absent spec item is honestly reported, never silently
AVAILABLE and never silently omitted.
"""
from __future__ import annotations

from app.calculations.balance_sheet_intelligence import coverage, sector_routing
from app.calculations.balance_sheet_intelligence.canonical_fields import STRUCTURALLY_ABSENT

_FULL_FACTS = {
    "cash": 66.9, "receivables": 5000.0, "inventory": 3000.0, "payables": 2000.0,
    "borrowings": 102.0, "capital_work_in_progress": 9838.0, "equity_capital": 157.0,
    "reserves": 106999.0, "total_assets": 148880.0, "total_liabilities": 148880.0,
    "current_assets": 50000.0, "current_liabilities": 36480.0, "ebit": 14788.0,
    "interest_expense": 200.0,
}


def test_structurally_absent_fields_never_available():
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    always_gap_metrics = ("ar_aging", "inventory_aging", "ap_aging", "debt_maturity",
                           "related_party_loans", "contingent_liabilities", "gross_ppe",
                           "accrued_expenses", "deferred_revenue")
    for metric in always_gap_metrics:
        assert result["metrics"][metric]["status"] in ("MISSING_INPUT", "SOURCE_REQUIRED")
        assert result["metrics"][metric]["status"] != "AVAILABLE"


def test_structurally_absent_fields_stay_absent_even_with_full_facts():
    """Even a `facts` dict with every real field populated must not make
    an inherently-unavailable metric look available — these can never be
    computed from any source, full stop."""
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    assert result["metrics"]["ar_aging"]["status"] == "SOURCE_REQUIRED"
    assert result["metrics"]["contingent_liabilities"]["status"] == "SOURCE_REQUIRED"


def test_available_when_all_dependencies_present():
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    for metric in ("cash", "receivables", "inventory", "payables", "debt", "net_worth", "current_ratio"):
        assert result["metrics"][metric]["status"] == "AVAILABLE"


def test_missing_input_when_dependency_absent():
    facts = dict(_FULL_FACTS)
    del facts["cash"]
    result = coverage.compute_coverage_audit(facts)
    assert result["metrics"]["cash"]["status"] == "MISSING_INPUT"


def test_partial_when_some_but_not_all_dependencies_present():
    facts = {"borrowings": 102.0}  # cash missing
    result = coverage.compute_coverage_audit(facts)
    assert result["metrics"]["net_debt"]["status"] == "PARTIAL"


def test_working_capital_ratios_are_partial_not_available_when_present():
    """DSO/DIO/DPO/CCC use a documented proxy formula (closing balance /
    total revenue, not average balance / credit sales) — even with the
    underlying receivables/inventory/payables present, these must never
    read as AVAILABLE, since that would misrepresent the spec's preferred
    formula as having been used."""
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    for metric in ("dso", "dio", "dpo", "ccc"):
        assert result["metrics"][metric]["status"] == "PARTIAL"


def test_dso_missing_input_when_receivables_absent():
    facts = dict(_FULL_FACTS)
    del facts["receivables"]
    result = coverage.compute_coverage_audit(facts)
    assert result["metrics"]["dso"]["status"] == "MISSING_INPUT"


def test_inventory_turnover_always_missing_input_no_cogs_source():
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    assert result["metrics"]["inventory_turnover"]["status"] == "MISSING_INPUT"


def test_inventory_turnover_not_applicable_when_sector_not_inventory_material():
    """2026-09-20 scope call: sectors where inventory isn't core to the
    business get NOT_APPLICABLE instead of MISSING_INPUT — same absent
    COGS input, different (honest) label."""
    result = coverage.compute_coverage_audit(_FULL_FACTS, is_inventory_material=False, sector_name="Healthcare")
    assert result["metrics"]["inventory_turnover"]["status"] == "NOT_APPLICABLE"
    assert "Healthcare" in result["metrics"]["inventory_turnover"]["reason"]


def test_not_applicable_excluded_from_coverage_pct_and_top_gaps():
    material = coverage.compute_coverage_audit(_FULL_FACTS, is_inventory_material=True)
    not_material = coverage.compute_coverage_audit(_FULL_FACTS, is_inventory_material=False, sector_name="Healthcare")
    # Excluded from the denominator entirely, not just the numerator — a
    # not-applicable metric shouldn't drag down "how much of what's
    # relevant is available".
    assert not_material["total_metrics"] == material["total_metrics"] - 1
    assert not_material["total_metrics_tracked"] == material["total_metrics_tracked"]
    assert not_material["coverage_pct"] > material["coverage_pct"]
    assert "inventory_turnover" not in {g["metric"] for g in coverage.top_source_gaps(not_material)}


def test_coverage_pct_reflects_available_and_calculable_only():
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    assert 0 < result["coverage_pct"] < 100
    # 6, not 9 — gross_ppe/accrued_expenses/deferred_revenue moved out of
    # the always-SOURCE_REQUIRED bucket (2026-09-16, NSE annual-report
    # extraction generalized past banking-only) into real dependency
    # checks; _FULL_FACTS has no values for them, so they resolve
    # MISSING_INPUT instead — see test_annual_report_sourced_fields below.
    assert result["summary"]["SOURCE_REQUIRED"] >= 6


def test_annual_report_sourced_fields_available_when_present():
    """gross_ppe/accrued_expenses/deferred_revenue are genuinely obtainable
    now (NSE annual-report extraction) — unlike the 6 still-always-absent
    metrics, they must read AVAILABLE once the ledger actually has a value,
    not stay permanently SOURCE_REQUIRED."""
    facts = dict(_FULL_FACTS)
    facts.update({"gross_ppe": 39208.0, "accrued_expenses": 657.0, "deferred_revenue": 694.0})
    result = coverage.compute_coverage_audit(facts)
    for metric in ("gross_ppe", "accrued_expenses", "deferred_revenue"):
        assert result["metrics"][metric]["status"] == "AVAILABLE"
        assert result["metrics"][metric]["reason"] is None


def test_annual_report_sourced_fields_missing_input_with_explanatory_reason():
    """Absent from `facts` (extraction hasn't run/found anything for this
    company) must still be distinguishable from the 6 truly-structural
    SOURCE_REQUIRED gaps — MISSING_INPUT with a reason that says WHY,
    not just the generic 'Missing: <field>' every other MISSING_INPUT
    metric gets."""
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    for metric in ("gross_ppe", "accrued_expenses", "deferred_revenue"):
        assert result["metrics"][metric]["status"] == "MISSING_INPUT"
        assert "NSE annual report" in result["metrics"][metric]["reason"]


def test_top_source_gaps_prioritizes_aging_first():
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    gaps = coverage.top_source_gaps(result)
    high_priority_metrics = {g["metric"] for g in gaps if g["priority"] == "HIGH"}
    assert {"ar_aging", "inventory_aging", "ap_aging"} <= high_priority_metrics
    # HIGH priority gaps must sort before MEDIUM/LOW
    priorities_in_order = [g["priority"] for g in gaps]
    assert priorities_in_order == sorted(priorities_in_order, key=lambda p: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[p])


def test_gap_reason_matches_canonical_fields_reason_text():
    result = coverage.compute_coverage_audit(_FULL_FACTS)
    assert result["metrics"]["ar_aging"]["reason"] == STRUCTURALLY_ABSENT["ar_aging"]


# ── sector_routing.py ────────────────────────────────────────────────────────

def test_is_financial_institution_true_for_banks():
    assert sector_routing.is_financial_institution("Banks") is True


def test_is_financial_institution_false_for_manufacturing():
    assert sector_routing.is_financial_institution("Auto Manufacturers") is False


def test_is_financial_institution_false_for_none():
    assert sector_routing.is_financial_institution(None) is False


def test_financial_institution_summary_never_includes_inventory():
    summary = sector_routing.financial_institution_summary({"deposits": 3000.0, "total_assets": 5000.0})
    assert "inventory" not in summary
    assert "dio" not in summary
    assert summary["deposits"] == 3000.0


def test_is_inventory_material_true_for_goods_sectors():
    for sector in ("Retail", "Fast Moving Consumer Goods", "Automobile", "Capital Goods", "Chemicals",
                   "Cement", "Metals", "Real Estate"):
        assert sector_routing.is_inventory_material(sector) is True


def test_is_inventory_material_false_for_service_sectors():
    for sector in ("Information Technology", "Telecom", "Services", "Media & Entertainment", "Aviation"):
        assert sector_routing.is_inventory_material(sector) is False


def test_is_inventory_material_healthcare_split_by_basic_industry():
    """Healthcare covers both hospitals (no material inventory) and pharma/
    device manufacturers (real inventory) under one sector_name — the
    exact ambiguity that prompted this feature (GPT Healthcare, a
    hospital)."""
    assert sector_routing.is_inventory_material("Healthcare", "Hospital") is False
    assert sector_routing.is_inventory_material("Healthcare", "Healthcare Service Provider") is False
    assert sector_routing.is_inventory_material("Healthcare", "Pharmaceuticals") is True
    assert sector_routing.is_inventory_material("Healthcare", "Biotechnology") is True
    assert sector_routing.is_inventory_material("Healthcare", None) is False  # unknown basic_industry -> assume service (safer default for the sector's majority)


def test_is_inventory_material_unknown_sector_defaults_true():
    """An unrecognized/None sector_name must not suppress a real gap on a
    guess — defaults to treating inventory as material (the old, universal
    behavior) rather than silently hiding it. Only sectors explicitly
    reviewed and added to INVENTORY_LIGHT_SECTORS get exempted; a brand new
    sector this app hasn't classified yet stays conservative, unlike a
    naive "not in the material list" check would produce."""
    assert sector_routing.is_inventory_material(None) is True
    assert sector_routing.is_inventory_material("Some New Sector Not Yet Classified") is True


def test_inventory_material_and_light_sector_sets_never_overlap():
    from app.calculations.balance_sheet_intelligence.canonical_fields import (
        INVENTORY_LIGHT_SECTORS, INVENTORY_MATERIAL_SECTORS,
    )
    assert INVENTORY_MATERIAL_SECTORS.isdisjoint(INVENTORY_LIGHT_SECTORS)
