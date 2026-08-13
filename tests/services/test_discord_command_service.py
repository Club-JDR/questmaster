"""Tests for DiscordCommandService (Discord slash-command dispatch)."""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from config.constants import (
    DISCORD_MESSAGE_MAX_LENGTH,
    INFRACTION_SEVERITY_REMINDER,
    INFRACTION_SEVERITY_WARNING,
)
from tests.factories import GameFactory, GameSessionFactory
from website.exceptions import NotFoundError
from website.models import GameEvent, Infraction
from website.services.discord_command import (
    MSG_ALERT_SENT,
    MSG_ALREADY_PUBLISHED,
    MSG_BAD_DATE_FORMAT,
    MSG_BAD_DURATION_FORMAT,
    MSG_EMPTY_NOTIFICATION,
    MSG_EMPTY_REASON,
    MSG_GAME_CLOSED_OK,
    MSG_GAME_OPENED_OK,
    MSG_GAME_PUBLISHED,
    MSG_GM_CANNOT_REGISTER,
    MSG_NO_BADGES,
    MSG_NO_INFRACTIONS,
    MSG_NOT_A_GAME_CHANNEL,
    MSG_NOT_A_PLAYER,
    MSG_NOT_ADMIN,
    MSG_NOT_CLOSED,
    MSG_NOT_GM,
    MSG_NOT_OPEN,
    MSG_NOT_PARTICIPANT,
    MSG_PLAYER_NOT_REGISTERED,
    MSG_PLAYER_REGISTERED,
    MSG_PLAYER_UNREGISTERED,
    MSG_PLAYERS_NOTIFIED,
    MSG_SESSION_ADDED,
    MSG_SESSION_CONFLICT,
    MSG_SESSION_DELETED,
    MSG_SESSION_EDITED,
    MSG_SESSION_NOT_FOUND,
    MSG_UNKNOWN_COMMAND,
    DiscordCommandService,
)
from website.services.game import GameService
from website.services.game_session import GameSessionService
from website.services.user import UserService


def _make_user(user_id, is_admin=False):
    """Build a lightweight stand-in for a resolved User (no Discord lookups)."""
    user = Mock()
    user.id = user_id
    user.is_admin = is_admin
    return user


def _payload(name, channel_id, user_id="42", options=None):
    """Build a minimal APPLICATION_COMMAND interaction payload."""
    return {
        "type": 2,
        "token": "interaction-token",
        "channel_id": channel_id,
        "member": {"user": {"id": user_id, "username": "tester", "global_name": "Tester"}},
        "data": {"name": name, "options": options or []},
    }


def _opt(name, value):
    return {"name": name, "type": 3, "value": value}


@pytest.fixture
def command_service(mock_discord):
    """DiscordCommandService with mocked Discord + user services."""
    return DiscordCommandService(
        game_service=GameService(discord_service=mock_discord),
        session_service=GameSessionService(),
        discord_service=mock_discord,
        user_service=Mock(spec=UserService),
    )


@pytest.fixture
def channel_game(db_session, admin_user, default_system):
    """An open game bound to a Discord channel."""
    return GameFactory(
        db_session,
        gm_id=admin_user.id,
        system_id=default_system.id,
        status="open",
        channel=str(uuid4().int)[:18],
    )


def _resolve_as(command_service, user):
    """Make the command service resolve the interaction caller as ``user``."""
    command_service.users.get_or_create.return_value = (user, False)


class TestInlineInfo:
    def test_info_returns_game_summary(self, db_session, command_service, channel_game):
        content = command_service.handle_inline(_payload("info", channel_game.channel))
        assert channel_game.name in content
        assert f"/annonces/{channel_game.slug}/" in content
        assert "Joueur·euses : aucun·e" in content
        assert "Prochaine session : aucune" in content
        assert "Statut : ouverte" in content

    def test_info_shows_role_and_players(
        self, db_session, command_service, channel_game, regular_user
    ):
        # Role mode: the role mention replaces the player list.
        channel_game.role = "555000111222333444"
        channel_game.players.append(regular_user)
        db_session.flush()

        content = command_service.handle_inline(_payload("info", channel_game.channel))
        assert "Rôle : <@&555000111222333444>" in content
        assert "Joueur·euses" not in content

        # Direct-permission mode (no role): players are listed individually.
        channel_game.role = None
        db_session.flush()

        content = command_service.handle_inline(_payload("info", channel_game.channel))
        assert f"Joueur·euses : <@{regular_user.id}>" in content

    def test_info_shows_next_session(self, db_session, command_service, channel_game):
        GameSessionFactory(
            db_session,
            game_id=channel_game.id,
            start=datetime(2030, 9, 1, 20, 0),
            end=datetime(2030, 9, 1, 23, 0),
        )
        content = command_service.handle_inline(_payload("info", channel_game.channel))
        assert "Prochaine session :" in content
        assert "Prochaine session : aucune" not in content

    def test_info_in_non_game_channel_returns_notice(self, db_session, command_service):
        content = command_service.handle_inline(_payload("info", "000000000000000000"))
        assert content == MSG_NOT_A_GAME_CHANNEL

    def test_is_inline(self, command_service):
        assert command_service.is_inline(_payload("info", "1"))
        assert not command_service.is_inline(_payload("signaler", "1"))


class TestSignaler:
    def test_signaler_sends_alert_and_logs_event(
        self, db_session, command_service, channel_game, mock_discord
    ):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "signaler", channel_game.channel, options=[_opt("message", "Au secours")]
        )

        content = command_service._execute(payload)

        assert content == MSG_ALERT_SENT
        mock_discord.send_game_embed.assert_called_once_with(
            channel_game,
            embed_type="alert",
            alert_message="Au secours",
            player=channel_game.gm_id,
        )
        events = (
            db_session.query(GameEvent).filter_by(game_id=channel_game.id, action="alert").all()
        )
        assert len(events) == 1

    def test_signaler_non_participant_is_refused(
        self, db_session, command_service, channel_game, mock_discord
    ):
        _resolve_as(command_service, _make_user("999999999999999999"))
        payload = _payload("signaler", channel_game.channel, options=[_opt("message", "x")])

        content = command_service._execute(payload)

        assert content == MSG_NOT_PARTICIPANT
        mock_discord.send_game_embed.assert_not_called()

    def test_signaler_registered_player_is_allowed(
        self, db_session, command_service, channel_game, regular_user, mock_discord
    ):
        channel_game.players.append(regular_user)
        db_session.flush()
        _resolve_as(command_service, _make_user(regular_user.id))
        payload = _payload("signaler", channel_game.channel, options=[_opt("message", "x")])

        assert command_service._execute(payload) == MSG_ALERT_SENT
        mock_discord.send_game_embed.assert_called_once()

    def test_signaler_outside_game_channel_sends_general_alert(
        self, db_session, command_service, mock_discord
    ):
        _resolve_as(command_service, _make_user("42"))
        payload = _payload(
            "signaler", "000000000000000000", options=[_opt("message", "Souci général")]
        )

        assert command_service._execute(payload) == MSG_ALERT_SENT
        mock_discord.send_game_embed.assert_not_called()
        mock_discord.send_embed.assert_called_once()
        embed = mock_discord.send_embed.call_args.args[0]
        assert "<@42>" in embed["description"]
        assert "Souci général" in embed["description"]

    def test_unknown_channel_returns_notice(self, db_session, command_service):
        _resolve_as(command_service, _make_user("42"))
        payload = _payload("notifier", "000000000000000000", options=[_opt("message", "x")])
        assert command_service._execute(payload) == MSG_NOT_A_GAME_CHANNEL


class TestNotifier:
    def test_notifier_delegates_to_notify_players(
        self, db_session, command_service, channel_game, regular_user
    ):
        channel_game.players.append(regular_user)
        db_session.flush()
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "notifier", channel_game.channel, options=[_opt("message", "Session demain !")]
        )

        assert command_service._execute(payload) == MSG_PLAYERS_NOTIFIED

    def test_notifier_empty_message_returns_french_error(
        self, db_session, command_service, channel_game
    ):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload("notifier", channel_game.channel, options=[_opt("message", "  ")])

        assert command_service._execute(payload) == MSG_EMPTY_NOTIFICATION

    def test_notifier_non_gm_is_refused(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user("999999999999999999"))
        payload = _payload("notifier", channel_game.channel, options=[_opt("message", "x")])

        assert command_service._execute(payload) == MSG_NOT_GM


class TestAjouterSession:
    def test_add_session_happy_path(self, db_session, command_service, channel_game, mock_discord):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "ajouter-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 20:00"), _opt("fin", "01/09/2030 23:00")],
        )

        content = command_service._execute(payload)

        assert content == MSG_SESSION_ADDED
        assert len(channel_game.sessions) == 1
        assert channel_game.sessions[0].start == datetime(2030, 9, 1, 20, 0)
        mock_discord.send_game_embed.assert_called_once()
        assert mock_discord.send_game_embed.call_args.kwargs["embed_type"] == "add-session"

    def test_add_session_with_duration(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "ajouter-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 20:00"), _opt("duree", "2h30")],
        )

        assert command_service._execute(payload) == MSG_SESSION_ADDED
        assert channel_game.sessions[0].end == datetime(2030, 9, 1, 22, 30)

    def test_add_session_defaults_to_game_session_length(
        self, db_session, command_service, channel_game
    ):
        # GameFactory sets session_length to 3.0 hours
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "ajouter-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 20:00")],
        )

        assert command_service._execute(payload) == MSG_SESSION_ADDED
        assert channel_game.sessions[0].end == datetime(2030, 9, 1, 23, 0)

    def test_add_session_bad_duration_returns_format_error(
        self, db_session, command_service, channel_game
    ):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "ajouter-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 20:00"), _opt("duree", "beaucoup")],
        )

        assert command_service._execute(payload) == MSG_BAD_DURATION_FORMAT
        assert len(channel_game.sessions) == 0

    def test_add_session_bad_date_returns_format_error(
        self, db_session, command_service, channel_game
    ):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "ajouter-session",
            channel_game.channel,
            options=[_opt("debut", "pas-une-date"), _opt("fin", "01/09/2030 23:00")],
        )

        assert command_service._execute(payload) == MSG_BAD_DATE_FORMAT
        assert len(channel_game.sessions) == 0

    def test_add_session_conflict_returns_french_message(
        self, db_session, command_service, channel_game
    ):
        GameSessionFactory(
            db_session,
            game_id=channel_game.id,
            start=datetime(2030, 9, 1, 20, 0),
            end=datetime(2030, 9, 1, 23, 0),
        )
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "ajouter-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 21:00"), _opt("fin", "01/09/2030 22:00")],
        )

        assert command_service._execute(payload) == MSG_SESSION_CONFLICT

    def test_add_session_non_gm_is_refused(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user("999999999999999999"))
        payload = _payload(
            "ajouter-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 20:00"), _opt("fin", "01/09/2030 23:00")],
        )

        assert command_service._execute(payload) == MSG_NOT_GM


class TestEditerSession:
    def test_edit_session_happy_path(
        self, db_session, command_service, channel_game, mock_discord
    ):
        session = GameSessionFactory(
            db_session,
            game_id=channel_game.id,
            start=datetime(2030, 9, 1, 20, 0),
            end=datetime(2030, 9, 1, 23, 0),
        )
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "editer-session",
            channel_game.channel,
            options=[
                _opt("debut", "01/09/2030 20:00"),
                _opt("nouveau_debut", "02/09/2030 20:00"),
                _opt("nouvelle_fin", "02/09/2030 23:00"),
            ],
        )

        content = command_service._execute(payload)

        assert content == MSG_SESSION_EDITED
        assert session.start == datetime(2030, 9, 2, 20, 0)
        assert session.end == datetime(2030, 9, 2, 23, 0)
        mock_discord.send_game_embed.assert_called_once()
        assert mock_discord.send_game_embed.call_args.kwargs["embed_type"] == "edit-session"

    def test_edit_session_keeps_current_duration_by_default(
        self, db_session, command_service, channel_game
    ):
        session = GameSessionFactory(
            db_session,
            game_id=channel_game.id,
            start=datetime(2030, 9, 1, 20, 0),
            end=datetime(2030, 9, 1, 23, 0),
        )
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "editer-session",
            channel_game.channel,
            options=[
                _opt("debut", "01/09/2030 20:00"),
                _opt("nouveau_debut", "02/09/2030 19:00"),
            ],
        )

        assert command_service._execute(payload) == MSG_SESSION_EDITED
        assert session.start == datetime(2030, 9, 2, 19, 0)
        # The 3-hour duration is preserved
        assert session.end == datetime(2030, 9, 2, 22, 0)

    def test_edit_session_with_duration(self, db_session, command_service, channel_game):
        session = GameSessionFactory(
            db_session,
            game_id=channel_game.id,
            start=datetime(2030, 9, 1, 20, 0),
            end=datetime(2030, 9, 1, 23, 0),
        )
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "editer-session",
            channel_game.channel,
            options=[
                _opt("debut", "01/09/2030 20:00"),
                _opt("nouveau_debut", "02/09/2030 19:00"),
                _opt("duree", "4h"),
            ],
        )

        assert command_service._execute(payload) == MSG_SESSION_EDITED
        assert session.end == datetime(2030, 9, 2, 23, 0)

    def test_edit_session_unknown_start_returns_not_found(
        self, db_session, command_service, channel_game
    ):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "editer-session",
            channel_game.channel,
            options=[
                _opt("debut", "01/09/2030 20:00"),
                _opt("nouveau_debut", "02/09/2030 20:00"),
                _opt("nouvelle_fin", "02/09/2030 23:00"),
            ],
        )

        assert command_service._execute(payload) == MSG_SESSION_NOT_FOUND


class TestSupprimerSession:
    def test_delete_session_happy_path(
        self, db_session, command_service, channel_game, mock_discord
    ):
        GameSessionFactory(
            db_session,
            game_id=channel_game.id,
            start=datetime(2030, 9, 1, 20, 0),
            end=datetime(2030, 9, 1, 23, 0),
        )
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "supprimer-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 20:00")],
        )

        content = command_service._execute(payload)

        assert content == MSG_SESSION_DELETED
        assert len(channel_game.sessions) == 0
        mock_discord.send_game_embed.assert_called_once()
        assert mock_discord.send_game_embed.call_args.kwargs["embed_type"] == "del-session"

    def test_delete_session_unknown_start_returns_not_found(
        self, db_session, command_service, channel_game, mock_discord
    ):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "supprimer-session",
            channel_game.channel,
            options=[_opt("debut", "01/09/2030 20:00")],
        )

        assert command_service._execute(payload) == MSG_SESSION_NOT_FOUND
        mock_discord.send_game_embed.assert_not_called()


class TestInscrireDesinscrire:
    def test_inscrire_registers_target_player(
        self, db_session, command_service, channel_game, regular_user
    ):
        target = _make_user(regular_user.id)
        target.is_player = True
        command_service.users.get_or_create.side_effect = [
            (_make_user(channel_game.gm_id), False),  # caller
            (target, False),  # membre option
        ]
        payload = _payload(
            "inscrire", channel_game.channel, options=[_opt("membre", regular_user.id)]
        )

        assert command_service._execute(payload) == MSG_PLAYER_REGISTERED
        assert any(p.id == regular_user.id for p in channel_game.players)

    def test_inscrire_refuses_non_player_target(
        self, db_session, command_service, channel_game, regular_user
    ):
        target = _make_user(regular_user.id)
        target.is_player = False
        command_service.users.get_or_create.side_effect = [
            (_make_user(channel_game.gm_id), False),
            (target, False),
        ]
        payload = _payload(
            "inscrire", channel_game.channel, options=[_opt("membre", regular_user.id)]
        )

        assert command_service._execute(payload) == MSG_NOT_A_PLAYER
        assert len(channel_game.players) == 0

    def test_inscrire_refuses_gm_as_target(self, db_session, command_service, channel_game):
        target = _make_user(channel_game.gm_id)
        command_service.users.get_or_create.side_effect = [
            (_make_user(channel_game.gm_id), False),
            (target, False),
        ]
        payload = _payload(
            "inscrire", channel_game.channel, options=[_opt("membre", channel_game.gm_id)]
        )

        assert command_service._execute(payload) == MSG_GM_CANNOT_REGISTER

    def test_inscrire_non_gm_is_refused(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user("999999999999999999"))
        payload = _payload("inscrire", channel_game.channel, options=[_opt("membre", "42")])

        assert command_service._execute(payload) == MSG_NOT_GM

    def test_desinscrire_removes_registered_player(
        self, db_session, command_service, channel_game, regular_user
    ):
        channel_game.players.append(regular_user)
        db_session.flush()
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "desinscrire", channel_game.channel, options=[_opt("membre", regular_user.id)]
        )

        assert command_service._execute(payload) == MSG_PLAYER_UNREGISTERED
        assert all(p.id != regular_user.id for p in channel_game.players)

    def test_desinscrire_unregistered_target_returns_notice(
        self, db_session, command_service, channel_game, regular_user
    ):
        _resolve_as(command_service, _make_user(channel_game.gm_id))
        payload = _payload(
            "desinscrire", channel_game.channel, options=[_opt("membre", regular_user.id)]
        )

        assert command_service._execute(payload) == MSG_PLAYER_NOT_REGISTERED


class TestStatusCommands:
    def test_ouvrir_reopens_closed_game(self, db_session, command_service, channel_game):
        channel_game.status = "closed"
        db_session.flush()
        _resolve_as(command_service, _make_user(channel_game.gm_id))

        assert command_service._execute(_payload("ouvrir", channel_game.channel)) == (
            MSG_GAME_OPENED_OK
        )
        assert channel_game.status == "open"

    def test_ouvrir_on_open_game_returns_notice(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user(channel_game.gm_id))

        assert command_service._execute(_payload("ouvrir", channel_game.channel)) == (
            MSG_NOT_CLOSED
        )

    def test_fermer_closes_open_game(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user(channel_game.gm_id))

        assert command_service._execute(_payload("fermer", channel_game.channel)) == (
            MSG_GAME_CLOSED_OK
        )
        assert channel_game.status == "closed"

    def test_fermer_on_closed_game_returns_notice(self, db_session, command_service, channel_game):
        channel_game.status = "closed"
        db_session.flush()
        _resolve_as(command_service, _make_user(channel_game.gm_id))

        assert command_service._execute(_payload("fermer", channel_game.channel)) == (MSG_NOT_OPEN)

    def test_fermer_non_gm_is_refused(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user("999999999999999999"))

        assert command_service._execute(_payload("fermer", channel_game.channel)) == MSG_NOT_GM


class TestPublier:
    def test_publier_publishes_unpublished_game(
        self, db_session, command_service, channel_game, mock_discord
    ):
        # Silent-publish situation: channel exists, no announcement yet.
        channel_game.status = "closed"
        channel_game.msg_id = None
        channel_game.date = datetime(2030, 9, 1, 20, 0)
        db_session.flush()
        _resolve_as(command_service, _make_user(channel_game.gm_id))

        assert command_service._execute(_payload("publier", channel_game.channel)) == (
            MSG_GAME_PUBLISHED
        )
        assert channel_game.status == "open"
        assert channel_game.msg_id == "mock_msg_id"
        assert mock_discord.send_game_embed.call_args.kwargs["embed_type"] == "annonce"

    def test_publier_already_published_returns_notice(
        self, db_session, command_service, channel_game
    ):
        channel_game.msg_id = "123456789"
        db_session.flush()
        _resolve_as(command_service, _make_user(channel_game.gm_id))

        assert command_service._execute(_payload("publier", channel_game.channel)) == (
            MSG_ALREADY_PUBLISHED
        )

    def test_publier_non_gm_is_refused(self, db_session, command_service, channel_game):
        _resolve_as(command_service, _make_user("999999999999999999"))

        assert command_service._execute(_payload("publier", channel_game.channel)) == MSG_NOT_GM


class TestBadges:
    def test_badges_lists_target_member_trophies(self, db_session, command_service):
        member = _make_user("777")
        member.name = "Riri"
        member.trophy_summary = [
            {"name": "Badge OS", "icon": None, "quantity": 3},
            {"name": "Badge Campagne", "icon": None, "quantity": 1},
        ]
        command_service.users.get_by_id.return_value = member
        payload = _payload("badges", "000000000000000000", options=[_opt("membre", "777")])

        content = command_service.handle_inline(payload)

        command_service.users.get_by_id.assert_called_once_with("777")
        assert "Riri" in content
        assert "Badge OS ×3" in content
        assert "Badge Campagne ×1" in content

    def test_badges_defaults_to_caller(self, db_session, command_service):
        member = _make_user("42")
        member.name = "Tester"
        member.trophy_summary = [{"name": "Badge OS", "icon": None, "quantity": 1}]
        command_service.users.get_by_id.return_value = member

        content = command_service.handle_inline(_payload("badges", "000000000000000000"))

        command_service.users.get_by_id.assert_called_once_with("42")
        assert "Badge OS ×1" in content

    def test_badges_unknown_or_trophyless_member_returns_notice(self, db_session, command_service):
        command_service.users.get_by_id.side_effect = NotFoundError(
            "User not found", resource_type="User", resource_id="777"
        )
        payload = _payload("badges", "000000000000000000", options=[_opt("membre", "777")])

        assert command_service.handle_inline(payload) == MSG_NO_BADGES

    def test_badges_is_inline(self, command_service):
        assert command_service.is_inline(_payload("badges", "1"))


class TestAvertir:
    def test_avertir_records_infraction(
        self, db_session, command_service, admin_user, regular_user
    ):
        command_service.users.get_or_create.side_effect = [
            (_make_user(admin_user.id, is_admin=True), False),  # caller
            (_make_user(regular_user.id), False),  # membre option
        ]
        payload = _payload(
            "avertir",
            "000000000000000000",
            options=[_opt("membre", regular_user.id), _opt("raison", "Spam dans #général")],
        )

        content = command_service._execute(payload)

        assert "Infraction enregistrée" in content
        assert f"<@{regular_user.id}>" in content
        assert "Rappel à l'ordre" in content
        infraction = db_session.query(Infraction).filter_by(user_id=regular_user.id).one()
        assert infraction.reason == "Spam dans #général"
        assert infraction.severity == INFRACTION_SEVERITY_REMINDER
        assert infraction.admin_id == admin_user.id

    def test_avertir_with_all_options(self, db_session, command_service, admin_user, regular_user):
        command_service.users.get_or_create.side_effect = [
            (_make_user(admin_user.id, is_admin=True), False),
            (_make_user(regular_user.id), False),
        ]
        payload = _payload(
            "avertir",
            "000000000000000000",
            options=[
                _opt("membre", regular_user.id),
                _opt("raison", "Récidive"),
                _opt("gravite", INFRACTION_SEVERITY_WARNING),
                _opt("article", "Article 3"),
                _opt("lien", "https://discord.com/channels/1/2/3"),
            ],
        )

        content = command_service._execute(payload)

        assert "Avertissement" in content
        infraction = db_session.query(Infraction).filter_by(user_id=regular_user.id).one()
        assert infraction.severity == INFRACTION_SEVERITY_WARNING
        assert infraction.rule_article == "Article 3"
        assert infraction.message_link == "https://discord.com/channels/1/2/3"

    def test_avertir_blank_reason_returns_french_error(
        self, db_session, command_service, admin_user, regular_user
    ):
        command_service.users.get_or_create.side_effect = [
            (_make_user(admin_user.id, is_admin=True), False),
            (_make_user(regular_user.id), False),
        ]
        payload = _payload(
            "avertir",
            "000000000000000000",
            options=[_opt("membre", regular_user.id), _opt("raison", "   ")],
        )

        assert command_service._execute(payload) == MSG_EMPTY_REASON
        assert db_session.query(Infraction).filter_by(user_id=regular_user.id).count() == 0

    def test_avertir_non_admin_is_refused(self, db_session, command_service, regular_user):
        _resolve_as(command_service, _make_user(regular_user.id, is_admin=False))
        payload = _payload(
            "avertir",
            "000000000000000000",
            options=[_opt("membre", "42"), _opt("raison", "x")],
        )

        assert command_service._execute(payload) == MSG_NOT_ADMIN
        assert db_session.query(Infraction).filter_by(user_id="42").count() == 0


class TestInfractions:
    def test_infractions_lists_member_history_newest_first(
        self, db_session, command_service, admin_user, regular_user
    ):
        db_session.add(
            Infraction(
                user_id=regular_user.id,
                reason="Spam",
                severity=INFRACTION_SEVERITY_WARNING,
                rule_article="Article 3",
                message_link="https://discord.com/channels/1/2/3",
                admin_id=admin_user.id,
                created_at=datetime(2026, 1, 1, 12, 0),
            )
        )
        db_session.add(
            Infraction(
                user_id=regular_user.id,
                reason="Flood",
                created_at=datetime(2026, 2, 1, 12, 0),
            )
        )
        db_session.flush()
        _resolve_as(command_service, _make_user(admin_user.id, is_admin=True))
        payload = _payload(
            "infractions", "000000000000000000", options=[_opt("membre", regular_user.id)]
        )

        content = command_service._execute(payload)

        assert f"**Infractions de <@{regular_user.id}>** (2)" in content
        assert "01/01/2026 — Avertissement — Article 3 — Spam" in content
        assert f"par <@{admin_user.id}>" in content
        assert "(https://discord.com/channels/1/2/3)" in content
        # Newest first
        assert content.index("Flood") < content.index("Spam")

    def test_infractions_without_history_returns_notice(
        self, db_session, command_service, admin_user, regular_user
    ):
        _resolve_as(command_service, _make_user(admin_user.id, is_admin=True))
        payload = _payload(
            "infractions", "000000000000000000", options=[_opt("membre", regular_user.id)]
        )

        assert command_service._execute(payload) == MSG_NO_INFRACTIONS

    def test_infractions_non_admin_is_refused(self, db_session, command_service, regular_user):
        _resolve_as(command_service, _make_user(regular_user.id, is_admin=False))
        payload = _payload("infractions", "000000000000000000", options=[_opt("membre", "42")])

        assert command_service._execute(payload) == MSG_NOT_ADMIN

    def test_infractions_long_history_is_truncated(
        self, db_session, command_service, admin_user, regular_user
    ):
        for i in range(30):
            db_session.add(
                Infraction(
                    user_id=regular_user.id,
                    reason=f"Motif {i} " + "x" * 100,
                    admin_id=admin_user.id,
                )
            )
        db_session.flush()
        _resolve_as(command_service, _make_user(admin_user.id, is_admin=True))
        payload = _payload(
            "infractions", "000000000000000000", options=[_opt("membre", regular_user.id)]
        )

        content = command_service._execute(payload)

        assert len(content) <= DISCORD_MESSAGE_MAX_LENGTH
        assert "de plus" in content
        assert "(30)" in content


class TestResolutionAndFollowup:
    def test_resolve_user_get_or_creates_and_refreshes_roles(self, command_service):
        stub = _make_user("42")
        command_service.users.get_or_create.return_value = (stub, True)

        user = command_service._resolve_user(_payload("info", "1"))

        assert user is stub
        command_service.users.get_or_create.assert_called_once_with(
            user_id="42", name="Tester", username="tester"
        )
        stub.refresh_roles.assert_called_once()

    def test_resolve_game_maps_channel_to_game(self, db_session, command_service, channel_game):
        game = command_service._resolve_game(_payload("info", channel_game.channel))
        assert game is not None
        assert game.id == channel_game.id

    def test_unknown_command_returns_notice(self, db_session, command_service, channel_game):
        assert (
            command_service._execute(_payload("inconnue", channel_game.channel))
            == MSG_UNKNOWN_COMMAND
        )

    def test_run_in_context_sends_followup(self, test_app, command_service, mock_discord):
        payload = _payload("inconnue", "000000000000000000")

        command_service._run_in_context(test_app, payload)

        mock_discord.send_interaction_followup.assert_called_once_with(
            test_app.config["DISCORD_APP_ID"], "interaction-token", MSG_UNKNOWN_COMMAND
        )
