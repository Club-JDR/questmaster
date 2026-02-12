"""GameEvent repository for audit log data access."""

from website.models import GameEvent
from website.repositories.base import BaseRepository


class GameEventRepository(BaseRepository[GameEvent]):
    """Repository for GameEvent entities."""

    model_class = GameEvent

    def log(self, action: str, game_id: int, description: str = None) -> GameEvent:
        """Create and persist a new game event.

        Args:
            action: Event action type.
            game_id: ID of the related game.
            description: Optional event description.

        Returns:
            Created GameEvent instance.
        """
        event = GameEvent(
            action=action,
            game_id=game_id,
            description=description,
        )
        return self.add(event)
