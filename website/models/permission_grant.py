"""PermissionGrant model for RBAC capability grants."""

from website.extensions import db
from website.models.base import SerializableMixin


class PermissionGrant(db.Model, SerializableMixin):
    """A single RBAC grant: one capability granted to one subject.

    A subject is either a Discord role (``subject_type == "role"``) or an
    individual user (``subject_type == "user"``); ``subject_id`` is the
    corresponding Discord role or user ID. ``permission_key`` is validated by
    the service layer against the code-defined catalog (it is intentionally not
    a database foreign key).

    Attributes:
        id: Primary key.
        permission_key: Capability key from the code catalog.
        subject_type: ``"role"`` or ``"user"``.
        subject_id: Discord role ID or user ID the capability is granted to.
        granted_by_id: Discord ID of the admin who created the grant (audit only).
        created_at: Creation timestamp.
    """

    __tablename__ = "permission_grant"
    __table_args__ = (
        db.UniqueConstraint(
            "permission_key",
            "subject_type",
            "subject_id",
            name="uq_permission_grant_subject",
        ),
    )

    SUBJECT_ROLE = "role"
    SUBJECT_USER = "user"
    SUBJECT_TYPES = (SUBJECT_ROLE, SUBJECT_USER)

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.Integer, primary_key=True)
    permission_key = db.Column(db.String(), nullable=False, index=True)
    subject_type = db.Column(db.String(), nullable=False)
    subject_id = db.Column(db.String(), nullable=False, index=True)
    granted_by_id = db.Column(db.String(), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    def __repr__(self):
        return f"<PermissionGrant {self.permission_key} " f"{self.subject_type}:{self.subject_id}>"
