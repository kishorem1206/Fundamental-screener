"""Tests for `app/ingestion/nse_ipo_client.py` — NSE public-past-issues/
all-upcoming-issues parsing, and the within-fetch duplicate-key dedup that
`ingest_ipo_issues` needs (NSE's own past-issues endpoint repeats several
rows verbatim, e.g. every InvIT/REIT/NCD entry with two allotment
tranches — confirmed live, "PKH" on 2023-06-30 appears twice)."""
from __future__ import annotations

from datetime import date

from app.infrastructure.database.models import IPOIssue
from app.ingestion import nse_ipo_client as ic

_COMPANY = "TEST:PKH"


def test_parse_date_handles_dd_mon_yyyy():
    assert ic._parse_date("24-SEP-2026") == date(2026, 9, 24)


def test_parse_date_dash_is_none():
    assert ic._parse_date("-") is None
    assert ic._parse_date(None) is None
    assert ic._parse_date("") is None


def test_parse_price_range_with_to():
    assert ic._parse_price_range("Rs.140 to Rs.148") == (140.0, 148.0)


def test_parse_price_range_single_fixed_price():
    assert ic._parse_price_range("Rs.94") == (94.0, 94.0)
    assert ic._parse_price_range("RS.41") == (41.0, 41.0)


def test_parse_price_range_missing_to_word():
    # Real formatting gap found in NSE's own export: "Rs.130 Rs.140"
    assert ic._parse_price_range("Rs.130 Rs.140") == (130.0, 140.0)


def test_parse_price_range_no_dot_and_trailing_space():
    assert ic._parse_price_range("Rs 180 to Rs 186") == (180.0, 186.0)
    assert ic._parse_price_range("Rs.163 to RS.171") == (163.0, 171.0)


def test_parse_price_range_none_or_dash():
    assert ic._parse_price_range(None) == (None, None)
    assert ic._parse_price_range("-") == (None, None)


def test_parse_issue_price_bare_number_with_padding():
    assert ic._parse_issue_price("   186") == 186.0


def test_parse_issue_price_dash_or_excel_overflow_is_none():
    assert ic._parse_issue_price("-") is None
    assert ic._parse_issue_price("######") is None
    assert ic._parse_issue_price(None) is None


def test_upsert_past_issue_skips_row_with_no_symbol_or_start_date():
    now = ic.datetime.now(ic.timezone.utc)
    assert ic._upsert_past_issue(None, {"company": "X", "symbol": "", "ipoStartDate": "24-SEP-2026"}, now, {}) is None
    assert ic._upsert_past_issue(None, {"company": "X", "symbol": "X", "ipoStartDate": "-"}, now, {}) is None


def test_upsert_past_issue_duplicate_within_same_fetch_updates_one_row_not_two(db):
    """The real bug: two identical rows for the same (symbol, start date) in
    one API response used to create two IPOIssue objects with the same
    natural key, both flushed as INSERTs, violating the unique constraint
    before either committed."""
    now = ic.datetime.now(ic.timezone.utc)
    cache: dict = {}
    row = {"company": "PKH Test", "symbol": "PKHTST", "ipoStartDate": "30-JUN-2023",
           "ipoEndDate": "03-JUL-2023", "priceRange": "Rs.100 to Rs.110", "securityType": "IV",
           "listingDate": "-", "issuePrice": "-"}
    first = ic._upsert_past_issue(db, row, now, cache)
    second = ic._upsert_past_issue(db, dict(row), now, cache)
    assert first is second  # same in-memory object, not a duplicate
    assert len(cache) == 1
    db.add(first)
    db.flush()  # would raise IntegrityError if this were two separate rows
    assert db.query(IPOIssue).filter_by(symbol="PKHTST").count() == 1


def test_ingest_ipo_issues_dedups_across_both_endpoints(db, monkeypatch):
    """A symbol appearing in BOTH `public-past-issues` (already listed) and
    `all-upcoming-issues` (still-open, shouldn't normally overlap but NSE's
    own data has shown cross-endpoint drift before) must still resolve to
    one row per (symbol, issue_start_date), not two."""
    monkeypatch.setattr(ic, "_session", lambda: object())
    monkeypatch.setattr(ic, "fetch_past_issues", lambda s: [
        {"company": "Dup Co", "symbol": "DUPCO", "ipoStartDate": "01-JAN-2026", "ipoEndDate": "03-JAN-2026",
         "priceRange": "Rs.50 to Rs.55", "securityType": "EQ", "listingDate": "10-JAN-2026", "issuePrice": "-"},
    ])
    monkeypatch.setattr(ic, "fetch_upcoming_issues", lambda s: [
        {"companyName": "Dup Co", "symbol": "DUPCO", "issueStartDate": "01-JAN-2026", "issueEndDate": "03-JAN-2026",
         "issuePrice": "Rs.50 to Rs.55", "series": "EQ", "status": "Active"},
    ])
    result = ic.ingest_ipo_issues(db)
    db.flush()
    assert result["past_written"] == 1
    assert result["upcoming_written"] == 1
    assert db.query(IPOIssue).filter_by(symbol="DUPCO").count() == 1
    # the later (upcoming) write must not have clobbered the real listing_date
    # the earlier (past) write established
    row = db.query(IPOIssue).filter_by(symbol="DUPCO").one()
    assert row.listing_date == date(2026, 1, 10)
