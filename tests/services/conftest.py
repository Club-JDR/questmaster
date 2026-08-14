"""Shared fixtures for service tests."""

from unittest.mock import Mock

import pytest

from tests.factories import GameFactory
from website.models import Channel
from website.services.discord import DiscordService
from website.services.game import GameService


@pytest.fixture
def mock_discord():
    """Provide a mocked DiscordService for service tests."""
    discord = Mock(spec=DiscordService)
    discord.create_role = Mock(return_value={"id": "mock_role_id"})
    discord.create_channel = Mock(return_value={"id": "mock_channel_id"})
    discord.delete_role = Mock()
    discord.delete_channel = Mock()
    discord.add_role_to_user = Mock()
    discord.remove_role_from_user = Mock()
    discord.delete_message = Mock()
    discord.send_game_embed = Mock(return_value="mock_msg_id")
    discord.get_channel = Mock(return_value={"parent_id": "mock_category_id"})
    return discord


@pytest.fixture
def game_service(mock_discord):
    """Provide a GameService with mocked Discord dependency."""
    return GameService(discord_service=mock_discord)


@pytest.fixture
def sample_game(db_session, admin_user, default_system):
    """Create a draft game for service testing."""
    return GameFactory(
        db_session,
        gm_id=admin_user.id,
        system_id=default_system.id,
    )


@pytest.fixture
def isolated_channel_categories(db_session, oneshot_channel, campaign_channel):
    """Make oneshot_channel/campaign_channel the smallest of their type.

    get_category() picks the smallest category per type, and the shared dev
    DB may hold other categories with arbitrary sizes (or even a drifted
    `type` on these two rows themselves). Rolled back with the rest of the
    test, so nothing here is persisted.
    """
    db_session.query(Channel).filter(
        Channel.type.in_(["oneshot", "campaign"]),
        Channel.id.notin_([oneshot_channel.id, campaign_channel.id]),
    ).update({Channel.size: 9999}, synchronize_session=False)
    oneshot_channel.type = "oneshot"
    oneshot_channel.size = 0
    campaign_channel.type = "campaign"
    campaign_channel.size = 0
    db_session.commit()
