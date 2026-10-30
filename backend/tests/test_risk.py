"""Phase A: SEBI orders and credit ratings (app/risk/). Offline — no network, no database."""
from datetime import date
from types import SimpleNamespace as NS

from app.framework import decision as dec
from app.framework.quality import compute_quality
from app.risk import record
from app.risk.names import Matcher
from app.risk.rating_text import parse
from app.risk.sebi_orders import classify_outcome, kind_of, largest_amount, operative_part

# ── rating letters ───────────────────────────────────────────────────────────

_COVER = ("To, National Stock Exchange of India Limited, Exchange Plaza, Bandra (East) Mumbai 400 051. Symbol: XYZ. "
          "Sub: Intimation under Regulation 30 of SEBI (LODR) Regulations, 2015. Dear Sir/Madam, ")


def test_reaffirmation_with_mixed_case_prefix():
    p = parse(_COVER + "we wish to inform you that Crisil Ratings has reaffirmed the ratings: Long Term Rating "
                       "Crisil AA-/Stable (Reaffirmed) Short Term Rating Crisil A1+ (Reaffirmed). Bank loan facilities Rs 500 crore.")
    assert p["parsed"] and p["agency"] == "CRISIL" and p["rating"] == "AA-" and p["short_term"] == "A1+"
    assert p["outlook"] == "Stable" and p["action"] == "REAFFIRMED" and p["instrument"] == "Bank facilities"


def test_upgrade_with_previous_rating():
    p = parse(_COVER + "Crisil Ratings has upgraded the rating. Long Term Bank Facilities 649.00 Crisil AA/Stable "
                       "(Upgraded from 'Crisil AA-/Stable').")
    assert p["action"] == "UPGRADE" and p["rating"] == "AA" and p["previous_rating"] == "AA-"


def test_rationale_boilerplate_is_not_a_downgrade():
    text = (_COVER + "CRISIL has reaffirmed the Company's long-term rating at CRISIL AA/Stable and short-term rating at CRISIL A1+. "
            "Thank you. " + "x" * 300 + " Rating Rationale ... Rating sensitivity factors. Negative factors: factors that "
            "could lead to a downgrade include a sharp fall in profit; the company was downgraded in 2019.")
    p = parse(text)
    assert p["action"] == "REAFFIRMED" and p["rating"] == "AA"


def test_outlook_revision_and_watch():
    p = parse(_COVER + "CARE Ratings has reaffirmed CARE A-; Positive, with revision in outlook from Stable to Positive. Bank facilities.")
    assert p["outlook"] == "Positive" and p["previous_outlook"] == "Stable" and p["action"] == "OUTLOOK_REVISED"
    w = parse(_COVER + "ICRA has placed the rating of [ICRA]AA+ on Rating Watch with Negative Implications. NCDs.")
    assert w["outlook"] == "Watch Negative" and w["action"] == "WATCH" and w["agency"] == "ICRA"


def test_agency_comes_from_the_rating_prefix_not_a_stray_word():
    p = parse(_COVER + "We take care to inform you that India Ratings and Research has affirmed IND AA-/Stable.")
    assert p["agency"] == "India Ratings" and p["rating"] == "AA-"


def test_letter_without_an_indian_scale_rating_is_not_parsed():
    p = parse(_COVER + "Moody's Ratings has affirmed the ratings at Baa3 level with Stable outlook.")
    assert not p["parsed"] and p.get("rating") is None


# ── SEBI order titles ───────────────────────────────────────────────────────

def _matcher():
    return Matcher({"NSE:OMAXE": {"Omaxe", "Omaxe Limited"}, "NSE:MPSLTD": {"MPS Ltd."}, "NSE:BSE": {"BSE Ltd."},
                    "NSE:SBIN": {"State Bank of India"}, "NSE:BANKINDIA": {"Bank of India"}, "NSE:INFY": {"Infosys Ltd."},
                    "NSE:ADANIENT": {"Adani Enterprises Ltd."}, "NSE:ADANIPORTS": {"Adani Ports and Special Economic Zone Ltd."}})


def test_titles_are_matched_conservatively():
    m = _matcher()
    ids = lambda t: sorted((x.stock_id, x.role) for x in m.find(t))  # noqa: E731
    assert ids("Order in the matter of Non-Compliance of Minimum Public Shareholding in Omaxe Limited") == [("NSE:OMAXE", "NAMED")]
    assert ids("Adjudication Order in the matter of Taurian MPS Ltd.") == []
    assert ids("Adjudication Order in respect of X in the matter of Illiquid Stock Options at BSE") == []
    assert ids("Settlement order in the matter of State Bank of India") == [("NSE:SBIN", "NAMED")]  # not Bank of India
    assert ids("Order in the matter of insider trading in the scrip of Infosys Limited") == [("NSE:INFY", "SCRIP")]
    assert ids("Final order in the matter of Adani Group Companies") == [("NSE:ADANIENT", "GROUP"), ("NSE:ADANIPORTS", "GROUP")]


def test_order_kinds_from_titles():
    assert kind_of("Appeal No. 7108 of 2026 filed by Meera Devi") == "RTI_APPEAL"
    assert kind_of("Exemption order in the matter of S Chand and Company Limited") == "EXEMPTION"
    assert kind_of("Confirmatory order in the matter of Rajesh Exports Limited") == "INTERIM"
    assert kind_of("Settlement Order in the matter of Cupid Limited") == "SETTLEMENT"
    assert kind_of("Adjudication Order in the matter of Prime Focus Limited.") == "ADJUDICATION"
    assert kind_of("Final order in the matter of Religare Enterprises Limited") == "FINAL"
    assert kind_of("Notice of Demand dated May 14, 2026 issued under RC No. 9112 of 2026") == "RECOVERY"


def test_outcome_from_the_operative_part():
    assert classify_outcome("the Noticees are hereby restrained from accessing the securities market")[0] == "DIRECTIONS"
    assert classify_outcome("Noticee no. 1 is hereby imposed with the following monetary penalties: 15A(b) 2 Lacs")[0] == "PENALTY"
    assert classify_outcome("the charges are not established; the proceedings are disposed of.")[0] == "DISPOSED"
    assert classify_outcome("a scanned page")[0] == "UNKNOWN"


# ── record and gates ────────────────────────────────────────────────────────

def _pair(day, kind, outcome, role="NAMED", named=True, title="Order in the matter of X Limited", penalty=None):
    o = NS(order_date=day, kind=kind, outcome=outcome, title=title, url=f"u{day}{kind}", pdf_url=None, penalty_rs=penalty)
    return o, NS(role=role, company_in_operative=named)


def test_regulatory_record_grades_and_flags():
    today = date(2026, 10, 30)
    rows = [_pair(date(2026, 9, 24), "ORDER", "PENALTY", penalty=15e7), _pair(date(2026, 1, 5), "ADJUDICATION", "PENALTY"),
            _pair(date(2025, 6, 1), "SETTLEMENT", None), _pair(date(2025, 3, 1), "ORDER", "PENALTY", named=False),
            _pair(date(2025, 2, 1), "ORDER", "DIRECTIONS", role="SCRIP"), _pair(date(2022, 1, 1), "FINAL", "DIRECTIONS")]
    r = record.regulatory_record(rows, today, earliest=date(2021, 10, 1))
    assert [o["grade"] for o in r["orders"]] == ["SERIOUS", "PENALTY", "SETTLED", "MATTER", "NOTE"]  # 2022 is outside 3 years
    assert r["deduction"] == 20 and r["red_flag"].startswith("SEBI order 2026-09-24 (penalty ₹15.00 crore)")
    clean = record.regulatory_record([], today, earliest=date(2021, 10, 1))
    assert clean["measured"] and clean["deduction"] == 0 and clean["red_flag"] is None
    assert not record.regulatory_record([], today, earliest=date(2025, 1, 1))["measured"]


def test_disposed_order_is_only_a_note():
    r = record.regulatory_record([_pair(date(2026, 5, 1), "FINAL", "DISPOSED")], date(2026, 10, 30), date(2021, 10, 1))
    assert r["orders"][0]["grade"] == "NOTE" and r["deduction"] == 0 and r["red_flag"] is None


def _rating(day, agency="CRISIL", rating="AA", outlook="Stable", action="REAFFIRMED", previous=None, parsed=True):
    return NS(announced_on=day, agency=agency, instrument="Bank facilities", rating=rating, short_term=None, outlook=outlook,
              action=action, previous_rating=previous, previous_outlook=None, parsed=parsed, filing_url=f"f{day}{agency}",
              rationale_url=None, excerpt=None)


def test_credit_status_reports_facts_and_judges_nothing():
    today = date(2026, 10, 30)
    r = record.credit_status([_rating(date(2026, 1, 1)), _rating(date(2026, 9, 1), rating="BB+", action="DOWNGRADE", outlook="Negative", previous="AA"),
                              _rating(date(2026, 2, 1), rating=None, parsed=False)], today)
    assert r["current"]["rating"] == "BB+" and r["letters"] == 3 and r["read"] == 2
    assert "red_flag" not in r and "flag" not in str(sorted(r))


def _s(q):
    return {"quality": q, "fundamental": q, "technical": 60, "relative_strength": 60, "valuation_view": "FAIR",
            "trend": "STABLE", "quality_direction": "STABLE"}


def test_only_the_sebi_record_can_fail_the_gate():
    rank = {"rank": 2, "of": 30, "top_pct": 6.7, "label": "Top 10%", "sector": "X"}
    clean = dec.decide(_s(80), {}, rank)
    # credit ratings are report-only: even a default in the detail changes nothing
    assert dec.decide(_s(80), {"risk": {"credit": {"red_flag": "CARE D"}}}, rank) == clean
    d = dec.decide(_s(80), {"risk": {"regulatory": {"red_flag": "SEBI order 2026-09-24 (penalty): X"}}}, rank)
    assert d["classification"] == "Replacement Candidate"
    assert d["gates"]["red_flags"] == ["governance: SEBI order 2026-09-24 (penalty): X"]
    # the same flag already carried by Quality is not listed twice
    d = dec.decide(_s(49), {"quality": {"governance_red_flag": "SEBI order 2026-09-24 (penalty): X"},
                            "risk": {"regulatory": {"red_flag": "SEBI order 2026-09-24 (penalty): X"}}}, rank)
    assert len(d["gates"]["red_flags"]) == 1


def test_serious_order_caps_quality():
    bq = {"score": 80.0, "components": {}, "regulatory_record": {"red_flag": "SEBI order 2026-09-24 (directions): X"}}
    q = compute_quality({"score": 85.0}, bq)
    assert q["score"] == 49.0 and q["governance_red_flag"].startswith("SEBI order")


def test_orders_against_others_in_the_company_matter():
    m = _matcher()
    roles = lambda t: sorted((x.stock_id, x.role) for x in m.find(t))  # noqa: E731
    assert roles("Adjudication Order in respect of Mr. R Saravanan in the matter of Infosys Ltd.") == [("NSE:INFY", "MATTER")]
    assert roles("Adjudication Order in respect of Omaxe Limited in the matter of Infosys Ltd.") == [("NSE:INFY", "MATTER"), ("NSE:OMAXE", "NAMED")]
    assert kind_of("Order under Regulation 11 of SEBI (SAST) Regulations, 2011 in the matter of Vodafone Idea Limited") == "EXEMPTION"
    assert kind_of("Order passed by the Hon'ble Court of Additional District Munsif") == "COURT"
    many = [_pair(date(2026, 1, d), "ADJUDICATION", "PENALTY", role="MATTER") for d in range(1, 11)]
    r = record.regulatory_record(many, date(2026, 10, 30), date(2021, 10, 1))
    assert r["deduction"] == 8 and {o["grade"] for o in r["orders"]} == {"MATTER"} and r["red_flag"] is None


def test_closed_without_directions_beats_a_quoted_restraint():
    t = ("The interim order had restrained the Noticees from accessing the market. 32. In view of the above, I hereby "
         "dispose of the SCN against the Noticee No.1, 2 and 3 without any directions.")
    assert classify_outcome(t)[0] == "DISPOSED"
    assert classify_outcome("the Noticee shall not take up any new assignment as merchant banker")[0] == "DIRECTIONS"


def test_footer_and_recital_are_removed_before_reading():
    title = "Order in the matter of Omaxe Limited"
    text = ("The earlier order restrained the promoters. A penalty of Rs. 8.32 crore was imposed by the NGT. "
            f"{title} 90 of 91 In exercise of the powers conferred upon me, I hereby dispose of the SCN without any directions. "
            f"{title} Page 91 of 91")
    part = operative_part(text, title)
    assert "NGT" not in part and "Omaxe" not in part
    assert classify_outcome(part)[0] == "DISPOSED"


def test_penalty_amounts():
    assert largest_amount("15A(b) 2 Lacs 15HA 15 Lacs 15HB 10 Lacs") == 15e5
    assert largest_amount("penalty of Rs.2,00,000/- and Rs.3,00,000/-") == 3e5
    assert largest_amount("Noticee No. 1 15 Crore 15.95 Crore") == 15.95e7


def test_grades_separate_debarment_from_a_small_fine():
    assert record.grade("ORDER", "DIRECTIONS", "NAMED", False) == "SERIOUS"  # its people debarred
    assert record.grade("ORDER", "PENALTY", "NAMED", True, 5e5) == "PENALTY"  # ₹5 lakh disclosure fine
    assert record.grade("ORDER", "PENALTY", "NAMED", True, 15e7) == "SERIOUS"
    assert record.grade("ORDER", "PENALTY", "NAMED", False, 15e7) == "MATTER"  # someone else fined
    assert record.grade("ORDER", "COMPLIANCE", "NAMED", True) == "PENALTY"
    assert record.grade("FINAL", "DIRECTIONS", "GROUP", False) == "MATTER"  # group order not naming this member
    assert record.grade("ADJUDICATION", "DIRECTIONS", "NAMED", True) == "PENALTY"


def test_front_running_a_company_is_not_against_it():
    m = Matcher({"NSE:LICI": {"Life Insurance Corporation of India"}})
    x = m.find("Confirmatory order in the matter of suspected entities front running the trades of Life Insurance Corporation of India")
    assert x[0].role == "SCRIP"
    assert kind_of("Order in the matter of Avil Menezes vs. Central Depository Services (India) Limited") == "COURT"


def test_default_and_low_ratings_are_read():
    p = parse(_COVER + "India Ratings has downgraded the Bank Loan Facilities rating to 'IND D' from 'IND BB'.")
    assert p["rating"] == "D" and p["previous_rating"] == "BB" and p["action"] == "DOWNGRADE"
    assert parse(_COVER + "Long Term Rating IVR C+/Stable (Rating Downgraded). Short Term Rating IVR A4 (Rating Downgraded).")["rating"] == "C+"
    assert parse(_COVER + "Long-term / Short-term bank facilities CARE D. Copy of the letter is attached.")["rating"] == "D"


def test_order_of_a_table_does_not_flip_the_rating():
    p = parse(_COVER + "[ICRA]BB+(Negative); Rating downgraded from [ICRA]BBB-(Negative). Non-Convertible Debentures.")
    assert p["rating"] == "BB+" and p["previous_rating"] == "BBB-"
    p = parse(_COVER + "Downgraded from CARE A; Fixed Deposit 33.22 CARE A-; Stable")
    assert p["rating"] == "A-" and p["previous_rating"] == "A"


def test_words_that_look_like_ratings_or_actions():
    assert parse(_COVER + "We are thankful for the kind A support. Crisil AA/Stable reaffirmed.")["rating"] == "AA"
    assert parse(_COVER + "Crisil AAA (CE)/Watch Negative. Rating continues on watch; it may be downgraded.")["action"] == "WATCH"
    p = parse(_COVER + "Form: Rating (Upgrade/Downgrade/Reaffirm) action. IND AA Stable Reaffirmed.")
    assert p["action"] == "REAFFIRMED"


def test_disgorgement_by_one_person_is_not_against_the_company():
    assert classify_outcome("the Noticee is liable to disgorge the amount of Rs.6,17,25,000")[0] == "DISGORGEMENT"
    assert record.grade("ORDER", "DISGORGEMENT", "NAMED", False) == "MATTER"
    assert record.grade("FINAL", "DISGORGEMENT", "NAMED", True) == "SERIOUS"


def test_outlook_is_read_beside_the_current_rating():
    p = parse(_COVER + "Existing Revised Rating/Outlook Long term bank facilities CRISIL A/Negative Crisil A-/Stable. Rating downgraded.")
    assert p["rating"] == "A-" and p["outlook"] == "Stable" and p["previous_rating"] == "A"


def test_a_form_heading_and_an_attached_rationale_are_not_actions():
    form = _COVER + "Type of credit rating (New/Upgraded/ other positive/ downgraded/ Reaffirm/other). IND AA Stable Reaffirmed."
    assert parse(form)["action"] == "REAFFIRMED"
    # no rating in the letter itself: the rating comes from the attachment, the action must not
    text = _COVER + "We enclose the letter from the agency regarding the assignment. " + "x" * 3600 + " BWR BBB/Stable. Could be downgraded."
    assert parse(text).get("action") != "DOWNGRADE" and parse(text)["rating"] == "BBB"
