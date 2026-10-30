"""Phases C and D: macro sources and FPI flows (app/macro/). Offline: parsers on fixed text."""
from datetime import date
from types import SimpleNamespace as NS

from app.macro import fpi, sources


def test_rbi_current_rates_block():
    html = """<div><script>var x = 'Policy Repo Rate : 9.99%';</script>Policy&nbsp; Rates Policy Repo Rate : <b>5.50%</b> Standing Deposit Facility Rate : 5.25%
    Marginal Standing Facility Rate : 5.75% Bank Rate : 5.75% Reserve &nbsp;Ratios CRR : 3.00% SLR : 18.00% INR / 1 USD : 95.2492 INR / 1 GBP : 127.60
    Money Market Call Rates : 4.30% - 5.80% * * as on October 29, 2026 6.20% GS 2029 : 7.0470% # 6.36% GS 2031 : 7.1645% # 6.94% GS 2036 : 7.3888% # 7.63% GS 2056 : 7.8335%</div>"""
    got = {s: v for s, _, v in sources.parse_rbi(html, date(2026, 10, 30))}
    assert got == {"repo": 5.5, "sdf": 5.25, "msf": 5.75, "crr": 3.0, "slr": 18.0, "usd_inr": 95.2492, "call_rate": 5.8, "gsec_10y": 7.3888}


def test_mospi_rows():
    cpi = sources.parse_cpi([{"year": "2026", "month": "September", "inflation": "5.54"}, {"year": "2025", "month": "March", "inflation": None}])
    assert cpi == [("cpi_inflation", date(2026, 9, 30), 5.54)]
    assert sources.parse_iip([{"year": 2026, "month": "February", "growth_rate": "5.1"}]) == [("iip_growth", date(2026, 2, 28), 5.1)]
    wpi = sources.parse_wpi([{"year": 2026, "month": "September", "group": None, "index_value": "110"},
                             {"year": 2025, "month": "September", "group": None, "index_value": "100"},
                             {"year": 2026, "month": "September", "group": "Food Articles", "index_value": "999"}])
    assert wpi == [("wpi_inflation", date(2026, 9, 30), 10.0)]


def test_gdp_growth_from_constant_prices():
    q = [{"year": "2026-27", "quarter": "Q1", "constant_price": "8136153"}, {"year": "2025-26", "quarter": "Q1", "constant_price": "7546230"},
         {"year": "2025-26", "quarter": "Q4", "constant_price": "8880334"}]
    a = [{"year": "2025-26", "constant_price": "32470100"}, {"year": "2024-25", "constant_price": "30115428"}]
    got = {(s, d): v for s, d, v in sources.parse_gdp(q, a)}
    assert got == {("gdp_growth_q", date(2026, 6, 30)): 7.82, ("gdp_growth_a", date(2026, 3, 31)): 7.82}


def test_fx_reserves_take_the_dollar_total():
    rows = [{"year": "2025", "month": "June", "foreign_exchange_reserve_type": "Total", "foreign_exchange_reserve_currency": "US $ Millions", "value": "698120"},
            {"year": "2025", "month": "June", "foreign_exchange_reserve_type": "Total", "foreign_exchange_reserve_currency": "₹ Crores", "value": "5971165"},
            {"year": "2025", "month": "June", "foreign_exchange_reserve_type": "SDRs", "foreign_exchange_reserve_currency": "US $ Millions", "value": "18000"}]
    assert sources.parse_fx_reserves(rows) == [("fx_reserves", date(2025, 6, 30), 698.12)]


def test_cboe_and_world_bank():
    text = "DATE,OPEN,HIGH,LOW,CLOSE\n10/28/2026,17,18,16,16.91\n01/02/2020,13,14,13,12.47\n"
    assert sources.parse_cboe(text, date(2026, 1, 1)) == [("cboe_vix", date(2026, 10, 28), 16.91)]
    wb = [{"page": 1}, [{"date": "2025", "value": 6.5012}, {"date": "2024", "value": None}]]
    assert sources.parse_world_bank("wb_gdp_growth", wb) == [("wb_gdp_growth", date(2025, 12, 31), 6.5)]
    assert sources.parse_world_bank("wb_gdp_growth", [{"message": "x"}]) == []


_DAILY = """<table><tr><th>Reporting Date</th><th>Kind</th><th>Route</th><th>Buy</th><th>Sell</th><th>Net</th><th>USD</th></tr>
<tr><td>01-Oct-2026</td><td>Equity</td><td>Stock Exchange</td><td>1</td><td>2</td><td>(9,569.57)</td><td>0</td></tr>
<tr><td>01-Oct-2026</td><td>Equity</td><td>Sub-total</td><td>1</td><td>2</td><td>(9,231.88)</td><td>0</td></tr>
<tr><td>01-Oct-2026</td><td>Debt-General Limit</td><td>Sub-total</td><td>1</td><td>2</td><td>(669.12)</td><td>0</td></tr>
<tr><td>01-Oct-2026</td><td>Debt-VRR</td><td>Sub-total</td><td>1</td><td>2</td><td>163.52</td><td>0</td></tr>
<tr><td>Note</td><td>Note</td><td>Note</td><td>Note</td><td>Note</td><td>Note</td><td>Note</td></tr></table>"""


def test_nsdl_daily_adds_debt_kinds_and_reads_brackets_as_negative():
    got = {s: v for s, _, v in fpi.parse_daily(_DAILY)}
    assert got == {"fpi_equity_daily": -9231.88, "fpi_debt_daily": -505.6}


def _sector_html():
    cols = [("", "", "", "Sr. No."), ("", "", "", "Sectors")]
    for title in ("AUC as on September 30, 2026", "Net Investment October 01-15, 2026", "AUC as on October 15, 2026"):
        cols += [(title, "IN INR Cr.", "Equity", "Equity"), (title, "IN INR Cr.", "Mutual Funds", "Equity"), (title, "IN USD Mn", "Equity", "Equity")]
    rows = [[*c] for c in zip(*cols)]
    rows += [[1, "Capital Goods", 487700, 0, 1, -6533, 0, 1, 477593, 0, 1], [2, "Sovereign", 0, 0, 0, 0, 0, 0, 0, 0, 0], [3, "Grand Total", 9, 9, 9, 9, 9, 9, 9, 9, 9]]
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table>{body}</table>"


def test_nsdl_sector_file_reads_fpi_equity_not_the_mutual_fund_column():
    rows = {(r["period_end"], r["sector"]): r for r in fpi.parse_sector_file(_sector_html())}
    assert set(rows) == {(date(2026, 9, 30), "Capital Goods"), (date(2026, 10, 15), "Capital Goods")}
    oct15 = rows[(date(2026, 10, 15), "Capital Goods")]
    assert oct15["net_cr"] == -6533 and oct15["auc_cr"] == 477593
    assert rows[(date(2026, 9, 30), "Capital Goods")]["auc_cr"] == 487700


def test_sector_flow_is_measured_against_what_is_held():
    r = lambda d, n, a: NS(sector="Power", period_end=date(2026, 10, d), net_cr=n, auc_cr=a)  # noqa: E731
    f = fpi._flow([r(15, 100.0, 10000.0), r(1, 300.0, 9000.0), NS(sector="Power", period_end=date(2026, 9, 30), net_cr=None, auc_cr=8000.0)])
    assert f["net_cr"] == 400 and f["held_cr"] == 10000 and f["net_pct_of_holding"] == 4.0 and f["fortnights"] == 2
    assert fpi._flow([NS(sector="Power", period_end=date(2026, 9, 30), net_cr=None, auc_cr=1.0)]) is None


def test_flows_do_not_reach_any_score():
    import pathlib

    for name in ("decision", "decisions", "quality", "business_quality", "relative_strength", "fundamental", "quantitative", "technical", "valuation"):
        assert "app.macro" not in pathlib.Path(f"app/framework/{name}.py").read_text()


def test_estimates_treat_zero_as_missing_and_prefer_next_year():
    from app.ingestion.estimate_revisions_client import parse

    trend = {"0y": {"current": 0.0, "30daysAgo": 0.0, "90daysAgo": 56.4},
             "+1y": {"current": 62.6, "30daysAgo": 64.15, "90daysAgo": 65.45}}
    p = parse(trend, {"+1y": {"upLast30days": 1.0, "downLast30days": 3.0}}, {"+1y": {"numberOfAnalysts": 30}})
    assert p["period"] == "+1y" and p["revision_90d_pct"] == -4.35 and p["up_30d"] == 1 and p["down_30d"] == 3 and p["analysts"] == 30
    # Krishna-style: no earlier estimate at all
    assert parse({"+1y": {"current": 48.2, "30daysAgo": 0.0, "90daysAgo": 0.0}}, {}, {}) is None
    assert parse({}, {}, {}) is None


def test_a_jump_from_a_split_is_not_a_revision():
    from app.ingestion.estimate_revisions_client import parse

    p = parse({"+1y": {"current": 20.0, "30daysAgo": 19.0, "90daysAgo": 100.0}}, {}, {})
    assert p["revision_90d_pct"] is None and p["revision_30d_pct"] == 5.26


def test_estimates_are_shown_never_scored(monkeypatch):
    import pathlib

    from app.framework import quantitative as q
    from app.ingestion import estimate_revisions_client as e

    assert "earnings_revisions" not in q._WEIGHTS and "earnings_revisions" not in q._WEIGHTS_LENDER
    for f in pathlib.Path("app/framework").glob("*.py"):
        assert "estimate_revisions_client" not in f.read_text().replace("(app/ingestion/estimate_revisions_client.py)", ""), f
    row = NS(period="+1y", eps_now=10.0, revision_90d_pct=None, revision_30d_pct=1.5, up_30d=1, down_30d=0, analysts=2, on_date=date(2026, 10, 30))
    monkeypatch.setattr(e, "latest", lambda db, sid: row)
    assert e.for_stock(None, "X")["over"] == "30 days" and e.for_stock(None, "X")["revision_pct"] == 1.5


def test_rss_with_cdata_and_news_matching():
    from app.ingestion.news_feeds import parse_rss
    from app.risk.names import Matcher

    xml = """<rss><channel><title>x</title><item><title><![CDATA[Asian Paints&#39; profit jumps]]></title><link><![CDATA[https://x.in/a]]></link>
    <description><![CDATA[<p>Up 7%</p>]]></description><pubDate><![CDATA[Fri, 30 Oct 2026 15:14:09 +0530]]></pubDate></item>
    <item><title>No link here</title></item></channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1 and items[0]["headline"] == "Asian Paints' profit jumps" and items[0]["summary"] == "Up 7%" and items[0]["published_at"].year == 2026
    m = Matcher({"NSE:ASIANPAINT": {"Asian Paints Ltd."}, "NSE:TRENT": {"Trent Ltd."}, "NSE:BANKINDIA": {"Bank of India"}, "NSE:SBIN": {"State Bank of India"}})
    ids = lambda t: [x.stock_id for x in m.find_news(t)]  # noqa: E731
    assert ids("Asian Paints' strokes of price hikes") == ["NSE:ASIANPAINT"]
    assert ids("Trent shares soar 7% after Q2") == ["NSE:TRENT"]
    assert ids("The trent of the river rose") == []  # one word needs a market cue
    assert ids("State Bank of India raises rates") == ["NSE:SBIN"]
