"""User repository for user data access."""

from website.models import User
from website.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entities."""

    model_class = User

    def get_active_users(self) -> list[User]:
        """Retrieve all users not marked as inactive.

        Returns:
            List of User instances where not_player_as_of is NULL.
        """
        return self.session.query(User).filter(User.not_player_as_of.is_(None)).all()

    def get_inactive_users(self) -> list[User]:
        """Retrieve all users marked as inactive.

        Returns:
            List of User instances where not_player_as_of is set.
        """
        return self.session.query(User).filter(User.not_player_as_of.isnot(None)).all()
