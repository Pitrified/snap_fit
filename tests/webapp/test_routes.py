"""Smoke tests for webapp routes."""

from fastapi.testclient import TestClient

from snap_fit.webapp.main import create_app


def client() -> TestClient:
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_ping() -> None:
    """Health endpoint returns ok."""
    c = client()
    response = c.get("/api/v1/debug/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_available() -> None:
    """OpenAPI schema is generated."""
    c = client()
    response = c.get("/api/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()
