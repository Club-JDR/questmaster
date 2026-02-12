from datetime import datetime

import pytest

from website.models.game_session import GameSession


@pytest.fixture
def sample_game_session():
    """Reusable GameSession instance."""
    return GameSession(
        id=1,
        game_id=42,
        start=datetime(2025, 1, 15, 18, 0),
        end=datetime(2025, 1, 15, 21, 0),
    )


def test_to_dict(sample_game_session):
    data = sample_game_session.to_dict()
    assert data["id"] == 1
    assert data["game_id"] == 42
    assert data["start"] == sample_game_session.start.isoformat()
    assert data["end"] == sample_game_session.end.isoformat()


def test_from_dict_creates_game_session():
    start = datetime(2025, 2, 1, 19, 0)
    end = datetime(2025, 2, 1, 22, 0)
    data = {"id": 2, "game_id": 99, "start": start, "end": end}
    session = GameSession.from_dict(data)
    assert isinstance(session, GameSession)
    assert session.id == 2
    assert session.game_id == 99
    assert session.start == start
    assert session.end == end


def test_update_from_dict(sample_game_session):
    new_end = datetime(2025, 1, 15, 22, 30)
    update_data = {"end": new_end}
    updated = sample_game_session.update_from_dict(update_data)
    assert updated is sample_game_session  # in-place update
    assert sample_game_session.end == new_end
    # Unchanged fields remain the same
    assert sample_game_session.id == 1
    assert sample_game_session.game_id == 42


def test_update_from_dict_ignores_unknown_fields(sample_game_session):
    update_data = {"unknown_field": "value", "game_id": 100}
    sample_game_session.update_from_dict(update_data)
    assert not hasattr(sample_game_session, "unknown_field")
    assert sample_game_session.game_id == 100


def test_update_from_dict_ignores_protected_fields(sample_game_session):
    new_end = datetime(2025, 1, 15, 22, 30)
    sample_game_session.update_from_dict({"id": 999, "end": new_end})
    assert sample_game_session.id == 1
    assert sample_game_session.end == new_end
