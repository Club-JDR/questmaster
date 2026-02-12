"""VTT repository for virtual tabletop data access."""

from website.models import Vtt
from website.repositories.base import BaseRepository


class VttRepository(BaseRepository[Vtt]):
    """Repository for Vtt entities."""

    model_class = Vtt

    def get_all_ordered(self) -> list[Vtt]:
        """Retrieve all VTTs ordered by name.

        Returns:
            List of Vtt instances sorted alphabetically.
        """
        return self.session.query(Vtt).order_by(Vtt.name).all()

    def get_by_name(self, name: str) -> Vtt | None:
        """Find a VTT by its name.

        Args:
            name: VTT name to search for.

        Returns:
            Vtt instance if found, None otherwise.
        """
        return self.session.query(Vtt).filter_by(name=name).first()
