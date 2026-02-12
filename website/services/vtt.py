"""VTT service for virtual tabletop business logic."""

from website.exceptions import NotFoundError, ValidationError
from website.extensions import cache, db
from website.models import Vtt
from website.repositories.vtt import VttRepository


class VttService:
    """Service layer for Vtt (virtual tabletop) operations.

    Handles CRUD operations with cache invalidation.
    """

    def __init__(self, repository=None):
        self.repo = repository or VttRepository()

    def get_all(self) -> list[Vtt]:
        """Get all VTTs ordered by name.

        Returns:
            List of Vtt instances.
        """
        return self.repo.get_all_ordered()

    def get_by_id(self, id: int) -> Vtt:
        """Get VTT by ID.

        Args:
            id: VTT ID.

        Returns:
            Vtt instance.

        Raises:
            NotFoundError: If VTT does not exist.
        """
        vtt = self.repo.get_by_id(id)
        if not vtt:
            raise NotFoundError(
                f"Vtt with id {id} not found",
                resource_type="Vtt",
                resource_id=id,
            )
        return vtt

    def create(self, name: str, icon: str = None) -> Vtt:
        """Create a new VTT.

        Args:
            name: VTT name (must be unique).
            icon: Optional icon path.

        Returns:
            Created Vtt instance.

        Raises:
            ValidationError: If name already exists.
        """
        if self.repo.get_by_name(name):
            raise ValidationError("Vtt name already exists.", field="name")
        vtt = Vtt(name=name, icon=icon)
        self.repo.add(vtt)
        db.session.commit()
        cache.delete_memoized(Vtt.get_vtts)
        return vtt

    def update(self, id: int, data: dict) -> Vtt:
        """Update an existing VTT.

        Args:
            id: VTT ID.
            data: Dictionary of fields to update.

        Returns:
            Updated Vtt instance.
        """
        vtt = self.repo.get_by_id_or_404(id)
        vtt.update_from_dict(data)
        db.session.commit()
        cache.delete_memoized(Vtt.get_vtts)
        return vtt

    def delete(self, id: int) -> None:
        """Delete a VTT.

        Args:
            id: VTT ID.
        """
        vtt = self.repo.get_by_id_or_404(id)
        self.repo.delete(vtt)
        db.session.commit()
        cache.delete_memoized(Vtt.get_vtts)
