"""Tests for the PermissionService (RBAC grants + resolution)."""

import pytest

from website.exceptions import ValidationError
from website.extensions import cache
from website.models import PermissionGrant
from website.permissions import PERMISSION_KEYS
from website.services.permission import PermissionService


@pytest.fixture(autouse=True)
def clean_grants(db_session):
    """Empty the permission_grant table and cache around each test."""
    cache.clear()
    db_session.query(PermissionGrant).delete()
    db_session.commit()
    yield
    db_session.query(PermissionGrant).delete()
    db_session.commit()
    cache.clear()


class TestResolveFor:
    def test_admin_gets_full_catalog(self, db_session):
        """An admin resolves the entire catalog regardless of grants."""
        service = PermissionService()
        assert service.resolve_for("u-admin", [], is_admin=True) == set(PERMISSION_KEYS)

    def test_role_grant_resolves(self, db_session):
        """A capability granted to a role the user holds is resolved."""
        service = PermissionService()
        service.grant("vtt.manage", PermissionGrant.SUBJECT_ROLE, "role-1")
        resolved = service.resolve_for("u-1", ["role-1"], is_admin=False)
        assert resolved == {"vtt.manage"}

    def test_user_grant_resolves_without_role(self, db_session):
        """A direct user grant resolves even with no matching role."""
        service = PermissionService()
        service.grant("system.manage", PermissionGrant.SUBJECT_USER, "u-2")
        resolved = service.resolve_for("u-2", [], is_admin=False)
        assert resolved == {"system.manage"}

    def test_combined_role_and_user_grants_deduplicated(self, db_session):
        """Role and user grants are unioned without duplicates."""
        service = PermissionService()
        service.grant("vtt.manage", PermissionGrant.SUBJECT_ROLE, "role-1")
        service.grant("vtt.manage", PermissionGrant.SUBJECT_USER, "u-3")
        service.grant("system.manage", PermissionGrant.SUBJECT_USER, "u-3")
        resolved = service.resolve_for("u-3", ["role-1"], is_admin=False)
        assert resolved == {"vtt.manage", "system.manage"}

    def test_orphaned_key_filtered_out(self, db_session):
        """A stored grant whose key left the catalog is ignored on resolve."""
        db_session.add(
            PermissionGrant(
                permission_key="removed.capability",
                subject_type=PermissionGrant.SUBJECT_USER,
                subject_id="u-4",
            )
        )
        db_session.commit()
        resolved = PermissionService().resolve_for("u-4", [], is_admin=False)
        assert resolved == set()


class TestGrant:
    def test_rejects_unknown_key(self, db_session):
        with pytest.raises(ValidationError):
            PermissionService().grant("nope.key", PermissionGrant.SUBJECT_ROLE, "r-1")

    def test_rejects_bad_subject_type(self, db_session):
        with pytest.raises(ValidationError):
            PermissionService().grant("vtt.manage", "group", "r-1")

    def test_rejects_empty_subject_id(self, db_session):
        with pytest.raises(ValidationError):
            PermissionService().grant("vtt.manage", PermissionGrant.SUBJECT_ROLE, "   ")

    def test_grant_is_idempotent(self, db_session):
        """Granting twice creates a single row and raises no error."""
        service = PermissionService()
        service.grant("vtt.manage", PermissionGrant.SUBJECT_ROLE, "role-9")
        service.grant("vtt.manage", PermissionGrant.SUBJECT_ROLE, "role-9")
        rows = (
            db_session.query(PermissionGrant)
            .filter_by(permission_key="vtt.manage", subject_id="role-9")
            .all()
        )
        assert len(rows) == 1


class TestRevoke:
    def test_revoke_removes_grant(self, db_session):
        """Revoking a grant removes it and updates resolution."""
        service = PermissionService()
        service.grant("vtt.manage", PermissionGrant.SUBJECT_USER, "u-5")
        grant = (
            db_session.query(PermissionGrant)
            .filter_by(subject_id="u-5", permission_key="vtt.manage")
            .one()
        )
        service.revoke(grant.id)
        assert db_session.get(PermissionGrant, grant.id) is None
        assert service.resolve_for("u-5", [], is_admin=False) == set()
