"""Trophy service for achievement and badge business logic."""

import logging

from website.exceptions import NotFoundError
from website.extensions import db
from website.models.trophy import Trophy, UserTrophy
from website.models.user import User
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
        """Get all trophy definitions.

        Returns:
            List of all Trophy instances.
        """
        return self.repo.get_all()

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
