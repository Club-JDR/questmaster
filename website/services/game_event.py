"""GameEvent service for audit trail management."""

from website.extensions import db
from website.models import GameEvent
from website.repositories.game_event import GameEventRepository


class GameEventService:
    """Service layer for game event logging.

    Provides transaction-safe event recording for the game audit trail.
    """

    def __init__(self, repository=None):
        self.repo = repository or GameEventRepository()

    def get_recent(self, limit: int = 200) -> list[GameEvent]:
        """Get the most recent game events for the audit trail.

        Args:
            limit: Maximum number of events to return. Defaults to 200.

        Returns:
            List of GameEvent instances ordered by timestamp (newest first).
        """
        return self.repo.get_recent(limit)

    def log_event(
        self, action: str, game_id: int, description: str | None = None, user_id: str | None = None
    ) -> GameEvent:
        """Log a game event and commit the transaction.

        Args:
            action: Event action type (create, edit, delete, etc.).
            game_id: ID of the related game.
            description: Optional human-readable description.
            user_id: Optional ID of the user that performed the action.

        Returns:
            Created GameEvent instance.
        """
        event = self.repo.log(action, game_id, description, user_id)
        db.session.commit()
        return event
