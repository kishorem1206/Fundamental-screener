"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Electronics / EMS / Semiconductor sector framework.
Electronics Manufacturing Services, PCB, component assembly, semiconductors.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class ElectronicsSector(SectorFramework):
    sector_name = "Electronics"
    sector_aliases = [
        "Electronics", "Electronic Components", "EMS",
        "Electronics Manufacturing", "Semiconductors", "PCB",
        "Electronic Equipment", "Technology Hardware",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.26,
        "profitability": 0.22,
        "cash_flow": 0.17,
        "balance_sheet": 0.19,
        "efficiency": 0.12,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — EMS/electronics benefits from India PLI and China+1 sourcing shift",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Earnings growth — operating leverage should amplify PAT growth at scale",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
            ),
            SectorMetric(
                "pli_incentive_revenue_pct", "PLI Incentive / Revenue", 0.08, "medium",
                "neutral", "%",
                "PLI benefit as % of revenue — high PLI dependence inflates earnings artificially",
                thresholds=[(0, 75), (2, 85), (5, 90), (8, 82), (12, 65), (18, 42), (25, 18)],
                available_from_yfinance=False,
                na_message="PLI incentives from company disclosures / government notifications",
            ),
            SectorMetric(
                "customer_concentration_top3", "Top-3 Customer %", 0.10, "high",
                "lower_is_better", "%",
                "Revenue from top 3 customers — EMS often very concentrated (Apple, Samsung)",
                thresholds=[(20, 100), (35, 82), (50, 65), (65, 45), (80, 25), (90, 8)],
                available_from_yfinance=False,
                na_message="Customer concentration from company annual report",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "EMS margins 3-7% (assembly-heavy); electronics 8-15%; semiconductor 25-45%",
                thresholds=[(0, 5), (3, 20), (5, 38), (7, 55), (10, 70), (14, 85), (20, 100)],
            ),
            SectorMetric(
                "asset_turnover", "Asset Turnover", 0.10, "high",
                "higher_is_better", "x",
                "Revenue / Total Assets — EMS should generate 1.5-2.5x asset turns",
                thresholds=[(0.5, 10), (0.8, 28), (1.2, 48), (1.6, 65), (2.0, 80), (2.5, 92), (3.0, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Capital efficiency — EMS 14-22%; IP-rich electronics 20-35%",
                thresholds=[(0, 5), (8, 22), (14, 45), (18, 62), (22, 78), (28, 90), (35, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Leverage — EMS should be lightly leveraged given thin margins; above 0.8x is elevated",
                thresholds=[(0, 100), (0.2, 88), (0.4, 72), (0.6, 55), (0.8, 38), (1.2, 18), (2.0, 0)],
            ),
            SectorMetric(
                "working_capital_days", "Working Capital Days", 0.10, "medium",
                "lower_is_better", "days",
                "Net working capital — components-heavy EMS often 30-60 WC days",
                thresholds=[(10, 100), (25, 88), (40, 72), (55, 55), (70, 38), (90, 18), (120, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — EMS has low-capex assembly; should convert 60%+ to FCF",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.08, "medium",
                "neutral", "x",
                "EMS trades 20-40x given PLI and China+1 growth narrative",
                thresholds=[(0, 45), (10, 65), (20, 82), (32, 78), (50, 60), (75, 38), (120, 15)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="customer_concentration_top3 > 75",
                severity="HIGH",
                title="Dangerous Customer Concentration",
                description="Over 75% from top 3 customers — loss of a single large OEM relationship can crater revenue.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 4",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 4% for an EMS company — any cost shock turns the business loss-making.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.0",
                severity="HIGH",
                title="High Leverage for Thin-Margin EMS",
                description="D/E above 1x in an assembly-heavy business with thin margins amplifies downside risk.",
            ),
            SectorRedFlag(
                condition="pli_incentive_revenue_pct > 15",
                severity="MEDIUM",
                title="Very High PLI Dependence",
                description="PLI incentives above 15% of revenue — earnings quality concern; policy risk if incentive structure changes.",
            ),
            SectorRedFlag(
                condition="asset_turnover < 1.0",
                severity="MEDIUM",
                title="Low Asset Turnover for EMS",
                description="Asset turnover below 1x for an EMS player suggests idle capacity or poor asset productivity.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 8",
                severity="MEDIUM",
                title="Below-Par Growth for a PLI Beneficiary",
                description="Revenue CAGR below 8% for an EMS/electronics company in the India PLI era is below-expectation.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "customer_concentration_top3 > 75":
            v = metrics.get("customer_concentration_top3"); return v is not None and v > 75
        if cond == "ebitda_margin < 4":
            v = metrics.get("ebitda_margin"); return v is not None and v < 4
        if cond == "debt_to_equity > 1.0":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.0
        if cond == "pli_incentive_revenue_pct > 15":
            v = metrics.get("pli_incentive_revenue_pct"); return v is not None and v > 15
        if cond == "asset_turnover < 1.0":
            v = metrics.get("asset_turnover"); return v is not None and v < 1.0
        if cond == "revenue_cagr_3y < 8":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 8
        return False
