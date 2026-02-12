"""User repository for user data access."""

from website.models import User
from website.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entities."""

    model_class = User
