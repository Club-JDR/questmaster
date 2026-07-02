"""User service for user-related business logic."""

import re
from datetime import datetime, timezone

from website.exceptions import NotFoundError
from website.extensions import db
from website.models import User
from website.models.user import get_user_profile as _get_user_profile
from website.repositories.base import Pagination
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

    def list_paginated(
        self, page: int = 1, per_page: int = 25, search: str | None = None
    ) -> Pagination:
        """Get a paginated, optionally searched, list of users.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against user ID and name.

        Returns:
            Pagination result of User instances.
        """
        return self.repo.paginate(page=page, per_page=per_page, search=search)

    def search(self, term: str, limit: int = 10) -> list[User]:
        """Return users matching a search term (id, name, or username).

        Args:
            term: Free-text search term (matched case-insensitively).
            limit: Maximum number of results to return.

        Returns:
            List of matching User instances (possibly empty).
        """
        if not term or not term.strip():
            return []
        return self.repo.paginate(page=1, per_page=limit, search=term.strip()).items

    def resolve_input(self, value: str) -> User | None:
        """Resolve a Discord ID or a username/display name to a known user.

        A purely numeric value is treated as a Discord ID (created on the fly
        via :meth:`get_or_create`, preserving the existing behaviour). Any other
        value is matched against existing users; it resolves only when exactly
        one user matches.

        Args:
            value: Raw form input (Discord ID, username, or display name).

        Returns:
            The resolved User, or None when no unambiguous match exists.
        """
        value = (value or "").strip().lstrip("@")
        if not value:
            return None
        if re.fullmatch(r"\d{17,21}", value):
            user, _ = self.get_or_create(value)
            return user
        matches = self.repo.paginate(page=1, per_page=2, search=value).items
        return matches[0] if len(matches) == 1 else None

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

    def persist_profile(self, user_id: str, profile: dict, reactivate: bool = False) -> None:
        """Persist a freshly fetched Discord profile to the database.

        Writes ``name`` (and ``username`` when present) via a direct column
        update so the change is not silently dropped by the load-time name
        resolution in ``User.init_on_load``.

        Args:
            user_id: Discord user ID.
            profile: Profile dict from ``get_user_profile`` (a successful one,
                i.e. without ``not_found``/``error``).
            reactivate: When True, also clears the inactive flag
                (``not_player_as_of``) — used when an inactive user reappears.
        """
        values: dict = {"name": profile["name"]}
        if profile.get("username"):
            values["username"] = profile["username"]
        if reactivate:
            values["not_player_as_of"] = None
        self.repo.update_fields(user_id, values)
        db.session.commit()

    def update(self, user_id: str, data: dict) -> User:
        """Update an existing user's editable fields.

        Args:
            user_id: Discord user ID.
            data: Dictionary of fields to update (name, username, not_player_as_of).

        Returns:
            Updated User instance.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.get_by_id(user_id)
        user.update_from_dict(data)
        db.session.commit()
        return user

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
