"""Tests for `concall_report_data._dedupe_guidance()` — pure function, no
DB needed (operates on already-fetched ManagementGuidance rows)."""
from __future__ import annotations

from app.infrastructure.database.models import ManagementGuidance
from app.interpretation.concall_report_data import _dedupe_guidance


def _row(**kwargs):
    defaults = dict(
        metric="capex", category="Capital Allocation", period=None,
        guidance_type="quantitative", target_low=1200.0, target_high=1500.0,
        target_value=None, unit="crores",
        statement="Targeted for the full year is another INR1,200 crores to INR1,500 crores.",
        tone="positive", confidence="high", certainty="explicit", conditional=False, status="NEW",
    )
    defaults.update(kwargs)
    return ManagementGuidance(**defaults)


def test_exact_duplicate_collapses_to_one():
    rows = [_row(), _row()]
    result = _dedupe_guidance(rows)
    assert len(result) == 1


def test_unit_formatting_difference_still_collapses():
    """Real gap found live on GNFC: the same figure landed once as
    unit="crores" and once as unit="INR crores" across two extraction
    runs — a formatting difference, not a different number."""
    rows = [_row(unit="crores"), _row(unit="INR crores")]
    result = _dedupe_guidance(rows)
    assert len(result) == 1


def test_category_difference_still_collapses():
    """Same quote, same targets, different category tag across runs —
    still the same underlying guidance, not two."""
    rows = [_row(category="Capital Allocation"), _row(category="Operating")]
    result = _dedupe_guidance(rows)
    assert len(result) == 1


def test_different_targets_kept_separate():
    rows = [_row(target_low=1200.0, target_high=1500.0), _row(target_low=1500.0, target_high=1800.0)]
    result = _dedupe_guidance(rows)
    assert len(result) == 2


def test_different_metric_kept_separate_even_with_same_statement():
    rows = [_row(metric="capex"), _row(metric="pricing")]
    result = _dedupe_guidance(rows)
    assert len(result) == 2


def test_different_statement_kept_separate():
    rows = [_row(statement="Statement A"), _row(statement="Statement B")]
    result = _dedupe_guidance(rows)
    assert len(result) == 2
