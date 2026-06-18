"""DiscordMessage repository for admin-sent Discord message data access."""

from website.models import DiscordMessage
from website.repositories.base import BaseRepository


class DiscordMessageRepository(BaseRepository[DiscordMessage]):
    """Repository for DiscordMessage entities."""

    model_class = DiscordMessage

    #: Columns matched by paginated list searches.
    search_columns = [DiscordMessage.title, DiscordMessage.content]

    def base_query(self):
        """Return all messages ordered by send time (most recent first).

        Returns:
            A SQLAlchemy query over DiscordMessage.
        """
        return self.session.query(DiscordMessage).order_by(DiscordMessage.sent_at.desc())
