"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Pharma / Healthcare sector framework — PROMPT.md Section 19.
Covers pharmaceuticals, specialty pharma, drug manufacturers, CROs, CMOs.

Key metrics per spec:
R&D/revenue, ANDA/product pipeline, domestic/international revenue mix,
regulated-market exposure %, product concentration, regulatory risk flags
(FDA 483s, import alerts), ROCE, FCF, debt.

Most pipeline/regulatory metrics are NOT available from yfinance.

Updated 2026-09-20 (Healthcare pass):
* FIXED naming drift — `rd_to_revenue` -> `rd_to_revenue_pct`, and the
  never-populated `domestic_revenue_pct` replaced by `export_revenue_pct`:
  the Annual Report Extraction Engine writes exactly `rd_to_revenue_pct` and
  `export_revenue_pct` (rd_expenditure / revenue_geography areas, universal),
  but this framework asked for differently-named metrics, so those real
  extractions could never reach the ledger bridge or the score. Same class of
  bug Automobile had.
* ADDED hospital metrics `bed_occupancy_pct` and `arpob` (MD spec sections
  4-5; N/A for pharma-only companies, which normalises out of the score).
  Quarterly extraction for occupancy/ARPOB/US-share is built but live-
  unvalidated — see quarterly_operating_metrics_ingestion.py.
* Still NA: `anda_pipeline`, `fda_483_count` (FDA sources, not filings we
  ingest) and `us_revenue_pct` at annual granularity.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag

# Real NSE basic_industry values under the Healthcare sector (confirmed live
# via DB query, 2026-09) — this framework spans both drugmakers/device
# manufacturers and hospital operators, whose operating metrics don't
# overlap at all (a hospital has no ANDA pipeline; a drugmaker has no bed
# occupancy). Used as `applicable_to` on the metrics below so
# `key_metrics_for(basic_industry)` can omit an entire sub-type's metrics
# for the other, instead of showing them as a permanent "Not disclosed".
_PHARMA_MANUFACTURING_TYPES = ["Pharmaceuticals", "Biotechnology", "Medical Equipment & Supplies"]
_HOSPITAL_TYPES = ["Hospital", "Healthcare Service Provider"]


class PharmaSector(SectorFramework):
    sector_name = "Healthcare"
    sector_aliases = [
        "Healthcare", "Pharmaceuticals", "Pharma", "Pharmaceutical",
        "Drugs", "Drug Manufacturer", "Hospital", "Medical Device",
        "CRO", "CDMO", "CMO", "Diagnostics",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.25,
        "profitability": 0.22,
        "cash_flow": 0.20,
        "balance_sheet": 0.17,
        "efficiency": 0.10,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth ────────────────────────────────────────────────────────
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth over 3 years — reflects new launches and market penetration",
                thresholds=[(0, 15), (3, 30), (6, 48), (10, 65), (14, 80), (18, 92), (22, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Earnings growth — pharma earnings can be lumpy due to one-time product launches",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
            ),
            # ── NOT available from yfinance ───────────────────────────────────
            SectorMetric(
                "rd_to_revenue_pct", "R&D / Revenue", 0.12, "high",
                "higher_is_better", "%",
                "R&D as % of revenue — 6-10% for innovative pharma; 3-5% for generic players",
                thresholds=[(0, 10), (2, 30), (4, 52), (6, 70), (8, 84), (10, 94), (14, 100)],
                available_from_yfinance=False,
                na_message="R&D spend from the annual report (Annual Report Extraction Engine, rd_expenditure area)",
                applicable_to=_PHARMA_MANUFACTURING_TYPES,
            ),
            SectorMetric(
                "anda_pipeline", "ANDA / Product Pipeline", 0.10, "high",
                "higher_is_better", "count",
                "Pending ANDAs or product pipeline count — reflects future US generics revenue visibility",
                thresholds=[(5, 20), (10, 40), (20, 60), (40, 76), (70, 88), (100, 96), (150, 100)],
                available_from_yfinance=False,
                na_message="ANDA pipeline data from FDA GDUFA database and company filings",
                applicable_to=_PHARMA_MANUFACTURING_TYPES,
            ),
            SectorMetric(
                "us_revenue_pct", "US/Regulated Market Revenue %", 0.10, "high",
                "higher_is_better", "%",
                "Revenue from US/EU/Japan (regulated markets) as % of total — premium-priced, higher margin",
                thresholds=[(5, 20), (15, 38), (25, 55), (35, 70), (45, 82), (55, 92), (65, 100)],
                available_from_yfinance=False,
                na_message="Geographic revenue split requires segment reporting from annual reports",
                applicable_to=_PHARMA_MANUFACTURING_TYPES,
            ),
            SectorMetric(
                "export_revenue_pct", "Export Revenue %", 0.06, "medium",
                "neutral", "%",
                "Export/international revenue as % of total — replaces the old `domestic_revenue_pct` (its "
                "complement) so the Annual Report Extraction Engine's directly-computed `export_revenue_pct` "
                "actually reaches the score; ~40-70% typical for generics exporters, low for India-focused branded pharma",
                thresholds=[(0, 60), (15, 72), (30, 80), (45, 78), (60, 70), (75, 60), (90, 50)],
                available_from_yfinance=False,
                na_message="Domestic vs export split from the annual report (revenue_geography area)",
                applicable_to=_PHARMA_MANUFACTURING_TYPES,
            ),
            # ── Hospitals (MD spec section 4/5: this framework spans hospitals as well as pharma; ──
            # ── N/A for pharma-only companies, which normalises out of the score) ────────────────
            SectorMetric(
                "bed_occupancy_pct", "Bed Occupancy", 0.08, "high",
                "higher_is_better", "%",
                "Occupied beds / operational beds — hospital utilisation; ~60-70% is healthy, above 75% signals capacity constraint",
                thresholds=[(35, 10), (45, 30), (55, 52), (62, 68), (68, 82), (74, 92), (80, 100)],
                available_from_yfinance=False,
                na_message="Hospital operators report occupancy in quarterly presentations; N/A for pharma/devices",
                applicable_to=_HOSPITAL_TYPES,
            ),
            SectorMetric(
                "arpob", "ARPOB (INR / occupied bed / day)", 0.08, "high",
                "higher_is_better", "INR",
                "Average revenue per occupied bed per day — pricing power x case mix; the core hospital unit-economics figure",
                thresholds=[(20000, 15), (30000, 35), (45000, 55), (60000, 72), (75000, 85), (90000, 95), (110000, 100)],
                available_from_yfinance=False,
                na_message="Hospital operators report ARPOB in quarterly presentations; N/A for pharma/devices",
                applicable_to=_HOSPITAL_TYPES,
            ),
            SectorMetric(
                "alos_days", "Average Length of Stay (days)", 0.04, "low",
                "neutral", "days",
                "Days per in-patient stay — falling ALOS lifts ARPOB/turnover but a mix effect (day-care, robotics) "
                "as much as efficiency; 2.6-3.6 typical for tertiary chains",
                thresholds=[(2.0, 60), (2.6, 80), (3.2, 88), (3.8, 75), (4.6, 50), (6.0, 25)],
                available_from_yfinance=False,
                na_message="Hospital operators report ALOS in quarterly filings; N/A for pharma/devices",
                applicable_to=_HOSPITAL_TYPES,
            ),
            SectorMetric(
                "arpp", "ARPP (INR / in-patient)", 0.0, "low",
                "neutral", "INR",
                "Average revenue per in-patient — display only: definitions differ by company (which revenue is "
                "excluded) so it is not scored across companies",
                available_from_yfinance=False,
                na_message="Hospital operators report ARPP in quarterly filings; N/A for pharma/devices",
                applicable_to=_HOSPITAL_TYPES,
            ),
            SectorMetric(
                "operational_beds", "Operational Beds", 0.0, "low",
                "neutral", "count",
                "Operational bed count — capacity base for occupancy and ARPOB; display only, not scored",
                available_from_yfinance=False,
                na_message="Hospital operators report bed counts in quarterly filings; N/A for pharma/devices",
                applicable_to=_HOSPITAL_TYPES,
            ),
            SectorMetric(
                "fda_483_count", "FDA 483 Observations (last 3Y)", 0.08, "high",
                "lower_is_better", "count",
                "Regulatory observations from FDA inspections — lower is better; 0 is ideal",
                thresholds=[(0, 100), (1, 82), (3, 60), (5, 40), (8, 20), (12, 5)],
                available_from_yfinance=False,
                na_message="FDA 483/warning letters tracked via FDA website; not in financial statements",
                applicable_to=_PHARMA_MANUFACTURING_TYPES,
            ),
            # ── Profitability (available) ─────────────────────────────────────
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "EBITDA margin — branded pharma 25-35%; generic 15-25%; CDMO 20-30%",
                thresholds=[(5, 10), (10, 28), (15, 50), (20, 68), (25, 82), (30, 93), (35, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.08, "medium",
                "higher_is_better", "%",
                "Net margin — 10-20% typical for quality pharma companies",
                thresholds=[(0, 5), (5, 22), (8, 42), (12, 62), (16, 78), (20, 90), (25, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital returns — 18-25%+ for quality pharma; CDMOs may have lower ROCE",
                thresholds=[(0, 5), (8, 22), (14, 45), (18, 62), (22, 78), (28, 90), (35, 100)],
            ),
            SectorMetric(
                "roic", "ROIC", 0.08, "high",
                "higher_is_better", "%",
                "Return on invested capital including R&D amortization",
                thresholds=[(0, 5), (8, 22), (14, 45), (18, 62), (22, 78), (28, 90), (35, 100)],
            ),
            # ── Cash Flow ─────────────────────────────────────────────────────
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.10, "high",
                "higher_is_better", "%",
                "Cash conversion — pharma should convert 60-80%+ of PAT to FCF",
                thresholds=[(0, 5), (25, 22), (45, 42), (60, 62), (75, 78), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "capex_to_revenue", "CapEx / Revenue", 0.06, "medium",
                "lower_is_better", "%",
                "CapEx intensity — watch for heavy API plant builds reducing FCF",
                thresholds=[(2, 100), (4, 88), (6, 72), (8, 55), (10, 38), (14, 18), (20, 0)],
            ),
            # ── Balance Sheet ─────────────────────────────────────────────────
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "medium",
                "lower_is_better", "x",
                "Leverage — pharma should be conservatively financed; above 0.5x warrants scrutiny",
                thresholds=[(0, 100), (0.2, 88), (0.4, 72), (0.6, 55), (0.8, 38), (1.2, 18), (2.0, 0)],
            ),
            # ── Valuation ─────────────────────────────────────────────────────
            SectorMetric(
                "pe_ratio", "P/E", 0.07, "medium",
                "neutral", "x",
                "P/E — branded pharma commands 25-40x; generics 15-25x",
                thresholds=[(0, 45), (10, 65), (18, 82), (28, 78), (38, 62), (55, 40), (80, 18)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.05, "medium",
                "neutral", "x",
                "Enterprise multiple — 12-20x typical for quality pharma",
                thresholds=[(0, 55), (8, 78), (12, 88), (18, 78), (24, 60), (32, 38), (45, 15)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_margin < 12",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 12% for a pharma company suggests severe pricing pressure, quality issues, or high R&D burn without returns.",
            ),
            SectorRedFlag(
                condition="rd_to_revenue_pct < 3",
                severity="MEDIUM",
                title="Very Low R&D Spend",
                description="R&D below 3% of revenue suggests a pure generics play with no innovation pipeline — competitive vulnerability.",
            ),
            SectorRedFlag(
                condition="fda_483_count > 5",
                severity="HIGH",
                title="Multiple FDA Observations",
                description="5+ FDA 483 observations in 3 years indicates systemic manufacturing quality issues — import alert risk.",
            ),
            SectorRedFlag(
                condition="roce < 12",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 12% in pharma may indicate R&D or capex not yet generating returns — monitor timeline.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.0",
                severity="HIGH",
                title="High Leverage for Pharma",
                description="D/E above 1x for a pharma company is elevated given lumpy product revenues and regulatory risk.",
            ),
            SectorRedFlag(
                condition="fcf_to_pat < 40",
                severity="MEDIUM",
                title="Low Cash Conversion",
                description="FCF/PAT below 40% suggests heavy capex cycle or working capital buildup — earnings quality concern.",
            ),
            SectorRedFlag(
                condition="bed_occupancy_pct < 50",
                severity="MEDIUM",
                title="Low Bed Occupancy",
                description="Occupancy below 50% leaves a hospital's fixed cost base under-absorbed — expansion into weak demand or share loss.",
            ),
            SectorRedFlag(
                condition="us_revenue_pct < 10",
                severity="LOW",
                title="Minimal Regulated Market Exposure",
                description="Less than 10% US/regulated market revenue limits premium-pricing opportunity and growth potential.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_margin < 12":
            v = metrics.get("ebitda_margin"); return v is not None and v < 12
        if cond == "rd_to_revenue_pct < 3":
            v = metrics.get("rd_to_revenue_pct"); return v is not None and v < 3
        if cond == "fda_483_count > 5":
            v = metrics.get("fda_483_count"); return v is not None and v > 5
        if cond == "roce < 12":
            v = metrics.get("roce"); return v is not None and v < 12
        if cond == "debt_to_equity > 1.0":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.0
        if cond == "fcf_to_pat < 40":
            v = metrics.get("fcf_to_pat"); return v is not None and v < 40
        if cond == "bed_occupancy_pct < 50":
            v = metrics.get("bed_occupancy_pct"); return v is not None and v < 50
        if cond == "us_revenue_pct < 10":
            v = metrics.get("us_revenue_pct"); return v is not None and v < 10
        return False
