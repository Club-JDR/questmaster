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
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    description = db.Column(db.Text)
    game = db.relationship("Game", backref="events")

    __table_args__ = (
        db.Index("ix_gameevent_timestamp", "timestamp"),
        db.Index("ix_gameevent_game", "game_id"),
    )
