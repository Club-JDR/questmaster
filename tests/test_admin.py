def test_admin_requires_admin_user(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "test_user"
        sess["is_admin"] = False

    response = client.get("/admin/", follow_redirects=True)
    assert response.status_code == 403


def test_admin_dashboard_loads(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "admin_user"
        sess["is_admin"] = True

    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"QuestMaster Admin" in response.data
