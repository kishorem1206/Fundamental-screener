"""Route smoke tests for `/api/pl-intelligence/*` (P&L Analysis Engine
plan, Milestone 5) — the first route-level test in this codebase (no
existing route had a `TestClient`-based test to mirror). Confirms the
route registration-order fix (specific sub-paths before the greedy
`{company_id:path}` catch-all) actually holds, and that every endpoint
degrades cleanly (200, not 500) for a company with zero P&L Intelligence
data computed yet.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_UNKNOWN_COMPANY = "NOT-A-REAL-COMPANY-ID"


def test_base_route_returns_200_for_unknown_company():
    response = client.get(f"/api/pl-intelligence/{_UNKNOWN_COMPANY}")
    assert response.status_code == 200
    body = response.json()
    assert body["period"] is None
    assert "score" in body
    assert body["score"]["components"] == {"M1": None, "M2": None, "M3": None, "M4": None, "M5": None}


def test_score_subroute_does_not_get_swallowed_by_base_route():
    # Regression test for the real routing bug found live-testing this
    # session: the bare "/{company_id:path}" route, if registered before
    # this one, greedily matches "NOT-A-REAL-COMPANY-ID/score" as a single
    # company_id (since :path converters match slashes too) and the /score
    # handler never runs. A correctly-routed response has the narrower
    # {company_id, period, score, diagnostic_flags, diagnostics} shape,
    # not the base route's full ~10-key shape.
    response = client.get(f"/api/pl-intelligence/{_UNKNOWN_COMPANY}/score")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"company_id", "period", "score", "diagnostic_flags", "diagnostics"}
    assert body["company_id"] == _UNKNOWN_COMPANY


def test_peers_subroute_does_not_get_swallowed_by_base_route():
    response = client.get(f"/api/pl-intelligence/{_UNKNOWN_COMPANY}/peers")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"company_id", "period", "peer_percentiles"}


def test_history_subroute_does_not_get_swallowed_by_base_route():
    response = client.get(f"/api/pl-intelligence/{_UNKNOWN_COMPANY}/history")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"company_id", "statement_type", "cascade", "earnings_bridge"}


def test_base_route_real_company():
    response = client.get("/api/pl-intelligence/NSE:MARUTI")
    assert response.status_code == 200
    body = response.json()
    assert body["period"] is not None
    assert body["score"]["master_pl_score"] is not None
    assert body["structure"]["csr_band"] == "PRIMARILY_PARENT_DOMESTIC"
