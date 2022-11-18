from api import db
from sqlalchemy import Enum

GAME_TYPES = ("oneshot", "campaign")

"""
players_table = db.Table(
    "game_players",
    db.Column("game_id", db.ForeignKey("game.id")),
    db.Column("player_id", db.ForeignKey("player.id")),
)
"""


class Game(db.Model):
    __tablename__ = "game"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String())
    type = db.Column("type", Enum(*GAME_TYPES, name="gender_enum", create_type=False))
    # gm = db.Column(db.Integer(), db.ForeignKey("user.id"))
    # players = db.relationship("User", secondary=players_table, backref='players')

    def __repr__(self) -> str:
        return "<id {self.id}>"

    def create_channel() -> str:
        return ""

    def create_role() -> str:
        return ""
