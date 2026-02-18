"""User service for user-related business logic."""

from datetime import datetime, timezone

from website.exceptions import NotFoundError
from website.extensions import db
from website.models import User
from website.models.user import get_user_profile as _get_user_profile
from website.repositories.user import UserRepository


class UserService:
    """Service layer for User operations.

    Handles user retrieval, creation, and Discord profile management.
    """

    def __init__(self, repository=None):
        self.repo = repository or UserRepository()

    def get_by_id(self, user_id: str) -> User:
        """Get user by ID.

        Args:
            user_id: Discord user ID.

        Returns:
            User instance.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(
                f"User with id {user_id} not found",
                resource_type="User",
                resource_id=user_id,
            )
        return user

    def get_or_create(
        self, user_id: str, name: str = "Inconnu", username: str | None = None
    ) -> tuple[User, bool]:
        """Get an existing user or create a new one.

        Args:
            user_id: Discord user ID.
            name: Display name for new users. Defaults to 'Inconnu'.
            username: Stable Discord username (optional).

        Returns:
            Tuple of (User, created) where created is True if the user was new.
        """
        user = self.repo.get_by_id(user_id)
        if user:
            return user, False
        user = User(id=user_id, name=name, username=username)
        self.repo.add(user)
        db.session.commit()
        user.init_on_load()
        return user, True

    def get_all(self) -> list[User]:
        """Get all users.

        Returns:
            List of all User instances.
        """
        return self.repo.get_all()

    def get_active_users(self) -> list[User]:
        """Get all users not marked as inactive.

        Returns:
            List of active User instances.
        """
        return self.repo.get_active_users()

    def get_active_user_ids(self) -> list[str]:
        """Get IDs of all users not marked as inactive.

        Lightweight query that avoids loading full ORM objects.

        Returns:
            List of active user ID strings.
        """
        return self.repo.get_active_user_ids()

    def get_inactive_users(self) -> list[User]:
        """Get all users marked as inactive.

        Returns:
            List of inactive User instances.
        """
        return self.repo.get_inactive_users()

    def get_inactive_user_ids(self) -> list[str]:
        """Get IDs of all users marked as inactive.

        Lightweight query that avoids loading full ORM objects.

        Returns:
            List of inactive user ID strings.
        """
        return self.repo.get_inactive_user_ids()

    def get_by_ids(self, ids: list[str]) -> list[User]:
        """Get users by a list of IDs.

        Args:
            ids: List of user ID strings.

        Returns:
            List of User instances matching the given IDs.
        """
        return self.repo.get_by_ids(ids)

    @staticmethod
    def get_user_profile(user_id: str, force_refresh: bool = False) -> dict:
        """Fetch a user's Discord profile.

        Args:
            user_id: Discord user ID.
            force_refresh: If True, bypass cache and fetch from Discord.

        Returns:
            Dict with 'name', 'avatar', and optionally 'not_found' keys.
        """
        return _get_user_profile(user_id, force_refresh=force_refresh)

    def mark_inactive(self, user_id: str) -> User:
        """Mark a user as inactive (left the Discord server).

        Args:
            user_id: Discord user ID.

        Returns:
            Updated User instance.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.get_by_id(user_id)
        user.not_player_as_of = datetime.now(timezone.utc)
        db.session.commit()
        return user

    def clear_inactive(self, user_id: str) -> User:
        """Clear the inactive flag for a user (they have rejoined).

        Args:
            user_id: Discord user ID.

        Returns:
            Updated User instance.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.get_by_id(user_id)
        user.not_player_as_of = None
        db.session.commit()
        return user
