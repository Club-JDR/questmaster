def test_404(client):
    """
    Test 404 page.
    """
    response = client.get("/404/")
    assert response.status_code == 404


def test_403(client):
    """
    Test 403 page.
    """
    response = client.get("/annonce/")
    assert response.status_code == 403
