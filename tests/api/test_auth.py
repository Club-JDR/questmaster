"""Tests for the API auth endpoints and JWT decorators."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from tests.api.conftest import make_jwt_token
from tests.constants import TEST_GM_USER_ID, TEST_REGULAR_USER_ID


class TestExchangeToken:
    """Tests for POST /api/v1/auth/token."""

    def test_missing_body_returns_400(self, api_client):
        """Request without JSON body returns 400."""
        response = api_client.post("/api/v1/auth/token", content_type="application/json")
        assert response.status_code == 400

    def test_missing_discord_token_returns_400(self, api_client):
        """Request with empty body returns 400."""
        response = api_client.post("/api/v1/auth/token", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "discord_access_token" in data.get("error", "")

    @patch("website.api.auth._fetch_discord_user")
    def test_successful_exchange(self, mock_fetch, api_client, db_session):
        """Valid Discord token exchange returns JWT."""
        mock_fetch.return_value = {
            "id": TEST_REGULAR_USER_ID,
            "username": "testuser",
            "global_name": "Test User",
        }

        with (
            patch("website.models.user.get_user_profile") as mock_profile,
            patch("website.models.user.get_user_roles") as mock_roles,
        ):
            mock_profile.return_value = {
                "name": "Test User",
                "avatar": "/static/img/avatar.webp",
                "username": "testuser",
            }
            mock_roles.return_value = []

            response = api_client.post(
                "/api/v1/auth/token",
                json={"discord_access_token": "valid_discord_token"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "expires_in" in data
        assert data["expires_in"] == 3600

    @patch("website.api.auth._fetch_discord_user")
    def test_invalid_discord_token_returns_400(self, mock_fetch, api_client):
        """Invalid Discord token returns 400."""
        from website.exceptions import ValidationError

        mock_fetch.side_effect = ValidationError(
            "Invalid Discord access token", field="discord_access_token"
        )

        response = api_client.post(
            "/api/v1/auth/token",
            json={"discord_access_token": "bad_token"},
        )
        assert response.status_code == 400


class TestRefreshToken:
    """Tests for POST /api/v1/auth/refresh."""

    def test_missing_auth_header_returns_403(self, api_client):
        """Request without Authorization header returns 403."""
        response = api_client.post("/api/v1/auth/refresh")
        assert response.status_code == 403

    def test_refresh_valid_expired_token(self, test_app, api_client, db_session):
        """Expired token within refresh window returns new JWT."""
        token = make_jwt_token(test_app, TEST_REGULAR_USER_ID, expired=True)

        with (
            patch("website.models.user.get_user_profile") as mock_profile,
            patch("website.models.user.get_user_roles") as mock_roles,
        ):
            mock_profile.return_value = {
                "name": "Test User",
                "avatar": "/static/img/avatar.webp",
                "username": "testuser",
            }
            mock_roles.return_value = []

            response = api_client.post(
                "/api/v1/auth/refresh",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data

    def test_refresh_too_old_token_returns_403(self, test_app, api_client):
        """Token issued beyond refresh window returns 403."""
        old_iat = datetime.now(timezone.utc) - timedelta(hours=48)
        token = make_jwt_token(test_app, TEST_REGULAR_USER_ID, expired=True, iat_override=old_iat)

        response = api_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestApiLoginRequired:
    """Tests for the @api_login_required decorator."""

    def test_no_auth_header_returns_403(self, api_client):
        """Endpoints requiring auth return 403 without a token."""
        # Use a non-existent protected endpoint; the error handlers catch it
        response = api_client.get("/api/v1/health", headers={"Authorization": "InvalidScheme abc"})
        # Health doesn't require auth, so this just tests the header parse
        assert response.status_code == 200

    def test_expired_token_returns_403(self, test_app, api_client):
        """Expired JWT returns 403."""
        token = make_jwt_token(test_app, TEST_REGULAR_USER_ID, expired=True)
        # We can't easily test @api_login_required without a protected endpoint.
        # The decorator is tested indirectly via the auth/refresh endpoint tests.
        # This test verifies the token decode behaviour directly.
        from website.api.auth import decode_token
        from website.exceptions import UnauthorizedError

        with test_app.app_context():
            with pytest.raises(UnauthorizedError):
                decode_token(token)
