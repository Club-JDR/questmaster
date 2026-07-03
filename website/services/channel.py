"""Channel service for Discord category management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config.constants import DISCORD_CHANNEL_TYPE_TEXT
from website.exceptions import NotFoundError, ValidationError
from website.extensions import db
from website.models import Channel
from website.repositories.base import Pagination
from website.repositories.channel import ChannelRepository
from website.utils.logger import logger, sanitize_log_value

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

    def list_paginated(
        self, page: int = 1, per_page: int = 25, search: str | None = None
    ) -> Pagination:
        """Get a paginated, optionally searched, list of channel categories.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against channel ID and type.

        Returns:
            Pagination result of Channel instances.
        """
        return self.repo.paginate(page=page, per_page=per_page, search=search)

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
        logger.info(
            f"Channel category {sanitize_log_value(channel_id)} registered "
            f"(type={sanitize_log_value(type)}, size={size})"
        )
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
        logger.info(f"Channel category {sanitize_log_value(channel_id)} updated")
        return channel

    def delete(self, channel_id: str) -> None:
        """Delete a channel category.

        Args:
            channel_id: Discord channel (category) ID.
        """
        channel = self.repo.get_by_id_or_404(channel_id)
        self.repo.delete(channel)
        db.session.commit()
        logger.info(f"Channel category {sanitize_log_value(channel_id)} deleted")

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

    def reconcile_sizes(self, discord_service: DiscordService) -> list[dict]:
        """Correct every tracked category's ``size`` from its real Discord channel count.

        Fetches the guild channel list once, counts GUILD_TEXT children per category,
        and updates any ``Channel.size`` that has drifted. Commits once when at least
        one size changed.

        Args:
            discord_service: DiscordService used to read the guild's channels.

        Returns:
            List of ``{"id", "old", "new"}`` dicts for each corrected category
            (empty if everything already matched).
        """
        channels = discord_service.list_guild_channels()
        counts: dict[str, int] = {}
        for c in channels:
            if c.get("type") == DISCORD_CHANNEL_TYPE_TEXT and c.get("parent_id"):
                counts[c["parent_id"]] = counts.get(c["parent_id"], 0) + 1

        corrections = []
        for category in self.repo.get_all():
            real = counts.get(category.id, 0)
            if category.size != real:
                corrections.append({"id": category.id, "old": category.size, "new": real})
                category.size = real
        if corrections:
            db.session.commit()
            logger.info(f"Reconciled {len(corrections)} category size(s): {corrections}")
        return corrections

    def create_category(self, discord_service: DiscordService, type: str) -> Channel:
        """Create a Discord category for a game type and register it.

        The category is named per the admin-configured templates with the next
        per-type sequence number, created on Discord, then stored locally with
        ``size=0``.

        Args:
            discord_service: DiscordService used to create the Discord category.
            type: Game type the category serves (``oneshot`` or ``campaign``).

        Returns:
            The created Channel (Discord category) record.

        Raises:
            ValidationError: If ``type`` is not a known game type.
        """
        from website.services.setting import SettingsService

        templates = SettingsService().get_category_name_templates()
        if type not in templates:
            raise ValidationError("Unknown game type.", field="type")
        next_n = self.repo.count_by_type(type) + 1
        name = templates[type].format(n=next_n)
        discord_id = discord_service.create_category(name)["id"]
        channel = Channel(id=discord_id, type=type, size=0)
        self.repo.add(channel)
        db.session.commit()
        logger.info(f"Created Discord category '{name}' (id={discord_id}, type={type})")
        return channel

    def auto_provision_if_full(self, discord_service: DiscordService, type: str) -> Channel | None:
        """Create a new category for ``type`` when its least-full category is near the cap.

        Reads the smallest category for the type; if even that one is at/above the
        admin-configured auto-provision threshold (so every category of the type is
        near full), provisions a fresh one. Also bootstraps a category for a type
        that has none yet. A no-op otherwise.

        Args:
            discord_service: DiscordService used to create the category.
            type: Game type to check.

        Returns:
            The newly created Channel, or ``None`` when no provisioning was needed.
        """
        from website.services.setting import SettingsService

        threshold = SettingsService().get_category_auto_threshold()
        smallest = self.repo.get_smallest_by_type(type)
        if smallest is None or smallest.size >= threshold:
            return self.create_category(discord_service, type)
        return None

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
