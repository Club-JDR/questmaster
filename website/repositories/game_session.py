"""GameSession repository for session data access."""

from datetime import datetime

from config.constants import GAME_STATUS_ARCHIVED, GAME_STATUS_DRAFT
from website.models import Game, GameSession
from website.repositories.base import BaseRepository


class GameSessionRepository(BaseRepository[GameSession]):
    """Repository for GameSession entities."""

    model_class = GameSession

    def find_in_range(self, start: datetime, end: datetime) -> list[GameSession]:
        """Find all sessions within a date range.

        Args:
            start: Range start datetime (inclusive).
            end: Range end datetime (inclusive).

        Returns:
            List of GameSession instances within the range.
        """
        return (
            self.session.query(GameSession)
            .filter(GameSession.start >= start, GameSession.end <= end)
            .all()
        )

    def find_due_for_reminder(self, start: datetime, end: datetime) -> list[GameSession]:
        """Find sessions starting within a window that still need a reminder.

        Draft games are excluded since they were never actually published,
        and archived games are excluded since the game is already over.

        Args:
            start: Window start datetime (typically "now"), inclusive.
            end: Window end datetime (typically now + reminder horizon), inclusive.

        Returns:
            List of GameSession instances due a reminder, oldest start first.
        """
        return (
            self.session.query(GameSession)
            .join(Game, GameSession.game_id == Game.id)
            .filter(
                GameSession.reminder_sent.is_(False),
                GameSession.start >= start,
                GameSession.start <= end,
                Game.status.notin_([GAME_STATUS_DRAFT, GAME_STATUS_ARCHIVED]),
            )
            .order_by(GameSession.start)
            .all()
        )
