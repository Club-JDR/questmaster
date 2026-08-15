"""Tests for admin "view-as" (user impersonation)."""

import pytest

from tests.constants import (
    TEST_ADMIN_USER_ID,
    TEST_ADMIN_USER_NAME,
    TEST_GM_USER_ID,
    TEST_REGULAR_USER_ID,
)


@pytest.fixture
def real_admin_client(test_app, admin_user):
    """Admin client whose session user is a real, persisted user.

    Restoring the real admin at "stop" looks the acting admin up by
    ``impersonator_id``, so — unlike the plain ``admin_client`` used
    elsewhere for admin-only checks — the session user must exist in the DB.
    """
    client = test_app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = admin_user.id
        sess["username"] = TEST_ADMIN_USER_NAME
        sess["is_admin"] = True
        sess["permissions"] = []
    return client


# -- Access control ------------------------------------------------------------


def test_start_requires_admin(logged_in_user, mock_csrf):
    response = logged_in_user.post(f"/admin/view-as/{TEST_ADMIN_USER_ID}/")
    assert response.status_code == 403


def test_start_requires_login(client, mock_csrf):
    response = client.post(f"/admin/view-as/{TEST_REGULAR_USER_ID}/")
    assert response.status_code in (302, 303)


def test_stop_does_not_require_admin(logged_in_user, mock_csrf):
    """The stop route must stay reachable after ``is_admin`` is downgraded."""
    response = logged_in_user.post("/admin/view-as/stop/")
    assert response.status_code in (302, 303)


def test_stop_requires_login(client, mock_csrf):
    response = client.post("/admin/view-as/stop/")
    assert response.status_code in (302, 303)


# -- Start ----------------------------------------------------------------------


def test_start_self_rejected(real_admin_client, mock_csrf):
    response = real_admin_client.post(
        f"/admin/view-as/{TEST_ADMIN_USER_ID}/", follow_redirects=True
    )
    assert response.status_code == 200
    with real_admin_client.session_transaction() as sess:
        assert "impersonator_id" not in sess


def test_start_unknown_user_flashes(real_admin_client, mock_csrf):
    response = real_admin_client.post("/admin/view-as/000000000000000000/", follow_redirects=True)
    assert response.status_code == 200
    assert "Utilisateur introuvable" in response.get_data(as_text=True)
    with real_admin_client.session_transaction() as sess:
        assert "impersonator_id" not in sess


def test_start_swaps_session_and_downgrades_admin_flag(
    real_admin_client, mock_csrf, mock_discord_lookups
):
    """Impersonating a non-admin user drops the admin flag (no privilege retention)."""
    real_admin_client.post(f"/admin/view-as/{TEST_REGULAR_USER_ID}/")

    with real_admin_client.session_transaction() as sess:
        assert sess["user_id"] == TEST_REGULAR_USER_ID
        assert sess["is_admin"] is False
        assert sess["impersonator_id"] == TEST_ADMIN_USER_ID
        assert sess["impersonator_username"] == TEST_ADMIN_USER_NAME


def test_start_while_already_impersonating_is_noop(
    real_admin_client, mock_csrf, mock_discord_lookups
):
    real_admin_client.post(f"/admin/view-as/{TEST_REGULAR_USER_ID}/")
    with real_admin_client.session_transaction() as sess:
        original_target = sess["user_id"]

    # A second start attempt (no nested impersonation) leaves the session alone.
    real_admin_client.post(f"/admin/view-as/{TEST_GM_USER_ID}/")
    with real_admin_client.session_transaction() as sess:
        assert sess["user_id"] == original_target


# -- Stop -------------------------------------------------------------------


def test_stop_restores_the_real_admin(real_admin_client, mock_csrf, mock_discord_lookups):
    real_admin_client.post(f"/admin/view-as/{TEST_REGULAR_USER_ID}/")

    real_admin_client.post("/admin/view-as/stop/")

    with real_admin_client.session_transaction() as sess:
        assert sess["user_id"] == TEST_ADMIN_USER_ID
        assert sess["is_admin"] is True
        assert "impersonator_id" not in sess
        assert "impersonator_username" not in sess


def test_stop_without_active_impersonation_is_harmless(real_admin_client, mock_csrf):
    response = real_admin_client.post("/admin/view-as/stop/", follow_redirects=True)
    assert response.status_code == 200
    with real_admin_client.session_transaction() as sess:
        assert sess["user_id"] == TEST_ADMIN_USER_ID


# -- Logout interaction -------------------------------------------------------


def test_logout_clears_impersonation_flag(real_admin_client, mock_csrf, mock_discord_lookups):
    real_admin_client.post(f"/admin/view-as/{TEST_REGULAR_USER_ID}/")

    real_admin_client.get("/logout/")

    with real_admin_client.session_transaction() as sess:
        assert "impersonator_id" not in sess
        assert "user_id" not in sess


# -- Banner --------------------------------------------------------------------


def test_banner_hidden_without_impersonation(logged_in_admin):
    response = logged_in_admin.get("/")
    assert "Revenir à mon compte" not in response.get_data(as_text=True)


def test_banner_shown_while_impersonating(real_admin_client, mock_csrf, mock_discord_lookups):
    real_admin_client.post(f"/admin/view-as/{TEST_REGULAR_USER_ID}/")

    response = real_admin_client.get("/")

    body = response.get_data(as_text=True)
    assert "Revenir à mon compte" in body
    assert "Vous incarnez" in body
