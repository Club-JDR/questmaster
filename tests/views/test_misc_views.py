"""Tests for non-game view endpoints (calendar, demo pages).

The demo views serve static fake data and require no authentication.
The calendar view requires a logged-in user.
"""

import pytest

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
    """

    def test_demo_landing(self, client):
        """Landing demo page lists the two fake games."""
        response = client.get("/demo/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "La Tombe de l'Annihilation" in body
        assert "Le Pensionnaire" in body

    def test_demo_inscription(self, client):
        """Registration demo page shows the sign-up button."""
        response = client.get("/demo/inscription/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "La Tombe de l'Annihilation" in body
        assert "S'inscrire" in body

    def test_demo_post(self, client):
        """Post demo page shows the game creation form."""
        response = client.get("/demo/poster/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Nouvelle annonce" in body

    def test_demo_manage(self, client):
        """Management demo page shows edit controls on a fake game."""
        response = client.get("/demo/gerer/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "La Tombe de l'Annihilation" in body
        assert "editButton" in body
