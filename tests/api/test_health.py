"""Tests for the API health endpoint."""

from unittest.mock import patch

from website.extensions import cache, db


def test_health_returns_ok(api_client):
    """GET /api/v1/health returns 200 with expected JSON fields."""
    response = api_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.content_type == "application/json"

    data = response.get_json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["cache"] == "ok"
    assert "version" in data
    assert "uptime" in data
    assert "timestamp" in data


def test_health_no_auth_required(api_client):
    """Health endpoint should not require authentication."""
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_reports_unhealthy_on_database_failure(api_client):
    """A DB probe failure fails the healthcheck (503), not a silent 200.

    Without this, the container healthcheck (`curl -f`) would keep passing
    while the app can't serve a single real page.
    """
    with patch.object(db.session, "execute", side_effect=Exception("connection refused")):
        response = api_client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.get_json()
    assert data["status"] == "error"
    assert data["database"] == "error"


def test_health_reports_unhealthy_on_cache_failure(api_client):
    """A cache (Redis) probe failure also fails the healthcheck (503)."""
    with patch.object(cache, "get", side_effect=Exception("connection refused")):
        response = api_client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.get_json()
    assert data["status"] == "error"
    assert data["cache"] == "error"
