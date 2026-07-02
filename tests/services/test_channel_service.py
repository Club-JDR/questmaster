from unittest.mock import MagicMock, patch

import pytest

from tests.constants import TEST_ONESHOT_CHANNEL_ID
from website.exceptions import NotFoundError, ValidationError
from website.models import Channel
from website.repositories.channel import ChannelRepository
from website.services.channel import ChannelService


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


class TestReconcileSizes:
    def test_corrects_drift_only(self, db_session):
        """Drifted sizes are corrected; in-sync ones are left untouched."""
        cat_a = MagicMock(id="A", size=3)
        cat_b = MagicMock(id="B", size=2)
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [cat_a, cat_b]
        service = ChannelService(repository=mock_repo)

        discord = MagicMock()
        discord.list_guild_channels.return_value = [
            {"type": 0, "parent_id": "A"},
            {"type": 0, "parent_id": "A"},  # A has 2 text children (drift: 3 -> 2)
            {"type": 0, "parent_id": "B"},
            {"type": 0, "parent_id": "B"},  # B has 2 (already correct)
            {"type": 2, "parent_id": "A"},  # voice child ignored
            {"type": 0, "parent_id": None},  # uncategorised ignored
            {"type": 4, "id": "A"},  # the category itself ignored
        ]

        corrections = service.reconcile_sizes(discord)

        assert cat_a.size == 2
        assert cat_b.size == 2
        assert corrections == [{"id": "A", "old": 3, "new": 2}]

    def test_zero_children_sets_zero(self, db_session):
        """A category with no children on Discord is reset to 0."""
        cat = MagicMock(id="A", size=4)
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [cat]
        service = ChannelService(repository=mock_repo)

        discord = MagicMock()
        discord.list_guild_channels.return_value = []

        corrections = service.reconcile_sizes(discord)

        assert cat.size == 0
        assert corrections == [{"id": "A", "old": 4, "new": 0}]


class TestCreateCategory:
    @patch("website.services.setting.SettingsService")
    def test_creates_and_registers(self, mock_settings_cls, db_session):
        """Templated name (emoji intact) is sent and a size-0 Channel stored."""
        mock_settings_cls.return_value.get_category_name_templates.return_value = {
            "campaign": "🎲 CAMPAGNES {n} 📖",
            "oneshot": "🎲 ONE SHOTS {n} 📖",
        }
        mock_repo = MagicMock()
        mock_repo.count_by_type.return_value = 2
        service = ChannelService(repository=mock_repo)

        discord = MagicMock()
        discord.create_category.return_value = {"id": "newcat123"}

        channel = service.create_category(discord, "campaign")

        discord.create_category.assert_called_once_with("🎲 CAMPAGNES 3 📖")
        mock_repo.add.assert_called_once()
        added = mock_repo.add.call_args[0][0]
        assert added.id == "newcat123"
        assert added.type == "campaign"
        assert added.size == 0
        assert channel.id == "newcat123"

    @patch("website.services.setting.SettingsService")
    def test_unknown_type_raises(self, mock_settings_cls, db_session):
        """An unknown game type is rejected before any Discord call."""
        mock_settings_cls.return_value.get_category_name_templates.return_value = {
            "campaign": "C {n}",
            "oneshot": "O {n}",
        }
        service = ChannelService(repository=MagicMock())
        discord = MagicMock()
        with pytest.raises(ValidationError):
            service.create_category(discord, "bogus")
        discord.create_category.assert_not_called()


class TestAutoProvisionIfFull:
    def test_creates_when_smallest_at_threshold(self, db_session):
        """Provisions when even the least-full category is at/above the threshold."""
        mock_repo = MagicMock()
        mock_repo.get_smallest_by_type.return_value = MagicMock(size=45)
        mock_repo.count_by_type.return_value = 1
        service = ChannelService(repository=mock_repo)

        discord = MagicMock()
        discord.create_category.return_value = {"id": "new"}

        assert service.auto_provision_if_full(discord, "oneshot") is not None
        discord.create_category.assert_called_once()

    def test_noop_when_below_threshold(self, db_session):
        """No provisioning when the smallest category has headroom."""
        mock_repo = MagicMock()
        mock_repo.get_smallest_by_type.return_value = MagicMock(size=10)
        service = ChannelService(repository=mock_repo)

        discord = MagicMock()
        assert service.auto_provision_if_full(discord, "oneshot") is None
        discord.create_category.assert_not_called()

    def test_bootstraps_when_no_category(self, db_session):
        """A type with no categories yet gets one provisioned."""
        mock_repo = MagicMock()
        mock_repo.get_smallest_by_type.return_value = None
        mock_repo.count_by_type.return_value = 0
        service = ChannelService(repository=mock_repo)

        discord = MagicMock()
        discord.create_category.return_value = {"id": "new"}

        assert service.auto_provision_if_full(discord, "campaign") is not None
        discord.create_category.assert_called_once()


class TestCountByType:
    def test_count_by_type(self, db_session):
        """count_by_type returns the per-type category count from the DB."""
        repo = ChannelRepository()
        assert repo.count_by_type("oneshot") >= 1
        assert repo.count_by_type("campaign") >= 1
