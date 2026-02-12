"""Channel repository for Discord category data access."""

from website.models import Channel
from website.repositories.base import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    """Repository for Channel (Discord category) entities."""

    model_class = Channel

    def get_smallest_by_type(self, type: str) -> Channel | None:
        """Find the category with the fewest channels for a game type.

        Args:
            type: Game type (oneshot or campaign).

        Returns:
            Channel with smallest size, or None if no match.
        """
        return self.session.query(Channel).filter_by(type=type).order_by(Channel.size).first()

    def increment_size(self, channel: Channel) -> None:
        """Increment the channel count of a category.

        Args:
            channel: Channel entity to update.
        """
        channel.size += 1
        self.session.flush()

    def decrement_size(self, channel: Channel) -> None:
        """Decrement the channel count of a category (minimum 0).

        Args:
            channel: Channel entity to update.
        """
        channel.size = max(0, channel.size - 1)
        self.session.flush()
