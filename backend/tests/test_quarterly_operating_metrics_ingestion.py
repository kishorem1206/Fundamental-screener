"""Tests for the Quarterly Sector KPI Extraction Engine
(`app/ingestion/quarterly_operating_metrics_ingestion.py`) — sourced from
NSE quarterly Investor Presentation filings, a different document type
than every other annual-report-sourced area in this app.

Covers: period parsing (both the SEBI-boilerplate "quarter ended <date>"
phrase, in its two real date-order variants, and the fallback "Q_ FY__"
label parsing for company-authored decks with no boilerplate at all —
found live on JSW Steel's real deck); statement-type resolution;
per-tonne ratio computation with the same "prefer a directly-reported
figure over a derived one" precedent as the annual engine; and that an
unconfigured sector is a clean no-op, not an error.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.database import metric_store
from app.ingestion import quarterly_operating_metrics_ingestion as qomi

_COMPANY_ID = "NSE:MARUTI"


# ── Period parsing ───────────────────────────────────────────────────────

def test_parses_quarter_ended_day_month_year():
    text = "Sub: Investor Presentation on the financial results for the quarter ended 30th June 2026"
    assert qomi._parse_quarter_end_date(text) == "2026-06-30"


def test_parses_quarter_ended_month_day_year():
    text = "Presentation titled Operational & Financial Highlights of the Company for the quarter ended June 30, 2026."
    assert qomi._parse_quarter_end_date(text) == "2026-06-30"


def test_falls_back_to_quarter_label_when_no_boilerplate_phrase():
    """Real gap found live on JSW Steel's deck (fetched via the external-
    link fallback, a company-authored deck, not a SEBI cover letter) — no
    "quarter ended" phrase anywhere, just a "Q1 FY27 Production & Sales"
    label deep in the content."""
    text = "Q1 FY27 Production & Sales\nIn million metric tonnes"
    assert qomi._parse_quarter_end_date(text) == "2026-06-30"


def test_quarter_label_q4_maps_to_march_of_the_fy_year():
    text = "Q4 FY26 Highlights"
    assert qomi._parse_quarter_end_date(text) == "2026-03-31"


def test_quarter_label_with_fy_span_uses_ending_year():
    """IOC labels quarters "Q2 FY 25-26" — must resolve to FY26, not FY25."""
    assert qomi._parse_quarter_end_date("Q2 FY 25-26 Standalone Financial Highlights") == "2025-09-30"


def test_returns_none_when_nothing_matches():
    assert qomi._parse_quarter_end_date("Some unrelated cover page text") is None


def test_quarter_label_without_fy_token_still_parses():
    """ICICI Bank's deck labels columns "Q1-2027", not "Q1 FY27" — same
    Indian-fiscal-year meaning (Q1-2027 = Apr-Jun 2026), just no "FY" token
    to anchor on."""
    assert qomi._parse_quarter_end_date("Percent FY2026 Q1-2027") == "2026-06-30"


def test_quarter_label_picks_latest_not_first_match_in_a_comparison_table():
    """Real bug found live on ICICI Bank's "Key ratios" table: "FY2024
    FY2025 FY2026 Q1-2026 Q1-2027" (oldest-to-newest, left to right) — a
    plain `.search()` matched the leftmost "Q1-2026" comparison column
    instead of the actual current quarter "Q1-2027", dating every value on
    that page a full year early."""
    text = "Key ratios Percent FY2024 FY2025 FY2026 Q1-2026 Q1-2027"
    assert qomi._parse_quarter_end_date(text) == "2026-06-30"


def test_quarter_label_fy_and_no_fy_variants_both_considered_for_latest():
    text = "Q4 FY26 Highlights ... comparison table Q1-2027"
    assert qomi._parse_quarter_end_date(text) == "2026-06-30"


# ── Statement-type resolution ────────────────────────────────────────────

def test_resolves_standalone_when_explicitly_titled():
    text = "Maruti Suzuki India Limited\nQ1 FY'27 Standalone Financial Results\n31st July 2026"
    assert qomi._resolve_statement_type(text) == "STANDALONE"


def test_defaults_to_consolidated_otherwise():
    text = "Investor Presentation\nAugust 2026"
    assert qomi._resolve_statement_type(text) == "CONSOLIDATED"


# ── Unconfigured sector is a clean no-op ─────────────────────────────────

def test_unconfigured_sector_returns_empty_without_any_fetch(monkeypatch, db):
    called = {"fetch": False}
    monkeypatch.setattr(qomi.ipc, "fetch_latest_investor_presentation", lambda *a, **k: called.__setitem__("fetch", True))
    result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="MARUTI", sector_name="IT Services")
    assert result == []
    assert called["fetch"] is False


# ── End-to-end ratio computation (mocked fetch/locate/extract) ──────────

_FAKE_FILING = {"an_dt": "28-Jul-2026 14:56:58", "attchmntFile": "https://example.com/deck.pdf"}


class _FakeDocument:
    pass


_ALL_QUARTERLY_AREAS = (
    "cement_quarterly_metrics", "metals_quarterly_metrics",
    "automobile_quarterly_metrics", "paper_quarterly_metrics", "chemicals_quarterly_metrics",
    "consumer_durables_quarterly_metrics", "hotels_quarterly_metrics", "retail_quarterly_metrics",
    "realty_quarterly_metrics", "oil_gas_quarterly_metrics", "fmcg_quarterly_metrics",
    "healthcare_quarterly_metrics", "banking_quarterly_metrics",
)


def _common_mocks(monkeypatch, extracted: dict, page_text: str = "Q1FY27 highlights page text"):
    monkeypatch.setattr(qomi.ipc, "fetch_latest_investor_presentation",
                         lambda symbol: (b"%PDF-fake", "https://example.com/deck.pdf", _FAKE_FILING))
    monkeypatch.setattr(qomi.ipc, "store_investor_presentation",
                         lambda db, company_id, symbol, filing, pdf_bytes, source_url: _FakeDocument())
    monkeypatch.setattr(qomi, "locate_sections",
                         lambda pdf_bytes, **kw: ({area: [0] for area in _ALL_QUARTERLY_AREAS}, {}))

    class _FakePage:
        def extract_text(self_inner, **kw):
            return "Sub: Investor Presentation for the quarter ended 30th June 2026\n" + page_text

    class _FakePdf:
        pages = [_FakePage()]

        def __enter__(self_inner):
            return self_inner

        def __exit__(self_inner, *a):
            return False

    monkeypatch.setattr(qomi.pdfplumber, "open", lambda *a, **k: _FakePdf())
    monkeypatch.setattr(qomi, "extract_area", lambda prompt_key, text: extracted)
    monkeypatch.setattr(qomi.default_llm_client, "last_used_fallback", False)


def test_cement_prefers_reported_ebitda_over_derived_but_always_derives_cost(monkeypatch, db):
    """Direct regression test for the same precedent the annual Metals
    area established: a directly-reported per-tonne figure must win over
    a derived one, even when qtr_sales/qtr_operating_profit are available
    (which would let the derivation branch also fire). Cement's clean
    row-based table (see the "cement" prompt's own comment) has no
    cost-per-tonne row at all — real gap found live-testing Ambuja
    Cements — so qtr_cost_per_tonne is always the derived
    (realisation - ebitda) figure for this sector, never a reported one."""
    extracted = {
        "sales_million_tonnes_current_quarter": 17.1,
        "sales_million_tonnes_yoy_prior_quarter": 19.9,
        "sales_million_tonnes_qoq_prior_quarter": 18.4,
        "ebitda_per_tonne_reported": 735.0,
    }
    _common_mocks(monkeypatch, extracted)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_sales", period="2026-06-30", value=7300.0, unit="cr",
        statement_type="CONSOLIDATED", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_operating_profit", period="2026-06-30", value=1200.0,
        unit="cr", statement_type="CONSOLIDATED", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )

    result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="AMBUJACEM", sector_name="Cement")
    by_key = {r.metric_key: r for r in result}

    assert by_key["qtr_ebitda_per_tonne"].value == 735.0
    assert by_key["qtr_ebitda_per_tonne"].reported_or_calculated == "REPORTED"
    expected_realisation = round(7300.0 * 10 / 17.1, 2)
    assert by_key["qtr_cost_per_tonne"].value == round(expected_realisation - 735.0, 2)
    assert by_key["qtr_cost_per_tonne"].reported_or_calculated == "CALCULATED"
    # (17.1 - 19.9) / 19.9 * 100
    assert by_key["qtr_volume_growth_yoy"].value == round((17.1 - 19.9) / 19.9 * 100, 2)


def test_metals_derives_ebitda_and_cost_when_not_directly_reported(monkeypatch, db):
    extracted = {
        "production_million_tonnes_current_quarter": 6.59,
        "production_million_tonnes_yoy_prior_quarter": 6.38,
        "sales_million_tonnes_current_quarter": 6.25,
        "sales_million_tonnes_yoy_prior_quarter": 6.03,
    }
    _common_mocks(monkeypatch, extracted)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_sales", period="2026-06-30", value=48000.0, unit="cr",
        statement_type="CONSOLIDATED", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_operating_profit", period="2026-06-30", value=7000.0,
        unit="cr", statement_type="CONSOLIDATED", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )

    result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="JSWSTEEL", sector_name="Metals")
    by_key = {r.metric_key: r for r in result}

    # Uses SALES volume (6.25), not production (6.59), for per-tonne ratios
    expected_realisation = round(48000.0 * 10 / 6.25, 2)
    expected_ebitda = round(7000.0 * 10 / 6.25, 2)
    assert by_key["qtr_realisation_per_tonne"].value == expected_realisation
    assert by_key["qtr_ebitda_per_tonne"].value == expected_ebitda
    assert by_key["qtr_ebitda_per_tonne"].reported_or_calculated == "CALCULATED"
    assert by_key["qtr_cost_per_tonne"].value == round(expected_realisation - expected_ebitda, 2)


def test_banking_stores_bare_metric_keys_not_qtr_prefixed(monkeypatch, db):
    """Unlike every other sector here (`qtr_{prefix}_{suffix}` keys), Banks/
    NBFCs must store under the BARE `nim`/`cost_to_income_ratio` keys —
    matching `banking_ingestion.py`'s existing convention so `scoring.py`'s
    efficiency scorers and `banking_data_bridge.py` pick them up with no
    further wiring (see `_SECTOR_CONFIG`'s comment)."""
    extracted = {"nim_pct": 4.36, "cost_to_income_pct": 39.2}
    _common_mocks(monkeypatch, extracted)

    for sector in ("Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans"):
        result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="HDFCBANK", sector_name=sector)
        by_key = {r.metric_key: r for r in result}
        assert by_key["nim"].value == 4.36
        assert by_key["cost_to_income_ratio"].value == 39.2
        assert "qtr_banking_nim" not in by_key and "qtr_banking_cost_to_income_pct" not in by_key


def test_banking_omits_cost_to_income_when_not_stated(monkeypatch, db):
    _common_mocks(monkeypatch, {"nim_pct": 3.46, "cost_to_income_pct": None})
    result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="AXISBANK", sector_name="Banks")
    by_key = {r.metric_key: r for r in result}
    assert by_key["nim"].value == 3.46
    assert "cost_to_income_ratio" not in by_key


def test_automobile_volume_growth_yoy_and_no_per_tonne_ratios(monkeypatch, db):
    extracted = {
        "units_sold_current_quarter": 682724.0,
        "units_sold_yoy_prior_quarter": 527861.0,
        "units_sold_qoq_prior_quarter": 676209.0,
        "market_share_pct": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="MARUTI", sector_name="Automobile")
    by_key = {r.metric_key: r for r in result}

    assert by_key["qtr_automobile_units_sold"].value == 682724.0
    expected_growth = round((682724.0 - 527861.0) / 527861.0 * 100, 2)
    assert by_key["qtr_volume_growth_yoy"].value == expected_growth
    # No per-tonne ratios for a non-tonne-denominated sector
    assert "qtr_ebitda_per_tonne" not in by_key
    assert "qtr_cost_per_tonne" not in by_key


def test_chemicals_stores_segment_growth_under_shared_final_key(monkeypatch, db):
    """ChemicalsSector has no tonne-denominated absolute volume (its
    annual metrics are cost/revenue ratios, not physical units) — the
    directly-reported segment growth % is stored straight under the same
    final `qtr_volume_growth_yoy` key the other sectors' _compute_ratios
    block derives, for cross-sector dashboard consistency, with no
    per-tonne ratio block running at all for this sector."""
    extracted = {"primary_segment_name": "Energy", "volume_growth_yoy_pct": 57.0, "export_revenue_pct": None}
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="AARTIIND", sector_name="Chemicals")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_volume_growth_yoy"].value == 57.0
    assert by_key["qtr_volume_growth_yoy"].reported_or_calculated == "REPORTED"
    assert "Energy" in by_key["qtr_volume_growth_yoy"].raw_reported_value
    assert "qtr_ebitda_per_tonne" not in by_key
    assert "qtr_chemicals_export_revenue_pct" not in by_key  # None extracted, never stored


def test_chemicals_specialty_alias_resolves_the_same_way(monkeypatch, db):
    extracted = {"primary_segment_name": "Non-Energy", "volume_growth_yoy_pct": 12.0, "export_revenue_pct": 42.0}
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(
        db, company_id=_COMPANY_ID, symbol="PIDILITIND", sector_name="Specialty Chemicals")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_volume_growth_yoy"].value == 12.0
    assert by_key["qtr_chemicals_export_revenue_pct"].value == 42.0


def test_consumer_durables_stores_growth_and_market_share(monkeypatch, db):
    """Confirmed exact live on Voltas' real Q1 FY27 filing (a 7-page MD&A
    earnings note, not a slide deck): 'RAC volumes grew 45% year on year'
    and 'achieved a 17.3% secondary market share' for the primary Room Air
    Conditioner segment. Like Chemicals, no tonne-denominated absolute
    volume here, so growth is stored straight under the shared
    `qtr_volume_growth_yoy` key and no _compute_ratios block runs; market
    share gets its own `qtr_consumer_durables_market_share` key, mirroring
    Automobile's `qtr_automobile_market_share`."""
    extracted = {"primary_segment_name": "Room Air Conditioners", "volume_growth_yoy_pct": 45.0, "market_share_pct": 17.3}
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:VOLTAS", symbol="VOLTAS", sector_name="Consumer Durables")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_volume_growth_yoy"].value == 45.0
    assert by_key["qtr_volume_growth_yoy"].reported_or_calculated == "REPORTED"
    assert "Room Air Conditioners" in by_key["qtr_volume_growth_yoy"].raw_reported_value
    assert by_key["qtr_consumer_durables_market_share"].value == 17.3
    assert "qtr_ebitda_per_tonne" not in by_key


def test_consumer_durables_omits_market_share_when_not_reported(monkeypatch, db):
    """Real per-company miss confirmed live on Blue Star's Q1 FY27 deck —
    a slide-style deck (not narrative) with only qualitative segment
    commentary ('delivered robust revenue growth'), no numeric volume
    growth % or market share % anywhere; the locator itself correctly
    finds zero candidate pages for that company (a separate, earlier
    check), but even when a page IS found and sent for extraction, an
    honest null here must not be stored as a fabricated row."""
    extracted = {"primary_segment_name": None, "volume_growth_yoy_pct": None, "market_share_pct": None}
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:BLUESTARCO", symbol="BLUESTARCO", sector_name="Consumer Durables")
    assert result == []


def test_hotels_stores_absolute_current_quarter_values(monkeypatch, db):
    """Confirmed exact live on Chalet Hotels' real Q1 FY27 filing (a
    genuine row-based 'Combined Portfolio' table, not a bar-chart
    infographic): ADR 13,247 vs 12,207, Occupancy 64.8% vs 66.0%, RevPAR
    8,582 vs 8,059. HotelsSector's NA fields are all ABSOLUTE values, not
    growth rates, so no _compute_ratios step runs."""
    extracted = {
        "adr_current_quarter": 13247.0, "adr_yoy_prior_quarter": 12207.0,
        "occupancy_pct_current_quarter": 64.8, "occupancy_pct_yoy_prior_quarter": 66.0,
        "revpar_current_quarter": 8582.0, "revpar_yoy_prior_quarter": 8059.0,
    }
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:CHALET", symbol="CHALET", sector_name="Hotels & Restaurants")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_hotels_arr"].value == 13247.0
    assert by_key["qtr_hotels_occupancy"].value == 64.8
    assert by_key["qtr_hotels_revpar"].value == 8582.0
    # yoy_prior figures are stored (raw history) even though not surfaced
    # as their own card in quarterly_sector_kpis.py
    assert by_key["qtr_hotels_revpar_yoy_prior"].value == 8059.0
    assert "qtr_ebitda_per_tonne" not in by_key


def test_retail_derives_revenue_per_sqft_and_omits_sssg_when_qualitative_only(monkeypatch, db):
    """Confirmed live on Trent's real Q1 FY27 'AT A GLANCE' snapshot
    (store count/retail area/revenue) — structurally exact (live
    primary-model confirmation of the numbers themselves is still pending
    a Groq quota reset, documented in the module docstring). SSSG is
    disclosed only as vague qualitative text on Trent's own deck ('low
    single digits'), so the prompt returns null rather than guess — must
    not be stored as a fabricated row."""
    extracted = {
        "store_count_current_quarter": 1312.0, "retail_area_sqft_current_quarter": 18_040_000.0,
        "revenue_cr_current_quarter": 5666.0, "sssg_pct": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:TRENT", symbol="TRENT", sector_name="Retail")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_retail_store_count"].value == 1312.0
    expected_revenue_per_sqft = round(5666.0 * 1e7 / 18_040_000.0, 2)
    assert by_key["qtr_retail_revenue_per_sqft"].value == expected_revenue_per_sqft
    assert by_key["qtr_retail_revenue_per_sqft"].reported_or_calculated == "CALCULATED"
    assert "qtr_retail_sssg" not in by_key  # None extracted, never stored
    assert "qtr_retail_store_count_growth_yoy" not in by_key  # no prior-year ledger value yet


def test_retail_computes_store_count_growth_against_own_prior_year_ledger(monkeypatch, db):
    """Unlike every other sector's growth calc, Retail's store count
    growth is NOT derived from a same-deck YoY pair (Trent's snapshot page
    only gives the current total) — it looks up OUR OWN previously-stored
    qtr_retail_store_count from the same quarter a year ago."""
    metric_store.insert_metric_value(
        db, company_id="NSE:TRENT", metric_key="qtr_retail_store_count", period="2025-06-30",
        value=1100.0, unit="count", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    extracted = {
        "store_count_current_quarter": 1312.0, "retail_area_sqft_current_quarter": None,
        "revenue_cr_current_quarter": None, "sssg_pct": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:TRENT", symbol="TRENT", sector_name="Retail")
    by_key = {r.metric_key: r for r in result}
    expected_growth = round((1312.0 - 1100.0) / 1100.0 * 100, 2)
    assert by_key["qtr_retail_store_count_growth_yoy"].value == expected_growth
    assert by_key["qtr_retail_store_count_growth_yoy"].reported_or_calculated == "CALCULATED"


def test_realty_stores_pre_sales_and_derives_collections_growth(monkeypatch, db):
    """Confirmed exact live on Godrej Properties' real Q1 FY27 filing (a
    clean row-based 'Sales highlights' table): Booking Value 8,651 vs
    7,082 Cr, Customer Collections 4,348 vs 3,670 Cr. Unlike Retail's
    store-count growth, this IS derived from a same-deck current+yoy_prior
    pair (real estate decks reliably give both periods on the same page).
    No launch_pipeline_msf field — dropped after a real, caught
    fabrication (see the ingestion module's own docstring)."""
    extracted = {
        "booking_value_cr_current_quarter": 8651.0, "booking_value_cr_yoy_prior_quarter": 7082.0,
        "collections_cr_current_quarter": 4348.0, "collections_cr_yoy_prior_quarter": 3670.0,
    }
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:GODREJPROP", symbol="GODREJPROP", sector_name="Real Estate")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_realty_pre_sales_value"].value == 8651.0
    assert by_key["qtr_realty_pre_sales_value"].reported_or_calculated == "REPORTED"
    assert by_key["qtr_realty_collections"].value == 4348.0
    expected_growth = round((4348.0 - 3670.0) / 3670.0 * 100, 2)
    assert by_key["qtr_realty_collections_growth_yoy"].value == expected_growth
    assert by_key["qtr_realty_collections_growth_yoy"].reported_or_calculated == "CALCULATED"
    assert "qtr_ebitda_per_tonne" not in by_key


def test_oil_gas_stores_grm_as_absolute_value(monkeypatch, db):
    """Confirmed exact live on BPCL's real Q1 FY27 'Investor Handout' (the
    standardized Reg-30 format every PSU refiner files): GRM 41.41 vs
    4.88 (YoY) vs 17.53 (QoQ) US$/bbl. Unlike the tonne-denominated
    sectors, GRM is already a per-barrel spread figure the company states
    directly — stored as-is, no _compute_ratios step."""
    extracted = {
        "grm_usd_bbl_current_quarter": 41.41, "grm_usd_bbl_yoy_prior_quarter": 4.88,
        "grm_usd_bbl_qoq_prior_quarter": 17.53,
    }
    _common_mocks(monkeypatch, extracted)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:BPCL", symbol="BPCL", sector_name="Oil & Gas")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_oilgas_grm"].value == 41.41
    assert by_key["qtr_oilgas_grm"].reported_or_calculated == "REPORTED"
    assert by_key["qtr_oilgas_grm_yoy_prior"].value == 4.88
    assert by_key["qtr_oilgas_grm_qoq_prior"].value == 17.53
    assert "qtr_ebitda_per_tonne" not in by_key


def test_fmcg_stores_uvg_and_derives_price_mix(monkeypatch, db):
    """HUL Q1 FY27 (confirmed exact live): UVG 5%, USG 10%. Price/mix is
    derived from the pair, never stored as REPORTED."""
    _common_mocks(monkeypatch, {"underlying_volume_growth_pct": 5.0, "underlying_sales_growth_pct": 10.0})
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:HINDUNILVR", symbol="HINDUNILVR", sector_name="Fast Moving Consumer Goods")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_volume_growth_yoy"].value == 5.0
    assert by_key["qtr_volume_growth_yoy"].reported_or_calculated == "REPORTED"
    assert by_key["qtr_fmcg_underlying_sales_growth"].value == 10.0
    assert by_key["qtr_fmcg_price_mix_growth"].value == round((1.10 / 1.05 - 1) * 100, 2)
    assert by_key["qtr_fmcg_price_mix_growth"].reported_or_calculated == "CALCULATED"


def test_fmcg_no_price_mix_without_both_inputs(monkeypatch, db):
    """Dabur states only volume growth — price/mix must not be invented."""
    _common_mocks(monkeypatch, {"underlying_volume_growth_pct": 5.0, "underlying_sales_growth_pct": None})
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:DABUR", symbol="DABUR", sector_name="Fast Moving Consumer Goods")
    keys = {r.metric_key for r in result}
    assert keys == {"qtr_volume_growth_yoy"}


def test_healthcare_stores_only_explicit_fields(monkeypatch, db):
    """Alkem-shaped pharma: US share stated, hospital fields null -> one row."""
    _common_mocks(monkeypatch, {"bed_occupancy_pct": None, "arpob_inr_per_day": None, "us_revenue_pct": 21.7})
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:ALKEM", symbol="ALKEM", sector_name="Healthcare")
    assert {r.metric_key: float(r.value) for r in result} == {"qtr_healthcare_us_revenue_pct": 21.7}


def test_healthcare_prompt_refuses_the_known_hospital_traps():
    p = qomi._AREA_PROMPTS["healthcare"].lower()
    for guard in ("per year", "arpp", "single city", "interleaved", "never invent"):
        assert guard in p


def test_fallback_llm_response_is_not_stored(monkeypatch, db):
    extracted = {
        "sales_million_tonnes_current_quarter": 17.1, "sales_million_tonnes_yoy_prior_quarter": 19.9,
        "sales_million_tonnes_qoq_prior_quarter": None, "cost_per_tonne_reported": None,
        "ebitda_per_tonne_reported": None,
    }
    _common_mocks(monkeypatch, extracted)
    monkeypatch.setattr(qomi.default_llm_client, "last_used_fallback", True)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id=_COMPANY_ID, symbol="AMBUJACEM", sector_name="Cement")
    assert result == []


# ── Source cascade: Investor Presentation -> earnings-call transcript ─────

def _mock_transcript(monkeypatch, extracted: dict, seen: dict | None = None):
    class _Resp:
        content = b"%PDF-fake"

        def raise_for_status(self):
            pass

    class _Session:
        def get(self, url, **kw):
            return _Resp()

    monkeypatch.setattr(qomi.nse_client, "_session", lambda: _Session())
    monkeypatch.setattr(qomi, "find_transcript_filings", lambda symbol, session=None, **kw: [
        {"an_dt": "17-Aug-2026 12:00:00", "attchmntFile": "https://example.com/transcript.pdf"}])
    monkeypatch.setattr(qomi, "locate_sections",
                        lambda pdf_bytes, **kw: ({area: [0] for area in _ALL_QUARTERLY_AREAS}, {}))

    class _Page:
        def extract_text(self_inner, **kw):
            return "Q1 FY27 earnings call. ARPOB for the quarter stood at INR 77,900."

    class _Pdf:
        pages = [_Page()]

        def __enter__(self_inner):
            return self_inner

        def __exit__(self_inner, *a):
            return False

    monkeypatch.setattr(qomi.pdfplumber, "open", lambda *a, **k: _Pdf())

    def _extract(prompt_key, text, prefix=""):
        if seen is not None:
            seen["prefix"] = prefix
        return extracted

    monkeypatch.setattr(qomi, "extract_area", _extract)
    monkeypatch.setattr(qomi.default_llm_client, "last_used_fallback", False)


def test_cascade_falls_back_to_transcript_when_no_deck(monkeypatch, db):
    """Max-Healthcare-shaped: no usable deck, but management states ARPOB on
    the call ("ARPOB for the quarter stood at INR 77,900")."""
    monkeypatch.setattr(qomi.ipc, "fetch_latest_investor_presentation", lambda symbol: None)
    seen: dict = {}
    _mock_transcript(monkeypatch, {"bed_occupancy_pct": 75.0, "arpob_inr_per_day": 77900.0, "us_revenue_pct": None}, seen)

    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:MAXHEALTH", symbol="MAXHEALTH", sector_name="Healthcare")
    by_key = {r.metric_key: r for r in result}
    assert by_key["qtr_healthcare_arpob"].value == 77900.0
    assert by_key["qtr_healthcare_arpob"].source == "NSE_CONCALL"
    # transcript figures are capped below HIGH — management rounds ("more than 75%")
    assert by_key["qtr_healthcare_arpob"].confidence == "MEDIUM"
    assert "EARNINGS CALL TRANSCRIPT" in seen["prefix"]
    assert "transcript" in by_key["qtr_healthcare_arpob"].source_document.lower()


def test_cascade_skips_transcript_when_deck_delivers(monkeypatch, db):
    _common_mocks(monkeypatch, {"bed_occupancy_pct": None, "arpob_inr_per_day": None, "us_revenue_pct": 21.7})
    called = {"transcript": False}
    monkeypatch.setattr(qomi, "_ingest_from_filing", lambda *a, **k: called.__setitem__("transcript", True) or [])
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:ALKEM", symbol="ALKEM", sector_name="Healthcare")
    assert [r.metric_key for r in result] == ["qtr_healthcare_us_revenue_pct"]
    assert result[0].source == "NSE_INVESTOR_PRESENTATION" and result[0].confidence == "HIGH"
    assert called["transcript"] is False


def test_transcript_path_never_stores_fallback_llm_output(monkeypatch, db):
    monkeypatch.setattr(qomi.ipc, "fetch_latest_investor_presentation", lambda symbol: None)
    _mock_transcript(monkeypatch, {"bed_occupancy_pct": 75.0, "arpob_inr_per_day": None, "us_revenue_pct": None})
    monkeypatch.setattr(qomi.default_llm_client, "last_used_fallback", True)
    assert qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:MAXHEALTH", symbol="MAXHEALTH", sector_name="Healthcare") == []


def test_transcript_source_does_not_leak_into_later_deck_writes(monkeypatch, db):
    monkeypatch.setattr(qomi.ipc, "fetch_latest_investor_presentation", lambda symbol: None)
    _mock_transcript(monkeypatch, {"bed_occupancy_pct": 75.0, "arpob_inr_per_day": None, "us_revenue_pct": None})
    qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:MAXHEALTH", symbol="MAXHEALTH", sector_name="Healthcare")
    assert qomi._source_ctx.get() == "NSE_INVESTOR_PRESENTATION"


def test_press_release_layer_precedes_transcript_and_keeps_high_confidence(monkeypatch, db):
    """Rainbow-shaped: no deck; the results press release carries a clean KPI
    table, so it wins over the transcript and is NOT capped at MEDIUM."""
    monkeypatch.setattr(qomi.ipc, "fetch_latest_investor_presentation", lambda symbol: None)
    order = []

    def _fake_filing(db_, company_id, symbol, sector_name, kind):
        order.append(kind)
        if kind == "press":
            token = qomi._source_ctx.set("NSE_PRESS_RELEASE")
            try:
                return qomi._store_extracted(
                    db_, company_id, sector_name, qomi._SECTOR_CONFIG[sector_name],
                    {"bed_occupancy_pct": 41.24, "arpob_inr_per_day": 67256.0, "us_revenue_pct": None},
                    "2026-06-30", "CONSOLIDATED", "https://example.com/pr.pdf", "NSE results press release", [])
            finally:
                qomi._source_ctx.reset(token)
        return []

    monkeypatch.setattr(qomi, "_ingest_from_filing", _fake_filing)
    result = qomi.ingest_quarterly_operating_metrics(db, company_id="NSE:RAINBOW", symbol="RAINBOW", sector_name="Healthcare")
    by_key = {r.metric_key: r for r in result}
    assert order == ["press"]  # transcript never consulted
    assert by_key["qtr_healthcare_arpob"].value == 67256.0
    assert by_key["qtr_healthcare_arpob"].source == "NSE_PRESS_RELEASE"
    assert by_key["qtr_healthcare_arpob"].confidence == "HIGH"


def test_find_nse_filings_keeps_only_press_releases_newest_first(monkeypatch):
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {"desc": "Press Release", "an_dt": "03-Sep-2026 13:43:29", "attchmntFile": "https://x/a.pdf"},
                {"desc": "Outcome of Board Meeting", "an_dt": "13-Aug-2026 14:26:54", "attchmntFile": "https://x/o.pdf"},
                {"desc": "Press Release", "an_dt": "13-Aug-2026 14:32:49", "attchmntFile": "https://x/b.pdf"},
                {"desc": "Press Release", "an_dt": "14-Aug-2026 10:00:00", "attchmntFile": None},
            ]

    class _S:
        def get(self, *a, **k):
            return _Resp()

    out = qomi._find_nse_filings("MAXHEALTH", "press", _S())
    assert [f["attchmntFile"] for f in out] == ["https://x/a.pdf", "https://x/b.pdf"]
