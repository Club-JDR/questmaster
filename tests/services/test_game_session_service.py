"""Tests for GameSessionService."""

from datetime import datetime

import pytest

from website.exceptions import SessionConflictError, ValidationError
from website.models import GameSession
from website.services.game_session import GameSessionService


class TestGameSessionService:
    def test_create(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 1, 20, 0)
        end = datetime(2025, 9, 1, 23, 0)
        session = service.create(sample_game, start, end)
        assert session.id is not None
        assert session.game_id == sample_game.id

    def test_create_invalid_times(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 1, 23, 0)
        end = datetime(2025, 9, 1, 20, 0)
        with pytest.raises(ValidationError):
            service.create(sample_game, start, end)

    def test_create_conflict(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 1, 20, 0)
        end = datetime(2025, 9, 1, 23, 0)
        service.create(sample_game, start, end)
        # Overlapping session
        with pytest.raises(SessionConflictError):
            service.create(sample_game, start, end)

    def test_delete(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 2, 20, 0)
        end = datetime(2025, 9, 2, 23, 0)
        session = service.create(sample_game, start, end)
        session_id = session.id
        service.delete(session)
        assert db_session.get(GameSession, session_id) is None

    def test_find_in_range(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 3, 20, 0)
        end = datetime(2025, 9, 3, 23, 0)
        service.create(sample_game, start, end)
        results = service.find_in_range(datetime(2025, 9, 1, 0, 0), datetime(2025, 9, 30, 23, 59))
        assert len(results) >= 1

    def test_update_valid_times(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 10, 1, 20, 0)
        end = datetime(2025, 10, 1, 23, 0)
        session = service.create(sample_game, start, end)

        new_start = datetime(2025, 10, 1, 19, 0)
        new_end = datetime(2025, 10, 1, 22, 0)
        updated = service.update(session, new_start, new_end)

        assert updated.start == new_start
        assert updated.end == new_end
        assert updated.id == session.id

    def test_update_invalid_times(self, db_session, sample_game):
        service = GameSessionService()
        session = service.create(
            sample_game, datetime(2025, 10, 2, 20, 0), datetime(2025, 10, 2, 23, 0)
        )

        with pytest.raises(ValidationError):
            service.update(session, datetime(2025, 10, 2, 23, 0), datetime(2025, 10, 2, 20, 0))

    def test_update_conflict_with_other_session(self, db_session, sample_game):
        service = GameSessionService()
        service.create(sample_game, datetime(2025, 10, 3, 20, 0), datetime(2025, 10, 3, 23, 0))
        session_b = service.create(
            sample_game, datetime(2025, 10, 4, 20, 0), datetime(2025, 10, 4, 23, 0)
        )

        # Try to move session_b into session_a's time slot
        with pytest.raises(SessionConflictError):
            service.update(
                session_b,
                datetime(2025, 10, 3, 21, 0),
                datetime(2025, 10, 3, 22, 0),
            )

    def test_update_no_self_conflict(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 10, 5, 20, 0)
        end = datetime(2025, 10, 5, 23, 0)
        session = service.create(sample_game, start, end)

        # Updating a session to overlap with its own original times should succeed
        new_start = datetime(2025, 10, 5, 19, 0)
        new_end = datetime(2025, 10, 5, 22, 0)
        updated = service.update(session, new_start, new_end)

        assert updated.start == new_start
        assert updated.end == new_end
