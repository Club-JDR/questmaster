"""User service for user-related business logic."""

from website.exceptions import NotFoundError
from website.extensions import db
from website.models import User
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

    def get_or_create(self, user_id: str, name: str = "Inconnu") -> tuple[User, bool]:
        """Get an existing user or create a new one.

        Args:
            user_id: Discord user ID.
            name: Display name for new users. Defaults to 'Inconnu'.

        Returns:
            Tuple of (User, created) where created is True if the user was new.
        """
        user = self.repo.get_by_id(user_id)
        if user:
            return user, False
        user = User(id=user_id, name=name)
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
