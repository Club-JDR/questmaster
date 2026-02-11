import uuid

import pytest
from datetime import datetime, timezone
from website.models import Game, GameEvent
from website.services.game_event import GameEventService

from tests.constants import TEST_ADMIN_USER_ID


@pytest.fixture
def sample_game(db_session):
    unique = uuid.uuid4().hex[:8]
    game = Game(
        name=f"EventServiceTestGame-{unique}",
        slug=f"event-service-test-game-{unique}",
        type="oneshot",
        length="1 session",
        gm_id=TEST_ADMIN_USER_ID,
        system_id=1,
        description="A test game for event service tests",
        restriction="all",
        party_size=4,
        date=datetime(2025, 7, 10, 20, 30, tzinfo=timezone.utc),
        session_length=3.5,
        status="draft",
    )
    db_session.add(game)
    db_session.flush()
    yield game


class TestGameEventService:
    def test_log_event(self, db_session, sample_game):
        service = GameEventService()
        event = service.log_event("create", sample_game.id, "Game created.")
        assert event.id is not None
        assert event.action == "create"
        assert event.game_id == sample_game.id
        assert event.description == "Game created."

    def test_log_event_without_description(self, db_session, sample_game):
        service = GameEventService()
        event = service.log_event("edit", sample_game.id)
        assert event.id is not None
        assert event.description is None

    def test_log_event_persists(self, db_session, sample_game):
        service = GameEventService()
        event = service.log_event("create", sample_game.id, "Persisted event")
        found = db_session.get(GameEvent, event.id)
        assert found is not None
        assert found.description == "Persisted event"
