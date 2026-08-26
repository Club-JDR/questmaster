"""UserSystemInterest repository for data access."""

from sqlalchemy.orm import joinedload

from config.constants import USER_PLACEHOLDER_NAME
from website.models import User, UserSystemInterest
from website.repositories.base import BaseRepository


class UserSystemInterestRepository(BaseRepository[UserSystemInterest]):
    """Repository for UserSystemInterest entities."""

    model_class = UserSystemInterest

    def get(self, user_id: str, system_id: int, role: str) -> UserSystemInterest | None:
        """Get a single declared interest by its composite key.

        Args:
            user_id: User ID.
            system_id: System ID.
            role: "player" or "gm".

        Returns:
            The UserSystemInterest instance, or None if not declared.
        """
        return self.session.get(UserSystemInterest, (user_id, system_id, role))

    def list_by_system_and_role(self, system_id: int, role: str) -> list[UserSystemInterest]:
        """List declared interests for a system, filtered by role.

        Placeholder users (unresolved Discord profiles) are excluded since
        they aren't a real person to recommend as a contact.

        Args:
            system_id: System ID.
            role: "player" or "gm".

        Returns:
            List of UserSystemInterest instances, with ``user`` eager-loaded,
            ordered by the interested user's name.
        """
        return (
            self.session.query(UserSystemInterest)
            .join(User, UserSystemInterest.user_id == User.id)
            .options(joinedload(UserSystemInterest.user))
            .filter(
                UserSystemInterest.system_id == system_id,
                UserSystemInterest.role == role,
                User.name != USER_PLACEHOLDER_NAME,
            )
            .order_by(User.name)
            .all()
        )
