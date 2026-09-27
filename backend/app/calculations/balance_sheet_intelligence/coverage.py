"""Data Availability / Coverage Audit (spec §54-56) — explicitly mandatory.
Walks a hardcoded dependency graph (spec §55's literal examples) and
assigns each tracked metric one of the spec's 7 statuses. This is the
single most important module for honesty in this whole package: it's the
one place that makes every gap in the source-of-truth table visible to the
UI/PDF/LLM rather than silently absent.
"""
from __future__ import annotations

from app.calculations.balance_sheet_intelligence.canonical_fields import STRUCTURALLY_ABSENT

_VALID_STATUSES = {"AVAILABLE", "CALCULABLE", "PARTIAL", "MISSING_INPUT", "SOURCE_REQUIRED", "NOT_APPLICABLE", "INVALID"}

# metric -> (dependencies, present-status, missing-status). `dependencies`
# are keys looked up in the `facts` dict passed to `compute_coverage_audit`
# — every one of them must be present (not None) for the metric to count
# as fully AVAILABLE; some present + some missing is PARTIAL.
_DEPENDENCY_GRAPH: dict[str, tuple[tuple[str, ...], str, str]] = {
    "cash": (("cash",), "AVAILABLE", "MISSING_INPUT"),
    "receivables": (("receivables",), "AVAILABLE", "MISSING_INPUT"),
    "inventory": (("inventory",), "AVAILABLE", "MISSING_INPUT"),
    "payables": (("payables",), "AVAILABLE", "MISSING_INPUT"),
    "debt": (("borrowings",), "AVAILABLE", "MISSING_INPUT"),
    "cwip": (("capital_work_in_progress",), "AVAILABLE", "MISSING_INPUT"),
    "net_worth": (("equity_capital", "reserves"), "AVAILABLE", "MISSING_INPUT"),
    "accounting_integrity": (("total_assets", "total_liabilities"), "AVAILABLE", "MISSING_INPUT"),
    "common_size": (("total_assets",), "AVAILABLE", "MISSING_INPUT"),
    "debt_to_equity": (("borrowings", "equity_capital", "reserves"), "AVAILABLE", "MISSING_INPUT"),
    "liabilities_to_equity": (("total_liabilities", "equity_capital", "reserves"), "AVAILABLE", "MISSING_INPUT"),
    "net_debt": (("borrowings", "cash"), "CALCULABLE", "PARTIAL"),
    "inventory_turnover": (("cogs", "inventory"), "CALCULABLE", "MISSING_INPUT"),  # cogs is STRUCTURALLY_ABSENT -> always MISSING_INPUT
    # Only the input the PROXY formula actually uses gates PARTIAL vs
    # MISSING_INPUT below (`_ALWAYS_PARTIAL_PROXY` handling) — "credit_sales"/
    # "credit_purchases" are never in `facts` (nothing computes them) and
    # are listed here purely as the spec's PREFERRED-but-absent input, not
    # something whose absence should downgrade this to MISSING_INPUT.
    "dso": (("receivables",), "CALCULABLE", "PARTIAL"),
    "dio": (("inventory",), "CALCULABLE", "PARTIAL"),
    "dpo": (("payables",), "CALCULABLE", "PARTIAL"),
    "ccc": (("receivables", "inventory", "payables"), "CALCULABLE", "PARTIAL"),
    "current_ratio": (("current_assets", "current_liabilities"), "AVAILABLE", "MISSING_INPUT"),
    "quick_ratio": (("cash", "receivables", "current_liabilities"), "AVAILABLE", "MISSING_INPUT"),
    "cash_ratio": (("cash", "current_liabilities"), "AVAILABLE", "MISSING_INPUT"),
    "roce": (("total_assets", "current_liabilities", "ebit"), "CALCULABLE", "MISSING_INPUT"),
    "interest_coverage": (("ebit", "interest_expense"), "AVAILABLE", "MISSING_INPUT"),
    # Genuinely obtainable now (2026-09-16) via NSE annual-report extraction
    # (`app/ingestion/annual_report_ingestion.py`'s "ppe"/"other_liabilities"
    # areas) — real dependency checks, not `_ALWAYS_ABSENT`. Still commonly
    # MISSING_INPUT in practice: the annual-report ingestion stage may not
    # have run yet for this company, NSE may not have this filing, or the
    # company may genuinely not disclose the field by a recognizable label
    # — `facts` only has a value once that extraction has actually
    # succeeded for this specific company.
    "gross_ppe": (("gross_ppe",), "AVAILABLE", "MISSING_INPUT"),
    "accrued_expenses": (("accrued_expenses",), "AVAILABLE", "MISSING_INPUT"),
    "deferred_revenue": (("deferred_revenue",), "AVAILABLE", "MISSING_INPUT"),
    # These 6 always resolve via `_ALWAYS_ABSENT` below regardless of
    # `facts` — the "status" values in these tuples are never actually
    # read (documented here only so the metric appears in the graph at
    # all); the real status each produces is SOURCE_REQUIRED in every case.
    # Unlike gross_ppe/accrued_expenses/deferred_revenue above, no source
    # this app ingests carries these at all yet, even in principle.
    "ar_aging": ((), "SOURCE_REQUIRED", "SOURCE_REQUIRED"),
    "inventory_aging": ((), "SOURCE_REQUIRED", "SOURCE_REQUIRED"),
    "ap_aging": ((), "SOURCE_REQUIRED", "SOURCE_REQUIRED"),
    "debt_maturity": ((), "SOURCE_REQUIRED", "SOURCE_REQUIRED"),
    "related_party_loans": ((), "SOURCE_REQUIRED", "SOURCE_REQUIRED"),
    "contingent_liabilities": ((), "SOURCE_REQUIRED", "SOURCE_REQUIRED"),
}

# Metrics that always resolve to SOURCE_REQUIRED regardless of `facts` — no
# dependency check needed, they're structurally absent (need an annual-
# report note disclosure or a data point no source this app has reports at
# all, not merely one missing field in an otherwise-computable formula).
_ALWAYS_ABSENT = {
    "ar_aging": "ar_aging", "inventory_aging": "inventory_aging", "ap_aging": "ap_aging",
    "debt_maturity": "debt_maturity_schedule", "related_party_loans": "related_party_loans",
    "contingent_liabilities": "contingent_liabilities",
}
# Metrics whose formula uses a documented proxy (not the spec's literal
# preferred inputs) — always PARTIAL, never AVAILABLE, regardless of facts.
_ALWAYS_PARTIAL_PROXY = {"dso", "dio", "dpo", "ccc"}
_ALWAYS_MISSING_PROXY = {"inventory_turnover"}  # needs cogs, structurally absent

# Sourced from NSE annual-report extraction (app/ingestion/
# annual_report_ingestion.py's "ppe"/"other_liabilities" areas), not a
# recurring quarterly/API feed — when missing it's specifically because
# that extraction hasn't produced a value for this company yet (stage
# hasn't run, NSE has no filing on file, or this company doesn't disclose
# the field under a recognizable label), not because no source could ever
# supply it. A generic "Missing: gross_ppe" reason wouldn't tell the user
# that re-running the analysis (or waiting for the next NSE filing cycle)
# is a real path to closing the gap, unlike the truly structural absences
# below.
_ANNUAL_REPORT_SOURCED = {
    "gross_ppe": "Extracted from the NSE annual report's PPE note when available — not yet "
                 "ingested for this company, or the note doesn't disclose a Total column.",
    "accrued_expenses": "Extracted from the NSE annual report's Other Liabilities note when "
                         "available — not yet ingested for this company, or this company doesn't "
                         "disclose accrued expenses as a distinct line separate from other payables.",
    "deferred_revenue": "Extracted from the NSE annual report's Other Liabilities note when "
                         "available — not yet ingested for this company, or this company doesn't "
                         "disclose deferred revenue/contract liabilities as a distinct line.",
}


def compute_coverage_audit(facts: dict, is_inventory_material: bool = True, sector_name: str | None = None) -> dict:
    """`facts` is a flat {field: value_or_None} dict the orchestrator
    assembles from every source this package reads (Screener balance sheet,
    yfinance blend, cash flow). Returns {metric: {"status", "reason",
    "dependencies"}} plus a summary count per status.

    `is_inventory_material=False` (sector_routing.is_inventory_material(),
    2026-09-20) relabels `inventory_turnover` NOT_APPLICABLE instead of
    MISSING_INPUT — the underlying data (COGS) is equally unavailable for
    every sector (STRUCTURALLY_ABSENT), but for a hospital/IT/services
    company that absence isn't a real analytical gap the way it is for a
    retailer or manufacturer, so it shouldn't count against coverage_pct or
    appear in top_source_gaps() as something worth chasing down."""
    results: dict[str, dict] = {}
    for metric, (deps, present_status, missing_status) in _DEPENDENCY_GRAPH.items():
        if metric in _ALWAYS_ABSENT:
            results[metric] = {
                "status": "SOURCE_REQUIRED",
                "reason": STRUCTURALLY_ABSENT[_ALWAYS_ABSENT[metric]],
                "dependencies": list(deps),
            }
            continue
        if metric in _ALWAYS_MISSING_PROXY:
            if not is_inventory_material:
                results[metric] = {
                    "status": "NOT_APPLICABLE",
                    "reason": f"Inventory Turnover (COGS / Average Inventory) isn't a materially relevant metric for "
                              f"a {sector_name or 'this'} business — inventory is not a core part of this sector's "
                              f"balance sheet story, even where a small inventory line genuinely exists.",
                    "dependencies": list(deps),
                }
                continue
            results[metric] = {
                "status": "MISSING_INPUT",
                "reason": STRUCTURALLY_ABSENT.get("credit_sales", "Required input has no source."),
                "dependencies": list(deps),
            }
            continue

        present = [d for d in deps if facts.get(d) is not None]
        missing = [d for d in deps if facts.get(d) is None]

        if metric in _ALWAYS_PARTIAL_PROXY:
            status = "PARTIAL" if not missing else "MISSING_INPUT"
            reason = "Uses a documented closing-balance/total-revenue proxy, not the spec's preferred average-balance/credit-sales formula." if status == "PARTIAL" else f"Missing: {', '.join(missing)}"
        elif not missing:
            status = present_status
            reason = None
        elif present:
            status = "PARTIAL"
            reason = f"Missing: {', '.join(missing)}"
        elif metric in _ANNUAL_REPORT_SOURCED:
            status = missing_status
            reason = _ANNUAL_REPORT_SOURCED[metric]
        else:
            status = missing_status
            reason = f"Missing: {', '.join(missing)}"

        results[metric] = {"status": status, "reason": reason, "dependencies": list(deps)}

    summary = {status: 0 for status in _VALID_STATUSES}
    for r in results.values():
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    # NOT_APPLICABLE metrics (e.g. Inventory Turnover for a hospital) are
    # excluded from both the numerator and denominator — they're not a gap
    # to weigh "what's available" against, so `total_metrics`/`coverage_pct`
    # reflect "how much of what's relevant to THIS company is available",
    # not "how much of a one-size-fits-all universal checklist".
    not_applicable = summary.get("NOT_APPLICABLE", 0)
    total = len(results) - not_applicable
    available_like = summary.get("AVAILABLE", 0) + summary.get("CALCULABLE", 0)
    coverage_pct = round(available_like / total * 100, 1) if total else 0.0

    return {"metrics": results, "summary": summary, "coverage_pct": coverage_pct,
            "total_metrics": total, "total_metrics_tracked": len(results)}


_GAP_PRIORITY = {
    "ar_aging": "HIGH", "inventory_aging": "HIGH", "ap_aging": "HIGH", "debt_maturity": "MEDIUM",
    "related_party_loans": "MEDIUM", "contingent_liabilities": "MEDIUM",
    "gross_ppe": "LOW", "accrued_expenses": "LOW", "deferred_revenue": "LOW",
}


def top_source_gaps(coverage: dict) -> list[dict]:
    """Ranked source-gap report (spec §56, §73) — every MISSING_INPUT/
    SOURCE_REQUIRED metric, ordered HIGH -> MEDIUM -> LOW priority, matching
    spec §56's own example ordering (aging first, debt maturity/related
    party next, everything else last)."""
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    gaps = [
        {"metric": metric, "status": r["status"], "reason": r["reason"], "priority": _GAP_PRIORITY.get(metric, "LOW")}
        for metric, r in coverage["metrics"].items()
        if r["status"] in ("MISSING_INPUT", "SOURCE_REQUIRED")
    ]
    return sorted(gaps, key=lambda g: order.get(g["priority"], 3))
