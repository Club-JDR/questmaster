import json
import os

mimetype = "application/json"
headers = {"Content-Type": mimetype, "Accept": mimetype}
redirect_url = "https://discordapp.com/api/oauth2/authorize"
users = json.loads(os.environ.get("USER_ID_LIST"))


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
    response = client.post("/users/", data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["user"] == users["gm1"]
    assert data["status"] == "created"
    # POST EXISTING USER
    data = {"id": users["gm1"]}
    response = client.post("/users/", data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["user"] == users["gm1"]
    assert data["status"] == "exists"
    # GET ALL USERS
    response = client.get("/users/")
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert isinstance(data["count"], int)
    assert isinstance(data["users"], list)
    # GET USER DETAILS
    response = client.get(f"/users/{users['gm1']}")
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert f"https://cdn.discordapp.com/avatars/{users['gm1']}" in data["avatar"]
    assert isinstance(data["gm"], bool)
    assert data["id"] == users["gm1"]
    assert isinstance(data["username"], str)
    # DELETE GAME
    response = client.delete(f"/users/{users['gm1']}", headers=headers)
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
    game_name = "OS test"
    game_type = "oneshot"
    data = {"name": game_name, "type": game_type, "gm": users["gm2"]}
    response = client.post("/games/", data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert isinstance(data["game"], int)
    assert data["status"] == "created"
    game_id = data["game"]
    # POST NEW GAME WHERE USER IS NOT GM
    data = {"name": game_name, "type": game_type, "gm": users["notgm"]}
    response = client.post("/games/", data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 401
    assert data["error"] == "GM doesn't have the correct role on the server."
    # GET ALL GAMES
    response = client.get("/games/")
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert isinstance(data["count"], int)
    assert isinstance(data["games"], list)
    # GET GAME DETAILS
    response = client.get(f"/games/{game_id}", headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["id"] == game_id
    assert data["name"] == game_name
    assert data["type"] == game_type
    assert data["gm"] == users["gm2"]
    # DELETE GAME
    response = client.delete(f"/games/{game_id}", headers=headers)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["game"] == game_id
    assert data["status"] == "deleted"
