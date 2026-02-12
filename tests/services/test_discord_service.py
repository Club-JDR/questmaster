"""Tests for DiscordService."""

from unittest.mock import MagicMock, patch

import pytest

from website.services.discord import DiscordService


class TestDiscordService:
    """Test cases for DiscordService."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot."""
        return MagicMock()

    @pytest.fixture
    def discord_service(self, mock_bot):
        """Create DiscordService with injected mock bot."""
        return DiscordService(bot=mock_bot)

    # -------------------------------------------------------------------------
    # User operations
    # -------------------------------------------------------------------------

    def test_get_user(self, discord_service, mock_bot):
        """Test getting user data from Discord."""
        mock_bot.get_user.return_value = {"user": {"id": "123"}, "roles": []}

        result = discord_service.get_user("123")

        mock_bot.get_user.assert_called_once_with("123")
        assert result["user"]["id"] == "123"

    def test_add_role_to_user(self, discord_service, mock_bot):
        """Test adding role to user."""
        mock_bot.add_role_to_user.return_value = {}

        result = discord_service.add_role_to_user("user123", "role456")

        mock_bot.add_role_to_user.assert_called_once_with("user123", "role456")
        assert result == {}

    def test_remove_role_from_user(self, discord_service, mock_bot):
        """Test removing role from user."""
        mock_bot.remove_role_from_user.return_value = {}

        result = discord_service.remove_role_from_user("user123", "role456")

        mock_bot.remove_role_from_user.assert_called_once_with("user123", "role456")
        assert result == {}

    # -------------------------------------------------------------------------
    # Role operations
    # -------------------------------------------------------------------------

    def test_create_role(self, discord_service, mock_bot):
        """Test creating a Discord role."""
        mock_bot.create_role.return_value = {"id": "role123", "name": "TestRole"}

        result = discord_service.create_role("TestRole", "12345", 0xFF0000)

        mock_bot.create_role.assert_called_once_with("TestRole", "12345", 0xFF0000)
        assert result["id"] == "role123"

    def test_delete_role(self, discord_service, mock_bot):
        """Test deleting a Discord role."""
        mock_bot.delete_role.return_value = {}

        result = discord_service.delete_role("role123")

        mock_bot.delete_role.assert_called_once_with("role123")
        assert result == {}

    # -------------------------------------------------------------------------
    # Channel operations
    # -------------------------------------------------------------------------

    def test_create_channel(self, discord_service, mock_bot):
        """Test creating a Discord channel."""
        mock_bot.create_channel.return_value = {"id": "channel123"}

        result = discord_service.create_channel(
            name="test-channel",
            parent_id="category123",
            role_id="role456",
            gm_id="gm789",
        )

        mock_bot.create_channel.assert_called_once_with(
            "test-channel", "category123", "role456", "gm789"
        )
        assert result["id"] == "channel123"

    def test_get_channel(self, discord_service, mock_bot):
        """Test getting channel data."""
        mock_bot.get_channel.return_value = {"id": "channel123", "parent_id": "cat456"}

        result = discord_service.get_channel("channel123")

        mock_bot.get_channel.assert_called_once_with("channel123")
        assert result["parent_id"] == "cat456"

    def test_delete_channel(self, discord_service, mock_bot):
        """Test deleting a channel."""
        mock_bot.delete_channel.return_value = {}

        result = discord_service.delete_channel("channel123")

        mock_bot.delete_channel.assert_called_once_with("channel123")
        assert result == {}

    # -------------------------------------------------------------------------
    # Message operations
    # -------------------------------------------------------------------------

    def test_send_message(self, discord_service, mock_bot):
        """Test sending a plain message."""
        mock_bot.send_message.return_value = {"id": "msg123"}

        result = discord_service.send_message("Hello!", "channel123")

        mock_bot.send_message.assert_called_once_with("Hello!", "channel123")
        assert result["id"] == "msg123"

    def test_delete_message(self, discord_service, mock_bot):
        """Test deleting a message."""
        mock_bot.delete_message.return_value = {}

        result = discord_service.delete_message("msg123", "channel456")

        mock_bot.delete_message.assert_called_once_with("msg123", "channel456")
        assert result == {}

    def test_send_embed(self, discord_service, mock_bot):
        """Test sending an embed message."""
        mock_bot.send_embed_message.return_value = {"id": "msg123"}
        embed = {"title": "Test", "color": 0xFF0000}

        result = discord_service.send_embed(embed, "channel123")

        mock_bot.send_embed_message.assert_called_once_with(embed, "channel123")
        assert result["id"] == "msg123"

    def test_edit_embed(self, discord_service, mock_bot):
        """Test editing an embed message."""
        mock_bot.edit_embed_message.return_value = {"id": "msg123"}
        embed = {"title": "Updated", "color": 0x00FF00}

        result = discord_service.edit_embed("msg123", embed, "channel456")

        mock_bot.edit_embed_message.assert_called_once_with("msg123", embed, "channel456")
        assert result["id"] == "msg123"

    # -------------------------------------------------------------------------
    # Lazy loading bot
    # -------------------------------------------------------------------------

    def test_bot_lazy_loads_from_get_bot(self):
        """Test that bot is lazy-loaded from get_bot when not injected."""
        mock_global_bot = MagicMock()

        with patch("website.bot.get_bot", return_value=mock_global_bot):
            service = DiscordService()
            bot = service.bot
            assert bot == mock_global_bot

    def test_bot_raises_error_when_not_available(self):
        """Test that RuntimeError is raised when bot is not available."""
        with patch("website.bot.get_bot", return_value=None):
            service = DiscordService()
            service._bot = None

            with pytest.raises(RuntimeError, match="Discord bot not initialized"):
                _ = service.bot

    # -------------------------------------------------------------------------
    # Game embed operations
    # -------------------------------------------------------------------------

    def test_send_game_embed_new_annonce(self, discord_service, mock_bot, test_app):
        """Test sending a new game announcement embed."""
        with test_app.app_context():
            mock_game = MagicMock()
            mock_game.msg_id = None
            mock_game.name = "Test Game"
            mock_game.status = "open"
            mock_game.type = "oneshot"
            mock_game.gm = MagicMock(name="TestGM")
            mock_game.system = MagicMock(name="D&D 5e")
            mock_game.restriction = "all"
            mock_game.restriction_tags = None
            mock_game.special_event = None
            mock_game.date = MagicMock()
            mock_game.date.strftime.return_value = "2026-02-10"
            mock_game.length = "4h"
            mock_game.slug = "test-game"
            mock_game.img = "http://example.com/img.png"

            mock_bot.send_embed_message.return_value = {"id": "new_msg_123"}

            result = discord_service.send_game_embed(mock_game, embed_type="annonce")

            mock_bot.send_embed_message.assert_called_once()
            assert result == "new_msg_123"

    def test_send_game_embed_update_existing(self, discord_service, mock_bot, test_app):
        """Test updating an existing game announcement embed."""
        with test_app.app_context():
            mock_game = MagicMock()
            mock_game.msg_id = "existing_msg_456"
            mock_game.name = "Test Game"
            mock_game.status = "open"
            mock_game.type = "oneshot"
            mock_game.gm = MagicMock(name="TestGM")
            mock_game.system = MagicMock(name="D&D 5e")
            mock_game.restriction = "all"
            mock_game.restriction_tags = None
            mock_game.special_event = None
            mock_game.date = MagicMock()
            mock_game.date.strftime.return_value = "2026-02-10"
            mock_game.length = "4h"
            mock_game.slug = "test-game"
            mock_game.img = "http://example.com/img.png"

            mock_bot.edit_embed_message.return_value = {"id": "existing_msg_456"}

            result = discord_service.send_game_embed(mock_game, embed_type="annonce")

            mock_bot.edit_embed_message.assert_called_once()
            assert result == "existing_msg_456"

    def test_send_game_embed_unknown_type_raises(self, discord_service):
        """Test that unknown embed type raises ValueError."""
        mock_game = MagicMock()

        with pytest.raises(ValueError, match="Unknown embed type"):
            discord_service.send_game_embed(mock_game, embed_type="invalid_type")
