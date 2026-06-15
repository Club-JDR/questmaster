"""AppSetting model for database-backed configuration overrides."""

from datetime import datetime, timezone

from website.extensions import db
from website.models.base import SerializableMixin


class AppSetting(db.Model, SerializableMixin):
    """A single runtime configuration override stored in the database.

    Overrides take precedence over the corresponding environment-backed
    ``app.config`` value. Only keys explicitly allowed by the service layer
    (operational Discord IDs) are ever persisted here; secrets stay in the
    environment.

    Attributes:
        key: Configuration key (matches the ``app.config`` key it overrides).
        value: Override value as a string, or None to fall back to the env value.
        updated_at: Timestamp of the last write.
        updated_by_id: Discord ID of the admin who last set the value (audit only).
    """

    __tablename__ = "app_setting"

    _exclude_fields = []
    _relationship_fields = []

    key = db.Column(db.String(), primary_key=True)
    value = db.Column(db.Text(), nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by_id = db.Column(db.String(), nullable=True)

    @classmethod
    def from_dict(cls, data):
        """Create an AppSetting instance from a Python dict."""
        return cls(
            key=data.get("key"),
            value=data.get("value"),
            updated_by_id=data.get("updated_by_id"),
        )

    def __repr__(self):
        return f"<AppSetting key='{self.key}' value='{self.value}'>"
