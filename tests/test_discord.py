from dotenv import load_dotenv
from api.utils.discord import Discord
from flask_discord import Unauthorized
import os
import pytest

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
    client.send_message(f"Rôle <@&{role_id}> créé.", test_channel_id)
    # Role attribution
    response = client.add_role_to_user(bot_user_id, role_id)
    client.send_message(
        f"Rôle <@&{role_id}> donné à <@{bot_user_id}>.", test_channel_id
    )
    assert response == "{}"
    # Role de-attribution
    response = client.remove_role_from_user(bot_user_id, role_id)
    client.send_message(
        f"Rôle <@&{role_id}> enlevé à <@{bot_user_id}>.", test_channel_id
    )
    assert response == "{}"
    # Role deletion
    response = client.delete_role(role_id)
    assert response == "{}"
    client.send_message(f"Rôle @{role_name} supprimé.", test_channel_id)


def test_channel_workflow():
    """
    Test creating and deleting a channel
    """
    channel_name = "testchannel"
    parent_id = os.environ.get("CATEGORIES_CHANNEL_ID")
    # Channel creation
    response = client.create_channel(channel_name, parent_id)
    channel_id = response["id"]
    client.send_message(f"Channel <#{channel_id}> créé.", test_channel_id)
    assert response["name"] == channel_name
    assert response["parent_id"] == parent_id
    # Channel deletion
    response = client.delete_channel(channel_id)
    assert response["id"] == channel_id
    client.send_message(f"Channel @{channel_name} supprimé.", test_channel_id)
