"""
Commercial / business / engineering services framework (Services -> Services
spec, sections 2.1, 2.2, 2.4, 6, 9).

Covers NSE basic industries that previously fell through to Generic: Diversified
Commercial Services (staffing, facility management, cash logistics, co-working),
BPO/KPO, Trading & Distributors, Transport Related Services. Transport operators,
ports/roads/airports keep their dedicated frameworks (Logistics, Aviation,
Infrastructure); all four share the `svc` quarterly extraction prefix.

Labour-intensive economics (spec 6.2): headcount, attrition, utilisation, contract order
book (revenue/employee and wage cost are not disclosed comparably, so left out). Only what filings state is captured; headcount and
attrition come from the quarterly engine (`qtr_svc_*`) through the ledger bridge.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class ServicesSector(SectorFramework):
    sector_name = "Services"
    sector_aliases = [
        "Commercial Services", "Business Support Services", "Staffing", "Facility Management",
        "Outsourcing", "Business Process Outsourcing", "Professional Services",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.21,
        "cash_flow": 0.20,
        "balance_sheet": 0.19,
        "efficiency": 0.12,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high", "higher_is_better", "%",
                "Contract wins and volume growth — services revenue compounds with client mining",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "medium", "higher_is_better", "%",
                "Earnings growth — operating leverage on a largely fixed delivery base",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (28, 100)],
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high", "higher_is_better", "%",
                "Asset-light contract services run 8-25%; staffing sits at the low end (wage pass-through)",
                thresholds=[(2, 8), (5, 28), (8, 45), (12, 62), (17, 78), (22, 92), (28, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.14, "high", "higher_is_better", "%",
                "Capital efficiency — asset-light services should clear 20%+",
                thresholds=[(0, 5), (8, 22), (14, 45), (20, 65), (26, 82), (34, 94), (42, 100)],
            ),
            SectorMetric(
                "receivable_days", "Receivable Days", 0.10, "high", "lower_is_better", "days",
                "Collection discipline — government/enterprise clients stretch payments (spec 6.3)",
                thresholds=[(20, 100), (40, 85), (60, 68), (80, 48), (100, 28), (130, 10), (170, 0)],
            ),
            SectorMetric(
                "working_capital_days", "Working Capital Days", 0.08, "high", "lower_is_better", "days",
                "Net working capital days — labour-intensive contracts pay wages before clients pay",
                thresholds=[(10, 100), (30, 85), (55, 68), (80, 48), (110, 28), (150, 10), (200, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "high", "lower_is_better", "x",
                "Leverage — asset-light services should be lightly geared",
                thresholds=[(0, 100), (0.2, 88), (0.5, 72), (0.8, 55), (1.2, 35), (1.8, 15), (2.5, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.10, "high", "higher_is_better", "%",
                "Revenue growth without cash is a spec red flag (bad-growth pattern 2)",
                thresholds=[(0, 10), (25, 30), (45, 50), (65, 68), (80, 82), (95, 93), (110, 100)],
            ),
            SectorMetric(
                "headcount", "Headcount", 0.0, "low", "neutral", "units",
                "Employees at quarter end — the scale driver of a labour-intensive service; display only",
                available_from_yfinance=False,
                na_message="Stated by staffing/BPO issuers in results releases and decks",
            ),
            SectorMetric(
                "attrition_rate", "Attrition Rate (LTM)", 0.0, "low", "lower_is_better", "%",
                "Employee attrition — wage inflation and productivity risk; display only",
                available_from_yfinance=False,
                na_message="Stated by some BPO/staffing issuers",
            ),
            SectorMetric(
                "order_book_to_revenue", "Order Book / Revenue", 0.0, "low", "neutral", "x",
                "Contracted order book cover — display only; engineering services (spec 9.1)",
                available_from_yfinance=False,
                na_message="Only contract/engineering-services issuers state an order book",
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "medium", "neutral", "x",
                "Services P/E — asset-light compounders 25-40x; low-margin distribution 10-18x",
                thresholds=[(0, 45), (10, 65), (18, 82), (28, 78), (38, 60), (55, 38), (80, 15)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "medium", "neutral", "x",
                "Enterprise multiple — 10-22x for quality services names",
                thresholds=[(0, 55), (6, 78), (10, 90), (16, 80), (22, 62), (30, 40), (42, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(condition="receivable_days > 120", severity="HIGH", title="Stretched Receivables",
                          description="Receivables above 120 days — revenue is outrunning collections (spec bad-growth pattern 6)."),
            SectorRedFlag(condition="fcf_to_pat < 20", severity="MEDIUM", title="Weak Cash Conversion",
                          description="FCF below 20% of PAT — profit is not turning into cash."),
            SectorRedFlag(condition="debt_to_equity > 1.5", severity="HIGH", title="High Leverage",
                          description="D/E above 1.5x for an asset-light service business."),
            SectorRedFlag(condition="roce < 10", severity="MEDIUM", title="Low Capital Returns",
                          description="ROCE below 10% — the model is not earning its capital."),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        conds = {
            "receivable_days > 120": lambda m: (m.get("receivable_days") or 0) > 120,
            "fcf_to_pat < 20": lambda m: m.get("fcf_to_pat") is not None and m["fcf_to_pat"] < 20,
            "debt_to_equity > 1.5": lambda m: (m.get("debt_to_equity") or 0) > 1.5,
            "roce < 10": lambda m: m.get("roce") is not None and m["roce"] < 10,
        }
        fn = conds.get(rule.condition)
        return bool(fn and fn(metrics))
