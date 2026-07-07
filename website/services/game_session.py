"""GameSession service for play session management."""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import TYPE_CHECKING

from config.constants import GAME_STATUS_DRAFT, MAX_SESSION_DURATION_HOURS
from website.exceptions import SessionConflictError, ValidationError
from website.extensions import cache, db
from website.models import GameSession
from website.repositories.game_session import GameSessionRepository
from website.utils.logger import logger

if TYPE_CHECKING:
    from website.models import Game


class GameSessionService:
    """Service layer for GameSession operations.

    Handles session creation, deletion, updates, and conflict detection.
    """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

    def __init__(self, repository=None):
        self.repo = repository or GameSessionRepository()

    def create(self, game: Game, start: datetime, end: datetime) -> GameSession:
        """Create a new game session.

        Args:
            game: Game instance to add the session to.
            start: Session start datetime.
            end: Session end datetime.

        Returns:
            Created GameSession instance.

        Raises:
            ValidationError: If start >= end.
            SessionConflictError: If the session overlaps with an existing one.
        """
        self._validate_times(start, end)

        if self._has_conflict(game, start, end):
            raise SessionConflictError(
                "Session overlaps with an existing session.", game_id=game.id
            )

        session = GameSession(start=start, end=end)
        self.repo.add(session)
        game.sessions.append(session)
        db.session.commit()
        logger.info(f"Session added for game {game.id} from {start} to {end}")
        self._invalidate_stats(game)
        return session

    def delete(self, session: GameSession) -> None:
        """Delete a game session.

        Args:
            session: GameSession instance to delete.
        """
        game = session.game
        game_id = session.game_id
        start = session.start
        end = session.end
        self.repo.delete(session)
        db.session.commit()
        logger.info(f"Session removed for game {game_id} from {start} to {end}")
        self._invalidate_stats(game)

    def update(self, session: GameSession, new_start: datetime, new_end: datetime) -> GameSession:
        """Update a session's start/end times.

        Args:
            session: Existing GameSession instance.
            new_start: New start datetime.
            new_end: New end datetime.

        Returns:
            Updated GameSession instance.

        Raises:
            ValidationError: If new_start >= new_end.
            SessionConflictError: If new times overlap another session.
        """
        self._validate_times(new_start, new_end)

        game = session.game
        if self._has_conflict(game, new_start, new_end, exclude_session_id=session.id):
            raise SessionConflictError(
                "Session overlaps with an existing session.", game_id=game.id
            )

        session.start = new_start
        session.end = new_end
        db.session.commit()
        logger.info(f"Session {session.id} updated to {new_start} - {new_end}")
        self._invalidate_stats(game)
        return session

    def get_by_id_or_404(self, session_id: int) -> GameSession:
        """Get session by ID or abort with 404.

        Args:
            session_id: Session ID.

        Returns:
            GameSession instance.

        Raises:
            NotFound: Flask 404 error.
        """
        return self.repo.get_by_id_or_404(session_id)

    def find_in_range(self, start: datetime, end: datetime) -> list[GameSession]:
        """Find all sessions within a date range.

        Args:
            start: Range start datetime.
            end: Range end datetime.

        Returns:
            List of GameSession instances within the range.
        """
        return self.repo.find_in_range(start, end)

    def get_stats_for_period(self, year: int | None, month: int | None) -> dict:
        """Compute game statistics for a given month.

        Resolves None year/month to the current month, then delegates to the
        cached implementation so the cache key is always a concrete (year, month)
        pair — preventing separate cache entries for the same period when it is
        reached via different URLs.

        Args:
            year: Year to compute stats for, or None for current month.
            month: Month to compute stats for, or None for current month.

        Returns:
            Dict with keys: base_day, last_day, num_os, num_campaign,
            os_games, campaign_games, gm_names.
        """
        if year and month:
            base_day = datetime(year, month, 1)
        else:
            today = datetime.today()
            base_day = today.replace(day=1)
        return self._compute_stats(base_day.year, base_day.month)

    @cache.memoize(timeout=3600)
    def _compute_stats(self, year: int, month: int) -> dict:
        base_day = datetime(year, month, 1)
        last_day = datetime(
            year,
            month,
            calendar.monthrange(year, month)[1],
            23,
            59,
            59,
            999999,
        )

        sessions = self.find_in_range(base_day, last_day)

        num_os = 0
        num_campaign = 0
        os_games: dict[str, dict] = {}
        campaign_games: dict[str, dict] = {}
        gm_names: list[str] = []

        for session in sessions:
            game = session.game
            # Draft (unpublished) games must never contribute to statistics.
            if game.status == GAME_STATUS_DRAFT:
                continue

            if game.type == "oneshot":
                num_os += 1
                self._accumulate_game(os_games, game)
            else:
                num_campaign += 1
                self._accumulate_game(campaign_games, game)

            gm_names.append(game.gm.name)

        return {
            "base_day": base_day,
            "last_day": last_day,
            "num_os": num_os,
            "num_campaign": num_campaign,
            "os_games": os_games,
            "campaign_games": campaign_games,
            "gm_names": gm_names,
        }

    @staticmethod
    def _accumulate_game(bucket: dict[str, dict], game) -> None:
        """Tally one session's game into a system-keyed breakdown bucket.

        Groups games by system name, then by slug, incrementing a per-game
        session ``count`` so a game with several sessions in the month appears
        once with the right tally.

        Args:
            bucket: System-keyed mapping being built (``os_games`` or
                ``campaign_games``); mutated in place.
            game: Game owning the current session.
        """
        system_games = bucket.setdefault(game.system.name, {})
        if game.slug in system_games:
            system_games[game.slug]["count"] += 1
        else:
            system_games[game.slug] = {"name": game.name, "gm": game.gm.name, "count": 1}

    @staticmethod
    def _invalidate_stats(game) -> None:
        """Invalidate dashboard stats for everyone involved in the game.

        A session change shifts the GM's and players' agendas, play hours,
        session counts and rhythm, so their cached dashboard data is dropped.
        """
        from website.services.stats import StatsService

        StatsService().invalidate_for_game(game)

    @staticmethod
    def _validate_times(start: datetime, end: datetime) -> None:
        """Validate a session's start/end pair.

        Ensures the session starts before it ends and does not span an
        implausibly long period. The upper bound guards against date-entry
        typos (e.g. an ``end`` a day, month or year off) that would otherwise be
        stored verbatim and poison play-time statistics.

        Args:
            start: Session start datetime.
            end: Session end datetime.

        Raises:
            ValidationError: If start is not before end, or the duration exceeds
                ``MAX_SESSION_DURATION_HOURS``.
        """
        if start >= end:
            raise ValidationError("Session start must be before end time.")

        if (end - start).total_seconds() / 3600 > MAX_SESSION_DURATION_HOURS:
            raise ValidationError(
                f"Session duration cannot exceed {MAX_SESSION_DURATION_HOURS} hours."
            )

    @staticmethod
    def _has_conflict(game, start_dt, end_dt, exclude_session_id=None):
        for s in game.sessions:
            if exclude_session_id and s.id == exclude_session_id:
                continue
            if not (end_dt <= s.start or start_dt >= s.end):
                return True
        return False
