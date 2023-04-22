from dotenv import load_dotenv
from website.utils.discord import Discord
from flask_discord import Unauthorized
import os
import pytest

from website.utils.exceptions import RateLimited


def test_rate_limited_exception():
    is_global = False
    message = "You are being rate limited."
    retry_after = 64.57
    headers = {
        "HTTP/1.1 429": "TOO MANY REQUESTS",
        "Content-Type": "application/json",
        "Retry-After": retry_after,
        "X-RateLimit-Limit": 10,
        "X-RateLimit-Remaining": 0,
        "X-RateLimit-Reset": 1470173023.123,
        "X-RateLimit-Reset-After": retry_after,
        "X-RateLimit-Bucket": "abcd1234",
        "X-RateLimit-Scope": "user",
    }
    json = {"message": message, "retry_after": retry_after, "global": is_global}
    error = RateLimited(json, headers)
    assert error.json == json
    assert error.headers == headers
    assert error.is_global == is_global
    assert error.message == message
    assert error.retry_after == retry_after


config = load_dotenv()
client = Discord(
    os.environ.get("DISCORD_GUILD_ID"), os.environ.get("DISCORD_BOT_TOKEN")
)
bot_user_id = os.environ.get("DISCORD_CLIENT_ID")
test_channel_id = os.environ.get("UNITTEST_CHANNEL_ID")


def test_wrong_token():
    wrong_client = Discord(os.environ.get("DISCORD_GUILD_ID"), "wrong-token")
    with pytest.raises(Unauthorized):
        wrong_client.send_message("blublu", test_channel_id)


def test_get_user():
    response = client.get_user(bot_user_id)
    assert response["user"]["id"] == bot_user_id
    assert response["user"]["username"] == "QuestMaster"


def test_send_message():
    """
    Test sending a messages to the defined test channel
    """
    # Simple text message
    content = "This is a unit test"
    response = client.send_message(content, test_channel_id)
    assert response["content"] == content
    assert response["channel_id"] == test_channel_id
    # Embed
    title = "Annonce de test"
    color = 39423
    embed = {
        "title": title,
        "color": color,
        "fields": [
            {"name": "Name", "value": "Mon OS"},
            {"name": "MJ", "value": "John Bob"},
            {"name": "Description", "value": "blabla"},
            {"name": "Type de session", "value": "OS", "inline": True},
            {"name": "Nombre de sessions", "value": "2", "inline": True},
        ],
        "image": {"url": "https://club-jdr.fr/wp-content/uploads/2021/12/dnd.png"},
        "footer": {},
    }
    response = client.send_embed_message(embed, test_channel_id)
    assert response["channel_id"] == test_channel_id
    assert response["embeds"][0]["title"] == title
    assert response["embeds"][0]["color"] == color


def test_role_workflow():
    """
    Test creating a role, assigning it to a know user (the bot id), removing the role from the user and finally deleting the role
    """
    role_name = "testrole"
    permissions = "3072"
    color = 15844367
    # Role creation
    response = client.create_role(role_name, permissions, color)
    role_id = response["id"]
    assert role_name == response["name"]
    assert permissions == response["permissions"]
    assert color == response["color"]
    # Role details
    response = client.get_role(role_id)
    assert role_name == response["name"]
    assert permissions == response["permissions"]
    assert color == response["color"]
    # Role attribution
    response = client.add_role_to_user(bot_user_id, role_id)
    assert response == "{}"
    # Role de-attribution
    response = client.remove_role_from_user(bot_user_id, role_id)
    assert response == "{}"
    # Role deletion
    response = client.delete_role(role_id)
    assert response == "{}"
    # Role should not exist
    response = client.get_role(role_id)
    assert response["message"] == "Unknown Role"


def test_channel_workflow():
    """
    Test creating and deleting a channel
    """
    channel_name = "testchannel"
    parent_id = os.environ.get("CATEGORIES_CHANNEL_ID")
    # Channel creation
    response = client.create_channel(channel_name, parent_id)
    channel_id = response["id"]
    assert response["name"] == channel_name
    assert response["parent_id"] == parent_id
    # Channel details
    response = client.get_channel(channel_id)
    assert response["name"] == channel_name
    assert response["parent_id"] == parent_id
    # Channel deletion
    response = client.delete_channel(channel_id)
    assert response["id"] == channel_id
