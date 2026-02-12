import pytest

from tests.constants import TEST_ONESHOT_CHANNEL_ID
from website.models import Channel
from website.repositories.channel import ChannelRepository


class TestChannelRepository:
    def test_get_smallest_by_type_oneshot(self, db_session):
        repo = ChannelRepository()
        channel = repo.get_smallest_by_type("oneshot")
        assert channel is not None
        assert channel.type == "oneshot"

    def test_get_smallest_by_type_campaign(self, db_session):
        repo = ChannelRepository()
        channel = repo.get_smallest_by_type("campaign")
        assert channel is not None
        assert channel.type == "campaign"

    def test_get_smallest_by_type_invalid_enum_raises(self, db_session):
        repo = ChannelRepository()
        with pytest.raises(Exception):
            repo.get_smallest_by_type("nonexistent")

    def test_get_smallest_by_type_returns_smallest(self, db_session):
        repo = ChannelRepository()
        # Get all oneshot channels and find the minimum size
        all_oneshot = db_session.query(Channel).filter_by(type="oneshot").all()
        if len(all_oneshot) > 1:
            min_size = min(c.size for c in all_oneshot)
            result = repo.get_smallest_by_type("oneshot")
            assert result.size == min_size

    def test_increment_size(self, db_session):
        repo = ChannelRepository()
        channel = repo.get_smallest_by_type("oneshot")
        original_size = channel.size
        repo.increment_size(channel)
        assert channel.size == original_size + 1
        # Restore
        channel.size = original_size
        db_session.flush()

    def test_decrement_size(self, db_session):
        repo = ChannelRepository()
        channel = repo.get_smallest_by_type("oneshot")
        original_size = channel.size
        channel.size = 5
        db_session.flush()
        repo.decrement_size(channel)
        assert channel.size == 4
        # Restore
        channel.size = original_size
        db_session.flush()

    def test_decrement_size_floors_at_zero(self, db_session):
        repo = ChannelRepository()
        channel = repo.get_smallest_by_type("oneshot")
        original_size = channel.size
        channel.size = 0
        db_session.flush()
        repo.decrement_size(channel)
        assert channel.size == 0
        # Restore
        channel.size = original_size
        db_session.flush()

    def test_inherits_get_by_id(self, db_session):
        repo = ChannelRepository()
        channel = repo.get_by_id(TEST_ONESHOT_CHANNEL_ID)
        assert channel is not None
        assert channel.type == "oneshot"
