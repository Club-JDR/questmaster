"""Tests for GameSessionService."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from website.exceptions import SessionConflictError, ValidationError
from website.models import GameSession
from website.services.game_session import GameSessionService
from website.utils.timezone import APP_TIMEZONE


class TestGameSessionService:
    def test_create(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 1, 20, 0, tzinfo=timezone.utc)
        end = datetime(2025, 9, 1, 23, 0, tzinfo=timezone.utc)
        session = service.create(sample_game, start, end)
        assert session.id is not None
        assert session.game_id == sample_game.id

    def test_create_invalid_times(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 1, 23, 0, tzinfo=timezone.utc)
        end = datetime(2025, 9, 1, 20, 0, tzinfo=timezone.utc)
        with pytest.raises(ValidationError):
            service.create(sample_game, start, end)

    def test_create_rejects_implausibly_long_session(self, db_session, sample_game):
        """A session spanning more than the allowed max (e.g. an end-year typo) is rejected."""
        service = GameSessionService()
        start = datetime(2024, 7, 31, 20, 30, tzinfo=timezone.utc)
        end = datetime(2025, 7, 31, 23, 0, tzinfo=timezone.utc)  # one-year typo -> ~8762h
        with pytest.raises(ValidationError):
            service.create(sample_game, start, end)

    def test_create_conflict(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 1, 20, 0, tzinfo=timezone.utc)
        end = datetime(2025, 9, 1, 23, 0, tzinfo=timezone.utc)
        service.create(sample_game, start, end)
        # Overlapping session
        with pytest.raises(SessionConflictError):
            service.create(sample_game, start, end)

    def test_delete(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 2, 20, 0, tzinfo=timezone.utc)
        end = datetime(2025, 9, 2, 23, 0, tzinfo=timezone.utc)
        session = service.create(sample_game, start, end)
        session_id = session.id
        service.delete(session)
        assert db_session.get(GameSession, session_id) is None

    def test_find_in_range(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 9, 3, 20, 0, tzinfo=timezone.utc)
        end = datetime(2025, 9, 3, 23, 0, tzinfo=timezone.utc)
        service.create(sample_game, start, end)
        results = service.find_in_range(
            datetime(2025, 9, 1, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 9, 30, 23, 59, tzinfo=timezone.utc),
        )
        assert len(results) >= 1

    def test_update_valid_times(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 10, 1, 20, 0, tzinfo=timezone.utc)
        end = datetime(2025, 10, 1, 23, 0, tzinfo=timezone.utc)
        session = service.create(sample_game, start, end)

        new_start = datetime(2025, 10, 1, 19, 0, tzinfo=timezone.utc)
        new_end = datetime(2025, 10, 1, 22, 0, tzinfo=timezone.utc)
        updated = service.update(session, new_start, new_end)

        assert updated.start == new_start
        assert updated.end == new_end
        assert updated.id == session.id

    def test_update_invalid_times(self, db_session, sample_game):
        service = GameSessionService()
        session = service.create(
            sample_game,
            datetime(2025, 10, 2, 20, 0, tzinfo=timezone.utc),
            datetime(2025, 10, 2, 23, 0, tzinfo=timezone.utc),
        )

        with pytest.raises(ValidationError):
            service.update(
                session,
                datetime(2025, 10, 2, 23, 0, tzinfo=timezone.utc),
                datetime(2025, 10, 2, 20, 0, tzinfo=timezone.utc),
            )

    def test_update_rejects_implausibly_long_session(self, db_session, sample_game):
        """Editing a session to an out-of-range duration is rejected."""
        service = GameSessionService()
        session = service.create(
            sample_game,
            datetime(2025, 10, 2, 20, 0, tzinfo=timezone.utc),
            datetime(2025, 10, 2, 23, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(ValidationError):
            service.update(
                session,
                datetime(2025, 10, 2, 20, 0, tzinfo=timezone.utc),
                datetime(2025, 10, 30, 23, 0, tzinfo=timezone.utc),
            )

    def test_update_conflict_with_other_session(self, db_session, sample_game):
        service = GameSessionService()
        service.create(
            sample_game,
            datetime(2025, 10, 3, 20, 0, tzinfo=timezone.utc),
            datetime(2025, 10, 3, 23, 0, tzinfo=timezone.utc),
        )
        session_b = service.create(
            sample_game,
            datetime(2025, 10, 4, 20, 0, tzinfo=timezone.utc),
            datetime(2025, 10, 4, 23, 0, tzinfo=timezone.utc),
        )

        # Try to move session_b into session_a's time slot
        with pytest.raises(SessionConflictError):
            service.update(
                session_b,
                datetime(2025, 10, 3, 21, 0, tzinfo=timezone.utc),
                datetime(2025, 10, 3, 22, 0, tzinfo=timezone.utc),
            )

    def test_update_no_self_conflict(self, db_session, sample_game):
        service = GameSessionService()
        start = datetime(2025, 10, 5, 20, 0, tzinfo=timezone.utc)
        end = datetime(2025, 10, 5, 23, 0, tzinfo=timezone.utc)
        session = service.create(sample_game, start, end)

        # Updating a session to overlap with its own original times should succeed
        new_start = datetime(2025, 10, 5, 19, 0, tzinfo=timezone.utc)
        new_end = datetime(2025, 10, 5, 22, 0, tzinfo=timezone.utc)
        updated = service.update(session, new_start, new_end)

        assert updated.start == new_start
        assert updated.end == new_end

    def test_get_stats_for_period(self, db_session, sample_game):
        service = GameSessionService()
        sample_game.status = "open"  # only published games count toward the breakdown
        service.create(
            sample_game,
            datetime(2025, 11, 10, 20, 0, tzinfo=timezone.utc),
            datetime(2025, 11, 10, 23, 0, tzinfo=timezone.utc),
        )

        stats = service.get_stats_for_period(2025, 11)

        assert stats["base_day"] == datetime(2025, 11, 1, tzinfo=APP_TIMEZONE)
        assert stats["num_os"] == 1
        assert stats["num_campaign"] == 0
        assert len(stats["gm_names"]) == 1

    def test_get_stats_for_period_excludes_draft_games(self, db_session, sample_game):
        """Sessions belonging to draft games must not appear in the monthly breakdown."""
        service = GameSessionService()
        service.create(
            sample_game,
            datetime(2029, 4, 10, 20, 0, tzinfo=timezone.utc),
            datetime(2029, 4, 10, 23, 0, tzinfo=timezone.utc),
        )
        sample_game.status = "draft"
        db_session.flush()

        stats = service.get_stats_for_period(2029, 4)

        assert stats["num_os"] == 0
        assert stats["num_campaign"] == 0
        assert stats["gm_names"] == []
        assert stats["os_games"] == {}

    def test_get_stats_for_period_empty(self, db_session, sample_game):
        service = GameSessionService()

        stats = service.get_stats_for_period(2020, 1)

        assert stats["num_os"] == 0
        assert stats["num_campaign"] == 0
        assert stats["gm_names"] == []

    def test_get_stats_for_period_none_uses_current_month(self, db_session, sample_game):
        """`get_stats_for_period(None, None)` resolves to the real current month.

        Asserts on the specific session created here rather than an absolute
        `num_os` count: the shared dev DB persists between runs (no automatic
        `--drop-db`), so unrelated real games may already have sessions this
        month — an exact `== 0`/`== N` would be flaky depending on when/where
        this runs.
        """
        service = GameSessionService()
        sample_game.status = "open"  # only published games count toward the breakdown
        now = datetime.now(APP_TIMEZONE)
        start = now.replace(hour=20, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23)
        service.create(sample_game, start, end)
        # `_compute_stats` is cached for an hour; bust it so the freshly
        # created session above is reflected in the next read.
        GameSessionService.clear_cache()

        stats = service.get_stats_for_period(None, None)

        assert stats["base_day"].year == now.year
        assert stats["base_day"].month == now.month
        assert stats["base_day"].day == 1
        assert stats["num_os"] >= 1
        assert sample_game.slug in stats["os_games"].get(sample_game.system.name, {})

    def test_clear_cache_busts_every_cached_month(self, db_session):
        """Resets `_compute_stats` via the class, invalidating every cached (year, month)."""
        with patch("website.services.game_session.cache.delete_memoized") as mock_delete:
            GameSessionService.clear_cache()
        mock_delete.assert_called_once_with(GameSessionService._compute_stats)
