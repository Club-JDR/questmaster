"""Tests for non-game view endpoints (calendar, demo pages, leaderboard).

The demo views serve static fake data and require no authentication.
The calendar view requires a logged-in user.
"""

import html

import pytest

from tests.factories import GameFactory, SpecialEventFactory

pytestmark = pytest.mark.integration


# -- Calendar --------------------------------------------------------------


class TestCalendar:
    """GET /calendrier/ — club calendar page."""

    def test_calendar_renders(self, logged_in_user, mock_discord_lookups, db_session):
        """Authenticated user can access the calendar page."""
        response = logged_in_user.get("/calendrier/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Le Calendrier du Club" in body


# -- Demo Pages ------------------------------------------------------------


class TestDemo:
    """GET /demo/* — static demo pages with fake game data.

    These pages showcase the UI to unauthenticated visitors using
    hard-coded fake games (defined in website/views/demo.py).

    Bodies are unescaped before asserting: templates are autoescaped, so an
    apostrophe reaches the browser as ``&#39;``.
    """

    def test_demo_landing(self, client):
        """Landing demo page lists the two fake games."""
        response = client.get("/demo/")
        body = html.unescape(response.data.decode())
        assert response.status_code == 200
        assert "La Tombe de l'Annihilation" in body
        assert "Le Pensionnaire" in body

    def test_demo_inscription(self, client):
        """Registration demo page shows the sign-up button."""
        response = client.get("/demo/inscription/")
        body = html.unescape(response.data.decode())
        assert response.status_code == 200
        assert "La Tombe de l'Annihilation" in body
        assert "S'inscrire" in body

    def test_demo_post(self, client):
        """Post demo page shows the game creation form."""
        response = client.get("/demo/poster/")
        body = html.unescape(response.data.decode())
        assert response.status_code == 200
        assert "Nouvelle annonce" in body

    def test_demo_manage(self, client):
        """Management demo page shows edit controls on a fake game."""
        response = client.get("/demo/gerer/")
        body = html.unescape(response.data.decode())
        assert response.status_code == 200
        assert "La Tombe de l'Annihilation" in body
        assert "editButton" in body


# -- Trophy Leaderboard ------------------------------------------------------


class TestTrophiesLeaderboard:
    """GET /badges/classement/ — global badge leaderboards + per-event tab."""

    def test_renders_without_event_selected(self, client, mock_discord_lookups, db_session):
        """With no ?event=, the page renders the global leaderboards only."""
        response = client.get("/badges/classement/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Classement des badges" in body
        assert "Sélectionnez un évènement" in body

    def test_renders_event_leaderboard(
        self, client, mock_discord_lookups, db_session, admin_user, regular_user, default_system
    ):
        """Selecting an event shows its player/GM game-count leaderboard."""
        event = SpecialEventFactory(db_session, name="Halloween Test Event")
        game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            special_event_id=event.id,
            status="archived",
            trophies_awarded=True,
        )
        game.players.append(regular_user)
        db_session.flush()

        response = client.get(f"/badges/classement/?event={event.id}")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Halloween Test Event" in body
        assert admin_user.name in body
        assert regular_user.name in body
        assert "Annonces" in body

    def test_unknown_event_flashes_and_falls_back(self, client, mock_discord_lookups, db_session):
        """An unknown event id flashes a warning and falls back to no selection."""
        response = client.get("/badges/classement/?event=999999", follow_redirects=True)
        body = response.data.decode()
        assert response.status_code == 200
        assert "Événement introuvable." in body
