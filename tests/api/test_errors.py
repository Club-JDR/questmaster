"""Tests for API JSON error handlers."""


class TestJsonErrorHandlers:
    """Tests for JSON error responses on API routes."""

    def test_404_returns_json(self, api_client):
        """Non-existent API route returns JSON 404."""
        response = api_client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        assert response.content_type == "application/json"
        data = response.get_json()
        assert "error" in data
        assert "code" in data

    def test_405_returns_json(self, api_client):
        """Wrong HTTP method on API route returns JSON 405."""
        response = api_client.delete("/api/v1/health/")
        assert response.status_code == 405
        assert response.content_type == "application/json"

    def test_non_api_404_is_not_json(self, api_client):
        """Non-existent non-API route does NOT return JSON."""
        response = api_client.get("/nonexistent-page")
        assert response.status_code == 404
        # Should be HTML, not JSON
        assert "text/html" in response.content_type
