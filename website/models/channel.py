from website import db
from sqlalchemy import Enum
from website.models.game import GAME_TYPES
from sqlalchemy.dialects.postgresql import ENUM


class Channel(db.Model):
    __tablename__ = "channel"

    id = db.Column(db.String(), primary_key=True)
    type = db.Column(ENUM(*GAME_TYPES, name="game_type_enum", create_type=False), nullable=False)
    size = db.Column(db.Integer(), nullable=False, default=0)
