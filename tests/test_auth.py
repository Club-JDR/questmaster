import json, os

users = json.loads(os.environ.get("USER_ID_LIST"))
redirect_url = "https://discordapp.com/api/oauth2/authorize"


def test_login_redirect(session):
    """
    Test /login/ endpoint.
    """
    response = session.get("/login/")
    assert response.status_code == 302
    assert redirect_url in response.headers.get("Location")


def test_unauthorized(session):
    """
    Test failure of an unauthorized access to a URL needing authentication.
    """
    response = session.get("/mes_parties/")
    assert response.status_code == 403
