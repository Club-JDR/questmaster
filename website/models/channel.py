from website.extensions import db
from website.models.base import SerializableMixin
from sqlalchemy.dialects.postgresql import ENUM
from config.constants import GAME_TYPES


class Channel(db.Model, SerializableMixin):
    __tablename__ = "channel"

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.String(), primary_key=True)
    type = db.Column(
        ENUM(*GAME_TYPES, name="game_type_enum", create_type=False), nullable=False
    )
    size = db.Column(db.Integer(), nullable=False, default=0)

    @classmethod
    def from_dict(cls, data):
        """Create a Channel instance from a Python dict."""
        return cls(
            id=data.get("id"),
            type=data.get("type"),
            size=data.get("size", 0),
        )

    def update_from_dict(self, data):
        """Update the Channel instance from a dict (in place)."""
        super().update_from_dict(data)
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
