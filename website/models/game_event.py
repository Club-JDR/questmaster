"""GameEvent model for the game audit trail."""

from datetime import datetime, timezone

from sqlalchemy import Enum

from config.constants import EVENT_ACTIONS
from website.extensions import db
from website.models.base import SerializableMixin


class GameEvent(db.Model, SerializableMixin):
    """Audit log entry recording an action on a game.

    Attributes:
        id: Primary key.
        timestamp: When the event occurred (UTC).
        action: Event action type (create, edit, delete, etc.).
        game_id: Foreign key to the related game.
        description: Optional human-readable description.
    """

    __tablename__ = "game_event"

    _exclude_fields = []
    _relationship_fields = ["game"]

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    action = db.Column(Enum(*EVENT_ACTIONS, name="action_type_enum"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id", ondelete="CASCADE"), nullable=False)
    description = db.Column(db.Text)
    game = db.relationship("Game", backref="events", cascade="all,delete")

    __table_args__ = (
        db.Index("ix_gameevent_timestamp", "timestamp"),
        db.Index("ix_gameevent_game", "game_id"),
    )

    @classmethod
    def from_dict(cls, data):
        """Create a GameEvent instance from a Python dict."""
        return cls(
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            action=data.get("action"),
            game_id=data.get("game_id"),
            description=data.get("description"),
        )

    def update_from_dict(self, data):
        """Update the GameEvent instance from a dict (in place)."""
        super().update_from_dict(data)
        return self

    def __repr__(self):
        return f"<GameEvent id={self.id} action='{self.action}' game_id={self.game_id}>"

    def __eq__(self, other):
        if not isinstance(other, GameEvent):
            return NotImplemented
        return (
            self.id == other.id
            and self.timestamp == other.timestamp
            and self.action == other.action
            and self.game_id == other.game_id
            and self.description == other.description
        )

    def __ne__(self, other):
        return not self.__eq__(other)
