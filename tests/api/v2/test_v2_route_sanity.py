# test_v2_route_sanity.py
"""
Regression test: verifies that the FastAPI app loads, OpenAPI builds, and critical V2 routes are present.
- Import-safe: should not raise on import
- OpenAPI schema builds
- Checks for key V2 endpoints
"""
from fastapi.testclient import TestClient
from api.main import app
import pytest

def test_app_import_and_openapi():
    client = TestClient(app)
    # OpenAPI schema loads
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "paths" in data

@pytest.mark.parametrize("route", [
    "/api/v2/sessions",  # POST
    "/api/v2/sessions/{session_id}/events",  # POST/GET
    "/api/v2/sessions/{session_id}/snapshot",  # POST/GET
    "/api/v2/sessions/{session_id}/snapshot/metadata",  # GET
    "/api/v2/sessions/{session_id}/compute/requests",  # GET
])
def test_v2_route_present(route):
    client = TestClient(app)
    openapi = client.get("/openapi.json").json()
    # Replace {session_id} with a path param template
    found = any(
        r.replace("{session_id}", "{session_id}") in openapi["paths"]
        for r in [route, route.replace("{session_id}", "{session_id}")]
    )
    assert found, f"Route {route} missing from OpenAPI paths"
