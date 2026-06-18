"""Service for composing, sending and editing admin Discord messages.

Wraps :class:`DiscordService` for the actual Discord API calls and persists a
:class:`DiscordMessage` record for each sent message so it can be edited later.
Target channels are resolved from the settings allowlist (see
:class:`SettingsService`), never from raw user input.
"""

from __future__ import annotations

from website.exceptions import DiscordAPIError, NotFoundError, ValidationError
from website.extensions import db
from website.models import DiscordMessage
from website.repositories.base import Pagination
from website.repositories.discord_message import DiscordMessageRepository
from website.services.discord import DiscordService
from website.services.setting import SettingsService
from website.utils.logger import logger


class DiscordMessageService:
    """Service layer for admin-authored Discord messages.

    Owns the transaction boundary: a ``DiscordMessage`` row is only persisted
    once the Discord API call succeeds (Discord first, then database).
    """

    def __init__(
        self,
        repository: DiscordMessageRepository | None = None,
        discord_service: DiscordService | None = None,
        settings_service: SettingsService | None = None,
    ):
        self.repo = repository or DiscordMessageRepository()
        self.discord = discord_service or DiscordService()
        self.settings = settings_service or SettingsService()

    def list_paginated(
        self, page: int = 1, per_page: int = 25, search: str | None = None
    ) -> Pagination:
        """Get a paginated, optionally searched, list of sent messages.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against title and content.

        Returns:
            Pagination result of DiscordMessage instances.
        """
        return self.repo.paginate(page=page, per_page=per_page, search=search)

    def get_post_channels(self) -> list[dict]:
        """Return the configured channels an admin may post into.

        Returns:
            List of dicts with ``key``, ``label`` and ``channel_id``.
        """
        return self.settings.get_post_channels()

    def get_by_id(self, message_id: int) -> DiscordMessage:
        """Get a stored message by ID.

        Args:
            message_id: DiscordMessage primary key.

        Returns:
            DiscordMessage instance.

        Raises:
            NotFoundError: If the message does not exist.
        """
        message = self.repo.get_by_id(message_id)
        if message is None:
            raise NotFoundError(
                f"DiscordMessage with id {message_id} not found",
                resource_type="DiscordMessage",
                resource_id=message_id,
            )
        return message

    def _resolve_channel(self, channel_id: str) -> str:
        """Validate that a Discord channel ID is a configured postable channel.

        Args:
            channel_id: Discord channel ID submitted by the form.

        Returns:
            The validated Discord channel ID.

        Raises:
            ValidationError: If the ID is not a configured postable channel.
        """
        if not channel_id or not self.settings.is_post_channel(channel_id):
            raise ValidationError("Unknown or unconfigured channel.", field="channel")
        return channel_id

    @staticmethod
    def _build_embed(data: dict) -> dict:
        """Build a Discord embed payload from compose-form fields.

        Args:
            data: Dict with optional ``title``, ``description``, ``color``,
                ``footer`` and ``image_url`` keys.

        Returns:
            A Discord embed dict containing only the provided fields.
        """
        embed: dict = {}
        if data.get("title"):
            embed["title"] = data["title"]
        if data.get("description"):
            embed["description"] = data["description"]
        if data.get("color") is not None:
            embed["color"] = data["color"]
        if data.get("footer"):
            embed["footer"] = {"text": data["footer"]}
        if data.get("image_url"):
            embed["image"] = {"url": data["image_url"]}
        return embed

    def send(self, channel_id: str, msg_type: str, data: dict) -> DiscordMessage:
        """Send a new message to Discord and persist it.

        The Discord call happens first; the ``DiscordMessage`` row is only
        created once Discord confirms the send (returning a message ID).

        Args:
            channel_id: Discord channel ID identifying the target channel; must
                be one of the configured postable channels.
            msg_type: ``"plain"`` or ``"embed"``.
            data: Field values (``content`` for plain; ``title``, ``description``,
                ``color``, ``footer``, ``image_url`` for embeds).

        Returns:
            The persisted DiscordMessage instance.

        Raises:
            ValidationError: If the channel or message type is invalid, or a
                plain message has no content.
            DiscordAPIError: If the Discord API request fails (nothing persisted).
        """
        channel_id = self._resolve_channel(channel_id)
        channel_label = self.settings.get_post_channel_label(channel_id)

        if msg_type == DiscordMessage.TYPE_PLAIN:
            content = (data.get("content") or "").strip()
            if not content:
                raise ValidationError("Message content is required.", field="content")
            response = self.discord.send_message(content, channel_id)
        elif msg_type == DiscordMessage.TYPE_EMBED:
            embed = self._build_embed(data)
            if not embed:
                raise ValidationError("Embed must have at least one field.", field="title")
            response = self.discord.send_embed(embed, channel_id)
        else:
            raise ValidationError("Invalid message type.", field="type")

        message = DiscordMessage(
            discord_msg_id=response["id"],
            channel_id=channel_id,
            channel_label=channel_label,
            type=msg_type,
            content=data.get("content") if msg_type == DiscordMessage.TYPE_PLAIN else None,
            title=data.get("title") if msg_type == DiscordMessage.TYPE_EMBED else None,
            description=data.get("description") if msg_type == DiscordMessage.TYPE_EMBED else None,
            color=data.get("color") if msg_type == DiscordMessage.TYPE_EMBED else None,
            footer=data.get("footer") if msg_type == DiscordMessage.TYPE_EMBED else None,
            image_url=data.get("image_url") if msg_type == DiscordMessage.TYPE_EMBED else None,
        )
        self.repo.add(message)
        db.session.commit()
        logger.info(f"Admin Discord message {message.discord_msg_id} sent to {channel_id}")
        return message

    def edit(self, message_id: int, data: dict) -> DiscordMessage:
        """Edit a previously-sent message on Discord, then update the record.

        The channel and type cannot change (Discord messages cannot move
        channels). The Discord edit happens first; the stored row is only
        updated once Discord confirms success.

        Args:
            message_id: DiscordMessage primary key.
            data: New field values (same shape as :meth:`send`).

        Returns:
            The updated DiscordMessage instance.

        Raises:
            NotFoundError: If the message does not exist.
            ValidationError: If a plain message is edited to empty content.
            DiscordAPIError: If the Discord API request fails (nothing updated).
        """
        message = self.get_by_id(message_id)

        if message.type == DiscordMessage.TYPE_PLAIN:
            content = (data.get("content") or "").strip()
            if not content:
                raise ValidationError("Message content is required.", field="content")
            self.discord.edit_message(message.discord_msg_id, content, message.channel_id)
            message.content = data.get("content")
        else:
            embed = self._build_embed(data)
            if not embed:
                raise ValidationError("Embed must have at least one field.", field="title")
            self.discord.edit_embed(message.discord_msg_id, embed, message.channel_id)
            message.title = data.get("title")
            message.description = data.get("description")
            message.color = data.get("color")
            message.footer = data.get("footer")
            message.image_url = data.get("image_url")

        db.session.commit()
        logger.info(f"Admin Discord message {message.discord_msg_id} edited")
        return message

    def delete(self, message_id: int) -> None:
        """Delete a sent message from Discord and remove its stored record.

        The Discord deletion is best-effort: if it fails (e.g. the message was
        already removed on Discord), the stored record is removed anyway so the
        admin list stays consistent.

        Args:
            message_id: DiscordMessage primary key.

        Raises:
            NotFoundError: If the message does not exist.
        """
        message = self.get_by_id(message_id)
        try:
            self.discord.delete_message(message.discord_msg_id, message.channel_id)
        except DiscordAPIError as e:
            logger.warning(f"Failed to delete Discord message {message.discord_msg_id}: {e}")
        self.repo.delete(message)
        db.session.commit()
        logger.info(f"Admin Discord message {message.discord_msg_id} deleted")
