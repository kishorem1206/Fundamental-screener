"""
Other Utilities framework (Utilities -> Utilities spec): water supply & treatment,
waste management, municipal / other regulated infrastructure services.

Integrated power utilities moved to the Power framework (the Utilities spec excludes power
generation/T&D; they were previously inheriting Power's PLF/T&D scale here and now use it
directly). City-gas distribution stays under Oil & Gas (its own spec has a gas-distribution
chapter); the gas-distribution KPIs are extracted there.

Quarterly operating metrics (`qtr_util_*`: order inflow/backlog and book-to-bill for water EPC/O&M,
waste processed/collected, treatment capacity, customers, collection efficiency, network length)
come from the Quarterly Sector KPI Extraction Engine. Only rate/level metrics feed scoring.
Traps: contracted vs pipeline capacity, tonnes per quarter vs per day vs per year, MLD (million litres per day)
vs MGD, order book that includes long-tenor O&M, EPC vs BOOT project revenue.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class UtilitiesSector(SectorFramework):
    sector_name = "Utilities"
    sector_aliases = ["Utilities", "Water Utilities", "Gas Utilities", "Multi-Utilities", "Waste Management",
                      "Water Supply & Management", "Other Utilities"]

    SECTOR_WEIGHTS = {
        "growth": 0.20,
        "profitability": 0.21,
        "cash_flow": 0.23,
        "balance_sheet": 0.22,
        "efficiency": 0.10,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric("revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "medium", "higher_is_better", "%",
                         "Growth from contracts, connections and tariff — should come with volume (spec bad-growth pattern 3)",
                         thresholds=[(0, 15), (5, 30), (9, 48), (13, 65), (18, 80), (23, 92), (30, 100)]),
            SectorMetric("order_book_to_revenue", "Order Book / Revenue", 0.10, "high", "higher_is_better", "x",
                         "Contracted order book cover for water/waste EPC and O&M businesses",
                         thresholds=[(0.5, 10), (1.0, 30), (1.5, 50), (2.0, 66), (2.7, 80), (3.5, 92), (4.5, 100)],
                         available_from_yfinance=False,
                         na_message="Order book from quarterly disclosures (water/waste contractors only)"),
            SectorMetric("book_to_bill", "Book-to-Bill (latest quarter)", 0.04, "medium", "higher_is_better", "x",
                         "Order intake / revenue — lumpy; read with backlog cover",
                         thresholds=[(0.5, 5), (0.8, 25), (1.0, 48), (1.3, 68), (1.8, 85), (2.5, 100)],
                         available_from_yfinance=False, na_message="Order intake and revenue from results / decks"),
            SectorMetric("ebitda_margin", "EBITDA Margin", 0.14, "high", "higher_is_better", "%",
                         "Regulated/contracted utilities earn 15-40%; EPC-heavy water names 10-16%",
                         thresholds=[(4, 8), (8, 28), (12, 46), (16, 62), (22, 78), (30, 90), (40, 100)]),
            SectorMetric("roce", "ROCE", 0.12, "high", "higher_is_better", "%",
                         "Return on capital — infrastructure utilities 10-16%, asset-light service names higher",
                         thresholds=[(0, 5), (7, 22), (11, 45), (15, 65), (20, 80), (26, 92), (34, 100)]),
            SectorMetric("receivable_days", "Receivable Days", 0.10, "high", "lower_is_better", "days",
                         "Municipal/government counterparties pay slowly — receivable build-up is the key risk (spec 9)",
                         thresholds=[(30, 100), (60, 82), (90, 62), (130, 42), (180, 22), (250, 5)]),
            SectorMetric("debt_to_equity", "Debt/Equity", 0.10, "high", "lower_is_better", "x",
                         "Leverage — capital-intensive utilities tolerate more, contractors should stay low",
                         thresholds=[(0, 100), (0.3, 88), (0.6, 72), (1.0, 55), (1.6, 32), (2.4, 12), (3.2, 0)]),
            SectorMetric("fcf_to_pat", "FCF / PAT", 0.10, "high", "higher_is_better", "%",
                         "Cash conversion — volume/revenue growth without cash is a spec red flag",
                         thresholds=[(0, 10), (25, 30), (45, 50), (65, 68), (80, 82), (95, 93), (110, 100)]),
            SectorMetric("collection_efficiency_pct", "Collection Efficiency", 0.0, "low", "neutral", "%",
                         "Share of billed revenue collected — display only",
                         available_from_yfinance=False, na_message="Stated by some utilities in results releases"),
            SectorMetric("waste_processed_kt", "Waste Processed (thousand tonnes, quarter)", 0.0, "low", "neutral", "kt",
                         "Waste volume processed in the quarter — display only; read against contracted capacity",
                         available_from_yfinance=False, na_message="Stated by waste-management operators"),
            SectorMetric("treatment_capacity_mld", "Treatment Capacity (MLD)", 0.0, "low", "neutral", "MLD",
                         "Water/wastewater treatment capacity in million litres per day — display only",
                         available_from_yfinance=False, na_message="Stated by water-infrastructure companies"),
            SectorMetric("pe_ratio", "P/E", 0.06, "medium", "neutral", "x",
                         "Utilities P/E — regulated compounders 18-30x, contractors 20-40x on growth",
                         thresholds=[(0, 45), (10, 65), (18, 82), (28, 78), (38, 60), (55, 38), (80, 15)]),
            SectorMetric("ev_to_ebitda", "EV/EBITDA", 0.04, "medium", "neutral", "x",
                         "Enterprise multiple", thresholds=[(0, 55), (6, 78), (10, 90), (16, 80), (22, 62), (30, 40), (42, 18)]),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(condition="receivable_days > 180", severity="HIGH", title="Stretched Receivables",
                          description="Receivables above 180 days — municipal/government payment delay risk."),
            SectorRedFlag(condition="fcf_to_pat < 20", severity="MEDIUM", title="Weak Cash Conversion",
                          description="FCF below 20% of PAT — growth is not turning into cash."),
            SectorRedFlag(condition="debt_to_equity > 2", severity="HIGH", title="High Leverage",
                          description="D/E above 2x for a utility without regulated returns."),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        c = {"receivable_days > 180": lambda m: (m.get("receivable_days") or 0) > 180,
             "fcf_to_pat < 20": lambda m: m.get("fcf_to_pat") is not None and m["fcf_to_pat"] < 20,
             "debt_to_equity > 2": lambda m: (m.get("debt_to_equity") or 0) > 2}
        fn = c.get(rule.condition)
        return bool(fn and fn(metrics))
