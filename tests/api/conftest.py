"""API test fixtures.

Provides JWT token helpers and pre-authenticated API clients.
"""

from datetime import datetime, timezone

import jwt
import pytest

from tests.constants import TEST_ADMIN_USER_ID, TEST_GM_USER_ID, TEST_REGULAR_USER_ID


def make_jwt_token(
    app,
    sub,
    *,
    is_gm=False,
    is_admin=False,
    is_player=True,
    expired=False,
    iat_override=None,
):
    """Mint a JWT token for testing.

    Args:
        app: Flask application instance.
        sub: User ID (``sub`` claim).
        is_gm: Whether the user has the GM role.
        is_admin: Whether the user has the admin role.
        is_player: Whether the user has the player role.
        expired: If True, set ``exp`` in the past.
        iat_override: Override the ``iat`` claim (datetime).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    iat = iat_override or now
    if expired:
        from datetime import timedelta

        exp = now - timedelta(seconds=1)
    else:
        exp = now + app.config["JWT_ACCESS_TOKEN_EXPIRES"]

    payload = {
        "sub": sub,
        "is_gm": is_gm,
        "is_admin": is_admin,
        "is_player": is_player,
        "iat": iat,
        "exp": exp,
    }
    return jwt.encode(
        payload,
        app.config["JWT_SECRET_KEY"],
        algorithm=app.config["JWT_ALGORITHM"],
    )


@pytest.fixture
def api_client(test_app):
    """Flask test client for API requests."""
    return test_app.test_client()


@pytest.fixture
def user_token(test_app):
    """Valid JWT for the regular test user."""
    return make_jwt_token(test_app, TEST_REGULAR_USER_ID, is_player=True)


@pytest.fixture
def gm_token(test_app):
    """Valid JWT for the GM test user."""
    return make_jwt_token(test_app, TEST_GM_USER_ID, is_gm=True, is_player=True)


@pytest.fixture
def admin_token(test_app):
    """Valid JWT for the admin test user."""
    return make_jwt_token(test_app, TEST_ADMIN_USER_ID, is_admin=True, is_player=True)


@pytest.fixture
def auth_headers_user(user_token):
    """Authorization headers for the regular user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def auth_headers_gm(gm_token):
    """Authorization headers for the GM user."""
    return {"Authorization": f"Bearer {gm_token}"}


@pytest.fixture
def auth_headers_admin(admin_token):
    """Authorization headers for the admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
