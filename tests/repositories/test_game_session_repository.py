"""Tests for GameSessionRepository."""

from datetime import datetime

import pytest

from website.models import GameSession
from website.repositories.game_session import GameSessionRepository


class TestGameSessionRepository:
    def test_find_in_range(self, db_session, sample_game):
        repo = GameSessionRepository()
        start = datetime(2025, 8, 1, 20, 0)
        end = datetime(2025, 8, 1, 23, 0)
        session = GameSession(start=start, end=end, game_id=sample_game.id)
        repo.add(session)

        results = repo.find_in_range(datetime(2025, 8, 1, 0, 0), datetime(2025, 8, 1, 23, 59))
        assert any(s.id == session.id for s in results)

    def test_find_in_range_excludes_outside(self, db_session, sample_game):
        repo = GameSessionRepository()
        start = datetime(2025, 8, 1, 20, 0)
        end = datetime(2025, 8, 1, 23, 0)
        session = GameSession(start=start, end=end, game_id=sample_game.id)
        repo.add(session)

        # Search in a different month
        results = repo.find_in_range(datetime(2025, 9, 1, 0, 0), datetime(2025, 9, 30, 23, 59))
        assert not any(s.id == session.id for s in results)

    def test_add(self, db_session, sample_game):
        repo = GameSessionRepository()
        session = GameSession(
            start=datetime(2025, 8, 2, 20, 0),
            end=datetime(2025, 8, 2, 23, 0),
            game_id=sample_game.id,
        )
        repo.add(session)
        assert session.id is not None

    def test_delete(self, db_session, sample_game):
        repo = GameSessionRepository()
        session = GameSession(
            start=datetime(2025, 8, 3, 20, 0),
            end=datetime(2025, 8, 3, 23, 0),
            game_id=sample_game.id,
        )
        repo.add(session)
        session_id = session.id
        repo.delete(session)
        assert repo.get_by_id(session_id) is None
