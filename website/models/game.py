from website import db
from sqlalchemy import Enum

GAME_TYPES = ("oneshot", "campaign")
GAME_STATUS = ("draft", "open", "closed", "archived")
RESTRICTIONS = ("all", "16+", "18+")


players_table = db.Table(
    "game_players",
    db.Column("game_id", db.ForeignKey("game.id")),
    db.Column("player_id", db.ForeignKey("user.id")),
)


def remove_archived(games) -> object:
    """
    Remove all closed games from a list of games.
    """
    for game in games:
        if game.status == "archived":
            games.remove(game)
    return games


class Game(db.Model):
    __tablename__ = "game"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    type = db.Column("type", Enum(*GAME_TYPES, name="game_type_enum"), nullable=False)
    length = db.Column(db.String(), nullable=False)
    gm_id = db.Column(db.String(), db.ForeignKey("user.id"), nullable=False)
    system_id = db.Column(db.Integer(), db.ForeignKey("system.id"), nullable=False)
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
    img = db.Column(db.String())
    date = db.Column(db.DateTime)
