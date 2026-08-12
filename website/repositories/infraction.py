"""Infraction repository for moderation-log data access."""

from sqlalchemy import String, cast, or_

from website.models import Infraction, User
from website.repositories.base import BaseRepository


class InfractionRepository(BaseRepository[Infraction]):
    """Data access for moderation infractions (query-only, no commits)."""

    model_class = Infraction

    def base_query(self):
        """Return all infractions ordered newest-first, joined to the user."""
        return (
            self.session.query(Infraction)
            .outerjoin(Infraction.user)
            .order_by(Infraction.created_at.desc())
        )

    def apply_search(self, query, search: str | None):
        """Search across rule article, reason, and the warned user's name/ID.

        Args:
            query: The query to filter.
            search: Search term, or None/empty to skip filtering.

        Returns:
            The (possibly) filtered query.
        """
        if not search:
            return query
        term = f"%{search}%"
        return query.filter(
            or_(
                Infraction.rule_article.ilike(term),
                Infraction.reason.ilike(term),
                User.name.ilike(term),
                cast(Infraction.user_id, String).ilike(term),
            )
        )

    def list_for_user(self, user_id: str) -> list[Infraction]:
        """Return every infraction issued against a user, newest first.

        Args:
            user_id: Discord ID of the warned user.

        Returns:
            List of :class:`Infraction` rows.
        """
        return (
            self.session.query(Infraction)
            .filter(Infraction.user_id == user_id)
            .order_by(Infraction.created_at.desc())
            .all()
        )
