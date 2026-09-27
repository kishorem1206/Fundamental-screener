"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Textiles sector framework — Consumer_Discretionary_Textiles_Analysis.md.
Spinning, weaving, processing, garments/apparel (own-brand and export/
private-label), home textiles, synthetic/technical textiles, integrated
manufacturers. Covers both commodity-cycle businesses (spinning/weaving,
where the yarn/fabric spread over raw cotton/polymer cost drives margin)
and branded/export garment businesses (where volume, ASP and customer
relationships matter more) — the spec explicitly warns against comparing
them with the same KPI set, but this framework, like HotelsSector's
Hotels+QSR span or ConsumerDurablesSector's appliances+electronics span,
uses one metric set with importance/weight tuned to work reasonably across
both rather than building a second framework for a still-related industry.

Built 2026-09-20 — previously every textiles company (Page Industries,
KPR Mill, Welspun Living, Vardhman Textiles, Arvind, ...) fell through to
GenericSector, since `classification_map.py` explicitly documented this as
an open coverage gap ("no dedicated framework exists yet ... Textiles").
`volume_growth_yoy`, `utilization_pct` and `export_revenue_pct` are
genuinely disclosed by textile companies in quarterly investor
presentations/concalls but have no structured-API source (not on
yfinance, not on Screener) — real candidates and a possible quarterly
extraction area are a follow-up, not built in this same pass. Spread
analysis (yarn/fabric realization minus cotton/polymer cost, MD spec §10 —
a core sector-specific engine) is deliberately NOT modeled as a metric
here: it needs a paired realization + input-cost figure that isn't
reliably available from any source wired up yet, and a fabricated proxy
would be worse than an honest gap.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class TextilesSector(SectorFramework):
    sector_name = "Textiles"
    sector_aliases = [
        "Textiles", "Textiles & Apparels", "Garments & Apparels",
        "Other Textile Products", "Spinning", "Weaving", "Home Textiles",
        "Technical Textiles", "Apparel",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.27,
        "profitability": 0.22,
        "cash_flow": 0.15,
        "balance_sheet": 0.15,
        "efficiency": 0.16,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — textiles is cycle-sensitive; sustained double-digit growth is strong",
                thresholds=[(0, 15), (5, 32), (10, 52), (15, 68), (20, 82), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "volume_growth_yoy", "Volume Growth (YoY)", 0.10, "high",
                "higher_is_better", "%",
                "Production/sales volume growth — separates real demand from price/spread-driven revenue growth",
                thresholds=[(-5, 0), (0, 22), (5, 42), (10, 62), (15, 78), (20, 90), (25, 100)],
                available_from_yfinance=False,
                na_message="Volume data from company quarterly disclosures / investor presentations",
            ),
            SectorMetric(
                "utilization_pct", "Capacity Utilization", 0.10, "high",
                "higher_is_better", "%",
                "Production / installed capacity — below 65% signals demand weakness or overcapacity",
                thresholds=[(50, 10), (60, 28), (70, 48), (80, 65), (88, 82), (94, 93), (98, 100)],
                available_from_yfinance=False,
                na_message="Capacity utilization from company disclosures / investor presentations",
            ),
            SectorMetric(
                "export_revenue_pct", "Export Revenue %", 0.06, "low",
                "higher_is_better", "%",
                "Export share — diversification/global competitiveness signal, not inherently required "
                "for a domestic-branded player",
                thresholds=[(0, 40), (15, 55), (30, 68), (45, 78), (60, 88), (75, 95), (90, 100)],
                available_from_yfinance=False,
                na_message="Export revenue % from company segment disclosures",
            ),
            SectorMetric(
                "gross_margin", "Gross Margin", 0.10, "high",
                "higher_is_better", "%",
                "Commodity spinning/weaving 15-25%; branded apparel/home textiles 40-60%",
                thresholds=[(10, 10), (18, 30), (25, 50), (32, 65), (40, 80), (48, 92), (55, 100)],
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "EBITDA margin — reflects spread/utilization for commodity players, brand strength for apparel",
                thresholds=[(5, 10), (9, 28), (13, 45), (17, 62), (22, 78), (28, 90), (35, 100)],
            ),
            SectorMetric(
                "inventory_days", "Inventory Days", 0.10, "medium",
                "lower_is_better", "days",
                "Raw material + WIP + finished goods — textiles run high inventory; watch for slow-moving buildup",
                thresholds=[(30, 100), (50, 85), (70, 68), (90, 50), (120, 30), (150, 10)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital returns — capital-intensive spinning/weaving typically 10-18%; asset-light apparel higher",
                thresholds=[(0, 5), (8, 22), (12, 42), (16, 60), (20, 76), (26, 88), (34, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "medium",
                "lower_is_better", "x",
                "Leverage — capacity-heavy commodity players run higher D/E than branded/asset-light apparel",
                thresholds=[(0, 100), (0.3, 88), (0.6, 70), (1.0, 50), (1.5, 30), (2.2, 10), (3.0, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.06, "medium",
                "higher_is_better", "%",
                "Cash conversion — watch capex intensity and working-capital swings across the textile cycle",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "low",
                "neutral", "x",
                "Cyclical sector — use normalized earnings where possible; commodity players 8-16x, branded apparel 30-50x",
                thresholds=[(0, 50), (8, 70), (14, 85), (20, 80), (28, 62), (40, 40), (60, 15)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 8% signals spread compression, weak utilization, or input-cost pressure the company can't pass through.",
            ),
            SectorRedFlag(
                condition="volume_growth_yoy < -5",
                severity="HIGH",
                title="Volume Decline",
                description="Negative volume growth signals demand weakness or capacity under-absorption, not just price-led revenue softness.",
            ),
            SectorRedFlag(
                condition="utilization_pct < 60",
                severity="MEDIUM",
                title="Low Capacity Utilization",
                description="Utilization below 60% leaves fixed costs under-absorbed — margin pressure until demand or capacity discipline improves.",
            ),
            SectorRedFlag(
                condition="inventory_days > 120",
                severity="MEDIUM",
                title="High Inventory",
                description="Inventory above 120 days signals slow-moving finished goods or raw-material buildup — working-capital and write-down risk.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="MEDIUM",
                title="Elevated Leverage",
                description="D/E above 1.5x is high for textiles — capacity expansion or working-capital funding through debt raises cycle-downturn risk.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 3",
                severity="HIGH",
                title="Slow Revenue Growth",
                description="Revenue CAGR below 3% suggests demand stagnation, market-share loss, or a prolonged cycle downturn.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "volume_growth_yoy < -5":
            v = metrics.get("volume_growth_yoy"); return v is not None and v < -5
        if cond == "utilization_pct < 60":
            v = metrics.get("utilization_pct"); return v is not None and v < 60
        if cond == "inventory_days > 120":
            v = metrics.get("inventory_days"); return v is not None and v > 120
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "revenue_cagr_3y < 3":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 3
        return False
