def test_404(client):
    response = client.get("/404/")
    assert response.status_code == 404


def test_403(client):
    response = client.get("/admin/")
    assert response.status_code == 403


def test_403_returns_json_when_requested(client):
    response = client.get("/admin/", headers={"Accept": "application/json"})
    assert response.status_code == 403
    data = response.get_json()
    assert data["code"] == "UNAUTHORIZED"
    assert "error" in data


def test_403_admin_model_view_returns_json(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "some_user"
        sess["is_admin"] = False

    response = client.get(
        "/admin/game/", headers={"Accept": "application/json"}
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data["code"] == "UNAUTHORIZED"


def test_403_gm_required_returns_json(test_app, regular_user):
    client = test_app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = regular_user.id

    response = client.get(
        "/mes_annonces/", headers={"Accept": "application/json"}
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data["code"] == "UNAUTHORIZED"
    assert data["details"]["action"] == "gm"
