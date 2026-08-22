"""Focused tests for game view endpoints.

Each test exercises a single action with mocked Discord and factory data.
For end-to-end scenarios with real Discord, see test_e2e.py.
"""

import html
from datetime import datetime, timedelta

import pytest

from config.constants import GAMES_PER_PAGE
from tests.constants import TEST_ADMIN_USER_ID, TEST_GM_USER_ID
from tests.factories import GameFactory, GameSessionFactory, SpecialEventFactory

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _purge_leaked_games(test_app):
    """Remove only the games that escaped this test's savepoint rollback.

    Some view actions (publishing, status changes) commit through a path the
    per-test ``db_session`` savepoint does not capture, leaking committed game
    rows that would skew later search/pagination tests (``open_game`` gets
    pushed off page 1). We snapshot the committed game ids before the test and,
    afterwards, delete only the rows that appeared during it — leaving any
    pre-existing persistent data intact, so this is safe whether or not
    ``--drop-db`` is used. Runs on a fresh connection, after the savepoint
    rollback, to avoid lock contention.
    """
    from sqlalchemy import bindparam, text

    from website.extensions import db

    def _committed_game_ids() -> set[int]:
        with db.engine.connect() as conn:
            return {row[0] for row in conn.execute(text("SELECT id FROM game"))}

    before = _committed_game_ids()
    yield
    leaked = sorted(_committed_game_ids() - before)
    if not leaked:
        return
    # game_event cascades on delete; game_session/game_players do not, so clear
    # the leaked games' children explicitly before removing the games themselves.
    with db.engine.begin() as conn:
        for table, column in (
            ("game_session", "game_id"),
            ("game_players", "game_id"),
            ("game", "id"),
        ):
            stmt = text(f"DELETE FROM {table} WHERE {column} IN :ids").bindparams(
                bindparam("ids", expanding=True)
            )
            conn.execute(stmt, {"ids": leaked})


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
        # Future by default so publish flows aren't blocked by the past-date guard.
        "date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d 20:30"),
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

    def test_create_game_missing_action_defaults_to_draft(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        """A malformed submission missing the `action` field doesn't 500."""
        data = _game_form_data(default_system.id, default_vtt.id)
        del data["action"]
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

    def test_blocked_gm_cannot_create_game(
        self,
        logged_in_admin,
        admin_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        admin_user.can_post_games = False
        db_session.flush()

        data = _game_form_data(default_system.id, default_vtt.id, action="open")
        response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
        body = html.unescape(response.data.decode())
        assert response.status_code == 200
        assert "n'êtes pas autorisé" in body
        mock_discord_service.create_role.assert_not_called()

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

    def test_gm_cannot_spoof_gm_id(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        """A tampered gm_id form field can't attribute the game to someone else."""
        from website.models import Game

        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name="Spoofed GM Game",
            gm_id=TEST_ADMIN_USER_ID,
            action="draft",
        )
        response = logged_in_gm.post("/annonce/", data=data, follow_redirects=True)
        assert response.status_code == 200

        game = db_session.query(Game).filter_by(name="Spoofed GM Game").one()
        assert game.gm_id == TEST_GM_USER_ID

    def test_admin_can_create_game_for_another_gm(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        """Unlike a regular GM, an admin may post a game on someone else's behalf."""
        from website.models import Game

        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name="Admin Posted For GM",
            gm_id=TEST_GM_USER_ID,
            action="draft",
        )
        response = logged_in_admin.post("/annonce/", data=data, follow_redirects=True)
        assert response.status_code == 200

        game = db_session.query(Game).filter_by(name="Admin Posted For GM").one()
        assert game.gm_id == TEST_GM_USER_ID

    def test_create_open_to_viewers(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        default_system,
        default_vtt,
    ):
        from website.models import Game

        data = _game_form_data(
            default_system.id, default_vtt.id, action="draft", open_to_viewers="on"
        )
        logged_in_admin.post("/annonce/", data=data, follow_redirects=True)

        game = db_session.query(Game).filter_by(name="Test Game").one()
        assert game.open_to_viewers is True


# -- Game Details ----------------------------------------------------------


class TestGameDetails:
    """GET /annonces/<slug>/ — view game detail page."""

    def test_anonymous_can_view(self, client, mock_discord_lookups, db_session, open_game):
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

    def test_gm_authored_name_is_escaped(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        """.j2 templates must autoescape: a GM-chosen name is not raw HTML."""
        open_game.name = "<script>alert('xss')</script>"
        open_game.restriction_tags = "<img src=x onerror=alert(1)>"
        db_session.flush()

        response = client.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "<script>alert(" not in body
        assert "<img src=x onerror" not in body
        assert "&lt;script&gt;" in body

    def test_description_renders_markdown(
        self, client, mock_discord_lookups, db_session, default_system, default_vtt
    ):
        """Markdown in description/complement is rendered to HTML, not shown raw."""
        game = GameFactory(
            db_session,
            status="open",
            system_id=default_system.id,
            vtt_id=default_vtt.id,
            description="**Bold** scenario",
            complement="Some *complement* info",
        )
        response = client.get(f"/annonces/{game.slug}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "<strong>Bold</strong>" in body
        assert "<em>complement</em>" in body

    def test_description_xss_attempt_is_neutralized(
        self, client, mock_discord_lookups, db_session, default_system, default_vtt
    ):
        """A script-tag XSS attempt in description is rendered inert, not executed."""
        game = GameFactory(
            db_session,
            status="open",
            system_id=default_system.id,
            vtt_id=default_vtt.id,
            description="<script>alert(1)</script>",
        )
        response = client.get(f"/annonces/{game.slug}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "<script>alert(1)</script>" not in body

    def test_open_to_viewers_badge_shown(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        open_game.open_to_viewers = True
        db_session.flush()
        response = client.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert "Ouverte aux spectateur·ices" in body

    def test_open_to_viewers_badge_hidden_by_default(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        response = client.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert "Ouverte aux spectateur·ices" not in body

    def test_follow_button_shown_to_non_participant(
        self, logged_in_user, mock_discord_lookups, db_session, open_game
    ):
        open_game.open_to_viewers = True
        db_session.flush()
        response = logged_in_user.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert "Suivre en tant que spectateur" in body

    def test_follow_button_hidden_when_flag_off(
        self, logged_in_user, mock_discord_lookups, db_session, open_game
    ):
        response = logged_in_user.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert "Suivre en tant que spectateur" not in body

    def test_follow_button_hidden_for_gm(
        self, logged_in_admin, mock_discord_lookups, db_session, open_game
    ):
        open_game.open_to_viewers = True
        db_session.flush()
        response = logged_in_admin.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert "Suivre en tant que spectateur" not in body

    def test_follow_button_hidden_for_registered_player(
        self, logged_in_user, mock_discord_lookups, db_session, open_game, regular_user
    ):
        open_game.open_to_viewers = True
        open_game.players.append(regular_user)
        db_session.flush()
        response = logged_in_user.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert "Suivre en tant que spectateur" not in body


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

    def test_gm_notifies_players(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """The game's GM can post a notification to the channel."""
        open_game.role = "role_123"
        open_game.channel = "channel_123"
        db_session.commit()

        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/notifier/",
            data={"notifyMessage": "Rendez-vous ce soir !"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert "Joueur·euses notifié·es." in response.data.decode()
        mock_discord_service.send_message.assert_called_once()

    def test_notify_without_channel_flashes_specific_error(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """Notifying a game with no Discord channel gives its own message.

        Regression test: this ``ValidationError`` (field="channel") used to
        be indistinguishable from an empty message and always flashed "Le
        message de notification est vide.", which was misleading here.
        """
        assert open_game.channel is None

        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/notifier/",
            data={"notifyMessage": "Rendez-vous ce soir !"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        body = html.unescape(response.data.decode())
        assert "n'a pas de salon Discord associé" in body
        assert "Le message de notification est vide." not in body

    def test_non_owner_cannot_notify(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A GM who does not own the game cannot notify its players."""
        open_game.channel = "channel_123"
        db_session.commit()

        response = logged_in_gm.post(
            f"/annonces/{open_game.slug}/notifier/",
            data={"notifyMessage": "Coucou"},
        )

        assert response.status_code == 403
        mock_discord_service.send_message.assert_not_called()

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
        # Give the draft a future date so the past-date publish guard doesn't fire.
        draft_game.date = datetime.now() + timedelta(days=30)
        db_session.commit()
        response = logged_in_admin.post(
            f"/annonces/{draft_game.slug}/statut/",
            data={"status": "publish"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Annonce publiée avec succès." in body

    def test_publish_draft_game_blocked_by_can_post_games(
        self,
        logged_in_admin,
        admin_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        draft_game,
    ):
        """Publishing via the status-change route flashes, not 500s, when blocked.

        Regression test: unlike the other ``publish()`` call sites in this
        module, ``_handle_publish`` didn't used to catch
        ``GamePostingBlockedError``, so this specific route (draft → open via
        POST /annonces/<slug>/statut/) would 500 instead of flashing the
        usual French message.
        """
        admin_user.can_post_games = False
        draft_game.date = datetime.now() + timedelta(days=30)
        db_session.commit()

        response = logged_in_admin.post(
            f"/annonces/{draft_game.slug}/statut/",
            data={"status": "publish"},
            follow_redirects=True,
        )
        body = html.unescape(response.data.decode())
        assert response.status_code == 200
        assert "n'êtes pas autorisé" in body
        db_session.refresh(draft_game)
        assert draft_game.status == "draft"

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
        )
        assert response.status_code == 403


# -- Game Edit -------------------------------------------------------------


class TestGameEdit:
    """GET/POST /annonces/<slug>/editer/ — edit game."""

    def test_get_edit_form(self, logged_in_admin, mock_discord_lookups, db_session, draft_game):
        response = logged_in_admin.get(f"/annonces/{draft_game.slug}/editer/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous êtes en train de modifier une annonce." in body

    def test_get_clone_form(self, logged_in_admin, mock_discord_lookups, db_session, open_game):
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

    def test_edit_sets_open_to_viewers(
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
            open_to_viewers="on",
        )
        logged_in_admin.post(
            f"/annonces/{draft_game.slug}/editer/",
            data=data,
            follow_redirects=True,
        )
        db_session.refresh(draft_game)
        assert draft_game.open_to_viewers is True

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

    def test_non_owner_gm_cannot_edit_game(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        draft_game,
        default_system,
        default_vtt,
    ):
        """A GM (non-admin, non-owner) cannot edit another GM's game."""
        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name=draft_game.name,
            complement="Sneaky edit",
        )
        response = logged_in_gm.post(
            f"/annonces/{draft_game.slug}/editer/",
            data=data,
        )
        assert response.status_code == 403
        db_session.refresh(draft_game)
        assert draft_game.complement != "Sneaky edit"

    def test_non_owner_gm_cannot_get_edit_form(
        self, logged_in_gm, mock_discord_lookups, db_session, draft_game
    ):
        """A GM (non-admin, non-owner) cannot open another GM's edit form."""
        response = logged_in_gm.get(f"/annonces/{draft_game.slug}/editer/")
        assert response.status_code == 403


# -- Branch a campaign into a quick one-shot --------------------------------


class TestGameBranch:
    """GET/POST /annonces/<slug>/brancher/ — branch a campaign into a one-shot."""

    def test_branch_link_shown_for_open_campaign(
        self, logged_in_admin, mock_discord_lookups, db_session, open_campaign
    ):
        response = logged_in_admin.get(f"/annonces/{open_campaign.slug}/")
        body = response.data.decode()
        assert "branchButton" in body
        assert "One-shot ponctuel" in body
        assert "cloneButton" not in body

    def test_branch_link_hidden_for_oneshot(
        self, logged_in_admin, mock_discord_lookups, db_session, open_game
    ):
        response = logged_in_admin.get(f"/annonces/{open_game.slug}/")
        body = response.data.decode()
        assert "branchButton" not in body
        assert "cloneButton" in body

    def test_branch_link_hidden_for_draft_campaign(
        self, logged_in_admin, mock_discord_lookups, db_session, default_system, default_vtt
    ):
        draft_campaign = GameFactory(
            db_session,
            type="campaign",
            status="draft",
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        response = logged_in_admin.get(f"/annonces/{draft_campaign.slug}/")
        body = response.data.decode()
        assert "branchButton" not in body
        assert "cloneButton" in body

    def test_get_branch_form(
        self, logged_in_admin, mock_discord_lookups, db_session, open_campaign
    ):
        response = logged_in_admin.get(f"/annonces/{open_campaign.slug}/brancher/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous êtes en train de créer un one-shot ponctuel pour cette campagne." in body

    def test_branch_form_does_not_reuse_campaign_data(
        self, logged_in_admin, mock_discord_lookups, db_session, open_campaign
    ):
        """Description is blank; only system/VTT/type/party_size carry over."""
        open_campaign.description = "Une description très spécifique à la campagne"
        db_session.flush()

        response = logged_in_admin.get(f"/annonces/{open_campaign.slug}/brancher/")
        body = response.data.decode()
        assert open_campaign.description not in body
        # The name field starts empty, not pre-filled with the campaign's own name.
        name_tag = body.split('id="game_name"')[1].split(">")[0]
        assert 'value=""' in name_tag

    def test_branch_form_defaults_party_size_to_app_default_without_players(
        self, logged_in_admin, mock_discord_lookups, db_session, open_campaign
    ):
        """An empty campaign doesn't shrink party_size down to 1 — falls back to 4."""
        response = logged_in_admin.get(f"/annonces/{open_campaign.slug}/brancher/")
        body = response.data.decode()
        party_size_tag = body.split('id="party_size_input"')[1].split(">")[0]
        assert 'value="4"' in party_size_tag

    def test_branch_form_defaults_party_size_to_campaign_headcount(
        self, logged_in_admin, mock_discord_lookups, db_session, open_campaign, regular_user
    ):
        open_campaign.players.append(regular_user)
        db_session.flush()

        response = logged_in_admin.get(f"/annonces/{open_campaign.slug}/brancher/")
        body = response.data.decode()
        party_size_tag = body.split('id="party_size_input"')[1].split(">")[0]
        assert 'value="1"' in party_size_tag

    def test_branch_form_defaults_party_selection_checked(
        self, logged_in_admin, mock_discord_lookups, db_session, open_campaign
    ):
        """A branched table is GM-curated by default, not open self-registration."""
        response = logged_in_admin.get(f"/annonces/{open_campaign.slug}/brancher/")
        body = response.data.decode()
        party_selection_tag = body.split('id="party_selection"')[1].split(">")[0]
        assert "checked" in party_selection_tag

    def test_get_branch_form_rejects_oneshot(
        self, logged_in_admin, mock_discord_lookups, db_session, open_game
    ):
        response = logged_in_admin.get(
            f"/annonces/{open_game.slug}/brancher/", follow_redirects=True
        )
        body = html.unescape(response.data.decode())
        assert response.status_code == 200
        assert "Seule une campagne publiée peut être branchée en one-shot." in body

    def test_get_branch_form_rejects_draft_campaign(
        self, logged_in_admin, mock_discord_lookups, db_session, default_system, default_vtt
    ):
        draft_campaign = GameFactory(
            db_session,
            type="campaign",
            status="draft",
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        response = logged_in_admin.get(
            f"/annonces/{draft_campaign.slug}/brancher/", follow_redirects=True
        )
        body = html.unescape(response.data.decode())
        assert "Seule une campagne publiée peut être branchée en one-shot." in body

    def test_get_branch_form_rejects_archived_campaign(
        self, logged_in_admin, mock_discord_lookups, db_session, default_system, default_vtt
    ):
        archived_campaign = GameFactory(
            db_session,
            type="campaign",
            status="archived",
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        response = logged_in_admin.get(
            f"/annonces/{archived_campaign.slug}/brancher/", follow_redirects=True
        )
        body = html.unescape(response.data.decode())
        assert "Seule une campagne publiée peut être branchée en one-shot." in body

    def test_branch_creates_closed_oneshot_with_resources(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_campaign,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name="Session de rattrapage",
            type="oneshot",
            gm_id=TEST_ADMIN_USER_ID,
        )
        response = logged_in_admin.post(
            f"/annonces/{open_campaign.slug}/brancher/",
            data=data,
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "créé" in body
        mock_discord_service.create_role.assert_called_once()
        mock_discord_service.create_channel.assert_called_once()
        # Silent publish: no public announcement sent.
        assert all(
            call.kwargs.get("embed_type") != "annonce"
            for call in mock_discord_service.send_game_embed.call_args_list
        )

    def test_branch_post_rejects_oneshot(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        default_system,
        default_vtt,
    ):
        data = _game_form_data(default_system.id, default_vtt.id, type="oneshot")
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/brancher/",
            data=data,
            follow_redirects=True,
        )
        body = html.unescape(response.data.decode())
        assert "Seule une campagne publiée peut être branchée en one-shot." in body

    def test_branch_gm_only(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_campaign,
    ):
        """A GM (non-admin) cannot branch another GM's campaign."""
        response = logged_in_gm.post(
            f"/annonces/{open_campaign.slug}/brancher/",
            data={"csrf_token": "test"},
        )
        assert response.status_code == 403

    def test_branch_gm_cannot_spoof_gm_id(
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
        """Branching a GM's own campaign can't attribute the one-shot to someone else."""
        from website.models import Game

        own_campaign = GameFactory(
            db_session,
            type="campaign",
            status="open",
            gm_id=gm_user.id,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name="Spoofed Branch",
            type="oneshot",
            gm_id=TEST_ADMIN_USER_ID,
        )
        response = logged_in_gm.post(
            f"/annonces/{own_campaign.slug}/brancher/",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200

        game = db_session.query(Game).filter_by(name="Spoofed Branch").one()
        assert game.gm_id == TEST_GM_USER_ID

    def test_branch_roster_modal_shown_after_creation(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_campaign,
        regular_user,
        default_system,
        default_vtt,
    ):
        open_campaign.players.append(regular_user)
        db_session.flush()

        data = _game_form_data(
            default_system.id,
            default_vtt.id,
            name="Session de rattrapage",
            type="oneshot",
            gm_id=TEST_ADMIN_USER_ID,
        )
        response = logged_in_admin.post(
            f"/annonces/{open_campaign.slug}/brancher/",
            data=data,
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert '<dialog id="branchRosterModal"' in body
        assert "Reporter les joueur" in body
        assert regular_user.name in body

    def test_branch_roster_not_shown_for_other_visitors(
        self, logged_in_user, mock_discord_lookups, db_session, open_game
    ):
        """The ?branch_from= query param is ignored for anyone but the game's GM/admin."""
        response = logged_in_user.get(f"/annonces/{open_game.slug}/?branch_from={open_game.slug}")
        body = response.data.decode()
        # The auto-open script is always present (harmless no-op via getElementById);
        # what must be absent is the modal's own markup.
        assert '<dialog id="branchRosterModal"' not in body

    def test_confirm_branch_roster_carries_checked_players(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_campaign,
        regular_user,
        default_system,
        default_vtt,
    ):
        open_campaign.players.append(regular_user)
        db_session.flush()

        new_game = GameFactory(
            db_session,
            type="oneshot",
            status="closed",
            gm_id=TEST_ADMIN_USER_ID,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
            channel="mock_channel_id",
        )

        response = logged_in_admin.post(
            f"/annonces/{new_game.slug}/brancher/roster/{open_campaign.slug}/",
            data={
                "csrf_token": "test",
                "known_players": regular_user.id,
                regular_user.id: "on",
            },
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "reportée" in body
        db_session.refresh(new_game)
        assert regular_user in new_game.players

    def test_confirm_branch_roster_skips_unchecked_players(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_campaign,
        regular_user,
        default_system,
        default_vtt,
    ):
        open_campaign.players.append(regular_user)
        db_session.flush()

        new_game = GameFactory(
            db_session,
            type="oneshot",
            status="closed",
            gm_id=TEST_ADMIN_USER_ID,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
            channel="mock_channel_id",
        )

        response = logged_in_admin.post(
            f"/annonces/{new_game.slug}/brancher/roster/{open_campaign.slug}/",
            data={
                "csrf_token": "test",
                "known_players": regular_user.id,
                # regular_user's checkbox intentionally omitted (unchecked).
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        db_session.refresh(new_game)
        assert regular_user not in new_game.players


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

    def test_cannot_register_with_schedule_conflict(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        default_system,
        default_vtt,
        regular_user,
        admin_user,
    ):
        other_game = GameFactory(
            db_session,
            gm_id=admin_user.id,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
            status="open",
        )
        other_game.players.append(regular_user)
        # Commit to release the savepoint so the service-level rollback
        # (on ScheduleConflictError) cannot undo the factory-created game.
        db_session.commit()

        response = logged_in_user.post(
            f"/annonces/{open_game.slug}/inscription/",
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous avez déjà une partie prévue à cette date et heure." in body

    def test_cannot_register_with_schedule_conflict_via_gm_game(
        self,
        logged_in_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        default_system,
        default_vtt,
        regular_user,
    ):
        # regular_user GMs another game overlapping open_game's schedule — this
        # must be caught too, not just games they're already a player in.
        GameFactory(
            db_session,
            gm_id=regular_user.id,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
            status="open",
        )
        # Commit to release the savepoint so the service-level rollback
        # (on ScheduleConflictError) cannot undo the factory-created game.
        db_session.commit()

        response = logged_in_user.post(
            f"/annonces/{open_game.slug}/inscription/",
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Vous avez déjà une partie prévue à cette date et heure." in body

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
            data={"action": "manage", "known_players": str(regular_user.id)},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert body.count("Libre") == open_game.party_size

    def test_gm_removes_unchecked_known_player(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        regular_user,
    ):
        """A shown player left unchecked is unregistered."""
        open_game.players.append(regular_user)
        db_session.flush()

        # known_players lists the player, but no checkbox came back for them.
        logged_in_admin.post(
            f"/annonces/{open_game.slug}/gerer/",
            data={"action": "manage", "known_players": str(regular_user.id)},
            follow_redirects=True,
        )
        assert regular_user not in open_game.players

    def test_manage_does_not_remove_player_registered_after_modal_opened(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        regular_user,
        admin_user,
    ):
        """A player absent from the modal snapshot is never unregistered.

        Simulates the race: the GM's modal only knew about ``regular_user`` (kept
        checked), while ``admin_user`` registered afterwards and so is absent from
        ``known_players``. ``admin_user`` must survive the submission.
        """
        open_game.players.append(regular_user)
        open_game.players.append(admin_user)
        db_session.flush()

        logged_in_admin.post(
            f"/annonces/{open_game.slug}/gerer/",
            data={
                "action": "manage",
                "known_players": str(regular_user.id),
                str(regular_user.id): "on",
            },
            follow_redirects=True,
        )

        assert regular_user in open_game.players
        assert admin_user in open_game.players

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
        body = html.unescape(response.data.decode())
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
        assert 'data-start-date="2025-07-07"' in body

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
        assert "Dates de session invalides" in body

    def test_add_session_rejects_malformed_date(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A malformed date string doesn't 500 — it flashes and redirects."""
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/ajouter/",
            data={"date_start": "not-a-date", "date_end": "2025-07-07 23:00"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Dates de session invalides" in body
        assert [s for s in db_session.get(type(open_game), open_game.id).sessions] == []

    def test_add_session_rejects_over_max_duration(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A session longer than 24h (e.g. an end-date typo) is rejected and not stored."""
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/ajouter/",
            # 48h span — mimics a wrong end day/year.
            data={"date_start": "2025-07-07 20:00", "date_end": "2025-07-09 20:00"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Dates de session invalides" in response.data.decode()
        # Nothing must have been persisted for this game.
        assert [s for s in db_session.get(type(open_game), open_game.id).sessions] == []

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
        assert 'data-start-date="2025-08-01"' in body

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
        assert "Dates de session invalides" in body

    def test_edit_session_rejects_malformed_date(
        self,
        logged_in_admin,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A malformed date string doesn't 500 — it flashes and redirects."""
        gs = GameSessionFactory(db_session, game_id=open_game.id)
        original_start = gs.start
        response = logged_in_admin.post(
            f"/annonces/{open_game.slug}/sessions/{gs.id}/editer/",
            data={"date_start": "not-a-date", "date_end": "2025-08-01 23:00"},
            follow_redirects=True,
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Dates de session invalides" in body
        db_session.refresh(gs)
        assert gs.start == original_start

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

    def test_non_owner_gm_cannot_edit_session(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A GM (non-admin, non-owner) cannot edit another GM's game session."""
        gs = GameSessionFactory(db_session, game_id=open_game.id)
        original_start = gs.start
        response = logged_in_gm.post(
            f"/annonces/{open_game.slug}/sessions/{gs.id}/editer/",
            data={"date_start": "2025-08-01 20:00", "date_end": "2025-08-01 23:00"},
        )
        assert response.status_code == 403
        db_session.refresh(gs)
        assert gs.start == original_start

    def test_non_owner_gm_cannot_remove_session(
        self,
        logged_in_gm,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
    ):
        """A GM (non-admin, non-owner) cannot remove another GM's game session."""
        gs = GameSessionFactory(db_session, game_id=open_game.id)
        response = logged_in_gm.post(
            f"/annonces/{open_game.slug}/sessions/{gs.id}/supprimer/",
        )
        assert response.status_code == 403
        assert db_session.get(type(gs), gs.id) is not None

    def test_cannot_edit_another_games_session_via_own_slug(
        self,
        logged_in_gm,
        gm_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        default_system,
        default_vtt,
    ):
        """A GM authorized on their own game can't edit another game's session (IDOR).

        Even though the GM is authorized on ``own_game``, passing the
        ``session_id`` of a session belonging to ``open_game`` (someone
        else's game) must 404, not silently edit it.
        """
        own_game = GameFactory(
            db_session,
            status="open",
            gm_id=gm_user.id,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        foreign_gs = GameSessionFactory(db_session, game_id=open_game.id)
        original_start = foreign_gs.start

        response = logged_in_gm.post(
            f"/annonces/{own_game.slug}/sessions/{foreign_gs.id}/editer/",
            data={"date_start": "2025-08-01 20:00", "date_end": "2025-08-01 23:00"},
        )
        assert response.status_code == 404
        db_session.refresh(foreign_gs)
        assert foreign_gs.start == original_start

    def test_cannot_remove_another_games_session_via_own_slug(
        self,
        logged_in_gm,
        gm_user,
        mock_discord_lookups,
        mock_csrf,
        mock_discord_service,
        db_session,
        open_game,
        default_system,
        default_vtt,
    ):
        """A GM authorized on their own game can't delete another game's session (IDOR)."""
        own_game = GameFactory(
            db_session,
            status="open",
            gm_id=gm_user.id,
            system_id=default_system.id,
            vtt_id=default_vtt.id,
        )
        foreign_gs = GameSessionFactory(db_session, game_id=open_game.id)

        response = logged_in_gm.post(
            f"/annonces/{own_game.slug}/sessions/{foreign_gs.id}/supprimer/",
        )
        assert response.status_code == 404
        assert db_session.get(type(foreign_gs), foreign_gs.id) is not None


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
        )
        assert response.status_code == 403


# -- Follow as viewer -------------------------------------------------------


class TestFollowGame:
    """POST /annonces/<slug>/suivre/ — follow/unfollow a game as a viewer."""

    def test_requires_login(self, client, mock_csrf, db_session, open_game):
        open_game.open_to_viewers = True
        db_session.flush()
        response = client.post(f"/annonces/{open_game.slug}/suivre/")
        assert response.status_code in (302, 303)

    def test_user_can_follow_then_unfollow(
        self, logged_in_user, mock_discord_lookups, mock_csrf, db_session, open_game
    ):
        open_game.open_to_viewers = True
        db_session.flush()

        follow_response = logged_in_user.post(
            f"/annonces/{open_game.slug}/suivre/", follow_redirects=True
        )
        assert "Vous suivez maintenant cette annonce." in follow_response.data.decode()

        unfollow_response = logged_in_user.post(
            f"/annonces/{open_game.slug}/suivre/", follow_redirects=True
        )
        assert "Vous ne suivez plus cette annonce." in unfollow_response.data.decode()

    def test_cannot_follow_when_not_open_to_viewers(
        self, logged_in_user, mock_discord_lookups, mock_csrf, db_session, open_game
    ):
        response = logged_in_user.post(
            f"/annonces/{open_game.slug}/suivre/", follow_redirects=True
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert "Impossible de suivre cette annonce." in body


# -- Game Form Access ------------------------------------------------------


class TestGameFormAccess:
    """GET /annonce/ — access the game creation form."""

    def test_admin_can_access_form(self, logged_in_admin, mock_discord_lookups, db_session):
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


class TestGameFormDefaults:
    """User game-form defaults: only pre-fill new games, never edit/clone."""

    def test_new_game_form_prefills_from_user_defaults(
        self, logged_in_admin, mock_discord_lookups, db_session, admin_user
    ):
        admin_user.game_defaults = {"description": "Ma trame habituelle"}
        db_session.flush()

        response = logged_in_admin.get("/annonce/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Ma trame habituelle" in body

    def test_edit_form_ignores_user_defaults(
        self, logged_in_admin, mock_discord_lookups, db_session, draft_game, admin_user
    ):
        admin_user.game_defaults = {"description": "Ma trame habituelle"}
        db_session.flush()

        response = logged_in_admin.get(f"/annonces/{draft_game.slug}/editer/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Ma trame habituelle" not in body
        assert draft_game.description in body

    def test_clone_form_ignores_user_defaults(
        self, logged_in_admin, mock_discord_lookups, db_session, open_game, admin_user
    ):
        admin_user.game_defaults = {"description": "Ma trame habituelle"}
        db_session.flush()

        response = logged_in_admin.get(f"/annonces/{open_game.slug}/cloner/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Ma trame habituelle" not in body
        assert open_game.description in body


# -- Game Search -----------------------------------------------------------


class TestGameSearch:
    """GET /annonces/ — search and filter games."""

    def test_search_no_filters(self, client, mock_discord_lookups, db_session):
        """Search page renders with no query parameters."""
        response = client.get("/annonces/")
        assert response.status_code == 200

    def test_search_by_name(self, client, mock_discord_lookups, db_session, open_game):
        """Searching by name matches the open_game's name via ilike filter."""
        response = client.get(f"/annonces/cards/?name={open_game.name}")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_search_by_system(
        self, client, mock_discord_lookups, db_session, open_game, default_system
    ):
        """open_game uses default_system, so filtering by its ID returns it."""
        response = client.get(f"/annonces/cards/?system={default_system.id}")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_search_by_vtt(self, client, mock_discord_lookups, db_session, open_game, default_vtt):
        """open_game uses default_vtt, so filtering by its ID returns it."""
        response = client.get(f"/annonces/cards/?vtt={default_vtt.id}")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_card_shows_open_to_viewers_indicator(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        open_game.open_to_viewers = True
        db_session.flush()
        response = client.get(f"/annonces/cards/?name={open_game.name}")
        body = response.data.decode()
        assert "Ouverte aux spectateur" in body

    def test_card_omits_open_to_viewers_indicator_by_default(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        response = client.get(f"/annonces/cards/?name={open_game.name}")
        body = response.data.decode()
        assert "Ouverte aux spectateur" not in body

    def test_search_status_open_includes_open_game(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        """Filtering by status=open should include the open_game."""
        response = client.get("/annonces/cards/?open=on")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body

    def test_search_status_archived_excludes_open_game(
        self, client, mock_discord_lookups, db_session, open_game
    ):
        """Filtering by status=archived only should exclude the open_game."""
        response = client.get("/annonces/cards/?archived=on")
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name not in body

    def test_search_name_no_match(self, client, mock_discord_lookups, db_session, open_game):
        """A name filter that matches nothing should not show the open_game."""
        response = client.get("/annonces/cards/?name=NonExistentGame12345")
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
            f"/annonces/cards/?system={default_system.id}&vtt={default_vtt.id}"
            "&open=on&oneshot=on&all=on"
        )
        body = response.data.decode()
        assert response.status_code == 200
        assert open_game.name in body


class TestSpecialEventGameSearch:
    """GET /annonces/evenement/<event_id>/ — games filtered by special event."""

    def test_search_by_event_renders(self, client, mock_discord_lookups, db_session):
        """The event-filtered search page renders and names the event."""
        event = SpecialEventFactory(db_session, name="Halloween 2026")
        response = client.get(f"/annonces/evenement/{event.id}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Halloween 2026" in body

    def test_search_by_event_unknown_id_redirects(self, client, mock_discord_lookups, db_session):
        """An unknown event id redirects back to the general search page."""
        response = client.get("/annonces/evenement/999999/")
        assert response.status_code == 302
        assert response.location.endswith("/annonces/")

    def test_search_by_event_pagination_links(
        self, client, mock_discord_lookups, db_session, default_system, default_vtt
    ):
        """Regression: pagination must not crash with a BuildError.

        The route's next/prev links used to be built with the wrong endpoint
        prefix ("game.search_games_by_event" instead of
        "annonces.search_games_by_event"), which raised a BuildError as soon
        as a second page of results existed.
        """
        event = SpecialEventFactory(db_session, name="Overflowing Event")
        for _ in range(GAMES_PER_PAGE + 1):
            GameFactory(
                db_session,
                status="open",
                type="oneshot",
                system_id=default_system.id,
                vtt_id=default_vtt.id,
                special_event_id=event.id,
            )

        response = client.get(f"/annonces/evenement/{event.id}/")
        body = response.data.decode()
        assert response.status_code == 200
        assert f"/annonces/evenement/{event.id}/?page=2" in body


# -- My Games / My GM Games -----------------------------------------------


class TestMyGames:
    """GET /mes_annonces/ and /mes_parties/ — personal game lists."""

    def test_admin_can_view_gm_games(self, logged_in_admin, mock_discord_lookups, db_session):
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

    def test_user_can_view_my_games(self, logged_in_user, mock_discord_lookups, db_session):
        response = logged_in_user.get("/mes_parties/")
        body = response.data.decode()
        assert response.status_code == 200
        assert "Mes parties en cours" in body
