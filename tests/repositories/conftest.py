"""Shared fixtures for repository tests."""

import pytest

from tests.factories import GameFactory


@pytest.fixture
def sample_game(db_session, admin_user, default_system):
    """Create a draft game for repository testing."""
    return GameFactory(
        db_session,
        gm_id=admin_user.id,
        system_id=default_system.id,
    )


@pytest.fixture
def published_game(db_session, admin_user, default_system):
    """Create an open/published game for repository testing."""
    return GameFactory(
        db_session,
        gm_id=admin_user.id,
        system_id=default_system.id,
        name="Published Game",
        type="campaign",
        status="open",
        msg_id="123456789",
        party_size=5,
        xp="seasoned",
        characters="pregen",
        length="Long",
    )
