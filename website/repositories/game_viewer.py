"""GameViewer repository for data access."""

from sqlalchemy.orm import joinedload

from website.models import GameViewer, User
from website.repositories.base import BaseRepository


class GameViewerRepository(BaseRepository[GameViewer]):
    """Repository for GameViewer entities (spectator follow signals)."""

    model_class = GameViewer

    def get(self, game_id: int, user_id: str) -> GameViewer | None:
        """Get a single follow record by its composite key.

        Args:
            game_id: Game ID.
            user_id: User ID.

        Returns:
            The GameViewer instance, or None if not following.
        """
        return self.session.get(GameViewer, (game_id, user_id))

    def list_for_game(self, game_id: int) -> list[GameViewer]:
        """List everyone following a game as a spectator, with ``user`` eager-loaded.

        Args:
            game_id: Game ID.

        Returns:
            List of GameViewer instances, ordered by the follower's name.
        """
        return (
            self.session.query(GameViewer)
            .join(User, GameViewer.user_id == User.id)
            .options(joinedload(GameViewer.user))
            .filter(GameViewer.game_id == game_id)
            .order_by(User.name)
            .all()
        )
