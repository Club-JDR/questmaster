"""Tests for the game API endpoints."""

from unittest.mock import MagicMock, patch

from website.exceptions import NotFoundError


class TestListGames:
    """Tests for GET /api/v1/games/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/games/")
        assert response.status_code == 403

    @patch("website.api.games.game_service")
    def test_returns_paginated_list(self, mock_service, api_client, auth_headers_user):
        """Returns paginated list of games."""
        game = MagicMock()
        game.to_dict.return_value = {"id": 1, "name": "Test Game", "slug": "test-game"}
        mock_service.search.return_value = ([game], 1)

        response = api_client.get("/api/v1/games/", headers=auth_headers_user)
        assert response.status_code == 200

        data = response.get_json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Game"

    @patch("website.api.games.game_service")
    def test_passes_filters_to_service(self, mock_service, api_client, auth_headers_user):
        """Query parameters are passed as filters to the service."""
        mock_service.search.return_value = ([], 0)

        api_client.get(
            "/api/v1/games/?status=open&type=oneshot&name=dragon&system_id=1",
            headers=auth_headers_user,
        )

        call_args = mock_service.search.call_args
        filters = call_args[0][0]
        assert filters["status"] == ["open"]
        assert filters["game_type"] == ["oneshot"]
        assert filters["name"] == "dragon"
        assert filters["system_id"] == 1

    @patch("website.api.games.game_service")
    def test_default_pagination(self, mock_service, api_client, auth_headers_user):
        """Default pagination is page=1, per_page=20."""
        mock_service.search.return_value = ([], 0)

        api_client.get("/api/v1/games/", headers=auth_headers_user)

        call_args = mock_service.search.call_args
        assert call_args[0][1] == 1  # page
        assert call_args[0][2] == 20  # per_page

    @patch("website.api.games.game_service")
    def test_custom_pagination(self, mock_service, api_client, auth_headers_user):
        """Custom page and per_page are forwarded."""
        mock_service.search.return_value = ([], 0)

        api_client.get("/api/v1/games/?page=3&per_page=50", headers=auth_headers_user)

        call_args = mock_service.search.call_args
        assert call_args[0][1] == 3  # page
        assert call_args[0][2] == 50  # per_page

    @patch("website.api.games.game_service")
    def test_user_payload_from_jwt(self, mock_service, api_client, auth_headers_user):
        """User payload is derived from JWT claims."""
        mock_service.search.return_value = ([], 0)

        api_client.get("/api/v1/games/", headers=auth_headers_user)

        call_args = mock_service.search.call_args
        user_payload = call_args[0][3]
        assert "user_id" in user_payload
        assert "is_admin" in user_payload


class TestGetGame:
    """Tests for GET /api/v1/games/<slug>/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/games/some-slug/")
        assert response.status_code == 403

    @patch("website.api.games.game_service")
    def test_returns_game_with_relationships(self, mock_service, api_client, auth_headers_user):
        """Returns full game detail with relationships."""
        game = MagicMock()
        game.to_dict.return_value = {
            "id": 1,
            "name": "Test Game",
            "slug": "test-game",
            "gm": {"id": "123", "name": "GM"},
            "players": [],
            "sessions": [],
        }
        mock_service.get_by_slug.return_value = game

        response = api_client.get("/api/v1/games/test-game/", headers=auth_headers_user)
        assert response.status_code == 200

        data = response.get_json()
        assert data["name"] == "Test Game"
        assert "gm" in data
        game.to_dict.assert_called_once_with(include_relationships=True)

    @patch("website.api.games.game_service")
    def test_not_found(self, mock_service, api_client, auth_headers_user):
        """Returns 404 for non-existent game."""
        mock_service.get_by_slug.side_effect = NotFoundError(
            "Game not found", resource_type="Game", resource_id="bad-slug"
        )
        response = api_client.get("/api/v1/games/bad-slug/", headers=auth_headers_user)
        assert response.status_code == 404


class TestListGameSessions:
    """Tests for GET /api/v1/games/<slug>/sessions/."""

    @patch("website.api.games.game_service")
    def test_returns_sessions(self, mock_service, api_client, auth_headers_user):
        """Returns list of sessions for a game."""
        session = MagicMock()
        session.to_dict.return_value = {
            "id": 1,
            "start": "2026-03-01T18:00:00",
            "end": "2026-03-01T22:00:00",
        }
        game = MagicMock()
        game.sessions = [session]
        mock_service.get_by_slug.return_value = game

        response = api_client.get("/api/v1/games/test-game/sessions/", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["id"] == 1

    @patch("website.api.games.game_service")
    def test_not_found(self, mock_service, api_client, auth_headers_user):
        """Returns 404 for non-existent game."""
        mock_service.get_by_slug.side_effect = NotFoundError(
            "Game not found", resource_type="Game", resource_id="bad-slug"
        )
        response = api_client.get("/api/v1/games/bad-slug/sessions/", headers=auth_headers_user)
        assert response.status_code == 404


class TestListGameEvents:
    """Tests for GET /api/v1/games/<slug>/events/."""

    @patch("website.api.games.game_service")
    def test_returns_events(self, mock_service, api_client, auth_headers_user):
        """Returns audit trail for a game."""
        event = MagicMock()
        event.to_dict.return_value = {
            "id": 1,
            "action": "create",
            "description": "Game created",
        }
        game = MagicMock()
        game.events = [event]
        mock_service.get_by_slug.return_value = game

        response = api_client.get("/api/v1/games/test-game/events/", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["action"] == "create"
