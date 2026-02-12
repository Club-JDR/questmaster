from website.exceptions import NotFoundError, ValidationError
from website.extensions import db
from website.models import SpecialEvent
from website.repositories.special_event import SpecialEventRepository


class SpecialEventService:
    """Service layer for SpecialEvent business logic.

    Handles creation, updates, deletion, and retrieval of special events.
    Manages transaction boundaries and validation.
    """

    def __init__(self, repository=None):
        self.repo = repository or SpecialEventRepository()

    def get_all(self, active_only: bool = False) -> list[SpecialEvent]:
        """Get all special events, optionally filtered by active status.

        Args:
            active_only: If True, only return active events. Defaults to False.

        Returns:
            List of SpecialEvent instances ordered by name.
        """
        return self.repo.get_all(active_only=active_only)

    def get_active(self) -> list[SpecialEvent]:
        """Get all active special events.

        Convenience method for dropdowns and context processors.

        Returns:
            List of active SpecialEvent instances ordered by name.
        """
        return self.repo.get_active()

    def get_by_id(self, id: int) -> SpecialEvent:
        """Get special event by ID.

        Args:
            id: Special event ID.

        Returns:
            SpecialEvent instance.

        Raises:
            NotFoundError: If special event with given ID doesn't exist.
        """
        event = self.repo.get_by_id(id)
        if not event:
            raise NotFoundError(
                f"SpecialEvent with id {id} not found",
                resource_type="SpecialEvent",
                resource_id=id,
            )
        return event

    def create(
        self, name: str, emoji: str = None, color: int = None, active: bool = False
    ) -> SpecialEvent:
        """Create a new special event.

        Args:
            name: Name of the special event (must be unique).
            emoji: Optional emoji for the event.
            color: Optional color as integer (e.g., 0xFF6600).
            active: Whether the event is active. Defaults to False.

        Returns:
            Created SpecialEvent instance.

        Raises:
            ValidationError: If name already exists or validation fails.
        """
        if self.repo.get_by_name(name):
            raise ValidationError("Special event name already exists.", field="name")

        event = SpecialEvent(name=name, emoji=emoji, color=color, active=active)
        self.repo.add(event)
        db.session.commit()
        return event

    def update(self, id: int, data: dict) -> SpecialEvent:
        """Update special event.

        Args:
            id: Special event ID.
            data: Dictionary of fields to update.

        Returns:
            Updated SpecialEvent instance.

        Raises:
            NotFoundError: If special event doesn't exist.
            ValidationError: If name conflicts with existing event.
        """
        event = self.repo.get_by_id_or_404(id)

        # Check for name uniqueness if name is being changed
        if "name" in data and data["name"] != event.name:
            existing = self.repo.get_by_name(data["name"])
            if existing:
                raise ValidationError("Special event name already exists.", field="name")

        event.update_from_dict(data)
        db.session.commit()
        return event

    def delete(self, id: int) -> None:
        """Delete special event.

        Args:
            id: Special event ID.

        Raises:
            NotFoundError: If special event doesn't exist.
        """
        event = self.repo.get_by_id_or_404(id)
        self.repo.delete(event)
        db.session.commit()
