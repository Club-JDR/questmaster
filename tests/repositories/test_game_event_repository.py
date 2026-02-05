import pytest
from datetime import datetime, timezone
from website.models import Game, GameEvent
from website.repositories.game_event import GameEventRepository


@pytest.fixture
def sample_game(db_session):
    game = Game(
        name="EventTestGame",
        slug="event-test-game",
        type="oneshot",
        length="1 session",
        gm_id="664487064577900594",
        system_id=1,
        description="A test game for event tests",
        restriction="all",
        party_size=4,
        date=datetime(2025, 7, 10, 20, 30, tzinfo=timezone.utc),
        session_length=3.5,
        status="draft",
    )
    db_session.add(game)
    db_session.flush()
    yield game
    db_session.rollback()


class TestGameEventRepository:
    def test_log_creates_event(self, db_session, sample_game):
        repo = GameEventRepository()
        event = repo.log("create", sample_game.id, "Game created.")
        assert event.id is not None
        assert event.action == "create"
        assert event.game_id == sample_game.id
        assert event.description == "Game created."

    def test_log_without_description(self, db_session, sample_game):
        repo = GameEventRepository()
        event = repo.log("edit", sample_game.id)
        assert event.id is not None
        assert event.action == "edit"
        assert event.description is None

    def test_log_sets_timestamp(self, db_session, sample_game):
        repo = GameEventRepository()
        event = repo.log("create", sample_game.id)
        assert event.timestamp is not None

    def test_inherits_get_by_id(self, db_session, sample_game):
        repo = GameEventRepository()
        event = repo.log("create", sample_game.id, "Test")
        found = repo.get_by_id(event.id)
        assert found is not None
        assert found.id == event.id

    def test_inherits_count(self, db_session, sample_game):
        repo = GameEventRepository()
        initial = repo.count()
        repo.log("create", sample_game.id)
        assert repo.count() == initial + 1
