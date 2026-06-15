"""Trophy repository for badge and achievement data access."""

from sqlalchemy import func

from website.models.trophy import Trophy, UserTrophy
from website.models.user import User
from website.repositories.base import BaseRepository


class TrophyRepository(BaseRepository[Trophy]):
    """Repository for Trophy data access.

    Handles querying trophies, user trophies, and leaderboard aggregations.
    """

    model_class = Trophy

    def get_all_ordered(self) -> list[Trophy]:
        """Retrieve all trophy definitions ordered by name.

        Returns:
            List of Trophy instances sorted alphabetically.
        """
        return self.session.query(Trophy).order_by(Trophy.name).all()

    def get_by_name(self, name: str) -> Trophy | None:
        """Find a trophy definition by its name.

        Args:
            name: Trophy name to search for.

        Returns:
            Trophy instance if found, None otherwise.
        """
        return self.session.query(Trophy).filter_by(name=name).first()

    def get_all_user_trophies(self) -> list[UserTrophy]:
        """Retrieve all user/trophy associations.

        Returns:
            List of UserTrophy instances.
        """
        return self.session.query(UserTrophy).join(Trophy).order_by(Trophy.name).all()

    def add_user_trophy(self, user_trophy: UserTrophy) -> UserTrophy:
        """Persist a new user/trophy association.

        Args:
            user_trophy: UserTrophy instance to add.

        Returns:
            The persisted UserTrophy instance.
        """
        self.session.add(user_trophy)
        self.session.flush()
        return user_trophy

    def delete_user_trophy(self, user_trophy: UserTrophy) -> None:
        """Delete a user/trophy association.

        Args:
            user_trophy: UserTrophy instance to remove.
        """
        self.session.delete(user_trophy)
        self.session.flush()

    def get_user_trophy(self, user_id: str, trophy_id: int) -> UserTrophy | None:
        """Get a user's trophy record.

        Args:
            user_id: User ID.
            trophy_id: Trophy ID.

        Returns:
            UserTrophy instance if user has this trophy, None otherwise.
        """
        return (
            self.session.query(UserTrophy).filter_by(user_id=user_id, trophy_id=trophy_id).first()
        )

    def award_trophy(self, user_id: str, trophy_id: int, amount: int = 1) -> UserTrophy:
        """Create or update a user trophy record.

        Args:
            user_id: User ID.
            trophy_id: Trophy ID.
            amount: Quantity to add. Defaults to 1.

        Returns:
            Created or updated UserTrophy instance.
        """
        user_trophy = self.get_user_trophy(user_id, trophy_id)

        if user_trophy:
            user_trophy.quantity += amount
        else:
            user_trophy = UserTrophy(user_id=user_id, trophy_id=trophy_id, quantity=amount)
            self.session.add(user_trophy)

        self.session.flush()
        return user_trophy

    def get_leaderboard(self, trophy_id: int, limit: int = 10) -> list[tuple[User, int]]:
        """Get leaderboard for a specific trophy.

        Args:
            trophy_id: Trophy ID to get leaderboard for.
            limit: Maximum number of entries to return. Defaults to 10.

        Returns:
            List of (User, total_quantity) tuples ordered by quantity descending.
        """
        return (
            self.session.query(User, func.sum(UserTrophy.quantity).label("total"))
            .join(UserTrophy)
            .filter(UserTrophy.trophy_id == trophy_id)
            .group_by(User.id)
            .order_by(func.sum(UserTrophy.quantity).desc())
            .limit(limit)
            .all()
        )
