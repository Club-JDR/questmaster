"""AppLog repository for application log data access."""

from datetime import datetime

from sqlalchemy import or_

from website.models import AppLog
from website.repositories.base import BaseRepository, Pagination, paginate_query


class AppLogRepository(BaseRepository[AppLog]):
    """Repository for AppLog entities."""

    model_class = AppLog

    def base_query(self):
        """Return all log records ordered newest-first."""
        return self.session.query(AppLog).order_by(AppLog.timestamp.desc())

    def paginate_filtered(
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
        """Return a paginated, filtered page of log records (newest first).

        Args:
            page: Page number (1-based).
            per_page: Items per page.
            level_no: Minimum numeric level; keeps records at this level and above.
            start: Keep records emitted at or after this UTC timestamp.
            end: Keep records emitted at or before this UTC timestamp.
            logger: Optional logger-name substring (case-insensitive).
            search: Optional term matched (case-insensitively) against
                message, logger name and trace ID.

        Returns:
            Pagination result for the requested page.
        """
        query = self.base_query()
        if level_no is not None:
            query = query.filter(AppLog.level_no >= level_no)
        if start is not None:
            query = query.filter(AppLog.timestamp >= start)
        if end is not None:
            query = query.filter(AppLog.timestamp <= end)
        if logger:
            query = query.filter(AppLog.logger.ilike(f"%{logger}%"))
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    AppLog.message.ilike(term),
                    AppLog.logger.ilike(term),
                    AppLog.trace_id.ilike(term),
                )
            )
        return paginate_query(query, page, per_page)

    def prune(self, before: datetime) -> int:
        """Bulk-delete log records older than the given timestamp.

        Args:
            before: Records with a strictly older timestamp are deleted.

        Returns:
            Number of deleted rows (not committed — the service commits).
        """
        return (
            self.session.query(AppLog)
            .filter(AppLog.timestamp < before)
            .delete(synchronize_session=False)
        )
