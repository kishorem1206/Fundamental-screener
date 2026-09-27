"""Speaker/section transcript parsing — Concall Intelligence System, Stage
C1. Pure deterministic parsing, no LLM — confirmed live-testing two real
transcripts (HDFC Bank, TCS) that the "SpeakerName:    text" format with
indented continuation lines is consistent enough across both templates
Stage C0 already found to make this a regex problem, not an ML one.

Re-extracts text from the PDF already durably stored in MinIO (Stage C0)
rather than persisting the full transcript text separately — the source
PDF is the single source of truth; re-running pdfplumber on it is cheap.
"""
from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timezone

import pdfplumber
from sqlalchemy.orm import Session

from app.infrastructure.database.models import ConcallTranscript, ConcallUtterance, Document
from app.infrastructure.storage.minio_client import get_document
from app.logger import logger

# A new utterance starts when a line begins with minimal leading whitespace
# and matches "Name:" — continuation lines of the same utterance are
# indented further (confirmed on both real transcripts: dialogue text
# wraps at ~26 spaces of indentation, well past a speaker label's own
# leading whitespace of 0-4).
_UTTERANCE_START_RE = re.compile(
    r"^(\s{0,4})([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,4}):\s*(.*)$"
)

# Page footers/headers repeated on every page — found live-testing HDFC's
# transcript (2026-09-13): "Page N of M" and a right-aligned company-name-
# then-date running header. Filtered before utterance splitting so they
# don't get appended as noise into whatever utterance was active on that
# page boundary.
_PAGE_NUMBER_RE = re.compile(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", re.I)
_DATE_ONLY_RE = re.compile(
    r"^\s*(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s*\d{4}\s*$", re.I
)


def _is_junk_line(line: str) -> bool:
    if _PAGE_NUMBER_RE.match(line) or _DATE_ONLY_RE.match(line):
        return True
    stripped = line.strip()
    leading_ws = len(line) - len(line.lstrip())
    # Right-aligned running header: far more leading whitespace than any
    # real continuation line uses, and short with no sentence punctuation.
    if stripped and leading_ws > 50 and len(stripped) < 40 and not stripped.endswith((".", ",", ":", "?")):
        return True
    return False


_QA_TRANSITION_RE = re.compile(r"question[\s-]and[\s-]answer session", re.I)


def _split_utterances(full_text: str) -> list[dict]:
    """[{speaker_name, text}] in document order, starting at the first
    "Moderator:" line (the actual transcript body — skips the cover
    letter/regulatory intimation that precedes it in every filing seen).
    Never raises — returns [] if no Moderator line is found at all."""
    lines = full_text.split("\n")

    start_idx = None
    for i, line in enumerate(lines):
        m = _UTTERANCE_START_RE.match(line)
        if m and m.group(2).strip().lower() == "moderator":
            start_idx = i
            break
    if start_idx is None:
        return []

    utterances: list[dict] = []
    current: dict | None = None
    for line in lines[start_idx:]:
        if _is_junk_line(line):
            continue
        m = _UTTERANCE_START_RE.match(line)
        if m:
            if current is not None:
                current["text"] = current["text"].strip()
                if current["text"]:
                    utterances.append(current)
            current = {"speaker_name": m.group(2).strip(), "text": m.group(3).strip()}
        elif current is not None:
            stripped = line.strip()
            if stripped:
                current["text"] += " " + stripped
    if current is not None:
        current["text"] = current["text"].strip()
        if current["text"]:
            utterances.append(current)
    return utterances


def _normalize_name(name: str) -> str:
    return re.sub(r"^(MR|MS|MRS|DR)\.?\s+", "", name.strip(), flags=re.I).strip().lower()


_ROLE_KEYWORDS = [
    ("chief executive", "CEO"), ("managing director", "CEO"),
    ("chief financial officer", "CFO"),
    ("deputy managing director", "Deputy MD"),
    ("chief operating officer", "COO"),
    ("chairman", "Chairman"),
]


def _build_role_map(management_participants: list[dict]) -> dict[str, str]:
    """{normalized_name: role} from Stage C0's parsed MANAGEMENT block.
    Falls back to "Management" for a named participant whose title doesn't
    match a known keyword, rather than guessing further."""
    role_map = {}
    for p in management_participants or []:
        normalized = _normalize_name(p.get("name", ""))
        if not normalized:
            continue
        title = (p.get("title") or "").lower()
        role = next((r for kw, r in _ROLE_KEYWORDS if kw in title), "Management")
        role_map[normalized] = role
    return role_map


def _assign_roles_and_sections(utterances: list[dict], role_map: dict[str, str]) -> list[dict]:
    """Real bug found live-testing TCS's transcript (2026-09-14): its
    template has no upfront "MANAGEMENT:" block (Stage C0 correctly leaves
    `management_participants` empty there), so the static role_map alone
    left every real management speaker — CFO, COO, CHRO, all clearly
    identified inline as the Moderator/IR head introduces them — falling
    back to "Analyst". That's not just cosmetically wrong: Stage C3's
    entire safety guarantee ("an analyst's question can never become
    guidance") depends on this field being right.

    Fixed with a structural rule specific to this transcript format,
    confirmed on both real templates seen so far: only the Moderator and
    company management speak before the Q&A transition — analysts are
    individually introduced by name only once Q&A starts. So any non-
    Moderator speaker observed during `opening_remarks` is learned as
    "Management" on the spot and reused for the rest of the document,
    letting that same person be recognized correctly when they speak again
    to answer a question later. This needs no LLM and no company-specific
    knowledge — it falls out of the transcript's own structure."""
    section = "opening_remarks"
    learned_role_map = dict(role_map)
    out = []
    for u in utterances:
        normalized = _normalize_name(u["speaker_name"])
        if normalized == "moderator":
            role = "Moderator"
        elif normalized in learned_role_map:
            role = learned_role_map[normalized]
        elif section == "opening_remarks":
            role = "Management"
            learned_role_map[normalized] = role
        else:
            role = "Analyst"

        out.append({**u, "speaker_role": role, "section": section})

        if role == "Moderator" and _QA_TRANSITION_RE.search(u["text"]):
            section = "qa"
    return out


def parse_and_store_utterances(db: Session, transcript: ConcallTranscript) -> list[ConcallUtterance]:
    """Re-extracts the transcript's PDF text from MinIO, splits it into
    speaker turns, assigns role/section, and stores one ConcallUtterance
    row per turn. Idempotent — clears any previously stored utterances for
    this transcript before re-inserting, so re-running after a parser fix
    doesn't duplicate rows. Never raises — logs and returns [] on failure."""
    document = db.query(Document).filter_by(id=transcript.document_id).first()
    if document is None:
        logger.warning("concall_parser: source document missing", transcript_id=transcript.id)
        return []

    pdf_bytes = get_document(document.storage_key)
    if pdf_bytes is None:
        logger.warning("concall_parser: could not retrieve PDF from storage", transcript_id=transcript.id)
        return []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception as e:
        logger.warning("concall_parser: PDF text extraction failed", transcript_id=transcript.id, error=str(e))
        return []

    raw_utterances = _split_utterances(full_text)
    if not raw_utterances:
        logger.warning("concall_parser: no utterances found (unrecognized template?)", transcript_id=transcript.id)
        return []

    role_map = _build_role_map(transcript.management_participants or [])
    assigned = _assign_roles_and_sections(raw_utterances, role_map)

    db.query(ConcallUtterance).filter_by(transcript_id=transcript.id).delete()

    now = datetime.now(timezone.utc)
    stored = []
    for i, u in enumerate(assigned):
        row = ConcallUtterance(
            id=str(uuid.uuid4()), transcript_id=transcript.id, sequence=i,
            speaker_name=u["speaker_name"], speaker_role=u["speaker_role"],
            section=u["section"], text=u["text"], retrieved_at=now,
        )
        db.add(row)
        stored.append(row)

    transcript.extraction_status = "PARSED"
    db.flush()

    logger.info("concall_parser: utterances stored", transcript_id=transcript.id,
                count=len(stored), opening_remarks=sum(1 for u in assigned if u["section"] == "opening_remarks"),
                qa=sum(1 for u in assigned if u["section"] == "qa"))
    return stored
