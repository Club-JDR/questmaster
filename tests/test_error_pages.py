def test_404(client):
    response = client.get("/404/")
    assert response.status_code == 404


def test_403(client):
    response = client.get("/admin/")
    assert response.status_code == 403
