"""Read a credit rating out of the letter a company files with NSE.

NSE's "Credit Rating" announcements carry only a generic line ("…has
informed the Exchange about Credit Rating"); the substance is in the PDF the
company attached, written in each company's own words. This module takes the
text of that PDF and finds, by pattern only (nothing is guessed):

  agency            CRISIL, ICRA, CARE, India Ratings, Acuite, Infomerics,
                    Brickwork, Fitch, Moody's, S&P (first one named)
  rating            the first long-term rating on the Indian scale
                    (AAA … D, with the agency's prefix: "CRISIL AA/Stable",
                    "[ICRA]AA+ (Stable)", "CARE AA-; Stable", "IND AA")
  short_term        the first short-term rating ("CRISIL A1+", "[ICRA]A1")
  outlook           Stable / Positive / Negative / Developing, or a rating
                    watch with negative / positive / developing implications
  action            UPGRADE, DOWNGRADE, OUTLOOK_REVISED, WATCH, ASSIGNED,
                    REAFFIRMED, WITHDRAWN (strongest word found)
  previous          "revised from X to Y" / "upgraded from X" phrasing
  instrument        bank facilities, NCDs, commercial paper, …
  rationale_url     a link to the agency's own rationale, when the letter has one

A letter in which no rating can be found is still stored (parsed = False) so
the filing link is shown, but it never feeds a flag.
"""
from __future__ import annotations

import re

AGENCIES = [
    ("CRISIL", r"\bcrisil\b"), ("ICRA", r"\bicra\b"), ("CARE", r"\bcare\s*(?:ratings|edge)\b|careedge"),
    ("India Ratings", r"india\s+ratings|\bind-?ra\b"), ("Acuite", r"\bacuit[eé]\b|\bsmera\b"),
    ("Infomerics", r"\binfomerics\b|\bivr\b"), ("Brickwork", r"\bbrickwork\b|\bbwr\b"),
    ("Fitch", r"\bfitch\b"), ("Moody's", r"\bmoody"), ("S&P", r"\bs\s*&\s*p\b|standard\s*&\s*poor"),
]
_PREFIX = r"(?<![A-Za-z])(?i:PP-MLD\s*)?(?i:crisil|\[icra\]|icra|care|ind|acuite|ivr|bwr|infomerics)"
_LONG = rf"{_PREFIX}\s*\(?\s*(AAA|AA\+|AA-|AA|A\+|A-|A|BBB\+|BBB-|BBB|BB\+|BB-|BB|B\+|B-|B|C\+|C-|C|D)(?![0-9A-Za-z+])(?:\s*\(\s*CE\s*\))?"
_SHORT = rf"{_PREFIX}\s*\(?\s*(A1\+|A1|A2\+|A2|A3\+|A3|A4\+|A4)(?![0-9])"
_OUTLOOK = r"(stable|positive|negative|developing)"
_WATCH = r"(?:rating\s+)?watch\s+(?:with\s+)?(negative|positive|developing)(?:\s+implications)?"

SCALE = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "C+", "C", "C-", "D"]
INVESTMENT_GRADE_FLOOR = SCALE.index("BBB-")

_INSTRUMENTS = [
    ("Bank facilities", r"bank\s+(?:loan\s+)?facilit|fund[\s-]based|term\s+loan|working\s+capital|cash\s+credit"),
    ("Non-convertible debentures", r"non[\s-]*convertible\s+debenture|\bncds?\b"),
    ("Commercial paper", r"commercial\s+paper"),
    ("Fixed deposits", r"fixed\s+deposit"),
    ("Bonds", r"\bbonds?\b"),
    ("Market linked debentures", r"market\s+linked"),
    ("Issuer rating", r"issuer\s+rating"),
]
_AGENCY_SITES = r"https?://[^\s\"')]*(?:crisil|icra|careratings|careedge|indiaratings|acuite|infomerics|brickworkratings|fitchratings)[^\s\"')]*"


def notch(rating: str | None) -> int | None:
    return SCALE.index(rating) if rating in SCALE else None


def _first(pattern: str, text: str, flags=re.I):
    m = re.search(pattern, text, flags)
    return m


_DOWN = r"\bdowngraded\b(?!\s*/)|downgrad(?:e|ation)\s+(?:of|in)\s+(?:the\s+)?(?:credit\s+)?rating|revised\s+downward"
_UP = r"\bupgraded\b(?!\s*/)|upgrad(?:e|ation)\s+(?:of|in)\s+(?:the\s+)?(?:credit\s+)?rating|revised\s+upward"


def cover_letter(flat: str) -> str:
    """The company's own letter, without the agency rationale often attached
    after it — whose "factors that could lead to a downgrade" would otherwise
    read as a downgrade."""
    i = flat.lower().find("rating rationale", 300)
    return flat[:i] if i > 0 else flat[:3500]


def parse(text: str) -> dict:
    whole = " ".join(text.split())
    flat = cover_letter(whole)
    if not re.search(_LONG, flat) and not re.search(_SHORT, flat):
        flat = whole
    low = flat.lower()
    out: dict = {"parsed": False}
    for name, pattern in AGENCIES:
        if re.search(pattern, low):
            out["agency"] = name
            break
    longs = [(m.start(), m.group(1).upper()) for m in re.finditer(_LONG, flat)]
    shorts = [(m.start(), m.group(1).upper()) for m in re.finditer(_SHORT, flat)]
    short_pos = {p for p, _ in shorts}
    longs = [(p, r) for p, r in longs if p not in short_pos]
    first = min(longs + shorts) if longs or shorts else None
    if first:  # the agency whose prefix the rating carries beats a name found anywhere in the letter
        prefix = flat[first[0]:first[0] + 12].lower()
        for key, name in (("crisil", "CRISIL"), ("icra", "ICRA"), ("care", "CARE"), ("ind", "India Ratings"),
                          ("acuite", "Acuite"), ("ivr", "Infomerics"), ("infomerics", "Infomerics"), ("bwr", "Brickwork")):
            if key in prefix:
                out["agency"] = name
                break

    # "revised from CRISIL AA-/Stable to CRISIL AA/Stable" — the later one is current
    q = "['\"‘“]?"
    move = re.search(rf"(?:from|earlier)\s*:?\s*{q}{_LONG}.{{0,60}}?\bto\s*:?\s*{q}{_LONG}", flat)
    back = re.search(rf"\bto\s*:?\s*{q}{_LONG}.{{0,40}}?\bfrom\s*:?\s*{q}{_LONG}", flat)
    was = re.search(rf"(?:upgraded|downgraded|revised)\s+from\s*{q}{_LONG}", flat, re.I)
    if move:
        out["previous_rating"], out["rating"] = move.group(1).upper(), move.group(2).upper()
    elif back:
        out["rating"], out["previous_rating"] = back.group(1).upper(), back.group(2).upper()
    elif was and longs:
        out["previous_rating"] = was.group(1).upper()
        out["rating"] = next((r for _, r in longs if r != out["previous_rating"]), out["previous_rating"])
    elif longs:
        out["rating"] = longs[0][1]
        # a table with "previous rating" and "current/revised rating" columns: the second listed is current
        if re.search(r"(?:previous|existing|earlier)\s+rating|existing\s+revised", low) and len({r for _, r in longs[:2]}) == 2:
            out["previous_rating"], out["rating"] = longs[0][1], longs[1][1]
    if shorts:
        out["short_term"] = shorts[0][1]

    watch = _first(_WATCH, low)
    if watch:
        out["outlook"] = f"Watch {watch.group(1).capitalize()}"
    current = next((p for p, r in longs if r == out.get("rating")), longs[0][0]) if longs else None
    after = flat[current:current + 80] if longs else ""
    m = re.search(_OUTLOOK, after, re.I) or re.search(rf"outlook[^.]{{0,40}}?\b{_OUTLOOK}", flat, re.I)
    if m and "outlook" not in out:
        out["outlook"] = m.group(1).capitalize()
    ol = re.search(rf"outlook[^.]{{0,60}}?from\s+'?{_OUTLOOK}'?\s+to\s+'?{_OUTLOOK}", flat, re.I)
    if ol:
        out["previous_outlook"], out["outlook"] = ol.group(1).capitalize(), ol.group(2).capitalize()

    # the action comes from the company's letter alone, never an attached rationale; a form's
    # "Upgraded/Downgraded" column heading is not an action
    words = re.sub(r"up-?grad\w*\s*/\s*down-?grad\w*", " ", cover_letter(whole).lower())
    if "esg rating" in low and not longs:
        out["action"] = "ESG"
    elif re.search(_DOWN, words) and out.get("rating") != "AAA":  # nothing is downgraded to the top of the scale
        out["action"] = "DOWNGRADE"
    elif re.search(_UP, words):
        out["action"] = "UPGRADE"
    elif watch:
        out["action"] = "WATCH"
    elif ol or re.search(r"(?:revision|revised|change)\s+(?:in|of)\s+(?:the\s+)?outlook|outlook\s+(?:has\s+been\s+)?revised", low):
        out["action"] = "OUTLOOK_REVISED"
    elif re.search(r"withdr[ae]w", low) and not re.search(r"reaffirm|re-affirm|assign", low):
        out["action"] = "WITHDRAWN"
    elif re.search(r"reaffirm|re-affirm", low):
        out["action"] = "REAFFIRMED"
    elif re.search(r"\bassign", low):
        out["action"] = "ASSIGNED"
    if out.get("previous_rating") and out.get("rating"):
        a, b = notch(out["previous_rating"]), notch(out["rating"])
        if "action" not in out:
            out["action"] = "DOWNGRADE" if b > a else "UPGRADE" if b < a else "REAFFIRMED"
        # a table read out of order: the action says which of the two is current
        if (out["action"] == "DOWNGRADE" and b < a) or (out["action"] == "UPGRADE" and b > a):
            out["previous_rating"], out["rating"] = out["rating"], out["previous_rating"]

    for name, pattern in _INSTRUMENTS:
        if re.search(pattern, low):
            out["instrument"] = name
            break
    site = re.search(_AGENCY_SITES, flat, re.I)
    if site:
        out["rationale_url"] = site.group(0).rstrip(".,;")
    if out.get("rating") or out.get("short_term"):
        out["parsed"] = True
    # the sentence that carries the rating, for display
    anchor = longs[0][0] if longs else (shorts[0][0] if shorts else None)
    if anchor is not None:
        out["excerpt"] = flat[max(0, anchor - 220):anchor + 160]
    return out
