"""Base repository with generic CRUD operations."""

import math

from sqlalchemy import String, cast, or_

from website.extensions import db


class Pagination[T]:
    """Lightweight, query-agnostic pagination result.

    Mirrors the subset of the Flask-SQLAlchemy ``Pagination`` API consumed by
    the admin templates, but is built from the legacy ``session.query`` API
    used throughout the repository layer.

    Attributes:
        items: Entities on the current page.
        total: Total number of matching entities across all pages.
        page: Current page number (1-based).
        per_page: Number of items per page.
    """

    def __init__(self, items: list[T], total: int, page: int, per_page: int):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page

    @property
    def pages(self) -> int:
        """Total number of pages."""
        if self.per_page == 0 or self.total == 0:
            return 0
        return math.ceil(self.total / self.per_page)

    @property
    def has_prev(self) -> bool:
        """Whether a previous page exists."""
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """Whether a next page exists."""
        return self.page < self.pages

    @property
    def prev_num(self) -> int | None:
        """Number of the previous page, or None."""
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self) -> int | None:
        """Number of the next page, or None."""
        return self.page + 1 if self.has_next else None

    def iter_pages(
        self,
        *,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 4,
        right_edge: int = 2,
    ):
        """Yield page numbers for rendering, using None for elided gaps.

        Args:
            left_edge: Pages to always show at the start.
            left_current: Pages to show before the current page.
            right_current: Pages to show after the current page.
            right_edge: Pages to always show at the end.

        Yields:
            Page numbers, with None marking a skipped range.
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (self.page - left_current - 1 < num < self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


def paginate_query(query, page: int, per_page: int) -> Pagination:
    """Paginate a SQLAlchemy query into a :class:`Pagination` result.

    Args:
        query: A (possibly filtered/ordered) legacy SQLAlchemy query.
        page: Requested page number (clamped to a minimum of 1).
        per_page: Items per page (clamped to a minimum of 1).

    Returns:
        Pagination wrapping the current page of results and the total count.
    """
    page = max(1, page)
    per_page = max(1, per_page)
    total = query.order_by(None).count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return Pagination(items=items, total=total, page=page, per_page=per_page)


class BaseRepository[T]:
    """Base repository providing common CRUD operations.

    Repositories never commit — they only add, flush, and delete.
    The service layer owns the transaction boundary.
    """

    model_class: type[T]

    #: Columns matched (case-insensitively) by :meth:`paginate` searches.
    #: Subclasses override this to opt list views into search.
    search_columns: list = []

    def __init__(self, session=None):
        self.session = session or db.session

    def base_query(self):
        """Return the base query used for listing and pagination.

        Subclasses override this to apply default ordering or joins.

        Returns:
            A SQLAlchemy query over ``model_class``.
        """
        return self.session.query(self.model_class)

    def apply_search(self, query, search: str | None):
        """Apply a case-insensitive search filter over ``search_columns``.

        Args:
            query: The query to filter.
            search: Search term, or None/empty to skip filtering.

        Returns:
            The (possibly) filtered query.
        """
        if not search or not self.search_columns:
            return query
        term = f"%{search}%"
        return query.filter(or_(*[cast(col, String).ilike(term) for col in self.search_columns]))

    def paginate(self, page: int = 1, per_page: int = 25, search: str | None = None) -> Pagination:
        """Return a paginated, optionally searched, list of entities.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            search: Optional search term applied to ``search_columns``.

        Returns:
            Pagination result for the requested page.
        """
        query = self.apply_search(self.base_query(), search)
        return paginate_query(query, page, per_page)

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
