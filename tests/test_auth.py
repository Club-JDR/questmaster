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
