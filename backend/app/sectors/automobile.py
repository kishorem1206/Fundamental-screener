"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Automobile (OEM) sector framework — implements "Important md files/Sector
analysis framework/Consumer_Discretionary_Automobile_and_Auto_Components_
Analysis.md". Covers passenger vehicles, commercial vehicles, two-wheelers,
three-wheelers OEMs. Auto Ancillaries (component suppliers) have their own
framework (app/sectors/auto_ancillaries.py).

Key metrics per spec:
Vehicle volume growth, ASP/ASP growth, price/mix growth, market share,
EV penetration, EV market share, EV revenue contribution, battery localization,
EV R&D spend, R&D/revenue, exports/revenue, commodity sensitivity,
dealer inventory, premiumization %, segment share, premium segment share.

`volume_growth_yoy`/`asp_growth`/`market_share`/`dealer_inventory_days`
(wired 2026-09-20) are sourced from `app/ingestion/annual_report_ingestion.py`'s
new `automobile_operating_metrics` area — validated live against two real
companies with genuinely different disclosure styles: Maruti Suzuki gives a
clean 5-year "Total Sales Volume" callout (current+prior year in one
place) plus a directly-stated dealer-inventory figure in MD&A narrative;
Bajaj Auto gives a "Table 1: Domestic Sale of Motorcycles" 5-year table
with its own sales, growth %, AND market share % together (market share is
sometimes genuinely company-disclosed, sourced from SIAM data in the
report itself — not always requiring third-party industry data as
originally assumed). `rd_to_revenue_pct`/`export_revenue_pct` are free
reuse of the universal `rd_expenditure`/`revenue_geography` areas already
built for Chemicals — renamed from `rd_to_revenue`/`exports_to_revenue` to
match those areas' computed metric_key names exactly.

`ev_penetration`/`ev_revenue_contribution` remain a documented gap — EV
volume/revenue split isn't reliably a single stated number across
companies the way total volume or market share sometimes is; deferred
rather than force an unreliable extraction.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class AutomobileSector(SectorFramework):
    sector_name = "Automobile"
    sector_aliases = [
        "Automobile", "Automobiles", "Auto", "Automotive",
        "Passenger Vehicles", "Commercial Vehicles", "Two Wheelers",
        "Three Wheelers", "Auto OEM",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.25,
        "profitability": 0.22,
        "cash_flow": 0.17,
        "balance_sheet": 0.13,
        "efficiency": 0.17,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth ────────────────────────────────────────────────────────
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue 3Y CAGR — proxies volume × ASP/realization growth",
                thresholds=[(0, 15), (3, 30), (6, 48), (10, 65), (14, 80), (18, 92), (25, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Profit growth over 3 years — should exceed revenue CAGR in margin-expansion cycle",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (28, 100)],
            ),
            # ── Volume / Operational (NOT in yfinance) ────────────────────────
            SectorMetric(
                "volume_growth_yoy", "Volume Growth (YoY)", 0.10, "high",
                "higher_is_better", "%",
                "Annual wholesale volume growth — core demand indicator for auto OEMs. Computed from "
                "the same-report current+prior-year units in the new automobile_operating_metrics "
                "annual-report area (2026-09-20) — not every company gives both years in one place.",
                thresholds=[(-10, 0), (-5, 15), (0, 30), (5, 52), (10, 70), (15, 84), (20, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report to disclose both current- and "
                           "prior-year unit sales in the same place — not every company does",
            ),
            SectorMetric(
                "asp_growth", "ASP Growth (YoY)", 0.08, "medium",
                "higher_is_better", "%",
                "Average Selling Price growth — reflects premiumization and price hikes net of mix. "
                "Computed as (Screener pnl_sales / annual-report units_sold) for the current and prior "
                "fiscal year each, from the ledger's own two most recent fiscal periods.",
                thresholds=[(-5, 5), (0, 25), (2, 45), (4, 62), (6, 78), (8, 90), (10, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A to disclose both current- and "
                           "prior-year unit sales in the same place",
            ),
            SectorMetric(
                "market_share", "Market Share", 0.08, "medium",
                "higher_is_better", "%",
                "Domestic market share by segment — stability or gain indicates competitive moat. "
                "Sometimes genuinely company-disclosed (sourced from SIAM data in the annual report "
                "itself, confirmed live on Bajaj Auto's 'Table 1: Domestic Sale of Motorcycles' — "
                "company sales, growth %, AND market share % together) — extracted only when directly "
                "stated, never estimated from an industry total.",
                thresholds=[(2, 20), (5, 35), (10, 52), (20, 68), (30, 80), (40, 90), (50, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report to directly state its own market "
                           "share — not every company discloses this",
            ),
            # ── EV Metrics (NOT in yfinance) ──────────────────────────────────
            SectorMetric(
                "ev_penetration", "EV Penetration (%)", 0.08, "high",
                "higher_is_better", "%",
                "EV units as % of total sales — signals transition readiness and future-proofing",
                thresholds=[(0, 20), (2, 38), (5, 58), (10, 74), (20, 87), (30, 95), (50, 100)],
                available_from_yfinance=False,
                na_message="EV penetration requires company-reported segment breakdowns",
            ),
            SectorMetric(
                "ev_revenue_contribution", "EV Revenue Contribution", 0.06, "medium",
                "higher_is_better", "%",
                "EV segment revenue as % of total — revenue mix shift to EVs",
                thresholds=[(0, 20), (3, 40), (8, 60), (15, 75), (25, 88), (40, 100)],
                available_from_yfinance=False,
                na_message="EV revenue split requires company segment reporting",
            ),
            SectorMetric(
                "rd_to_revenue_pct", "R&D / Revenue", 0.06, "medium",
                "higher_is_better", "%",
                "R&D investment as % of revenue — proxy for EV/technology investment intensity. "
                "Sourced from the universal rd_expenditure annual-report area (built for Chemicals, "
                "reused as-is here — same Companies Act Board's Report annexure structure). Renamed "
                "from `rd_to_revenue` (2026-09-20) to match that area's computed metric_key exactly.",
                thresholds=[(0, 15), (0.5, 32), (1.0, 50), (1.5, 65), (2.5, 80), (3.5, 92), (5.0, 100)],
                available_from_yfinance=False,
                na_message="R&D expenditure requires this company's annual report to have been ingested",
            ),
            SectorMetric(
                "export_revenue_pct", "Exports / Revenue", 0.05, "medium",
                "higher_is_better", "%",
                "Export revenue as % of total — geographic diversification and global competitiveness. "
                "Sourced from the universal revenue_geography annual-report area (built for Chemicals, "
                "reused as-is here). Renamed from `exports_to_revenue` (2026-09-20) to match that "
                "area's computed metric_key exactly.",
                thresholds=[(0, 20), (5, 38), (10, 55), (18, 70), (25, 83), (35, 100)],
                available_from_yfinance=False,
                na_message="Revenue geography split requires this company's annual report to have "
                           "been ingested",
            ),
            SectorMetric(
                "dealer_inventory_days", "Dealer Inventory (Days)", 0.05, "medium",
                "lower_is_better", "days",
                "Days of inventory at dealer level — high inventory signals weak demand. Rarely "
                "disclosed numerically, but sometimes stated directly in MD&A narrative (confirmed "
                "live on Maruti Suzuki: 'dealer inventory also remained low at around 12 days of "
                "stock') — sourced from the new automobile_operating_metrics annual-report area "
                "(2026-09-20), never estimated.",
                thresholds=[(15, 100), (25, 85), (35, 68), (45, 50), (55, 32), (70, 15), (90, 0)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A to state dealer inventory "
                           "directly — most companies don't disclose this",
            ),
            # ── Profitability (available from yfinance) ───────────────────────
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "Auto OEM EBITDA margin — 10-14% is healthy; >14% indicates pricing power",
                thresholds=[(0, 5), (5, 22), (8, 42), (10, 60), (12, 74), (15, 87), (20, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.08, "medium",
                "higher_is_better", "%",
                "Net profit margin — 5-8% typical for auto OEMs",
                thresholds=[(0, 5), (2, 22), (4, 42), (6, 60), (8, 75), (10, 87), (14, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Capital efficiency — 15-20%+ indicates strong returns on manufacturing assets",
                thresholds=[(0, 5), (5, 22), (10, 45), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            # ── Efficiency ────────────────────────────────────────────────────
            SectorMetric(
                "asset_turnover", "Asset Turnover", 0.08, "medium",
                "higher_is_better", "x",
                "Revenue / Total Assets — higher means better asset utilization",
                thresholds=[(0.3, 10), (0.6, 30), (0.8, 50), (1.0, 65), (1.2, 78), (1.5, 90), (2.0, 100)],
            ),
            SectorMetric(
                "inventory_days", "Inventory Days", 0.06, "medium",
                "lower_is_better", "days",
                "Factory/WIP inventory days — lower is better for working capital",
                thresholds=[(10, 100), (20, 88), (30, 75), (40, 60), (55, 42), (70, 22), (100, 0)],
            ),
            SectorMetric(
                "capex_to_revenue", "CapEx / Revenue", 0.06, "medium",
                "lower_is_better", "%",
                "Capital intensity — autos are capex heavy; watch for EV transition capex spike",
                thresholds=[(2, 100), (4, 88), (6, 72), (8, 55), (10, 38), (14, 18), (20, 0)],
            ),
            # ── Balance Sheet ─────────────────────────────────────────────────
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "high",
                "lower_is_better", "x",
                "Leverage — autos have capex cycles; above 1.5x warrants concern",
                thresholds=[(0, 100), (0.3, 88), (0.6, 75), (1.0, 58), (1.5, 38), (2.0, 18), (3.0, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "high",
                "higher_is_better", "%",
                "Cash conversion — consistently >60% indicates quality earnings",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            # ── Valuation ─────────────────────────────────────────────────────
            SectorMetric(
                "pe_ratio", "P/E", 0.07, "medium",
                "neutral", "x",
                "P/E — autos are cyclical; 12-20x in normal cycle",
                thresholds=[(0, 50), (8, 75), (14, 88), (20, 78), (28, 60), (40, 38), (60, 15)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.07, "medium",
                "neutral", "x",
                "Enterprise multiple — 8-15x is typical for auto OEMs",
                thresholds=[(0, 60), (5, 85), (8, 90), (12, 80), (16, 65), (22, 45), (30, 20)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 8% for an auto OEM signals pricing pressure or commodity cost squeeze — profitability at risk.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 10",
                severity="MEDIUM",
                title="Below-Par EBITDA Margin",
                description="EBITDA margin 8-10% is below the 10-14% typical for healthy auto OEMs — margin recovery is a watch point.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="High Leverage for Auto OEM",
                description="D/E above 1.5x is concerning given volume cyclicality — earnings can drop sharply in a demand downturn.",
            ),
            SectorRedFlag(
                condition="roce < 10",
                severity="HIGH",
                title="Weak Capital Returns (ROCE)",
                description="ROCE below 10% means the business is not earning its cost of capital — poor capital allocation.",
            ),
            SectorRedFlag(
                condition="fcf_to_pat < 40",
                severity="MEDIUM",
                title="Low Cash Conversion",
                description="FCF/PAT below 40% suggests working capital buildup or heavy capex consuming cash profits.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 3",
                severity="HIGH",
                title="Stagnant Revenue Growth",
                description="Revenue CAGR below 3% for 3 years indicates volume stagnation or severe pricing pressure.",
            ),
            SectorRedFlag(
                condition="capex_to_revenue > 12",
                severity="MEDIUM",
                title="Very High CapEx Intensity",
                description="CapEx above 12% of revenue is very high — could indicate EV transition spending or capacity overbuild.",
            ),
            SectorRedFlag(
                condition="ev_penetration < 2",
                severity="MEDIUM",
                title="Minimal EV Transition Progress",
                description="EV penetration below 2% as India accelerates EV adoption raises long-term relevance risk.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "ebitda_margin < 10":
            v = metrics.get("ebitda_margin"); return v is not None and 8 <= v < 10
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "roce < 10":
            v = metrics.get("roce"); return v is not None and v < 10
        if cond == "fcf_to_pat < 40":
            v = metrics.get("fcf_to_pat"); return v is not None and v < 40
        if cond == "revenue_cagr_3y < 3":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 3
        if cond == "capex_to_revenue > 12":
            v = metrics.get("capex_to_revenue"); return v is not None and v > 12
        if cond == "ev_penetration < 2":
            v = metrics.get("ev_penetration"); return v is not None and v < 2
        return False
