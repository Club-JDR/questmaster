import uuid

import pytest
from datetime import datetime, timezone, timedelta
from website.models import Game, GameSession
from website.repositories.game_session import GameSessionRepository


@pytest.fixture
def sample_game(db_session):
    unique = uuid.uuid4().hex[:8]
    game = Game(
        name=f"SessionRepoTestGame-{unique}",
        slug=f"session-repo-test-game-{unique}",
        type="oneshot",
        length="1 session",
        gm_id="664487064577900594",
        system_id=1,
        description="A test game for session repo tests",
        restriction="all",
        party_size=4,
        date=datetime(2025, 8, 1, 20, 0, tzinfo=timezone.utc),
        session_length=3.0,
        status="draft",
    )
    db_session.add(game)
    db_session.flush()
    yield game
    db_session.rollback()


class TestGameSessionRepository:
    def test_find_in_range(self, db_session, sample_game):
        repo = GameSessionRepository()
        start = datetime(2025, 8, 1, 20, 0)
        end = datetime(2025, 8, 1, 23, 0)
        session = GameSession(start=start, end=end, game_id=sample_game.id)
        repo.add(session)

        results = repo.find_in_range(
            datetime(2025, 8, 1, 0, 0), datetime(2025, 8, 1, 23, 59)
        )
        assert any(s.id == session.id for s in results)

    def test_find_in_range_excludes_outside(self, db_session, sample_game):
        repo = GameSessionRepository()
        start = datetime(2025, 8, 1, 20, 0)
        end = datetime(2025, 8, 1, 23, 0)
        session = GameSession(start=start, end=end, game_id=sample_game.id)
        repo.add(session)

        # Search in a different month
        results = repo.find_in_range(
            datetime(2025, 9, 1, 0, 0), datetime(2025, 9, 30, 23, 59)
        )
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
