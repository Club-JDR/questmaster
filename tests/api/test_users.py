"""Tests for the user API endpoints."""

from unittest.mock import MagicMock, patch

from tests.constants import TEST_REGULAR_USER_ID
from website.exceptions import NotFoundError


class TestGetCurrentUser:
    """Tests for GET /api/v1/users/me/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/users/me/")
        assert response.status_code == 403

    @patch("website.api.users.user_service")
    def test_returns_current_user(self, mock_service, api_client, auth_headers_user):
        """Returns the authenticated user's profile."""
        user = MagicMock()
        user.to_dict.return_value = {
            "id": TEST_REGULAR_USER_ID,
            "name": "Test User",
            "username": "testuser",
            "avatar": "/static/img/avatar.webp",
            "is_gm": False,
            "is_admin": False,
            "is_player": True,
        }
        mock_service.get_by_id.return_value = user

        response = api_client.get("/api/v1/users/me/", headers=auth_headers_user)
        assert response.status_code == 200

        data = response.get_json()
        assert data["id"] == TEST_REGULAR_USER_ID
        assert data["name"] == "Test User"
        mock_service.get_by_id.assert_called_once_with(TEST_REGULAR_USER_ID)


class TestGetUser:
    """Tests for GET /api/v1/users/<user_id>/."""

    @patch("website.api.users.user_service")
    def test_returns_user(self, mock_service, api_client, auth_headers_user):
        """Returns a user by ID."""
        user = MagicMock()
        user.to_dict.return_value = {
            "id": "123456789012345678",
            "name": "Some User",
            "username": "someuser",
        }
        mock_service.get_by_id.return_value = user

        response = api_client.get("/api/v1/users/123456789012345678/", headers=auth_headers_user)
        assert response.status_code == 200
        assert response.get_json()["name"] == "Some User"
        mock_service.get_by_id.assert_called_once_with("123456789012345678")

    @patch("website.api.users.user_service")
    def test_not_found(self, mock_service, api_client, auth_headers_user):
        """Returns 404 for non-existent user."""
        mock_service.get_by_id.side_effect = NotFoundError(
            "User not found", resource_type="User", resource_id="999"
        )
        response = api_client.get("/api/v1/users/999/", headers=auth_headers_user)
        assert response.status_code == 404


class TestGetUserBadges:
    """Tests for GET /api/v1/users/<user_id>/badges/."""

    @patch("website.api.users.trophy_service")
    @patch("website.api.users.user_service")
    def test_returns_badges(
        self, mock_user_service, mock_trophy_service, api_client, auth_headers_user
    ):
        """Returns list of badges for a user."""
        mock_user_service.get_by_id.return_value = MagicMock()
        mock_trophy_service.get_user_badges.return_value = [
            {"name": "One-shot Player", "icon": "os.png", "quantity": 5},
            {"name": "Campaign Player", "icon": "camp.png", "quantity": 3},
        ]

        response = api_client.get(
            "/api/v1/users/123456789012345678/badges/", headers=auth_headers_user
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert data[0]["name"] == "One-shot Player"
        assert data[0]["quantity"] == 5

    @patch("website.api.users.user_service")
    def test_user_not_found(self, mock_service, api_client, auth_headers_user):
        """Returns 404 when user does not exist."""
        mock_service.get_by_id.side_effect = NotFoundError(
            "User not found", resource_type="User", resource_id="999"
        )
        response = api_client.get("/api/v1/users/999/badges/", headers=auth_headers_user)
        assert response.status_code == 404
