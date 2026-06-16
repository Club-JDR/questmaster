"""GameEvent repository for audit log data access."""

from sqlalchemy import String, cast, or_

from website.models import Game, GameEvent, User
from website.repositories.base import BaseRepository


class GameEventRepository(BaseRepository[GameEvent]):
    """Repository for GameEvent entities."""

    model_class = GameEvent

    def base_query(self):
        """Return all events ordered newest-first, joined to game and user."""
        return (
            self.session.query(GameEvent)
            .outerjoin(GameEvent.game)
            .outerjoin(GameEvent.user)
            .order_by(GameEvent.timestamp.desc())
        )

    def apply_search(self, query, search: str | None):
        """Search across action, description, game slug, and user name.

        Args:
            query: The query to filter.
            search: Search term, or None/empty to skip filtering.

        Returns:
            The (possibly) filtered query.
        """
        if not search:
            return query
        term = f"%{search}%"
        return query.filter(
            or_(
                cast(GameEvent.action, String).ilike(term),
                GameEvent.description.ilike(term),
                Game.slug.ilike(term),
                User.name.ilike(term),
            )
        )

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
