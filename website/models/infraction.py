"""Infraction model for the in-app moderation log."""

from datetime import datetime, timezone

from config.constants import INFRACTION_SEVERITY_LABELS, INFRACTION_SEVERITY_REMINDER
from website.extensions import db
from website.models.base import SerializableMixin


class Infraction(db.Model, SerializableMixin):
    """A moderation infraction (warning) issued against a user.

    Preserves the historical Mee6 warning format:
    ``[Article du règlement] - [Raison] [Lien vers le post] - [Détail] -
    [Date] - [Admin]``.

    Attributes:
        id: Primary key.
        user_id: Discord ID of the warned user (FK to ``user``).
        rule_article: The rule/article violated.
        severity: Integer severity (lower = reminder, higher = warning).
        message_link: Optional link to the Discord moderation post.
        reason: Free-text detail describing the infraction.
        admin_id: Discord ID of the admin who issued it (FK to ``user``).
        created_at: When the infraction was issued (admin-editable to backfill).
        user: The warned user.
        admin: The admin who issued the infraction.
    """

    __tablename__ = "infraction"

    _exclude_fields = []
    _relationship_fields = ["user", "admin"]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_article = db.Column(db.String(), nullable=True)
    severity = db.Column(
        db.Integer, nullable=False, default=INFRACTION_SEVERITY_REMINDER, server_default="1"
    )
    message_link = db.Column(db.String(), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    admin_id = db.Column(db.String(), db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", foreign_keys=[user_id])
    admin = db.relationship("User", foreign_keys=[admin_id])

    __table_args__ = (db.Index("ix_infraction_created_at", "created_at"),)

    @property
    def severity_label(self) -> str:
        """Return the French label for this infraction's severity."""
        return INFRACTION_SEVERITY_LABELS.get(self.severity, str(self.severity))

    def __repr__(self):
        return f"<Infraction id={self.id} user_id={self.user_id} severity={self.severity}>"
