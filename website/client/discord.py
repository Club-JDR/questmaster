"""Discord API client for low-level HTTP operations.

This module provides the low-level Discord API client with HTTP request handling,
rate limiting, and retry logic. Business logic should use DiscordService instead.
"""

import time

import requests
from unidecode import unidecode

from config.constants import (
    DISCORD_API_BASE_URL,
    DISCORD_CHANNEL_TYPE_CATEGORY,
    GM_ROLE_PERMISSION,
    PLAYER_ROLE_PERMISSION,
)
from website.exceptions import DiscordAPIError
from website.utils.logger import logger


class Discord:
    """Low-level Discord API client.

    Handles HTTP requests to the Discord API with retry logic and rate limiting.
    For business logic, use DiscordService which wraps this client.

    Attributes:
        guild_id: The Discord guild (server) ID.
        authorization: The bot token for authentication.
        headers: HTTP headers for API requests.
    """

    def __init__(self, guild_id, bot_token):
        self.guild_id = guild_id
        self.authorization = bot_token
        self.headers = self._make_headers(self.authorization)

    def _make_headers(self, authorization=""):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "authorization": f"Bot {authorization}",
        }
        return headers

    def _request(
        self,
        method,
        endpoint,
        *,
        json=None,
        params=None,
        reason=None,
        max_retries=3,
    ):
        """Generic helper for all HTTP requests with retry + error handling."""
        url = f"{DISCORD_API_BASE_URL}{endpoint}"
        headers = dict(self.headers)
        if reason:
            headers["X-Audit-Log-Reason"] = reason

        for _ in range(max_retries):
            r = requests.request(method, url, headers=headers, json=json, params=params)

            # Handle rate limiting (HTTP 429)
            if r.status_code == 429:
                data = r.json()
                retry_after = data.get("retry_after", 1)
                logger.warning("Rate limited by Discord. Retrying after %.2f s...", retry_after)
                time.sleep(float(retry_after))
                continue

            # Handle non-success codes
            if not r.ok:
                try:
                    err_json = r.json()
                except Exception:
                    err_json = {"message": r.text}
                raise DiscordAPIError(
                    err_json.get("message", "Unknown error"),
                    status_code=r.status_code,
                    response=err_json,
                )

            # Some endpoints return 204 No Content
            if r.status_code == 204 or not r.content:
                return {}

            return r.json()

        raise DiscordAPIError("Exceeded retry attempts", status_code=429)

    def get_user(self, user_id: str) -> dict:
        """Fetch a guild member's data from Discord.

        Args:
            user_id: Discord user ID.

        Returns:
            Dict with member data including user, nick, and roles.
        """
        return self._request(endpoint=f"/guilds/{self.guild_id}/members/{user_id}", method="GET")

    def send_message(
        self,
        content: str,
        channel_id: str,
        allowed_mentions: dict | None = None,
        components: list | None = None,
    ) -> dict:
        """Send a text message to a Discord channel.

        Args:
            content: Message content string.
            channel_id: Target channel ID.
            allowed_mentions: Optional Discord ``allowed_mentions`` object controlling
                which mentions in ``content`` actually ping (e.g.
                ``{"parse": ["users", "roles"]}``).
            components: Optional Discord ``components`` list (action rows of buttons).

        Returns:
            Dict with the created message data.
        """
        payload = {
            "content": content,
        }
        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions
        if components is not None:
            payload["components"] = components
        return self._request(
            endpoint=f"/channels/{channel_id}/messages", method="POST", json=payload
        )

    def delete_message(self, msg_id: str, channel_id: str) -> dict:
        """Delete a message from a Discord channel.

        Args:
            msg_id: Message ID to delete.
            channel_id: Channel containing the message.
        """
        return self._request(endpoint=f"/channels/{channel_id}/messages/{msg_id}", method="DELETE")

    def create_message(
        self,
        channel_id: str,
        *,
        content: str | None = None,
        embeds: list | None = None,
        components: list | None = None,
    ) -> dict:
        """Create a message with any combination of content, embeds and buttons.

        Args:
            channel_id: Target channel ID.
            content: Plain-text body, or None to omit.
            embeds: List of embed dicts (Discord caps a message at 10), or None.
            components: Discord ``components`` list (action rows of buttons), or None.

        Returns:
            Dict with the created message data.
        """
        payload: dict = {}
        if content is not None:
            payload["content"] = content
        if embeds is not None:
            payload["embeds"] = embeds
        if components is not None:
            payload["components"] = components
        return self._request(
            endpoint=f"/channels/{channel_id}/messages", method="POST", json=payload
        )

    def update_message(
        self,
        msg_id: str,
        channel_id: str,
        *,
        content: str | None = None,
        embeds: list | None = None,
        components: list | None = None,
    ) -> dict:
        """Edit a message's content, embeds and/or buttons.

        Any argument left as None is omitted from the payload (unchanged); pass an
        empty string/list to clear a field.

        Args:
            msg_id: Message ID to edit.
            channel_id: Channel containing the message.
            content: New plain-text body (``""`` to clear), or None to leave as-is.
            embeds: New list of embed dicts (``[]`` to clear), or None.
            components: New ``components`` list (``[]`` to clear), or None.

        Returns:
            Dict with the updated message data.
        """
        payload: dict = {}
        if content is not None:
            payload["content"] = content
        if embeds is not None:
            payload["embeds"] = embeds
        if components is not None:
            payload["components"] = components
        return self._request(
            endpoint=f"/channels/{channel_id}/messages/{msg_id}",
            method="PATCH",
            json=payload,
        )

    def send_embed_message(
        self, embed: dict, channel_id: str, components: list | None = None
    ) -> dict:
        """Send a single-embed message to a Discord channel.

        Args:
            embed: Embed dict following Discord embed structure.
            channel_id: Target channel ID.
            components: Optional Discord ``components`` list (action rows of buttons).

        Returns:
            Dict with the created message data.
        """
        return self.create_message(channel_id, embeds=[embed], components=components)

    def edit_message(
        self, msg_id: str, content: str, channel_id: str, components: list | None = None
    ) -> dict:
        """Edit the text content of an existing message.

        Args:
            msg_id: Message ID to edit.
            content: New message content string.
            channel_id: Channel containing the message.
            components: Optional Discord ``components`` list. Pass ``[]`` to clear
                any existing buttons.

        Returns:
            Dict with the updated message data.
        """
        return self.update_message(msg_id, channel_id, content=content, components=components)

    def edit_embed_message(
        self, msg_id: str, embed: dict, channel_id: str, components: list | None = None
    ) -> dict:
        """Edit an existing message to a single embed.

        Args:
            msg_id: Message ID to edit.
            embed: Updated embed dict.
            channel_id: Channel containing the message.
            components: Optional Discord ``components`` list. Pass ``[]`` to clear
                any existing buttons.

        Returns:
            Dict with the updated message data.
        """
        return self.update_message(msg_id, channel_id, embeds=[embed], components=components)

    def pin_message(self, msg_id: str, channel_id: str) -> dict:
        """Pin an existing message.

        Args:
            msg_id: Message ID to pin.
            channel_id: Channel containing the message.
        """
        return self._request(
            endpoint=f"/channels/{channel_id}/messages/pins/{msg_id}",
            method="PUT",
        )

    def create_channel(
        self, channel_name: str, parent_id: str, role_id: str | None, gm_id: str
    ) -> dict:
        """Create a text channel in the guild with permission overwrites.

        Args:
            channel_name: Display name for the channel.
            parent_id: Parent category ID.
            role_id: Player role ID for permission overwrites, or None to create
                the channel without a player-role overwrite (direct-permission mode,
                where players are granted access individually).
            gm_id: GM user ID for elevated permissions.

        Returns:
            Dict with the created channel data.
        """
        permission_overwrites = [
            {"id": self.guild_id, "type": 0, "deny": "1024"},
            {"id": gm_id, "type": 1, "allow": GM_ROLE_PERMISSION},
        ]
        if role_id:
            permission_overwrites.insert(
                0, {"id": role_id, "type": 0, "allow": PLAYER_ROLE_PERMISSION}
            )
        payload = {
            "name": "-".join(unidecode(channel_name).split()),
            "type": 0,
            "parent_id": parent_id,
            "permission_overwrites": permission_overwrites,
        }
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/channels", method="POST", json=payload
        )

    def create_category(self, name: str) -> dict:
        """Create a category channel (type 4) in the guild.

        Unlike :meth:`create_channel`, the name is sent verbatim (no unidecode /
        hyphen-join) so emoji category names are preserved.

        Args:
            name: Display name for the category (kept as-is, emojis included).

        Returns:
            Dict with the created category data (including ``id``).
        """
        payload = {"name": name, "type": DISCORD_CHANNEL_TYPE_CATEGORY}
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/channels", method="POST", json=payload
        )

    def list_guild_channels(self) -> list:
        """Fetch every channel in the guild.

        Returns:
            List of channel dicts as returned by the Discord API.
        """
        return self._request(endpoint=f"/guilds/{self.guild_id}/channels", method="GET")

    def get_channel(self, channel_id: str) -> dict:
        """Fetch channel data from Discord.

        Args:
            channel_id: Discord channel ID.

        Returns:
            Dict with channel data.
        """
        return self._request(endpoint=f"/channels/{channel_id}", method="GET")

    def delete_channel(self, channel_id: str) -> dict:
        """Delete a Discord channel.

        Args:
            channel_id: Channel ID to delete.
        """
        return self._request(endpoint=f"/channels/{channel_id}", method="DELETE")

    def update_channel_parent(self, channel_id: str, parent_id: str) -> dict:
        """Move a channel under a different parent category.

        Args:
            channel_id: Channel to move.
            parent_id: ID of the destination category.

        Returns:
            Dict with the updated channel data.
        """
        return self._request(
            endpoint=f"/channels/{channel_id}", method="PATCH", json={"parent_id": parent_id}
        )

    def create_role(self, role_name: str, permissions: str, color: int) -> dict:
        """Create a new guild role.

        Args:
            role_name: Display name for the role.
            permissions: Permission bitfield string.
            color: Role color as integer.

        Returns:
            Dict with the created role data.
        """
        payload = {
            "name": "_".join(unidecode(role_name).split()),
            "permissions": permissions,
            "color": color,
            "mentionable": True,
        }
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/roles", method="POST", json=payload
        )

    def list_roles(self) -> list:
        """Fetch all roles defined in the guild.

        Returns:
            List of role dicts as returned by the Discord API.
        """
        return self._request(endpoint=f"/guilds/{self.guild_id}/roles", method="GET")

    def get_role(self, role_id: str) -> dict:
        """Fetch a guild role by ID.

        Args:
            role_id: Role ID to look up.

        Returns:
            Dict with role data, or a fallback dict if not found.
        """
        for role in self.list_roles():
            if role["id"] == role_id:
                return role
        return {"message": "Unknown Role"}

    def delete_role(self, role_id: str) -> dict:
        """Delete a guild role.

        Args:
            role_id: Role ID to delete.
        """
        return self._request(endpoint=f"/guilds/{self.guild_id}/roles/{role_id}", method="DELETE")

    def add_role_to_user(self, user_id: str, role_id: str) -> dict:
        """Assign a role to a guild member.

        Args:
            user_id: Discord user ID.
            role_id: Role ID to assign.
        """
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            method="PUT",
        )

    def remove_role_from_user(self, user_id: str, role_id: str) -> dict:
        """Remove a role from a guild member.

        Args:
            user_id: Discord user ID.
            role_id: Role ID to remove.
        """
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            method="DELETE",
        )

    def set_channel_permission(
        self, channel_id: str, target_id: str, allow: str, type_: int = 1
    ) -> dict:
        """Create or edit a permission overwrite on a channel.

        Used in direct-permission mode to grant a single player access to a game
        channel without consuming a guild role.

        Args:
            channel_id: Channel to set the overwrite on.
            target_id: Member or role ID the overwrite applies to.
            allow: Allowed permission bitfield string.
            type_: Overwrite type (1 = member, 0 = role).
        """
        payload = {"allow": allow, "type": type_}
        return self._request(
            endpoint=f"/channels/{channel_id}/permissions/{target_id}",
            method="PUT",
            json=payload,
        )

    def delete_channel_permission(self, channel_id: str, target_id: str) -> dict:
        """Delete a permission overwrite from a channel.

        Args:
            channel_id: Channel to remove the overwrite from.
            target_id: Member or role ID whose overwrite is removed.
        """
        return self._request(
            endpoint=f"/channels/{channel_id}/permissions/{target_id}",
            method="DELETE",
        )
