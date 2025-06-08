def test_404(session):
    """
    Test 404 page.
    """
    response = session.get("/404/")
    assert response.status_code == 404


def test_403(session):
    """
    Test 403 page.
    """
    response = session.get("/annonce/")
    assert response.status_code == 403
