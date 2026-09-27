"""Base sector framework — enhanced with thresholds, scoring, and metric status."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SectorMetric:
    name: str                        # key in metrics dict
    label: str                       # display label
    weight: float                    # weight within sector score (sum → 1.0 per category)
    importance: str                  # "high" | "medium" | "low"
    direction: str                   # "higher_is_better" | "lower_is_better" | "neutral"
    unit: str = "%"
    description: str = ""
    # Piecewise thresholds: [(value, score_0_100)…] sorted ascending by value
    # higher_is_better: low value → low score; lower_is_better: reverse meaning is built in
    thresholds: list[tuple[float, float]] = field(default_factory=list)
    available_from_yfinance: bool = True   # False → operational/filing data needed
    na_message: str = "Operational data required"
    # Which sector types this metric applies to. ["all"] means universal.
    # Examples: ["bank"], ["nbfc"], ["bank", "nbfc"], ["insurance"]
    applicable_to: list[str] = field(default_factory=lambda: ["all"])


@dataclass
class SectorRedFlag:
    condition: str                   # human-readable condition identifier
    severity: str                    # "HIGH" | "MEDIUM" | "LOW"
    title: str
    description: str


def _piecewise(value: float, pts: list[tuple[float, float]]) -> float:
    """Piecewise-linear interpolation between threshold breakpoints."""
    if not pts:
        return 50.0
    if value <= pts[0][0]:
        return pts[0][1]
    if value >= pts[-1][0]:
        return pts[-1][1]
    for i in range(1, len(pts)):
        x0, s0 = pts[i - 1]
        x1, s1 = pts[i]
        if x0 <= value <= x1:
            if x1 == x0:
                return s0
            t = (value - x0) / (x1 - x0)
            return s0 + t * (s1 - s0)
    return 50.0


def metric_status(value: float | None, metric: SectorMetric) -> str:
    """Return EXCELLENT / GOOD / FAIR / POOR for a metric value."""
    if value is None:
        return "N/A"
    if not metric.thresholds:
        return "N/A"
    score = _piecewise(value, metric.thresholds)
    if score >= 80:
        return "EXCELLENT"
    if score >= 60:
        return "GOOD"
    if score >= 40:
        return "FAIR"
    return "POOR"


import re as _re


def _eval_condition(condition: str, metrics: dict) -> bool | None:
    """
    Evaluate a simple condition string like "ebitda_margin < 8" against metrics.
    Supports operators: <, >, <=, >=, ==, !=
    Returns None when the metric value is missing (condition cannot be evaluated).
    """
    m = _re.match(
        r"^\s*(\w+)\s*(<=|>=|<|>|==|!=)\s*([+-]?\d+(?:\.\d+)?)\s*$",
        condition,
    )
    if not m:
        return None
    key, op, threshold_str = m.group(1), m.group(2), m.group(3)
    value = metrics.get(key)
    if value is None:
        return None
    try:
        value = float(value)
        threshold = float(threshold_str)
    except (TypeError, ValueError):
        return None
    ops = {
        "<":  value < threshold,
        ">":  value > threshold,
        "<=": value <= threshold,
        ">=": value >= threshold,
        "==": value == threshold,
        "!=": value != threshold,
    }
    return ops.get(op, None)


class SectorFramework:
    """Base class for all sector frameworks."""
    sector_name: str = "Generic"
    sector_aliases: list[str] = []

    SECTOR_WEIGHTS: dict[str, float] = {
        "growth": 0.25,
        "profitability": 0.21,
        "cash_flow": 0.19,
        "balance_sheet": 0.19,
        "efficiency": 0.10,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        """Return sector-specific key metrics in display order."""
        raise NotImplementedError

    def key_metrics_for(self, basic_industry: str | None) -> list[SectorMetric]:
        """`key_metrics()`, filtered to the ones applicable to this specific
        `basic_industry` sub-type (a metric with `applicable_to=["all"]`
        always stays in). Needed for framework classes that cover several
        genuinely different business models under one `sector_name` — e.g.
        PharmaSector spans both hospitals and drugmakers, and a hospital
        has no ANDA pipeline or R&D/revenue ratio, just as a pure-play
        drugmaker has no bed occupancy or ARPOB. Without this, every
        sub-type sees every other sub-type's metrics rendered as a
        permanent, confusing "Not disclosed" rather than simply omitted.

        Use this (not the raw `key_metrics()`) at DISPLAY/comparison call
        sites only — the sector-analysis key_metrics list and peer
        sector-metric columns. Scoring (`compute_sector_score`) and red-flag
        evaluation deliberately keep using the raw `key_metrics()`: a metric
        genuinely absent for a sub-type already contributes zero weight
        there (its value resolves to None and is skipped), so filtering it
        out wouldn't change the score — only what gets shown."""
        if not basic_industry:
            return self.key_metrics()
        return [m for m in self.key_metrics() if "all" in m.applicable_to or basic_industry in m.applicable_to]

    def required_metric_ids(self) -> dict[str, list[str]]:
        """The declarative "which metrics does this sector need, by
        category" view — Architecture v2 Stage 5. Derived live from
        key_metrics() and app/metrics/registry.py's categories, not a
        second hand-maintained config file: key_metrics() (with its
        weights, thresholds, direction) is already the real source of
        truth for scoring, per the doc's own System A/B/C separation
        (calculation code owns thresholds, not a YAML file) — this just
        projects "which ids, grouped by category" out of it, matching the
        shape Architecture v2 chatgpt.md's own sector-config example uses
        (section 8: `required_metrics: {profitability: [roe, roa, nim], ...}`).
        A metric_id with no registry entry lands under "unregistered" —
        that's a real gap this exposes rather than hides."""
        from app.metrics.registry import get_metric

        grouped: dict[str, list[str]] = {}
        for m in self.key_metrics():
            definition = get_metric(m.name)
            category = definition.category if definition else "unregistered"
            grouped.setdefault(category, []).append(m.name)
        return grouped

    def red_flag_rules(self) -> list[SectorRedFlag]:
        """Return sector-specific red flag rules."""
        return []

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        """
        Evaluate a red flag rule.  Subclasses may override for custom logic,
        but the base implementation auto-evaluates simple "metric op value"
        condition strings — so overrides are only needed for compound logic.
        """
        result = _eval_condition(rule.condition, metrics)
        return bool(result) if result is not None else False

    def _compute_special_metric(self, name: str, metrics: dict, data: dict) -> float | None:
        """Override in subclass to compute sector-specific unavailable metrics."""
        return None

    def extract_sector_metrics(self, metrics: dict, financial_data: dict) -> dict:
        """Extract and compute sector-specific metric values. Checks the
        generic provenance-ledger bridge (app/sectors/ledger_bridge.py)
        before falling back to _compute_special_metric — any sector that
        has a ledger value for a declared metric gets it automatically,
        without needing its own bridge override (BankingSector/NBFCSector's
        existing _banking_authoritative_metrics-based overrides still work
        exactly as before; this is an additive fallback, not a replacement)."""
        result = {}
        ledger_bridge = (financial_data or {}).get("_ledger_metrics", {})
        for m in self.key_metrics():
            if m.available_from_yfinance:
                result[m.name] = metrics.get(m.name)
            elif m.name in ledger_bridge:
                result[m.name] = ledger_bridge[m.name]
            else:
                computed = self._compute_special_metric(m.name, metrics, financial_data)
                result[m.name] = computed
        return result

    def compute_sector_score(self, metrics: dict, financial_data: dict) -> float | None:
        """
        Weighted average of per-metric scores for available metrics.
        Normalises weight over available metrics so N/A fields don't zero the score.

        Checks the ledger bridge (app/sectors/ledger_bridge.py) before
        falling back to `_compute_special_metric`, mirroring
        `extract_sector_metrics()`'s exact resolution order. Real bug fixed
        2026-09-17: this method used to skip the ledger dict entirely and
        call `_compute_special_metric` directly for every non-yfinance
        metric — so a ledger-bridged value (e.g. IT Services' real,
        HIGH-confidence `deal_wins_tcv` sourced from an earnings-call
        transcript) would render correctly in the displayed key_metrics
        list (which goes through `extract_sector_metrics()`) but silently
        never contribute to the actual sector score, since
        `_compute_special_metric` doesn't know about ledger-bridged data
        unless a subclass separately re-implements the lookup itself (none
        do). Same fix needed for FintechSector's new ledger-sourced metrics
        (gtv_growth, take_rate, contribution_margin) to actually score.
        """
        ledger_bridge = (financial_data or {}).get("_ledger_metrics", {})
        total_weight = 0.0
        weighted_score = 0.0
        for sm in self.key_metrics():
            if not sm.thresholds:
                continue
            if sm.available_from_yfinance:
                val = metrics.get(sm.name)
            elif sm.name in ledger_bridge:
                val = ledger_bridge[sm.name]
            else:
                val = self._compute_special_metric(sm.name, metrics, financial_data)
            if val is None:
                continue
            try:
                score = _piecewise(float(val), sm.thresholds)
            except (TypeError, ValueError):
                continue
            weighted_score += score * sm.weight
            total_weight += sm.weight
        if total_weight == 0:
            return None
        return round(weighted_score / total_weight, 1)

    def identify_risks(self, metrics: dict, financial_data: dict) -> list[dict]:
        """Same ledger-bridge merge fix as `compute_sector_score()`
        (2026-09-17), same underlying bug: a red flag `condition` string
        referencing a ledger-only metric (e.g. IT Services' own
        "attrition_rate > 22") is evaluated by `_eval_condition()` against
        `metrics` alone — which never contains ledger-bridged values — so
        it could never fire even when a real, HIGH-confidence attrition
        figure was on file. Merging the ledger dict into a `metrics` copy
        here, once, means every existing and future red flag condition
        (simple string or custom `_check_rule` override) sees the same
        fully-resolved values `extract_sector_metrics()` already computes
        for display — no framework needs its own ledger lookup just to
        make a red flag work."""
        ledger_bridge = (financial_data or {}).get("_ledger_metrics", {})
        if ledger_bridge:
            augmented = dict(metrics)
            for m in self.key_metrics():
                if not m.available_from_yfinance and m.name in ledger_bridge:
                    augmented[m.name] = ledger_bridge[m.name]
            metrics = augmented
        risks = []
        for rule in self.red_flag_rules():
            try:
                triggered = self._check_rule(rule, metrics, financial_data)
                if triggered:
                    risks.append({
                        "severity": rule.severity,
                        "category": "SECTOR",
                        "title": rule.title,
                        "description": rule.description,
                        "confidence": 0.82,
                    })
            except Exception:
                pass
        return risks

    def score_key_metric(self, name: str, value: float | None) -> float | None:
        """Score a single metric using its defined thresholds (0-100)."""
        if value is None:
            return None
        for sm in self.key_metrics():
            if sm.name == name and sm.thresholds:
                return round(_piecewise(value, sm.thresholds), 1)
        return None

    def describe(self) -> dict:
        return {
            "sector": self.sector_name,
            "weights": self.SECTOR_WEIGHTS,
            "metrics": [
                {
                    "name": m.name, "label": m.label, "weight": m.weight,
                    "importance": m.importance, "direction": m.direction,
                    "unit": m.unit, "description": m.description,
                    "available": m.available_from_yfinance,
                }
                for m in self.key_metrics()
            ],
        }
