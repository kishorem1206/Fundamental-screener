"""Shared confidence-tagging helper (spec Stage 22).

`cascade.py`/`standalone_consolidated.py`/`earnings_quality.py` each
already tag confidence inline (HIGH for a directly-reported ledger value,
MEDIUM for a value derived from two+ reported values, LOW/UNAVAILABLE for
missing or structurally-absent data) — that inline logic is simple enough
per call site that it isn't being retrofitted through this helper
retroactively (each is already tested). This module exists for **new**
code (the `compute_pl_intelligence()` orchestrator, and anything built on
top of it) so confidence tagging doesn't get reinvented a fourth and fifth
time, per Rule 4/Stage 22's requirement that missing data is always tagged,
never silently coerced to zero or a default.
"""
from __future__ import annotations

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
UNAVAILABLE = "UNAVAILABLE"


def confidence_for(value, source_count: int = 1, is_derived: bool = False) -> str:
    """`value`: the computed/looked-up value itself (None => UNAVAILABLE,
    always, regardless of the other args). `source_count`: how many
    independently-reported ledger values fed into `value` (0 => UNAVAILABLE
    even if `value` is somehow not None; 1 with `is_derived=False` => HIGH,
    a direct pass-through of one reported figure; 2+ or `is_derived=True`
    => MEDIUM, since it's arithmetic over reported figures, not a reported
    figure itself). Never returns LOW on its own — LOW is reserved for the
    package's own documented structural dead ends (gross margin, employee
    cost, exceptional items), which set that tag explicitly at the source
    rather than through this general-purpose helper.
    """
    if value is None or source_count <= 0:
        return UNAVAILABLE
    if is_derived or source_count > 1:
        return MEDIUM
    return HIGH
