"""Unit tests for the low-level Discord client (no live Discord required).

These mock the HTTP layer (``Discord._request``) to assert endpoint and payload
shaping for the channel-permission and role-related helpers.
"""

from unittest.mock import patch

import pytest

from config.constants import GM_ROLE_PERMISSION, PLAYER_ROLE_PERMISSION
from website.client.discord import Discord


@pytest.fixture
def client():
    """A Discord client with a fixed guild id and token."""
    return Discord(guild_id="guild_1", bot_token="token")


class TestCreateChannel:
    def test_includes_role_overwrite_when_role_given(self, client):
        """Role mode adds a player-role overwrite alongside @everyone and GM."""
        with patch.object(Discord, "_request", return_value={"id": "chan"}) as req:
            client.create_channel("My Game", "cat_1", "role_9", "gm_1")

        payload = req.call_args.kwargs["json"]
        overwrites = payload["permission_overwrites"]
        assert {"id": "role_9", "type": 0, "allow": PLAYER_ROLE_PERMISSION} in overwrites
        assert {"id": "guild_1", "type": 0, "deny": "1024"} in overwrites
        assert {"id": "gm_1", "type": 1, "allow": GM_ROLE_PERMISSION} in overwrites

    def test_omits_role_overwrite_in_direct_mode(self, client):
        """Direct mode (role_id=None) creates only @everyone and GM overwrites."""
        with patch.object(Discord, "_request", return_value={"id": "chan"}) as req:
            client.create_channel("My Game", "cat_1", None, "gm_1")

        overwrites = req.call_args.kwargs["json"]["permission_overwrites"]
        assert len(overwrites) == 2
        assert all(o["id"] != "role_9" for o in overwrites)
        assert {"id": "guild_1", "type": 0, "deny": "1024"} in overwrites


class TestChannelPermissions:
    def test_set_channel_permission(self, client):
        """set_channel_permission PUTs an allow/type overwrite for the member."""
        with patch.object(Discord, "_request", return_value={}) as req:
            client.set_channel_permission("chan_1", "user_1", PLAYER_ROLE_PERMISSION)

        assert req.call_args.kwargs["endpoint"] == "/channels/chan_1/permissions/user_1"
        assert req.call_args.kwargs["method"] == "PUT"
        assert req.call_args.kwargs["json"] == {"allow": PLAYER_ROLE_PERMISSION, "type": 1}

    def test_delete_channel_permission(self, client):
        """delete_channel_permission DELETEs the member overwrite."""
        with patch.object(Discord, "_request", return_value={}) as req:
            client.delete_channel_permission("chan_1", "user_1")

        assert req.call_args.kwargs["endpoint"] == "/channels/chan_1/permissions/user_1"
        assert req.call_args.kwargs["method"] == "DELETE"


class TestRolesAndMessages:
    def test_list_roles(self, client):
        """list_roles fetches the guild roles list."""
        with patch.object(Discord, "_request", return_value=[{"id": "1"}]) as req:
            assert client.list_roles() == [{"id": "1"}]

        assert req.call_args.kwargs["endpoint"] == "/guilds/guild_1/roles"

    def test_send_message_forwards_allowed_mentions(self, client):
        """allowed_mentions is included in the message payload when provided."""
        allowed = {"parse": ["users", "roles"]}
        with patch.object(Discord, "_request", return_value={"id": "m"}) as req:
            client.send_message("hi", "chan_1", allowed_mentions=allowed)

        assert req.call_args.kwargs["json"]["allowed_mentions"] == allowed

    def test_send_message_omits_allowed_mentions_by_default(self, client):
        """No allowed_mentions key is sent when not provided."""
        with patch.object(Discord, "_request", return_value={"id": "m"}) as req:
            client.send_message("hi", "chan_1")

        assert "allowed_mentions" not in req.call_args.kwargs["json"]
