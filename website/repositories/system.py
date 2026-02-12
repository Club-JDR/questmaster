"""System repository for game system data access."""

from website.models import System
from website.repositories.base import BaseRepository


class SystemRepository(BaseRepository[System]):
    """Repository for System entities."""

    model_class = System

    def get_all_ordered(self) -> list[System]:
        """Retrieve all systems ordered by name.

        Returns:
            List of System instances sorted alphabetically.
        """
        return self.session.query(System).order_by(System.name).all()

    def get_by_name(self, name: str) -> System | None:
        """Find a system by its name.

        Args:
            name: System name to search for.

        Returns:
            System instance if found, None otherwise.
        """
        return self.session.query(System).filter_by(name=name).first()
