"""Discord service for Discord API interactions.

This service wraps Discord API calls with dependency injection for testability.
It replaces the global singleton pattern previously used in website/bot.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from config.constants import (
    DISCORD_CHANNEL_TYPE_TEXT,
    DISCORD_ROLE_COUNT_CACHE_TIMEOUT,
    PLAYER_ROLE_PERMISSION,
)
from website.client.discord import Discord
from website.extensions import cache

if TYPE_CHECKING:
    from website.models import Game


class DiscordService:
    """Service layer for Discord API interactions.

    Provides a testable wrapper around the Discord API client. Uses dependency
    injection to allow mocking in tests.

    Attributes:
        bot: The underlying Discord API client instance.
    """

    def __init__(self, bot: Optional[Discord] = None):
        self._bot = bot

    @property
    def bot(self) -> Discord:
        """Get the Discord bot instance.

        Lazy-loads from the global singleton if not injected.

        Returns:
            Discord client instance.

        Raises:
            RuntimeError: If no bot instance is available.
        """
        if self._bot is None:
            from website.bot import get_bot

            self._bot = get_bot()
        if self._bot is None:
            raise RuntimeError("Discord bot not initialized")
        return self._bot

    # -------------------------------------------------------------------------
    # User operations
    # -------------------------------------------------------------------------

    def get_user(self, user_id: str) -> dict:
        """Fetch guild member data from Discord.

        Args:
            user_id: Discord user ID.

        Returns:
            Member data dictionary from Discord API.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.get_user(user_id)

    def add_role_to_user(self, user_id: str, role_id: str) -> dict:
        """Add a role to a user.

        Args:
            user_id: Discord user ID.
            role_id: Discord role ID.

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.add_role_to_user(user_id, role_id)

    def remove_role_from_user(self, user_id: str, role_id: str) -> dict:
        """Remove a role from a user.

        Args:
            user_id: Discord user ID.
            role_id: Discord role ID.

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.remove_role_from_user(user_id, role_id)

    # -------------------------------------------------------------------------
    # Role operations
    # -------------------------------------------------------------------------

    def create_role(
        self,
        name: str,
        permissions: str = PLAYER_ROLE_PERMISSION,
        color: int = 0,
    ) -> dict:
        """Create a Discord role.

        Args:
            name: Role name (will be sanitized).
            permissions: Permission bitfield string.
            color: Role color as integer.

        Returns:
            Created role data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.create_role(name, permissions, color)

    def get_role(self, role_id: str) -> dict:
        """Get a role by ID.

        Args:
            role_id: Discord role ID.

        Returns:
            Role data dictionary.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.get_role(role_id)

    def list_roles(self) -> list:
        """Return all roles defined in the guild.

        Returns:
            List of role dicts (each with at least ``id`` and ``name``).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.list_roles()

    def count_roles(self) -> int:
        """Count the roles currently defined in the guild.

        Returns:
            Number of guild roles (including the ``@everyone`` role).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return len(self.bot.list_roles())

    @cache.memoize(timeout=DISCORD_ROLE_COUNT_CACHE_TIMEOUT)
    def count_roles_cached(self) -> int:
        """Return the guild role count, cached to avoid frequent API calls.

        The admin settings page reads this on every load, so the value is cached
        rather than hitting the Discord API each time.

        Returns:
            Number of guild roles.

        Raises:
            DiscordAPIError: If the API request fails on a cache miss.
        """
        return self.count_roles()

    def delete_role(self, role_id: str) -> dict:
        """Delete a Discord role.

        Args:
            role_id: Discord role ID.

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.delete_role(role_id)

    # -------------------------------------------------------------------------
    # Channel operations
    # -------------------------------------------------------------------------

    def create_channel(
        self,
        name: str,
        parent_id: str,
        role_id: str | None,
        gm_id: str,
    ) -> dict:
        """Create a Discord text channel with permissions.

        Args:
            name: Channel name (will be sanitized).
            parent_id: Parent category ID.
            role_id: Player role ID for permission overwrites, or None to create
                the channel without a player-role overwrite (direct-permission mode).
            gm_id: GM user ID for permission overwrites.

        Returns:
            Created channel data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.create_channel(name, parent_id, role_id, gm_id)

    def create_category(self, name: str) -> dict:
        """Create a Discord category channel (name kept verbatim).

        Args:
            name: Display name for the category (emojis preserved).

        Returns:
            Created category data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.create_category(name)

    def list_guild_channels(self) -> list:
        """Return every channel in the guild.

        Returns:
            List of channel dicts as returned by the Discord API.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.list_guild_channels()

    def count_category_children(self, category_id: str) -> int:
        """Count the text channels currently parented to a category.

        Args:
            category_id: Discord category (parent) ID.

        Returns:
            Number of GUILD_TEXT channels whose ``parent_id`` is ``category_id``.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return sum(
            1
            for c in self.list_guild_channels()
            if c.get("parent_id") == category_id and c.get("type") == DISCORD_CHANNEL_TYPE_TEXT
        )

    def set_channel_permission(
        self, channel_id: str, target_id: str, allow: str, type_: int = 1
    ) -> dict:
        """Grant a member (or role) access to a channel via a permission overwrite.

        Args:
            channel_id: Channel to set the overwrite on.
            target_id: Member or role ID the overwrite applies to.
            allow: Allowed permission bitfield string.
            type_: Overwrite type (1 = member, 0 = role).

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.set_channel_permission(channel_id, target_id, allow, type_)

    def delete_channel_permission(self, channel_id: str, target_id: str) -> dict:
        """Remove a permission overwrite from a channel.

        Args:
            channel_id: Channel to remove the overwrite from.
            target_id: Member or role ID whose overwrite is removed.

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.delete_channel_permission(channel_id, target_id)

    def get_channel(self, channel_id: str) -> dict:
        """Get a channel by ID.

        Args:
            channel_id: Discord channel ID.

        Returns:
            Channel data dictionary.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.get_channel(channel_id)

    def delete_channel(self, channel_id: str) -> dict:
        """Delete a Discord channel.

        Args:
            channel_id: Discord channel ID.

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.delete_channel(channel_id)

    # -------------------------------------------------------------------------
    # Message operations
    # -------------------------------------------------------------------------

    def send_message(
        self,
        content: str,
        channel_id: str,
        allowed_mentions: dict | None = None,
        components: list | None = None,
    ) -> dict:
        """Send a plain text message to a channel.

        Args:
            content: Message content.
            channel_id: Target channel ID.
            allowed_mentions: Optional Discord ``allowed_mentions`` object controlling
                which mentions in ``content`` actually ping.
            components: Optional Discord ``components`` list (action rows of buttons).

        Returns:
            Created message data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.send_message(
            content, channel_id, allowed_mentions=allowed_mentions, components=components
        )

    def delete_message(self, message_id: str, channel_id: str) -> dict:
        """Delete a message.

        Args:
            message_id: Discord message ID.
            channel_id: Channel containing the message.

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.delete_message(message_id, channel_id)

    def send_embed(self, embed: dict, channel_id: str, components: list | None = None) -> dict:
        """Send an embed message to a channel.

        Args:
            embed: Embed data dictionary.
            channel_id: Target channel ID.
            components: Optional Discord ``components`` list (action rows of buttons).

        Returns:
            Created message data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.send_embed_message(embed, channel_id, components=components)

    def create_message(
        self,
        channel_id: str,
        *,
        content: str | None = None,
        embeds: list | None = None,
        components: list | None = None,
    ) -> dict:
        """Create a message combining content, embeds and/or buttons.

        Args:
            channel_id: Target channel ID.
            content: Plain-text body, or None to omit.
            embeds: List of embed dicts (Discord caps a message at 10), or None.
            components: Discord ``components`` list (action rows of buttons), or None.

        Returns:
            Created message data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.create_message(
            channel_id, content=content, embeds=embeds, components=components
        )

    def edit_message(
        self, message_id: str, content: str, channel_id: str, components: list | None = None
    ) -> dict:
        """Edit the text content of an existing plain message.

        Args:
            message_id: Message ID to edit.
            content: New message content.
            channel_id: Channel containing the message.
            components: Optional Discord ``components`` list. Pass ``[]`` to clear
                any existing buttons.

        Returns:
            Updated message data.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.edit_message(message_id, content, channel_id, components=components)

    def edit_embed(
        self, message_id: str, embed: dict, channel_id: str, components: list | None = None
    ) -> dict:
        """Edit an existing embed message.

        Args:
            message_id: Message ID to edit.
            embed: New embed data dictionary.
            channel_id: Channel containing the message.
            components: Optional Discord ``components`` list. Pass ``[]`` to clear
                any existing buttons.

        Returns:
            Updated message data.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.edit_embed_message(message_id, embed, channel_id, components=components)

    def update_message(
        self,
        message_id: str,
        channel_id: str,
        *,
        content: str | None = None,
        embeds: list | None = None,
        components: list | None = None,
    ) -> dict:
        """Edit a message's content, embeds and/or buttons.

        Any argument left as None is omitted (unchanged); pass an empty
        string/list to clear a field.

        Args:
            message_id: Message ID to edit.
            channel_id: Channel containing the message.
            content: New plain-text body (``""`` to clear), or None to leave as-is.
            embeds: New list of embed dicts (``[]`` to clear), or None.
            components: New ``components`` list (``[]`` to clear), or None.

        Returns:
            Updated message data.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.update_message(
            message_id, channel_id, content=content, embeds=embeds, components=components
        )

    def pin_message(self, message_id: str, channel_id: str) -> dict:
        """Pin a message to a channel.

        Args:
            message_id: Message ID to edit.
            channel_id: Target channel ID.

        Returns:
            API response (usually empty on success).

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.pin_message(message_id, channel_id)

    # -------------------------------------------------------------------------
    # Game embed operations (high-level)
    # -------------------------------------------------------------------------

    def send_game_embed(
        self,
        game: Game,
        embed_type: str = "annonce",
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        player: Optional[str] = None,
        old_start: str | datetime | None = None,
        old_end: str | datetime | None = None,
        alert_message: Optional[str] = None,
    ) -> str:
        """Send or update a Discord embed for a game event.

        This is a high-level method that builds and sends the appropriate embed
        based on the embed_type.

        Args:
            game: Game model instance.
            embed_type: Type of embed ('annonce', 'annonce_details', 'add-session',
                'edit-session', 'del-session', 'register', 'alert').
            start: Session start datetime (for session embeds).
            end: Session end datetime (for session embeds).
            player: Player user ID (for register/alert embeds).
            old_start: Previous session start (for edit-session).
            old_end: Previous session end (for edit-session).
            alert_message: Alert text (for alert embed).

        Returns:
            Discord message ID string.

        Raises:
            ValueError: If embed_type is unknown.
            DiscordAPIError: If the API request fails.
        """
        from website.utils.game_embeds import (
            build_add_session_embed,
            build_alert_embed,
            build_annonce_components,
            build_annonce_details_embed,
            build_annonce_embed,
            build_delete_session_embed,
            build_edit_session_embed,
            build_register_embed,
        )

        embed_builders = {
            "annonce": build_annonce_embed,
            "annonce_details": build_annonce_details_embed,
            "add-session": build_add_session_embed,
            "edit-session": build_edit_session_embed,
            "del-session": build_delete_session_embed,
            "register": build_register_embed,
            "alert": build_alert_embed,
        }

        if embed_type not in embed_builders:
            raise ValueError(f"Unknown embed type: {embed_type}")

        embed, target = embed_builders[embed_type](
            game,
            start=start,
            end=end,
            player=player,
            old_start=old_start,
            old_end=old_end,
            alert_message=alert_message,
        )

        # The announcement embed carries a link button to the game page (replacing
        # the old inline "Pour s'inscrire" URL field); other embeds have no buttons.
        components = build_annonce_components(game) if embed_type == "annonce" else None

        if embed_type == "annonce" and game.msg_id:
            response = self.edit_embed(game.msg_id, embed, target, components=components)
        else:
            response = self.send_embed(embed, target, components=components)

        return response["id"]
