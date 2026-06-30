"""Tests for the dashboard landing page, its lazy panels, and the browser split.

The dashboard at ``/`` renders fast (open-games preview only); the agenda +
stats panels are lazy-loaded from ``/tableau-de-bord/panneaux/``. ``/annonces/``
keeps the full open-games browser.
"""

from datetime import datetime

from tests.factories import GameFactory, GameSessionFactory


class TestDashboard:
    """GET / — personalised landing dashboard."""

    def test_anonymous_shows_open_games_only(self, client, db_session, admin_user, default_system):
        """Anonymous visitors see the open-games section, no agenda/stats panels."""
        GameFactory(
            db_session,
            name="Anon Visible Game",
            status="open",
            gm_id=admin_user.id,
            system_id=default_system.id,
        )

        response = client.get("/")
        body = response.data.decode()

        assert response.status_code == 200
        assert "Tableau de bord" in body
        assert "Annonces ouvertes" in body
        assert 'id="game-cards-container"' in body  # lazy open-games container
        assert "dashboard-panels" not in body  # no member panels for anonymous

    def test_member_gets_lazy_panels_placeholder(
        self, logged_in_user, mock_discord_lookups, db_session
    ):
        """A logged-in member gets the lazy panels placeholder (not the data itself)."""
        response = logged_in_user.get("/")
        body = response.data.decode()

        assert response.status_code == 200
        assert 'id="dashboard-panels"' in body
        assert "/tableau-de-bord/panneaux/" in body  # data-src for the fragment
        assert "Mes statistiques" not in body  # rendered only in the fragment


class TestDashboardPanels:
    """GET /tableau-de-bord/panneaux/ — lazy agenda + stats fragment."""

    def test_requires_login(self, client):
        """Anonymous users are redirected to login."""
        response = client.get("/tableau-de-bord/panneaux/")
        assert response.status_code in (301, 302)

    def test_renders_agenda_and_stats(
        self,
        logged_in_user,
        mock_discord_lookups,
        db_session,
        regular_user,
        admin_user,
        default_system,
    ):
        """The fragment renders the agenda + stats with the member's session."""
        game = GameFactory(
            db_session,
            name="Agenda Game",
            status="open",
            gm_id=admin_user.id,
            system_id=default_system.id,
        )
        game.players.append(regular_user)
        GameSessionFactory(
            db_session,
            game_id=game.id,
            start=datetime(2030, 1, 4, 20, 0),
            end=datetime(2030, 1, 4, 23, 0),
        )
        db_session.flush()

        response = logged_in_user.get("/tableau-de-bord/panneaux/")
        body = response.data.decode()

        assert response.status_code == 200
        assert "Mon agenda" in body
        assert "Mes statistiques" in body
        assert "Agenda Game" in body


class TestOpenGamesBrowser:
    """GET /annonces/ — full open-games browser stays intact after the split."""

    def test_browser_has_search_bar(self, client, db_session):
        """The open-games page still renders the advanced search bar."""
        response = client.get("/annonces/")
        body = response.data.decode()

        assert response.status_code == 200
        assert 'id="searchBar"' in body


class TestStatsPage:
    """GET /stats/ — public stats page (app-wide overview + monthly detail)."""

    def test_renders_overview_and_monthly_tabs(
        self, client, db_session, admin_user, default_system
    ):
        """The page renders both tabs and the global overview widgets."""
        game = GameFactory(
            db_session,
            status="open",
            type="oneshot",
            gm_id=admin_user.id,
            system_id=default_system.id,
        )
        GameSessionFactory(
            db_session,
            game_id=game.id,
            start=datetime(2025, 6, 10, 20, 0),
            end=datetime(2025, 6, 10, 23, 0),
        )
        db_session.flush()

        response = client.get("/stats/")
        body = response.data.decode()

        assert response.status_code == 200
        # Both tabs are present.
        assert "Vue d'ensemble" in body
        assert "Détail mensuel" in body
        # Global overview widgets render (catches Jinja errors in the partial/pie).
        assert "data-stats-root" in body
        assert "Temps de jeu" in body
        assert "Avertissements" in body
        assert "data-top-type-select" in body
