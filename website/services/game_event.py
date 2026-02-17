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
