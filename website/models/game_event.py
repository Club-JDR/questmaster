from datetime import datetime, timezone
from website.extensions import db
from sqlalchemy import Enum


EVENT_ACTIONS = (
    "create",
    "edit",
    "delete",
    "create-session",
    "edit-session",
    "delete-session",
    "register",
    "unregister",
    "alert",
)


class GameEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    action = db.Column(Enum(*EVENT_ACTIONS, name="action_type_enum"), nullable=False)
    game_id = db.Column(
        db.Integer, db.ForeignKey("game.id", ondelete="CASCADE"), nullable=False
    )
    description = db.Column(db.Text)
    game = db.relationship("Game", backref="events", cascade="all,delete")

    __table_args__ = (
        db.Index("ix_gameevent_timestamp", "timestamp"),
        db.Index("ix_gameevent_game", "game_id"),
    )

    def to_dict(self):
        """Serialize the GameEvent instance to a Python dict."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "game_id": self.game_id,
            "description": self.description,
        }

    def to_json(self):
        """Alias for to_dict() for API compatibility."""
        return self.to_dict()

    @property
    def json(self):
        """Property alias for JSON serialization."""
        return self.to_dict()

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

    @classmethod
    def from_json(cls, data):
        """Alias for from_dict() for API compatibility."""
        return cls.from_dict(data)

    def update_from_dict(self, data):
        """Update the GameEvent instance from a dict (in place)."""
        for field in ["timestamp", "action", "game_id", "description"]:
            if field in data:
                setattr(self, field, data[field])
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
