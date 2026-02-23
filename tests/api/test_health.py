"""Tests for the API health endpoint."""


def test_health_returns_ok(api_client):
    """GET /api/v1/health returns 200 with expected JSON fields."""
    response = api_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.content_type == "application/json"

    data = response.get_json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "database" in data
    assert "uptime" in data
    assert "timestamp" in data


def test_health_no_auth_required(api_client):
    """Health endpoint should not require authentication."""
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
