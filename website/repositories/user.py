"""User repository for user data access."""

from website.models import User
from website.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entities."""

    model_class = User
    search_columns = [User.id, User.name]

    def base_query(self):
        """Return all users ordered by display name."""
        return self.session.query(User).order_by(User.name)

    def get_active_users(self) -> list[User]:
        """Retrieve all users not marked as inactive.

        Returns:
            List of User instances where not_player_as_of is NULL.
        """
        return self.session.query(User).filter(User.not_player_as_of.is_(None)).all()

    def get_active_user_ids(self) -> list[str]:
        """Retrieve IDs of all users not marked as inactive.

        Uses a scalar query to avoid loading full ORM objects
        (and triggering init_on_load).

        Returns:
            List of user ID strings where not_player_as_of is NULL.
        """
        rows = self.session.query(User.id).filter(User.not_player_as_of.is_(None)).all()
        return [row[0] for row in rows]

    def get_inactive_user_ids(self) -> list[str]:
        """Retrieve IDs of all users marked as inactive.

        Uses a scalar query to avoid loading full ORM objects
        (and triggering init_on_load).

        Returns:
            List of user ID strings where not_player_as_of is set.
        """
        rows = self.session.query(User.id).filter(User.not_player_as_of.isnot(None)).all()
        return [row[0] for row in rows]

    def update_fields(self, user_id: str, values: dict) -> None:
        """Apply a partial column update without loading the ORM object.

        Uses a Core UPDATE so the write is not suppressed by the display-name
        resolution performed in ``User.init_on_load`` (which, in background
        contexts, sets ``name`` at load time and makes an identical ORM
        assignment a no-op).

        Args:
            user_id: Discord user ID.
            values: Mapping of column names to new values.
        """
        if not values:
            return
        self.session.query(User).filter(User.id == user_id).update(
            values, synchronize_session=False
        )

    def get_by_ids(self, ids: list[str]) -> list[User]:
        """Retrieve users by a list of IDs.

        Args:
            ids: List of user ID strings.

        Returns:
            List of User instances matching the given IDs.
        """
        if not ids:
            return []
        return self.session.query(User).filter(User.id.in_(ids)).all()

    def get_inactive_users(self) -> list[User]:
        """Retrieve all users marked as inactive.

        Returns:
            List of User instances where not_player_as_of is set.
        """
        return self.session.query(User).filter(User.not_player_as_of.isnot(None)).all()
