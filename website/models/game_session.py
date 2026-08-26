"""GameSession model for scheduled play sessions."""

from website.extensions import db
from website.models.base import SerializableMixin


class GameSession(db.Model, SerializableMixin):
    """A scheduled play session belonging to a Game.

    Attributes:
        id: Primary key.
        game_id: Foreign key to the parent game.
        start: Session start datetime.
        end: Session end datetime.
        reminder_sent: Whether the ~24h-ahead Discord reminder has already
            been sent for this session (see ``SESSION_REMINDER_HORIZON_HOURS``),
            so the scheduler never sends it twice.
    """

    __tablename__ = "game_session"

    _exclude_fields = []
    _relationship_fields = []

    id = db.Column(db.BigInteger, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), index=True)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=False)
    reminder_sent = db.Column(db.Boolean(), nullable=False, default=False, server_default="false")

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            game_id=data.get("game_id"),
            start=data.get("start"),
            end=data.get("end"),
            reminder_sent=data.get("reminder_sent", False),
        )

    def update_from_dict(self, data):
        super().update_from_dict(data)
        return self
