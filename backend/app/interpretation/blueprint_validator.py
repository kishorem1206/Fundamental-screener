"""Output validator — Stage L2. Summary.md section 20: check that a
generated section doesn't introduce a number the master object never
supplied, before it reaches a rendered report.

Deliberately a best-effort, not a perfect, checker: it extracts numeric
tokens from generated text and confirms each one is traceable back to some
value in the Master Company Object (within a small rounding tolerance,
since "16.9%" and "16.90%" are the same fact). A handful of small integers
(0, 1, 2, 3...) are exempted — they show up constantly in ordinary prose
("one of three systemically important banks") and would otherwise make the
validator noisy without catching anything real. Years (2000-2099) are
exempted too — they're dates, not facts requiring grounding.

A section that fails is not silently rewritten or "fixed" — per Summary.md
section 4 ("Llama SHOULD NOT... invent missing data"), fabricating a
correction would be exactly the failure mode this exists to catch. It's
flagged and dropped from the blueprint, same as a section that failed to
generate at all.
"""
from __future__ import annotations

import re

from app.logger import logger

_ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# A `-` directly between two digit runs ("800-1400", a range, not "-1400" a
# negative number) is excluded from the sign via the negative lookbehind —
# same root cause as the ISO-date bug this module already guards against
# (dates handled by stripping them entirely above; this covers the same
# hyphen-as-separator pattern in ranges, which dates don't fully cover).
_NUMBER_RE = re.compile(r"(?<!\d)-?\d[\d,]*\.?\d*")
_EXEMPT_SMALL_INTS = set(range(0, 32))  # covers ordinary small counts and
# calendar day-of-month values written in non-ISO form ("31 March 2023"),
# which _ISO_DATE_RE can't strip since it only matches YYYY-MM-DD literally
_TOLERANCE_ABS = 0.05  # absolute
_TOLERANCE_REL = 0.005  # 0.5%, covers minor rounding-display differences


def _is_year(n: float) -> bool:
    return n == int(n) and 2000 <= n <= 2099


def _extract_numbers(text: str) -> list[float]:
    # Real bug found 2026-09-13: an ISO date like "2023-03-31" was being
    # scanned as three separate numbers (2023, -3, -31) — the hyphens read
    # as minus signs — which then correctly-but-wrongly failed grounding
    # and caused a whole section to be dropped despite being entirely
    # accurate. Dates aren't facts that need numeric grounding, so strip
    # them out before scanning at all.
    text = _ISO_DATE_RE.sub(" ", text or "")
    out = []
    for match in _NUMBER_RE.finditer(text):
        raw = match.group().replace(",", "")
        try:
            n = float(raw)
        except ValueError:
            continue
        if n in _EXEMPT_SMALL_INTS or _is_year(n):
            continue
        out.append(n)
    return out


def _collect_known_numbers(obj) -> set[float]:
    known = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            known.add(round(float(node), 4))
        elif isinstance(node, str):
            # Real gap found 2026-09-13: `business.about`/`key_points` prose
            # (Screener's company description) legitimately contains figures
            # ("over 50 years", "37% market share") that business_model/
            # company_snapshot are explicitly told to draw from — but as
            # plain strings, not structured numeric fields, they were
            # invisible to the numeric-leaf walk above, causing correct
            # prose citations to be flagged as ungrounded. Every string in
            # the object gets scanned the same way, not just those two
            # fields — a broader net here only makes the validator more
            # lenient, never less able to catch a genuine fabrication in a
            # *different* number that matches nothing anywhere.
            for n in _extract_numbers(node):
                known.add(round(n, 4))

    walk(obj)
    return known


def _grounded(n: float, known: set[float]) -> bool:
    for k in known:
        if abs(n - k) <= _TOLERANCE_ABS:
            return True
        if k != 0 and abs(n - k) / abs(k) <= _TOLERANCE_REL:
            return True
    return False


def _section_text(section: dict) -> str:
    parts = [section.get("content") or ""]
    for item in section.get("items") or []:
        # title/description (insight_cards, risk_cards) and question/answer
        # (Deep Research System's qa_cards, Stage R3) are the two item
        # shapes in use — extracting both keeps every content_type's prose
        # subject to the same numeric-grounding check, not just the first
        # shape this function happened to be written for.
        parts.append(item.get("title") or "")
        parts.append(item.get("description") or "")
        parts.append(item.get("question") or "")
        parts.append(item.get("answer") or "")
    return " ".join(parts)


def validate_section(section: dict, master: dict) -> tuple[bool, list[float]]:
    """Returns (is_valid, ungrounded_numbers). A section with any ungrounded
    number is considered invalid — the caller decides whether to drop it."""
    known = _collect_known_numbers(master)
    numbers = _extract_numbers(_section_text(section))
    ungrounded = [n for n in numbers if not _grounded(n, known)]
    return (len(ungrounded) == 0, ungrounded)


def validate_blueprint(blueprint: dict, master: dict) -> dict:
    """Drops any section carrying an ungrounded number. Never raises."""
    known = _collect_known_numbers(master)
    kept = []
    for section in blueprint.get("sections", []):
        numbers = _extract_numbers(_section_text(section))
        ungrounded = [n for n in numbers if not _grounded(n, known)]
        if ungrounded:
            logger.warning("blueprint_validator: dropped section with ungrounded numbers",
                            section=section.get("id"), ungrounded=ungrounded)
            continue
        kept.append(section)
    return {"report": blueprint.get("report"), "sections": kept}
