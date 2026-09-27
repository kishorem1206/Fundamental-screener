"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Cement sector framework — implements "Important md files/Sector analysis
framework/Commodities_Construction_Materials_Analysis.md" §2.1 (Cement &
Cement Products). Regional cyclical — volume (MT), cost/tonne, realisation/
tonne, capacity utilization.

`volume_growth_yoy`/`realisation_per_tonne`/`cost_per_tonne`/
`ebitda_per_tonne`/`capacity_utilization` (wired 2026-09-20) are sourced
from `app/ingestion/annual_report_ingestion.py`'s `cement_operating_metrics`
area — production volume/installed capacity/capacity utilisation are
reported in the annual report's MD&A section, never on Screener or
yfinance. Validated live against two real companies (UltraTech Cement:
clean, extractable; Ambuja Cements: NOT extractable in this text form,
its equivalent figures are laid out as a scattered infographic — an
accepted, documented per-company miss, not a bug). Realisation/cost/EBITDA
per tonne are computed (in the ingestion layer, which has DB access) from
that production volume combined with Screener's own `pnl_sales`/
`pnl_operating_profit` — this file has no DB access and does not derive them.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class CementSector(SectorFramework):
    sector_name = "Cement"
    sector_aliases = ["Cement", "Cement Products", "Concrete", "Ready Mix Concrete", "RMC"]

    SECTOR_WEIGHTS = {
        "growth": 0.22,
        "profitability": 0.23,
        "cash_flow": 0.19,
        "balance_sheet": 0.19,
        "efficiency": 0.12,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "medium",
                "higher_is_better", "%",
                "Revenue growth — blends volume (MT) + realization (price/tonne) growth",
                thresholds=[(0, 15), (3, 28), (5, 45), (8, 62), (12, 78), (16, 90), (20, 100)],
            ),
            SectorMetric(
                "volume_growth_yoy", "Volume Growth (YoY, MT)", 0.12, "high",
                "higher_is_better", "%",
                "Cement dispatches growth — key demand metric; tracks infrastructure cycle",
                thresholds=[(-5, 0), (0, 20), (3, 40), (6, 60), (9, 76), (12, 88), (15, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A Production/Capacity table to "
                           "have been ingested (app/ingestion/annual_report_ingestion.py's "
                           "cement_operating_metrics area) — not on Screener or yfinance",
            ),
            SectorMetric(
                "realisation_per_tonne", "Realisation per Tonne (INR)", 0.10, "high",
                "higher_is_better", "INR",
                "Net realisation per tonne — reflects pricing power and regional mix. Computed "
                "(annual-report ingestion layer) as Screener's pnl_sales / annual-report-extracted "
                "production volume, same statement_type — never derived here, no DB access at this layer.",
                thresholds=[(3500, 15), (4000, 32), (4500, 52), (5000, 68), (5500, 82), (6000, 92), (6500, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A Production table to have been "
                           "ingested (production volume, MMT) — not on Screener or yfinance",
            ),
            SectorMetric(
                "cost_per_tonne", "Cost per Tonne (INR)", 0.10, "high",
                "lower_is_better", "INR",
                "Total production cost per tonne — energy + logistics key cost drivers. Derived as "
                "realisation_per_tonne - ebitda_per_tonne (the Realization - Costs = EBITDA bridge), "
                "not a sum of individually-extracted cost components — see annual_report_ingestion.py's "
                "cement_operating_metrics prompt comment for why per-component costs aren't extracted.",
                thresholds=[(2800, 100), (3200, 82), (3600, 65), (4000, 48), (4400, 30), (4800, 12), (5200, 0)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A Production table to have been "
                           "ingested — not on Screener or yfinance",
            ),
            SectorMetric(
                "ebitda_per_tonne", "EBITDA per Tonne (INR)", 0.12, "high",
                "higher_is_better", "INR",
                "EBITDA/tonne — most important cement metric; ₹800-1400+ is healthy. Computed "
                "(annual-report ingestion layer) as Screener's pnl_operating_profit / annual-report "
                "production volume, same statement_type.",
                thresholds=[(300, 10), (500, 25), (700, 45), (900, 62), (1100, 78), (1300, 90), (1500, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A Production table to have been "
                           "ingested — not on Screener or yfinance",
            ),
            SectorMetric(
                "capacity_utilization", "Capacity Utilization", 0.08, "high",
                "higher_is_better", "%",
                "Plant utilization — below 65% is demand-weak; above 85% signals tight supply. Reported "
                "directly by the company in its annual report MD&A (Production / Installed Capacity "
                "table), extracted and stored as-is, not recomputed.",
                thresholds=[(40, 10), (55, 28), (65, 48), (72, 65), (80, 80), (87, 92), (93, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A Production/Capacity table to "
                           "have been ingested — not on Screener or yfinance",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "EBITDA margin — 18-25% is healthy; depends heavily on energy costs",
                thresholds=[(5, 10), (10, 28), (14, 48), (18, 65), (22, 80), (26, 92), (30, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital returns — cement is capex heavy; 12-20%+ across cycle is good",
                thresholds=[(0, 5), (5, 20), (10, 42), (14, 62), (18, 78), (24, 90), (30, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Leverage — cement plants are capital intensive; D/E >1.5x post-expansion is concerning",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (0.8, 60), (1.2, 40), (1.8, 18), (2.5, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — watch during greenfield phase; should be 60%+ in steady state",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.08, "medium",
                "neutral", "x",
                "Enterprise multiple — cement typically 8-14x; premium players 12-18x",
                thresholds=[(0, 55), (5, 78), (8, 90), (12, 80), (16, 62), (22, 40), (30, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_per_tonne < 600",
                severity="HIGH",
                title="Very Low EBITDA per Tonne",
                description="EBITDA/tonne below ₹600 signals severe cost pressure or pricing collapse — profitability is at risk.",
            ),
            SectorRedFlag(
                condition="capacity_utilization < 60",
                severity="HIGH",
                title="Very Low Capacity Utilization",
                description="Below 60% utilization signals severe demand weakness or excess regional supply — fixed cost leverage works in reverse.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="High Leverage Post-Expansion",
                description="D/E above 1.5x post greenfield is dangerous if volume ramp-up is delayed.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 12",
                severity="MEDIUM",
                title="Low EBITDA Margin",
                description="EBITDA below 12% indicates energy/logistics cost squeeze or weak realization.",
            ),
            SectorRedFlag(
                condition="roce < 10",
                severity="MEDIUM",
                title="Below-Par ROCE",
                description="ROCE below 10% in cement over 3 years indicates structural cost or pricing problem.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_per_tonne < 600":
            v = metrics.get("ebitda_per_tonne"); return v is not None and v < 600
        if cond == "capacity_utilization < 60":
            v = metrics.get("capacity_utilization"); return v is not None and v < 60
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "ebitda_margin < 12":
            v = metrics.get("ebitda_margin"); return v is not None and v < 12
        if cond == "roce < 10":
            v = metrics.get("roce"); return v is not None and v < 10
        return False
