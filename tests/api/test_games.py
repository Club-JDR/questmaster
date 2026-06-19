"""Tests for the game API endpoints."""

from unittest.mock import MagicMock, patch

from website.exceptions import NotFoundError

VALID_GAME_PAYLOAD = {
    "name": "Test Game",
    "type": "oneshot",
    "system_id": 1,
    "description": "A thrilling adventure.",
    "restriction": "all",
    "party_size": 4,
    "xp": "all",
    "date": "2026-07-01T20:00:00",
    "length": "1 session",
    "session_length": 3.5,
    "characters": "with_gm",
}

# Mimics Game.to_dict() output for an existing game (used for PATCH merges).
FULL_GAME_DICT = {
    "id": 1,
    "slug": "existing-game",
    "status": "draft",
    "name": "Existing Game",
    "type": "oneshot",
    "special_event_id": None,
    "system_id": 1,
    "vtt_id": None,
    "description": "desc",
    "restriction": "all",
    "restriction_tags": None,
    "party_size": 4,
    "party_selection": False,
    "xp": "all",
    "date": "2026-07-01T20:00:00",
    "length": "1 session",
    "session_length": 3.0,
    "frequency": None,
    "characters": "with_gm",
    "classification": {},
    "ambience": [],
    "complement": None,
    "img": None,
}


def _mock_user(user_id="gm-123", *, is_gm=True, is_admin=False):
    """Build a mock authenticated user with the given roles."""
    user = MagicMock()
    user.id = user_id
    user.is_gm = is_gm
    user.is_admin = is_admin
    return user


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


class TestCreateGame:
    """Tests for POST /api/v1/games/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.post("/api/v1/games/", json=VALID_GAME_PAYLOAD)
        assert response.status_code == 403

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_requires_gm_or_admin(
        self, mock_service, mock_load_user, api_client, auth_headers_user
    ):
        """A plain player cannot create a game."""
        mock_load_user.return_value = _mock_user(is_gm=False, is_admin=False)

        response = api_client.post(
            "/api/v1/games/", json=VALID_GAME_PAYLOAD, headers=auth_headers_user
        )
        assert response.status_code == 403
        mock_service.create.assert_not_called()

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_creates_game_as_draft(
        self, mock_service, mock_load_user, api_client, auth_headers_gm
    ):
        """A GM creates a game; the service is called with their id."""
        mock_load_user.return_value = _mock_user(user_id="gm-123", is_gm=True)
        created = MagicMock()
        created.to_dict.return_value = {"id": 1, "slug": "test-game", "name": "Test Game"}
        mock_service.create.return_value = created

        response = api_client.post(
            "/api/v1/games/", json=VALID_GAME_PAYLOAD, headers=auth_headers_gm
        )
        assert response.status_code == 201
        assert response.get_json()["slug"] == "test-game"

        service_data, gm_id = mock_service.create.call_args[0]
        assert gm_id == "gm-123"
        assert service_data["name"] == "Test Game"
        assert service_data["type"] == "oneshot"
        assert service_data["system"] == 1
        created.to_dict.assert_called_once_with(include_relationships=True)

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_special_event_type_mapping(
        self, mock_service, mock_load_user, api_client, auth_headers_gm
    ):
        """special_event_id is encoded into the service 'type' field."""
        mock_load_user.return_value = _mock_user(is_gm=True)
        mock_service.create.return_value = MagicMock(to_dict=MagicMock(return_value={"id": 1}))

        payload = {**VALID_GAME_PAYLOAD, "special_event_id": 7}
        response = api_client.post("/api/v1/games/", json=payload, headers=auth_headers_gm)
        assert response.status_code == 201

        service_data = mock_service.create.call_args[0][0]
        assert service_data["type"] == "specialevent-7"

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_classification_and_ambience_mapping(
        self, mock_service, mock_load_user, api_client, auth_headers_gm
    ):
        """Nested classification/ambience map to form-shaped keys."""
        mock_load_user.return_value = _mock_user(is_gm=True)
        mock_service.create.return_value = MagicMock(to_dict=MagicMock(return_value={"id": 1}))

        payload = {
            **VALID_GAME_PAYLOAD,
            "classification": {"action": 2, "horror": 1},
            "ambience": ["chill", "epic"],
            "party_selection": True,
        }
        response = api_client.post("/api/v1/games/", json=payload, headers=auth_headers_gm)
        assert response.status_code == 201

        service_data = mock_service.create.call_args[0][0]
        assert service_data["class-action"] == 2
        assert service_data["class-horror"] == 1
        assert service_data["chill"] is True
        assert service_data["epic"] is True
        assert service_data["party_selection"] is True

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_missing_required_field(
        self, mock_service, mock_load_user, api_client, auth_headers_gm
    ):
        """A missing required field yields a 400 validation error."""
        mock_load_user.return_value = _mock_user(is_gm=True)

        payload = {k: v for k, v in VALID_GAME_PAYLOAD.items() if k != "name"}
        response = api_client.post("/api/v1/games/", json=payload, headers=auth_headers_gm)
        assert response.status_code == 400
        mock_service.create.assert_not_called()

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_invalid_enum_value(self, mock_service, mock_load_user, api_client, auth_headers_gm):
        """An out-of-range enum value yields a 400 validation error."""
        mock_load_user.return_value = _mock_user(is_gm=True)

        payload = {**VALID_GAME_PAYLOAD, "restriction": "21+"}
        response = api_client.post("/api/v1/games/", json=payload, headers=auth_headers_gm)
        assert response.status_code == 400
        mock_service.create.assert_not_called()


class TestUpdateGame:
    """Tests for PATCH /api/v1/games/<slug>/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.patch("/api/v1/games/test-game/", json={"name": "X"})
        assert response.status_code == 403

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_owner_can_update(self, mock_service, mock_load_user, api_client, auth_headers_gm):
        """The game's GM can update it; omitted fields are merged from current."""
        mock_load_user.return_value = _mock_user(user_id="gm-123", is_gm=True)
        game = MagicMock()
        game.gm_id = "gm-123"
        game.to_dict.return_value = dict(FULL_GAME_DICT)
        mock_service.get_by_slug.return_value = game
        updated = MagicMock()
        updated.to_dict.return_value = {"id": 1, "name": "New Name"}
        mock_service.update.return_value = updated

        response = api_client.patch(
            "/api/v1/games/existing-game/", json={"name": "New Name"}, headers=auth_headers_gm
        )
        assert response.status_code == 200
        assert response.get_json()["name"] == "New Name"

        slug, service_data = mock_service.update.call_args[0]
        assert slug == "existing-game"
        assert service_data["name"] == "New Name"
        # merged from existing
        assert service_data["description"] == "desc"

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_non_owner_forbidden(
        self, mock_service, mock_load_user, api_client, auth_headers_user
    ):
        """A non-owner, non-admin cannot update the game."""
        mock_load_user.return_value = _mock_user(user_id="someone-else", is_gm=True)
        game = MagicMock()
        game.gm_id = "gm-123"
        mock_service.get_by_slug.return_value = game

        response = api_client.patch(
            "/api/v1/games/existing-game/", json={"name": "X"}, headers=auth_headers_user
        )
        assert response.status_code == 403
        mock_service.update.assert_not_called()

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_admin_can_update_any(
        self, mock_service, mock_load_user, api_client, auth_headers_admin
    ):
        """An admin can update a game they do not own."""
        mock_load_user.return_value = _mock_user(user_id="admin-1", is_gm=False, is_admin=True)
        game = MagicMock()
        game.gm_id = "gm-123"
        game.to_dict.return_value = dict(FULL_GAME_DICT)
        mock_service.get_by_slug.return_value = game
        mock_service.update.return_value = MagicMock(to_dict=MagicMock(return_value={"id": 1}))

        response = api_client.patch(
            "/api/v1/games/existing-game/", json={"party_size": 6}, headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert mock_service.update.call_args[0][1]["party_size"] == 6

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_not_found(self, mock_service, mock_load_user, api_client, auth_headers_gm):
        """Returns 404 when the game does not exist."""
        mock_load_user.return_value = _mock_user(is_gm=True)
        mock_service.get_by_slug.side_effect = NotFoundError(
            "Game not found", resource_type="Game", resource_id="bad-slug"
        )

        response = api_client.patch(
            "/api/v1/games/bad-slug/", json={"name": "X"}, headers=auth_headers_gm
        )
        assert response.status_code == 404


class TestDeleteGame:
    """Tests for DELETE /api/v1/games/<slug>/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.delete("/api/v1/games/test-game/")
        assert response.status_code == 403

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_owner_can_delete(self, mock_service, mock_load_user, api_client, auth_headers_gm):
        """The game's GM can delete it; 204 with no body."""
        mock_load_user.return_value = _mock_user(user_id="gm-123", is_gm=True)
        game = MagicMock()
        game.gm_id = "gm-123"
        mock_service.get_by_slug.return_value = game

        response = api_client.delete("/api/v1/games/existing-game/", headers=auth_headers_gm)
        assert response.status_code == 204
        assert response.data == b""
        mock_service.delete.assert_called_once_with("existing-game")

    @patch("website.api.games.load_current_user")
    @patch("website.api.games.game_service")
    def test_non_owner_forbidden(
        self, mock_service, mock_load_user, api_client, auth_headers_user
    ):
        """A non-owner, non-admin cannot delete the game."""
        mock_load_user.return_value = _mock_user(user_id="someone-else", is_gm=True)
        game = MagicMock()
        game.gm_id = "gm-123"
        mock_service.get_by_slug.return_value = game

        response = api_client.delete("/api/v1/games/existing-game/", headers=auth_headers_user)
        assert response.status_code == 403
        mock_service.delete.assert_not_called()
