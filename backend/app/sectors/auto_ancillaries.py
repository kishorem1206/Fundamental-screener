"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Auto Ancillaries sector framework.
Component suppliers, tier-1/tier-2 vendors, auto parts manufacturers.
Distinct from AutomobileSector (OEMs) — different margin profiles, customer concentration risk.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag
from app.sectors.automobile import AutomobileSector


class AutoAncillariesSector(AutomobileSector):
    sector_name = "Auto Ancillaries"
    sector_aliases = [
        "Auto Ancillaries", "Auto Components", "Auto Parts",
        "Automotive Components", "Tyres",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.22,
        "cash_flow": 0.17,
        "balance_sheet": 0.15,
        "efficiency": 0.17,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — auto ancillaries track OEM volumes with 1-2 quarter lag",
                thresholds=[(0, 15), (3, 30), (6, 48), (10, 65), (14, 80), (18, 92), (22, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Earnings growth — supplier pricing power determines margin leverage",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
            ),
            SectorMetric(
                "customer_concentration_top3", "Top-3 Customer Revenue %", 0.10, "high",
                "lower_is_better", "%",
                "Revenue from top 3 OEM customers — high concentration = demand and pricing vulnerability",
                thresholds=[(15, 100), (25, 85), (35, 68), (50, 50), (65, 30), (80, 12), (95, 0)],
                available_from_yfinance=False,
                na_message="Customer concentration requires segment data from annual report",
            ),
            SectorMetric(
                "ev_ready_revenue_pct", "EV-Compatible Revenue %", 0.10, "high",
                "higher_is_better", "%",
                "Products compatible with EVs as % of revenue — key EV transition risk indicator",
                thresholds=[(5, 15), (15, 35), (25, 55), (40, 72), (55, 84), (70, 94), (85, 100)],
                available_from_yfinance=False,
                na_message="EV content analysis requires company-specific product mix data",
            ),
            SectorMetric(
                "export_revenue_pct", "Exports / Revenue", 0.08, "medium",
                "higher_is_better", "%",
                "Export diversification — reduces dependence on single OEM / domestic cycle. Sourced "
                "from the universal revenue_geography annual-report area (built for Chemicals, reused "
                "as-is here). Renamed from `exports_to_revenue` (2026-09-20) to match that area's "
                "computed metric_key exactly.",
                thresholds=[(0, 20), (5, 38), (12, 55), (20, 70), (30, 83), (40, 100)],
                available_from_yfinance=False,
                na_message="Revenue geography split requires this company's annual report to have "
                           "been ingested",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "Ancillary EBITDA typically 10-16%; RM pass-through determines compression risk",
                thresholds=[(0, 5), (5, 22), (8, 42), (10, 60), (12, 75), (15, 87), (20, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Capital efficiency — ancillaries should earn 15-25%+ ROCE",
                thresholds=[(0, 5), (5, 22), (10, 45), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "high",
                "lower_is_better", "x",
                "Leverage — ancillaries are capital intensive; above 1x warrants watch",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (0.8, 60), (1.2, 40), (1.8, 18), (2.5, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — ancillaries face capex and RM working capital demands",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "inventory_days", "Inventory Days", 0.08, "medium",
                "lower_is_better", "days",
                "RM and WIP inventory — just-in-time supply requires tight inventory control",
                thresholds=[(10, 100), (20, 88), (30, 75), (42, 60), (55, 42), (70, 22), (100, 0)],
            ),
            SectorMetric(
                "asset_turnover", "Asset Turnover", 0.08, "medium",
                "higher_is_better", "x",
                "Revenue / assets — ancillaries should maintain 1.0-1.5x asset turns",
                thresholds=[(0.3, 10), (0.6, 30), (0.8, 50), (1.0, 65), (1.2, 78), (1.5, 90), (2.0, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "medium",
                "neutral", "x",
                "Auto ancillaries trade 12-20x; premium for EV-content-rich suppliers",
                thresholds=[(0, 50), (8, 75), (14, 88), (20, 78), (28, 60), (38, 38), (55, 15)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "medium",
                "neutral", "x",
                "Enterprise multiple — 8-14x typical for auto suppliers",
                thresholds=[(0, 60), (5, 80), (8, 90), (12, 80), (16, 62), (22, 40), (30, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 8% for an auto ancillary means RM cost or customer pricing is severely squeezing margins.",
            ),
            SectorRedFlag(
                condition="customer_concentration_top3 > 70",
                severity="HIGH",
                title="Very High Customer Concentration",
                description="Over 70% from top 3 OEM customers makes the ancillary highly vulnerable to a single customer's volume decisions.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="High Leverage",
                description="D/E above 1.5x in auto ancillaries amplifies downturn risk given OEM volume cyclicality.",
            ),
            SectorRedFlag(
                condition="ev_ready_revenue_pct < 20",
                severity="MEDIUM",
                title="Low EV-Compatible Revenue",
                description="Less than 20% of revenue is EV-compatible — ICE-heavy ancillaries face structural volume risk over 3-5 years.",
            ),
            SectorRedFlag(
                condition="roce < 12",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 12% for an auto supplier indicates poor asset utilization or margin compression.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 3",
                severity="HIGH",
                title="Stagnant Growth",
                description="Revenue CAGR below 3% suggests market share losses or OEM volume weakness.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "customer_concentration_top3 > 70":
            v = metrics.get("customer_concentration_top3"); return v is not None and v > 70
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "ev_ready_revenue_pct < 20":
            v = metrics.get("ev_ready_revenue_pct"); return v is not None and v < 20
        if cond == "roce < 12":
            v = metrics.get("roce"); return v is not None and v < 12
        if cond == "revenue_cagr_3y < 3":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 3
        return False
