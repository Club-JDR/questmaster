import uuid

import pytest
from datetime import datetime, timezone
from website.models import Game, GameSession
from website.exceptions import ValidationError, SessionConflictError
from website.services.game_session import GameSessionService


@pytest.fixture
def sample_game(db_session):
    unique = uuid.uuid4().hex[:8]
    game = Game(
        name=f"SessionServiceTestGame-{unique}",
        slug=f"session-service-test-game-{unique}",
        type="oneshot",
        length="1 session",
        gm_id="664487064577900594",
        system_id=1,
        description="A test game for session service tests",
        restriction="all",
        party_size=4,
        date=datetime(2025, 9, 1, 20, 0, tzinfo=timezone.utc),
        session_length=3.0,
        status="draft",
    )
    db_session.add(game)
    db_session.flush()
    yield game
    # Service tests commit, so rollback won't clean up.
    # Delete explicitly instead.
    db_session.execute(
        GameSession.__table__.delete().where(GameSession.game_id == game.id)
    )
    db_session.execute(Game.__table__.delete().where(Game.id == game.id))
    db_session.commit()


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
