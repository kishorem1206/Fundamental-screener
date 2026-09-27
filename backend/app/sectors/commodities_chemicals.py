"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Chemicals sector framework — implements "Important md files/Sector analysis
framework/Commodities_Chemicals_Analysis_Framework.md" (Macro Sector:
Commodities, Sector: Chemicals). File renamed from chemicals.py to
commodities_chemicals.py (2026-09-20) to mirror that spec file's naming —
as more sector frameworks get built one MD file at a time, matching the
python module name to its spec file keeps the two traceable to each other
(e.g. a future commodities_metals_and_mining.py for
Commodities_Metals_and_Mining_Analysis_Framework.md).

Commodity chemicals, specialty intermediates, agrochemicals, paints, adhesives.
SpecialtyChemicalsSector inherits this with tighter margin expectations.

`raw_material_cost_pct`/`energy_cost_pct`/`export_revenue_pct`/
`rd_to_revenue_pct` (added 2026-09-20) are sourced from
`app/ingestion/annual_report_ingestion.py`'s Chemicals-specific note
extraction (Cost of Materials Consumed, Power & Fuel, Revenue by Geography,
R&D Expenditure) — real annual-report disclosures Screener/yfinance don't
carry at all, validated live against two real companies (Pidilite
Industries, Aarti Industries) before shipping. The ratios themselves
(cost/revenue, etc.) are computed and stored directly by that ingestion
module (it already has both the extracted absolute value and access to
`pnl_sales` in the same DB session), not derived here — this framework just
declares them as ledger-bridged metrics and reads the ratio straight off
the ledger like any other non-yfinance metric.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class ChemicalsSector(SectorFramework):
    sector_name = "Chemicals"
    sector_aliases = [
        "Chemicals", "Chemical", "Commodity Chemicals", "Basic Chemicals",
        "Agrochemicals", "Pesticides", "Paints", "Adhesives", "Fertilisers", "Fertilizers",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.23,
        "cash_flow": 0.17,
        "balance_sheet": 0.16,
        "efficiency": 0.14,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — chemicals growth driven by volume + product mix upgrades",
                thresholds=[(0, 15), (3, 30), (6, 48), (10, 65), (14, 80), (18, 92), (22, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Earnings growth — specialty mix shift drives margin expansion",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
            ),
            SectorMetric(
                "specialty_revenue_pct", "Specialty / Value-Add Revenue %", 0.10, "high",
                "higher_is_better", "%",
                "High-margin specialty products as % of revenue — key quality indicator",
                thresholds=[(10, 15), (20, 32), (30, 52), (40, 68), (55, 82), (65, 92), (80, 100)],
                available_from_yfinance=False,
                na_message="Specialty vs commodity revenue mix requires segment disclosure",
            ),
            SectorMetric(
                "capacity_utilization", "Capacity Utilization", 0.08, "high",
                "higher_is_better", "%",
                "Plant utilization — below 70% signals excess capacity or demand weakness",
                thresholds=[(40, 15), (55, 35), (65, 52), (75, 70), (82, 83), (88, 93), (95, 100)],
                available_from_yfinance=False,
                na_message="Capacity utilization requires operational data from investor presentations",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "Commodity chemicals 8-14%; specialty 18-30%; agrochemicals 15-25%",
                thresholds=[(0, 5), (5, 18), (8, 38), (12, 58), (16, 74), (22, 87), (28, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.08, "medium",
                "higher_is_better", "%",
                "Net margin — specialty chemicals should sustain 10-18%+",
                thresholds=[(0, 5), (3, 22), (6, 42), (10, 62), (14, 78), (18, 90), (22, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Capital efficiency — specialty chemicals should generate 18-28%+ ROCE",
                thresholds=[(0, 5), (8, 22), (12, 45), (16, 62), (20, 78), (26, 90), (32, 100)],
            ),
            SectorMetric(
                "capex_to_revenue", "CapEx / Revenue", 0.08, "medium",
                "lower_is_better", "%",
                "Capital intensity — chemicals are capex heavy; watch expansion cycles",
                thresholds=[(2, 100), (4, 88), (6, 72), (8, 55), (10, 38), (14, 18), (20, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "high",
                "lower_is_better", "x",
                "Leverage — chemicals capex cycles often require debt; watch above 1x",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (0.8, 60), (1.2, 40), (1.8, 18), (2.5, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — lower during capex phase; should recover post-expansion",
                thresholds=[(0, 10), (15, 25), (35, 45), (55, 62), (70, 78), (85, 90), (100, 100)],
            ),
            SectorMetric(
                "inventory_days", "Inventory Days", 0.06, "medium",
                "lower_is_better", "days",
                "RM + WIP inventory — chemicals often hold 30-60 days of RM",
                thresholds=[(15, 100), (25, 88), (40, 75), (55, 58), (70, 38), (90, 18), (120, 0)],
            ),
            # ── Annual-report-sourced (2026-09-20) — see this file's module
            # docstring and app/ingestion/annual_report_ingestion.py's
            # Chemicals-specific extraction areas for how these are sourced
            # and validated. All four ledger-bridged; N/A until a
            # company's annual report has been ingested and disclosed the
            # underlying figure.
            SectorMetric(
                "raw_material_cost_pct", "Raw Material Cost / Revenue", 0.06, "high",
                "lower_is_better", "%",
                "Cost of Materials Consumed as % of revenue — the core spread-pressure indicator. "
                "Composition varies by company: some bundle packing material/fuel/stores into this "
                "figure (confirmed on Aarti Industries), others report a pure raw-material number "
                "(Pidilite) — treat as a trend/peer signal for THIS company over time, not a "
                "perfectly apples-to-apples cross-company comparison.",
                thresholds=[(35, 100), (45, 85), (55, 65), (65, 45), (75, 25), (85, 10), (95, 0)],
                available_from_yfinance=False,
                na_message="Cost of Materials Consumed requires this company's annual report to have been ingested",
            ),
            SectorMetric(
                "energy_cost_pct", "Energy (Power & Fuel) Cost / Revenue", 0.05, "medium",
                "lower_is_better", "%",
                "Power and fuel expense as % of revenue — energy intensity, a structural cost "
                "disadvantage if persistently high relative to peers",
                thresholds=[(1, 100), (2, 85), (3, 65), (5, 45), (8, 22), (12, 5)],
                available_from_yfinance=False,
                na_message="Power & Fuel expense requires this company's annual report to have been ingested",
            ),
            SectorMetric(
                "export_revenue_pct", "Export Revenue %", 0.05, "medium",
                "higher_is_better", "%",
                "Export revenue as % of total — geographic diversification away from pure domestic-"
                "demand dependency; very high export concentration on one destination market carries "
                "its own currency/trade-policy risk the engine doesn't separately score here",
                thresholds=[(0, 30), (10, 45), (20, 60), (35, 75), (50, 88), (70, 96), (85, 100)],
                available_from_yfinance=False,
                na_message="Domestic/export revenue split requires this company's annual report to have been ingested",
            ),
            SectorMetric(
                "rd_to_revenue_pct", "R&D / Revenue", 0.05, "medium",
                "higher_is_better", "%",
                "R&D expenditure (capital + recurring) as % of revenue — technical-capability "
                "investment; most relevant for specialty chemicals and agrochemicals, less "
                "meaningful for pure commodity producers",
                thresholds=[(0, 20), (0.5, 40), (1, 58), (2, 75), (3, 88), (5, 100)],
                available_from_yfinance=False,
                na_message="R&D expenditure requires this company's annual report to have disclosed it (common for companies with no formal R&D program)",
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.07, "medium",
                "neutral", "x",
                "Specialty chemicals premium 20-35x; commodity 10-16x",
                thresholds=[(0, 45), (8, 65), (14, 80), (22, 78), (32, 62), (44, 40), (65, 18)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.07, "medium",
                "neutral", "x",
                "Enterprise multiple — specialty 12-22x; commodity 7-12x",
                thresholds=[(0, 55), (6, 78), (10, 90), (16, 80), (22, 62), (30, 40), (42, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_margin < 10",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 10% for chemicals indicates severe feedstock cost pressure or commodity pricing erosion.",
            ),
            SectorRedFlag(
                condition="capacity_utilization < 60",
                severity="HIGH",
                title="Low Capacity Utilization",
                description="Below 60% utilization signals demand weakness or recent greenfield with delayed ramp-up.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="High Leverage",
                description="D/E above 1.5x for a chemicals company during a downcycle can stress debt service.",
            ),
            SectorRedFlag(
                condition="roce < 12",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 12% suggests the business is not covering cost of capital — review capex decisions.",
            ),
            SectorRedFlag(
                condition="specialty_revenue_pct < 25",
                severity="MEDIUM",
                title="Highly Commodity-Exposed",
                description="Less than 25% specialty revenue makes the business vulnerable to feedstock cost swings.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 5",
                severity="HIGH",
                title="Stagnant Revenue Growth",
                description="Revenue CAGR below 5% for 3 years signals demand loss or pricing power erosion.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_margin < 10":
            v = metrics.get("ebitda_margin"); return v is not None and v < 10
        if cond == "capacity_utilization < 60":
            v = metrics.get("capacity_utilization"); return v is not None and v < 60
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "roce < 12":
            v = metrics.get("roce"); return v is not None and v < 12
        if cond == "specialty_revenue_pct < 25":
            v = metrics.get("specialty_revenue_pct"); return v is not None and v < 25
        if cond == "revenue_cagr_3y < 5":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 5
        return False


class SpecialtyChemicalsSector(ChemicalsSector):
    """Specialty chemicals — higher margin expectations, CRAMS, CSM contracts."""

    sector_name = "Specialty Chemicals"
    sector_aliases = [
        "Specialty Chemicals", "Specialty Chemical", "Fine Chemicals",
        "CRAMS", "CSM", "Contract Research", "Fluorochemicals",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.25,
        "profitability": 0.26,
        "cash_flow": 0.17,
        "balance_sheet": 0.15,
        "efficiency": 0.11,
        "valuation": 0.06,
    }
