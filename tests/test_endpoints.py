import json

mimetype = "application/json"
headers = {"Content-Type": mimetype, "Accept": mimetype}
redirect_url = "https://discordapp.com/api/oauth2/authorize"


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
    assert data["uptime"] is not None
    assert data["version"] is not None
    assert data["date"] is not None
    assert data["status"] == "OK"
    assert data["database"] == "OK"
    assert data["title"] == "QuestMaster API"
    assert response.content_type == mimetype
    assert response.status_code == 200


def test_users(client):
    """
    Test /users/ endpoint.
    """
    user_id = 297442997468004353
    # POST
    data = {"id": user_id}
    response = client.post("/users/", data=json.dumps(data), headers=headers)
    data = json.loads(response.data)
    assert data["user"] == user_id
    assert data["status"] == "created"
    assert response.content_type == mimetype
    assert response.status_code == 200
    # GET ALL USERS
    response = client.get("/users/")
    data = json.loads(response.data)
    assert isinstance(data["count"], int)
    assert isinstance(data["users"], list)
    assert response.content_type == mimetype
    assert response.status_code == 200
    # GET USER DETAILS
    response = client.get(f"/users/{user_id}")
    data = json.loads(response.data)
    assert f"https://cdn.discordapp.com/avatars/{user_id}" in data["avatar"]
    assert isinstance(data["gm"], bool)
    assert data["id"] == user_id
    assert isinstance(data["username"], str)
    assert response.content_type == mimetype
    assert response.status_code == 200
    # DELETE
    response = client.delete(f"/users/{user_id}", headers=headers)
    data = json.loads(response.data)
    assert data["user"] == user_id
    assert data["status"] == "deleted"
    assert response.content_type == mimetype
    assert response.status_code == 200
