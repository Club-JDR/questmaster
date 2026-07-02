"""DiscordMessage repository for admin-sent Discord message data access."""

from website.models import DiscordMessage
from website.repositories.base import BaseRepository


class DiscordMessageRepository(BaseRepository[DiscordMessage]):
    """Repository for DiscordMessage entities."""

    model_class = DiscordMessage

    #: Columns matched by paginated list searches (embeds are cast to text so a
    #: search hits embed titles/descriptions stored in the JSON list).
    search_columns = [DiscordMessage.content, DiscordMessage.embeds]

    def base_query(self):
        """Return all messages ordered by channel, then send time (newest first).

        Ordering by channel keeps each channel's messages contiguous so the list
        view can group them by channel.

        Returns:
            A SQLAlchemy query over DiscordMessage.
        """
        return self.session.query(DiscordMessage).order_by(
            DiscordMessage.channel_label, DiscordMessage.sent_at.desc()
        )
