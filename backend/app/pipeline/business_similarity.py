"""TF-IDF cosine similarity over Yahoo business descriptions (no ML deps)."""
from __future__ import annotations

import math
import re
from collections import Counter

from sqlalchemy.orm import Session

from app.infrastructure.database.models import StockBusinessProfile

_STOP = frozenset(
    "the a an and or of in on for to with by as at from is are was were be been its it this that which "
    "company companies limited ltd india indian also other including includes offers provides provide "
    "products services product service business segment segments operates engaged offering through "
    "primarily various well formerly founded headquartered based".split()
)
_cache: dict = {"key": None, "vecs": {}}


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in _STOP]


def _build(db: Session) -> dict[str, dict[str, float]]:
    rows = db.query(StockBusinessProfile.stock_id, StockBusinessProfile.description).all()
    key = (len(rows), sum(len(d or "") for _, d in rows))
    if _cache["key"] == key:
        return _cache["vecs"]
    docs = {sid: Counter(_tokens(d)) for sid, d in rows if d}
    df: Counter = Counter()
    for c in docs.values():
        df.update(c.keys())
    n = max(len(docs), 1)
    vecs: dict[str, dict[str, float]] = {}
    for sid, c in docs.items():
        v = {w: (1 + math.log(f)) * math.log(n / df[w]) for w, f in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs[sid] = {w: x / norm for w, x in v.items()}
    _cache["key"], _cache["vecs"] = key, vecs
    return vecs


def similarity(db: Session, subject_id: str, other_id: str) -> float:
    vecs = _build(db)
    a, b = vecs.get(subject_id), vecs.get(other_id)
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0.0) for w, x in a.items())
