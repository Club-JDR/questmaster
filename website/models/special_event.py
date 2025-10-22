from website.extensions import db
from website.models.base import SerializableMixin


class SpecialEvent(db.Model, SerializableMixin):
    __tablename__ = "special_event"

    _exclude_fields = []
    _relationship_fields = ["games"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    emoji = db.Column(db.String, nullable=True)
    color = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, default=False, nullable=False)

    games = db.relationship("Game", back_populates="special_event")

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            emoji=data.get("emoji"),
            color=data.get("color"),
            active=data.get("active", False),
        )

    def update_from_dict(self, data):
        super().update_from_dict(data)
        return self

    def __str__(self):
        hex_color = (
            f"#{self.color:06x}" if isinstance(self.color, int) else (self.color or "")
        )
        return f"{self.emoji} {self.name} ({hex_color})"
