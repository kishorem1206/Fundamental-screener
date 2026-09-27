"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Forest Materials sector framework — implements "Important md files/Sector
analysis framework/Commodities_Forest_Materials_Analysis.md" (Macro Sector:
Commodities, Sector: Forest Materials; Industries: Paper, Forest & Jute
Products). File named commodities_forest_materials.py to mirror the spec
file's naming, same convention `commodities_chemicals.py` established.

Every real company classified here today (basic_industry='Paper & Paper
Products', confirmed live: SATIA, ANDHRAPAP, NRAIL, WSTCSTPAPR, SESHAPAPER,
JKPAPER, TNPL) is a paper manufacturer — no pure-jute company is in the DB
yet, so this framework is tuned against real paper-company disclosures.

`raw_material_cost_pct`/`energy_cost_pct`/`export_revenue_pct` are FREE
reuse of the universal annual-report areas already built for Chemicals
(`raw_material`/`energy_cost`/`revenue_geography` in
app/ingestion/annual_report_ingestion.py) — paper companies file the same
Ind-AS notes-to-accounts structure, so zero new extraction work was needed
for these three.

`capacity_utilization`/`realisation_per_tonne`/`ebitda_per_tonne`/
`cost_per_tonne` are sourced from a NEW `paper_operating_metrics`
annual-report area, mirroring Cement's `cement_operating_metrics` area's
architecture and lessons (MD&A-based, narrow anchor terms, "return null
if ambiguous" prompt discipline). Validated live against two real
companies with genuinely different disclosure quality: TNPL's MD&A
"Performance Highlights" gives clean current-year Paper production/sales
volume (in lakh MT) and an explicit domestic/export sales split; JK
Paper's report has no comparably extractable production/capacity table in
plain text at all (a real, accepted per-company miss, same class as
Ambuja Cements' — see the area's own prompt comment).

Deliberately does NOT declare `volume_growth_yoy` (unlike CementSector) —
unlike UltraTech Cement's clean current+prior-year table, TNPL's real
MD&A only gives a superlative ("highest since inception"), never a
same-report prior-year comparison figure, so a reliable single-call YoY
figure isn't available yet. Left as a documented scope gap, not
approximated.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class ForestMaterialsSector(SectorFramework):
    sector_name = "Forest Materials"
    sector_aliases = ["Forest Materials", "Paper", "Paper & Paper Products",
                       "Forest & Jute Products", "Jute", "Paperboard"]

    SECTOR_WEIGHTS = {
        "growth": 0.21,
        "profitability": 0.23,
        "cash_flow": 0.19,
        "balance_sheet": 0.19,
        "efficiency": 0.13,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "medium",
                "higher_is_better", "%",
                "Revenue growth — blends volume and realization; paper is a cyclical commodity",
                thresholds=[(0, 15), (3, 30), (5, 48), (8, 65), (12, 80), (16, 92), (20, 100)],
            ),
            SectorMetric(
                "capacity_utilization", "Capacity Utilization", 0.10, "high",
                "higher_is_better", "%",
                "Plant utilization — below 65% signals demand weakness or structural overcapacity",
                thresholds=[(40, 10), (55, 28), (65, 48), (72, 65), (80, 80), (87, 92), (93, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A production/capacity "
                           "disclosure to have been ingested (app/ingestion/annual_report_ingestion.py's "
                           "paper_operating_metrics area) — not on Screener or yfinance; not every "
                           "company discloses this in extractable text form",
            ),
            SectorMetric(
                "realisation_per_tonne", "Realisation per Tonne (INR)", 0.10, "high",
                "higher_is_better", "INR",
                "Net realisation per tonne of paper sold — reflects pricing power and product mix. "
                "Computed (annual-report ingestion layer) as Screener's pnl_sales / annual-report "
                "sales volume, same statement_type.",
                thresholds=[(35000, 15), (42000, 32), (48000, 52), (55000, 68), (62000, 82),
                            (70000, 92), (78000, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A sales-volume disclosure to "
                           "have been ingested — not on Screener or yfinance",
            ),
            SectorMetric(
                "cost_per_tonne", "Cost per Tonne (INR)", 0.08, "medium",
                "lower_is_better", "INR",
                "Total production cost per tonne (pulp/fibre + energy + chemicals + freight + other). "
                "Derived as realisation_per_tonne - ebitda_per_tonne, not a sum of individually-"
                "extracted cost components (same conservative-derivation precedent as CementSector).",
                thresholds=[(28000, 100), (34000, 82), (40000, 65), (46000, 48), (52000, 30),
                            (58000, 12), (65000, 0)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A sales-volume disclosure to "
                           "have been ingested — not on Screener or yfinance",
            ),
            SectorMetric(
                "ebitda_per_tonne", "EBITDA per Tonne (INR)", 0.10, "high",
                "higher_is_better", "INR",
                "EBITDA/tonne — the core paper-industry unit-economics metric. Computed "
                "(annual-report ingestion layer) as Screener's pnl_operating_profit / annual-report "
                "sales volume, same statement_type.",
                thresholds=[(3000, 10), (5000, 28), (7000, 48), (9000, 65), (12000, 80),
                            (15000, 92), (18000, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A sales-volume disclosure to "
                           "have been ingested — not on Screener or yfinance",
            ),
            SectorMetric(
                "raw_material_cost_pct", "Raw Material Cost / Revenue", 0.10, "high",
                "lower_is_better", "%",
                "Cost of Materials Consumed as % of revenue — pulp/wood/waste-paper/chemicals spread "
                "pressure indicator. Sourced from the universal raw_material annual-report area "
                "(built for Chemicals, reused as-is here — same Ind-AS note structure).",
                thresholds=[(30, 100), (40, 85), (50, 65), (60, 45), (70, 25), (80, 10), (90, 0)],
                available_from_yfinance=False,
                na_message="Cost of Materials Consumed requires this company's annual report to "
                           "have been ingested",
            ),
            SectorMetric(
                "energy_cost_pct", "Energy Cost / Revenue", 0.08, "medium",
                "lower_is_better", "%",
                "Power & fuel cost as % of revenue — paper is energy-intensive (pulping, drying). "
                "Sourced from the universal energy_cost annual-report area (built for Chemicals, "
                "reused as-is here).",
                thresholds=[(1, 100), (2, 85), (4, 65), (6, 45), (9, 22), (13, 5)],
                available_from_yfinance=False,
                na_message="Power & Fuel cost requires this company's annual report to have been ingested",
            ),
            SectorMetric(
                "export_revenue_pct", "Export Revenue %", 0.05, "low",
                "higher_is_better", "%",
                "Export revenue as % of total — diversification signal against domestic pricing cycles. "
                "Sourced from the universal revenue_geography annual-report area (built for Chemicals, "
                "reused as-is here).",
                thresholds=[(0, 30), (10, 45), (20, 60), (35, 75), (50, 88), (70, 96), (85, 100)],
                available_from_yfinance=False,
                na_message="Revenue geography split requires this company's annual report to have "
                           "been ingested",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.10, "high",
                "higher_is_better", "%",
                "EBITDA margin — 15-22% is healthy for integrated players; commodity paper runs thinner",
                thresholds=[(4, 10), (8, 28), (12, 48), (16, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.09, "high",
                "higher_is_better", "%",
                "Capital returns — paper is capex heavy (pulp mills, paper machines); 10-16%+ across "
                "cycle is good",
                thresholds=[(0, 5), (5, 20), (9, 42), (13, 62), (17, 78), (22, 90), (28, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "medium",
                "lower_is_better", "x",
                "Leverage — paper mills are capital intensive; D/E >1.2x is a real risk in a down cycle",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (0.8, 58), (1.2, 38), (1.8, 18), (2.5, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.07, "medium",
                "higher_is_better", "%",
                "Cash conversion — watch during capacity-expansion phases; should be 50%+ in steady state",
                thresholds=[(0, 10), (20, 28), (40, 48), (55, 65), (70, 80), (85, 92), (100, 100)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.05, "low",
                "neutral", "x",
                "Enterprise multiple — paper typically trades 6-10x; premium/specialty players higher",
                thresholds=[(0, 55), (4, 78), (7, 90), (10, 80), (14, 62), (18, 40), (24, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="capacity_utilization < 60",
                severity="HIGH",
                title="Very Low Capacity Utilization",
                description="Below 60% utilization signals severe demand weakness or structural "
                            "overcapacity — fixed cost leverage works in reverse.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="High Leverage",
                description="D/E above 1.5x is dangerous for a capital-intensive, cyclical paper "
                            "business if the down cycle extends.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="MEDIUM",
                title="Low EBITDA Margin",
                description="EBITDA below 8% indicates weak pulp-paper spread or energy cost pressure.",
            ),
            SectorRedFlag(
                condition="roce < 8",
                severity="MEDIUM",
                title="Below-Par ROCE",
                description="ROCE below 8% over a cycle indicates structural cost or pricing problems.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "capacity_utilization < 60":
            v = metrics.get("capacity_utilization"); return v is not None and v < 60
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "roce < 8":
            v = metrics.get("roce"); return v is not None and v < 8
        return False
