"""Results calendar (app/results/). Offline."""
from datetime import date, datetime, timezone
from types import SimpleNamespace as NS

from app.results import calendar


def test_only_results_meetings_of_stocks_we_hold():
    rows = [{"symbol": "AAA", "purpose": "Financial Results/Dividend", "date": "20-Oct-2026"},
            {"symbol": "AAA", "purpose": "Financial Results", "date": "20-Oct-2026"},
            {"symbol": "BBB", "purpose": "Fund Raising", "date": "21-Oct-2026"},
            {"symbol": "ZZZ", "purpose": "Financial Results", "date": "21-Oct-2026"},
            {"symbol": "CCC", "purpose": "Financial Results", "date": "not a date"}]
    got = calendar.parse(rows, {"AAA": "NSE:AAA", "BBB": "NSE:BBB", "CCC": "NSE:CCC"})
    assert got == [{"stock_id": "NSE:AAA", "board_date": date(2026, 10, 20), "purpose": "Financial Results"}]


def test_the_stored_quarter_must_belong_to_the_meeting():
    meeting = date(2026, 11, 14)
    assert calendar.has_quarter("2026-09-30", meeting)
    assert not calendar.has_quarter("2026-06-30", meeting)  # last quarter's numbers: Screener has not updated
    assert not calendar.has_quarter(None, meeting)
    assert calendar.has_quarter("2026-03-31", date(2026, 5, 30))  # year-end results, 60 days on
    # an early-October meeting reports September, however recent June looks
    assert not calendar.has_quarter("2026-06-30", date(2026, 10, 8))
    assert calendar.expected_quarter(date(2026, 1, 20)) == date(2025, 12, 31)


def _row(attempts=0):
    return NS(board_date=date(2026, 11, 2), status="PENDING", attempts=attempts, quarter=None, last_tried_at=None, done_at=None)


def test_a_stock_waits_for_its_quarter_then_gives_up():
    now = datetime(2026, 11, 3, tzinfo=timezone.utc)
    r = _row()
    calendar.settle(r, "2026-06-30", now, tried=True)
    assert r.status == "PENDING" and r.attempts == 1 and r.quarter == "2026-06-30"
    r = _row()
    calendar.settle(r, "2026-09-30", now, tried=True)
    assert r.status == "DONE" and r.done_at == now
    r = _row(attempts=4)
    calendar.settle(r, "2026-06-30", now, tried=True)
    assert r.status == "GAVE_UP"


def test_checking_without_reading_does_not_use_up_a_try():
    r = _row()
    calendar.settle(r, "2026-06-30", datetime(2026, 11, 3, tzinfo=timezone.utc), tried=False)
    assert r.attempts == 0 and r.status == "PENDING" and r.last_tried_at is None


def test_full_analysis_is_redone_once_for_a_new_quarter():
    from app.results.full_analysis import is_due

    landed = datetime(2026, 11, 3, tzinfo=timezone.utc)
    before, after = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 11, 4, tzinfo=timezone.utc)
    assert is_due(before, True, landed)
    assert not is_due(after, True, landed)  # already redone, or tried and failed: not every night
    assert not is_due(before, False, landed)  # never fully analysed: not added to the list
    assert not is_due(None, False, landed)


def test_yahoo_zeros_and_gaps_are_missing_not_numbers():
    from app.results.estimates import parse

    got = parse({"avg": 31.9, "low": 26.6, "high": 38.6, "yearAgoEps": 25.97, "numberOfAnalysts": 12.0}, {"avg": 31970000000, "yearAgoRevenue": 27150000000, "numberOfAnalysts": 21})
    assert got["eps_estimate"] == 31.9 and got["eps_analysts"] == 12 and got["revenue_estimate_cr"] == 3197.0 and got["revenue_year_ago_cr"] == 2715.0
    empty = parse({"avg": 0.0, "numberOfAnalysts": float("nan")}, None)
    assert empty["eps_estimate"] is None and empty["eps_analysts"] is None and empty["revenue_estimate_cr"] is None


def test_day_ordering_and_surprise():
    from app.routes.macro import _day_group, _surprise

    assert _day_group(True, 40.0) == "held" and _day_group(False, 75.0) == "strong" and _day_group(False, 69.9) == "other" and _day_group(False, None) == "other"
    assert _surprise(11.0, 10.0) == 10.0 and _surprise(9.0, 10.0) == -10.0 and _surprise(-1.0, -2.0) == 50.0
    assert _surprise(None, 10.0) is None and _surprise(11.0, None) is None
