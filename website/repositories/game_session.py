"""GameSession repository for session data access."""

from website.models import GameSession
from website.repositories.base import BaseRepository


class GameSessionRepository(BaseRepository[GameSession]):
    """Repository for GameSession entities."""

    model_class = GameSession

    def find_in_range(self, start, end) -> list[GameSession]:
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
