"""The report's exhibits: one data set per chart, drawn as SVG for the PDF
and as a native chart in the Excel export. Every exhibit is built from
figures already in the report; history and forecast sit on one axis with the
forecast marked.
"""
from __future__ import annotations

from html import escape

_COLOURS = ("#c79a3b", "#1f5d55", "#e0793c", "#4d7190", "#4fb3a0", "#66716d")  # the editorial report's palette
CR = 1e7


def _series(name: str, values: list) -> dict:
    return {"name": name, "values": [None if v is None else float(v) for v in values]}


def build_exhibits(r: dict) -> list[dict]:
    v = r["valuation"]
    if not v or "skipped" in v:
        return []
    base = v["scenarios"]["Base"]
    rows = base["rows"]
    annual = sorted(r["annual"], key=lambda a: a["end"])
    cash = r["cash"]["rows"] if r.get("cash") else []
    hist, fore = [a["label"] for a in annual], [y["label"] for y in rows]
    labels, split = hist + fore, len(hist)
    out: list[dict] = []

    def add(title: str, unit: str, kind: str, x: list[str], series: list[dict], note: str, forecast_from: int | None = None) -> None:
        series = [s for s in series if any(val is not None for val in s["values"])]
        if series and len(x) >= 2:
            out.append({"n": len(out) + 1, "title": title, "unit": unit, "kind": kind, "labels": x, "series": series, "note": note,
                        "forecast_from": forecast_from})

    def past(key: str) -> list:
        return [a.get(key) for a in annual]

    crore = lambda key: [y[key] / CR for y in rows]  # noqa: E731
    blank = [None] * len(fore)

    add("Revenue: reported and net of excise" if v["has_excise"] else "Revenue", "₹ crore", "line", labels,
        [_series("Revenue as reported", past("revenue") + crore("revenue"))]
        + ([_series("Revenue net of excise", past("net_revenue") + crore("net_revenue"))] if v["has_excise"] else []),
        "Reported revenue includes excise the company collects; the net line is the economic one." if v["has_excise"]
        else "Reported history and the Base-case forecast.", split)
    profit_key = "profit_continuing" if any(a.get("profit_continuing") is not None for a in annual) else "profit"
    add("Profit before and after tax", "₹ crore", "line", labels,
        [_series("Profit before tax", past("pbt_before_exceptional") + crore("pbt")), _series("Profit after tax", past(profit_key) + crore("pat"))],
        "History is before exceptional items and excludes discontinued operations where the filing separates them.", split)
    if rows[0].get("dps") is not None:
        add("Earnings and dividend per share", "₹ per share", "line", labels,
            [_series("Earnings per share", past("eps") + [y["eps"] for y in rows]), _series("Dividend per share", [None] * split + [y["dps"] for y in rows])],
            "Forecast earnings are the owners' share; the dividend holds the last year's payout ratio.", split)
    if v["by_segment"]:
        names = [u["name"] for u in rows[0]["units"]]
        add(f"Segment revenue: {hist[-1] if hist else 'latest'} and {fore[-1]}", "₹ crore", "bar", names,
            [_series(hist[-1] if hist else "Latest", [u["revenue0"] / CR for u in v["units"]]),
             _series(fore[-1], [u["revenue"] / CR for u in rows[-1]["units"]])], "Before inter-segment elimination.")
        add(f"Segment result: {hist[-1] if hist else 'latest'} and {fore[-1]}", "₹ crore", "bar", names,
            [_series(hist[-1] if hist else "Latest", [u["revenue0"] * u.get("margin0", u["margin"]) / CR for u in v["units"]]),
             _series(fore[-1], [u["result"] / CR for u in rows[-1]["units"]])],
            "A segment's share of revenue and its share of profit are different things.")
        top = max(range(len(names)), key=lambda i: rows[0]["units"][i]["result"])
        add(f"{names[top]}: share of segment result", "%", "line", fore,
            [_series(names[top], [100 * y["units"][top]["result"] / sum(u["result"] for u in y["units"]) for y in rows])],
            "How far the forecast leans on its largest profit source.")
        add("Segment margins in the forecast", "%", "bar", names,
            [_series("Margin used", [100 * u["margin"] for u in v["units"]]), _series("Last full year", [100 * u.get("margin0", u["margin"]) for u in v["units"]])],
            "Where the margin used differs from last year's, the Assumptions table says why.")
    if rows[0].get("cfo") is not None:
        c_labels = [c["label"] for c in cash]
        both = c_labels + fore
        add("Operating cash flow and capital expenditure", "₹ crore", "line", both,
            [_series("Operating cash flow", [c.get("cfo") for c in cash] + crore("cfo")), _series("Capital expenditure", [c.get("capex") for c in cash] + crore("capex"))],
            "Forecast operating cash flow is profit plus depreciation less working-capital growth.", len(c_labels))
        add("Cash after capex against dividends", "₹ crore", "line", both,
            [_series("Operating cash flow less capex", [c.get("fcf") for c in cash] + [(y["cfo"] - y["capex"]) / CR for y in rows]),
             _series("Dividends paid", [c.get("dividends") for c in cash] + crore("dividends"))],
            "Where the dividend line sits above the cash line, the payout is funded from the balance sheet.", len(c_labels))
        add("Working capital", "₹ crore", "line", both,
            [_series("Inventories", [c.get("inventories") for c in cash] + [next(x["value"] for x in y["working_capital"] if x["label"] == "Inventories") / CR for y in rows]),
             _series("Trade receivables", [c.get("receivables") for c in cash] + [next(x["value"] for x in y["working_capital"] if x["label"] == "Trade receivables") / CR for y in rows]),
             _series("Trade payables", [None] * len(cash) + [next(x["value"] for x in y["working_capital"] if x["label"] == "Trade payables") / CR for y in rows])],
            "Each line is held at its share of revenue in the last full year.", len(c_labels))
        if rows[0].get("sheet"):
            add("Cash and current investments, and borrowings", "₹ crore", "line", ["Opening"] + fore,
                [_series("Cash and current investments", [v["sheet0"]["liquid"] / CR] + crore("liquid_close")),
                 _series("Borrowings", [v["sheet0"]["borrowings"] / CR] + [y["sheet"]["borrowings"] / CR for y in rows])],
                "Borrowings are held flat; whatever cash is left each year accumulates.", 1)
        add("Net margin and payout", "%", "line", fore,
            [_series("Profit after tax ÷ revenue" + (" net of excise" if v["has_excise"] else ""), [100 * y["pat"] / y["net_revenue"] for y in rows]),
             _series("Dividends ÷ profit", [100 * y["dividends"] / y["pat"] if y["pat"] > 0 else None for y in rows])],
            "Base case.")
    if base.get("dcf_pv"):
        add("Free cash flow and its present value", "₹ crore", "bar", fore,
            [_series("Free cash flow to the firm", crore("fcff")), _series("Present value", [x / CR for x in base["dcf_pv"]])],
            "The first year counts only the part of it still to come.")
    bridge = v["equity_bridge"]["items"]
    if bridge and base.get("dcf_ev"):
        add("From business value to equity value", "₹ crore", "bar", ["Business value"] + [i["label"][:26] for i in bridge],
            [_series("₹ crore", [base["dcf_ev"] * (1 - v["equity_bridge"]["minority"]) / CR] + [i["value"] / CR for i in bridge])],
            "Discounted cash-flow value of the business after the minority share, then each asset or liability added once.")
    if base.get("sotp_parts"):
        add("Sum of the parts", "₹ crore", "bar", [p["name"] for p in base["sotp_parts"]],
            [_series("Value", [p["value"] / CR for p in base["sotp_parts"]])], "Next year's segment result × the multiple of its line of business.")
    if v.get("pe_parts"):
        add("Peer earnings multiples by segment", "×", "bar", [p["name"] for p in v["pe_parts"]],
            [_series("Price ÷ earnings of peers", [p["multiple"] for p in v["pe_parts"]])], "Trailing multiples of the listed peers matched to each segment.")
    lens_names = [(k, n) for k, n in (("dcf", "Cash flow"), ("sotp", "Sum of parts"), ("relative", "Peer multiple"), ("average", "Blend")) if k in base]
    if lens_names:
        add("Value per share by method, against the price", "₹ per share", "bar", [n for _, n in lens_names],
            [_series("Model", [base[k] for k, _ in lens_names]), _series("Market price", [v["price"]] * len(lens_names))],
            "The methods are expected to disagree; the spread is the uncertainty.")
        scen = v["scenarios"]
        add("Blended value by scenario, against the price", "₹ per share", "bar", ["Bear", "Base", "Bull"],
            [_series("Blended reference", [scen[k].get("average") for k in ("Bear", "Base", "Bull")]), _series("Market price", [v["price"]] * 3)],
            "Scenarios are sets of assumptions, not probabilities.")
    if v.get("sensitivity"):
        s = v["sensitivity"]
        add("Cash-flow value against the cost of capital", "₹ per share", "line", [f"{w:.1%}" for w in s["waccs"]],
            [_series(f"Terminal growth {row['g']:.1%}", row["values"]) for row in s["rows"][::2]], "One line per terminal growth rate.")
    quarters = sorted(r.get("quarters") or [], key=lambda q: q["end"])
    add("Latest quarters", "₹ crore", "bar", [q["label"] for q in quarters],
        [_series("Revenue net of excise" if v["has_excise"] else "Revenue", [q.get("net_revenue") if v["has_excise"] else q.get("revenue") for q in quarters]),
         _series("Profit after tax", [q.get("profit") for q in quarters])], "As filed with the exchange.")
    return out


def _fmt(x: float, span: float) -> str:
    if abs(x) >= 100000:
        return f"{x / 1000:,.0f}k"
    if span >= 50 or abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:,.1f}" if span >= 5 else f"{x:,.2f}"


def svg(e: dict, width: int = 520, height: int = 250) -> str:
    """One exhibit as an SVG chart."""
    left, right, top, bottom = 52, 10, 10, 58
    values = [val for s in e["series"] for val in s["values"] if val is not None]
    lo, hi = min(values + [0.0]) if e["kind"] == "bar" else min(values), max(values + [0.0]) if e["kind"] == "bar" else max(values)
    if hi == lo:
        hi, lo = hi + 1, lo - 1
    pad = (hi - lo) * 0.08
    hi, lo = hi + pad, (lo - pad if lo < 0 or e["kind"] == "line" else lo)
    plot_w, plot_h, n = width - left - right, height - top - bottom, len(e["labels"])
    y = lambda val: top + plot_h * (1 - (val - lo) / (hi - lo))  # noqa: E731
    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(e["title"])}">']
    for k in range(5):
        val = lo + (hi - lo) * k / 4
        parts.append(f'<line x1="{left}" x2="{width - right}" y1="{y(val):.1f}" y2="{y(val):.1f}" stroke="#ebebe4"/>'
                     f'<text x="{left - 5}" y="{y(val) + 3:.1f}" font-size="8.5" fill="#7b838a" text-anchor="end">{_fmt(val, hi - lo)}</text>')
    step = plot_w / n
    centre = lambda i: left + step * (i + 0.5)  # noqa: E731
    if e.get("forecast_from") is not None and 0 < e["forecast_from"] < n:
        x0 = left + step * e["forecast_from"]
        parts.append(f'<rect x="{x0:.1f}" y="{top}" width="{width - right - x0:.1f}" height="{plot_h}" fill="#f6f5ef"/>'
                     f'<text x="{x0 + 4:.1f}" y="{top + 10}" font-size="8" fill="#7b838a">forecast</text>')
    if lo < 0 < hi:
        parts.append(f'<line x1="{left}" x2="{width - right}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="#7b838a" stroke-width="0.8"/>')
    for i, label in enumerate(e["labels"]):
        words = str(label)
        text = words if len(words) <= 13 else words[:12] + "…"
        angle = f' transform="rotate(-28 {centre(i):.1f} {height - bottom + 12})" text-anchor="end"' if n > 6 or any(len(str(l)) > 8 for l in e["labels"]) else ' text-anchor="middle"'
        parts.append(f'<text x="{centre(i):.1f}" y="{height - bottom + 12}" font-size="8.5" fill="#4a5158"{angle}>{escape(text)}</text>')
    for j, s in enumerate(e["series"]):
        colour = _COLOURS[j % len(_COLOURS)]
        if e["kind"] == "bar":
            group = step * 0.72
            bar = group / len(e["series"])
            for i, val in enumerate(s["values"]):
                if val is None:
                    continue
                x = centre(i) - group / 2 + bar * j
                parts.append(f'<rect x="{x:.1f}" y="{min(y(val), y(0)):.1f}" width="{bar * 0.9:.1f}" height="{abs(y(val) - y(0)):.1f}" fill="{colour}"/>')
        else:
            points = [(centre(i), y(val)) for i, val in enumerate(s["values"]) if val is not None]
            if len(points) > 1:
                parts.append(f'<polyline fill="none" stroke="{colour}" stroke-width="1.8" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in points)}"/>')
            parts += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.2" fill="{colour}"/>' for a, b in points]
    x = left
    for j, s in enumerate(e["series"]):
        parts.append(f'<rect x="{x}" y="{height - 12}" width="9" height="9" fill="{_COLOURS[j % len(_COLOURS)]}"/>'
                     f'<text x="{x + 12}" y="{height - 4}" font-size="9" fill="#4a5158">{escape(s["name"][:34])}</text>')
        x += 22 + 5.2 * len(s["name"][:34])
    parts.append("</svg>")
    return "".join(parts)
