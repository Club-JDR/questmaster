from sqlalchemy.exc import SQLAlchemyError

from website.extensions import db
from website.models import Channel
from website.exceptions import NotFoundError
from website.repositories.channel import ChannelRepository
from website.utils.logger import logger


class ChannelService:
    def __init__(self, repository=None):
        self.repo = repository or ChannelRepository()

    def get_category(self, game_type: str) -> Channel:
        category = self.repo.get_smallest_by_type(game_type)
        if not category:
            raise NotFoundError(
                f"No channel category found for type '{game_type}'",
                resource_type="Channel",
            )
        return category

    def increment_size(self, channel: Channel) -> None:
        self.repo.increment_size(channel)

    def adjust_category_size(self, bot, game) -> None:
        try:
            discord_channel = bot.get_channel(game.channel)
            parent_id = discord_channel.get("parent_id")
            if parent_id:
                category = self.repo.get_by_id(parent_id)
                if category:
                    self.repo.decrement_size(category)
                    db.session.commit()
                    logger.info(
                        f"Decreased size of category {category.id} to {category.size}"
                    )
        except (SQLAlchemyError, Exception) as e:
            logger.warning(
                f"Failed to adjust category size for game {game.id}: {e}"
            )
