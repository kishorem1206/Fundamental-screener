"""End-to-end tests for `balance_sheet_intelligence.compute_balance_sheet_intelligence()`
(the package's orchestrator). Uses real, already-ingested Screener data for
Maruti/HDFC Bank (via the `db` fixture) combined with a hand-built synthetic
`yfinance_metrics` dict — avoids a live yfinance network call in the test
suite while still exercising the real cross-source blend and unit
conversion.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.calculations.balance_sheet_intelligence import compute_balance_sheet_intelligence
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock

_STMT_TYPE_FIXTURE_COMPANY = "TEST:BSI_STMT_TYPE_FIXTURE"


def _ensure_stmt_type_fixture_stock(db) -> None:
    if db.get(Stock, _STMT_TYPE_FIXTURE_COMPANY) is not None:
        return
    now = datetime.now(timezone.utc)
    db.add(Stock(
        id=_STMT_TYPE_FIXTURE_COMPANY, symbol="BSI_STMT_TYPE_FIXTURE", exchange="TEST",
        company_name="BSI Fixture Co.", sector="Healthcare", basic_industry="Hospital",
        is_active=True, created_at=now, updated_at=now,
    ))
    db.flush()


def _insert_bs(db, field: str, period: str, value: float, statement_type: str) -> None:
    _ensure_stmt_type_fixture_stock(db)
    metric_store.insert_metric_value(
        db, company_id=_STMT_TYPE_FIXTURE_COMPANY, metric_key=field, period=period, value=value,
        unit="cr", statement_type=statement_type, source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM", source_date=datetime.now(timezone.utc),
    )

_PNL_MISMATCH_FIXTURE_COMPANY = "TEST:BSI_PNL_STMT_TYPE_MISMATCH_FIXTURE"


def _ensure_pnl_mismatch_fixture_stock(db) -> None:
    if db.get(Stock, _PNL_MISMATCH_FIXTURE_COMPANY) is not None:
        return
    now = datetime.now(timezone.utc)
    db.add(Stock(
        id=_PNL_MISMATCH_FIXTURE_COMPANY, symbol="BSI_PNL_STMT_TYPE_MISMATCH_FIXTURE", exchange="TEST",
        company_name="PNL Mismatch Fixture Co.", sector="Information Technology",
        is_active=True, created_at=now, updated_at=now,
    ))
    db.flush()


def _insert_pnl_mismatch_fixture(db, field: str, period: str, value: float, statement_type: str) -> None:
    _ensure_pnl_mismatch_fixture_stock(db)
    metric_store.insert_metric_value(
        db, company_id=_PNL_MISMATCH_FIXTURE_COMPANY, metric_key=field, period=period, value=value,
        unit="cr", statement_type=statement_type, source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM", source_date=datetime.now(timezone.utc),
    )


def _seed_pnl_mismatch_fixture(db) -> None:
    """A synthetic company with a CONSOLIDATED balance sheet (whole-group
    total_assets=3730, matching the real TANLA figures this scenario was
    modeled on) but P&L data ONLY under STANDALONE (ebit=7 via
    operating_profit=14, depreciation=7) — deterministically reproduces
    the cross-statement-type mismatch regardless of what real companies'
    ledger data looks like at any given time (TANLA itself no longer
    reproduces this after its CONSOLIDATED P&L gap was backfilled
    2026-09-23)."""
    period = "2026-03-31"
    for field, value in (
        ("total_assets", 3730.0), ("total_liabilities", 3730.0),
        ("equity_capital", 100.0), ("reserves", 2388.0), ("borrowings", 50.0),
    ):
        _insert_pnl_mismatch_fixture(db, field, period, value, "CONSOLIDATED")
    for field, value in (
        ("pnl_sales", 133.0), ("pnl_operating_profit", 14.0), ("pnl_depreciation", 7.0),
    ):
        _insert_pnl_mismatch_fixture(db, field, period, value, "STANDALONE")
    db.flush()


_MANUFACTURING_SYMBOL = "MARUTI"
_BANK_SYMBOL = "HDFCBANK"

# Raw-Rupee yfinance series (deliberately unscaled, like the real thing) —
# exercises the real /1e7 unit-conversion path, not a pre-converted stub.
_SYNTHETIC_YFINANCE_METRICS = {
    "cash_series": {"FY2025": 500_000_000.0, "FY2026": 669_000_000.0},
    "current_liabilities_series": {"FY2025": 296_150_000_000.0, "FY2026": 364_802_000_000.0},
    "receivable_days_series": {"FY2025": 10.0, "FY2026": 11.0},
    "inventory_days_series": {"FY2025": 20.0, "FY2026": 23.3},
    "payable_days_series": {"FY2025": 55.0, "FY2026": 59.3},
    "ccc_series": {"FY2025": -25.0, "FY2026": -25.0},
    "curr_ratio_series": {"FY2025": 0.96, "FY2026": 1.07},
    "quick_ratio_series": {"FY2025": 0.23, "FY2026": 0.15},
    "cash_ratio_series": {"FY2025": 0.01, "FY2026": 0.0},
}


def _fixture_company_id(db, symbol: str) -> str:
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    assert stock is not None, f"fixture company {symbol} not found in stocks table"
    return stock.id


def test_manufacturing_company_full_result_shape(db):
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    result = compute_balance_sheet_intelligence(db, company_id, sector_name="Auto Manufacturers", yfinance_metrics=_SYNTHETIC_YFINANCE_METRICS)
    assert result["statement_type"] in ("CONSOLIDATED", "STANDALONE")
    assert result["period"] is not None
    assert result["balance_sheet_integrity"]["status"] == "VALID"
    assert result["archetype"]["classification"] in ("STRONG", "WEAK", "MIDDLE", "TRANSFORMING")
    assert len(result["risk_flags"]) == 12
    assert result["financial_institution_summary"] is None


def test_manufacturing_company_house_totals_match(db):
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    result = compute_balance_sheet_intelligence(db, company_id, sector_name="Auto Manufacturers", yfinance_metrics=_SYNTHETIC_YFINANCE_METRICS)
    house = result["house"]
    assert abs(house["sources_total"] - house["applications_total"]) < 5.0  # small rounding noise in Screener's own published figures, confirmed earlier


def test_manufacturing_company_roce_unit_conversion_sane(db):
    """Regression coverage for the unit-mismatch bug found live: ROCE must
    land in a plausible range (single-to-low-double-digit percent), not the
    ~0% or wildly negative value the unconverted-Rupees bug produced."""
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    result = compute_balance_sheet_intelligence(db, company_id, sector_name="Auto Manufacturers", yfinance_metrics=_SYNTHETIC_YFINANCE_METRICS)
    roce = result["derived_metrics"].get("roce")
    assert roce is not None
    assert -5.0 < roce < 100.0  # sane bound, not a unit-mismatch artifact


def test_manufacturing_company_working_capital_blend_present(db):
    """MARUTI has a full 12-year `bs_ratio_debtor_days` history on record
    (2026-09-23 fix — Screener's own Ratios tab has years of data, not just
    the latest point, confirmed by the user's own screenshot). Screener is
    the primary source, so it must override EVERY year it covers, not just
    the latest one: FY2025 here diverges from the synthetic yfinance
    fixture's 10.0 (Screener's real ledger value for 2025-03-31 is 16.0),
    proving this is a genuine multi-year merge and not a latest-period-only
    override that happens to also match on the newest year."""
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    result = compute_balance_sheet_intelligence(db, company_id, sector_name="Auto Manufacturers", yfinance_metrics=_SYNTHETIC_YFINANCE_METRICS)
    wc = result["working_capital"]
    assert wc["dso_series"]["FY2026"] == 11.0
    assert wc["dso_series"]["FY2025"] == 16.0, "Screener must override FY2025 too, not just the latest year"
    assert wc["dso_series"]["FY2025"] != _SYNTHETIC_YFINANCE_METRICS["receivable_days_series"]["FY2025"]
    assert wc["latest_cross_check"]["dso"]["yfinance"] == 11.0


def test_bank_routes_to_financial_institution_summary(db):
    company_id = _fixture_company_id(db, _BANK_SYMBOL)
    result = compute_balance_sheet_intelligence(db, company_id, sector_name="Banks", yfinance_metrics={})
    assert result["archetype"]["classification"] == "NOT_APPLICABLE"
    assert result["working_capital"] == {}
    assert result["financial_institution_summary"] is not None
    assert result["financial_institution_summary"]["deposits"] is not None


def test_bank_borrowings_alias_flows_through_orchestrator(db):
    """The whole point of the alias fallback (Milestone 2) is that it must
    not just resolve in isolation but actually flow through to the
    orchestrator's leverage/house output for a real bank."""
    company_id = _fixture_company_id(db, _BANK_SYMBOL)
    result = compute_balance_sheet_intelligence(db, company_id, sector_name="Banks", yfinance_metrics={})
    assert result["liabilities"]["borrowings"] is not None


def test_unknown_company_returns_empty_shape(db):
    result = compute_balance_sheet_intelligence(db, "NOT-A-REAL-COMPANY-ID", yfinance_metrics={})
    assert result["period"] is None
    assert result["balance_sheet_integrity"]["status"] == "MISSING_DATA"
    assert result["risk_flags"] == []


def test_no_yfinance_metrics_never_raises(db):
    """A company processed before this engine existed (or whose
    yfinance-sourced metrics genuinely failed) must degrade gracefully, not
    crash the whole pipeline stage. It must also not silently give up on
    Screener's own working-capital ratios just because yfinance has
    nothing at all — with no yfinance keys to match against, Screener's
    FULL multi-year history (MARUTI has 12 years of `bs_ratio_debtor_days`
    on record) is used directly under its own ISO period keys, not just a
    single backfilled point."""
    company_id = _fixture_company_id(db, _MANUFACTURING_SYMBOL)
    result = compute_balance_sheet_intelligence(db, company_id, sector_name="Auto Manufacturers", yfinance_metrics=None)
    assert result["period"] is not None
    assert result["working_capital"]["dso_series"][result["period"]] == 11.0
    assert len(result["working_capital"]["dso_series"]) >= 10, "should carry Screener's full multi-year history, not one point"
    assert result["working_capital"]["single_period_fallback"].get("dso") is True


def test_prefers_current_standalone_over_stale_consolidated(db):
    """Regression test for a real bug found live on GPT Healthcare
    (2026-09-20): Screener CONSOLIDATED data stops at FY2022 (deconsolidated
    a subsidiary) while STANDALONE runs current through FY2026. Both sides
    have SOME data (not `single_statement_source`), so the old auto-detect
    default always picked CONSOLIDATED purely for being nonempty — silently
    showing a 4-year-stale balance sheet (with Cash/Current Ratio reading
    MISSING_INPUT, since the yfinance-sourced cross-source series don't
    reach back that far) as the default view."""
    for period, mult, stmt in (("2022-03-31", 1.0, "CONSOLIDATED"), ("2026-03-31", 2.0, "STANDALONE")):
        for field, value in (("equity_capital", 10.0), ("reserves", 490.0), ("total_assets", 1000.0),
                             ("total_liabilities", 1000.0)):
            _insert_bs(db, field, period, value * mult, stmt)
    db.flush()

    result = compute_balance_sheet_intelligence(
        db, _STMT_TYPE_FIXTURE_COMPANY, sector_name="Healthcare",
        yfinance_metrics={"cash_series": {"FY2026": 41_332_000.0}, "current_liabilities_series": {"FY2026": 100_000_000.0}},
    )
    assert result["single_statement_source"] is False
    assert result["statement_type"] == "STANDALONE"
    assert result["period"] == "2026-03-31"
    assert result["coverage"]["metrics"]["cash"]["status"] == "AVAILABLE"  # only resolves for the FY2026 period

    explicit_consolidated = compute_balance_sheet_intelligence(
        db, _STMT_TYPE_FIXTURE_COMPANY, sector_name="Healthcare", statement_type="CONSOLIDATED", yfinance_metrics={})
    assert explicit_consolidated["statement_type"] == "CONSOLIDATED"
    assert explicit_consolidated["period"] == "2022-03-31"


def test_hospital_inventory_turnover_marked_not_applicable(db):
    """A hospital (Healthcare sector, basic_industry='Hospital', the
    fixture stock's own basic_industry) must not see Inventory Turnover
    listed as a data gap — inventory is real but immaterial to a hospital's
    balance sheet story."""
    for field, value in (("equity_capital", 10.0), ("reserves", 490.0), ("total_assets", 1000.0),
                         ("total_liabilities", 1000.0)):
        _insert_bs(db, field, "2026-03-31", value, "STANDALONE")
    db.flush()
    result = compute_balance_sheet_intelligence(db, _STMT_TYPE_FIXTURE_COMPANY, sector_name="Healthcare", yfinance_metrics=None)
    assert result["coverage"]["metrics"]["inventory_turnover"]["status"] == "NOT_APPLICABLE"
    assert "Healthcare" in result["coverage"]["metrics"]["inventory_turnover"]["reason"]


def test_cascade_falls_back_when_pnl_statement_type_differs_from_balance_sheet(db):
    """Real gap originally found live on TANLA (2026-09-23, user's own
    report — "Balance sheet only 27% available why"): a company can have a
    CONSOLIDATED balance sheet (real Screener consolidated data exists)
    while its `pnl_sales` ledger only ever has STANDALONE rows — no
    CONSOLIDATED P&L was ever ingested for it. Reusing the balance sheet's
    resolved type for the EBIT/EBITDA/revenue cascade lookup silently came
    back empty, so ROCE/EBIT margin/net-debt-to-EBITDA all went missing
    even though pl_intelligence's own (separate) fallback finds the real
    STANDALONE cascade for the exact same company. Uses a synthetic
    fixture rather than live TANLA data — TANLA's own CONSOLIDATED P&L gap
    was backfilled the same day this bug was found, so it no longer
    reproduces the scenario live."""
    _seed_pnl_mismatch_fixture(db)
    # yfinance_metrics={} deliberately omits current_liabilities_series —
    # ROCE itself has a real, separate, correct dependency on that (not
    # part of this bug), so ebit_margin (ebit/revenue only) isolates the
    # cascade-fallback fix specifically.
    result = compute_balance_sheet_intelligence(db, _PNL_MISMATCH_FIXTURE_COMPANY, sector_name="Information Technology", yfinance_metrics={})
    assert result["derived_metrics"]["ebit_margin"] is not None, "ebit_margin should resolve via the cross-statement-type cascade fallback"


def test_roce_withheld_not_blended_when_pnl_basis_differs_from_balance_sheet(db):
    """Regression test for a real ROCE-corruption bug found live on TANLA
    directly downstream of the fallback above (2026-09-23, FA-2026-000042,
    user's own report — "ROCE: 25.2% -> 0.3%, why did ROCE decline?"): the
    balance sheet resolved CONSOLIDATED (whole-group total_assets, ~3730
    Cr), but the P&L cascade fell back to STANDALONE (TANLA's own
    parent-entity-only ebit, ~7 Cr — no CONSOLIDATED P&L was ingested).
    Computing capital_employed as CONSOLIDATED total_assets minus current
    liabilities, then dividing STANDALONE ebit by it, silently paired two
    different statement bases and produced ROCE=0.28% instead of the real
    ~25% (confirmed live: 7 / (3730 - 1194.48) * 100 = 0.276, matching the
    corrupted value exactly). A same-basis re-fetch was tried and rejected
    (see the module's own comment) because yfinance's cross-sourced
    current_liabilities can't be reliably matched to either side either —
    the safe fix is to withhold ROCE/capital_employed_turnover (None) when
    the P&L and balance-sheet bases genuinely diverge, never blend a
    second, differently-wrong way. `ebit_margin` (pure P&L, no
    balance-sheet input) must still resolve via the fallback. Uses the
    same synthetic fixture as the test above — TANLA's own gap was
    backfilled the same day, so it no longer reproduces this live."""
    _seed_pnl_mismatch_fixture(db)
    result = compute_balance_sheet_intelligence(
        db, _PNL_MISMATCH_FIXTURE_COMPANY, sector_name="Information Technology",
        yfinance_metrics={"current_liabilities_series": {"FY2026": 11_944_806_000.0}},
    )
    dm = result["derived_metrics"]
    assert dm.get("roce") is None, f"roce={dm.get('roce')} should be withheld (MISSING_INPUT), not a cross-type blend"
    assert dm.get("capital_employed") is None
    assert dm.get("capital_employed_turnover") is None
    assert dm.get("ebit_margin") is not None, "ebit_margin is a pure P&L ratio and must still resolve via the cascade fallback"
