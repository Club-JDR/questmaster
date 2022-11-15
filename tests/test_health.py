import json


def test_health(client):
    """
    Test health endpoint.
    """
    response = client.get("/health/")
    data = json.loads(response.data)
    assert data["uptime"] is not None
    assert data["version"] is not None
    assert data["date"] is not None
    assert data["status"] == "OK"
    assert data["title"] == "QuestMaster API"
    assert response.status_code == 200
