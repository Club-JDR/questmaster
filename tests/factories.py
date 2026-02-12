"""Test data factories for QuestMaster models.

Provides factory_boy factories that reduce boilerplate across test files.
Each factory generates valid model instances with sensible defaults;
tests only need to override the fields relevant to the scenario under test.

Usage::

    # In a test or fixture:
    game = GameFactory(db_session, name="My Game", status="open")
    user = UserFactory(db_session)
    trophy = TrophyFactory(db_session, name="First Blood", unique=True)
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from website import db
from website.models import (
    Channel,
    Game,
    GameEvent,
    GameSession,
    SpecialEvent,
    System,
    Trophy,
    UserTrophy,
    User,
    Vtt,
)

from tests.constants import TEST_ADMIN_USER_ID


def _unique_id():
    return uuid4().hex[:8]


def _unique_discord_id():
    """Generate a unique 18-digit Discord-style ID."""
    return str(uuid4().int)[:18]


def GameFactory(session, **overrides):
    """Create and persist a Game instance with sensible defaults.

    Args:
        session: The SQLAlchemy session (typically the ``db_session`` fixture).
        **overrides: Any Game column values to override.

    Returns:
        A flushed Game instance with a generated ID.
    """
    uid = _unique_id()
    defaults = {
        "name": f"Test Game {uid}",
        "slug": f"test-game-{uid}",
        "type": "oneshot",
        "length": "3h",
        "gm_id": TEST_ADMIN_USER_ID,
        "system_id": 1,
        "description": "A test game",
        "restriction": "all",
        "party_size": 4,
        "xp": "all",
        "date": datetime(2025, 6, 15, 20, 0, tzinfo=timezone.utc),
        "session_length": Decimal("3.0"),
        "characters": "self",
        "status": "draft",
    }
    defaults.update(overrides)
    game = Game(**defaults)
    session.add(game)
    session.flush()
    return game


def UserFactory(session, **overrides):
    """Create and persist a User instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Any User column values to override.

    Returns:
        A flushed User instance.
    """
    defaults = {
        "id": _unique_discord_id(),
        "name": f"TestUser-{_unique_id()}",
    }
    defaults.update(overrides)
    user = User(**defaults)
    session.add(user)
    session.flush()
    return user


def TrophyFactory(session, **overrides):
    """Create and persist a Trophy instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Any Trophy column values to override.

    Returns:
        A flushed Trophy instance.
    """
    uid = _unique_id()
    defaults = {
        "name": f"Test Trophy {uid}",
        "unique": False,
        "icon": None,
    }
    defaults.update(overrides)
    trophy = Trophy(**defaults)
    session.add(trophy)
    session.flush()
    return trophy


def UserTrophyFactory(session, **overrides):
    """Create and persist a UserTrophy instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Must include ``user_id`` and ``trophy_id``.

    Returns:
        A flushed UserTrophy instance.
    """
    defaults = {
        "quantity": 1,
    }
    defaults.update(overrides)
    user_trophy = UserTrophy(**defaults)
    session.add(user_trophy)
    session.flush()
    return user_trophy


def GameSessionFactory(session, **overrides):
    """Create and persist a GameSession instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Must include ``game_id``.

    Returns:
        A flushed GameSession instance.
    """
    defaults = {
        "start": datetime(2025, 9, 1, 20, 0),
        "end": datetime(2025, 9, 1, 23, 0),
    }
    defaults.update(overrides)
    game_session = GameSession(**defaults)
    session.add(game_session)
    session.flush()
    return game_session


def GameEventFactory(session, **overrides):
    """Create and persist a GameEvent instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Must include ``game_id`` and ``action``.

    Returns:
        A flushed GameEvent instance.
    """
    defaults = {
        "action": "create",
        "description": "Test event",
    }
    defaults.update(overrides)
    event = GameEvent(**defaults)
    session.add(event)
    session.flush()
    return event


def SystemFactory(session, **overrides):
    """Create and persist a System instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Any System column values to override.

    Returns:
        A flushed System instance.
    """
    uid = _unique_id()
    defaults = {
        "name": f"Test System {uid}",
        "icon": "test.png",
    }
    defaults.update(overrides)
    system = System(**defaults)
    session.add(system)
    session.flush()
    return system


def VttFactory(session, **overrides):
    """Create and persist a Vtt instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Any Vtt column values to override.

    Returns:
        A flushed Vtt instance.
    """
    uid = _unique_id()
    defaults = {
        "name": f"Test VTT {uid}",
        "icon": "test.png",
    }
    defaults.update(overrides)
    vtt = Vtt(**defaults)
    session.add(vtt)
    session.flush()
    return vtt


def ChannelFactory(session, **overrides):
    """Create and persist a Channel instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Any Channel column values to override.

    Returns:
        A flushed Channel instance.
    """
    defaults = {
        "id": _unique_discord_id(),
        "type": "oneshot",
        "size": 20,
    }
    defaults.update(overrides)
    channel = Channel(**defaults)
    session.add(channel)
    session.flush()
    return channel


def SpecialEventFactory(session, **overrides):
    """Create and persist a SpecialEvent instance.

    Args:
        session: The SQLAlchemy session.
        **overrides: Any SpecialEvent column values to override.

    Returns:
        A flushed SpecialEvent instance.
    """
    uid = _unique_id()
    defaults = {
        "name": f"Test Event {uid}",
        "emoji": "\U0001f3b2",
        "color": 0xFF5733,
        "active": False,
    }
    defaults.update(overrides)
    event = SpecialEvent(**defaults)
    session.add(event)
    session.flush()
    return event
