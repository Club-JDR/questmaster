"""Tests for GameService."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from config.constants import DISCORD_NAME_MAX, MAX_SLUG_LENGTH, PLAYER_ROLE_PERMISSION
from tests.factories import GameFactory, UserFactory
from website.exceptions import (
    DiscordAPIError,
    DuplicateRegistrationError,
    GameClosedError,
    GameFullError,
    NotFoundError,
    PastDateError,
    ValidationError,
)
from website.services.game import GameService


class TestGameService:
    def test_get_by_id(self, db_session, sample_game, game_service):
        game = game_service.get_by_id(sample_game.id)
        assert game is not None
        assert game.id == sample_game.id

    def test_get_by_id_not_found(self, db_session, game_service):
        with pytest.raises(NotFoundError):
            game_service.get_by_id(999999)

    def test_get_by_slug(self, db_session, sample_game, game_service):
        game = game_service.get_by_slug(sample_game.slug)
        assert game is not None
        assert game.slug == sample_game.slug

    def test_get_by_slug_not_found(self, db_session, game_service):
        with pytest.raises(NotFoundError):
            game_service.get_by_slug("nonexistent")

    def test_generate_slug(self, db_session, game_service):
        slug = game_service.generate_slug("My Game", "TestGM")
        assert slug == "my-game-par-testgm"

    def test_generate_slug_with_collision(
        self, db_session, admin_user, default_system, game_service
    ):
        base_slug = "collision-test-par-testgm"
        GameFactory(
            db_session,
            slug=base_slug,
            name="Collision Test",
            gm_id=admin_user.id,
            system_id=default_system.id,
        )

        slug = game_service.generate_slug("Collision Test", "TestGM")
        assert slug != base_slug

    def test_generate_slug_exclude_does_not_produce_false_collision(
        self, db_session, admin_user, default_system, game_service
    ):
        """Excluding the current slug should not cause a rename to itself to produce slug-2."""
        existing_slug = "my-game-par-testgm"
        GameFactory(
            db_session,
            slug=existing_slug,
            name="My Game",
            gm_id=admin_user.id,
            system_id=default_system.id,
        )

        slug = game_service.generate_slug("My Game", "TestGM", exclude_slug=existing_slug)
        assert slug == existing_slug

    def test_generate_slug_exclude_does_not_bypass_real_collision(
        self, db_session, admin_user, default_system, game_service
    ):
        """Excluding the current slug must not hide collisions with other games."""
        other_slug = "plop-par-testgm"
        current_slug = "test-par-testgm"
        GameFactory(
            db_session,
            slug=other_slug,
            name="Plop",
            gm_id=admin_user.id,
            system_id=default_system.id,
        )
        GameFactory(
            db_session,
            slug=current_slug,
            name="Test",
            gm_id=admin_user.id,
            system_id=default_system.id,
        )

        slug = game_service.generate_slug("Plop", "TestGM", exclude_slug=current_slug)
        assert slug != other_slug

    def test_generate_slug_caps_long_name(self, db_session, game_service):
        """A very long name must yield a slug short enough for Discord names.

        Discord caps role ("PJ_<slug>") and channel names at 100 chars; the slug
        itself is bounded so those derived names never exceed the limit.
        """
        long_name = "Lorem ipsum dolor sit amet " * 10  # ~270 chars

        slug = game_service.generate_slug(long_name, "TestGM")

        assert len(slug) <= MAX_SLUG_LENGTH
        assert len("PJ_" + slug) <= DISCORD_NAME_MAX

    def test_parse_game_type_oneshot(self, db_session, game_service):
        game_type, event_id = game_service.parse_game_type("oneshot")
        assert game_type == "oneshot"
        assert event_id is None

    def test_parse_game_type_special_event(self, db_session, game_service):
        game_type, event_id = game_service.parse_game_type("specialevent-1000")
        assert game_type == "oneshot"
        assert event_id == 1000

    @patch("website.utils.form_parsers.get_classification")
    @patch("website.utils.form_parsers.get_ambience")
    @patch("website.utils.form_parsers.parse_restriction_tags")
    def test_create_draft_game(
        self,
        mock_tags,
        mock_ambience,
        mock_class,
        db_session,
        admin_user,
        default_system,
        game_service,
    ):
        mock_class.return_value = {
            "action": 1,
            "investigation": 1,
            "interaction": 0,
            "horror": 0,
        }
        mock_ambience.return_value = ["serious"]
        mock_tags.return_value = None

        data = {
            "name": "New Draft Game",
            "type": "oneshot",
            "length": "4h",
            "system": default_system.id,
            "vtt": None,
            "description": "Test game",
            "restriction": "all",
            "party_size": 5,
            "xp": "all",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "session_length": 4.0,
            "characters": "self",
        }

        game = game_service.create(data, admin_user.id, status="draft", create_resources=False)

        assert game is not None
        assert game.slug == f"new-draft-game-par-{admin_user.username}"
        assert game.status == "draft"
        assert game.name == "New Draft Game"
        assert game.party_size == 5

    @patch("website.utils.form_parsers.get_classification")
    @patch("website.utils.form_parsers.get_ambience")
    @patch("website.utils.form_parsers.parse_restriction_tags")
    def test_create_with_resources(
        self,
        mock_tags,
        mock_ambience,
        mock_class,
        db_session,
        admin_user,
        default_system,
        oneshot_channel,
        mock_discord,
        game_service,
    ):
        mock_class.return_value = {}
        mock_ambience.return_value = []
        mock_tags.return_value = None

        data = {
            "name": "Game With Resources",
            "type": "oneshot",
            "length": "3h",
            "system": default_system.id,
            "description": "Test",
            "restriction": "all",
            "party_size": 4,
            "xp": "all",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "session_length": 3.0,
            "characters": "self",
        }

        game = game_service.create(data, admin_user.id, status="open", create_resources=True)

        assert game.role == "mock_role_id"
        assert game.channel == "mock_channel_id"
        mock_discord.create_role.assert_called_once()
        mock_discord.create_channel.assert_called_once()

    @patch("website.utils.form_parsers.get_classification")
    @patch("website.utils.form_parsers.get_ambience")
    @patch("website.utils.form_parsers.parse_restriction_tags")
    def test_update_game(
        self,
        mock_tags,
        mock_ambience,
        mock_class,
        db_session,
        sample_game,
        default_system,
        game_service,
    ):
        mock_class.return_value = {}
        mock_ambience.return_value = []
        mock_tags.return_value = None

        data = {
            "name": "Test Service Game",
            "type": "oneshot",
            "system": default_system.id,
            "description": "Updated description",
            "restriction": "16+",
            "party_size": 6,
            "xp": "seasoned",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "length": "4h",
            "session_length": 4.0,
            "characters": "pregen",
        }

        game = game_service.update(sample_game.slug, data)

        assert game.description == "Updated description"
        assert game.restriction == "16+"
        assert game.party_size == 6

    @patch("website.utils.form_parsers.get_classification")
    @patch("website.utils.form_parsers.get_ambience")
    @patch("website.utils.form_parsers.parse_restriction_tags")
    def test_update_draft_game_regenerates_slug_on_rename(
        self,
        mock_tags,
        mock_ambience,
        mock_class,
        db_session,
        sample_game,
        default_system,
        game_service,
    ):
        mock_class.return_value = {}
        mock_ambience.return_value = []
        mock_tags.return_value = None
        old_slug = sample_game.slug

        data = {
            "name": "Renamed Game",
            "type": "oneshot",
            "system": default_system.id,
            "description": "desc",
            "restriction": "all",
            "party_size": 4,
            "xp": "all",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "length": "3h",
            "session_length": 3.0,
            "characters": "self",
        }

        game = game_service.update(old_slug, data)

        assert game.name == "Renamed Game"
        assert game.slug != old_slug
        assert "renamed-game" in game.slug

    @patch("website.utils.form_parsers.get_classification")
    @patch("website.utils.form_parsers.get_ambience")
    @patch("website.utils.form_parsers.parse_restriction_tags")
    def test_update_draft_game_slug_unchanged_when_name_unchanged(
        self,
        mock_tags,
        mock_ambience,
        mock_class,
        db_session,
        sample_game,
        default_system,
        game_service,
    ):
        mock_class.return_value = {}
        mock_ambience.return_value = []
        mock_tags.return_value = None
        old_slug = sample_game.slug

        data = {
            "name": sample_game.name,
            "type": "oneshot",
            "system": default_system.id,
            "description": "Updated description",
            "restriction": "all",
            "party_size": 4,
            "xp": "all",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "length": "3h",
            "session_length": 3.0,
            "characters": "self",
        }

        game = game_service.update(old_slug, data)

        assert game.slug == old_slug

    @patch("website.utils.form_parsers.get_classification")
    @patch("website.utils.form_parsers.get_ambience")
    @patch("website.utils.form_parsers.parse_restriction_tags")
    def test_update_published_game_does_not_change_slug(
        self,
        mock_tags,
        mock_ambience,
        mock_class,
        db_session,
        sample_game,
        default_system,
        game_service,
        mock_discord,
    ):
        mock_class.return_value = {}
        mock_ambience.return_value = []
        mock_tags.return_value = None
        sample_game.status = "open"
        sample_game.msg_id = "existing_msg"
        db_session.commit()
        old_slug = sample_game.slug

        data = {
            "name": "New Name That Should Be Ignored",
            "type": "oneshot",
            "system": default_system.id,
            "description": "Updated description",
            "restriction": "all",
            "party_size": 4,
            "xp": "all",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "length": "3h",
            "session_length": 3.0,
            "characters": "self",
        }

        game = game_service.update(old_slug, data)

        assert game.slug == old_slug
        assert game.name == sample_game.name

    def test_publish_game(
        self, db_session, sample_game, mock_discord, game_service, oneshot_channel
    ):
        mock_discord.send_game_embed.return_value = "msg_123456"

        game = game_service.publish(sample_game.slug, silent=False, allow_past_date=True)

        assert game.status == "open"
        assert game.msg_id == "msg_123456"
        mock_discord.send_game_embed.assert_called()

    def test_publish_game_silent(
        self, db_session, sample_game, mock_discord, game_service, oneshot_channel
    ):
        game = game_service.publish(sample_game.slug, silent=True, allow_past_date=True)

        assert game.status == "closed"
        assert game.msg_id is None
        mock_discord.send_game_embed.assert_called_once_with(game, embed_type="annonce_details")

    def test_publish_already_published(self, db_session, sample_game, game_service):
        sample_game.msg_id = "existing_msg"
        db_session.commit()

        with pytest.raises(ValidationError, match="already published"):
            game_service.publish(sample_game.slug)

    def test_publish_past_date_raises(
        self, db_session, sample_game, mock_discord, game_service, oneshot_channel
    ):
        """Publishing a draft dated in the past must be refused without confirmation."""
        sample_game.date = datetime.now() - timedelta(days=1)
        db_session.commit()

        with pytest.raises(PastDateError):
            game_service.publish(sample_game.slug)

        # No resources or announcement should have been created.
        assert sample_game.status == "draft"
        assert sample_game.channel is None
        mock_discord.create_channel.assert_not_called()

    def test_publish_past_date_allowed(
        self, db_session, sample_game, mock_discord, game_service, oneshot_channel
    ):
        """With explicit confirmation, a past-dated draft publishes normally."""
        sample_game.date = datetime.now() - timedelta(days=1)
        db_session.commit()
        mock_discord.send_game_embed.return_value = "msg_past"

        game = game_service.publish(sample_game.slug, silent=False, allow_past_date=True)

        assert game.status == "open"
        assert game.msg_id == "msg_past"

    def test_publish_future_date_ok(
        self, db_session, sample_game, mock_discord, game_service, oneshot_channel
    ):
        """A future start date needs no confirmation to publish."""
        sample_game.date = datetime.now() + timedelta(days=7)
        db_session.commit()
        mock_discord.send_game_embed.return_value = "msg_future"

        game = game_service.publish(sample_game.slug, silent=False)

        assert game.status == "open"
        assert game.msg_id == "msg_future"

    def test_close_game(self, db_session, sample_game, game_service):
        sample_game.status = "open"
        db_session.commit()

        game = game_service.close(sample_game.slug)

        assert game.status == "closed"

    def test_reopen_game(self, db_session, sample_game, game_service):
        sample_game.status = "closed"
        db_session.commit()

        game = game_service.reopen(sample_game.slug)

        assert game.status == "open"

    def test_archive_game(self, db_session, sample_game, mock_discord, game_service):
        sample_game.status = "closed"
        sample_game.role = "role_123"
        sample_game.channel = "channel_456"
        db_session.commit()

        game_service.archive(sample_game.slug, award_trophies=False)

        game = game_service.get_by_slug(sample_game.slug)
        assert game.status == "archived"
        mock_discord.delete_role.assert_called_once()
        mock_discord.delete_channel.assert_called_once()

    def test_archive_game_already_archived_is_noop(
        self, db_session, sample_game, mock_discord, game_service
    ):
        sample_game.status = "archived"
        db_session.commit()

        # Should not raise and should not touch Discord resources
        game_service.archive(sample_game.slug, award_trophies=True)

        mock_discord.delete_role.assert_not_called()
        mock_discord.delete_channel.assert_not_called()

    def test_delete_game(self, db_session, sample_game, game_service):
        game_service.delete(sample_game.slug)

        with pytest.raises(NotFoundError):
            game_service.get_by_slug(sample_game.slug)

    def test_register_player(
        self, db_session, sample_game, regular_user, mock_discord, game_service
    ):
        sample_game.status = "open"
        sample_game.role = "role_123"
        db_session.commit()

        game = game_service.register_player(sample_game.slug, regular_user.id, force=False)

        assert regular_user in game.players
        mock_discord.add_role_to_user.assert_called_once_with(regular_user.id, "role_123")

    def test_register_player_duplicate(self, db_session, sample_game, regular_user, game_service):
        sample_game.status = "open"
        sample_game.players.append(regular_user)
        db_session.commit()

        with pytest.raises(DuplicateRegistrationError):
            game_service.register_player(sample_game.slug, regular_user.id)

    def test_register_player_game_full(
        self, db_session, sample_game, regular_user, admin_user, game_service
    ):
        sample_game.status = "open"
        sample_game.party_size = 1
        sample_game.players.append(admin_user)
        db_session.commit()

        with pytest.raises(GameFullError):
            game_service.register_player(sample_game.slug, regular_user.id)

    def test_register_player_game_closed(
        self, db_session, sample_game, regular_user, game_service
    ):
        sample_game.status = "closed"
        db_session.commit()

        with pytest.raises(GameClosedError):
            game_service.register_player(sample_game.slug, regular_user.id)

    def test_register_player_force(
        self,
        db_session,
        sample_game,
        regular_user,
        admin_user,
        mock_discord,
        game_service,
    ):
        sample_game.status = "closed"
        sample_game.party_size = 1
        sample_game.players.append(admin_user)
        sample_game.role = "role_123"
        db_session.commit()

        game = game_service.register_player(sample_game.slug, regular_user.id, force=True)

        # Force should bypass both capacity and status checks
        assert regular_user in game.players
        assert len(game.players) == 2

    def test_register_player_auto_close(
        self, db_session, sample_game, regular_user, mock_discord, game_service
    ):
        sample_game.status = "open"
        sample_game.party_size = 1
        sample_game.party_selection = False
        sample_game.role = "role_123"
        sample_game.msg_id = "msg_123"
        db_session.commit()

        game = game_service.register_player(sample_game.slug, regular_user.id, force=False)

        # Game should auto-close when reaching capacity
        assert game.status == "closed"
        assert len(game.players) == 1

    def test_unregister_player(
        self, db_session, sample_game, regular_user, mock_discord, game_service
    ):
        sample_game.status = "open"
        sample_game.role = "role_123"
        sample_game.players.append(regular_user)
        db_session.commit()

        game = game_service.unregister_player(sample_game.slug, regular_user.id)

        assert regular_user not in game.players
        mock_discord.remove_role_from_user.assert_called_once_with(regular_user.id, "role_123")

    def test_unregister_player_not_registered(
        self, db_session, sample_game, regular_user, game_service
    ):
        with pytest.raises(ValidationError, match="not registered"):
            game_service.unregister_player(sample_game.slug, regular_user.id)

    def test_unregister_player_auto_reopen(
        self, db_session, sample_game, regular_user, mock_discord, game_service
    ):
        sample_game.status = "closed"
        sample_game.party_size = 2
        sample_game.party_selection = False
        sample_game.role = "role_123"
        sample_game.players.append(regular_user)
        db_session.commit()

        game = game_service.unregister_player(sample_game.slug, regular_user.id)

        # Game should reopen when below capacity
        assert game.status == "open"

    def test_clone_game(self, db_session, sample_game, game_service):
        game_data = game_service.clone(sample_game.slug)

        assert game_data is not None
        assert game_data["name"] == sample_game.name
        assert game_data["party_size"] == 4
        assert "id" in game_data
        assert "slug" in game_data

    def test_search(self, db_session, sample_game, game_service):
        games, total = game_service.search(
            filters={"status": ["draft"], "game_type": ["oneshot"]},
            page=1,
            per_page=20,
            user_payload={"user_id": sample_game.gm_id, "is_admin": True},
        )

        assert total >= 1
        assert len(games) >= 1


class TestGameServicePrivateHelpers:
    """Tests for GameService private helper error paths."""

    def test_cleanup_discord_resources_channel_failure_still_deletes_role(
        self, db_session, sample_game, mock_discord
    ):
        """When channel deletion fails, role deletion still proceeds."""
        mock_discord.delete_channel.side_effect = DiscordAPIError(
            "Channel not found", status_code=404
        )
        mock_channel_service = Mock()

        service = GameService(
            discord_service=mock_discord,
            channel_service=mock_channel_service,
        )

        sample_game.channel = "channel_123"
        sample_game.role = "role_456"

        # Should not raise — errors are caught and logged
        service._cleanup_discord_resources(sample_game)

        mock_discord.delete_channel.assert_called_once_with("channel_123")
        mock_discord.delete_role.assert_called_once_with("role_456")

    def test_cleanup_discord_resources_role_failure_does_not_propagate(
        self, db_session, sample_game, mock_discord
    ):
        """When role deletion fails, no exception propagates."""
        mock_discord.delete_role.side_effect = DiscordAPIError("Role not found", status_code=404)
        mock_channel_service = Mock()

        service = GameService(
            discord_service=mock_discord,
            channel_service=mock_channel_service,
        )

        sample_game.channel = "channel_123"
        sample_game.role = "role_456"

        # Should not raise
        service._cleanup_discord_resources(sample_game)

        mock_discord.delete_channel.assert_called_once_with("channel_123")
        mock_discord.delete_role.assert_called_once_with("role_456")

    def test_award_game_trophies_skips_on_error(self, db_session, sample_game):
        """Trophy award failure is logged but doesn't propagate."""
        mock_trophy_service = Mock()
        mock_trophy_service.award.side_effect = Exception("Trophy DB error")

        service = GameService(trophy_service=mock_trophy_service)

        sample_game.type = "oneshot"
        db_session.commit()

        # Should not raise — error is caught inside _award_game_trophies
        service._award_game_trophies(sample_game)

        mock_trophy_service.award.assert_called_once()

    def test_delete_game_message_logs_on_failure(self, db_session, sample_game, mock_discord):
        """Discord message deletion failure is logged but doesn't propagate."""
        mock_discord.delete_message.side_effect = DiscordAPIError(
            "Message not found", status_code=404
        )

        service = GameService(discord_service=mock_discord)

        sample_game.msg_id = "msg_to_delete"
        db_session.commit()

        # Should not raise
        service._delete_game_message(sample_game)

        mock_discord.delete_message.assert_called_once()
        # msg_id should NOT be cleared since deletion failed
        assert sample_game.msg_id == "msg_to_delete"

    def test_delete_game_message_skips_when_no_msg_id(self, db_session, sample_game, mock_discord):
        """When game has no msg_id, deletion is skipped entirely."""
        service = GameService(discord_service=mock_discord)

        sample_game.msg_id = None

        service._delete_game_message(sample_game)

        mock_discord.delete_message.assert_not_called()

    def test_is_player_true(self, db_session, sample_game, game_service, regular_user):
        """is_player returns True when user is in the players list."""
        sample_game.players.append(regular_user)
        db_session.commit()

        assert game_service.is_player(sample_game, regular_user.id) is True

    def test_is_player_false(self, db_session, sample_game, game_service, regular_user):
        """is_player returns False when user is not in the players list."""
        assert game_service.is_player(sample_game, regular_user.id) is False

    def test_is_player_empty_players(self, db_session, sample_game, game_service):
        """is_player returns False when game has no players."""
        assert game_service.is_player(sample_game, "nonexistent_id") is False

    def test_rollback_discord_resources_cleans_up(self, db_session, sample_game, mock_discord):
        """Rollback deletes both channel and role when both exist."""
        service = GameService(discord_service=mock_discord)

        sample_game.channel = "channel_123"
        sample_game.role = "role_456"

        service._rollback_discord_resources(sample_game)

        mock_discord.delete_channel.assert_called_once_with("channel_123")
        mock_discord.delete_role.assert_called_once_with("role_456")


class TestGameServiceDirectPermissions:
    """Tests for direct per-player channel permission mode (no per-game role)."""

    @pytest.fixture
    def direct_settings(self):
        """Settings service stub with direct-permission mode enabled."""
        settings = Mock()
        settings.is_direct_permissions_enabled.return_value = True
        return settings

    @patch("website.utils.form_parsers.get_classification")
    @patch("website.utils.form_parsers.get_ambience")
    @patch("website.utils.form_parsers.parse_restriction_tags")
    def test_setup_resources_skips_role_in_direct_mode(
        self,
        mock_tags,
        mock_ambience,
        mock_class,
        db_session,
        admin_user,
        default_system,
        oneshot_channel,
        mock_discord,
        direct_settings,
    ):
        """Direct mode creates no role and a channel without a role overwrite."""
        mock_class.return_value = {}
        mock_ambience.return_value = []
        mock_tags.return_value = None

        service = GameService(discord_service=mock_discord, settings_service=direct_settings)
        data = {
            "name": "Direct Mode Game",
            "type": "oneshot",
            "length": "3h",
            "system": default_system.id,
            "description": "Test",
            "restriction": "all",
            "party_size": 4,
            "xp": "all",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "session_length": 3.0,
            "characters": "self",
        }

        game = service.create(data, admin_user.id, status="open", create_resources=True)

        assert game.role is None
        assert game.channel == "mock_channel_id"
        mock_discord.create_role.assert_not_called()
        # Channel is created with role_id=None (no player-role overwrite).
        _, kwargs = mock_discord.create_channel.call_args
        assert kwargs["role_id"] is None

    def test_silent_then_open_publish_reuses_channel(
        self, db_session, sample_game, mock_discord, direct_settings, oneshot_channel
    ):
        """Re-publishing a silently-opened game must reuse its existing channel.

        Regression (v1.7.0): in direct-permission mode ``game.role`` is always
        ``None``, so the old ``not game.role or not game.channel`` guard re-ran
        resource setup on the second publish. That raised ``SessionConflictError``
        (duplicate session) and the error path then deleted the live channel.
        """
        service = GameService(discord_service=mock_discord, settings_service=direct_settings)

        # First publish: open silently -> creates session + channel, no role.
        game = service.publish(sample_game.slug, silent=True, allow_past_date=True)
        channel_after_silent = game.channel
        assert channel_after_silent == "mock_channel_id"
        assert game.role is None
        assert game.msg_id is None
        mock_discord.create_channel.assert_called_once()

        # Second publish: open for real. Must reuse the existing resources.
        mock_discord.send_game_embed.return_value = "announce_msg"
        game = service.publish(sample_game.slug, silent=False)

        assert game.status == "open"
        assert game.channel == channel_after_silent
        assert game.msg_id == "announce_msg"
        # Setup must not run a second time...
        mock_discord.create_channel.assert_called_once()
        # ...and the live channel must never be deleted.
        mock_discord.delete_channel.assert_not_called()

    def test_register_player_grants_channel_permission(
        self, db_session, sample_game, regular_user, mock_discord, game_service
    ):
        """A roleless game grants access via a per-member channel overwrite."""
        sample_game.status = "open"
        sample_game.role = None
        sample_game.channel = "channel_123"
        db_session.commit()

        game_service.register_player(sample_game.slug, regular_user.id, force=False)

        mock_discord.set_channel_permission.assert_called_once_with(
            "channel_123", regular_user.id, PLAYER_ROLE_PERMISSION
        )
        mock_discord.add_role_to_user.assert_not_called()

    def test_unregister_player_revokes_channel_permission(
        self, db_session, sample_game, regular_user, mock_discord, game_service
    ):
        """A roleless game revokes the per-member channel overwrite on unregister."""
        sample_game.status = "open"
        sample_game.role = None
        sample_game.channel = "channel_123"
        sample_game.players.append(regular_user)
        db_session.commit()

        game_service.unregister_player(sample_game.slug, regular_user.id)

        mock_discord.delete_channel_permission.assert_called_once_with(
            "channel_123", regular_user.id
        )
        mock_discord.remove_role_from_user.assert_not_called()

    def test_cleanup_skips_role_deletion_when_no_role(self, db_session, sample_game, mock_discord):
        """Cleanup deletes the channel but no role for direct-permission games."""
        mock_channel_service = Mock()
        service = GameService(
            discord_service=mock_discord,
            channel_service=mock_channel_service,
        )
        sample_game.channel = "channel_123"
        sample_game.role = None

        service._cleanup_discord_resources(sample_game)

        mock_discord.delete_channel.assert_called_once_with("channel_123")
        mock_discord.delete_role.assert_not_called()

    def test_notify_players_role_mode(self, db_session, sample_game, mock_discord, game_service):
        """Notify in role mode mentions the dedicated role in the channel message."""
        sample_game.status = "open"
        sample_game.role = "role_123"
        sample_game.channel = "channel_123"
        db_session.commit()

        game_service.notify_players(
            sample_game.slug, "Rendez-vous ce soir", user_id=sample_game.gm_id
        )

        mock_discord.send_message.assert_called_once()
        args, kwargs = mock_discord.send_message.call_args
        content, channel = args[0], args[1]
        assert "<@&role_123>" in content
        assert "Rendez-vous ce soir" in content
        assert channel == "channel_123"
        assert kwargs["allowed_mentions"] == {"parse": ["users", "roles"]}

    def test_notify_players_direct_mode_mentions_each_player(
        self, db_session, sample_game, regular_user, mock_discord, game_service
    ):
        """Notify without a role mentions every registered player individually."""
        sample_game.status = "open"
        sample_game.role = None
        sample_game.channel = "channel_123"
        sample_game.players.append(regular_user)
        db_session.commit()

        game_service.notify_players(sample_game.slug, "Coucou", user_id=sample_game.gm_id)

        content = mock_discord.send_message.call_args[0][0]
        assert f"<@{regular_user.id}>" in content
        assert "<@&" not in content

    def test_notify_players_empty_message_raises(
        self, db_session, sample_game, mock_discord, game_service
    ):
        """An empty notification message is rejected before any Discord call."""
        sample_game.channel = "channel_123"
        db_session.commit()

        with pytest.raises(ValidationError):
            game_service.notify_players(sample_game.slug, "   ", user_id=sample_game.gm_id)

        mock_discord.send_message.assert_not_called()


class TestGetOpenPreview:
    """Tests for GameService.get_open_preview (dashboard open-games section)."""

    def _slugs(self, games):
        return {g.slug for g in games}

    def test_returns_open_games_only(self, db_session, admin_user, default_system, game_service):
        """The preview contains only open games; a draft never appears."""
        draft = GameFactory(
            db_session, status="draft", gm_id=admin_user.id, system_id=default_system.id
        )

        data = game_service.get_open_preview({})

        assert all(g.status == "open" for g in data["open_games"])
        assert draft.slug not in self._slugs(data["open_games"])

    def test_open_hidden_counts_overflow_past_limit(
        self, db_session, admin_user, default_system, game_service
    ):
        """open_hidden reports the overflow (and the list is capped) past the limit."""
        # Isolate this user's games via a fresh GM so other seeded games don't skew counts.
        gm = UserFactory(db_session)
        limit = game_service.settings_service.get_dashboard_open_limit()
        extra = 3
        for _ in range(limit + extra):
            GameFactory(db_session, status="open", gm_id=gm.id, system_id=default_system.id)

        # Restrict the count to this GM's games by filtering on gm in the search payload.
        games, total = game_service.repo.search(
            {"status": ["open"], "gm_id": gm.id}, page=1, per_page=limit
        )
        assert len(games) == limit
        assert max(total - len(games), 0) == extra
