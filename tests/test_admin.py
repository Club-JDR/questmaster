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


import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/admin/game/",
        "/admin/vtt/",
        "/admin/channel/",
        "/admin/gameevent/",
        "/admin/system/",
        "/admin/usertrophy/",
    ],
)
def test_admin_model_view_requires_admin_user(client, path):
    with client.session_transaction() as sess:
        sess["user_id"] = "some_user"
        sess["is_admin"] = False

    response = client.get(path)
    assert response.status_code == 403


@pytest.mark.parametrize(
    "path",
    [
        "/admin/game/",
        "/admin/vtt/",
        "/admin/channel/",
        "/admin/gameevent/",
        "/admin/system/",
        "/admin/usertrophy/",
    ],
)
def test_admin_model_view_accessible_to_admin(client, path):
    with client.session_transaction() as sess:
        sess["user_id"] = "admin"
        sess["is_admin"] = True

    response = client.get(path)
    assert response.status_code == 200
