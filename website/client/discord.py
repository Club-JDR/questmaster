"""Discord API client for low-level HTTP operations.

This module provides the low-level Discord API client with HTTP request handling,
rate limiting, and retry logic. Business logic should use DiscordService instead.
"""

import time

import requests
from unidecode import unidecode

from config.constants import DISCORD_API_BASE_URL, GM_ROLE_PERMISSION, PLAYER_ROLE_PERMISSION
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

        for attempt in range(max_retries):
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

    def get_user(self, user_id):
        return self._request(endpoint=f"/guilds/{self.guild_id}/members/{user_id}", method="GET")

    def send_message(self, content, channel_id):
        payload = {
            "content": content,
        }
        return self._request(
            endpoint=f"/channels/{channel_id}/messages", method="POST", json=payload
        )

    def delete_message(self, msg_id, channel_id):
        return self._request(endpoint=f"/channels/{channel_id}/messages/{msg_id}", method="DELETE")

    def send_embed_message(self, embed, channel_id):
        payload = {"embeds": [embed]}
        return self._request(
            endpoint=f"/channels/{channel_id}/messages", method="POST", json=payload
        )

    def edit_embed_message(self, msg_id, embed, channel_id):
        payload = {"embeds": [embed]}
        return self._request(
            endpoint=f"/channels/{channel_id}/messages/{msg_id}",
            method="PATCH",
            json=payload,
        )

    def create_channel(self, channel_name, parent_id, role_id, gm_id):
        payload = {
            "name": "-".join(unidecode(channel_name).split()),
            "type": 0,
            "parent_id": parent_id,
            "permission_overwrites": [
                {"id": role_id, "type": 0, "allow": PLAYER_ROLE_PERMISSION},
                {"id": self.get_role(self.guild_id)["id"], "type": 0, "deny": "1024"},
                {"id": gm_id, "type": 1, "allow": GM_ROLE_PERMISSION},
            ],
        }
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/channels", method="POST", json=payload
        )

    def get_channel(self, channel_id):
        return self._request(endpoint=f"/channels/{channel_id}", method="GET")

    def delete_channel(self, channel_id):
        return self._request(endpoint=f"/channels/{channel_id}", method="DELETE")

    def create_role(self, role_name, permissions, color):
        payload = {
            "name": "_".join(unidecode(role_name).split()),
            "permissions": permissions,
            "color": color,
            "mentionable": True,
        }
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/roles", method="POST", json=payload
        )

    def get_role(self, role_id):
        roles = self._request(endpoint=f"/guilds/{self.guild_id}/roles", method="GET")
        for role in roles:
            if role["id"] == role_id:
                return role
        return {"message": "Unknown Role"}

    def delete_role(self, role_id):
        return self._request(endpoint=f"/guilds/{self.guild_id}/roles/{role_id}", method="DELETE")

    def add_role_to_user(self, user_id, role_id):
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            method="PUT",
        )

    def remove_role_from_user(self, user_id, role_id):
        return self._request(
            endpoint=f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            method="DELETE",
        )
