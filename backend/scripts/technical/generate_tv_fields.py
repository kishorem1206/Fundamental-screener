"""Regenerate the TradingView field catalog (JSON) from the public fields pages.

Usage (from backend/):  PYTHONPATH=. .venv/bin/python3.12 scripts/generate_tv_fields.py
Writes app/data/tv_fields/<market_type>.json
"""
import html
import json
import re
import urllib.request
from pathlib import Path

BASE = "https://shner-elmo.github.io/TradingView-Screener/fields/"
OUT = Path(__file__).resolve().parent.parent.parent / "app" / "technical" / "data" / "tv_fields"
PAGES = ["stocks", "crypto", "coin", "forex", "futures", "options", "bonds", "bond", "cfd", "economics2"]


def clean(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def parse(page: str) -> list[dict]:
    s = urllib.request.urlopen(BASE + page + ".html").read().decode()
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", s, re.S):
        tds = re.findall(r"<td>(.*?)</td>", tr, re.S)
        if len(tds) < 3:
            continue
        tfs: list[str] = []
        m = re.search(r"<summary>(.*?)</summary>", tds[0], re.S)
        if m:  # field with timeframe variants
            name = clean(m.group(1))
            tfs = [clean(li).split("|", 1)[1] for li in re.findall(r"<li>(.*?)</li>", tds[0], re.S) if "|" in li]
        else:
            name = clean(tds[0])
        values: list[str] = []
        count = 0
        if len(tds) > 3:
            c = re.search(r"<summary>(\d+)</summary>", tds[3])
            count = int(c.group(1)) if c else 0
            values = [clean(li) for li in re.findall(r"<li>(.*?)</li>", tds[3], re.S)]
        out.append({"name": name, "label": clean(tds[1]), "type": clean(tds[2]),
                    "timeframes": tfs, "value_count": count, "values": values})
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for page in PAGES:
        fields = parse(page)
        (OUT / f"{page}.json").write_text(json.dumps(fields, separators=(",", ":")))
        print(page, len(fields))
