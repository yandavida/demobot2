"""
Route-sanity regression test: ensures FastAPI app loads, OpenAPI builds, and critical V2 routes are present.
- Import-safe
- OpenAPI schema builds
- Checks for key (method, path) pairs
"""
from api.main import app

def test_openapi_builds():
    schema = app.openapi()
    assert "openapi" in schema
    assert "paths" in schema


def test_critical_v2_routes_present():
    # Collect all (method, path) pairs from app.routes
    route_set = set()
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                # FastAPI includes HEAD/OPTIONS automatically; focus on main verbs
                if method in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                    route_set.add((method, route.path))

    # At least one v2 command boundary endpoint (e.g., ingest)
    v2_command = ("POST", "/api/v2/sessions/{session_id}/events")
    assert v2_command in route_set, f"Missing V2 command boundary: {v2_command}"

    # At least one v2 read-only view endpoint (e.g., snapshot metadata)
    v2_read = ("GET", "/api/v2/sessions/{session_id}/snapshot/metadata")
    assert v2_read in route_set, f"Missing V2 read-only endpoint: {v2_read}"

    # Assert V2 prefix is present in at least one route
    assert any(path.startswith("/api/v2/") for _, path in route_set), "No /api/v2/ prefix found in routes"
