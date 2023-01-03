from api import db, bot
from sqlalchemy import Enum

GAME_TYPES = ("oneshot", "campaign")
GAME_STATUS = ("draft", "open", "closed", "archived")
RESTRICTIONS = ("all", "16+", "18+")


players_table = db.Table(
    "game_players",
    db.Column("game_id", db.ForeignKey("game.id")),
    db.Column("player_id", db.ForeignKey("user.id")),
)


class Game(db.Model):
    __tablename__ = "game"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    type = db.Column("type", Enum(*GAME_TYPES, name="game_type_enum"), nullable=False)
    length = db.Column(db.String(), nullable=False)
    gm_id = db.Column(db.String(), db.ForeignKey("user.id"), nullable=False)
    system = db.Column(db.String(), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    restriction = db.Column(
        "restriction", Enum(*RESTRICTIONS, name="restriction_enum"), nullable=False
    )
    restriction_tags = db.Column(db.String())
    party_size = db.Column(db.Integer(), nullable=False, default=4)
    party_selection = db.Column(db.Boolean(), nullable=False, default=False)
    pregen = db.Column(db.Boolean(), nullable=False, default=False)
    players = db.relationship("User", secondary=players_table, backref="games")
    channel = db.Column(db.String())
    role = db.Column(db.String())
    status = db.Column(
        "status",
        Enum(*GAME_STATUS, name="game_status_enum"),
        nullable=False,
        server_default="draft",
    )

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
            "status": self.status,
        }
