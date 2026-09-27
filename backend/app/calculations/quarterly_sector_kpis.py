"""Compute-on-read surface for the Quarterly Sector KPI Extraction Engine
(`app/ingestion/quarterly_operating_metrics_ingestion.py`) — a SEPARATE
concern from `app/calculations/quarterly_intelligence/` (which is generic,
Screener-sourced, every-stock financial QoQ/YoY/margin-trend data). This
module surfaces the SECTOR-SPECIFIC physical KPIs (production/sales
volume, capacity utilization, EBITDA/tonne, market share, dealer
inventory) that only exist for the 24 sectors with a configured quarterly
area today (Power/Utilities/Renewable Energy, Telecom, Services, Logistics, Aviation, Infrastructure, Information Technology, Capital Goods/Industrials/Defence/Construction, Automobile, Cement, Metals/Mining, Forest Materials,
Chemicals/Specialty Chemicals, Consumer Durables, Hotels & Restaurants,
Retail, Real Estate, Oil & Gas, FMCG, Healthcare) — `available: false` for every other
sector, not an error.

Per-sector metric-key/label maps mirror exactly what
`quarterly_operating_metrics_ingestion.py` actually stores (see that
module's docstring for the live-validation status behind each field) —
kept here, not duplicated there, since this is a read-side concern.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.quarterly_intelligence.series import quarter_series
from app.infrastructure.database import metric_store

# Human-readable labels for `metric_store` source codes, shown next to every
# value on the dashboard/PDF/HTML export so provenance is never hidden.
SOURCE_LABELS = {
    "NSE_INVESTOR_PRESENTATION": "Investor presentation",
    "NSE_PRESS_RELEASE": "Results press release",
    "NSE_RESULTS_FILING": "Results filing",
    "TRAI_REPORT": "TRAI monthly report",
    "CEA_REPORT": "CEA monthly report (sector benchmark)",
    "PPAC_REPORT": "PPAC monthly snapshot",
    "NSE_COMPANY_DISCLOSURE": "Company disclosure on NSE",
    "NSE_CONCALL": "Earnings call",
    "BSE_EARNINGS_CALL": "Earnings call",
    "MANUAL": "Analyst-verified (filing read by hand)",
    "SCREENER": "Screener.in",
    "CALCULATED": "Calculated",
}

# sector_name -> ordered [(metric_key, label, unit), ...]. Order matters —
# it's the display order the frontend renders in. The shared final keys
# (qtr_volume_growth_yoy, qtr_ebitda_per_tonne, qtr_cost_per_tonne,
# qtr_realisation_per_tonne) intentionally appear across multiple sectors —
# same metric_key, same meaning, just populated from a different sector's
# extraction area; never a collision since a company belongs to one sector.
_SECTOR_METRICS: dict[str, list[tuple[str, str, str]]] = {
    "Automobile": [
        ("qtr_automobile_units_sold", "Units Sold", "units"),
        ("qtr_volume_growth_yoy", "Volume Growth (YoY)", "%"),
        ("qtr_automobile_market_share", "Market Share", "%"),
    ],
    "Cement": [
        ("qtr_cement_sales_mnt", "Sales Volume", "MT"),
        ("qtr_volume_growth_yoy", "Volume Growth (YoY)", "%"),
        ("qtr_realisation_per_tonne", "Realisation / Tonne", "INR"),
        ("qtr_ebitda_per_tonne", "EBITDA / Tonne", "INR"),
        ("qtr_cost_per_tonne", "Cost / Tonne", "INR"),
    ],
    "Metals": [
        ("qtr_metals_production_mnt", "Production Volume", "MT"),
        ("qtr_metals_sales_mnt", "Sales Volume", "MT"),
        ("qtr_volume_growth_yoy", "Volume Growth (YoY)", "%"),
        ("qtr_realisation_per_tonne", "Realisation / Tonne", "INR"),
        ("qtr_ebitda_per_tonne", "EBITDA / Tonne", "INR"),
        ("qtr_cost_per_tonne", "Cost / Tonne", "INR"),
    ],
    "Forest Materials": [
        ("qtr_paper_production_tonnes", "Production Volume", "tonnes"),
        ("qtr_paper_sales_tonnes", "Sales Volume", "tonnes"),
        ("qtr_volume_growth_yoy", "Volume Growth (YoY)", "%"),
        ("qtr_realisation_per_tonne", "Realisation / Tonne", "INR"),
        ("qtr_ebitda_per_tonne", "EBITDA / Tonne", "INR"),
        ("qtr_cost_per_tonne", "Cost / Tonne", "INR"),
    ],
    "Chemicals": [
        ("qtr_volume_growth_yoy", "Primary Segment Volume Growth (YoY)", "%"),
        ("qtr_chemicals_export_revenue_pct", "Export Revenue %", "%"),
    ],
    "Consumer Durables": [
        ("qtr_volume_growth_yoy", "Primary Segment Volume Growth (YoY)", "%"),
        ("qtr_consumer_durables_market_share", "Market Share", "%"),
    ],
    "Hotels & Restaurants": [
        ("qtr_hotels_occupancy", "Occupancy", "%"),
        ("qtr_hotels_arr", "Average Daily Rate", "INR"),
        ("qtr_hotels_revpar", "RevPAR", "INR"),
    ],
    "Retail": [
        ("qtr_retail_store_count", "Store Count", "units"),
        ("qtr_retail_store_count_growth_yoy", "Store Count Growth (YoY)", "%"),
        ("qtr_retail_sssg", "Same-Store Sales Growth", "%"),
        ("qtr_retail_revenue_per_sqft", "Revenue / Sq. Ft. (Quarterly)", "INR"),
    ],
    "Real Estate": [
        ("qtr_realty_pre_sales_value", "Booking Value / Pre-Sales", "INR Cr"),
        ("qtr_realty_collections_growth_yoy", "Collections Growth (YoY)", "%"),
        ("qtr_realty_collections", "Customer Collections", "INR Cr"),
    ],
    "Oil & Gas": [
        ("qtr_oilgas_grm", "Gross Refining Margin", "USD/bbl"),
        ("qtr_oilgas_cgd_volume_mmscmd", "Gas Sales Volume", "MMSCMD"),
        ("qtr_oilgas_cgd_volume_mmscm", "Gas Sales Volume (quarter)", "MMSCM"),
        ("qtr_volume_growth_yoy", "Gas Volume Growth (YoY)", "%"),
        ("qtr_oilgas_gas_transmission_mmscmd", "Gas Transmission Volume", "MMSCMD"),
        ("qtr_oilgas_gas_marketing_mmscmd", "Gas Marketing Volume", "MMSCMD"),
        ("qtr_oilgas_lpg_transmission_kt", "LPG Transmission", "kt"),
        ("qtr_oilgas_petchem_production_kt", "Petrochemical Production", "kt"),
        ("qtr_oilgas_lhc_production_kt", "Liquid Hydrocarbon Production", "kt"),
        ("qtr_oilgas_lng_throughput_tbtu", "LNG Throughput", "TBtu"),
        ("qtr_oilgas_regas_utilization", "Regas Terminal Utilisation", "%"),
        ("qtr_oilgas_regas_capacity_mmtpa", "Regas Capacity", "MMTPA"),
        ("qtr_oilgas_pipeline_network_km", "Pipeline Network (operational)", "km"),
        ("qtr_oilgas_pipeline_authorised_mmscmd", "Pipeline Authorised Capacity", "MMSCMD"),
        ("qtr_oilgas_capex", "Capex", "INR Cr"),
        ("qtr_oilgas_ebitda_minus_capex_margin", "EBITDA - Capex Margin", "%"),
        ("qtr_oilgas_cng_stations", "CNG Stations", "units"),
        ("qtr_oilgas_png_connections_lakh", "Domestic PNG Connections", "lakh"),
        ("qtr_oilgas_cgd_margin_per_scm", "Gross Margin / SCM", "INR/SCM"),
    ],
    "Healthcare": [
        ("qtr_healthcare_bed_occupancy", "Bed Occupancy", "%"),
        ("qtr_healthcare_arpob", "ARPOB (per occupied bed / day)", "INR"),
        ("qtr_healthcare_alos", "Average Length of Stay", "days"),
        ("qtr_healthcare_arpp", "ARPP (per in-patient)", "INR"),
        ("qtr_healthcare_operational_beds", "Operational Beds", "units"),
        ("qtr_healthcare_us_revenue_pct", "US Revenue Share", "%"),
    ],
    "Utilities": [
        ("qtr_util_order_inflow", "Order Inflow", "INR Cr"),
        ("qtr_util_order_inflow_growth_yoy", "Order Inflow Growth (YoY)", "%"),
        ("qtr_util_order_backlog", "Order Backlog", "INR Cr"),
        ("qtr_util_order_backlog_growth_yoy", "Order Backlog Growth (YoY)", "%"),
        ("qtr_util_book_to_bill", "Book-to-Bill", "x"),
        ("qtr_util_order_backlog_to_ttm_revenue", "Order Backlog / TTM Revenue", "x"),
        ("qtr_util_waste_processed_kt", "Waste Processed (quarter)", "kt"),
        ("qtr_util_waste_collected_kt", "Waste Collected (quarter)", "kt"),
        ("qtr_util_treatment_capacity_mld", "Treatment Capacity", "MLD"),
        ("qtr_util_customers_mn", "Customers / Connections", "Mn"),
        ("qtr_util_collection_efficiency", "Collection Efficiency", "%"),
        ("qtr_util_network_km", "Network Length", "km"),
    ],
    "Power": [
        ("qtr_pow_installed_capacity_mw", "Operational Capacity", "MW"),
        ("qtr_pow_capacity_growth_yoy", "Capacity Growth (YoY)", "%"),
        ("qtr_pow_thermal_capacity_mw", "Thermal Capacity", "MW"),
        ("qtr_pow_renewable_capacity_mw", "Renewable Capacity", "MW"),
        ("qtr_pow_capacity_pipeline_mw", "Under Construction / Pipeline", "MW"),
        ("qtr_pow_generation_mu", "Generation / Sales", "MU"),
        ("qtr_pow_plf", "Thermal PLF", "%"),
        ("qtr_pow_thermal_plf_sector_benchmark", "Thermal PLF — CEA sector benchmark (quarter-end month)", "%"),
        ("qtr_pow_availability", "Plant Availability", "%"),
        ("qtr_pow_cuf", "Renewable CUF", "%"),
        ("qtr_pow_ppa_contracted_pct", "PPA / Regulated Share", "%"),
        ("qtr_pow_avg_tariff", "Average Tariff / Realisation", "INR/kWh"),
        ("qtr_pow_transmission_availability", "Transmission Availability", "%"),
        ("qtr_pow_network_ckm", "Network Length", "ckm"),
        ("qtr_pow_transformation_mva", "Transformation Capacity", "MVA"),
        ("qtr_pow_td_loss", "Distribution / T&D Loss", "%"),
        ("qtr_pow_atc_loss", "AT&C Loss", "%"),
        ("qtr_pow_collection_efficiency", "Collection Efficiency", "%"),
        ("qtr_pow_trading_volume_bu", "Volume Traded", "Bn units"),
        ("qtr_pow_capex", "Capex", "INR Cr"),
        ("qtr_pow_ebitda_margin", "EBITDA Margin (quarter)", "%"),
        ("qtr_pow_ebitda_minus_capex_margin", "EBITDA - Capex Margin", "%"),
    ],
    "Telecom": [
        ("qtr_tel_arpu", "ARPU (per month)", "INR"),
        ("qtr_tel_subscribers_mn", "Mobile Customers", "Mn"),
        ("qtr_tel_subscriber_growth_yoy", "Customer Growth (YoY)", "%"),
        ("qtr_tel_net_adds_mn", "Net Additions", "Mn"),
        ("qtr_tel_market_share_mobile_pct", "Mobile Subscriber Market Share (TRAI)", "%"),
        ("qtr_tel_wireless_broadband_share_pct", "Wireless Broadband Share (TRAI)", "%"),
        ("qtr_tel_churn", "Monthly Churn", "%"),
        ("qtr_tel_data_usage_gb", "Data Usage / Customer / Month", "GB"),
        ("qtr_tel_subscribers_4g5g_mn", "4G/5G Data Customers", "Mn"),
        ("qtr_tel_subscribers_4g5g_pct", "4G/5G Share of Base", "%"),
        ("qtr_tel_broadband_homes_mn", "Home Broadband Customers", "Mn"),
        ("qtr_tel_revenue_per_gb", "Mobile Revenue / GB", "INR"),
        ("qtr_tel_data_revenue_pct", "Data Services Share of Revenue", "%"),
        ("qtr_tel_capex", "Capex", "INR Cr"),
        ("qtr_tel_spectrum_liability", "Deferred Spectrum Liability", "INR Cr"),
        ("qtr_tel_agr_liability", "AGR Liability", "INR Cr"),
        ("qtr_tel_group_customers_mn", "Group Customers (all countries)", "Mn"),
        ("qtr_tel_africa_subscribers_mn", "Africa Customers", "Mn"),
        ("qtr_tel_africa_subscriber_growth_yoy", "Africa Customer Growth (YoY)", "%"),
        ("qtr_tel_africa_arpu_usd", "Africa ARPU (per month)", "USD"),
        ("qtr_tel_africa_churn", "Africa Monthly Churn", "%"),
        ("qtr_tel_africa_data_usage_gb", "Africa Data Usage / Customer / Month", "GB"),
        ("qtr_tel_africa_data_customers_mn", "Africa Data Customers", "Mn"),
        ("qtr_tel_africa_towers", "Africa Towers", "units"),
        ("qtr_tel_africa_mobile_money_active_mn", "Africa Mobile-Money Active Customers", "Mn"),
        ("qtr_tel_towers", "Towers", "units"),
        ("qtr_tel_colocations", "Co-locations", "units"),
        ("qtr_tel_tenancy", "Tenancy Ratio", "x"),
        ("qtr_tel_order_inflow", "Order Inflow", "INR Cr"),
        ("qtr_tel_order_backlog", "Order Backlog", "INR Cr"),
        ("qtr_tel_book_to_bill", "Book-to-Bill", "x"),
        ("qtr_tel_ebitda_minus_capex_margin", "EBITDA - Capex Margin", "%"),
    ],
    "Services": [
        ("qtr_svc_headcount", "Headcount", "units"),
        ("qtr_svc_attrition", "Attrition (LTM)", "%"),
        ("qtr_svc_order_inflow", "Order Inflow", "INR Cr"),
        ("qtr_svc_order_backlog", "Order Backlog", "INR Cr"),
        ("qtr_svc_book_to_bill", "Book-to-Bill", "x"),
        ("qtr_svc_capacity_utilization", "Utilisation", "%"),
        ("qtr_svc_employee_cost_pct", "Employee Cost % of Revenue", "%"),
    ],
    "Logistics": [
        ("qtr_volume_growth_yoy", "Volume Growth (YoY)", "%"),
        ("qtr_svc_shipments_mn", "Shipments", "Mn"),
        ("qtr_svc_tonnage_kt", "Tonnage", "kt"),
        ("qtr_svc_realisation_per_tonne", "Revenue / Tonne", "INR"),
        ("qtr_svc_warehouse_area_mn_sqft", "Warehousing Space", "Mn sq ft"),
        ("qtr_svc_fleet_vessels", "Owned Vessels", "units"),
        ("qtr_svc_fleet_dwt_mn", "Owned Fleet", "Mn dwt"),
        ("qtr_svc_tce_crude", "Crude Carrier Earnings", "USD/day"),
        ("qtr_svc_tce_product", "Product Carrier Earnings", "USD/day"),
        ("qtr_svc_tce_dry_bulk", "Dry Bulk Earnings", "USD/day"),
        ("qtr_svc_container_teu_mn", "Container Volume (TEU)", "Mn"),
        ("qtr_svc_tce_usd_per_day", "Time-Charter Equivalent", "USD/day"),
        ("qtr_svc_capacity_utilization", "Fleet / Asset Utilisation", "%"),
        ("qtr_svc_headcount", "Headcount", "units"),
    ],
    "Aviation": [
        ("qtr_svc_passengers_mn", "Passengers", "Mn"),
        ("qtr_volume_growth_yoy", "Traffic Growth (YoY)", "%"),
        ("qtr_svc_load_factor", "Passenger Load Factor", "%"),
        ("qtr_svc_ask_bn", "Available Seat-Km (ASK)", "Bn"),
        ("qtr_svc_yield", "Yield (per RPK)", "INR"),
        ("qtr_svc_cask", "CASK", "INR"),
        ("qtr_svc_cask_ex_fuel", "CASK ex-Fuel", "INR"),
        ("qtr_svc_aero_yield_per_pax", "Aero Yield / Passenger", "INR"),
        ("qtr_svc_nonaero_income_per_pax", "Non-Aero Income / Passenger", "INR"),
    ],
    "Infrastructure": [
        ("qtr_svc_toll_revenue", "Toll Revenue (gross, group)", "INR Cr"),
        ("qtr_svc_toll_growth_yoy", "Toll Revenue Growth (YoY)", "%"),
        ("qtr_svc_aero_yield_per_pax", "Aero Yield / Passenger", "INR"),
        ("qtr_svc_nonaero_income_per_pax", "Non-Aero Income / Passenger", "INR"),
        ("qtr_svc_cargo_volume_mmt", "Cargo Volume", "MT"),
        ("qtr_svc_container_teu_mn", "Container Volume (TEU)", "Mn"),
        ("qtr_svc_passengers_mn", "Passengers Handled", "Mn"),
        ("qtr_volume_growth_yoy", "Volume Growth (YoY)", "%"),
        ("qtr_svc_capacity_utilization", "Capacity Utilisation", "%"),
    ],
    "Information Technology": [
        ("qtr_it_cc_growth_yoy", "Constant-Currency Growth (YoY)", "%"),
        ("qtr_it_cc_growth_qoq", "Constant-Currency Growth (QoQ)", "%"),
        ("qtr_it_revenue_usd_mn", "Revenue (USD)", "USD Mn"),
        ("qtr_it_headcount", "Headcount", "units"),
        ("qtr_it_revenue_per_employee", "Revenue / Employee (annualised)", "USD k"),
        ("qtr_it_attrition", "Attrition (LTM)", "%"),
        ("qtr_it_utilization", "Billable Utilisation", "%"),
        ("qtr_it_deal_tcv", "Deal Wins (TCV)", "USD Bn"),
        ("qtr_it_large_deal_tcv", "Large-Deal TCV", "USD Bn"),
        ("qtr_it_top5_client_pct", "Top-5 Client Revenue %", "%"),
        ("qtr_it_top10_client_pct", "Top-10 Client Revenue %", "%"),
        ("qtr_it_north_america_pct", "North America Share", "%"),
        ("qtr_it_europe_pct", "Europe Share", "%"),
        ("qtr_it_bfsi_pct", "BFSI Share", "%"),
        ("qtr_it_offshore_effort_pct", "Offshore Effort", "%"),
        ("qtr_it_million_dollar_clients", "US$1M+ Clients", "units"),
    ],
    "Capital Goods": [
        ("qtr_capgoods_order_inflow", "Order Inflow", "INR Cr"),
        ("qtr_capgoods_order_inflow_growth_yoy", "Order Inflow Growth (YoY)", "%"),
        ("qtr_capgoods_order_backlog", "Order Backlog", "INR Cr"),
        ("qtr_capgoods_order_backlog_growth_yoy", "Order Backlog Growth (YoY)", "%"),
        ("qtr_capgoods_book_to_bill", "Book-to-Bill", "x"),
        ("qtr_capgoods_order_backlog_to_ttm_revenue", "Order Backlog / TTM Revenue", "x"),
        ("qtr_capgoods_export_order_pct", "Export Share of Order Intake", "%"),
        ("qtr_capgoods_aftermarket_order_pct", "Aftermarket Share of Order Intake", "%"),
        ("qtr_capgoods_international_backlog_pct", "International Share of Order Backlog", "%"),
        ("qtr_capgoods_capacity_utilization", "Capacity Utilisation", "%"),
    ],
    "Fast Moving Consumer Goods": [
        ("qtr_volume_growth_yoy", "Underlying Volume Growth (YoY)", "%"),
        ("qtr_fmcg_underlying_sales_growth", "Underlying Sales Growth (YoY)", "%"),
        ("qtr_fmcg_price_mix_growth", "Price / Mix Growth (derived)", "%"),
    ],
}
_SECTOR_METRICS["Renewable Energy"] = _SECTOR_METRICS["Power"]
_SECTOR_METRICS["Industrials"] = _SECTOR_METRICS["Capital Goods"]
_SECTOR_METRICS["Defence"] = _SECTOR_METRICS["Capital Goods"]
_SECTOR_METRICS["Construction"] = _SECTOR_METRICS["Capital Goods"]
_SECTOR_METRICS["Mining"] = _SECTOR_METRICS["Metals"]
_SECTOR_METRICS["Specialty Chemicals"] = _SECTOR_METRICS["Chemicals"]


# Industry/regulator series (TRAI, CEA, toll disclosures) are not tied to the company's statement basis;
# they must not decide whether the card shows CONSOLIDATED or STANDALONE company figures.
_STATEMENT_AGNOSTIC = {
    "qtr_pow_thermal_plf_sector_benchmark", "qtr_tel_market_share_mobile_pct", "qtr_tel_wireless_broadband_share_pct",
    "qtr_oilgas_pipeline_network_km", "qtr_oilgas_pipeline_authorised_mmscmd",
}


def compute_quarterly_sector_kpis(
    db: Session, company_id: str, sector_name: str | None, n_quarters: int = 8,
) -> dict:
    """Returns `{"available": False}` for a sector with no configured area
    (most sectors — not an error) or a company with no data extracted yet.
    Otherwise `{"available": True, "sector_name", "statement_type",
    "single_statement_source", "latest_quarter", "metrics": [{metric_key,
    label, unit, series: {period: value}, latest_value}, ...]}` — only
    metrics with at least one real value are included, so the frontend
    never has to render an all-null card. Never raises."""
    metric_defs = _SECTOR_METRICS.get(sector_name or "")
    if not metric_defs:
        return {"available": False, "sector_name": sector_name}

    statement_type = "CONSOLIDATED"
    single_statement_source = False
    company_defs = [d for d in metric_defs if d[0] not in _STATEMENT_AGNOSTIC]
    series_by_key = {key: quarter_series(db, company_id, key, statement_type) for key, _, _ in company_defs}
    if not any(series_by_key.values()):
        statement_type = "STANDALONE"
        single_statement_source = True
        series_by_key = {key: quarter_series(db, company_id, key, statement_type) for key, _, _ in company_defs}
    agnostic_type: dict[str, str] = {}
    for key, _, _ in metric_defs:
        if key in _STATEMENT_AGNOSTIC:
            for st in ("CONSOLIDATED", "STANDALONE"):
                series = quarter_series(db, company_id, key, st)
                if series:
                    series_by_key[key], agnostic_type[key] = series, st
                    break

    metrics = []
    latest_quarter = None
    for key, label, unit in metric_defs:
        series = series_by_key.get(key, {})
        if not series:
            continue
        trimmed = {p: series[p] for p in sorted(series.keys())[-n_quarters:]}
        latest_period = max(trimmed.keys())
        if latest_quarter is None or latest_period > latest_quarter:
            latest_quarter = latest_period
        winner, _ = metric_store.get_authoritative_value(db, company_id, key, latest_period,
                                                         statement_type=agnostic_type.get(key, statement_type))
        metrics.append({
            "metric_key": key, "label": label, "unit": unit,
            "series": trimmed, "latest_value": trimmed[latest_period],
            "latest_period": latest_period,
            "source": winner.source if winner else None,
            "source_label": SOURCE_LABELS.get(winner.source, winner.source) if winner else None,
            "confidence": winner.confidence if winner else None,
            "data_type": winner.reported_or_calculated if winner else None,
            "source_document": winner.source_document if winner else None,
            "source_url": winner.source_url if winner else None,
        })

    if not metrics:
        return {"available": False, "sector_name": sector_name}

    return {
        "available": True,
        "sector_name": sector_name,
        "statement_type": statement_type,
        "single_statement_source": single_statement_source,
        "latest_quarter": latest_quarter,
        "metrics": metrics,
    }
