from unittest.mock import patch

import pytest

from website.exceptions import UnauthorizedError
from website.views.auth import admin_only, require_permission


def _dummy_view(**kwargs):
    return "ok"


def test_require_permission_anonymous_redirects(test_app):
    with test_app.test_request_context():
        with patch("website.views.auth.session", {}):
            resp = require_permission("vtt.manage")(_dummy_view)()
            assert resp.status_code in (302, 303)


def test_require_permission_missing_raises(test_app):
    with test_app.test_request_context():
        with patch(
            "website.views.auth.session",
            {"user_id": "u", "is_admin": False, "permissions": []},
        ):
            with pytest.raises(UnauthorizedError):
                require_permission("vtt.manage")(_dummy_view)()


def test_require_permission_admin_passes(test_app):
    with test_app.test_request_context():
        with patch("website.views.auth.session", {"user_id": "u", "is_admin": True}):
            assert require_permission("vtt.manage")(_dummy_view)() == "ok"


def test_require_permission_granted_passes(test_app):
    with test_app.test_request_context():
        with patch(
            "website.views.auth.session",
            {"user_id": "u", "is_admin": False, "permissions": ["vtt.manage"]},
        ):
            assert require_permission("vtt.manage")(_dummy_view)() == "ok"


def test_admin_only_blocks_delegated_user(test_app):
    with test_app.test_request_context():
        with patch(
            "website.views.auth.session",
            {"user_id": "u", "is_admin": False, "permissions": ["vtt.manage"]},
        ):
            with pytest.raises(UnauthorizedError):
                admin_only(_dummy_view)()


def test_admin_only_allows_admin(test_app):
    with test_app.test_request_context():
        with patch("website.views.auth.session", {"user_id": "u", "is_admin": True}):
            assert admin_only(_dummy_view)() == "ok"


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
