"""GameSession service for play session management."""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING

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
        if start >= end:
            raise ValidationError("Session start must be before end time.")

        if self._has_conflict(game, start, end):
            raise SessionConflictError(
                "Session overlaps with an existing session.", game_id=game.id
            )

        session = GameSession(start=start, end=end)
        self.repo.add(session)
        game.sessions.append(session)
        db.session.commit()
        logger.info(f"Session added for game {game.id} from {start} to {end}")
        return session

    def delete(self, session: GameSession) -> None:
        """Delete a game session.

        Args:
            session: GameSession instance to delete.
        """
        game_id = session.game_id
        start = session.start
        end = session.end
        self.repo.delete(session)
        db.session.commit()
        logger.info(f"Session removed for game {game_id} from {start} to {end}")

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
        if new_start >= new_end:
            raise ValidationError("Session start must be before end time.")

        game = session.game
        if self._has_conflict(game, new_start, new_end, exclude_session_id=session.id):
            raise SessionConflictError(
                "Session overlaps with an existing session.", game_id=game.id
            )

        session.start = new_start
        session.end = new_end
        db.session.commit()
        logger.info(f"Session {session.id} updated to {new_start} - {new_end}")
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

    @cache.memoize(timeout=3600)
    def get_stats_for_period(self, year: int | None, month: int | None) -> dict:
        """Compute game statistics for a given month.

        Aggregates session data into per-system, per-game counts for
        oneshots and campaigns, along with GM participation.

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

        last_day = datetime(
            base_day.year,
            base_day.month,
            calendar.monthrange(base_day.year, base_day.month)[1],
            23,
            59,
            59,
            999999,
        )

        sessions = self.find_in_range(base_day, last_day)

        num_os = 0
        num_campaign = 0
        os_games: dict = defaultdict(lambda: defaultdict(self._default_game_entry))
        campaign_games: dict = defaultdict(lambda: defaultdict(self._default_game_entry))
        gm_names: list[str] = []

        for session in sessions:
            game = session.game
            system = game.system.name
            slug = game.slug
            entry = {"name": game.name, "gm": game.gm.name, "count": 1}

            if game.type == "oneshot":
                num_os += 1
                if slug in os_games[system]:
                    os_games[system][slug]["count"] += 1
                else:
                    os_games[system][slug] = entry
            else:
                num_campaign += 1
                if slug in campaign_games[system]:
                    campaign_games[system][slug]["count"] += 1
                else:
                    campaign_games[system][slug] = entry

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
    def _default_game_entry():
        """Return a default game entry dict for stats aggregation."""
        return {"count": 0, "gm": ""}

    @staticmethod
    def _has_conflict(game, start_dt, end_dt, exclude_session_id=None):
        for s in game.sessions:
            if exclude_session_id and s.id == exclude_session_id:
                continue
            if not (end_dt <= s.start or start_dt >= s.end):
                return True
        return False
