"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Logistics sector framework.
3PL, freight, courier, express, warehousing, cold chain, supply chain.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class LogisticsSector(SectorFramework):
    sector_name = "Logistics"
    sector_aliases = [
        "Logistics", "Transportation", "Freight", "Courier",
        "Express Logistics", "3PL", "Warehousing", "Supply Chain",
        "Shipping", "Cold Chain",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.22,
        "cash_flow": 0.19,
        "balance_sheet": 0.19,
        "efficiency": 0.12,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — logistics grows with GDP + e-commerce and manufacturing tailwinds",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "volume_growth_yoy", "Volume Growth (YoY)", 0.12, "high",
                "higher_is_better", "%",
                "Shipment volume or tonnage growth — separates real demand from price-driven revenue",
                thresholds=[(-5, 0), (0, 22), (5, 42), (10, 62), (15, 78), (20, 90), (25, 100)],
                available_from_yfinance=False,
                na_message="Volume data from company quarterly disclosures",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "3PL/express 8-14%; integrated logistics 12-18%; ports/container depots 25-40%",
                thresholds=[(0, 5), (5, 22), (8, 42), (10, 60), (13, 75), (16, 87), (22, 100)],
            ),
            SectorMetric(
                "asset_utilization", "Vehicle/Asset Utilization", 0.10, "high",
                "higher_is_better", "%",
                "Fleet utilization — below 70% is inefficient; above 85% is efficient",
                thresholds=[(50, 15), (60, 30), (70, 50), (78, 68), (84, 82), (90, 93), (95, 100)],
                available_from_yfinance=False,
                na_message="Asset utilization from company operational disclosures",
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Capital efficiency — asset-light logistics 20-35%; heavy-asset 10-18%",
                thresholds=[(0, 5), (8, 22), (12, 45), (16, 62), (20, 78), (26, 90), (32, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Leverage — logistics businesses with owned fleet; above 1x warrants watch",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (0.8, 60), (1.2, 42), (1.8, 20), (2.5, 0)],
            ),
            SectorMetric(
                "capex_to_revenue", "CapEx / Revenue", 0.08, "medium",
                "lower_is_better", "%",
                "Capital intensity — depends on asset ownership; pure 3PL should be <5%",
                thresholds=[(2, 100), (4, 88), (6, 72), (8, 55), (10, 38), (14, 18), (20, 0)],
            ),
            SectorMetric(
                "receivable_days", "Receivable Days", 0.08, "medium",
                "lower_is_better", "days",
                "Debtor days — logistics clients often large enterprises; above 60 days is high",
                thresholds=[(15, 100), (25, 88), (35, 75), (45, 60), (60, 42), (75, 22), (100, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — asset-light logistics should convert 70-90%+ to FCF",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "medium",
                "higher_is_better", "%",
                "Earnings growth — operating leverage from volume scaling",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.08, "medium",
                "neutral", "x",
                "Logistics P/E — asset-light 25-40x; asset-heavy 12-20x",
                thresholds=[(0, 45), (10, 65), (18, 82), (28, 78), (38, 60), (55, 38), (80, 15)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_margin < 7",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 7% for logistics — fuel, labor, and vehicle costs are squeezing margins to near-zero.",
            ),
            SectorRedFlag(
                condition="asset_utilization < 65",
                severity="HIGH",
                title="Low Fleet Utilization",
                description="Below 65% utilization — fixed costs on idle assets drag profitability.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="High Leverage",
                description="D/E above 1.5x for logistics — heavy fleet financing creates vulnerability to interest rate and demand cycles.",
            ),
            SectorRedFlag(
                condition="receivable_days > 75",
                severity="MEDIUM",
                title="High Receivable Days",
                description="Receivables above 75 days signals payment delays from customers — working capital stress.",
            ),
            SectorRedFlag(
                condition="roce < 10",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 10% for a logistics business suggests poor asset utilization or margin compression.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_margin < 7":
            v = metrics.get("ebitda_margin"); return v is not None and v < 7
        if cond == "asset_utilization < 65":
            v = metrics.get("asset_utilization"); return v is not None and v < 65
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "receivable_days > 75":
            v = metrics.get("receivable_days"); return v is not None and v > 75
        if cond == "roce < 10":
            v = metrics.get("roce"); return v is not None and v < 10
        return False
