"""Channel service for Discord category management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from website.exceptions import NotFoundError, ValidationError
from website.extensions import db
from website.models import Channel
from website.repositories.channel import ChannelRepository
from website.utils.logger import logger

if TYPE_CHECKING:
    from website.models import Game
    from website.services.discord import DiscordService


class ChannelService:
    """Service layer for Channel (Discord category) management.

    Handles category size tracking for Discord channel organization.
    """

    def __init__(self, repository=None):
        self.repo = repository or ChannelRepository()

    def get_all(self) -> list[Channel]:
        """Get all channel categories.

        Returns:
            List of Channel instances.
        """
        return self.repo.get_all()

    def get_by_id(self, channel_id: str) -> Channel:
        """Get a channel category by ID.

        Args:
            channel_id: Discord channel (category) ID.

        Returns:
            Channel instance.

        Raises:
            NotFoundError: If the channel does not exist.
        """
        channel = self.repo.get_by_id(channel_id)
        if not channel:
            raise NotFoundError(
                f"Channel with id {channel_id} not found",
                resource_type="Channel",
                resource_id=channel_id,
            )
        return channel

    def create(self, channel_id: str, type: str, size: int = 0) -> Channel:
        """Create a new channel category.

        Args:
            channel_id: Discord channel (category) ID.
            type: Game type served by this category (oneshot or campaign).
            size: Initial channel count. Defaults to 0.

        Returns:
            Created Channel instance.

        Raises:
            ValidationError: If a channel with this ID already exists.
        """
        if self.repo.get_by_id(channel_id):
            raise ValidationError("Channel id already exists.", field="id")
        channel = Channel(id=channel_id, type=type, size=size)
        self.repo.add(channel)
        db.session.commit()
        return channel

    def update(self, channel_id: str, data: dict) -> Channel:
        """Update an existing channel category.

        Args:
            channel_id: Discord channel (category) ID.
            data: Dictionary of fields to update.

        Returns:
            Updated Channel instance.
        """
        channel = self.repo.get_by_id_or_404(channel_id)
        channel.update_from_dict(data)
        db.session.commit()
        return channel

    def delete(self, channel_id: str) -> None:
        """Delete a channel category.

        Args:
            channel_id: Discord channel (category) ID.
        """
        channel = self.repo.get_by_id_or_404(channel_id)
        self.repo.delete(channel)
        db.session.commit()

    def get_category(self, game_type: str) -> Channel:
        """Get the smallest category for a game type.

        Args:
            game_type: Type of game (oneshot, campaign).

        Returns:
            Channel category with smallest size.

        Raises:
            NotFoundError: If no category found for type.
        """
        category = self.repo.get_smallest_by_type(game_type)
        if not category:
            raise NotFoundError(
                f"No channel category found for type '{game_type}'",
                resource_type="Channel",
            )
        return category

    def increment_size(self, channel: Channel) -> None:
        """Increment the channel count for a category.

        Args:
            channel: Channel category to increment.
        """
        self.repo.increment_size(channel)

    def adjust_category_size(self, discord_service: DiscordService, game: Game) -> None:
        """Decrement category size when a game channel is deleted.

        Args:
            discord_service: DiscordService instance for API calls.
            game: Game instance with channel to look up.
        """
        try:
            discord_channel = discord_service.get_channel(game.channel)
            parent_id = discord_channel.get("parent_id")
            if parent_id:
                category = self.repo.get_by_id(parent_id)
                if category:
                    self.repo.decrement_size(category)
                    db.session.commit()
                    logger.info(f"Decreased size of category {category.id} to {category.size}")
        except Exception as e:
            logger.warning(f"Failed to adjust category size for game {game.id}: {e}")
