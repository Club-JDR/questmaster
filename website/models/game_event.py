# website/models/game_event.py

from website.extensions import db
from datetime import datetime


class GameEvent(db.Model):
    __tablename__ = "game_event"

    id = db.Column(db.BigInteger, primary_key=True)
    game_id = db.Column(db.BigInteger, db.ForeignKey("game.id"))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    event_type = db.Column(db.String(), nullable=False)
    description = db.Column(db.Text(), nullable=True)

