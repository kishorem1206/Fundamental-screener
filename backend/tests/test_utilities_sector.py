"""Utilities -> Utilities (water / waste / other) framework, routing and quarterly KPIs."""
from __future__ import annotations

from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.ingestion import quarterly_operating_metrics_ingestion as q
from app.sectors.classification_map import BASIC_INDUSTRY_TO_FRAMEWORK as M
from app.sectors.ledger_bridge import inject_ledger_bridge
from app.sectors.registry import get_framework

_CO = "NSE:SUNTV"
_P = "2026-06-30"


def _store(db, sector, extracted):
    inserted: list = []
    token = q._source_ctx.set("NSE_PRESS_RELEASE")
    try:
        q._store_extracted(db, _CO, sector, q._SECTOR_CONFIG[sector], extracted, _P, "CONSOLIDATED", "u", "d", inserted)
    finally:
        q._source_ctx.reset(token)
    return {r.metric_key: float(r.value) for r in inserted}


def test_routing_integrated_power_to_power_and_water_waste_stay_utilities():
    assert M["integrated power utilities"] == "Power"       # previously inherited Power's scale under "Utilities"
    assert M["water supply & management"] == "Utilities" and M["waste management"] == "Utilities"
    assert M["gas transmission/marketing"] == "Oil & Gas"   # GAIL was mis-routed to Power
    assert M["lpg/cng/png/lng supplier"] == "Oil & Gas"     # CGD keeps the Oil & Gas spec's gas-distribution chapter


def test_utilities_framework_is_not_the_power_scale():
    fw = get_framework("Utilities", None, "Water Supply & Management")
    names = {m.name for m in fw.key_metrics()}
    assert fw.sector_name == "Utilities"
    assert "plf" not in names and "td_losses" not in names and "discom_receivables_days" not in names
    assert {"order_book_to_revenue", "receivable_days", "waste_processed_kt"} <= names


def test_utilities_orders_waste_and_bridge(db):
    got = _store(db, "Utilities", {"order_inflow_cr": 3400, "order_backlog_cr": 19400, "revenue_cr": 886.8,
                                    "waste_processed_kt": 850, "collection_efficiency_pct": 92})
    assert got["qtr_util_book_to_bill"] == round(3400 / 886.8, 2)
    assert compute_quarterly_sector_kpis(db, _CO, "Utilities")["available"] is True
    b = inject_ledger_bridge({}, db, _CO, ["waste_processed_kt", "collection_efficiency_pct", "book_to_bill"])["_ledger_metrics"]
    assert b["waste_processed_kt"] == 850.0 and b["collection_efficiency_pct"] == 92.0 and "book_to_bill" in b


def test_city_gas_fields_flow_through_oil_gas_with_shared_growth_key(db):
    got = _store(db, "Oil & Gas", {"cgd_volume_mmscmd": 9.66, "cgd_volume_mmscm": 878.98, "cgd_volume_growth_yoy_pct": 6,
                                    "cng_stations": 707})
    assert got["qtr_oilgas_cgd_volume_mmscmd"] == 9.66 and got["qtr_volume_growth_yoy"] == 6
    keys = {m["metric_key"] for m in compute_quarterly_sector_kpis(db, _CO, "Oil & Gas")["metrics"]}
    assert {"qtr_oilgas_cgd_volume_mmscmd", "qtr_oilgas_cng_stations"} <= keys


def test_gas_transmission_terminal_and_margin_fields(db):
    got = _store(db, "Oil & Gas", {"gas_transmission_mmscmd": 122.36, "lng_throughput_tbtu": 207, "regas_utilization_pct": 58,
                                    "revenue_cr": 38982, "ebitda_cr": 6948, "capex_cr": 6176, "lpg_transmission_tmt": 1077})
    assert got["qtr_oilgas_gas_transmission_mmscmd"] == 122.36 and got["qtr_oilgas_regas_utilization"] == 58
    assert got["qtr_oilgas_lpg_transmission_kt"] == 1077
    assert got["qtr_oilgas_ebitda_minus_capex_margin"] == round((6948 - 6176) / 38982 * 100, 2)


def test_ppac_parsers_read_the_terminal_and_pipeline_tables():
    from app.ingestion.ppac_client import parse_pipelines, parse_terminals
    terminals = ("Capacity utilisation (Apr'26- Aug'2026)\n"
                 "        Dahej         Petronet LNG Ltd (PLL)      22.5       68.21*\n"
                 "        Hazira        Shell Energy India Pvt. Ltd.  6        38.3\n"
                 "        Kochi         Petronet LNG Ltd (PLL)      5          24.26*\n")
    t = parse_terminals(terminals)
    assert t["petronet_capacity_mmtpa"] == 27.5 and round(t["petronet_utilization_pct"], 1) == 60.2   # capacity-weighted
    pipes = ("20. Common Carrier Natural Gas pipeline network as on 31.03.2026\n"
             "Nature of pipeline     GAIL    GSPL    PIL   IOCL\n"
             "Operational   Length   11,184   2,894   1,485   249\n"
             "              Capacity  240.1   74.8    85.0    25.2\n")
    p = parse_pipelines(pipes)
    assert p["as_on"] == "2026-03-31" and p["GAIL"] == (11184.0, 240.1) and p["GSPL"] == (2894.0, 74.8)
    assert parse_terminals("nothing here") is None and parse_pipelines("nothing here") is None
