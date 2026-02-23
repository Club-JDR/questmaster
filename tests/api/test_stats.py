"""Tests for the stats and calendar API endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch


class TestGetStats:
    """Tests for GET /api/v1/stats/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/stats/")
        assert response.status_code == 403

    @patch("website.api.stats.session_service")
    def test_returns_stats_current_month(self, mock_service, api_client, auth_headers_user):
        """Returns stats for current month when no params given."""
        mock_service.get_stats_for_period.return_value = {
            "base_day": datetime(2026, 2, 1),
            "last_day": datetime(2026, 2, 28, 23, 59, 59),
            "num_os": 5,
            "num_campaign": 3,
            "os_games": {},
            "campaign_games": {},
            "gm_names": ["Alice", "Alice", "Bob"],
        }

        response = api_client.get("/api/v1/stats/", headers=auth_headers_user)
        assert response.status_code == 200

        data = response.get_json()
        assert data["counts"]["oneshot"] == 5
        assert data["counts"]["campaign"] == 3
        assert data["counts"]["total"] == 8
        assert data["period"]["start"] == "2026-02-01T00:00:00"
        mock_service.get_stats_for_period.assert_called_once_with(None, None)

    @patch("website.api.stats.session_service")
    def test_returns_stats_specific_month(self, mock_service, api_client, auth_headers_user):
        """Returns stats for a specific year/month."""
        mock_service.get_stats_for_period.return_value = {
            "base_day": datetime(2025, 6, 1),
            "last_day": datetime(2025, 6, 30, 23, 59, 59),
            "num_os": 10,
            "num_campaign": 2,
            "os_games": {},
            "campaign_games": {},
            "gm_names": [],
        }

        response = api_client.get("/api/v1/stats/?year=2025&month=6", headers=auth_headers_user)
        assert response.status_code == 200
        mock_service.get_stats_for_period.assert_called_once_with(2025, 6)

    @patch("website.api.stats.session_service")
    def test_gm_leaderboard_sorted(self, mock_service, api_client, auth_headers_user):
        """GM leaderboard is sorted by count descending."""
        mock_service.get_stats_for_period.return_value = {
            "base_day": datetime(2026, 1, 1),
            "last_day": datetime(2026, 1, 31, 23, 59, 59),
            "num_os": 0,
            "num_campaign": 0,
            "os_games": {},
            "campaign_games": {},
            "gm_names": ["Bob", "Alice", "Alice", "Alice", "Bob"],
        }

        response = api_client.get("/api/v1/stats/", headers=auth_headers_user)
        data = response.get_json()
        leaderboard = data["gm_leaderboard"]
        assert leaderboard[0]["name"] == "Alice"
        assert leaderboard[0]["count"] == 3
        assert leaderboard[1]["name"] == "Bob"
        assert leaderboard[1]["count"] == 2


class TestGetCalendarEvents:
    """Tests for GET /api/v1/calendar/events/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/calendar/events/?start=2026-01-01&end=2026-02-01")
        assert response.status_code == 403

    @patch("website.api.stats.session_service")
    def test_returns_events(self, mock_service, api_client, auth_headers_user):
        """Returns calendar events for the given range."""
        game = MagicMock()
        game.name = "Test Game"
        game.type = "oneshot"
        game.slug = "test-game"

        session = MagicMock()
        session.id = 1
        session.start = datetime(2026, 1, 15, 18, 0)
        session.end = datetime(2026, 1, 15, 22, 0)
        session.game = game

        mock_service.find_in_range.return_value = [session]

        response = api_client.get(
            "/api/v1/calendar/events/?start=2026-01-01&end=2026-02-01",
            headers=auth_headers_user,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Game"
        assert data[0]["game_slug"] == "test-game"
        assert data[0]["type"] == "oneshot"
        assert data[0]["color"] == "#75b798"

    def test_missing_params_returns_400(self, api_client, auth_headers_user):
        """Missing start/end returns 400."""
        response = api_client.get("/api/v1/calendar/events/", headers=auth_headers_user)
        assert response.status_code == 400

    def test_missing_end_returns_400(self, api_client, auth_headers_user):
        """Missing end parameter returns 400."""
        response = api_client.get(
            "/api/v1/calendar/events/?start=2026-01-01", headers=auth_headers_user
        )
        assert response.status_code == 400

    def test_invalid_date_returns_400(self, api_client, auth_headers_user):
        """Invalid date format returns 400."""
        response = api_client.get(
            "/api/v1/calendar/events/?start=not-a-date&end=also-not",
            headers=auth_headers_user,
        )
        assert response.status_code == 400

    @patch("website.api.stats.session_service")
    def test_midnight_crossing_capped(self, mock_service, api_client, auth_headers_user):
        """Sessions crossing midnight have end capped to same day."""
        game = MagicMock()
        game.name = "Late Game"
        game.type = "campaign"
        game.slug = "late-game"

        session = MagicMock()
        session.id = 2
        session.start = datetime(2026, 1, 15, 22, 0)
        session.end = datetime(2026, 1, 16, 2, 0)  # crosses midnight
        session.game = game

        mock_service.find_in_range.return_value = [session]

        response = api_client.get(
            "/api/v1/calendar/events/?start=2026-01-01&end=2026-02-01",
            headers=auth_headers_user,
        )
        data = response.get_json()
        assert data[0]["end"] == "2026-01-15T23:59:59"
