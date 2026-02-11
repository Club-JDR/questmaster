"""Discord service for Discord API interactions.

This service wraps Discord API calls with dependency injection for testability.
It replaces the global singleton pattern previously used in website/bot.py.
"""

from typing import Optional

from config.constants import PLAYER_ROLE_PERMISSION
from website.client.discord import Discord


class DiscordService:
    """Service layer for Discord API interactions.

    Provides a testable wrapper around the Discord API client. Uses dependency
    injection to allow mocking in tests.

    Attributes:
        bot: The underlying Discord API client instance.
    """

    def __init__(self, bot: Optional[Discord] = None):
        """Initialize DiscordService.

        Args:
            bot: Optional Discord client instance. If not provided, will use
                the global bot instance from get_bot().
        """
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
        role_id: str,
        gm_id: str,
    ) -> dict:
        """Create a Discord text channel with permissions.

        Args:
            name: Channel name (will be sanitized).
            parent_id: Parent category ID.
            role_id: Player role ID for permission overwrites.
            gm_id: GM user ID for permission overwrites.

        Returns:
            Created channel data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.create_channel(name, parent_id, role_id, gm_id)

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

    def send_message(self, content: str, channel_id: str) -> dict:
        """Send a plain text message to a channel.

        Args:
            content: Message content.
            channel_id: Target channel ID.

        Returns:
            Created message data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.send_message(content, channel_id)

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

    def send_embed(self, embed: dict, channel_id: str) -> dict:
        """Send an embed message to a channel.

        Args:
            embed: Embed data dictionary.
            channel_id: Target channel ID.

        Returns:
            Created message data including 'id'.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.send_embed_message(embed, channel_id)

    def edit_embed(self, message_id: str, embed: dict, channel_id: str) -> dict:
        """Edit an existing embed message.

        Args:
            message_id: Message ID to edit.
            embed: New embed data dictionary.
            channel_id: Channel containing the message.

        Returns:
            Updated message data.

        Raises:
            DiscordAPIError: If the API request fails.
        """
        return self.bot.edit_embed_message(message_id, embed, channel_id)

    # -------------------------------------------------------------------------
    # Game embed operations (high-level)
    # -------------------------------------------------------------------------

    def send_game_embed(
        self,
        game,
        embed_type: str = "annonce",
        start=None,
        end=None,
        player=None,
        old_start=None,
        old_end=None,
        alert_message=None,
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
            build_annonce_embed,
            build_annonce_details_embed,
            build_add_session_embed,
            build_edit_session_embed,
            build_delete_session_embed,
            build_register_embed,
            build_alert_embed,
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
            game, start, end, player, old_start, old_end, alert_message
        )

        if embed_type == "annonce" and game.msg_id:
            response = self.edit_embed(game.msg_id, embed, target)
        else:
            response = self.send_embed(embed, target)

        return response["id"]
