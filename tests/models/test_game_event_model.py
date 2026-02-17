from datetime import datetime, timezone

import pytest

from website.models.game_event import GameEvent


@pytest.fixture
def sample_game_event():
    """Reusable GameEvent instance (not committed to DB)."""
    return GameEvent(
        id=1,
        timestamp=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        action="create",
        game_id=42,
        description="Test game event",
        user_id="user123",
    )


def test_game_event_to_dict(sample_game_event):
    data = sample_game_event.to_dict()
    assert data["id"] == 1
    assert data["timestamp"] == sample_game_event.timestamp.isoformat()
    assert data["action"] == "create"
    assert data["game_id"] == 42
    assert data["description"] == "Test game event"
    assert data["user_id"] == "user123"


def test_game_event_from_dict():
    timestamp = datetime(2025, 1, 2, 14, 0, tzinfo=timezone.utc)
    data = {
        "id": 2,
        "timestamp": timestamp,
        "action": "edit-session",
        "game_id": 99,
        "description": "Edited session",
        "user_id": "user456",
    }
    event = GameEvent.from_dict(data)
    assert event.id == 2
    assert event.timestamp == timestamp
    assert event.action == "edit-session"
    assert event.game_id == 99
    assert event.description == "Edited session"
    assert event.user_id == "user456"


def test_game_event_update_from_dict(sample_game_event):
    new_data = {
        "action": "register",
        "description": "Player registered",
    }
    sample_game_event.update_from_dict(new_data)
    assert sample_game_event.action == "register"
    assert sample_game_event.description == "Player registered"
    # Unchanged fields remain
    assert sample_game_event.id == 1
    assert sample_game_event.game_id == 42


def test_game_event_repr(sample_game_event):
    repr_str = repr(sample_game_event)
    assert "GameEvent" in repr_str
    assert str(sample_game_event.id) in repr_str


def test_game_event_eq_and_ne():
    e1 = GameEvent(
        id=1,
        timestamp=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        action="create",
        game_id=42,
        description="Test game event",
        user_id="user123",
    )
    e2 = GameEvent(
        id=1,
        timestamp=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        action="create",
        game_id=42,
        description="Test game event",
        user_id="user123",
    )
    e3 = GameEvent(
        id=2,
        timestamp=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        action="edit",
        game_id=42,
        description="Different event",
        user_id="user456",
    )
    assert e1 == e2
    assert e1 != e3


def test_game_event_update_from_dict_ignores_protected_fields(sample_game_event):
    sample_game_event.update_from_dict(
        {
            "id": 999,
            "game": "should_be_ignored",
            "action": "edit",
        }
    )
    # Protected field "id" unchanged
    assert sample_game_event.id == 1
    # Relationship field "game" unchanged (still None for detached instance)
    assert sample_game_event.game_id == 42
    # Regular field updated normally
    assert sample_game_event.action == "edit"
