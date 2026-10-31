"""Every threshold the classifier uses. The defaults live here; the page can
override any of them (table `stage_thresholds`), and a recalculation replays the
whole history with the new values."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import StageThreshold

# key: (default, lowest allowed, highest allowed, group, label)
DEFAULTS: dict[str, tuple[float, float, float, str, str]] = {
    "sma_long_weeks": (30, 20, 40, "Trend", "Long moving average, weeks"),
    "sma_short_weeks": (10, 5, 20, "Trend", "Short moving average, weeks"),
    "slope_weeks": (4, 2, 13, "Trend", "Slope measured over, weeks"),
    "flat_slope_pct": (1.0, 0.2, 3, "Trend", "Slope within this % counts as flat"),
    "pullback_pct": (3, 0, 10, "Trend", "A Stage 2 pullback may close this % under the average"),
    "structure_weeks": (52, 26, 104, "Trend", "Swing points read over, weeks"),
    "pivot_weeks": (3, 2, 6, "Trend", "A swing point needs this many weeks either side"),
    "rs_sma_weeks": (52, 26, 52, "Relative strength", "RS compared with its own average, weeks"),
    "rs_min_weeks": (30, 20, 52, "Relative strength", "Fewest weeks to read RS"),
    "rs_slope_weeks": (4, 2, 13, "Relative strength", "RS trend measured over, weeks"),
    "rsi_weeks": (14, 7, 21, "Momentum", "Weekly RSI period"),
    "volume_avg_weeks": (10, 5, 20, "Volume", "Volume ratio compares with this many earlier weeks"),
    "updown_weeks": (10, 5, 20, "Volume", "Up and down weeks compared over, weeks"),
    "updown_bull": (1.1, 1, 2, "Volume", "Up-week volume ÷ down-week volume at or above this is bullish"),
    "updown_bear": (0.9, 0.5, 1, "Volume", "At or below this is distribution"),
    "breakout_volume": (1.5, 1, 3, "Breakout", "Volume ratio that confirms a breakout"),
    "range_weeks": (20, 10, 40, "Breakout", "Resistance and support read over, weeks"),
    "event_gap_weeks": (4, 1, 12, "Breakout", "Weeks before another breakout marker"),
    "near_level_pct": (3, 1, 10, "Breakout", "Within this % of a level counts as at it"),
    "base_weeks": (12, 6, 30, "Base and top", "Consolidation measured over, weeks"),
    "base_range_pct": (30, 10, 60, "Base and top", "High-low range at or under this % is a consolidation"),
    "contraction_ratio": (0.9, 0.5, 1, "Base and top", "Recent weekly range ÷ earlier range at or under this is contraction"),
    "no_new_low_weeks": (8, 4, 26, "Base and top", "No new low for this many weeks"),
    "near_sma_pct": (10, 3, 25, "Base and top", "Within this % of the average"),
    "near_high_pct": (20, 5, 40, "Base and top", "Within this % of the 52-week high is near the highs"),
    "min_confidence": (50, 30, 80, "Classification", "Lowest confidence that names a stage"),
    "confirm_weeks": (2, 1, 4, "Classification", "A new stage must hold this many weeks in a row"),
    "switch_margin": (10, 0, 30, "Classification", "A rival stage must beat the running stage by this many points"),
    "stale_days": (10, 3, 30, "Classification", "No trade for this many days leaves a stock unclassified"),
    "new_weeks": (4, 1, 13, "Stage 2", "Newly entered means within this many weeks"),
    "early_weeks": (12, 4, 26, "Stage 2", "Early Stage 2 lasts this many weeks"),
    "late_distance_pct": (30, 10, 80, "Stage 2", "This % above the average is Late Stage 2"),
    "opportunity_high_pct": (10, 3, 25, "Stage 2", "Near a new high means within this %"),
    "opportunity_breakout_weeks": (8, 2, 26, "Stage 2", "Recent breakout means within this many weeks"),
    "signal_min_checks": (4, 2, 5, "Stage 2", "Checks met, of 5, to raise a transition watch"),
}


def defaults() -> dict[str, float]:
    return {k: float(v[0]) for k, v in DEFAULTS.items()}


def load(db: Session) -> dict[str, float]:
    return {**defaults(), **{r.key: float(r.value) for r in db.query(StageThreshold).filter(StageThreshold.key.in_(DEFAULTS))}}


def save(db: Session, changes: dict[str, float]) -> dict[str, float]:
    """A value equal to the default clears the override. Raises ValueError on a
    key that does not exist or a value outside its range."""
    for key, value in changes.items():
        if key not in DEFAULTS:
            raise ValueError(f"Unknown threshold {key}")
        low, high = DEFAULTS[key][1:3]
        if not low <= float(value) <= high:
            raise ValueError(f"{DEFAULTS[key][4]} must be between {low:g} and {high:g}")
    now = datetime.now(timezone.utc)
    for key, value in changes.items():
        if float(value) == DEFAULTS[key][0]:
            db.query(StageThreshold).filter(StageThreshold.key == key).delete()
            continue
        stmt = insert(StageThreshold).values(key=key, value=value, updated_at=now)
        db.execute(stmt.on_conflict_do_update(index_elements=["key"], set_={"value": value, "updated_at": now}))
    db.commit()
    return load(db)
