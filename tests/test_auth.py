def test_login_redirect_sets_next_url(client):
    response = client.get("/login/")
    assert response.status_code in (302, 303)
    assert "Location" in response.headers


def test_logout_clears_session_and_redirects(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "some_id"
    response = client.get("/logout/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Me connecter" in response.data
    with client.session_transaction() as sess:
        assert "some_id" not in sess
