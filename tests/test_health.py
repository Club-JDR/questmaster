import json

mimetype = "application/json"


def test_health(client):
    """
    Test /health/ endpoint.
    """
    response = client.get("/health/")
    print(response.data)
    data = json.loads(response.data)
    assert response.content_type == mimetype
    assert response.status_code == 200
    assert data["uptime"] is not None
    assert data["version"] is not None
    assert data["date"] is not None
    assert data["status"] == "OK"
    assert data["database"] == "OK"
    assert data["title"] == "QuestMaster"
