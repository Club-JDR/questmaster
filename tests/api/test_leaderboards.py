"""Tests for the leaderboard API endpoint."""

from unittest.mock import MagicMock, patch


class TestGetLeaderboards:
    """Tests for GET /api/v1/leaderboards/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/leaderboards/")
        assert response.status_code == 403

    @patch("website.api.leaderboards.trophy_service")
    def test_returns_all_categories(self, mock_service, api_client, auth_headers_user):
        """Returns all four leaderboard categories."""
        user = MagicMock()
        user.to_dict.return_value = {
            "id": "123456789012345678",
            "name": "Top Player",
        }

        mock_service.get_leaderboard.return_value = [(user, 42)]

        response = api_client.get("/api/v1/leaderboards/", headers=auth_headers_user)
        assert response.status_code == 200

        data = response.get_json()
        assert "oneshot_players" in data
        assert "campaign_players" in data
        assert "oneshot_gms" in data
        assert "campaign_gms" in data

        # Each category should have the mocked entry
        for category in ["oneshot_players", "campaign_players", "oneshot_gms", "campaign_gms"]:
            assert len(data[category]) == 1
            assert data[category][0]["user"]["name"] == "Top Player"
            assert data[category][0]["count"] == 42

    @patch("website.api.leaderboards.trophy_service")
    def test_empty_leaderboards(self, mock_service, api_client, auth_headers_user):
        """Returns empty lists when no trophies awarded."""
        mock_service.get_leaderboard.return_value = []

        response = api_client.get("/api/v1/leaderboards/", headers=auth_headers_user)
        assert response.status_code == 200

        data = response.get_json()
        for category in ["oneshot_players", "campaign_players", "oneshot_gms", "campaign_gms"]:
            assert data[category] == []
