"""PermissionGrant repository for RBAC grant data access."""

from sqlalchemy import and_, or_

from website.models import PermissionGrant
from website.repositories.base import BaseRepository


class PermissionGrantRepository(BaseRepository[PermissionGrant]):
    """Data access for RBAC permission grants (query-only, no commits)."""

    model_class = PermissionGrant

    def list_all(self) -> list[PermissionGrant]:
        """Return every grant, ordered by permission key then subject.

        Returns:
            All :class:`PermissionGrant` rows.
        """
        return (
            self.session.query(PermissionGrant)
            .order_by(
                PermissionGrant.permission_key,
                PermissionGrant.subject_type,
                PermissionGrant.subject_id,
            )
            .all()
        )

    def list_for_subjects(self, role_ids: list[str], user_id: str) -> list[PermissionGrant]:
        """Return grants matching any of the user's role IDs or their own ID.

        Args:
            role_ids: Discord role IDs held by the user.
            user_id: The user's own Discord ID.

        Returns:
            Grants whose subject is the user, or any of the given roles.
        """
        conditions = [
            and_(
                PermissionGrant.subject_type == PermissionGrant.SUBJECT_USER,
                PermissionGrant.subject_id == user_id,
            )
        ]
        if role_ids:
            conditions.append(
                and_(
                    PermissionGrant.subject_type == PermissionGrant.SUBJECT_ROLE,
                    PermissionGrant.subject_id.in_(role_ids),
                )
            )
        return self.session.query(PermissionGrant).filter(or_(*conditions)).all()

    def get(self, key: str, subject_type: str, subject_id: str) -> PermissionGrant | None:
        """Return a specific grant if present (for idempotent grant/revoke).

        Args:
            key: Permission key.
            subject_type: ``"role"`` or ``"user"``.
            subject_id: Discord role or user ID.

        Returns:
            The matching grant, or None.
        """
        return (
            self.session.query(PermissionGrant)
            .filter_by(permission_key=key, subject_type=subject_type, subject_id=subject_id)
            .one_or_none()
        )

    def add(
        self,
        key: str,
        subject_type: str,
        subject_id: str,
        granted_by_id: str | None = None,
    ) -> PermissionGrant:
        """Insert a grant (flush only — the service owns the commit).

        Args:
            key: Permission key.
            subject_type: ``"role"`` or ``"user"``.
            subject_id: Discord role or user ID.
            granted_by_id: Discord ID of the admin creating the grant.

        Returns:
            The persisted (flushed) grant.
        """
        grant = PermissionGrant(
            permission_key=key,
            subject_type=subject_type,
            subject_id=subject_id,
            granted_by_id=granted_by_id,
        )
        self.session.add(grant)
        self.session.flush()
        return grant

    def delete_by_id(self, grant_id: int) -> None:
        """Delete a grant by id (flush only — the service owns the commit).

        Args:
            grant_id: Primary key of the grant to remove.
        """
        grant = self.session.get(PermissionGrant, grant_id)
        if grant is not None:
            self.session.delete(grant)
            self.session.flush()
