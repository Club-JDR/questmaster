import pytest
from unittest.mock import MagicMock
from website.models import Channel
from website.services.channel import ChannelService
from website.exceptions import NotFoundError

from tests.constants import TEST_ONESHOT_CHANNEL_ID


class TestChannelService:
    def test_get_category_oneshot(self, db_session):
        service = ChannelService()
        category = service.get_category("oneshot")
        assert category is not None
        assert category.type == "oneshot"

    def test_get_category_campaign(self, db_session):
        service = ChannelService()
        category = service.get_category("campaign")
        assert category is not None
        assert category.type == "campaign"

    def test_get_category_not_found(self, db_session):
        mock_repo = MagicMock()
        mock_repo.get_smallest_by_type.return_value = None
        service = ChannelService(repository=mock_repo)
        with pytest.raises(NotFoundError):
            service.get_category("oneshot")

    def test_increment_size(self, db_session):
        service = ChannelService()
        channel = db_session.get(Channel, TEST_ONESHOT_CHANNEL_ID)
        original_size = channel.size
        service.increment_size(channel)
        assert channel.size == original_size + 1
        # Restore
        channel.size = original_size
        db_session.flush()

    def test_adjust_category_size(self, db_session):
        service = ChannelService()
        channel = db_session.get(Channel, TEST_ONESHOT_CHANNEL_ID)
        original_size = channel.size

        # Set up a known size
        channel.size = 5
        db_session.commit()

        # Mock the bot to return the channel's parent_id
        mock_bot = MagicMock()
        mock_bot.get_channel.return_value = {"parent_id": channel.id}

        mock_game = MagicMock()
        mock_game.channel = "fake-discord-channel-id"
        mock_game.id = 999

        service.adjust_category_size(mock_bot, mock_game)

        refreshed = db_session.get(Channel, channel.id)
        assert refreshed.size == 4

        # Restore
        channel.size = original_size
        db_session.commit()

    def test_adjust_category_size_handles_errors(self, db_session):
        service = ChannelService()

        mock_bot = MagicMock()
        mock_bot.get_channel.side_effect = Exception("Discord error")

        mock_game = MagicMock()
        mock_game.channel = "fake-channel"
        mock_game.id = 999

        # Should not raise — errors are logged and swallowed
        service.adjust_category_size(mock_bot, mock_game)
