"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Media & Entertainment sector framework.
Broadcasters, OTT platforms, print media, film studios, digital media, gaming.

`subscription_revenue_pct`, `subscriber_count_growth`,
`content_cost_to_revenue` and `arpu` below (all available_from_yfinance=
False) were checked live against the Quarterly Sector KPI Extraction
Engine (2026-09-20) and NOT filled — a genuine, structural gap, not an
oversight. None of the real subscription/OTT-relevant candidates in this
sector (Zee Entertainment, Sun TV Network, Nazara Technologies,
Network18) file ANY NSE "Investor Presentation" filing in a 120-day
lookback, so there is no quarterly document to extract from for this
sector today. Saregama (the one company that does file one with
loosely-relevant content) only has a bar-chart infographic with garbled
period/column ordering in raw text extraction — the same failure mode as
the rejected Ambuja Cement bar-chart page, so it was not targeted. See
`app/ingestion/quarterly_operating_metrics_ingestion.py`'s module
docstring for the full investigation.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class MediaSector(SectorFramework):
    sector_name = "Media & Entertainment"
    sector_aliases = [
        "Media", "Media & Entertainment", "Entertainment", "Broadcasting",
        "OTT", "Film", "Print Media", "Publishing", "Digital Media",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.27,
        "profitability": 0.23,
        "cash_flow": 0.21,
        "balance_sheet": 0.16,
        "efficiency": 0.08,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — advertising + subscription + content licensing",
                thresholds=[(0, 15), (3, 28), (6, 48), (10, 65), (14, 80), (18, 92), (22, 100)],
            ),
            SectorMetric(
                "subscription_revenue_pct", "Subscription Revenue %", 0.12, "high",
                "higher_is_better", "%",
                "Recurring subscription revenue as % of total — more predictable than ad revenue",
                thresholds=[(5, 15), (15, 32), (25, 50), (35, 65), (50, 80), (65, 92), (80, 100)],
                available_from_yfinance=False,
                na_message="Revenue mix (subscription vs ad) from company segment disclosures",
            ),
            SectorMetric(
                "subscriber_count_growth", "Subscriber Growth (YoY)", 0.10, "high",
                "higher_is_better", "%",
                "Paid subscriber / DAU growth — key for OTT and digital platforms",
                thresholds=[(-5, 0), (0, 20), (5, 40), (10, 60), (15, 76), (20, 88), (25, 100)],
                available_from_yfinance=False,
                na_message="Subscriber data from company quarterly disclosures",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "Broadcasters 25-40%; OTT in investment phase may be negative; mature content 20-35%",
                thresholds=[(0, 5), (8, 22), (14, 42), (20, 62), (28, 78), (35, 92), (45, 100)],
            ),
            SectorMetric(
                "content_cost_to_revenue", "Content Cost / Revenue", 0.10, "high",
                "lower_is_better", "%",
                "Content acquisition/production as % of revenue — key cost driver for OTT/broadcasters",
                thresholds=[(15, 100), (25, 85), (35, 68), (45, 50), (55, 32), (65, 15), (75, 0)],
                available_from_yfinance=False,
                na_message="Content cost breakdown from company disclosures",
            ),
            SectorMetric(
                "arpu", "ARPU (INR/month)", 0.08, "medium",
                "higher_is_better", "INR",
                "Average Revenue per User — reflects monetization quality of subscriber base",
                thresholds=[(30, 15), (60, 32), (100, 52), (150, 68), (200, 82), (300, 93), (500, 100)],
                available_from_yfinance=False,
                na_message="ARPU from company investor disclosures",
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital efficiency — media is asset-light; mature players should earn 20-35%+",
                thresholds=[(0, 5), (8, 22), (14, 45), (20, 62), (28, 78), (36, 90), (45, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "medium",
                "lower_is_better", "x",
                "Media should be conservatively financed; high content debt is risky",
                thresholds=[(0, 100), (0.2, 88), (0.4, 72), (0.6, 55), (0.8, 38), (1.2, 18), (2.0, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.10, "high",
                "higher_is_better", "%",
                "Cash conversion — content amortization inflates P&L; watch cash conversion carefully",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.08, "medium",
                "neutral", "x",
                "Media P/E — OTT growth companies 40-80x; mature broadcasters 12-22x",
                thresholds=[(0, 45), (10, 65), (20, 80), (32, 78), (50, 60), (75, 38), (120, 15)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "low",
                "neutral", "x",
                "Enterprise multiple — mature media 10-18x; growth OTT may not apply",
                thresholds=[(0, 55), (6, 78), (10, 88), (16, 80), (22, 60), (32, 38), (45, 15)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="subscriber_count_growth < -5",
                severity="HIGH",
                title="Subscriber Decline",
                description="Negative subscriber growth — platform losing relevance; revenue and ARPU risk.",
            ),
            SectorRedFlag(
                condition="content_cost_to_revenue > 60",
                severity="HIGH",
                title="Very High Content Cost",
                description="Content cost above 60% of revenue — unsustainable; leaves little room for profit.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 10",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 10% for a media company — advertising or subscription monetization is broken.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1",
                severity="MEDIUM",
                title="Elevated Leverage for Media",
                description="D/E above 1x for a media company signals content investment or acquisition debt — watch cash flow.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 5",
                severity="HIGH",
                title="Very Slow Growth",
                description="Revenue CAGR below 5% for media suggests structural decline (print) or subscriber growth plateau.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "subscriber_count_growth < -5":
            v = metrics.get("subscriber_count_growth"); return v is not None and v < -5
        if cond == "content_cost_to_revenue > 60":
            v = metrics.get("content_cost_to_revenue"); return v is not None and v > 60
        if cond == "ebitda_margin < 10":
            v = metrics.get("ebitda_margin"); return v is not None and v < 10
        if cond == "debt_to_equity > 1":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1
        if cond == "revenue_cagr_3y < 5":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 5
        return False
