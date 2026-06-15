"""GameEvent repository for audit log data access."""

from website.models import GameEvent
from website.repositories.base import BaseRepository


class GameEventRepository(BaseRepository[GameEvent]):
    """Repository for GameEvent entities."""

    model_class = GameEvent

    def get_recent(self, limit: int = 200) -> list[GameEvent]:
        """Retrieve the most recent game events.

        Args:
            limit: Maximum number of events to return. Defaults to 200.

        Returns:
            List of GameEvent instances ordered by timestamp (newest first).
        """
        return (
            self.session.query(GameEvent).order_by(GameEvent.timestamp.desc()).limit(limit).all()
        )

    def log(
        self, action: str, game_id: int, description: str | None = None, user_id: str | None = None
    ) -> GameEvent:
        """Create and persist a new game event.

        Args:
            action: Event action type.
            game_id: ID of the related game.
            description: Optional event description.
            user_id: Optional ID of the user that performed the action.

        Returns:
            Created GameEvent instance.
        """
        event = GameEvent(action=action, game_id=game_id, description=description, user_id=user_id)
        return self.add(event)
