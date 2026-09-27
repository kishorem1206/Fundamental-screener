"""Generic provenance-ledger bridge — 2026-09-12. Injects every available
ledger value for a sector's declared "not from yfinance" metrics into
financial_data["_ledger_metrics"], so SectorFramework.extract_sector_metrics()
(app/sectors/base.py) surfaces them automatically without every sector
needing its own banking_data_bridge.py-style override.

Built while wiring the earnings-call transcript source (attrition_rate,
utilization_rate, deal_wins_tcv for IT Services) — without this, those
values would land in fa_metric_data_points but never actually appear in a
sector_analysis result, the same class of gap Stage 8 found and fixed for
NBFCs (NBFCSector._compute_special_metric). Rather than write another
one-off per-sector override, this generalizes the mechanism once.

Confidence-gated the same way banking_data_bridge.py already is: a
LOW-confidence row stays visible via the provenance API but never silently
becomes an authoritative displayed/scored value. banking_data_bridge.py's
own "_banking_authoritative_metrics" mechanism is untouched — this is
additive, not a replacement, to avoid touching working, tested code.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store

LEDGER_BRIDGE_KEY = "_ledger_metrics"
_SCORABLE_CONFIDENCE = {"HIGH", "MEDIUM"}


# Sector metric -> quarterly ledger key (Quarterly Sector KPI Extraction Engine)
# used as a FALLBACK when no annual/other value exists for the sector metric —
# so the operating KPIs read from NSE filings actually reach the sector score,
# not just the Quarterly tab. Only LEVEL/RATE metrics whose quarterly figure is
# comparable to the metric's scoring thresholds belong here; absolute FLOW
# metrics (e.g. real-estate pre_sales_value: a quarter of bookings vs annual
# thresholds) deliberately do not.
QUARTERLY_FALLBACKS: dict[str, str | tuple[str, ...]] = {
    # hospitals / pharma
    "bed_occupancy_pct": "qtr_healthcare_bed_occupancy", "arpob": "qtr_healthcare_arpob",
    "alos_days": "qtr_healthcare_alos", "arpp": "qtr_healthcare_arpp",
    "operational_beds": "qtr_healthcare_operational_beds", "us_revenue_pct": "qtr_healthcare_us_revenue_pct",
    # hotels
    "occupancy_rate": "qtr_hotels_occupancy", "arr": "qtr_hotels_arr", "revpar": "qtr_hotels_revpar",
    # oil & gas
    "grm": "qtr_oilgas_grm",
    # FMCG / consumer durables / automobile / chemicals
    "volume_growth_yoy": "qtr_volume_growth_yoy", "price_mix_growth": "qtr_fmcg_price_mix_growth",
    "premiumization_pct": "premiumization_pct",
    # capital goods / defence (order-book rates and ratios; absolute INR Cr flows excluded)
    "order_inflow_growth": ("qtr_capgoods_order_inflow_growth_yoy", "qtr_util_order_inflow_growth_yoy"),
    "order_book_to_revenue": ("qtr_capgoods_order_backlog_to_ttm_revenue", "qtr_util_order_backlog_to_ttm_revenue"),
    "book_to_bill": ("qtr_capgoods_book_to_bill", "qtr_util_book_to_bill"), "export_order_pct": "qtr_capgoods_export_order_pct",
    "international_backlog_pct": "qtr_capgoods_international_backlog_pct",
    "aftermarket_order_pct": "qtr_capgoods_aftermarket_order_pct",
    "capacity_utilization": ("qtr_capgoods_capacity_utilization", "qtr_svc_capacity_utilization"),
    # IT services (rates/levels; an annual/transcript value on file wins)
    "cc_revenue_growth": "qtr_it_cc_growth_yoy", "attrition_rate": ("qtr_it_attrition", "qtr_svc_attrition"),
    "utilization_rate": "qtr_it_utilization", "deal_wins_tcv": "qtr_it_deal_tcv",
    "revenue_per_employee": "qtr_it_revenue_per_employee", "client_concentration_top10": "qtr_it_top10_client_pct",
    "client_concentration_top5": "qtr_it_top5_client_pct", "offshore_effort_pct": "qtr_it_offshore_effort_pct",
    "north_america_revenue_pct": "qtr_it_north_america_pct", "bfsi_revenue_pct": "qtr_it_bfsi_pct",
    "million_dollar_clients": "qtr_it_million_dollar_clients", "large_deal_tcv": "qtr_it_large_deal_tcv",
    # services / logistics / aviation / infrastructure
    "headcount": "qtr_svc_headcount", "plf_load_factor": "qtr_svc_load_factor", "yield_per_pkm": "qtr_svc_yield",
    "cask": "qtr_svc_cask", "asset_utilization": "qtr_svc_capacity_utilization",
    # telecom (an annual value on file wins)
    "arpu": "qtr_tel_arpu", "subscriber_growth_yoy": "qtr_tel_subscriber_growth_yoy",
    "ebitda_minus_capex_margin": "qtr_tel_ebitda_minus_capex_margin", "churn_pct": "qtr_tel_churn",
    "data_usage_gb_per_sub": "qtr_tel_data_usage_gb", "tenancy_ratio": "qtr_tel_tenancy", "data_revenue_pct": "qtr_tel_data_revenue_pct",
    "market_share_mobile_pct": "qtr_tel_market_share_mobile_pct",
    "wireless_broadband_share_pct": "qtr_tel_wireless_broadband_share_pct",
    # power (rates/levels; thermal PLF only feeds `plf` so solar/wind are never scored on a thermal scale)
    "plf": "qtr_pow_plf", "td_losses": "qtr_pow_td_loss", "regulated_capacity_pct": "qtr_pow_ppa_contracted_pct",
    "availability_pct": "qtr_pow_availability", "cuf_pct": "qtr_pow_cuf",
    "transmission_availability_pct": "qtr_pow_transmission_availability", "atc_loss_pct": "qtr_pow_atc_loss",
    "collection_efficiency_pct": ("qtr_pow_collection_efficiency", "qtr_util_collection_efficiency"),
    "waste_processed_kt": "qtr_util_waste_processed_kt", "treatment_capacity_mld": "qtr_util_treatment_capacity_mld", "capacity_growth_yoy": "qtr_pow_capacity_growth_yoy",
    # retail / real estate (rates only)
    "store_count_growth": "qtr_retail_store_count_growth_yoy", "sssg": "qtr_retail_sssg",
    "collections_growth_yoy": "qtr_realty_collections_growth_yoy",
}
# market_share is per-sector (one metric name, sector-specific quarterly keys)
_MARKET_SHARE_KEYS = ("qtr_consumer_durables_market_share", "qtr_automobile_market_share")


def _quarterly_value(db: Session, company_id: str, sector_metric: str):
    mapped = QUARTERLY_FALLBACKS.get(sector_metric)
    keys = ([mapped] if isinstance(mapped, str) else list(mapped)) if mapped else (
        list(_MARKET_SHARE_KEYS) if sector_metric == "market_share" else [])
    for key in keys:
        for statement_type in ("CONSOLIDATED", "STANDALONE"):
            row = metric_store.get_latest_period_value(db, company_id, key, statement_type=statement_type)
            if row is not None:
                return row
    return None


def inject_ledger_bridge(financial_data: dict, db: Session, company_id: str, metric_ids: list[str]) -> dict:
    """Populate financial_data["_ledger_metrics"] with the authoritative
    ledger value for every metric_id in `metric_ids` that has one on file
    (skips anything missing or LOW-confidence — stays a real N/A, not a
    guess). Merges into any existing dict rather than overwriting."""
    values = {}
    for metric_id in metric_ids:
        row = metric_store.get_latest_period_value(db, company_id, metric_id)
        if row is None:
            row = _quarterly_value(db, company_id, metric_id)
        if row is not None and row.confidence in _SCORABLE_CONFIDENCE:
            values[metric_id] = float(row.value)
    existing = financial_data.get(LEDGER_BRIDGE_KEY, {})
    existing.update(values)
    financial_data[LEDGER_BRIDGE_KEY] = existing
    return financial_data
