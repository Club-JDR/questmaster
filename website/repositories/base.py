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

    def get_by_id(self, id) -> T | None:
        return self.session.get(self.model_class, id)

    def get_by_id_or_404(self, id) -> T:
        return db.get_or_404(self.model_class, id)

    def get_all(self) -> list[T]:
        return self.session.query(self.model_class).all()

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()

    def count(self) -> int:
        return self.session.query(self.model_class).count()
