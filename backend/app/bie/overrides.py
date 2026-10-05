"""Phase 4.5 — the analyst's control over the model's assumptions.

The system's estimates stay the default. An override names one assumption
(a segment's growth or margin in a year and scenario, or a company-level
input such as the tax rate) and replaces it; everything downstream is
recomputed. Overrides carry a mandatory reason, are never edited in place,
and are written only through `set_override` — nothing automated calls it.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.bie.valuation import PATH_METRICS, SCALAR_METRICS, UNIT_METRICS, SCENARIOS, value_company
from app.infrastructure.database.models import BieAssumptionOverride

METRICS = SCALAR_METRICS | PATH_METRICS | UNIT_METRICS


class OverrideError(ValueError):
    pass


def set_override(db: Session, company_id: str, *, metric: str, value: float, reason: str, unit: str = "Company",
                 scenario: str = "All", fiscal_year: int | None = None, evidence_url: str | None = None,
                 confidence: str = "MEDIUM", created_by: str = "analyst") -> BieAssumptionOverride:
    if metric not in METRICS:
        raise OverrideError(f"unknown metric '{metric}'; choose one of {sorted(METRICS)}")
    if not reason or len(reason.strip()) < 10:
        raise OverrideError("an override needs a reason (at least a sentence)")
    if scenario not in ("All", *SCENARIOS):
        raise OverrideError("scenario must be All, Bear, Base or Bull")
    if metric in SCALAR_METRICS and (unit != "Company" or scenario != "All" or fiscal_year is not None):
        raise OverrideError(f"'{metric}' is a company-level input: it takes no segment, scenario or year")
    if metric in UNIT_METRICS and (scenario != "All" or fiscal_year is not None):
        raise OverrideError(f"'{metric}' is set per segment, for all scenarios and years")
    now = datetime.now(timezone.utc)
    for old in _active(db, company_id, metric, unit, scenario, fiscal_year):
        old.superseded_at, old.superseded_reason = now, "replaced by a newer override"
    row = BieAssumptionOverride(id=str(uuid.uuid4()), company_id=company_id, scenario=scenario, unit=unit, metric=metric,
                                fiscal_year=fiscal_year, value=value, reason=reason.strip(), evidence_url=evidence_url,
                                confidence=confidence, created_by=created_by, created_at=now)
    db.add(row)
    db.flush()
    return row


def _active(db, company_id, metric, unit, scenario, fiscal_year):
    q = db.query(BieAssumptionOverride).filter_by(company_id=company_id, metric=metric, unit=unit, scenario=scenario).filter(
        BieAssumptionOverride.superseded_at.is_(None))
    q = q.filter(BieAssumptionOverride.fiscal_year.is_(None)) if fiscal_year is None else q.filter(BieAssumptionOverride.fiscal_year == fiscal_year)
    return q.all()


def reset_override(db: Session, override_id: str, reason: str = "reset to the model's estimate") -> bool:
    row = db.get(BieAssumptionOverride, override_id)
    if row is None or row.superseded_at is not None:
        return False
    row.superseded_at, row.superseded_reason = datetime.now(timezone.utc), reason
    return True


def history(db: Session, company_id: str) -> list[dict]:
    rows = db.query(BieAssumptionOverride).filter_by(company_id=company_id).order_by(BieAssumptionOverride.created_at.desc()).all()
    return [{"id": r.id, "metric": r.metric, "unit": r.unit, "scenario": r.scenario, "fiscal_year": r.fiscal_year, "value": float(r.value),
             "reason": r.reason, "evidence_url": r.evidence_url, "confidence": r.confidence, "created_by": r.created_by,
             "created_at": r.created_at.isoformat(), "active": r.superseded_at is None,
             "superseded_at": r.superseded_at.isoformat() if r.superseded_at else None, "superseded_reason": r.superseded_reason} for r in rows]


def _dry(db: Session, company_id: str, **kwargs) -> dict:
    """Run the model without keeping anything it writes."""
    nested = db.begin_nested()
    try:
        return value_company(db, company_id, **kwargs)
    finally:
        nested.rollback()


def _headline(out: dict, scenario: str = "Base") -> dict:
    s = out["scenarios"][scenario]
    row = s["rows"][0]
    return {"revenue": row["revenue"], "profit_before_tax": row["pbt"], "profit_after_tax": row["pat"], "free_cash_flow": row["fcff"],
            "dcf": s.get("dcf"), "sotp": s.get("sotp"), "peer_multiple": s.get("relative"), "average": s.get("average")}


def impact(db: Session, company_id: str, scenario: str = "Base") -> dict:
    """Year-1 results and each valuation lens with the system's assumptions alone, and with the overrides in force."""
    before, after = _dry(db, company_id, use_overrides=False), _dry(db, company_id)
    if "skipped" in after:
        return after
    return {"scenario": scenario, "overrides": len(after["overrides"]), "before": _headline(before, scenario), "after": _headline(after, scenario)}


def what_if(db: Session, company_id: str, *, metric: str, values: list[float], unit: str = "Company",
            scenario: str = "All", fiscal_year: int | None = None) -> list[dict]:
    """The Base-case lenses for each trial value of one assumption, on top of the overrides already in force."""
    out = []
    for value in values:
        trial = SimpleNamespace(metric=metric, unit=unit, scenario=scenario, fiscal_year=fiscal_year, value=value, reason="what-if", id=None)
        out.append({"value": value, **_headline(_dry(db, company_id, extra_overrides=[trial]))})
    return out


def ranking(db: Session, company_id: str) -> list[dict]:
    """Which assumptions the valuation leans on most: each segment's growth is moved by ±2 points and its margin
    by ±10% (all years), and the swing in the Base-case average value per share is recorded."""
    base = _dry(db, company_id)
    if "skipped" in base or base["scenarios"]["Base"].get("average") is None:
        return []
    centre = base["scenarios"]["Base"]["average"]
    rows = []
    for u in base["units"]:
        # Growth is shifted year by year along the model's own path, so a one-year step (a break from history) stays one year.
        shifted = [_headline(_dry(db, company_id, extra_overrides=[
            SimpleNamespace(metric="revenue_growth", unit=u["name"], scenario="All", fiscal_year=year, value=g + delta, reason="what-if", id=None)
            for year, g in zip(u["path_years"], u["path"])])) for delta in (-0.02, 0.02)]
        margins = what_if(db, company_id, metric="margin", values=[u["margin"] * 0.9, u["margin"] * 1.1], unit=u["name"])
        for metric, label, results in (("revenue_growth", "growth ±2 points", shifted), ("margin", "margin ±10%", margins)):
            lo, hi = results[0]["average"], results[1]["average"]
            rows.append({"unit": u["name"], "metric": metric, "test": label, "low": lo, "high": hi, "swing": abs(hi - lo), "swing_pct": abs(hi - lo) / centre})
    return sorted(rows, key=lambda r: -r["swing"])


def control_centre(db: Session, company_id: str, scenario: str = "Base") -> dict:
    """Everything the Assumption Control Centre shows: each assumption's system estimate beside the value in
    force, the overrides with their reasons, and the before/after effect."""
    out = _dry(db, company_id)
    if "skipped" in out:
        return out
    before = _dry(db, company_id, use_overrides=False)
    units: dict[str, dict] = {}
    for g in out["grid"]:
        if g["scenario"] != scenario:
            continue
        unit = units.setdefault(g["unit"], {"name": g["unit"], "revenue_growth": [], "margin": []})
        unit[g["metric"]].append({"year": g["year"], "system": g["system"], "active": g["active"], "override_id": g["override_id"]})
    return {
        "scenario": scenario, "fiscal_years": sorted({g["year"] for g in out["grid"]}), "units": list(units.values()),
        "scalars": out["scalars"], "overrides": out["overrides"],
        "system_assumptions": len(out["assumption_ids"]), "analyst_overrides": len(out["overrides"]),
        "before": _headline(before, scenario), "after": _headline(out, scenario), "price": out["price"],
    }
