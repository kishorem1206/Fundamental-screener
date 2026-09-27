"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Power / Utilities sector framework.
Generation (thermal, hydro), transmission, distribution, integrated power companies.
RenewableEnergySector inherits this (UtilitiesSector now lives in other_utilities.py).

Key metrics: PLF (plant load factor), heat rate, power purchase agreements, T&D losses,
receivables from DISCOMs, regulated vs merchant mix.

Quarterly operating metrics (`qtr_pow_*`: operational MW and YoY growth, thermal PLF, availability,
renewable CUF, generation MU, PPA share, transmission availability/ckm/MVA, distribution loss and
AT&C, collection efficiency, trading volume, capex, service-FCF margin) come from the Quarterly Sector
KPI Extraction Engine and reach scoring through the ledger bridge. Thermal PLF feeds `plf` only:
NSE files solar/wind developers (Adani Green, NTPC Green, ACME) under the same "Power Generation"
industry as coal utilities, so a CUF of ~25% must never be scored on the thermal PLF scale. Traps:
operational vs pipeline MW, gross vs net generation, MU vs BU, per-licence-area (not company-wide) loss
figures, annual (FY) figures inside quarterly decks.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class PowerSector(SectorFramework):
    sector_name = "Power"
    sector_aliases = [
        "Power", "Electric Utilities", "Power Generation",
        "Transmission", "Power Distribution", "Integrated Power",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.20,
        "profitability": 0.21,
        "cash_flow": 0.23,
        "balance_sheet": 0.22,
        "efficiency": 0.10,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.08, "medium",
                "higher_is_better", "%",
                "Revenue growth — regulated utilities have stable tariff-driven growth",
                thresholds=[(0, 15), (3, 28), (5, 45), (8, 62), (12, 78), (16, 90), (20, 100)],
            ),
            SectorMetric(
                "plf", "Plant Load Factor (PLF)", 0.14, "high",
                "higher_is_better", "%",
                "Thermal plant utilization — above 65% is efficient; below 50% is idle capacity",
                thresholds=[(30, 10), (45, 28), (55, 48), (65, 65), (72, 80), (80, 92), (88, 100)],
                available_from_yfinance=False,
                na_message="PLF from company quarterly disclosures and Central Electricity Authority",
            ),
            SectorMetric(
                "regulated_capacity_pct", "Regulated / PPA Revenue %", 0.10, "high",
                "higher_is_better", "%",
                "Revenue under long-term PPAs or regulated tariffs — lower merchant exposure = more stability",
                thresholds=[(30, 20), (45, 38), (60, 55), (70, 70), (80, 82), (90, 93), (100, 100)],
                available_from_yfinance=False,
                na_message="PPA / merchant revenue mix from company reports",
            ),
            SectorMetric(
                "td_losses", "T&D Losses (%)", 0.10, "high",
                "lower_is_better", "%",
                "Transmission & Distribution losses — below 15% is efficient; above 25% is poor",
                thresholds=[(8, 100), (12, 85), (15, 70), (18, 55), (22, 38), (28, 18), (35, 0)],
                available_from_yfinance=False,
                na_message="T&D loss data from utility regulatory filings",
            ),
            SectorMetric(
                "discom_receivables_days", "DISCOM Receivable Days", 0.08, "high",
                "lower_is_better", "days",
                "Days of outstanding receivables from state DISCOMs — high = payment delay risk",
                thresholds=[(30, 100), (60, 82), (90, 62), (120, 45), (180, 25), (240, 8)],
                available_from_yfinance=False,
                na_message="DISCOM receivables require segment receivables data from annual report",
            ),
            SectorMetric(
                "availability_pct", "Plant Availability", 0.0, "low",
                "neutral", "%",
                "Plant availability factor — declared capacity actually available to the grid — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by generators in results releases / operating updates",
            ),
            SectorMetric(
                "cuf_pct", "Renewable CUF", 0.0, "low",
                "neutral", "%",
                "Solar/wind capacity utilisation factor — replaces PLF for renewables (typically 20-35%) — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by renewable developers",
            ),
            SectorMetric(
                "transmission_availability_pct", "Transmission Availability", 0.0, "low",
                "neutral", "%",
                "Transmission system availability — the key operating metric of a transmission business — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by transmission companies",
            ),
            SectorMetric(
                "atc_loss_pct", "AT&C Loss", 0.0, "low",
                "neutral", "%",
                "Aggregate technical & commercial loss of a distribution business — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by distribution utilities",
            ),
            SectorMetric(
                "collection_efficiency_pct", "Collection Efficiency", 0.0, "low",
                "neutral", "%",
                "Share of billed revenue actually collected — distribution cash discipline — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by distribution utilities",
            ),
            SectorMetric(
                "capacity_growth_yoy", "Operational Capacity Growth (YoY)", 0.0, "low",
                "neutral", "%",
                "Growth of operational (not pipeline) MW — read against PLF/CUF and returns (spec: capacity growth without utilization is a bad-growth pattern) — display only, not scored",
                available_from_yfinance=False,
                na_message="Needs year-ago operational capacity in the same document",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "Power generation EBITDA 30-55%; transmission 60-75%; distribution 10-20%",
                thresholds=[(10, 10), (20, 30), (28, 50), (35, 68), (42, 82), (52, 93), (65, 100)],
            ),
            SectorMetric(
                "net_debt_to_ebitda", "Net Debt / EBITDA", 0.14, "high",
                "lower_is_better", "x",
                "Leverage — regulated utilities tolerate 3-5x; merchant generators <2.5x",
                thresholds=[(0, 100), (1, 88), (2, 75), (3, 60), (4, 42), (5, 22), (7, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Power companies are capital-intensive; regulated utilities can sustain 2-3x",
                thresholds=[(0, 100), (1, 85), (2, 70), (3, 52), (4, 32), (5, 15), (7, 0)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital efficiency — regulated returns 12-15%; merchant generators higher but riskier",
                thresholds=[(0, 5), (5, 20), (8, 42), (12, 62), (16, 78), (20, 90), (26, 100)],
            ),
            SectorMetric(
                "cfo_to_pat", "CFO / PAT", 0.10, "high",
                "higher_is_better", "%",
                "Operating cash conversion — regulated utilities should convert 80-100%+",
                thresholds=[(20, 10), (40, 28), (60, 48), (80, 68), (90, 82), (100, 92), (120, 100)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "low",
                "neutral", "x",
                "Power sector trades 7-14x; regulated utilities command premium",
                thresholds=[(0, 55), (4, 75), (6, 88), (10, 82), (14, 65), (20, 42), (28, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="plf < 50",
                severity="HIGH",
                title="Very Low Plant Load Factor",
                description="PLF below 50% means the thermal plant is significantly underutilized — fixed cost burden without revenue.",
            ),
            SectorRedFlag(
                condition="discom_receivables_days > 180",
                severity="HIGH",
                title="Very High DISCOM Receivables",
                description="DISCOM receivables above 180 days signals state-level payment default risk — cash flow crunch likely.",
            ),
            SectorRedFlag(
                condition="net_debt_to_ebitda > 5",
                severity="HIGH",
                title="Dangerous Leverage",
                description="Net Debt/EBITDA above 5x — any tariff revision delay or PLF drop can cause debt service stress.",
            ),
            SectorRedFlag(
                condition="td_losses > 25",
                severity="MEDIUM",
                title="Very High T&D Losses",
                description="T&D losses above 25% indicate poor infrastructure or high pilferage — margin leakage at scale.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 20",
                severity="MEDIUM",
                title="Low EBITDA Margin for Power",
                description="EBITDA below 20% for a generation company indicates fuel cost squeeze or low merchant realization.",
            ),
            SectorRedFlag(
                condition="roce < 8",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 8% for a power company suggests assets are not earning their cost of capital.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "plf < 50":
            v = metrics.get("plf"); return v is not None and v < 50
        if cond == "discom_receivables_days > 180":
            v = metrics.get("discom_receivables_days"); return v is not None and v > 180
        if cond == "net_debt_to_ebitda > 5":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and v > 5
        if cond == "td_losses > 25":
            v = metrics.get("td_losses"); return v is not None and v > 25
        if cond == "ebitda_margin < 20":
            v = metrics.get("ebitda_margin"); return v is not None and v < 20
        if cond == "roce < 8":
            v = metrics.get("roce"); return v is not None and v < 8
        return False


class RenewableEnergySector(PowerSector):
    """Solar, wind, green energy — growth focus, CUF replaces PLF, green PPAs."""
    sector_name = "Renewable Energy"
    sector_aliases = [
        "Renewable Energy", "Solar", "Wind Energy", "Green Energy",
        "Renewables", "Clean Energy", "Solar Power",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.26,
        "profitability": 0.19,
        "cash_flow": 0.21,
        "balance_sheet": 0.20,
        "efficiency": 0.10,
        "valuation": 0.04,
    }
