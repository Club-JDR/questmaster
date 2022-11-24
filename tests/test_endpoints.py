from api.utils.discord import Discord
import json
import os
import re

mimetype = "application/json"
headers = {"Content-Type": mimetype, "Accept": mimetype}
redirect_url = "https://discordapp.com/api/oauth2/authorize"
users = json.loads(os.environ.get("USER_ID_LIST"))

users_base_endpoint = "/users/"
games_base_endpoint = "/games/"

bot = Discord(os.environ.get("DISCORD_GUILD_ID"), os.environ.get("DISCORD_BOT_TOKEN"))


def test_login_redirect(client):
    """
    Test /login/ endpoint.
    """
    response = client.get("/login/")
    assert response.status_code == 302
    assert redirect_url in response.headers.get("Location")


def test_health(client):
    """
    Test /health/ endpoint.
    """
    response = client.get("/health/")
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["uptime"] is not None
    assert data["version"] is not None
    assert data["date"] is not None
    assert data["status"] == "OK"
    assert data["database"] == "OK"
    assert data["title"] == "QuestMaster API"


def test_users(client):
    """
    Test /users/ endpoints.
    """
    # POST NEW USER
    data = {"id": users["gm1"]}
    response = client.post(users_base_endpoint, data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["user"] == users["gm1"]
    assert data["status"] == "created"
    # POST EXISTING USER
    data = {"id": users["gm1"]}
    response = client.post(users_base_endpoint, data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["user"] == users["gm1"]
    assert data["status"] == "exists"
    # GET ALL USERS
    response = client.get(users_base_endpoint)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert isinstance(data["count"], int)
    assert isinstance(data["users"], list)
    # GET USER DETAILS
    response = client.get(f"{users_base_endpoint}{users['gm1']}")
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert f"https://cdn.discordapp.com/avatars/{users['gm1']}" in data["avatar"]
    assert isinstance(data["gm"], bool)
    assert data["id"] == users["gm1"]
    assert isinstance(data["username"], str)
    # DELETE USER
    response = client.delete(f"{users_base_endpoint}{users['gm1']}", headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["user"] == users["gm1"]
    assert data["status"] == "deleted"


def test_games(client):
    """
    Test /games/ endpoints.
    """
    # Create GM and false GM(or ensure it is already present)
    data = {"id": users["gm2"]}
    client.post("/users/", data=json.dumps(data), headers=headers)
    data = {"id": users["notgm"]}
    client.post("/users/", data=json.dumps(data), headers=headers)
    # POST NEW GAME
    game_name = "Baldur's Gate: Descent into Avernus"
    game_type = "campaign"
    game_length = "20+ sessions"
    game_system = "5E"
    game_description = """
    Welcome to Baldur's Gate, a city of ambition and corruption.
    You’ve just started your adventuring career, but already find yourself embroiled in a plot that sprawls from the shadows of Baldur's Gate to the front lines of the planes-spanning Blood War!
    Do you have what it takes to turn infernal war machines and nefarious contracts against the archdevil Zariel and her diabolical hordes?
    And can you ever hope to find your way home safely when pitted against the infinite evils of the Nine Hells?

    This heroic Dungeons & Dragons adventure book takes players from levels 1 to 13 as they journey through Baldur's Gate and into Avernus, the first layer of the Nine Hells.
    """
    game_restriction = "16+"
    game_restriction_tags = "psychological violence, gore"
    game_party_size = 4
    game_party_selection = False
    game_pregen = False
    data = {
        "name": game_name,
        "type": game_type,
        "length": game_length,
        "gm_id": users["gm2"],
        "system": game_system,
        "description": game_description,
        "restriction": game_restriction,
        "restriction_tags": game_restriction_tags,
        "party_size": game_party_size,
        "party_selection": game_party_selection,
        "pregen": game_pregen,
    }
    response = client.post(games_base_endpoint, data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert isinstance(data["game"], int)
    assert data["status"] == "created"
    game_id = data["game"]
    # POST NEW GAME WHERE USER IS NOT GM
    data = {
        "name": game_name,
        "type": game_type,
        "length": game_length,
        "gm_id": users["notgm"],
        "system": game_system,
        "description": game_description,
        "restriction": game_restriction,
        "restriction_tags": game_restriction_tags,
        "party_size": game_party_size,
        "party_selection": game_party_selection,
        "pregen": game_pregen,
    }
    response = client.post(games_base_endpoint, data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 401
    assert data["error"] == "GM doesn't have the correct role on the server."
    # GET ALL GAMES
    response = client.get(games_base_endpoint)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert isinstance(data["count"], int)
    assert isinstance(data["games"], list)
    # GET GAME DETAILS
    response = client.get(f"{games_base_endpoint}{game_id}", headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["id"] == game_id
    assert data["name"] == game_name
    assert data["type"] == game_type
    assert data["length"] == game_length
    assert data["system"] == game_system
    assert data["description"] == game_description
    assert data["restriction"] == game_restriction
    assert data["restriction_tags"] == game_restriction_tags
    assert data["gm"]["id"] == users["gm2"]
    assert data["party_size"] == game_party_size
    assert data["party_selection"] == game_party_selection
    assert data["pregen"] == game_pregen
    assert data["role"]["name"] == game_name
    assert data["channel"]["name"] == re.sub("[^0-9a-zA-Z]+", "-", game_name.lower())
    role_id = data["role"]["id"]
    channel_id = data["channel"]["id"]
    # DELETE GAME
    response = client.delete(f"{games_base_endpoint}{game_id}", headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["game"] == game_id
    assert data["status"] == "deleted"
    assert bot.get_channel(channel_id)["message"] == "Unknown Channel"
    assert bot.get_role(role_id)["message"] == "Unknown Role"
