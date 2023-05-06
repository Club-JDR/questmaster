import json, os

users = json.loads(os.environ.get("USER_ID_LIST"))
redirect_url = "https://discordapp.com/api/oauth2/authorize"


def test_login_redirect(client):
    """
    Test /login/ endpoint.
    """
    response = client.get("/login/")
    assert response.status_code == 302
    assert redirect_url in response.headers.get("Location")


def test_sessions(client):
    """
    Fake session as player only
    """
    with client.session_transaction() as session:
        session["user_id"] = "664487064577900594"
        session["username"] = "user"
        session["avatar"] = "avatar.png"
        session["is_gm"] = False
        session["is_admin"] = False
    response = client.get("/")
    assert response.status_code == 200
    icon = b'<img src="avatar.png" alt="user" width="30" height="30" class="rounded-circle">'
    assert icon in response.data
    assert b"Me connecter</a>" not in response.data
    assert b"Poster une annnonce" not in response.data
    """
    Fake session as GM: should see Ressources and wiki menu items.
    """
    with client.session_transaction() as session:
        session["is_gm"] = True
    response = client.get("/")
    assert response.status_code == 200
    assert b"Me connecter</a>" not in response.data
    assert b"Poster une annnonce" in response.data
    """
    Logout should remove menu items and redirect.
    """
    response = client.get("/logout/")
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "username" not in session
        assert "avatar" not in session
        assert "is_gm" not in session
        assert "is_admin" not in session


def test_unauthorized(client):
    """
    Test failure of an unauthorized access to a URL needing authentication.
    """
    response = client.get("/mes_parties/")
    assert response.status_code == 403
