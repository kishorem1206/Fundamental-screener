import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.technical.tradingview_screener import And, Column, Or, Query

from app.technical.infrastructure.redis.client import cache_get, cache_set
from app.logger import logger
from app.technical.shared.errors import ValidationError

CATALOG_DIR = Path(__file__).resolve().parent.parent / "data" / "tv_fields"
CACHE_TTL_SECONDS = 30  # TradingView data is near-real-time; keep the cache short

COUNTRY_MARKETS = [
    "america", "argentina", "australia", "austria", "bahrain", "bangladesh", "belgium", "brazil",
    "bulgaria", "canada", "chile", "china", "colombia", "croatia", "cyprus", "czech", "denmark",
    "egypt", "estonia", "finland", "france", "germany", "greece", "hongkong", "hungary", "iceland",
    "india", "indonesia", "ireland", "israel", "italy", "japan", "kenya", "korea", "ksa", "kuwait",
    "latvia", "lithuania", "luxembourg", "malaysia", "mexico", "morocco", "netherlands",
    "newzealand", "nigeria", "norway", "pakistan", "peru", "philippines", "poland", "portugal",
    "qatar", "romania", "rsa", "russia", "serbia", "singapore", "slovakia", "slovenia", "spain",
    "srilanka", "sweden", "switzerland", "taiwan", "thailand", "tunisia", "turkey", "uae", "uk",
    "venezuela", "vietnam",
]
OTHER_MARKETS = ["bond", "bonds", "cfd", "coin", "crypto", "economics2", "forex", "futures", "options"]
ALL_MARKETS = COUNTRY_MARKETS + OTHER_MARKETS

# Operators the UI/API may use -> how many operands each needs
OPERATORS: dict[str, str] = {
    ">": "value", ">=": "value", "<": "value", "<=": "value", "==": "value", "!=": "value",
    "crosses": "value", "crosses_above": "value", "crosses_below": "value",
    "between": "range", "not_between": "range",
    "isin": "list", "not_in": "list", "has": "list", "has_none_of": "list",
    "in_day_range": "range", "in_week_range": "range", "in_month_range": "range",
    "above_pct": "pct", "below_pct": "pct", "between_pct": "pct_range", "not_between_pct": "pct_range",
    "like": "value", "not_like": "value", "empty": "none", "not_empty": "none",
}

ETF_SCOPE = And(Column("type") == "fund", Column("typespecs").has(["etf"]))
ASSET_SCOPES = {
    "etf": lambda: ETF_SCOPE,
    "fund": lambda: Column("type") == "fund",
    "stock": lambda: And(Column("type") == "stock", Column("typespecs").has(["common", "preferred"])),
    "dr": lambda: Column("type") == "dr",
}


def market_type(market: str) -> str:
    """Which field catalog applies to a market (every country market uses the stocks catalog)."""
    return "stocks" if market in COUNTRY_MARKETS else market


@lru_cache(maxsize=None)
def load_catalog(mtype: str) -> list[dict]:
    path = CATALOG_DIR / f"{mtype}.json"
    if not path.exists():
        raise ValidationError(f"Unknown market type '{mtype}'")
    return json.loads(path.read_text())


@lru_cache(maxsize=None)
def _catalog_index(mtype: str) -> dict[str, dict]:
    return {f["name"]: f for f in load_catalog(mtype)}


def validate_field(mtype: str, name: str) -> None:
    """Accepts `field` or `field|<timeframe>` if the catalog lists that timeframe."""
    base, _, tf = name.partition("|")
    meta = _catalog_index(mtype).get(base)
    if meta is None:
        raise ValidationError(f"Field '{base}' is not available for market type '{mtype}'")
    if tf and tf not in meta["timeframes"]:
        raise ValidationError(f"Field '{base}' has no '{tf}' timeframe (allowed: {meta['timeframes']})")


def _operand(mtype: str, v: Any) -> Any:
    """A {'field': 'name'} operand compares against another column."""
    if isinstance(v, dict) and "field" in v:
        validate_field(mtype, v["field"])
        return Column(v["field"])
    return v


def build_condition(mtype: str, node: dict) -> Any:
    """Compile a filter tree node into a library filter dict.

    Leaf: {"field","op","value"?,"value2"?}   Group: {"op":"and"|"or","children":[...]}
    """
    op = node.get("op")
    if op in ("and", "or"):
        children = [build_condition(mtype, c) for c in node.get("children", [])]
        if not children:
            raise ValidationError(f"'{op}' group needs at least one condition")
        if len(children) == 1:
            return children[0]
        return (And if op == "and" else Or)(*children)

    if op not in OPERATORS:
        raise ValidationError(f"Unknown operator '{op}'")
    field = node.get("field")
    if not field:
        raise ValidationError("Condition is missing 'field'")
    validate_field(mtype, field)
    col = Column(field)
    kind = OPERATORS[op]
    v, v2 = _operand(mtype, node.get("value")), _operand(mtype, node.get("value2"))
    try:
        if kind == "none":
            return getattr(col, op)()
        if kind == "value":
            if v is None:
                raise ValidationError(f"Operator '{op}' needs a value")
            return {
                ">": lambda: col > v, ">=": lambda: col >= v, "<": lambda: col < v,
                "<=": lambda: col <= v, "==": lambda: col == v, "!=": lambda: col != v,
            }.get(op, lambda: getattr(col, op)(v))()
        if kind == "range":
            return getattr(col, op)(v, v2)
        if kind == "list":
            return getattr(col, op)(v if isinstance(v, list) else [v])
        if kind == "pct":      # field above/below <other field> by pct  (value=other field, value2=pct)
            return getattr(col, op)(v, float(v2))
        if kind == "pct_range":  # value=other field, value2=lo pct, node["value3"]=hi pct
            return getattr(col, op)(v, float(v2), float(node["value3"]))
    except (TypeError, KeyError, ValueError) as e:
        raise ValidationError(f"Bad operands for '{op}' on '{field}': {e}")
    raise ValidationError(f"Unsupported operator '{op}'")


def _json_safe(v: Any) -> Any:
    if v is None:
        return None
    try:
        if v != v:  # NaN
            return None
    except Exception:
        pass
    if hasattr(v, "item"):  # numpy scalar
        return v.item()
    return v


class TVScreenerService:
    def markets(self) -> dict:
        return {
            "countries": COUNTRY_MARKETS,
            "other": OTHER_MARKETS,
            "operators": OPERATORS,
            "asset_scopes": ["all", *ASSET_SCOPES.keys()],
        }

    def fields(self, market: str) -> list[dict]:
        if market not in ALL_MARKETS:
            raise ValidationError(f"Unknown market '{market}'")
        return load_catalog(market_type(market))

    def scan(self, *, markets: list[str], columns: list[str], filters: dict | None, sort_by: str | None,
             ascending: bool, limit: int, offset: int, tickers: list[str], index: str | None,
             asset_scope: str, use_cache: bool = True) -> dict:
        for m in markets:
            if m not in ALL_MARKETS:
                raise ValidationError(f"Unknown market '{m}'")
        mtypes = {market_type(m) for m in markets}
        if len(mtypes) != 1:
            raise ValidationError("All markets in one scan must share a field catalog (e.g. several countries)")
        mtype = mtypes.pop()
        if not columns:
            raise ValidationError("Select at least one column")
        for c in [*columns, *([sort_by] if sort_by else [])]:
            validate_field(mtype, c)

        key_src = json.dumps(
            [markets, columns, filters, sort_by, ascending, limit, offset, tickers, index, asset_scope],
            sort_keys=True,
        )
        key = "tv:scan:" + hashlib.sha1(key_src.encode()).hexdigest()
        if use_cache:
            try:
                hit = cache_get(key)
                if hit is not None:
                    return {**hit, "cached": True}
            except Exception as e:  # Redis down must not break scans
                logger.warning("tv cache read failed", error=str(e))

        q = Query().select(*columns).set_markets(*markets).limit(limit).offset(offset)
        if tickers:
            q.set_tickers(*tickers)
        if index:
            q.set_index(index)
        conditions = []
        if filters and (filters.get("children") or filters.get("field")):
            conditions.append(build_condition(mtype, filters))
        if asset_scope != "all":
            # The library's default stock filter hides ETFs; an explicit scope replaces it.
            if asset_scope not in ASSET_SCOPES:
                raise ValidationError(f"Unknown asset_scope '{asset_scope}'")
            conditions.append(ASSET_SCOPES[asset_scope]())
        if conditions:
            q.where2(And(*conditions) if len(conditions) > 1 else conditions[0])
        if sort_by:
            q.order_by(sort_by, ascending=ascending)

        try:
            total, df = q.get_scanner_data()
        except Exception as e:
            logger.error("tv scan failed", error=str(e))
            raise ValidationError(f"TradingView request failed: {str(e).splitlines()[0]}")

        rows = [{k: _json_safe(v) for k, v in rec.items()} for rec in df.to_dict("records")]
        result = {"total": int(total), "columns": ["ticker", *columns], "rows": rows, "cached": False}
        try:
            cache_set(key, result, CACHE_TTL_SECONDS)
        except Exception as e:
            logger.warning("tv cache write failed", error=str(e))
        return result

    def presets(self) -> list[dict]:
        def leaf(field, op, value=None, value2=None):
            return {"field": field, "op": op, "value": value, "value2": value2}
        return [
            {"id": "donchian_breakout", "name": "Donchian 20 breakout (daily)", "market": "india",
             "columns": ["name", "close", "DonchCh20.Upper", "DonchCh20.Lower", "volume", "market_cap_basic"],
             "filters": {"op": "and", "children": [
                 leaf("close", ">=", {"field": "DonchCh20.Upper"}), leaf("market_cap_basic", ">", 1e10)]},
             "sort_by": "market_cap_basic", "ascending": False},
            {"id": "oversold_1m_rsi", "name": "Oversold on 1-min RSI (<30)", "market": "india",
             "columns": ["name", "close|1", "RSI|1", "volume|1", "RSI"],
             "filters": {"op": "and", "children": [leaf("RSI|1", "<", 30), leaf("market_cap_basic", ">", 1e10)]},
             "sort_by": "RSI|1", "ascending": True},
            {"id": "gross_profit_growth", "name": "Gross profit QoQ growth > 15%", "market": "india",
             "columns": ["name", "close", "gross_profit_qoq_growth_fq", "gross_profit_fq", "market_cap_basic"],
             "filters": {"op": "and", "children": [
                 leaf("gross_profit_qoq_growth_fq", ">", 15), leaf("gross_profit_fq", ">", 1e9),
                 leaf("market_cap_basic", ">", 1e10)]},
             "sort_by": "gross_profit_qoq_growth_fq", "ascending": False},
            {"id": "ema_cross_up_5m", "name": "EMA20 crosses above EMA50 (5-min)", "market": "india",
             "columns": ["name", "close|5", "EMA20|5", "EMA50|5", "volume|5"],
             "filters": {"op": "and", "children": [
                 leaf("EMA20|5", "crosses_above", {"field": "EMA50|5"}), leaf("market_cap_basic", ">", 1e10)]},
             "sort_by": "volume|5", "ascending": False},
            {"id": "top_etfs", "name": "Largest US ETFs", "market": "america", "asset_scope": "etf",
             "columns": ["name", "close", "aum", "expense_ratio", "nav", "fund_flows.1M"],
             "filters": None, "sort_by": "aum", "ascending": False},
            {"id": "high_volume_us", "name": "US stocks: relative volume > 3", "market": "america",
             "columns": ["name", "close", "change", "volume", "relative_volume_10d_calc", "market_cap_basic"],
             "filters": {"op": "and", "children": [
                 leaf("relative_volume_10d_calc", ">", 3), leaf("market_cap_basic", ">", 1e9)]},
             "sort_by": "relative_volume_10d_calc", "ascending": False},
        ]


tv_screener_service = TVScreenerService()
