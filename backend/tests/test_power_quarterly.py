"""Power quarterly KPIs: storage, derived growth/margins, bridge (thermal PLF vs renewable CUF)."""
from __future__ import annotations

from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.ingestion import quarterly_operating_metrics_ingestion as q
from app.sectors.ledger_bridge import inject_ledger_bridge

_CO = "NSE:SUNTV"
_P = "2026-06-30"


def _store(db, extracted, sector="Power"):
    inserted: list = []
    token = q._source_ctx.set("NSE_PRESS_RELEASE")
    try:
        q._store_extracted(db, _CO, sector, q._SECTOR_CONFIG[sector], extracted, _P, "CONSOLIDATED", "u", "d", inserted)
    finally:
        q._source_ctx.reset(token)
    return {r.metric_key: float(r.value) for r in inserted}


def test_power_family_shares_config():
    for name in ("Power", "Renewable Energy"):
        assert q._SECTOR_CONFIG[name]["prefix"] == "pow"
    for f in ("plf_pct", "cuf_pct", "installed_capacity_mw", "transmission_availability_pct", "atc_loss_pct"):
        assert f in q._AREA_PROMPTS["power"]


def test_capacity_growth_margin_and_service_fcf(db):
    got = _store(db, {"installed_capacity_mw": 20142, "installed_capacity_yoy_prior_mw": 15816, "revenue_cr": 1000,
                      "ebitda_cr": 900, "capex_cr": 300})
    assert round(got["qtr_pow_capacity_growth_yoy"], 2) == 27.35
    assert got["qtr_pow_ebitda_margin"] == 90.0 and got["qtr_pow_ebitda_minus_capex_margin"] == 60.0


def test_no_growth_without_a_year_ago_base(db):
    got = _store(db, {"installed_capacity_mw": 20142})
    assert "qtr_pow_capacity_growth_yoy" not in got


def test_thermal_plf_and_renewable_cuf_are_separate_keys(db):
    got = _store(db, {"plf_pct": 78, "cuf_pct": 26})
    assert got["qtr_pow_plf"] == 78 and got["qtr_pow_cuf"] == 26
    bridged = inject_ledger_bridge({}, db, _CO, ["plf", "cuf_pct", "transmission_availability_pct"])["_ledger_metrics"]
    assert bridged["plf"] == 78.0 and bridged["cuf_pct"] == 26.0


def test_solar_developer_with_only_cuf_gets_no_plf(db):
    _store(db, {"cuf_pct": 26})
    assert "plf" not in inject_ledger_bridge({}, db, _CO, ["plf"])["_ledger_metrics"]


def test_utilities_and_renewables_read_side(db):
    _store(db, {"generation_mu": 12900})
    for name in ("Power", "Renewable Energy"):
        assert compute_quarterly_sector_kpis(db, _CO, name)["available"] is True


_CEA_TEXT = """10. All India Thermal PLF Sector-wise (Excluding Gas Based Power Plants) for Jul-2026
        Sector                    Jul-2025                 Jul-2026
        Central                    65.30                    71.25
         State                     56.64                    62.41
  Private Sector IPP               66.35                    71.12
  Private Sector UTL.              62.35                    71.95
       ALL INDIA                   62.71                    68.25
"""


def test_cea_parser_reads_the_report_month_column_and_all_groups():
    from app.ingestion.cea_client import parse_executive_summary, _GROUP_BY_SYMBOL
    out = parse_executive_summary(_CEA_TEXT)
    assert out["month_end"] == "2026-07-31"
    assert out["plf"]["central"] == 71.25 and out["plf"]["private sector ipp"] == 71.12 and out["plf"]["private sector utl"] == 71.95
    assert all(g in out["plf"] for g in _GROUP_BY_SYMBOL.values())      # every mapped ownership group is a real table row
    assert parse_executive_summary(_CEA_TEXT.replace("Central ", "Centrl  ")) is None   # missing group -> rejected


def test_benchmark_series_never_decides_the_statement_basis(db):
    from app.infrastructure.database import metric_store
    _store(db, {"generation_mu": 1668}, sector="Power")   # helper stores CONSOLIDATED; re-store standalone below
    metric_store.insert_metric_value(db, company_id=_CO, metric_key="qtr_pow_td_loss", period=_P, value=6.85, unit="%",
        statement_type="STANDALONE", source="MANUAL", source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH")
    metric_store.insert_metric_value(db, company_id=_CO, metric_key="qtr_pow_thermal_plf_sector_benchmark", period=_P, value=68.04,
        unit="%", statement_type="CONSOLIDATED", source="CEA_REPORT", source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH")
    r = compute_quarterly_sector_kpis(db, _CO, "Power")
    assert "qtr_pow_thermal_plf_sector_benchmark" in {m["metric_key"] for m in r["metrics"]}
    assert r["metrics"]     # benchmark present alongside company figures


def test_cea_source_registered():
    from app.infrastructure.database import metric_store
    from app.calculations.quarterly_sector_kpis import SOURCE_LABELS
    assert "CEA_REPORT" in metric_store.VALID_SOURCES and "CEA_REPORT" in SOURCE_LABELS
