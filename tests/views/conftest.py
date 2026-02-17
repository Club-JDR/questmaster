"""Shared fixtures for view tests.

Provides Discord-mocked fixtures for focused (unit-style) view tests
and factory-based game fixtures for convenient test setup.
"""

from unittest.mock import MagicMock, patch

import pytest

from tests.constants import (
    TEST_ADMIN_USER_ID,
    TEST_ADMIN_USER_NAME,
    TEST_GM_USER_ID,
    TEST_GM_USER_NAME,
    TEST_REGULAR_USER_ID,
    TEST_REGULAR_USER_NAME,
)
from tests.factories import GameFactory
from website.models import User


@pytest.fixture
def mock_discord_lookups(test_app):
    """Patch Discord API lookups so views work without live credentials.

    Yields a mutable ``role_map`` dict keyed by user ID.  Tests can add
    entries to grant custom role sets to dynamically-created users.

    Default mappings:
        * Admin user (Notsag)  -> GM + admin + player roles
        * GM user (Jadow)     -> GM + player roles (not admin)
        * All others           -> player role only
    """
    gm_role = test_app.config["DISCORD_GM_ROLE_ID"]
    admin_role = test_app.config["DISCORD_ADMIN_ROLE_ID"]
    player_role = test_app.config["DISCORD_PLAYER_ROLE_ID"]

    role_map = {
        TEST_ADMIN_USER_ID: [gm_role, admin_role, player_role],
        TEST_GM_USER_ID: [gm_role, player_role],
    }

    def fake_get_user_roles(user_id):
        return role_map.get(user_id, [player_role])

    def fake_get_user_profile(user_id, force_refresh=False):
        names = {
            TEST_ADMIN_USER_ID: TEST_ADMIN_USER_NAME,
            TEST_GM_USER_ID: TEST_GM_USER_NAME,
            TEST_REGULAR_USER_ID: TEST_REGULAR_USER_NAME,
        }
        return {
            "name": names.get(user_id, "TestUser"),
            "avatar": "/static/img/default_avatar.png",
        }

    with (
        patch("website.models.user.get_user_roles", side_effect=fake_get_user_roles),
        patch("website.models.user.get_user_profile", side_effect=fake_get_user_profile),
    ):
        yield role_map


@pytest.fixture
def mock_csrf():
    """Bypass CSRF validation for POST requests."""
    with patch("flask_wtf.csrf.validate_csrf", return_value=True):
        yield


@pytest.fixture
def mock_discord_service():
    """Mock all DiscordService interactions in game views.

    Patches the game_service singleton's discord attribute and the
    module-level discord_service singleton used by view functions.
    """
    mock = MagicMock()
    mock.create_role.return_value = {"id": "mock_role_id"}
    mock.create_channel.return_value = {"id": "mock_channel_id"}
    mock.send_game_embed.return_value = "mock_msg_id"

    with (
        patch("website.views.games.game_service.discord", mock),
        patch("website.views.games.discord_service", mock),
    ):
        yield mock


# -- User fixtures (override root conftest to depend on db_session) ----------
#
# The root-level user fixtures depend on ``test_app`` only and load users via
# ``db.session``.  When ``logged_in_user`` (which depends on ``regular_user``)
# is resolved *before* ``db_session`` reconfigures the session factory, the
# user object ends up attached to a different session than factory-created
# games, causing "already attached to session" errors on relationship
# mutations.  These overrides force user fixtures to depend on ``db_session``,
# guaranteeing consistent session affinity.


@pytest.fixture
def regular_user(db_session):
    """Return the pre-seeded regular user from the test session."""
    return db_session.get(User, TEST_REGULAR_USER_ID)


@pytest.fixture
def admin_user(db_session):
    """Return the pre-seeded admin user from the test session."""
    return db_session.get(User, TEST_ADMIN_USER_ID)


@pytest.fixture
def gm_user(db_session):
    """Return the pre-seeded GM user from the test session."""
    return db_session.get(User, TEST_GM_USER_ID)


# -- Factory-based game fixtures --------------------------------------------


@pytest.fixture
def open_game(db_session, default_system, default_vtt):
    """An open oneshot game created via factory."""
    return GameFactory(
        db_session,
        status="open",
        system_id=default_system.id,
        vtt_id=default_vtt.id,
    )


@pytest.fixture
def draft_game(db_session, default_system, default_vtt):
    """A draft game created via factory."""
    return GameFactory(
        db_session,
        status="draft",
        system_id=default_system.id,
        vtt_id=default_vtt.id,
    )


@pytest.fixture
def closed_game(db_session, default_system, default_vtt):
    """A closed game created via factory."""
    return GameFactory(
        db_session,
        status="closed",
        system_id=default_system.id,
        vtt_id=default_vtt.id,
    )


@pytest.fixture
def open_campaign(db_session, default_system, default_vtt):
    """An open campaign created via factory."""
    return GameFactory(
        db_session,
        type="campaign",
        status="open",
        system_id=default_system.id,
        vtt_id=default_vtt.id,
    )
