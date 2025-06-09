from dotenv import load_dotenv
from website.utils.exceptions import RateLimited
import pytest


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


@pytest.fixture
def sent_discord_message(discord_session, test_channel_id):
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
    message = discord_session.send_embed_message(embed, test_channel_id)
    return message["id"]


def test_get_user(discord_session, bot_user_id):
    response = discord_session.get_user(bot_user_id)
    assert response["user"]["id"] == bot_user_id
    assert response["user"]["username"] == "QuestMaster"


def test_send_message(discord_session, test_channel_id, sent_discord_message):
    """
    Test sending a messages to the defined test channel
    """
    content = "This is a unit test"
    response = discord_session.send_message(content, test_channel_id)
    assert response["content"] == content
    assert response["channel_id"] == test_channel_id
    assert isinstance(sent_discord_message, str)
    assert len(sent_discord_message) > 0


def test_edit_message(discord_session, test_channel_id, sent_discord_message):
    """
    Test editing previous embed message
    """
    # Embed
    title = "Annonce de test (édité)"
    color = 16766723
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
    response = discord_session.edit_embed_message(
        sent_discord_message, embed, test_channel_id
    )
    print(response)
    assert response["channel_id"] == test_channel_id
    assert response["embeds"][0]["title"] == title
    assert response["embeds"][0]["color"] == color


def test_role_workflow(discord_session, bot_user_id):
    """
    Test creating a role, assigning it to a know user (the bot id), removing the role from the user and finally deleting the role
    """
    role_name = "testrole"
    permissions = "3072"
    color = 15844367
    # Role creation
    response = discord_session.create_role(role_name, permissions, color)
    role_id = response["id"]
    assert role_name == response["name"]
    assert permissions == response["permissions"]
    assert color == response["color"]
    # Role details
    response = discord_session.get_role(role_id)
    assert role_name == response["name"]
    assert permissions == response["permissions"]
    assert color == response["color"]
    # Role attribution
    response = discord_session.add_role_to_user(bot_user_id, role_id)
    assert response == "{}"
    # Role de-attribution
    response = discord_session.remove_role_from_user(bot_user_id, role_id)
    assert response == "{}"
    # Role deletion
    response = discord_session.delete_role(role_id)
    assert response == "{}"
    # Role should not exist
    response = discord_session.get_role(role_id)
    assert response["message"] == "Unknown Role"


def test_channel_workflow(discord_session, oneshot_channel):
    """
    Test creating and deleting a channel
    """
    role_name = "testrole"
    permissions = "3072"
    gm_id = "664487064577900594"
    color = 15844367
    # Role creation
    response = discord_session.create_role(role_name, permissions, color)
    role_id = response["id"]
    assert role_name == response["name"]
    assert permissions == response["permissions"]
    assert color == response["color"]
    channel_name = "testchannel"
    # Channel creation
    response = discord_session.create_channel(
        channel_name, oneshot_channel.id, role_id, gm_id
    )
    channel_id = response["id"]
    assert len(response["permission_overwrites"]) == 3
    assert any(
        role_id in permission["id"] for permission in response["permission_overwrites"]
    )
    assert any(
        gm_id in permission["id"] for permission in response["permission_overwrites"]
    )
    assert response["name"] == channel_name
    assert response["parent_id"] == oneshot_channel.id
    # Channel details
    response = discord_session.get_channel(channel_id)
    assert response["name"] == channel_name
    assert response["parent_id"] == oneshot_channel.id
    # Channel deletion
    response = discord_session.delete_channel(channel_id)
    assert response["id"] == channel_id
    # Role deletion
    response = discord_session.delete_role(role_id)
    assert response == "{}"
