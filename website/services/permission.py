"""Permission service: manage RBAC grants and resolve effective permissions.

Capabilities are a fixed catalog defined in code (:mod:`website.permissions`);
grants (who holds what) live in the database. This service owns grant
validation, the transaction boundary, and the resolution of a user's effective
permission set (cached, mirroring ``get_user_roles``).
"""

from __future__ import annotations

from website.extensions import cache, db
from website.models import PermissionGrant
from website.permissions import PERMISSION_KEYS, PERMISSIONS, Permission
from website.repositories.permission_grant import PermissionGrantRepository
from website.utils.logger import logger

# Cache timeout for a user's resolved permission set (mirrors get_user_roles).
PERMISSIONS_CACHE_TIMEOUT = 300  # 5 minutes


def _user_cache_key(user_id: str) -> str:
    """Return the cache key for a user's resolved permission set."""
    return f"user_perms_{user_id}"


class PermissionService:
    """Manage RBAC grants and resolve effective permissions for users."""

    def __init__(self, repository: PermissionGrantRepository | None = None):
        self.repo = repository or PermissionGrantRepository()

    def catalog(self) -> list[Permission]:
        """Return the code-defined permission catalog (for the admin UI).

        Returns:
            The list of :class:`Permission` entries.
        """
        return list(PERMISSIONS)

    def list_grants(self) -> list[PermissionGrant]:
        """Return all grants for the admin UI, ignoring unknown keys.

        Returns:
            Every stored grant whose key is still part of the catalog.
        """
        return [g for g in self.repo.list_all() if g.permission_key in PERMISSION_KEYS]

    def grants_by_key(self) -> dict[str, list[PermissionGrant]]:
        """Group current grants by permission key (for the admin UI).

        Returns:
            Mapping of each catalog key to its list of grants (possibly empty).
        """
        grouped: dict[str, list[PermissionGrant]] = {p.key: [] for p in PERMISSIONS}
        for grant in self.list_grants():
            grouped[grant.permission_key].append(grant)
        return grouped

    def grant(
        self,
        key: str,
        subject_type: str,
        subject_id: str,
        granted_by_id: str | None = None,
    ) -> None:
        """Grant a capability to a Discord role or an individual user.

        Idempotent: granting an existing (key, subject) pair is a no-op.

        Args:
            key: Permission key from the catalog.
            subject_type: ``"role"`` or ``"user"``.
            subject_id: Discord role or user ID.
            granted_by_id: Discord ID of the admin performing the change.

        Raises:
            ValidationError: If the key is unknown, the subject type is invalid,
                or the subject id is empty.
        """
        from website.exceptions import ValidationError

        if key not in PERMISSION_KEYS:
            raise ValidationError("Unknown permission.", field="permission_key")
        if subject_type not in PermissionGrant.SUBJECT_TYPES:
            raise ValidationError("Invalid subject type.", field="subject_type")
        subject_id = (subject_id or "").strip()
        if not subject_id:
            raise ValidationError("Subject id is required.", field="subject_id")

        if self.repo.get(key, subject_type, subject_id) is not None:
            return  # already granted — idempotent

        self.repo.add(key, subject_type, subject_id, granted_by_id)
        db.session.commit()
        self._invalidate(subject_type, subject_id)

    def revoke(self, grant_id: int) -> None:
        """Remove a grant.

        Args:
            grant_id: Primary key of the grant to remove.
        """
        grant = self.repo.get_by_id(grant_id)
        self.repo.delete_by_id(grant_id)
        db.session.commit()
        if grant is not None:
            self._invalidate(grant.subject_type, grant.subject_id)

    def resolve_for(self, user_id: str, role_ids: list[str], is_admin: bool) -> set[str]:
        """Return the effective permission set for a user.

        Admins implicitly hold the full catalog. Otherwise the union of grants
        matching the user's Discord role IDs and their own user ID, filtered to
        known keys. The non-admin result is cached per user for 5 minutes.

        Args:
            user_id: Discord user ID.
            role_ids: Discord role IDs held by the user.
            is_admin: Whether the user is a superuser admin.

        Returns:
            The set of capability keys the user effectively holds.
        """
        if is_admin:
            return set(PERMISSION_KEYS)

        cache_key = _user_cache_key(user_id)
        try:
            cached = cache.get(cache_key)
        except Exception:  # noqa: BLE001 - cache backend best-effort
            cached = None
        if cached is not None:
            return set(cached)

        grants = self.repo.list_for_subjects(role_ids, user_id)
        resolved = {g.permission_key for g in grants if g.permission_key in PERMISSION_KEYS}

        try:
            cache.set(cache_key, list(resolved), timeout=PERMISSIONS_CACHE_TIMEOUT)
        except Exception:  # noqa: BLE001 - cache backend best-effort
            pass
        return resolved

    def _invalidate(self, subject_type: str, subject_id: str) -> None:
        """Best-effort cache invalidation after a grant/revoke.

        A user-subject change invalidates exactly that user. A role-subject
        change cannot be mapped back to its members cheaply, so it relies on the
        5-minute TTL (same propagation lag as Discord role changes today).

        Args:
            subject_type: ``"role"`` or ``"user"``.
            subject_id: Discord role or user ID affected.
        """
        if subject_type != PermissionGrant.SUBJECT_USER:
            return
        try:
            cache.delete(_user_cache_key(subject_id))
        except Exception as exc:  # noqa: BLE001 - best-effort cache invalidation
            logger.warning("Failed to invalidate permissions for %s: %s", subject_id, exc)
