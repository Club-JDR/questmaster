"""Tests for GameEventRepository."""

import pytest

from website.models import GameEvent
from website.repositories.game_event import GameEventRepository


class TestGameEventRepository:
    def test_log_creates_event(self, db_session, sample_game, admin_user):
        repo = GameEventRepository()
        event = repo.log("create", sample_game.id, "Game created.", user_id=admin_user.id)
        assert event.id is not None
        assert event.action == "create"
        assert event.game_id == sample_game.id
        assert event.description == "Game created."
        assert event.user_id == admin_user.id

    def test_log_without_description(self, db_session, sample_game):
        repo = GameEventRepository()
        event = repo.log("edit", sample_game.id)
        assert event.id is not None
        assert event.action == "edit"
        assert event.description is None
        assert event.user_id is None

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
