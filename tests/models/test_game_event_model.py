import pytest
from datetime import datetime, timezone
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
    )


def test_game_event_to_dict(sample_game_event):
    data = sample_game_event.to_dict()
    assert data["id"] == 1
    assert data["timestamp"] == sample_game_event.timestamp
    assert data["action"] == "create"
    assert data["game_id"] == 42
    assert data["description"] == "Test game event"


def test_game_event_to_json(sample_game_event):
    json_data = sample_game_event.to_json()
    assert json_data == sample_game_event.to_dict()
    assert json_data["action"] == "create"


def test_game_event_json_property(sample_game_event):
    assert sample_game_event.json == sample_game_event.to_dict()


def test_game_event_from_dict():
    timestamp = datetime(2025, 1, 2, 14, 0, tzinfo=timezone.utc)
    data = {
        "id": 2,
        "timestamp": timestamp,
        "action": "edit-session",
        "game_id": 99,
        "description": "Edited session",
    }
    event = GameEvent.from_dict(data)
    assert event.id == 2
    assert event.timestamp == timestamp
    assert event.action == "edit-session"
    assert event.game_id == 99
    assert event.description == "Edited session"


def test_game_event_from_json_alias():
    timestamp = datetime(2025, 1, 3, 10, 30, tzinfo=timezone.utc)
    data = {
        "id": 3,
        "timestamp": timestamp,
        "action": "delete",
        "game_id": 101,
        "description": "Deleted game",
    }
    event = GameEvent.from_json(data)
    assert event.id == 3
    assert event.timestamp == timestamp
    assert event.action == "delete"
    assert event.game_id == 101
    assert event.description == "Deleted game"


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
    )
    e2 = GameEvent(
        id=1,
        timestamp=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        action="create",
        game_id=42,
        description="Test game event",
    )
    e3 = GameEvent(
        id=2,
        timestamp=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        action="edit",
        game_id=42,
        description="Different event",
    )
    assert e1 == e2
    assert e1 != e3
