"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Oil & Gas sector framework.
Upstream (E&P), midstream, downstream (refining/marketing), integrated companies.
Commodity price sensitive — Brent/WTI linkage, GRM for refiners, 2P reserves for E&P.

`grm` below (available_from_yfinance=False) is now filled by the
Quarterly Sector KPI Extraction Engine (`app/ingestion/
quarterly_operating_metrics_ingestion.py`, "oil_gas" area, added
2026-09-20) — sourced from NSE quarterly Investor Presentation/Investor
Handout filings, stored as `qtr_oilgas_grm`. Confirmed exact live on
BPCL's real Q1 FY27 "Investor Handout" (the standardized Reg-30 format
every PSU refiner files): GRM 41.41 US$/bbl, matching the table's own
Gross Refining Margin row exactly. `reserves_2p`/`reserve_replacement_ratio`
are NOT addressed — reserve data is an ANNUAL disclosure (from independent
reserve auditors), not a quarterly Investor Presentation item, so it's a
better fit for the Annual Report Extraction Engine — not built this pass.

Also fixed 2026-09-20: `classification_map.py` previously routed
`'lpg/cng/png/lng supplier'` (Adani Total Gas, Petronet LNG, IGL, MGL,
IRM Energy) and `'oil equipment & services'` to `'Generic'` even though
this file's own `sector_aliases` already list "Gas Distribution"/"City
Gas Distribution" — the exact-match-first classification design meant
those aliases could never actually be reached for real companies. Both
basic_industry values now route here.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class OilGasSector(SectorFramework):
    sector_name = "Oil & Gas"
    sector_aliases = [
        "Oil & Gas", "Oil And Gas", "Energy", "Petroleum", "Refining",
        "Exploration & Production", "E&P", "Integrated Oil",
        "Oil Exploration", "Gas Distribution", "City Gas Distribution",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.18,
        "profitability": 0.22,
        "cash_flow": 0.24,
        "balance_sheet": 0.21,
        "efficiency": 0.10,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.08, "low",
                "higher_is_better", "%",
                "Revenue growth — heavily influenced by crude price; volume growth more meaningful",
                thresholds=[(0, 15), (3, 28), (5, 45), (8, 62), (12, 78), (16, 90), (20, 100)],
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "Integrated: 8-15%; Refining: 5-10%; E&P: 35-60%+ (high RM-pass-through for downstream)",
                thresholds=[(0, 5), (5, 22), (8, 40), (12, 58), (18, 74), (25, 87), (35, 100)],
            ),
            SectorMetric(
                "grm", "Gross Refining Margin (USD/bbl)", 0.12, "high",
                "higher_is_better", "USD/bbl",
                "GRM — spread between crude input cost and refined product realization; $6+ is healthy",
                thresholds=[(0, 10), (2, 25), (4, 45), (6, 62), (8, 78), (10, 90), (14, 100)],
                available_from_yfinance=False,
                na_message="GRM disclosed by refiners in quarterly results; not in yfinance",
            ),
            SectorMetric(
                "reserves_2p", "2P Reserves (MMboe)", 0.10, "high",
                "higher_is_better", "MMboe",
                "2P (proved + probable) reserves — E&P reserve life and replacement ratio",
                thresholds=[(100, 20), (300, 38), (600, 55), (1000, 70), (2000, 82), (4000, 92), (8000, 100)],
                available_from_yfinance=False,
                na_message="Reserves from company annual reports; not in yfinance financial statements",
            ),
            SectorMetric(
                "reserve_replacement_ratio", "Reserve Replacement Ratio", 0.08, "high",
                "higher_is_better", "%",
                "New reserves added / production — >100% means resource base is growing",
                thresholds=[(40, 15), (70, 35), (90, 55), (100, 68), (120, 82), (150, 93), (200, 100)],
                available_from_yfinance=False,
                na_message="Reserve replacement from E&P company annual reports / reserve audits",
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital efficiency — E&P should generate 12-20%+ across the cycle",
                thresholds=[(0, 5), (5, 20), (10, 42), (14, 62), (18, 78), (24, 90), (30, 100)],
            ),
            SectorMetric(
                "net_debt_to_ebitda", "Net Debt / EBITDA", 0.12, "high",
                "lower_is_better", "x",
                "Leverage — E&P companies must manage debt through oil price cycles; <2.5x is prudent",
                thresholds=[(0, 100), (0.5, 90), (1.0, 78), (1.5, 62), (2.5, 45), (3.5, 25), (5.0, 5)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "high",
                "lower_is_better", "x",
                "Leverage — above 1.5x for E&P is elevated given commodity price risk",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (1.0, 58), (1.5, 38), (2.0, 18), (3.0, 0)],
            ),
            SectorMetric(
                "fcf_yield", "FCF Yield", 0.10, "high",
                "higher_is_better", "%",
                "FCF as % of market cap — key return metric for energy companies",
                thresholds=[(0, 10), (2, 28), (4, 50), (6, 68), (8, 82), (10, 92), (14, 100)],
            ),
            SectorMetric(
                "capex_to_revenue", "CapEx / Revenue", 0.08, "medium",
                "lower_is_better", "%",
                "Capital intensity — E&P and refining are capex heavy; watch exploration spend",
                thresholds=[(2, 100), (4, 88), (7, 72), (10, 55), (14, 38), (18, 18), (25, 0)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "low",
                "neutral", "x",
                "P/E unreliable for cyclicals — use EV/EBITDA and FCF yield instead",
                thresholds=[(0, 55), (5, 75), (8, 88), (12, 80), (18, 60), (28, 38), (45, 15)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "medium",
                "neutral", "x",
                "Oil & gas typically 5-10x; integrated companies 6-12x",
                thresholds=[(0, 58), (3, 80), (5, 90), (8, 82), (12, 62), (17, 40), (25, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="net_debt_to_ebitda > 4",
                severity="HIGH",
                title="Dangerous Leverage for Oil & Gas",
                description="Net Debt/EBITDA above 4x — a crude price drop can trigger debt covenants and liquidity stress.",
            ),
            SectorRedFlag(
                condition="reserve_replacement_ratio < 70",
                severity="HIGH",
                title="Reserve Depletion Risk",
                description="Reserve replacement below 70% means the E&P company is depleting its asset base faster than it is replacing.",
            ),
            SectorRedFlag(
                condition="grm < 4",
                severity="HIGH",
                title="Very Low Gross Refining Margin",
                description="GRM below $4/bbl for a refiner is near breakeven — profitability highly sensitive to any further squeeze.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 8% for an oil & gas company signals commodity price headwinds or high cost structure.",
            ),
            SectorRedFlag(
                condition="capex_to_revenue > 18",
                severity="MEDIUM",
                title="Very High CapEx Intensity",
                description="CapEx above 18% of revenue — heavy exploration/production or refinery expansion spend constraining FCF.",
            ),
            SectorRedFlag(
                condition="roce < 8",
                severity="MEDIUM",
                title="Poor Capital Returns",
                description="ROCE below 8% across 3 years suggests poor field economics or refinery margin compression.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "net_debt_to_ebitda > 4":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and v > 4
        if cond == "reserve_replacement_ratio < 70":
            v = metrics.get("reserve_replacement_ratio"); return v is not None and v < 70
        if cond == "grm < 4":
            v = metrics.get("grm"); return v is not None and v < 4
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "capex_to_revenue > 18":
            v = metrics.get("capex_to_revenue"); return v is not None and v > 18
        if cond == "roce < 8":
            v = metrics.get("roce"); return v is not None and v < 8
        return False
