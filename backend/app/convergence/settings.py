"""The method's weights and gates. Defaults live here; the page can override any
of them (table `convergence_settings`). A row records the version it was built
with, and any override shows in that version."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import ConvergenceSetting

METHOD_VERSION = "1.0"
WEIGHTS = ("weight_quality", "weight_technical", "weight_rs", "weight_valuation", "weight_risk_reward")

# key: (default, lowest allowed, highest allowed, group, label)
DEFAULTS: dict[str, tuple[float, float, float, str, str]] = {
    "weight_quality": (35, 0, 100, "Weights (must add up to 100)", "Fundamental Quality"),
    "weight_technical": (25, 0, 100, "Weights (must add up to 100)", "Technical Stage"),
    "weight_rs": (15, 0, 100, "Weights (must add up to 100)", "Relative Strength"),
    "weight_valuation": (15, 0, 100, "Weights (must add up to 100)", "Valuation"),
    "weight_risk_reward": (10, 0, 100, "Weights (must add up to 100)", "Risk/Reward"),
    "min_coverage": (70, 50, 100, "Weights (must add up to 100)", "Least weight with data for a combined score, %"),
    "stage_share": (40, 0, 100, "Stage fit", "Stage's share of Technical Stage, %"),
    "fit_established": (90, 0, 100, "Stage fit", "Established Stage 2"),
    "fit_early": (85, 0, 100, "Stage fit", "Early Stage 2"),
    "fit_late": (65, 0, 100, "Stage fit", "Late Stage 2"),
    "fit_weakening": (50, 0, 100, "Stage fit", "Stage 2 Weakening"),
    "fit_stage_1": (50, 0, 100, "Stage fit", "Stage 1"),
    "fit_stage_3": (30, 0, 100, "Stage fit", "Stage 3"),
    "fit_stage_4": (10, 0, 100, "Stage fit", "Stage 4"),
    "floor_quality": (40, 20, 50, "Gates", "Quality under this is Low Priority"),
    "high_quality": (65, 50, 90, "Gates", "High Priority: least Quality"),
    "high_combined": (70, 50, 95, "Gates", "High Priority: least combined score"),
    "high_reward_risk": (2, 1, 5, "Gates", "High Priority: least reward/risk"),
    "high_rs": (60, 30, 90, "Gates", "High Priority: least Relative Strength"),
    "strong_combined": (60, 40, 90, "Gates", "Strong Candidate: least combined score"),
    "strong_reward_risk": (1.5, 0.5, 4, "Gates", "Strong Candidate: least reward/risk"),
    "poor_reward_risk": (1, 0.2, 3, "Gates", "Reward/risk under this is poor"),
    "low_confidence": (60, 30, 90, "Confidence", "Under this, confidence is Low and High Priority is closed"),
    "high_confidence": (80, 60, 100, "Confidence", "At or above this, confidence is High"),
    "min_stop_pct": (5, 1, 15, "Reward/risk", "Invalidation at least this % under the price"),
    "sma_cushion_pct": (3, 0, 10, "Reward/risk", "Invalidation this % under the 30-week average"),
    "target_gap_pct": (5, 1, 20, "Reward/risk", "The 52-week high counts as a target if this % above"),
    "entry_band_pct": (3, 1, 10, "Reward/risk", "Stage 1 entry band above resistance, %"),
}


def defaults() -> dict[str, float]:
    return {k: float(v[0]) for k, v in DEFAULTS.items()}


def load(db: Session) -> dict[str, float]:
    return {**defaults(), **{r.key: float(r.value) for r in db.query(ConvergenceSetting).filter(ConvergenceSetting.key.in_(DEFAULTS))}}


def version(cfg: dict[str, float]) -> str:
    """"1.0" on the defaults; "1.0-ab12cd" when any value is overridden."""
    changed = sorted((k, v) for k, v in cfg.items() if v != DEFAULTS[k][0])
    return METHOD_VERSION + (f"-{hashlib.sha1(repr(changed).encode()).hexdigest()[:6]}" if changed else "")


def check(current: dict[str, float], changes: dict[str, float]) -> None:
    """Raises ValueError on an unknown key, a value out of range, or weights not adding up to 100."""
    for key, value in changes.items():
        if key not in DEFAULTS:
            raise ValueError(f"Unknown setting {key}")
        low, high = DEFAULTS[key][1:3]
        if not low <= float(value) <= high:
            raise ValueError(f"{DEFAULTS[key][4]} must be between {low:g} and {high:g}")
    total = sum({**current, **changes}[k] for k in WEIGHTS)
    if abs(total - 100) > 0.01:
        raise ValueError(f"The five weights must add up to 100, not {total:g}")


def save(db: Session, changes: dict[str, float]) -> dict[str, float]:
    check(load(db), changes)
    now = datetime.now(timezone.utc)
    for key, value in changes.items():
        if float(value) == DEFAULTS[key][0]:
            db.query(ConvergenceSetting).filter(ConvergenceSetting.key == key).delete()
            continue
        stmt = insert(ConvergenceSetting).values(key=key, value=value, updated_at=now)
        db.execute(stmt.on_conflict_do_update(index_elements=["key"], set_={"value": value, "updated_at": now}))
    db.commit()
    return load(db)
