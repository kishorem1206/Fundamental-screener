"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Aviation sector framework.
Airlines, MRO, airport operators.
RPK, ASK, PLF (load factor), CASK, yield are key airline metrics.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class AviationSector(SectorFramework):
    sector_name = "Aviation"
    sector_aliases = [
        "Aviation", "Airlines", "Airline", "Air Transport", "Airport",
        "Airports", "MRO", "Aviation Services",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.23,
        "cash_flow": 0.22,
        "balance_sheet": 0.22,
        "efficiency": 0.07,
        "valuation": 0.02,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "high",
                "higher_is_better", "%",
                "Revenue growth — airlines: RPK growth + yield; airports: passenger throughput",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "plf_load_factor", "Passenger Load Factor (%)", 0.14, "high",
                "higher_is_better", "%",
                "Seats filled as % of capacity — above 85% is efficient; below 75% is poor",
                thresholds=[(60, 10), (70, 28), (78, 50), (83, 68), (87, 82), (90, 93), (94, 100)],
                available_from_yfinance=False,
                na_message="PLF from DGCA monthly data and airline quarterly disclosures",
            ),
            SectorMetric(
                "yield_per_pkm", "Yield per PKM (INR)", 0.10, "high",
                "higher_is_better", "INR",
                "Revenue per passenger-km — reflects ticket pricing power",
                thresholds=[(3, 10), (4, 28), (5, 48), (6, 65), (7, 80), (8.5, 92), (10, 100)],
                available_from_yfinance=False,
                na_message="Yield per PKM from airline investor disclosures",
            ),
            SectorMetric(
                "cask", "CASK (Cost per Available Seat-km)", 0.10, "high",
                "lower_is_better", "INR",
                "Unit cost — below 4.5 INR/ASK is low-cost efficient; above 6 is full-service territory",
                thresholds=[(3.5, 100), (4.5, 82), (5.5, 62), (6.5, 45), (7.5, 28), (8.5, 12), (10, 0)],
                available_from_yfinance=False,
                na_message="CASK from airline quarterly disclosures; requires ASK data",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "Airlines (ex-lease) EBITDA 15-25%; airport operators 40-60%",
                thresholds=[(0, 5), (5, 18), (10, 38), (15, 58), (20, 74), (28, 88), (35, 100)],
            ),
            SectorMetric(
                "net_debt_to_ebitda", "Net Debt / EBITDA", 0.14, "high",
                "lower_is_better", "x",
                "Leverage (post Ind AS 116 lease; compare ex-lease too) — airlines are highly levered",
                thresholds=[(0, 100), (1, 88), (2, 75), (3, 58), (4, 38), (5, 20), (7, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Including lease liabilities — airlines often show negative equity",
                thresholds=[(0, 100), (1, 82), (2, 65), (3, 45), (5, 25), (7, 8)],
            ),
            SectorMetric(
                "fuel_cost_pct", "Fuel Cost % of Revenue", 0.10, "high",
                "lower_is_better", "%",
                "ATF cost as % of revenue — typically 30-40%; above 45% is margin-critical",
                thresholds=[(20, 100), (28, 82), (34, 65), (40, 45), (46, 25), (52, 8)],
                available_from_yfinance=False,
                na_message="Fuel cost breakdown from airline quarterly disclosures",
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — airlines are capex intensive (planes); watch lease-adjusted FCF",
                thresholds=[(0, 10), (15, 25), (35, 45), (55, 62), (70, 78), (85, 90), (100, 100)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "low",
                "neutral", "x",
                "Airlines trade 5-10x; airports 15-25x (regulated + high-barriers asset)",
                thresholds=[(0, 55), (3, 75), (6, 88), (9, 82), (13, 65), (18, 42), (28, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="plf_load_factor < 75",
                severity="HIGH",
                title="Very Low Passenger Load Factor",
                description="PLF below 75% — fixed cost per available seat is not being covered; unit economics deteriorate rapidly.",
            ),
            SectorRedFlag(
                condition="net_debt_to_ebitda > 5",
                severity="HIGH",
                title="Dangerous Leverage",
                description="Net Debt/EBITDA above 5x for an airline — any demand shock triggers liquidity crisis.",
            ),
            SectorRedFlag(
                condition="fuel_cost_pct > 45",
                severity="HIGH",
                title="Very High Fuel Cost",
                description="ATF above 45% of revenue — margin is critically exposed to crude price moves.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 10",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 10% for an airline — barely covering operating costs before interest and depreciation.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 5",
                severity="MEDIUM",
                title="Slow Revenue Growth",
                description="Revenue CAGR below 5% — capacity additions or yield improvements needed.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "plf_load_factor < 75":
            v = metrics.get("plf_load_factor"); return v is not None and v < 75
        if cond == "net_debt_to_ebitda > 5":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and v > 5
        if cond == "fuel_cost_pct > 45":
            v = metrics.get("fuel_cost_pct"); return v is not None and v > 45
        if cond == "ebitda_margin < 10":
            v = metrics.get("ebitda_margin"); return v is not None and v < 10
        if cond == "revenue_cagr_3y < 5":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 5
        return False
