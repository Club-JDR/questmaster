import json

def test_health(client):
    """
    Test health endpoint.
    """
    response = client.get("/health/")
    data = json.loads(response.data)
    assert data['uptime'] is not None
    assert data['status'] == "OK"
    assert response.status_code == 200
