"""Tests for GameService."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from website.exceptions import (
    NotFoundError,
    ValidationError,
    GameFullError,
    GameClosedError,
    DuplicateRegistrationError,
    DiscordAPIError,
)
from website.models import Game
from website.services.game import GameService

from tests.factories import GameFactory


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

        game = game_service.create(
            data, admin_user.id, status="draft", create_resources=False
        )

        assert game is not None
        assert game.slug.startswith("new-draft-game-par")
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

        game = game_service.create(
            data, admin_user.id, status="open", create_resources=True
        )

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

    def test_publish_game(
        self, db_session, sample_game, mock_discord, game_service, oneshot_channel
    ):
        mock_discord.send_game_embed.return_value = "msg_123456"

        game = game_service.publish(sample_game.slug, silent=False)

        assert game.status == "open"
        assert game.msg_id == "msg_123456"
        mock_discord.send_game_embed.assert_called()

    def test_publish_game_silent(
        self, db_session, sample_game, mock_discord, game_service, oneshot_channel
    ):
        game = game_service.publish(sample_game.slug, silent=True)

        assert game.status == "closed"
        assert game.msg_id is None
        mock_discord.send_game_embed.assert_called_once_with(
            game, embed_type="annonce_details"
        )

    def test_publish_already_published(self, db_session, sample_game, game_service):
        sample_game.msg_id = "existing_msg"
        db_session.commit()

        with pytest.raises(ValidationError, match="already published"):
            game_service.publish(sample_game.slug)

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

        game = game_service.register_player(
            sample_game.slug, regular_user.id, force=False
        )

        assert regular_user in game.players
        mock_discord.add_role_to_user.assert_called_once_with(
            regular_user.id, "role_123"
        )

    def test_register_player_duplicate(
        self, db_session, sample_game, regular_user, game_service
    ):
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

        game = game_service.register_player(
            sample_game.slug, regular_user.id, force=True
        )

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

        game = game_service.register_player(
            sample_game.slug, regular_user.id, force=False
        )

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
        mock_discord.remove_role_from_user.assert_called_once_with(
            regular_user.id, "role_123"
        )

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
        mock_discord.delete_channel.side_effect = DiscordAPIError("Channel not found", status_code=404)
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

    def test_award_game_trophies_skips_on_error(
        self, db_session, sample_game
    ):
        """Trophy award failure is logged but doesn't propagate."""
        mock_trophy_service = Mock()
        mock_trophy_service.award.side_effect = Exception("Trophy DB error")

        service = GameService(trophy_service=mock_trophy_service)

        sample_game.type = "oneshot"
        db_session.commit()

        # Should not raise — error is caught inside _award_game_trophies
        service._award_game_trophies(sample_game)

        mock_trophy_service.award.assert_called_once()

    def test_delete_game_message_logs_on_failure(
        self, db_session, sample_game, mock_discord
    ):
        """Discord message deletion failure is logged but doesn't propagate."""
        mock_discord.delete_message.side_effect = DiscordAPIError("Message not found", status_code=404)

        service = GameService(discord_service=mock_discord)

        sample_game.msg_id = "msg_to_delete"
        db_session.commit()

        # Should not raise
        service._delete_game_message(sample_game)

        mock_discord.delete_message.assert_called_once()
        # msg_id should NOT be cleared since deletion failed
        assert sample_game.msg_id == "msg_to_delete"

    def test_delete_game_message_skips_when_no_msg_id(
        self, db_session, sample_game, mock_discord
    ):
        """When game has no msg_id, deletion is skipped entirely."""
        service = GameService(discord_service=mock_discord)

        sample_game.msg_id = None

        service._delete_game_message(sample_game)

        mock_discord.delete_message.assert_not_called()

    def test_rollback_discord_resources_cleans_up(
        self, db_session, sample_game, mock_discord
    ):
        """Rollback deletes both channel and role when both exist."""
        service = GameService(discord_service=mock_discord)

        sample_game.channel = "channel_123"
        sample_game.role = "role_456"

        service._rollback_discord_resources(sample_game)

        mock_discord.delete_channel.assert_called_once_with("channel_123")
        mock_discord.delete_role.assert_called_once_with("role_456")
