"""Tests for GameEventService."""

import pytest

from website.models import GameEvent
from website.services.game_event import GameEventService


class TestGameEventService:
    def test_log_event(self, db_session, sample_game, admin_user):
        service = GameEventService()
        event = service.log_event("create", sample_game.id, "Game created.", user_id=admin_user.id)
        assert event.id is not None
        assert event.action == "create"
        assert event.game_id == sample_game.id
        assert event.description == "Game created."
        assert event.user_id == admin_user.id

    def test_log_event_without_description(self, db_session, sample_game):
        service = GameEventService()
        event = service.log_event("edit", sample_game.id)
        assert event.id is not None
        assert event.description is None
        assert event.user_id is None

    def test_log_event_persists(self, db_session, sample_game, admin_user):
        service = GameEventService()
        event = service.log_event(
            "create", sample_game.id, "Persisted event", user_id=admin_user.id
        )
        found = db_session.get(GameEvent, event.id)
        assert found is not None
        assert found.description == "Persisted event"
        assert found.user_id == admin_user.id
