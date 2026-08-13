"""Tests for the user preferences views (game-form defaults)."""

import pytest

from tests.factories import SystemFactory

pytestmark = pytest.mark.integration


class TestPreferencesAccess:
    """GET /preferences/ — view saved game-form default preferences (GM-only)."""

    def test_requires_login(self, client, db_session):
        response = client.get("/preferences/")
        assert response.status_code in (302, 401, 403)

    def test_non_gm_cannot_access(self, logged_in_user, mock_discord_lookups, db_session):
        response = logged_in_user.get("/preferences/")
        assert response.status_code == 403

    def test_gm_can_access(self, logged_in_gm, mock_discord_lookups, db_session):
        response = logged_in_gm.get("/preferences/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Mes préférences" in body

    def test_saved_default_prefills_field(
        self, logged_in_gm, mock_discord_lookups, db_session, gm_user
    ):
        gm_user.game_defaults = {"description": "My canvas text"}
        db_session.flush()
        response = logged_in_gm.get("/preferences/")
        body = response.data.decode()
        assert "My canvas text" in body

    def test_saved_default_is_escaped(
        self, logged_in_gm, mock_discord_lookups, db_session, gm_user
    ):
        """A saved default is validated for shape only, so it must be escaped."""
        gm_user.game_defaults = {"description": "</textarea><script>alert('xss')</script>"}
        db_session.flush()
        response = logged_in_gm.get("/preferences/")
        body = response.data.decode()
        assert "</textarea><script>" not in body
        assert "&lt;/textarea&gt;" in body


class TestUpdatePreferences:
    """POST /preferences/ — save game-form default preferences (GM-only)."""

    def test_non_gm_cannot_update(
        self, logged_in_user, mock_csrf, mock_discord_lookups, db_session
    ):
        response = logged_in_user.post(
            "/preferences/", data={"csrf_token": "test", "description": "x"}
        )
        assert response.status_code == 403

    def test_saves_whitelisted_fields(
        self, logged_in_gm, mock_csrf, mock_discord_lookups, db_session, gm_user
    ):
        response = logged_in_gm.post(
            "/preferences/",
            data={
                "csrf_token": "test",
                "description": "A reusable canvas",
                "complement": "Always mention safety tools",
                "xp": "beginners",
                "characters": "self",
                "party_size": "5",
                "session_length": "3",
                "chill": "on",
                "comic": "on",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        db_session.refresh(gm_user)
        assert gm_user.game_defaults == {
            "description": "A reusable canvas",
            "complement": "Always mention safety tools",
            "xp": "beginners",
            "characters": "self",
            "party_size": 5,
            "session_length": 3.0,
            "ambience": ["chill", "comic"],
        }

    def test_ignores_non_whitelisted_fields(
        self, logged_in_gm, mock_csrf, mock_discord_lookups, db_session, gm_user
    ):
        logged_in_gm.post(
            "/preferences/",
            data={"csrf_token": "test", "restriction": "18+", "img": "https://evil.example/x"},
            follow_redirects=True,
        )
        db_session.refresh(gm_user)
        assert gm_user.game_defaults == {}

    def test_clears_previous_value_when_submitted_blank(
        self, logged_in_gm, mock_csrf, mock_discord_lookups, db_session, gm_user
    ):
        gm_user.game_defaults = {"description": "Old canvas"}
        db_session.flush()

        logged_in_gm.post(
            "/preferences/",
            data={"csrf_token": "test", "description": ""},
            follow_redirects=True,
        )

        db_session.refresh(gm_user)
        assert gm_user.game_defaults == {}

    def test_valid_system_default_is_saved(
        self, logged_in_gm, mock_csrf, mock_discord_lookups, db_session, gm_user
    ):
        system = SystemFactory(db_session)

        logged_in_gm.post(
            "/preferences/",
            data={"csrf_token": "test", "system": str(system.id)},
            follow_redirects=True,
        )

        db_session.refresh(gm_user)
        assert gm_user.game_defaults == {"system": system.id}
