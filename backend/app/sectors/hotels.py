"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Hotels, Hospitality, and Leisure sector framework.
Hotel operators, resort chains, QSR (Quick Service Restaurants), casual dining.
RevPAR, occupancy, ARR, restaurant SSSG are key metrics.

`occupancy_rate`, `arr` and `revpar` below (all available_from_yfinance=
False) are now filled by the Quarterly Sector KPI Extraction Engine
(`app/ingestion/quarterly_operating_metrics_ingestion.py`, "hotels" area,
added 2026-09-20) — sourced from NSE quarterly Investor Presentation
filings, stored as `qtr_hotels_arr`/`qtr_hotels_occupancy`/
`qtr_hotels_revpar`. Confirmed exact live on Chalet Hotels' real Q1 FY27
deck (a genuine row-based "Combined Portfolio" table, not a bar-chart
infographic): ADR 13,247 vs 12,207, Occupancy 64.8% vs 66.0%, RevPAR 8,582
vs 8,059 (Q1 FY27 vs Q1 FY26) — all matching the table's own stated YoY%.
Indian Hotels' (IHCL) own deck was checked and rejected as unreliable: its
occupancy/ADR/RevPAR content is a multi-panel bar-chart infographic with
several unlabeled figures interleaved in extraction order, the same
failure mode as the rejected Ambuja Cement bar-chart page. `sssg` (a
QSR/restaurant same-store metric under this same framework) is not yet
addressed — no restaurant-chain deck was checked this round.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class HotelsSector(SectorFramework):
    sector_name = "Hotels & Restaurants"
    sector_aliases = [
        "Hotels", "Hotels & Restaurants", "Hospitality", "Tourism",
        "Restaurants", "QSR", "Food Service", "Leisure", "Resorts",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.23,
        "cash_flow": 0.20,
        "balance_sheet": 0.19,
        "efficiency": 0.10,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "high",
                "higher_is_better", "%",
                "Revenue growth — hotels: RevPAR × room additions; QSR: SSSG + store count",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "occupancy_rate", "Occupancy Rate (%)", 0.12, "high",
                "higher_is_better", "%",
                "Room nights occupied / available — above 70% is healthy; below 55% is weak",
                thresholds=[(40, 10), (50, 28), (58, 48), (65, 65), (72, 80), (78, 92), (85, 100)],
                available_from_yfinance=False,
                na_message="Occupancy rate from company quarterly disclosures / HVS data",
            ),
            SectorMetric(
                "arr", "Average Room Rate (INR)", 0.10, "high",
                "higher_is_better", "INR",
                "Average room rate per occupied night — premiumization indicator",
                thresholds=[(2000, 15), (3500, 32), (5000, 52), (7000, 68), (9000, 82), (12000, 93), (15000, 100)],
                available_from_yfinance=False,
                na_message="ARR from company quarterly disclosures",
            ),
            SectorMetric(
                "revpar", "RevPAR (INR)", 0.12, "high",
                "higher_is_better", "INR",
                "Revenue per Available Room = Occupancy × ARR — the key hotel performance metric",
                thresholds=[(1500, 15), (2500, 32), (3500, 52), (5000, 68), (7000, 82), (9000, 93), (12000, 100)],
                available_from_yfinance=False,
                na_message="RevPAR = Occupancy × ARR; requires both metrics from company disclosures",
            ),
            SectorMetric(
                "sssg", "Same-Store Sales Growth (SSSG)", 0.10, "high",
                "higher_is_better", "%",
                "QSR/restaurant same-store growth — quality of existing locations",
                thresholds=[(-5, 0), (0, 22), (3, 42), (6, 62), (9, 78), (12, 90), (15, 100)],
                available_from_yfinance=False,
                na_message="SSSG from company quarterly disclosures for restaurant chains",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "Hotels (owned) 25-40%; QSR 15-25%; management contracts 40-60%",
                thresholds=[(5, 10), (10, 28), (16, 48), (22, 65), (28, 80), (35, 92), (45, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital efficiency — owned hotels are asset heavy; management model 25-40%+",
                thresholds=[(0, 5), (5, 20), (10, 40), (14, 60), (18, 76), (24, 88), (30, 100)],
            ),
            SectorMetric(
                "net_debt_to_ebitda", "Net Debt / EBITDA", 0.12, "high",
                "lower_is_better", "x",
                "Leverage — owned hotel portfolios are asset-backed; <3x is manageable",
                thresholds=[(0, 100), (0.5, 90), (1.0, 78), (1.5, 65), (2.5, 48), (3.5, 25), (5.0, 5)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "medium",
                "lower_is_better", "x",
                "Leverage — hospitality businesses with owned assets; above 1.5x is elevated",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (0.8, 60), (1.2, 42), (1.8, 20), (2.5, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — watch refurbishment and expansion capex",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "low",
                "neutral", "x",
                "Hotels/QSR trade at premium P/E — 30-60x for quality brands",
                thresholds=[(0, 45), (15, 65), (25, 80), (38, 82), (55, 68), (80, 45), (120, 20)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="occupancy_rate < 55",
                severity="HIGH",
                title="Very Low Occupancy",
                description="Occupancy below 55% — fixed costs overwhelm the P&L; break-even not being reached.",
            ),
            SectorRedFlag(
                condition="net_debt_to_ebitda > 4",
                severity="HIGH",
                title="Dangerous Leverage",
                description="Net Debt/EBITDA above 4x — any demand softness (travel disruptions) creates debt distress.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 12",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 12% for a hotel indicates very low occupancy or high fixed costs unsupported by revenue.",
            ),
            SectorRedFlag(
                condition="sssg < 0",
                severity="HIGH",
                title="Negative SSSG for Restaurant",
                description="Negative same-store sales — existing restaurants losing customers to competition or declining footfall.",
            ),
            SectorRedFlag(
                condition="roce < 8",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 8% for a hospitality asset — hotel properties need 10%+ to justify the capital lock-in.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "occupancy_rate < 55":
            v = metrics.get("occupancy_rate"); return v is not None and v < 55
        if cond == "net_debt_to_ebitda > 4":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and v > 4
        if cond == "ebitda_margin < 12":
            v = metrics.get("ebitda_margin"); return v is not None and v < 12
        if cond == "sssg < 0":
            v = metrics.get("sssg"); return v is not None and v < 0
        if cond == "roce < 8":
            v = metrics.get("roce"); return v is not None and v < 8
        return False
