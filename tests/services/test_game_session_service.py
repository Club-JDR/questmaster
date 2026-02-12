"""Tests for GameSessionService."""

import pytest
from datetime import datetime

from website.models import GameSession
from website.exceptions import ValidationError, SessionConflictError
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
        results = service.find_in_range(
            datetime(2025, 9, 1, 0, 0), datetime(2025, 9, 30, 23, 59)
        )
        assert len(results) >= 1
