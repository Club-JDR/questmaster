"""Base repository with generic CRUD operations."""

from typing import Generic, TypeVar

from website.extensions import db

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository providing common CRUD operations.

    Repositories never commit — they only add, flush, and delete.
    The service layer owns the transaction boundary.
    """

    model_class: type[T]

    def __init__(self, session=None):
        self.session = session or db.session

    def get_by_id(self, id: int) -> T | None:
        """Retrieve an entity by its primary key.

        Args:
            id: Primary key value.

        Returns:
            Entity instance, or None if not found.
        """
        return self.session.get(self.model_class, id)

    def get_by_id_or_404(self, id: int) -> T:
        """Retrieve an entity by ID or abort with 404.

        Args:
            id: Primary key value.

        Returns:
            Entity instance.

        Raises:
            NotFound: If entity does not exist.
        """
        return db.get_or_404(self.model_class, id)

    def get_all(self) -> list[T]:
        """Retrieve all entities of this type.

        Returns:
            List of all entity instances.
        """
        return self.session.query(self.model_class).all()

    def add(self, entity: T) -> T:
        """Add an entity to the session and flush.

        Args:
            entity: Entity instance to persist.

        Returns:
            The persisted entity.
        """
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        """Delete an entity from the session and flush.

        Args:
            entity: Entity instance to remove.
        """
        self.session.delete(entity)
        self.session.flush()

    def count(self) -> int:
        """Return the total count of entities.

        Returns:
            Integer count.
        """
        return self.session.query(self.model_class).count()
