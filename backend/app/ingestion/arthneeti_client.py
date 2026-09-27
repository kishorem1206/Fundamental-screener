"""Results & Concall Highlights scraper — arthneeti.com, primary source
(2026-09-15 user directive: arthneeti.com already runs its own AI pass over
every concall and publishes readable highlight bullets per topic; re-deriving
the same narrative with our own LLM call is wasted spend when a free,
already-generated equivalent exists — use it as the PRIMARY source for the
"Results & Concall Highlights" content block, falling back to a deterministic
synthesis from our own already-extracted ConcallTopicSentiment/
ManagementGuidance rows (see `concall_highlights_fallback.py`) only when
arthneeti has no matching page).

Confirmed live (2026-09-15, L&T Q1 FY27 + Carysil Q1 FY25 pages) — no
CloudFront/bot gate like Trendlyne (robots.txt: `Allow: /`, only
`/api/ /admin/ /private/ /profile /login` disallowed), plain `requests` GET
returns 200 with the full page. Content isn't in visible HTML tables — it's
embedded as a Next.js React Server Component streaming payload
(`self.__next_f.push([1, "..."])` script tags), which the page's own client
JS parses to render; we parse the same payload directly with regex instead
of running a browser.

Company/quarter -> URL resolution has no public search API or a symbol/ISIN
field on any page we found, so it's done via `sitemaps/insights-{1,2}.xml`
(~5,836 URLs total, 2026-09-15), each in the form
`/insights/{company-slug}-q{N}-fy{YY}-earnings[-{dedup_suffix}]` — downloaded
and indexed once (cached, `_SITEMAP_TTL`), then matched against our own
`company_name` by normalized-slug equality first, difflib similarity second.
Never guesses a URL directly from a name — a wrong guess would silently
attribute one company's highlights to another.
"""
from __future__ import annotations

import difflib
import json
import re
import uuid
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from app.infrastructure.database.models import ConcallHighlight
from app.infrastructure.redis.client import cache_get_json, cache_set_json
from app.logger import logger

_SITEMAP_URLS = (
    "https://www.arthneeti.com/sitemaps/insights-1.xml",
    "https://www.arthneeti.com/sitemaps/insights-2.xml",
)
_SITEMAP_CACHE_KEY = "arthneeti:insights_sitemap"
_SITEMAP_TTL = 60 * 60 * 24  # 1 day — sitemap's own lastmod values update daily
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}
_URL_RE = re.compile(
    r"https://www\.arthneeti\.com/insights/(?P<slug>[a-z0-9-]+?)-(?P<quarter>q[1-4]-fy\d{2})-earnings(?:-\d+)?$"
)
_MIN_SLUG_SIMILARITY = 0.82  # below this, treat as "not found" rather than risk a wrong company


def _normalize(name: str) -> str:
    """"Larsen & Toubro Ltd." -> "larsen-toubro" — same normalization on
    both our company_name and arthneeti's URL slug so they're comparable."""
    name = re.sub(r"\b(ltd|limited|pvt|private|inc|corp|corporation|co)\b\.?", "", name.lower())
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name


def _fetch_sitemap_index() -> list[dict]:
    """[{"slug": normalized, "quarter": "q1-fy27", "url": ...}, ...]. Never
    raises — returns [] on any fetch/parse failure, caller treats that as
    "no arthneeti match", not a hard error."""
    cached = cache_get_json(_SITEMAP_CACHE_KEY)
    if cached is not None:
        return cached

    entries = []
    for sitemap_url in _SITEMAP_URLS:
        try:
            resp = requests.get(sitemap_url, headers=_HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("arthneeti_client: sitemap fetch failed", url=sitemap_url, error=str(e))
            continue
        for loc_match in re.finditer(r"<loc>([^<]+)</loc>", resp.text):
            url = loc_match.group(1)
            m = _URL_RE.match(url)
            if m:
                entries.append({"slug": m.group("slug"), "quarter": m.group("quarter"), "url": url})

    if entries:
        cache_set_json(_SITEMAP_CACHE_KEY, entries, _SITEMAP_TTL)
    logger.info("arthneeti_client: sitemap indexed", entries=len(entries))
    return entries


def find_insights_url(company_name: str, quarter: str) -> str | None:
    """`quarter` is our own "Q1 FY27" format. Returns the best-matching
    arthneeti insights URL for this exact company+quarter, or None if
    nothing confidently matches (company not covered, or only other
    quarters are)."""
    quarter_slug = quarter.strip().lower().replace(" ", "-")
    if not re.match(r"^q[1-4]-fy\d{2}$", quarter_slug):
        return None

    index = _fetch_sitemap_index()
    if not index:
        return None

    target = _normalize(company_name)
    same_quarter = [e for e in index if e["quarter"] == quarter_slug]
    if not same_quarter:
        return None

    exact = [e for e in same_quarter if e["slug"] == target]
    if exact:
        return exact[0]["url"]

    slugs = [e["slug"] for e in same_quarter]
    close = difflib.get_close_matches(target, slugs, n=1, cutoff=_MIN_SLUG_SIMILARITY)
    if close:
        return next(e["url"] for e in same_quarter if e["slug"] == close[0])

    return None


def _json_unescape(s: str) -> str:
    """Decode one JSON-string-literal's worth of backslash escapes (\\n,
    \\", \\uXXXX, ...) via the stdlib JSON decoder, which correctly leaves
    genuine UTF-8 characters untouched. Real bug found live (2026-09-15,
    Jyothy Labs' page): the previous approach
    (`raw.encode().decode("unicode_escape")`) treated the whole string as
    Latin-1 bytes, mangling every non-ASCII character it touched — a plain
    curly apostrophe in "company's" came out as "companyâ€™s" (each UTF-8
    byte reinterpreted as its own garbage code point). `json.loads` applies
    only the actual JSON escape grammar, so real Unicode text survives."""
    try:
        return json.loads(f'"{s}"')
    except json.JSONDecodeError:
        return s


def _extract_sections(decoded_rsc: str) -> list[dict]:
    """Pairs each `<h2>` heading with the next `$L26` "answer" block that
    falls before the following heading — matches the page's own structure
    (confirmed live on 2 different companies/templates, 2026-09-15).
    Headings with no answer between them (FAQ/Related/nav furniture) are
    silently skipped, not fabricated as empty sections."""
    headings = [
        (m.start(), _json_unescape(m.group(1)))
        for m in re.finditer(r'"h2",null,\{[^}]*?"children":"([^"]+)"', decoded_rsc)
    ]
    # The RSC module reference number ("$L25", "$L26", ...) is a per-page
    # bundle index, not a stable component name — confirmed it differs
    # between L&T's page (uses $L26) and Jyothy Labs' (uses $L25), so
    # matching a fixed number missed every page but the one it was
    # written against. Match any numeric ref instead.
    answers = [
        (m.start(), _json_unescape(m.group(1)))
        for m in re.finditer(r'"\$L\d+",null,\{"answer":"((?:[^"\\]|\\.)*)"', decoded_rsc)
    ]

    sections = []
    seen_headings = set()
    for i, (hpos, heading) in enumerate(headings):
        if heading in seen_headings:
            continue
        next_pos = headings[i + 1][0] if i + 1 < len(headings) else float("inf")
        match = next((a for apos, a in answers if hpos < apos < next_pos), None)
        if not match:
            continue
        bullets = [b.strip("- ").strip() for b in match.split("\n") if b.strip().startswith("-")]
        if bullets:
            sections.append({"heading": heading, "bullets": bullets})
            seen_headings.add(heading)
    return sections


def fetch_highlights(url: str) -> list[dict] | None:
    """Fetch and parse one arthneeti insights page into
    [{"heading": str, "bullets": [str, ...]}, ...]. Never raises — returns
    None on any failure (network, no RSC payload found, no sections
    extracted)."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("arthneeti_client: page fetch failed", url=url, error=str(e))
        return None

    # `_json_unescape`d once here at the whole-blob level (real bug found
    # 2026-09-15: the structural markers this module's regexes look for —
    # `"h2"`, `"$L25"`, `"answer"` — appear in the raw chunk text as
    # `\"h2\"` etc, escaped one level deeper than the finished page's own
    # RSC tree; the old `unicode_escape` approach happened to unescape
    # that layer too, which is the only reason it ever matched anything,
    # but did so by mangling every non-ASCII byte in the process). A
    # second, per-match `_json_unescape` pass happens in `_extract_sections`
    # below — the extracted heading/answer text is itself still
    # one JSON-escape layer deep (its own literal `\n`s, `\"`s) after this
    # first pass resolves the structural layer.
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', resp.text, re.S)
    if not chunks:
        logger.warning("arthneeti_client: no RSC payload found", url=url)
        return None
    decoded = _json_unescape("".join(chunks))

    sections = _extract_sections(decoded)
    if not sections:
        logger.warning("arthneeti_client: no sections extracted", url=url)
        return None
    return sections


def ingest_concall_highlights(
    db: Session, *, transcript_id: str, company_id: str, company_name: str, quarter: str,
) -> ConcallHighlight | None:
    """Resolve this company+quarter to an arthneeti page and store its
    highlight sections. Returns None (never raises) if no confident match
    is found or the fetch/parse fails — caller falls back to the
    deterministic generator in that case."""
    if not quarter:
        return None
    url = find_insights_url(company_name, quarter)
    if url is None:
        return None
    sections = fetch_highlights(url)
    if sections is None:
        return None

    row = ConcallHighlight(
        id=str(uuid.uuid4()), transcript_id=transcript_id, company_id=company_id,
        source="ARTHNEETI", sections=sections, source_url=url,
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add(row)
    logger.info("arthneeti_client: highlights ingested", company_id=company_id, url=url, sections=len(sections))
    return row
