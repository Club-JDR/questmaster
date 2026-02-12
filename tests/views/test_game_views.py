"""Focused tests for game view endpoints.

Each test exercises a single action with mocked Discord and factory data.
For end-to-end scenarios with real Discord, see test_e2e.py.
"""

import pytest

from tests.constants import TEST_ADMIN_USER_ID, TEST_GM_USER_ID
from tests.factories import GameFactory, GameSessionFactory


pytestmark = pytest.mark.integration


def _game_form_data(system_id, vtt_id, **overrides):
    """Build form data dict for game creation/edit POST."""
    data = {
        "name": "Test Game",
        "type": "oneshot",
        "length": "1 session",
        "gm_id": TEST_ADMIN_USER_ID,
        "system": str(system_id),
        "vtt": str(vtt_id),
        "description": "A test game description.",
        "restriction": "all",
        "restriction_tags": "[]",
        "party_size": "4",
        "xp": "all",
        "frequency": "",
        "characters": "self",
        "complement": "",
        "serious": "on",
        "class-action": "2",
        "class-investigation": "2",
        "class-interaction": "1",
        "class-horror": "1",
        "img": "",
        "action": "draft",
        "date": "2025-07-01 20:30",
        "session_length": "3.5",
    }
    data.update(overrides)
    return data


# -- Game Creation ---------------------------------------------------------


class TestGameCreation:
    """POST /annonce/ — create a new game."""

    def test_create_draft_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(default_system.id, default_vtt.id, action="draft")
        response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
        body = response.data.decode()
        assert response.status_code == 200
        assert "Brouillon" in body

    def test_create_and_publish_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(default_system.id, default_vtt.id, action="open")
        response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
        assert response.status_code == 200
        mock_discord_service.create_role.assert_called_once()
        mock_discord_service.create_channel.assert_called_once()

    def test_gm_can_create_game(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(
            default_system.id, default_vtt.id, gm_id=TEST_GM_USER_ID, action="draft"
        )
        response = logged_in_gm.post("/annonce/", data=data, follow_redirects=True)
        body = response.data.decode()
        assert response.status_code == 200
        assert "Brouillon" in body

    def test_non_gm_cannot_create_game(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        db_session,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(default_system.id, default_vtt.id)
        response = logged_in_user.post("/annonce/", data=data, follow_redirects=True)
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous devez être MJ pour poster une annonce." in body

    def test_create_special_event_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(
            default_system.id, default_vtt.id, type="specialevent-1000", action="draft"
        )
        response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
        body = response.data.decode()
        assert response.status_code == 200
        assert "CthulhuFest" in body


# -- Game Details ----------------------------------------------------------


class TestGameDetails:
    """GET /annonces/<slug>/ — view game detail page."""

    def test_anonymous_can_view(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        response = client.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_gm_sees_action_buttons(
        self, logged_in_admin, mock_discord_lookups, db_session, open_game
    ):
        response = logged_in_admin.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "editButton" in body
        assert "statusButton" in body

    def test_player_sees_register_button(
        self, logged_in_user, mock_discord_lookups, db_session, open_game
    ):
        response = logged_in_user.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "S'inscrire" in body

    def test_non_owner_gm_cannot_see_actions(
        self, logged_in_gm, mock_discord_lookups, db_session, open_game
    ):
        """GM user who is NOT the game's GM should not see edit/status buttons."""
        response = logged_in_gm.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "editButton" not in body
        assert "statusButton" not in body


# -- Game Status -----------------------------------------------------------


class TestGameStatus:
    """POST /annonces/<slug>/statut/ — change game status."""

    def test_close_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/statut/",
            data={"status": "closed"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Complet" in body
        assert f"Annonce {open_game.name} fermée." in body

    def test_reopen_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        closed_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{closed_game.slug}/statut/",
            data={"status": "open"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert f"Annonce {closed_game.name} ouverte." in body

    def test_archive_game_with_trophies(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/statut/",
            data={"status": "archived", "award_trophies": "on"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Archivée" in body
        assert "Badges distribués." in body

    def test_archive_game_without_trophies(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/statut/",
            data={"status": "archived"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Archivée" in body
        assert "Badges non-distribués." in body

    def test_delete_draft_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        draft_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{draft_game.slug}/statut/",
            data={"status": "deleted"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Annonce supprimée avec succès." in body

    def test_publish_draft_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        draft_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{draft_game.slug}/statut/",
            data={"status": "publish"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Annonce publiée avec succès." in body

    def test_gm_can_close_own_game(
        self,
        logged_in_gm,
        gm_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        """A GM (non-admin) can change the status of their own game."""
        game = GameFactory(
            db_session,
            status="open",
            gm_id=gm_user.id,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        response = logged_in_gm.post(
            f"/annonces/{game.slug}/statut/",
            data={"status": "closed"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert f"Annonce {game.name} fermée." in body

    def test_gm_cannot_close_others_game(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A GM (non-admin) cannot change the status of another GM's game."""
        response = logged_in_gm.post(
            f"/annonces/{open_game.slug}/statut/",
            data={"status": "closed"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Seul·e le·a MJ de l'annonce peut faire cette opération." in body


# -- Game Edit -------------------------------------------------------------


class TestGameEdit:
    """GET/POST /annonces/<slug>/editer/ — edit game."""

    def test_get_edit_form(
        self, logged_in_admin, mock_discord_lookups, db_session, draft_game
    ):
        response = logged_in_admin.get(f"/annonces/{draft_game.slug}/editer/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous êtes en train de modifier une annonce." in body

    def test_get_clone_form(
        self, logged_in_admin, mock_discord_lookups, db_session, open_game
    ):
        response = logged_in_admin.get(f"/annonces/{open_game.slug}/cloner/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous êtes en train de cloner une annonce." in body

    def test_edit_draft_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        draft_game,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name=draft_game.name,
            complement="New complement text",
        )
        response = logged_in_admin.post(
            f"/annonces/{draft_game.slug}/editer/",
            data=data,
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Annonce modifiée." in body
        assert "New complement text" in body

    def test_edit_and_publish_draft(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        draft_game,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name=draft_game.name,
            action="open-silent",
        )
        response = logged_in_admin.post(
            f"/annonces/{draft_game.slug}/editer/",
            data=data,
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Annonce modifiée et ouverte." in body


# -- Player Registration --------------------------------------------------


class TestPlayerRegistration:
    """POST /annonces/<slug>/inscription/ — player self-registration."""

    def test_player_registers(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_user.post(
            f"/annonces/{open_game.slug}/inscription/",
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous êtes inscrit·e." in body

    def test_gm_cannot_register_own_game(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/inscription/",
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous ne pouvez pas vous inscrire à votre propre partie." in body

    def test_cannot_register_closed_game(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        closed_game,
    ):
        # Commit to release the savepoint so the service-level rollback
        # (on GameClosedError) cannot undo the factory-created game.
        db_session.commit()
        response = logged_in_user.post(
            f"/annonces/{closed_game.slug}/inscription/",
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "La partie est fermée aux inscriptions." in body

    def test_registration_auto_closes_full_game(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        game = GameFactory(
            db_session,
            status="open",
            party_size=1,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        response = logged_in_user.post(
            f"/annonces/{game.slug}/inscription/",
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous êtes inscrit·e." in body
        assert "Complet" in body


# -- GM Player Management -------------------------------------------------


class TestGMPlayerManagement:
    """POST /annonces/<slug>/gerer/ — GM adds/removes players."""

    def test_gm_adds_player(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        regular_user,
    ):
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/gerer/",
            data={"action": "add", "discord_id": regular_user.id},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Liste des joueur·euses mise à jour." in body

    def test_gm_removes_all_players(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        regular_user,
    ):
        open_game.players.append(regular_user)
        db_session.flush()

        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/gerer/",
            data={"action": "manage"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert body.count("Libre") == open_game.party_size

    def test_non_owner_gm_cannot_manage_players(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A GM who is not the game owner (and not admin) cannot manage players."""
        response = logged_in_gm.post(
            f"/annonces/{open_game.slug}/gerer/",
            data={"action": "manage"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous n'êtes pas autorisé·e à faire cette action." in body


# -- Game Sessions ---------------------------------------------------------


class TestGameSessions:
    """Session CRUD on games."""

    def test_add_session(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/ajouter/",
            data={"date_start": "2025-07-07 20:00", "date_end": "2025-07-07 23:00"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert 'startDate="2025-07-07"' in body

    def test_add_session_rejects_invalid_dates(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/ajouter/",
            data={"date_start": "2025-07-07 23:00", "date_end": "2025-07-07 20:00"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert (
            "Impossible d'ajouter une session qui se termine avant de commencer" in body
        )

    def test_edit_session(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        gs = GameSessionFactory(db_session, game_id=open_game.id)
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/{gs.id}/editer/",
            data={"date_start": "2025-08-01 20:00", "date_end": "2025-08-01 23:00"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert 'startDate="2025-08-01"' in body

    def test_edit_session_rejects_invalid_dates(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        gs = GameSessionFactory(db_session, game_id=open_game.id)
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/{gs.id}/editer/",
            data={"date_start": "2025-08-01 23:00", "date_end": "2025-08-01 20:00"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert (
            "Impossible d'ajouter une session qui se termine avant de commencer" in body
        )

    def test_remove_session(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        gs = GameSessionFactory(db_session, game_id=open_game.id)
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/{gs.id}/supprimer/",
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Session supprimée." in body


# -- Game Alert ------------------------------------------------------------


class TestGameAlert:
    """POST /annonces/<slug>/alert/ — report/alert on a game."""

    def test_registered_player_sends_alert(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        regular_user,
    ):
        open_game.players.append(regular_user)
        db_session.flush()

        response = logged_in_user.post(
            f"/annonces/{open_game.slug}/alert/",
            data={"alertMessage": "Le MJ ne vient plus."},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Signalement effectué." in body

    def test_unrelated_user_cannot_alert(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        response = logged_in_user.post(
            f"/annonces/{open_game.slug}/alert/",
            data={"alertMessage": "Spam alert"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous n'êtes pas autorisé·e" in body


# -- Game Form Access ------------------------------------------------------


class TestGameFormAccess:
    """GET /annonce/ — access the game creation form."""

    def test_admin_can_access_form(
        self, logged_in_admin, mock_discord_lookups, db_session
    ):
        response = logged_in_admin.get("/annonce/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Nouvelle annonce" in body

    def test_gm_can_access_form(self, logged_in_gm, mock_discord_lookups, db_session):
        response = logged_in_gm.get("/annonce/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Nouvelle annonce" in body

    def test_regular_user_cannot_access_form(
        self, logged_in_user, mock_discord_lookups, db_session
    ):
        response = logged_in_user.get("/annonce/")
        assert response.status_code == 403


# -- Game Search -----------------------------------------------------------


class TestGameSearch:
    """GET /annonces/ — search and filter games."""

    def test_search_no_filters(self, client, mock_discord_lookups, db_session):
        """Search page renders with no query parameters."""
        response = client.get("/annonces/")
        assert response.status_code == 200

    def test_search_by_name(self, client, mock_discord_lookups, db_session, open_game):
        """Searching by name matches the open_game's name via ilike filter."""
        response = client.get(f"/annonces/?name={open_game.name}")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_search_by_system(
        self, client, mock_discord_lookups, db_session, open_game, default_system
    ):
        """open_game uses default_system, so filtering by its ID returns it."""
        response = client.get(f"/annonces/?system={default_system.id}")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_search_by_vtt(
        self, client, mock_discord_lookups, db_session, open_game, default_vtt
    ):
        """open_game uses default_vtt, so filtering by its ID returns it."""
        response = client.get(f"/annonces/?vtt={default_vtt.id}")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_search_status_open_includes_open_game(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        """Filtering by status=open should include the open_game."""
        response = client.get("/annonces/?open=on")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_search_status_archived_excludes_open_game(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        """Filtering by status=archived only should exclude the open_game."""
        response = client.get("/annonces/?archived=on")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name not in body

    def test_search_name_no_match(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        """A name filter that matches nothing should not show the open_game."""
        response = client.get("/annonces/?name=NonExistentGame12345")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name not in body

    def test_search_combined_filters(
        self,
        client,
        mock_discord_lookups,
        db_session,
        open_game,
        default_system,
        default_vtt,
    ):
        """open_game matches all combined filters: system, vtt, open, oneshot, all-ages."""
        response = client.get(
            f"/annonces/?system={default_system.id}&vtt={default_vtt.id}"
            "&open=on&oneshot=on&all=on"
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body


# -- My Games / My GM Games -----------------------------------------------


class TestMyGames:
    """GET /mes_annonces/ and /mes_parties/ — personal game lists."""

    def test_admin_can_view_gm_games(
        self, logged_in_admin, mock_discord_lookups, db_session
    ):
        response = logged_in_admin.get("/mes_annonces/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Mes annonces" in body

    def test_gm_can_view_gm_games(self, logged_in_gm, mock_discord_lookups, db_session):
        response = logged_in_gm.get("/mes_annonces/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Mes annonces" in body

    def test_regular_user_cannot_view_gm_games(
        self, logged_in_user, mock_discord_lookups, db_session
    ):
        response = logged_in_user.get("/mes_annonces/")
        assert response.status_code == 403

    def test_user_can_view_my_games(
        self, logged_in_user, mock_discord_lookups, db_session
    ):
        response = logged_in_user.get("/mes_parties/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Mes parties en cours" in body
