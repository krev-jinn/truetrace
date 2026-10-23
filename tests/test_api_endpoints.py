"""
Integration Tests for TrueTrace FastAPI Endpoints
Tests full end-to-end pipeline: investigation, evidence ingestion, arbitration, graphs, scenarios, reports.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_investigation_lifecycle():
    # 1. Create
    resp = client.post("/api/investigations", json={
        "name": "Integration Test Inv",
        "description": "Automated verification test"
    })
    assert resp.status_code == 200
    data = resp.json()
    inv_id = data["id"]
    assert inv_id.startswith("inv-")

    # 2. Get
    resp2 = client.get(f"/api/investigations/{inv_id}")
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "Integration Test Inv"

    # 3. List
    resp3 = client.get("/api/investigations")
    assert resp3.status_code == 200
    assert any(inv["id"] == inv_id for inv in resp3.json())

    # 4. Cleanup
    resp4 = client.delete(f"/api/investigations/{inv_id}")
    assert resp4.status_code == 200


def test_scenario_execution_case_1_supported():
    resp = client.post("/api/scenarios/run", json={"scenario_id": "scenario_1_supported"})
    assert resp.status_code == 200
    data = resp.json()
    inv_id = data["investigation_id"]

    assert data["summary"]["supported"] >= 1
    assert data["summary"]["contradicted"] == 0

    # Verify Candidate Graph
    cand_resp = client.get(f"/api/graphs/{inv_id}/candidate")
    assert cand_resp.status_code == 200
    cand_data = cand_resp.json()
    assert len(cand_data["nodes"]) > 0

    # Verify Refined Graph
    ref_resp = client.get(f"/api/graphs/{inv_id}/refined")
    assert ref_resp.status_code == 200
    ref_data = ref_resp.json()
    # Check that at least one edge has verdict SUPPORTED
    supported_edges = [e for e in ref_data["edges"] if e["data"].get("verdict") == "SUPPORTED"]
    assert len(supported_edges) >= 1

    # Verify Markdown Report
    rep_resp = client.get(f"/api/reports/{inv_id}/markdown")
    assert rep_resp.status_code == 200
    assert "# TrueTrace Forensic Investigation Report" in rep_resp.text
    assert "SUPPORTED" in rep_resp.text


def test_scenario_execution_case_2_contradicted():
    resp = client.post("/api/scenarios/run", json={"scenario_id": "scenario_2_contradicted"})
    assert resp.status_code == 200
    data = resp.json()
    inv_id = data["investigation_id"]

    assert data["summary"]["contradicted"] >= 1
    assert data["summary"]["supported"] == 0

    ref_resp = client.get(f"/api/graphs/{inv_id}/refined")
    ref_data = ref_resp.json()
    con_edges = [e for e in ref_data["edges"] if e["data"].get("verdict") == "CONTRADICTED"]
    assert len(con_edges) >= 1


def test_scenario_execution_case_3_unresolved():
    resp = client.post("/api/scenarios/run", json={"scenario_id": "scenario_3_unresolved"})
    assert resp.status_code == 200
    data = resp.json()
    inv_id = data["investigation_id"]

    assert data["summary"]["unresolved"] >= 1
    assert data["summary"]["contradicted"] == 0
    assert data["summary"]["supported"] == 0

    ref_resp = client.get(f"/api/graphs/{inv_id}/refined")
    ref_data = ref_resp.json()
    unr_edges = [e for e in ref_data["edges"] if e["data"].get("verdict") == "UNRESOLVED"]
    assert len(unr_edges) >= 1


def test_live_tcp_experiment():
    resp = client.post("/api/scenarios/run", json={"scenario_id": "live_tcp_supported"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["summary"]["supported"] >= 1
