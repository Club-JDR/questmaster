from website.extensions import db
from website.models.base import SerializableMixin
from .user import User


class Trophy(db.Model, SerializableMixin):
    __tablename__ = "trophy"

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    unique = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String(), nullable=True)

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            unique=data.get("unique", False),
            icon=data.get("icon"),
        )

    def update_from_dict(self, data):
        super().update_from_dict(data)
        return self

    def __str__(self):
        return self.name


class UserTrophy(db.Model, SerializableMixin):
    __tablename__ = "user_trophy"

    _exclude_fields = []
    _relationship_fields = ["user", "trophy"]

    user_id = db.Column(db.String(), db.ForeignKey("user.id"), primary_key=True)
    trophy_id = db.Column(db.Integer, db.ForeignKey("trophy.id"), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", back_populates="trophies")
    trophy = db.relationship("Trophy")

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data.get("user_id"),
            trophy_id=data.get("trophy_id"),
            quantity=data.get("quantity", 1),
        )

    def update_from_dict(self, data):
        super().update_from_dict(data)
        return self
