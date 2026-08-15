"""Tests for public system pages (details + lightweight matchmaking)."""

import html

from tests.factories import GameFactory, SystemFactory, UserFactory


class TestListSystems:
    """GET /systemes/ — index of all systems, linking to each system page."""

    def test_lists_systems_with_links(self, client, db_session):
        system = SystemFactory(db_session, name="Linked Test System")

        response = client.get("/systemes/")

        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Linked Test System" in body
        assert f"/systemes/{system.id}/" in body


class TestGetSystem:
    """GET /systemes/<id>/ — a system's public page."""

    def test_not_found(self, client, db_session):
        response = client.get("/systemes/999999/")
        assert response.status_code == 404

    def test_renders_description(self, client, db_session):
        system = SystemFactory(db_session, description="Un jeu de test **fantastique**.")
        response = client.get(f"/systemes/{system.id}/")
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "fantastique" in body

    def test_renders_reference_url_as_external_link(self, client, db_session):
        system = SystemFactory(
            db_session, description=None, reference_url="https://legrog.org/jeux/test"
        )
        response = client.get(f"/systemes/{system.id}/")
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert 'href="https://legrog.org/jeux/test"' in body
        assert 'target="_blank"' in body

    def test_lists_gm_history(self, client, db_session):
        system = SystemFactory(db_session)
        gm = UserFactory(db_session, name="History GM")
        GameFactory(db_session, system_id=system.id, gm_id=gm.id, status="open")

        response = client.get(f"/systemes/{system.id}/")

        assert "History GM" in response.get_data(as_text=True)

    def test_anonymous_sees_login_prompt_instead_of_toggle(self, client, db_session):
        system = SystemFactory(db_session)
        response = client.get(f"/systemes/{system.id}/")
        body = response.get_data(as_text=True)
        assert "Connectez-vous" in body

    def test_logged_in_user_sees_player_toggle(
        self, logged_in_user, mock_discord_lookups, db_session
    ):
        system = SystemFactory(db_session)
        response = logged_in_user.get(f"/systemes/{system.id}/")
        body = response.get_data(as_text=True)
        assert "Je veux jouer à ce système" in body

    def test_only_gm_sees_gm_toggle(self, logged_in_user, mock_discord_lookups, db_session):
        system = SystemFactory(db_session)
        response = logged_in_user.get(f"/systemes/{system.id}/")
        body = response.get_data(as_text=True)
        assert "faire tourner ce système" not in body

    def test_gm_sees_gm_toggle(self, logged_in_gm, mock_discord_lookups, db_session):
        system = SystemFactory(db_session)
        response = logged_in_gm.get(f"/systemes/{system.id}/")
        body = response.get_data(as_text=True)
        assert "faire tourner ce système" in body


class TestToggleInterest:
    """POST /systemes/<id>/interet/ — self-service interest toggle."""

    def test_requires_login(self, client, mock_csrf, db_session):
        system = SystemFactory(db_session)
        response = client.post(f"/systemes/{system.id}/interet/", data={"role": "player"})
        assert response.status_code in (302, 303)

    def test_player_can_toggle_player_interest(
        self, logged_in_user, mock_csrf, mock_discord_lookups, db_session
    ):
        system = SystemFactory(db_session)

        add_response = logged_in_user.post(
            f"/systemes/{system.id}/interet/", data={"role": "player"}, follow_redirects=True
        )
        assert "Intérêt enregistré." in add_response.get_data(as_text=True)

        remove_response = logged_in_user.post(
            f"/systemes/{system.id}/interet/", data={"role": "player"}, follow_redirects=True
        )
        assert "Intérêt retiré." in remove_response.get_data(as_text=True)

    def test_non_gm_cannot_toggle_gm_interest(
        self, logged_in_user, mock_csrf, mock_discord_lookups, db_session
    ):
        system = SystemFactory(db_session)
        response = logged_in_user.post(f"/systemes/{system.id}/interet/", data={"role": "gm"})
        assert response.status_code == 403

    def test_gm_can_toggle_gm_interest(
        self, logged_in_gm, mock_csrf, mock_discord_lookups, db_session
    ):
        system = SystemFactory(db_session)
        response = logged_in_gm.post(
            f"/systemes/{system.id}/interet/", data={"role": "gm"}, follow_redirects=True
        )
        assert "Intérêt enregistré." in response.get_data(as_text=True)

    def test_invalid_role_flashes_error(
        self, logged_in_user, mock_csrf, mock_discord_lookups, db_session
    ):
        system = SystemFactory(db_session)
        response = logged_in_user.post(
            f"/systemes/{system.id}/interet/", data={"role": "spectator"}, follow_redirects=True
        )
        body = html.unescape(response.get_data(as_text=True))
        assert "Rôle d'intérêt invalide." in body
