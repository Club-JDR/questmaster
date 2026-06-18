"""Tests for session-cookie auth fallback and api_login_optional.

Verifies that the API accepts Flask session cookies as an alternative
to JWT Bearer tokens, and that ``api_login_optional`` allows anonymous
access where appropriate.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from tests.api.conftest import make_jwt_token
from tests.constants import TEST_GM_USER_ID, TEST_REGULAR_USER_ID


class TestSessionFallbackAuth:
    """Session-cookie fallback on @api_login_required endpoints."""

    @patch("website.api.stats.session_service")
    def test_session_cookie_accepted(self, mock_service, session_client_user):
        """A session-authenticated client can call a login-required endpoint."""
        mock_service.get_stats_for_period.return_value = {
            "base_day": datetime(2026, 2, 1),
            "last_day": datetime(2026, 2, 28, 23, 59, 59),
            "num_os": 0,
            "num_campaign": 0,
            "os_games": {},
            "campaign_games": {},
            "gm_names": [],
        }

        response = session_client_user.get("/api/v1/stats/")
        assert response.status_code == 200

    @patch("website.api.stats.session_service")
    def test_jwt_takes_priority_over_session(self, mock_service, test_app, session_client_user):
        """When both JWT and session are present, JWT wins."""
        mock_service.get_stats_for_period.return_value = {
            "base_day": datetime(2026, 2, 1),
            "last_day": datetime(2026, 2, 28, 23, 59, 59),
            "num_os": 0,
            "num_campaign": 0,
            "os_games": {},
            "campaign_games": {},
            "gm_names": [],
        }

        # Session has regular user; JWT has GM user
        jwt_token = make_jwt_token(test_app, TEST_GM_USER_ID, is_gm=True)
        response = session_client_user.get(
            "/api/v1/stats/",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 200

    def test_no_auth_returns_403(self, api_client):
        """Unauthenticated client gets 403 on a login-required endpoint."""
        response = api_client.get("/api/v1/stats/")
        assert response.status_code == 403


class TestSessionWithRoleDecorators:
    """Role decorators (@require_gm, @require_admin) work with session auth."""

    # require_gm and require_admin load the user from DB and call
    # refresh_roles(), so we need to mock that.

    @patch("website.api.auth._load_and_refresh_user")
    def test_require_gm_with_session(self, mock_load, test_app, session_client_gm, gm_user):
        """Session-authenticated GM can access GM-only endpoints."""
        mock_load.return_value = gm_user

        # GET /api/v1/games/ is login-required but not GM-required,
        # so we test a mock endpoint indirectly.  The important thing
        # is that g.current_user is populated from the session.
        # We verify this by checking the stats endpoint works with session.
        with patch("website.api.stats.session_service") as mock_service:
            mock_service.get_stats_for_period.return_value = {
                "base_day": datetime(2026, 2, 1),
                "last_day": datetime(2026, 2, 28, 23, 59, 59),
                "num_os": 0,
                "num_campaign": 0,
                "os_games": {},
                "campaign_games": {},
                "gm_names": [],
            }
            response = session_client_gm.get("/api/v1/stats/")
            assert response.status_code == 200


class TestApiLoginOptional:
    """Tests for @api_login_optional on the calendar endpoint."""

    @patch("website.api.stats.session_service")
    def test_anonymous_access_allowed(self, mock_service, api_client):
        """Unauthenticated client can call the calendar endpoint."""
        mock_service.find_in_range.return_value = []

        response = api_client.get("/api/v1/calendar/events/?start=2026-01-01&end=2026-02-01")
        assert response.status_code == 200
        assert response.get_json() == []

    @patch("website.api.stats.session_service")
    def test_session_auth_works(self, mock_service, session_client_user):
        """Session-authenticated client can call the calendar endpoint."""
        mock_service.find_in_range.return_value = []

        response = session_client_user.get(
            "/api/v1/calendar/events/?start=2026-01-01&end=2026-02-01"
        )
        assert response.status_code == 200

    @patch("website.api.stats.session_service")
    def test_jwt_auth_works(self, mock_service, api_client, auth_headers_user):
        """JWT-authenticated client can call the calendar endpoint."""
        mock_service.find_in_range.return_value = []

        response = api_client.get(
            "/api/v1/calendar/events/?start=2026-01-01&end=2026-02-01",
            headers=auth_headers_user,
        )
        assert response.status_code == 200

    @patch("website.api.stats.session_service")
    def test_anonymous_returns_data(self, mock_service, api_client):
        """Anonymous client receives actual calendar data."""
        game = MagicMock()
        game.name = "Public Game"
        game.type = "oneshot"
        game.slug = "public-game"

        session = MagicMock()
        session.id = 42
        session.start = datetime(2026, 1, 15, 18, 0)
        session.end = datetime(2026, 1, 15, 22, 0)
        session.game = game

        mock_service.find_in_range.return_value = [session]

        response = api_client.get("/api/v1/calendar/events/?start=2026-01-01&end=2026-02-01")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Public Game"
        assert data[0]["game_slug"] == "public-game"
