"""Trophy service for achievement and badge business logic."""

import logging

from website.exceptions import NotFoundError, ValidationError
from website.extensions import db
from website.models.trophy import Trophy, UserTrophy
from website.models.user import User
from website.repositories.base import Pagination
from website.repositories.trophy import TrophyRepository

logger = logging.getLogger(__name__)


class TrophyService:
    """Service layer for Trophy business logic.

    Handles awarding trophies, leaderboards, and user badge retrieval.
    Manages transaction boundaries and trophy-specific business rules.
    """

    def __init__(self, repository=None):
        self.repo = repository or TrophyRepository()

    def get_by_id(self, trophy_id: int) -> Trophy:
        """Get trophy by ID.

        Args:
            trophy_id: Trophy ID.

        Returns:
            Trophy instance.

        Raises:
            NotFoundError: If trophy with given ID doesn't exist.
        """
        trophy = self.repo.get_by_id(trophy_id)
        if not trophy:
            raise NotFoundError(
                f"Trophy with id {trophy_id} not found",
                resource_type="Trophy",
                resource_id=trophy_id,
            )
        return trophy

    def get_all(self) -> list[Trophy]:
        """Get all trophy definitions ordered by name.

        Returns:
            List of all Trophy instances.
        """
        return self.repo.get_all_ordered()

    def list_paginated(
        self, page: int = 1, per_page: int = 25, search: str | None = None
    ) -> Pagination:
        """Get a paginated, optionally searched, list of trophy definitions.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against the trophy name.

        Returns:
            Pagination result of Trophy instances.
        """
        return self.repo.paginate(page=page, per_page=per_page, search=search)

    def list_user_trophies_paginated(
        self, page: int = 1, per_page: int = 25, search: str | None = None
    ) -> Pagination:
        """Get a paginated, optionally searched, list of user/trophy rows.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional term matched against user ID, user name, or
                trophy name.

        Returns:
            Pagination result of UserTrophy instances.
        """
        return self.repo.paginate_user_trophies(page=page, per_page=per_page, search=search)

    def create_trophy(self, name: str, unique: bool = False, icon: str | None = None) -> Trophy:
        """Create a new trophy definition.

        Args:
            name: Trophy name (must be unique).
            unique: Whether the trophy can only be earned once. Defaults to False.
            icon: Optional path or URL to the trophy icon.

        Returns:
            Created Trophy instance.

        Raises:
            ValidationError: If a trophy with this name already exists.
        """
        if self.repo.get_by_name(name):
            raise ValidationError("Trophy name already exists.", field="name")
        trophy = Trophy(name=name, unique=unique, icon=icon)
        self.repo.add(trophy)
        db.session.commit()
        return trophy

    def update_trophy(self, trophy_id: int, data: dict) -> Trophy:
        """Update a trophy definition.

        Args:
            trophy_id: Trophy ID.
            data: Dictionary of fields to update.

        Returns:
            Updated Trophy instance.

        Raises:
            ValidationError: If the new name conflicts with another trophy.
        """
        trophy = self.repo.get_by_id_or_404(trophy_id)
        if "name" in data and data["name"] != trophy.name:
            existing = self.repo.get_by_name(data["name"])
            if existing:
                raise ValidationError("Trophy name already exists.", field="name")
        trophy.update_from_dict(data)
        db.session.commit()
        return trophy

    def delete_trophy(self, trophy_id: int) -> None:
        """Delete a trophy definition.

        Args:
            trophy_id: Trophy ID.
        """
        trophy = self.repo.get_by_id_or_404(trophy_id)
        self.repo.delete(trophy)
        db.session.commit()

    def get_all_user_trophies(self) -> list[UserTrophy]:
        """Get all user/trophy associations.

        Returns:
            List of UserTrophy instances ordered by trophy name.
        """
        return self.repo.get_all_user_trophies()

    def get_user_trophy(self, user_id: str, trophy_id: int) -> UserTrophy:
        """Get a single user/trophy association.

        Args:
            user_id: User ID.
            trophy_id: Trophy ID.

        Returns:
            UserTrophy instance.

        Raises:
            NotFoundError: If the association does not exist.
        """
        user_trophy = self.repo.get_user_trophy(user_id, trophy_id)
        if user_trophy is None:
            raise NotFoundError(
                f"UserTrophy for user {user_id} and trophy {trophy_id} not found",
                resource_type="UserTrophy",
            )
        return user_trophy

    def create_user_trophy(self, user_id: str, trophy_id: int, quantity: int = 1) -> UserTrophy:
        """Create a user/trophy association.

        Enforces trophy uniqueness: unique trophies can only be awarded once and
        their quantity is forced to 1.

        Args:
            user_id: User ID.
            trophy_id: Trophy ID.
            quantity: Quantity to award. Defaults to 1.

        Returns:
            Created UserTrophy instance.

        Raises:
            ValidationError: If the user already owns this trophy.
        """
        trophy = self.get_by_id(trophy_id)
        if self.repo.get_user_trophy(user_id, trophy_id) is not None:
            raise ValidationError(
                "User already owns this trophy.",
                field="trophy_id",
            )
        if trophy.unique:
            quantity = 1
        user_trophy = UserTrophy(user_id=user_id, trophy_id=trophy_id, quantity=quantity)
        self.repo.add_user_trophy(user_trophy)
        db.session.commit()
        return user_trophy

    def update_user_trophy(self, user_id: str, trophy_id: int, quantity: int) -> UserTrophy:
        """Update the quantity of a user/trophy association.

        Args:
            user_id: User ID.
            trophy_id: Trophy ID.
            quantity: New quantity (forced to 1 for unique trophies).

        Returns:
            Updated UserTrophy instance.

        Raises:
            NotFoundError: If the association does not exist.
        """
        user_trophy = self.get_user_trophy(user_id, trophy_id)
        if user_trophy.trophy.unique:
            quantity = 1
        user_trophy.quantity = max(1, quantity)
        db.session.commit()
        return user_trophy

    def delete_user_trophy(self, user_id: str, trophy_id: int) -> None:
        """Delete a user/trophy association.

        Args:
            user_id: User ID.
            trophy_id: Trophy ID.

        Raises:
            NotFoundError: If the association does not exist.
        """
        user_trophy = self.get_user_trophy(user_id, trophy_id)
        self.repo.delete_user_trophy(user_trophy)
        db.session.commit()

    def decrement_user_trophy(
        self, user_id: str, trophy_id: int, amount: int = 1
    ) -> UserTrophy | None:
        """Decrement a user/trophy quantity, removing the record if it hits zero.

        Quantity never drops below 1: decrementing a record whose quantity would
        reach 0 deletes the association instead.

        Args:
            user_id: User ID.
            trophy_id: Trophy ID.
            amount: Amount to subtract. Defaults to 1.

        Returns:
            The updated UserTrophy instance, or None if the record was removed.

        Raises:
            NotFoundError: If the association does not exist.
        """
        user_trophy = self.get_user_trophy(user_id, trophy_id)
        if user_trophy.quantity - amount <= 0:
            self.repo.delete_user_trophy(user_trophy)
            db.session.commit()
            return None
        user_trophy.quantity -= amount
        db.session.commit()
        return user_trophy

    def award(self, user_id: str, trophy_id: int, amount: int = 1) -> UserTrophy:
        """Award a trophy to a user.

        Handles both unique and non-unique trophies according to business rules:
        - Unique trophies: Only awarded once (quantity = 1), additional awards are ignored
        - Non-unique trophies: Quantity is incremented by amount

        Args:
            user_id: User ID to award trophy to.
            trophy_id: Trophy ID to award.
            amount: Quantity to award (only applies to non-unique trophies). Defaults to 1.

        Returns:
            UserTrophy instance (created or updated).

        Raises:
            NotFoundError: If trophy doesn't exist.
        """
        trophy = self.get_by_id(trophy_id)
        user_trophy = self.repo.get_user_trophy(user_id, trophy_id)

        if trophy.unique:
            # Unique trophies: only award once
            if user_trophy is None:
                user_trophy = self.repo.award_trophy(user_id, trophy_id, amount=1)
                logger.info(f"User {user_id} got a trophy: {trophy.name}")
            else:
                logger.debug(f"User {user_id} already has unique trophy {trophy.name}, skipping")
        else:
            # Non-unique trophies: increment quantity
            user_trophy = self.repo.award_trophy(user_id, trophy_id, amount)
            logger.info(f"User {user_id} got a trophy: {trophy.name} (x{amount})")

        db.session.commit()
        return user_trophy

    def get_leaderboard(self, trophy_id: int, limit: int = 10) -> list[tuple[User, int]]:
        """Get leaderboard for a specific trophy.

        Args:
            trophy_id: Trophy ID to get leaderboard for.
            limit: Maximum number of entries to return. Defaults to 10.

        Returns:
            List of (User, total_quantity) tuples ordered by quantity descending.

        Raises:
            NotFoundError: If trophy doesn't exist.
        """
        # Verify trophy exists
        self.get_by_id(trophy_id)
        return self.repo.get_leaderboard(trophy_id, limit)

    def get_user_badges(self, user_id: str) -> list[dict]:
        """Get all trophies/badges for a user.

        Args:
            user_id: User ID.

        Returns:
            List of dicts with keys: name, icon, quantity.
        """
        user_trophies = (
            self.repo.session.query(UserTrophy).filter_by(user_id=user_id).join(Trophy).all()
        )

        return [
            {
                "name": ut.trophy.name,
                "icon": ut.trophy.icon,
                "quantity": ut.quantity,
            }
            for ut in user_trophies
        ]
