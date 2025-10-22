from website.extensions import db
from sqlalchemy.dialects.postgresql import ENUM
from website.models.game import GAME_TYPES


class Channel(db.Model):
    __tablename__ = "channel"

    id = db.Column(db.String(), primary_key=True)
    type = db.Column(
        ENUM(*GAME_TYPES, name="game_type_enum", create_type=False), nullable=False
    )
    size = db.Column(db.Integer(), nullable=False, default=0)

    def to_dict(self):
        """Serialize the channel instance to a Python dict."""
        return {
            "id": self.id,
            "type": self.type,
            "size": self.size,
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
        """Create a Channel instance from a Python dict."""
        return cls(
            id=data.get("id"),
            type=data.get("type"),
            size=data.get("size", 0),
        )

    @classmethod
    def from_json(cls, data):
        """Alias for from_dict() for API compatibility."""
        return cls.from_dict(data)

    def update_from_dict(self, data):
        """Update the Channel instance from a dict (in place)."""
        for field in ["type", "size"]:
            if field in data:
                setattr(self, field, data[field])
        return self

    def __repr__(self):
        return f"<Channel id='{self.id}' type='{self.type}' size={self.size}>"

    def __eq__(self, other):
        if not isinstance(other, Channel):
            return NotImplemented
        return (
            self.id == other.id and self.type == other.type and self.size == other.size
        )

    def __ne__(self, other):
        return not self.__eq__(other)
