"""Standalone vs Consolidated engine (spec Stage 8) + subsidiary
contribution (Stage 9).

Uses `metric_store.get_both_statement_types()` — the exact existing
primitive built for this, previously unused by any P&L code. Only works
for periods where a company has been re-ingested under Milestone 1's dual
statement-type `ingest_pnl_history()` — for anything ingested before that
change, this correctly reports `UNAVAILABLE` rather than guessing (no
backfill migration is run as part of this rollout).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import BusinessSegment

# CSR interpretation bands — spec's own explicit numbers (Stage 8), stored
# as configurable constants per Rule 8.
_CSR_PRIMARILY_PARENT_MIN = 0.80
_CSR_MATERIAL_SUBSIDIARY_MIN = 0.50
_CSR_SIGNIFICANT_GROUP_MIN = 0.30
# below _CSR_SIGNIFICANT_GROUP_MIN => "CONSOLIDATED_STRUCTURE_DOMINATES"

# Conglomerate/SOTP heuristic (spec Stage 24) — the spec gives no exact
# segment-count/spread numbers either, so these are explicit, documented,
# configurable thresholds (Rule 8), not literal spec content.
_CONGLOMERATE_MIN_SEGMENTS = 3
# Real bug caught live-testing Maruti Suzuki (2026-09-15): counting every
# `BusinessSegment` row flagged it `is_conglomerate=True` off 9 rows, but 7
# of those ("Scrap", "Fiscal Incentive", "Export Promotion Capital Goods",
# ...) are trivial revenue sub-lines (<2.5% of revenue each), not real
# diversified business lines — "Vehicles" + "Spare Parts" alone are 93.4%
# of revenue. A materiality filter (segment must be >= this share of its
# fiscal year's total segment revenue to count) is required before the
# segment COUNT means anything for conglomerate detection.
_MATERIAL_SEGMENT_MIN_SHARE = 0.10


def _classify_csr(csr: float) -> str:
    if csr > _CSR_PRIMARILY_PARENT_MIN:
        return "PRIMARILY_PARENT_DOMESTIC"
    if csr >= _CSR_MATERIAL_SUBSIDIARY_MIN:
        return "MATERIAL_SUBSIDIARY_CONTRIBUTION"
    if csr >= _CSR_SIGNIFICANT_GROUP_MIN:
        return "SIGNIFICANT_GROUP_CONTRIBUTION"
    return "CONSOLIDATED_STRUCTURE_DOMINATES"


def _ratio(db: Session, company_id: str, metric_key: str, period: str) -> dict:
    """One metric's standalone/consolidated pair + ratio for one period."""
    both = metric_store.get_both_statement_types(db, company_id, metric_key, period)
    standalone_row, consolidated_row = both.get("STANDALONE"), both.get("CONSOLIDATED")
    standalone = float(standalone_row.value) if standalone_row and standalone_row.value is not None else None
    consolidated = float(consolidated_row.value) if consolidated_row and consolidated_row.value is not None else None

    if standalone is None or consolidated is None or consolidated == 0:
        return {"standalone": standalone, "consolidated": consolidated, "ratio": None,
                "confidence": "UNAVAILABLE"}

    ratio = round(standalone / consolidated, 4)
    return {"standalone": standalone, "consolidated": consolidated, "ratio": ratio, "confidence": "HIGH"}


def compute_csr(db: Session, company_id: str, period: str) -> dict:
    """CSR = Standalone Revenue / Consolidated Revenue, for one period.

    `consolidated_ever_reported` (2026-09-24, real gap found live on Kross
    Ltd — user's own report: "why is consolidated revenue not being
    injected, we have that in Screener right?"): confirmed live against
    Screener.in itself (both via `openscreener`'s parser, which returns 0
    rows, AND a direct HTTP fetch of the company's own `/consolidated/`
    page, which renders the full P&L/balance-sheet/cash-flow TABLE
    STRUCTURE but with zero populated data rows anywhere) that Kross
    genuinely has no consolidated financial statements on Screener at
    all — a single-entity manufacturer with no subsidiaries to
    consolidate, not a scrape/ingestion failure. `confidence:
    "UNAVAILABLE"` alone can't distinguish that genuine, permanent
    structural absence from an ordinary transient gap (e.g. this one
    period not yet ingested while other periods have real consolidated
    data) — both looked identical to any caller before this field existed.
    Checks the FULL history (every period, not just this one) so a company
    with consolidated data in some years but not this exact period still
    correctly reports `True`."""
    revenue = _ratio(db, company_id, "pnl_sales", period)
    csr = revenue["ratio"]
    consolidated_ever_reported = bool(
        metric_store.get_metric_history(db, company_id, "pnl_sales", statement_type="CONSOLIDATED")
    )
    return {
        "csr": csr,
        "csr_band": _classify_csr(csr) if csr is not None else None,
        "standalone_revenue": revenue["standalone"],
        "consolidated_revenue": revenue["consolidated"],
        "confidence": revenue["confidence"],
        "consolidated_ever_reported": consolidated_ever_reported,
    }


def compute_pat_structural_ratio(db: Session, company_id: str, period: str) -> dict:
    """Same ratio for PAT — the spec's companion metric to CSR."""
    pat = _ratio(db, company_id, "pnl_net_profit", period)
    return {
        "pat_structural_ratio": pat["ratio"],
        "standalone_pat": pat["standalone"],
        "consolidated_pat": pat["consolidated"],
        "confidence": pat["confidence"],
    }


def subsidiary_contribution(db: Session, company_id: str, period: str) -> dict:
    """Consolidated - Standalone, both as an absolute Cr figure and a share
    of consolidated revenue. If `BusinessSegment` rows exist for the
    company, their names/count are surfaced too (for narrative wording
    only — Stage 9 explicitly prefers real segment data over the
    standalone/consolidated delta approximation when it exists, but this
    never fabricates a segment-level PROFIT figure, since `BusinessSegment`
    has revenue only)."""
    revenue = _ratio(db, company_id, "pnl_sales", period)
    standalone, consolidated = revenue["standalone"], revenue["consolidated"]

    if standalone is None or consolidated is None or consolidated == 0:
        result = {"subsidiary_revenue": None, "subsidiary_revenue_share": None, "confidence": "UNAVAILABLE"}
    else:
        subsidiary_revenue = round(consolidated - standalone, 2)
        result = {
            "subsidiary_revenue": subsidiary_revenue,
            "subsidiary_revenue_share": round(subsidiary_revenue / consolidated, 4),
            "confidence": "MEDIUM",  # derived, not directly reported as one line
        }

    segments = db.query(BusinessSegment).filter_by(company_id=company_id).all()
    if segments:
        result["segment_names"] = sorted({s.segment_name for s in segments})
        result["segment_count"] = len(result["segment_names"])
    else:
        result["segment_names"] = []
        result["segment_count"] = 0

    return result


def flag_conglomerate(db: Session, company_id: str) -> dict:
    """Spec Stage 24: a company operating across enough distinct MATERIAL
    segments shouldn't get a simplistic single-sector P&L score. Only the
    latest fiscal year's segments are considered, and only those clearing
    `_MATERIAL_SEGMENT_MIN_SHARE` of that year's total segment revenue —
    without this filter, TradingView's segment breakdown includes trivial
    revenue sub-lines (scrap sales, fiscal incentives, freight recovery)
    that are not real diversified business lines (see the module-level
    comment for the real bug this fixed on Maruti Suzuki). Segment-SECTOR
    spread (are the segments actually different businesses, not just a
    product-line split within one business) isn't derivable from
    `BusinessSegment` either way — it has no sector/industry tag per
    segment, only a name — so `segment_sector_count` is approximated as
    equal to the material `segment_count`, a documented simplification, not
    a claim of true cross-sector detection. `sotp_required` never implies a
    fabricated per-segment MARGIN exists (`BusinessSegment` has revenue
    only) — it only means the consolidated P&L score should be labeled
    "interpret with SOTP" when surfaced downstream (Milestones 6-7)."""
    segments = db.query(BusinessSegment).filter_by(company_id=company_id).all()
    if not segments:
        return {"is_conglomerate": False, "segment_count": 0, "segment_sector_count": 0,
                "sotp_required": False, "segment_names": []}

    latest_year = max(s.fiscal_year for s in segments)
    latest_segments = [s for s in segments if s.fiscal_year == latest_year]
    total_revenue = sum(float(s.revenue) for s in latest_segments)

    material_names = sorted(
        s.segment_name for s in latest_segments
        if total_revenue > 0 and float(s.revenue) / total_revenue >= _MATERIAL_SEGMENT_MIN_SHARE
    )
    segment_count = len(material_names)
    is_conglomerate = segment_count >= _CONGLOMERATE_MIN_SEGMENTS
    return {
        "is_conglomerate": is_conglomerate,
        "segment_count": segment_count,
        "segment_sector_count": segment_count,  # approximation — see docstring
        "sotp_required": is_conglomerate,
        "segment_names": material_names,
    }
