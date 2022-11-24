from api.utils.exceptions import RateLimited
from flask_discord import Unauthorized
import requests
import json

DISCORD_API_BASE_URL = "https://discordapp.com/api/v9"


class Discord:
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

    def _request(self, route, method, payload=None):
        route = DISCORD_API_BASE_URL + route
        if payload == None:
            response = requests.request(method, route, headers=self.headers)
        else:
            response = requests.request(
                method, route, data=json.dumps(payload), headers=self.headers
            )

        if response.status_code == 401:
            raise Unauthorized()

        if response.status_code == 429:
            raise RateLimited(response.json(), response.headers)

        if response.status_code == 204:
            return json.dumps({})

        return response.json()

    def get_user(self, user_id):
        return self._request(
            route=f"/guilds/{self.guild_id}/members/{user_id}", method="GET"
        )

    def send_message(self, content, channel_id):
        payload = {
            "content": content,
        }
        return self._request(
            route=f"/channels/{channel_id}/messages", method="POST", payload=payload
        )

    def send_embed_message(self, embed, channel_id):
        payload = {"embeds": [embed]}
        return self._request(
            route=f"/channels/{channel_id}/messages", method="POST", payload=payload
        )

    def create_channel(self, channel_name, parent_id):
        payload = {"name": channel_name, "type": 0, "parent_id": parent_id}
        return self._request(
            route=f"/guilds/{self.guild_id}/channels", method="POST", payload=payload
        )

    def get_channel(self, channel_id):
        return self._request(route=f"/channels/{channel_id}", method="GET")

    def delete_channel(self, channel_id):
        return self._request(route=f"/channels/{channel_id}", method="DELETE")

    def create_role(self, role_name, permissions, color):
        payload = {
            "name": role_name,
            "permissions": permissions,
            "color": color,
            "mentionable": True,
        }
        return self._request(
            route=f"/guilds/{self.guild_id}/roles", method="POST", payload=payload
        )

    def get_role(self, role_id):
        roles = self._request(route=f"/guilds/{self.guild_id}/roles", method="GET")
        for role in roles:
            if role["id"] == role_id:
                return role
        return {"message": "Unknown Role"}

    def delete_role(self, role_id):
        return self._request(
            route=f"/guilds/{self.guild_id}/roles/{role_id}", method="DELETE"
        )

    def add_role_to_user(self, user_id, role_id):
        return self._request(
            route=f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            method="PUT",
        )

    def remove_role_from_user(self, user_id, role_id):
        return self._request(
            route=f"/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}",
            method="DELETE",
        )
