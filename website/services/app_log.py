"""AppLog service for browsing and pruning application logs."""

from datetime import datetime, timedelta, timezone

from website.extensions import db
from website.repositories.app_log import AppLogRepository
from website.repositories.base import Pagination

DEFAULT_RETENTION_DAYS = 30


class AppLogService:
    """Service layer for the application log records.

    Records are *written* by ``DatabaseLogHandler`` outside any service; this
    service only reads (admin page) and prunes (scheduled retention job).
    """

    def __init__(self, repository=None):
        self.repo = repository or AppLogRepository()

    def list_paginated(
        self,
        page: int = 1,
        per_page: int = 25,
        *,
        level_no: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        logger: str | None = None,
        search: str | None = None,
    ) -> Pagination:
        """Get a paginated, filtered page of application log records.

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            level_no: Minimum numeric level; keeps records at this level and above.
            start: Keep records emitted at or after this UTC timestamp.
            end: Keep records emitted at or before this UTC timestamp.
            logger: Optional logger-name substring (case-insensitive).
            search: Optional term matched against message, logger and trace ID.

        Returns:
            Pagination result of AppLog instances (newest first).
        """
        return self.repo.paginate_filtered(
            page=page,
            per_page=per_page,
            level_no=level_no,
            start=start,
            end=end,
            logger=logger,
            search=search,
        )

    def prune(self, retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
        """Delete log records older than the retention window and commit.

        Args:
            retention_days: Records older than this many days are deleted.

        Returns:
            Number of deleted rows.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted = self.repo.prune(cutoff)
        db.session.commit()
        return deleted
