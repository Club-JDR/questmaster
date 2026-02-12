"""SpecialEvent repository for themed event data access."""

from website.models import SpecialEvent
from website.repositories.base import BaseRepository


class SpecialEventRepository(BaseRepository[SpecialEvent]):
    """Repository for SpecialEvent data access.

    Handles querying special events with optional filtering by active status.
    """

    model_class = SpecialEvent

    def get_all(self, active_only: bool = False) -> list[SpecialEvent]:
        """Get all special events, optionally filtered by active status.

        Args:
            active_only: If True, only return active events. Defaults to False.

        Returns:
            List of SpecialEvent instances ordered by name.
        """
        query = self.session.query(SpecialEvent).order_by(SpecialEvent.name)
        if active_only:
            query = query.filter_by(active=True)
        return query.all()

    def get_active(self) -> list[SpecialEvent]:
        """Get all active special events.

        Convenience method for getting active events only.

        Returns:
            List of active SpecialEvent instances ordered by name.
        """
        return self.get_all(active_only=True)

    def get_by_name(self, name: str) -> SpecialEvent | None:
        """Get special event by name.

        Args:
            name: Name of the special event.

        Returns:
            SpecialEvent instance if found, None otherwise.
        """
        return self.session.query(SpecialEvent).filter_by(name=name).first()
