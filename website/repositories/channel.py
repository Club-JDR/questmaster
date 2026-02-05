from website.models import Channel
from website.repositories.base import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    model_class = Channel

    def get_smallest_by_type(self, type: str) -> Channel | None:
        return (
            self.session.query(Channel)
            .filter_by(type=type)
            .order_by(Channel.size)
            .first()
        )

    def increment_size(self, channel: Channel) -> None:
        channel.size += 1
        self.session.flush()

    def decrement_size(self, channel: Channel) -> None:
        channel.size = max(0, channel.size - 1)
        self.session.flush()
