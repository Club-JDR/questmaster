from api import db, bot
from sqlalchemy import Enum

GAME_TYPES = ("oneshot", "campaign")
RESTRICTIONS = ("all", "16+", "18+")


players_table = db.Table(
    "game_players",
    db.Column("game_id", db.ForeignKey("game.id")),
    db.Column("player_id", db.ForeignKey("user.id")),
)


class Game(db.Model):
    __tablename__ = "game"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String())
    type = db.Column("type", Enum(*GAME_TYPES, name="game_type_enum"))
    length = db.Column(db.String())
    gm_id = db.Column(db.String(), db.ForeignKey("user.id"))
    system = db.Column(db.String())
    description = db.Column(db.Text())
    restriction = db.Column("restriction", Enum(*RESTRICTIONS, name="restriction_enum"))
    restriction_tags = db.Column(db.String())
    party_size = db.Column(db.Integer())
    party_selection = db.Column(db.Boolean(), default=False)
    pregen = db.Column(db.Boolean(), default=False)
    players = db.relationship("User", secondary=players_table, backref="players")
    channel = db.Column(db.String())
    role = db.Column(db.String())

    def serialize(self) -> object:
        return {
            "id": self.id,
            "name": self.name,
            "gm": self.gm.serialize(),
            "type": self.type,
            "length": self.length,
            "system": self.system,
            "description": self.description,
            "restriction": self.restriction,
            "restriction_tags": self.restriction_tags,
            "party_size": self.party_size,
            "party_selection": self.party_selection,
            "pregen": self.pregen,
            "players": [player.serialize() for player in self.players],
            "channel": bot.get_channel(self.channel),
            "role": bot.get_role(self.role),
        }
