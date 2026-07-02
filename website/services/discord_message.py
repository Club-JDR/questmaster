"""Service for composing, sending and editing admin Discord messages.

Wraps :class:`DiscordService` for the actual Discord API calls and persists a
:class:`DiscordMessage` record for each sent message so it can be edited later.
Target channels are resolved from the settings allowlist (see
:class:`SettingsService`), never from raw user input.
"""

from __future__ import annotations

from config.constants import DISCORD_EMBED_LIMIT
from website.exceptions import DiscordAPIError, NotFoundError, ValidationError
from website.extensions import db
from website.models import DiscordMessage
from website.repositories.base import Pagination
from website.repositories.discord_message import DiscordMessageRepository
from website.services.discord import DiscordService
from website.services.setting import SettingsService
from website.utils.discord_components import build_link_button_rows, clean_link_buttons
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
        """Build a Discord embed payload from a single embed's fields.

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

    @staticmethod
    def _clean_embeds(embeds_data: list[dict]) -> list[dict]:
        """Normalise embed blocks, dropping the visually-empty ones.

        A block counts as empty (and is dropped) when it has no title,
        description, footer or image — a colour alone does not make an embed.

        Args:
            embeds_data: List of raw embed field dicts from the compose form.

        Returns:
            A list of cleaned embed dicts (at most ``EMBED_LIMIT`` items), each
            keeping only the standard embed field keys.
        """
        cleaned: list[dict] = []
        for embed in embeds_data or []:
            block = {
                "title": (embed.get("title") or "").strip() or None,
                "description": (embed.get("description") or "").strip() or None,
                "color": embed.get("color"),
                "footer": (embed.get("footer") or "").strip() or None,
                "image_url": (embed.get("image_url") or "").strip() or None,
            }
            if block["title"] or block["description"] or block["footer"] or block["image_url"]:
                cleaned.append(block)
        return cleaned

    @classmethod
    def _build_embeds(cls, embeds_data: list[dict]) -> list[dict]:
        """Build Discord embed payloads from cleaned embed blocks.

        Args:
            embeds_data: Cleaned embed dicts (see :meth:`_clean_embeds`).

        Returns:
            A list of Discord embed dicts.
        """
        return [cls._build_embed(embed) for embed in embeds_data]

    def _prepare(self, data: dict) -> dict:
        """Validate compose-form data and shape it for sending and persistence.

        A message must carry plain content, at least one embed, or both. Buttons
        are optional on any message.

        Args:
            data: Field values (``content`` plain text, an ``embeds`` list and a
                ``buttons`` list, all optional).

        Returns:
            Dict with ``content`` (str or None), ``embeds`` (cleaned list),
            ``buttons`` (cleaned list) and ``components`` (Discord button rows).

        Raises:
            ValidationError: If the message has neither content nor an embed, has
                too many embeds, or a button is malformed.
        """
        content = (data.get("content") or "").strip() or None
        embeds = self._clean_embeds(data.get("embeds") or [])
        buttons = clean_link_buttons(data.get("buttons") or [])

        if not content and not embeds:
            raise ValidationError(
                "A message must have content or at least one embed.", field="content"
            )
        if len(embeds) > DISCORD_EMBED_LIMIT:
            raise ValidationError(
                f"A message can have at most {DISCORD_EMBED_LIMIT} embeds.", field="embed_title"
            )

        return {
            "content": content,
            "embeds": embeds,
            "buttons": buttons,
            "components": build_link_button_rows(buttons),
        }

    def send(self, channel_id: str, data: dict) -> DiscordMessage:
        """Send a new message to Discord and persist it.

        The Discord call happens first; the ``DiscordMessage`` row is only
        created once Discord confirms the send (returning a message ID).

        Args:
            channel_id: Discord channel ID identifying the target channel; must
                be one of the configured postable channels.
            data: Field values — ``content``, an ``embeds`` list and a ``buttons``
                list, all optional (but at least content or one embed is required).

        Returns:
            The persisted DiscordMessage instance.

        Raises:
            ValidationError: If the channel is invalid, the message has no
                content/embed, or a button is malformed.
            DiscordAPIError: If the Discord API request fails (nothing persisted).
        """
        channel_id = self._resolve_channel(channel_id)
        channel_label = self.settings.get_post_channel_label(channel_id)
        prepared = self._prepare(data)

        response = self.discord.create_message(
            channel_id,
            content=prepared["content"],
            embeds=self._build_embeds(prepared["embeds"]) or None,
            components=prepared["components"],
        )

        message = DiscordMessage(
            discord_msg_id=response["id"],
            channel_id=channel_id,
            channel_label=channel_label,
            content=prepared["content"],
            embeds=prepared["embeds"] or None,
            buttons=prepared["buttons"] or None,
        )
        self.repo.add(message)
        db.session.commit()
        logger.info(f"Admin Discord message {message.discord_msg_id} sent to {channel_id}")
        return message

    def edit(self, message_id: int, channel_id: str, data: dict) -> DiscordMessage:
        """Edit a previously-sent message on Discord, then update the record.

        The Discord edit happens first; the stored row is only updated once
        Discord confirms success. Empty content/embeds/buttons clear those parts.
        Changing the channel re-sends the message to the new channel and deletes
        the old one (Discord cannot move a message between channels).

        Args:
            message_id: DiscordMessage primary key.
            channel_id: Target channel ID (may differ from the original); must be
                a configured postable channel.
            data: New field values (same shape as :meth:`send`).

        Returns:
            The updated DiscordMessage instance.

        Raises:
            NotFoundError: If the message does not exist.
            ValidationError: If the channel is invalid, the edited message has no
                content/embed, or a button is malformed.
            DiscordAPIError: If the Discord API request fails (nothing updated).
        """
        message = self.get_by_id(message_id)
        new_channel = self._resolve_channel(channel_id)
        prepared = self._prepare(data)
        embeds = self._build_embeds(prepared["embeds"])

        if new_channel != message.channel_id:
            response = self.discord.create_message(
                new_channel,
                content=prepared["content"],
                embeds=embeds or None,
                components=prepared["components"],
            )
            try:
                self.discord.delete_message(message.discord_msg_id, message.channel_id)
            except DiscordAPIError as e:
                logger.warning(
                    f"Failed to delete old message {message.discord_msg_id} after move: {e}"
                )
            message.discord_msg_id = response["id"]
            message.channel_id = new_channel
            message.channel_label = self.settings.get_post_channel_label(new_channel)
        else:
            self.discord.update_message(
                message.discord_msg_id,
                message.channel_id,
                content=prepared["content"] or "",
                embeds=embeds,
                components=prepared["components"],
            )

        message.content = prepared["content"]
        message.embeds = prepared["embeds"] or None
        message.buttons = prepared["buttons"] or None
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
