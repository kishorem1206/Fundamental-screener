"""Loads canonical sector framework markdown docs (sector_frameworks/*.md) so the
AI-analysis stage can follow them directly, per each doc's "AI Interpretation
Rules" section. Python scoring code implements these docs; it does not
redefine them (see banking.md section 31, Framework Governance).
"""
from pathlib import Path

_FRAMEWORKS_DIR = Path(__file__).resolve().parent.parent.parent / "sector_frameworks"

_SECTOR_TO_FILENAME = {
    "Banks": "banking.md",
}

_cache: dict[str, str] = {}


def load_framework_doc(sector_name: str) -> str | None:
    """Read the canonical markdown framework for a sector, or None if this
    sector has no framework doc yet."""
    filename = _SECTOR_TO_FILENAME.get(sector_name)
    if filename is None:
        return None
    if filename in _cache:
        return _cache[filename]
    path = _FRAMEWORKS_DIR / filename
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    _cache[filename] = text
    return text


def has_framework_doc(sector_name: str) -> bool:
    return sector_name in _SECTOR_TO_FILENAME
