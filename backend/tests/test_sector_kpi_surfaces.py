"""Guards that every place a sector KPI can appear stays in sync — so a new
sector added to the Quarterly Sector KPI engine shows up in the dashboard,
the PDF and the offline HTML export automatically, and its figures reach the
sector score, instead of silently living only in the database.

Each test fails the moment someone adds a sector/unit/metric to one layer
without the others.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.calculations import quarterly_sector_kpis as qsk
from app.infrastructure.database import metric_store
from app.reporting import equity_report_mapper as erm
from app.sectors import ledger_bridge
from app.sectors.registry import _FRAMEWORKS

_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_KPI = (_ROOT / "frontend/src/components/sections/QuarterlySection.tsx").read_text()
_EXPORT_SERVICE = (Path(__file__).resolve().parents[1] / "app/reporting/html_export_service.py").read_text()
# A real stock id (metric rows have an FK to `stocks`) that has no ledger data of its
# own, so synthetic rows in a rolled-back test transaction are the only ones seen.
_BLANK_COMPANY = "NSE:SUNTV"
_ALL_UNITS = {unit for defs in qsk._SECTOR_METRICS.values() for _, _, unit in defs}


def test_every_kpi_unit_has_frontend_and_pdf_formatting():
    """A unit with no formatter falls back to a bare number (e.g. ARPOB shown
    without ₹) — catch it here rather than in a client's PDF."""
    for unit in _ALL_UNITS - {"%"}:
        assert f'case "{unit}"' in _FRONTEND_KPI, f"frontend fmtSectorKpiValue lacks unit {unit!r}"
        assert unit in erm._KPI_UNIT_FORMATS, f"PDF _KPI_UNIT_FORMATS lacks unit {unit!r}"


@pytest.mark.parametrize("sector", sorted(qsk._SECTOR_METRICS))
def test_every_configured_sector_flows_through_to_the_pdf_mapper(db, sector):
    """Synthetic value for every metric of every configured sector -> the same
    compute function the dashboard uses -> the PDF mapper. Nothing is dropped."""
    company = _BLANK_COMPANY
    for i, (key, _label, unit) in enumerate(qsk._SECTOR_METRICS[sector]):
        metric_store.insert_metric_value(
            db, company_id=company, metric_key=key, period="2026-06-30", value=10.0 + i, unit=unit,
            statement_type="CONSOLIDATED", source="NSE_PRESS_RELEASE", source_tier=1,
            reported_or_calculated="REPORTED", confidence="HIGH",
        )
    kpis = qsk.compute_quarterly_sector_kpis(db, company, sector)
    assert kpis["available"] is True
    assert len(kpis["metrics"]) == len(qsk._SECTOR_METRICS[sector])
    for m in kpis["metrics"]:  # provenance travels with every value
        assert m["source_label"] == "Results press release" and m["confidence"] == "HIGH"
    section = erm._sector_kpis(kpis)
    assert section is not None and len(section["metrics"]) == len(kpis["metrics"])
    assert all(g["value"] not in (None, "") and g["note"] == "Results press release" for g in section["metrics"])


def test_offline_html_export_bundles_the_tabs_that_need_live_data():
    for path in ("quarterly-intelligence", "bank-roe"):
        assert path in _EXPORT_SERVICE, f"export bundle missing /{path}/ — that tab would fail offline"


def test_pdf_report_service_passes_both_new_sections_to_the_mapper():
    service = (Path(__file__).resolve().parents[1] / "app/services/equity_pdf_service.py").read_text()
    assert "sector_kpis=sector_kpis" in service and "bank_roe=bank_roe" in service


def test_quarterly_score_fallbacks_point_at_real_keys_and_real_metrics():
    quarterly_keys = {k for defs in qsk._SECTOR_METRICS.values() for k, _, _ in defs}
    declared = {m.name for fw in _FRAMEWORKS for m in fw.key_metrics() if not m.available_from_yfinance}
    for sector_metric, qkey in ledger_bridge.QUARTERLY_FALLBACKS.items():
        assert sector_metric in declared, f"{sector_metric} is not a declared non-yfinance sector metric"
        for k in ((qkey,) if isinstance(qkey, str) else qkey):
            assert k in quarterly_keys or k == "premiumization_pct", f"{k} is not surfaced by any sector"


def test_absolute_flow_metrics_never_fall_back_to_a_single_quarter():
    """pre_sales_value thresholds are annual INR Cr; one quarter of bookings
    would be scored as a weak year."""
    assert "pre_sales_value" not in ledger_bridge.QUARTERLY_FALLBACKS


def test_quarterly_value_reaches_sector_score_inputs(db):
    metric_store.insert_metric_value(
        db, company_id=_BLANK_COMPANY, metric_key="qtr_healthcare_bed_occupancy", period="2026-06-30", value=75.0,
        unit="%", statement_type="CONSOLIDATED", source="MANUAL", source_tier=1,
        reported_or_calculated="REPORTED", confidence="HIGH",
    )
    fd: dict = {}
    ledger_bridge.inject_ledger_bridge(fd, db, _BLANK_COMPANY, ["bed_occupancy_pct", "arpob"])
    assert fd["_ledger_metrics"] == {"bed_occupancy_pct": 75.0}  # arpob absent -> stays N/A, never 0


def test_annual_value_wins_over_quarterly_fallback(db):
    for key, value, period in (("export_revenue_pct", 30.0, "2026-03-31"), ("qtr_chemicals_export_revenue_pct", 55.0, "2026-06-30")):
        metric_store.insert_metric_value(
            db, company_id=_BLANK_COMPANY, metric_key=key, period=period, value=value, unit="%",
            statement_type="STANDALONE", source="NSE_ANNUAL_REPORT", source_tier=1,
            reported_or_calculated="REPORTED", confidence="HIGH",
        )
    fd: dict = {}
    ledger_bridge.inject_ledger_bridge(fd, db, _BLANK_COMPANY, ["export_revenue_pct"])
    assert fd["_ledger_metrics"]["export_revenue_pct"] == 30.0


def test_misfiled_investor_presentation_is_still_found(monkeypatch):
    from app.ingestion import nse_investor_presentation_client as ipc

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {"desc": "General Updates", "attchmntText": "Bank Of Baroda has informed the Exchange about Investor Presentation", "attchmntFile": "https://x/bob.pdf"},
                {"desc": "General Updates", "attchmntText": "Bank Of Baroda has informed the Exchange about MCLR", "attchmntFile": "https://x/mclr.pdf"},
                {"desc": "Investor Presentation", "attchmntText": "", "attchmntFile": "https://x/normal.pdf"},
            ]

    class _S:
        def get(self, *a, **k):
            return _Resp()

    files = [f["attchmntFile"] for f in ipc.find_investor_presentation_filings("BANKBARODA", session=_S())]
    assert files == ["https://x/bob.pdf", "https://x/normal.pdf"]


def test_small_rupee_values_keep_their_decimals_in_pdf():
    from app.reporting.equity_report_mapper import _fmt_kpi
    assert _fmt_kpi(6.04, "INR") == "Rs 6.04"      # airline yield / CASK, not "Rs 6"
    assert _fmt_kpi(8546.0, "INR") == "Rs 8,546"
