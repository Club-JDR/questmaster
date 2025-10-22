from website.extensions import db
from website.models.base import SerializableMixin


class GameSession(db.Model, SerializableMixin):
    __tablename__ = "game_session"

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.BigInteger, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            game_id=data.get("game_id"),
            start=data.get("start"),
            end=data.get("end"),
        )

    def update_from_dict(self, data):
        super().update_from_dict(data)
        return self
