import pytest

from app.technical.services import tv_screener_service as svc
from app.technical.shared.errors import ValidationError


def test_catalog_loads_every_market_type():
    for t in ["stocks", "crypto", "coin", "forex", "futures", "options", "bonds", "bond", "cfd", "economics2"]:
        assert len(svc.load_catalog(t)) > 50


def test_country_markets_use_stock_catalog():
    assert svc.market_type("india") == "stocks"
    assert svc.market_type("crypto") == "crypto"


def test_validate_field_and_timeframe():
    svc.validate_field("stocks", "RSI|1")
    svc.validate_field("stocks", "DonchCh20.Upper|1W")
    with pytest.raises(ValidationError):
        svc.validate_field("stocks", "not_a_field")
    with pytest.raises(ValidationError):
        svc.validate_field("stocks", "close|7")


def test_build_condition_leaf_and_groups():
    leaf = svc.build_condition("stocks", {"field": "close", "op": ">=", "value": {"field": "DonchCh20.Upper"}})
    assert leaf["operation"] == "egreater"
    assert leaf["right"] == "DonchCh20.Upper"
    grp = svc.build_condition("stocks", {"op": "or", "children": [
        {"field": "RSI", "op": "<", "value": 30}, {"field": "sector", "op": "isin", "value": ["Finance"]}]})
    assert "operator" in str(grp) or "or" in str(grp).lower()


def test_unknown_operator_and_empty_group_rejected():
    with pytest.raises(ValidationError):
        svc.build_condition("stocks", {"field": "close", "op": "~~", "value": 1})
    with pytest.raises(ValidationError):
        svc.build_condition("stocks", {"op": "and", "children": []})


def test_scan_rejects_mixed_catalogs_and_bad_columns():
    base = dict(filters=None, sort_by=None, ascending=False, limit=1, offset=0, tickers=[], index=None, asset_scope="all")
    with pytest.raises(ValidationError):
        svc.tv_screener_service.scan(markets=["india", "crypto"], columns=["close"], **base)
    with pytest.raises(ValidationError):
        svc.tv_screener_service.scan(markets=["india"], columns=["bogus"], **base)
