"""Hand-rolled inline SVG charts — no JS charting library, no CDN.

Per banking_stock_analysis_report.md section 44 (self-containment) and section
52's recorded decision: chart markup is plain <svg> built from the same data
the template renders, so the live HTML and the Playwright-printed PDF are
pixel-identical, and the report stays fully readable with no network access.

Colors reference the page's CSS custom properties (--teal, --gold, etc.) via
var() — this works because these <svg> strings are inlined directly into the
HTML document, sharing its stylesheet cascade, not loaded as separate files.
"""
from __future__ import annotations

import math

_SERIES_COLORS = ["var(--gold)", "var(--teal)", "var(--orange)", "var(--red)", "var(--ink-dim)"]


def _fmt(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _nice_ticks(vmin: float, vmax: float, count: int = 4) -> list[float]:
    if vmin == vmax:
        vmin, vmax = vmin - 1, vmax + 1
    span = vmax - vmin
    step = span / count
    magnitude = 10 ** math.floor(math.log10(step)) if step > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if magnitude * m >= step:
            step = magnitude * m
            break
    start = math.floor(vmin / step) * step
    ticks = []
    v = start
    while v <= vmax + step / 2:
        ticks.append(round(v, 6))
        v += step
    return ticks


def line_chart(
    series: list[dict],
    *,
    width: int = 620,
    height: int = 260,
    unit: str = "%",
    fill: bool = False,
) -> str:
    """series: [{"label": str, "points": [(x_label, value|None), ...], "color": optional css color}]
    Missing values (None) create a gap in the line rather than a fabricated point.
    """
    pad_l, pad_r, pad_t, pad_b = 44, 16, 28, 30
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    x_labels = series[0]["points"] if series and series[0]["points"] else []
    n = len(x_labels)
    if n == 0:
        return _empty_chart(width, height, "No historical data available")

    all_vals = [v for s in series for (_, v) in s["points"] if v is not None]
    if not all_vals:
        return _empty_chart(width, height, "No historical data available")

    vmin, vmax = min(all_vals), max(all_vals)
    ticks = _nice_ticks(vmin, vmax)
    y_lo, y_hi = ticks[0], ticks[-1]
    if y_hi == y_lo:
        y_hi = y_lo + 1

    def x_at(i: int) -> float:
        return pad_l + (i / max(n - 1, 1)) * plot_w

    def y_at(v: float) -> float:
        return pad_t + plot_h - ((v - y_lo) / (y_hi - y_lo)) * plot_h

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="chart-svg">']

    for t in ticks:
        y = y_at(t)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
                      f'stroke="var(--glass-border)" stroke-width="1" />')
        parts.append(f'<text x="{pad_l - 8}" y="{y + 3:.1f}" text-anchor="end" '
                      f'class="chart-axis-label">{_fmt(t)}{unit}</text>')

    step = max(1, n // 6)
    for i, (label, _) in enumerate(x_labels):
        if i % step != 0 and i != n - 1:
            continue
        parts.append(f'<text x="{x_at(i):.1f}" y="{height - 8}" text-anchor="middle" '
                      f'class="chart-axis-label">{label}</text>')

    for si, s in enumerate(series):
        color = s.get("color") or _SERIES_COLORS[si % len(_SERIES_COLORS)]
        segments: list[list[tuple[float, float]]] = [[]]
        for i, (_, v) in enumerate(s["points"]):
            if v is None:
                if segments[-1]:
                    segments.append([])
                continue
            segments[-1].append((x_at(i), y_at(v)))
        for seg in segments:
            if len(seg) < 2:
                continue
            path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in seg)
            if fill:
                base_y = y_at(y_lo)
                area_d = path_d + f" L {seg[-1][0]:.1f},{base_y:.1f} L {seg[0][0]:.1f},{base_y:.1f} Z"
                parts.append(f'<path d="{area_d}" fill="{color}" fill-opacity="0.14" stroke="none" />')
            parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="2.25" '
                          f'stroke-linecap="round" stroke-linejoin="round" />')
            for x, y in seg:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.75" fill="{color}" />')

    if len(series) > 1:
        lx = pad_l
        ly = 14
        for si, s in enumerate(series):
            color = s.get("color") or _SERIES_COLORS[si % len(_SERIES_COLORS)]
            parts.append(f'<circle cx="{lx + 5}" cy="{ly}" r="4" fill="{color}" />')
            parts.append(f'<text x="{lx + 14}" y="{ly + 4}" class="chart-legend-label">{s["label"]}</text>')
            lx += 18 + len(s["label"]) * 6.5 + 18

    parts.append("</svg>")
    return "".join(parts)


def area_chart(series: list[dict], *, width: int = 620, height: int = 260, unit: str = "%") -> str:
    return line_chart(series, width=width, height=height, unit=unit, fill=True)


def bar_chart(
    categories: list[str],
    series: list[dict],
    *,
    width: int = 620,
    height: int = 260,
    unit: str = "%",
    stacked: bool = False,
) -> str:
    """series: [{"label": str, "values": [float|None, ...], "color": optional}]
    values aligned with `categories`. stacked=True sums segments per category."""
    pad_l, pad_r, pad_t, pad_b = 44, 16, 28, 34
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    n = len(categories)
    if n == 0 or not series:
        return _empty_chart(width, height, "No data available")

    if stacked:
        totals = [sum((s["values"][i] or 0) for s in series) for i in range(n)]
        vmax = max(totals) if totals else 1
        vmin = 0.0
    else:
        all_vals = [v for s in series for v in s["values"] if v is not None]
        if not all_vals:
            return _empty_chart(width, height, "No data available")
        vmin = min(0.0, min(all_vals))
        vmax = max(all_vals)

    ticks = _nice_ticks(vmin, vmax)
    y_lo, y_hi = ticks[0], ticks[-1]
    if y_hi == y_lo:
        y_hi = y_lo + 1

    def y_at(v: float) -> float:
        return pad_t + plot_h - ((v - y_lo) / (y_hi - y_lo)) * plot_h

    group_w = plot_w / n
    bar_gap = group_w * 0.28
    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="chart-svg">']

    for t in ticks:
        y = y_at(t)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
                      f'stroke="var(--glass-border)" stroke-width="1" />')
        parts.append(f'<text x="{pad_l - 8}" y="{y + 3:.1f}" text-anchor="end" '
                      f'class="chart-axis-label">{_fmt(t)}{unit}</text>')

    zero_y = y_at(0)
    n_series = len(series)
    bar_w = (group_w - bar_gap) / (1 if stacked else max(n_series, 1))

    for ci in range(n):
        gx = pad_l + ci * group_w + bar_gap / 2
        if stacked:
            running = 0.0
            for si, s in enumerate(series):
                v = s["values"][ci] or 0
                color = s.get("color") or _SERIES_COLORS[si % len(_SERIES_COLORS)]
                y0, y1 = y_at(running), y_at(running + v)
                parts.append(f'<rect x="{gx:.1f}" y="{y1:.1f}" width="{bar_w:.1f}" '
                              f'height="{max(y0 - y1, 0):.1f}" fill="{color}" rx="2" />')
                running += v
        else:
            for si, s in enumerate(series):
                v = s["values"][ci]
                if v is None:
                    continue
                color = s.get("color") or _SERIES_COLORS[si % len(_SERIES_COLORS)]
                bx = gx + si * bar_w
                y = y_at(v)
                top, bot = (min(y, zero_y), max(y, zero_y))
                parts.append(f'<rect x="{bx:.1f}" y="{top:.1f}" width="{max(bar_w - 3, 1):.1f}" '
                              f'height="{max(bot - top, 0):.1f}" fill="{color}" rx="2" />')
        parts.append(f'<text x="{gx + group_w / 2 - bar_gap / 2:.1f}" y="{height - 10}" '
                      f'text-anchor="middle" class="chart-axis-label">{categories[ci]}</text>')

    if n_series > 1:
        lx, ly = pad_l, 14
        for si, s in enumerate(series):
            color = s.get("color") or _SERIES_COLORS[si % len(_SERIES_COLORS)]
            parts.append(f'<rect x="{lx}" y="{ly - 7}" width="9" height="9" rx="2" fill="{color}" />')
            parts.append(f'<text x="{lx + 14}" y="{ly + 1}" class="chart-legend-label">{s["label"]}</text>')
            lx += 18 + len(s["label"]) * 6.5 + 18

    parts.append("</svg>")
    return "".join(parts)


def scatter_chart(
    points: list[dict],
    *,
    width: int = 560,
    height: int = 360,
    x_label: str = "",
    y_label: str = "",
) -> str:
    """points: [{"label": str, "x": float, "y": float, "highlight": bool}]"""
    pad_l, pad_r, pad_t, pad_b = 50, 20, 20, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    pts = [p for p in points if p.get("x") is not None and p.get("y") is not None]
    if not pts:
        return _empty_chart(width, height, "Insufficient peer data")

    xs, ys = [p["x"] for p in pts], [p["y"] for p in pts]
    x_ticks = _nice_ticks(min(xs), max(xs), 4)
    y_ticks = _nice_ticks(min(ys), max(ys), 4)
    x_lo, x_hi = x_ticks[0], x_ticks[-1]
    y_lo, y_hi = y_ticks[0], y_ticks[-1]
    if x_hi == x_lo:
        x_hi = x_lo + 1
    if y_hi == y_lo:
        y_hi = y_lo + 1

    def x_at(v):
        return pad_l + ((v - x_lo) / (x_hi - x_lo)) * plot_w

    def y_at(v):
        return pad_t + plot_h - ((v - y_lo) / (y_hi - y_lo)) * plot_h

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="chart-svg">']
    for t in y_ticks:
        y = y_at(t)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
                      f'stroke="var(--glass-border)" stroke-width="1" />')
        parts.append(f'<text x="{pad_l - 8}" y="{y + 3:.1f}" text-anchor="end" class="chart-axis-label">{_fmt(t)}</text>')
    for t in x_ticks:
        x = x_at(t)
        parts.append(f'<text x="{x:.1f}" y="{height - 12}" text-anchor="middle" class="chart-axis-label">{_fmt(t)}</text>')

    parts.append(f'<text x="{pad_l + plot_w / 2:.1f}" y="{height - 2}" text-anchor="middle" '
                  f'class="chart-axis-title">{x_label}</text>')
    parts.append(f'<text x="12" y="{pad_t + plot_h / 2:.1f}" text-anchor="middle" '
                  f'class="chart-axis-title" transform="rotate(-90 12 {pad_t + plot_h / 2:.1f})">{y_label}</text>')

    for p in pts:
        x, y = x_at(p["x"]), y_at(p["y"])
        color = "var(--gold)" if p.get("highlight") else "var(--ink-dim)"
        r = 6 if p.get("highlight") else 4
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" '
                      f'fill-opacity="{1 if p.get("highlight") else 0.65}" />')
        if p.get("highlight"):
            parts.append(f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" '
                          f'class="chart-point-label">{p["label"]}</text>')

    parts.append("</svg>")
    return "".join(parts)


def score_bar(score: float | None, *, width: int = 300, height: int = 10) -> str:
    """Horizontal 0-100 score bar with a marker, used for verdict + category scores."""
    if score is None:
        return _empty_chart(width, height, "")
    score = max(0.0, min(100.0, score))
    marker_x = (score / 100) * width
    color = "var(--teal)" if score >= 65 else "var(--gold)" if score >= 40 else "var(--orange)" if score >= 20 else "var(--red)"
    return (
        f'<svg viewBox="0 0 {width} {height + 4}" xmlns="http://www.w3.org/2000/svg" class="score-bar-svg">'
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="{height / 2}" fill="var(--glass)" '
        f'stroke="var(--glass-border)" stroke-width="1" />'
        f'<rect x="0" y="0" width="{marker_x:.1f}" height="{height}" rx="{height / 2}" fill="{color}" />'
        f"</svg>"
    )


def _empty_chart(width: int, height: int, message: str) -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="chart-svg chart-empty">'
        f'<text x="{width / 2}" y="{height / 2}" text-anchor="middle" class="chart-empty-label">{message}</text>'
        f"</svg>"
    )
