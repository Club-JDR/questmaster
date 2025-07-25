from website.extensions import db
from website.models.game_session import GameSession
from sqlalchemy import Enum, orm
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
import sqlalchemy.dialects.postgresql as pg
from schema import Schema, SchemaError


GAME_TYPES = ("oneshot", "campaign")
GAME_STATUS = ("draft", "open", "closed", "archived")
GAME_FREQUENCIES = ("weekly", "bi-weekly", "monthly", "other")
GAME_XP = ("all", "beginners", "seasoned")
GAME_CHAR = ("with_gm", "self", "pregen", "choice")
RESTRICTIONS = ("all", "16+", "18+")
AMBIENCES = ("chill", "serious", "comic", "epic")

CLASSIFICATION_SCHEMA = Schema(
    {
        "action": lambda n: 0 <= n <= 2,
        "investigation": lambda n: 0 <= n <= 2,
        "interaction": lambda n: 0 <= n <= 2,
        "horror": lambda n: 0 <= n <= 2,
    }
)

players_table = db.Table(
    "game_players",
    db.Column("game_id", db.ForeignKey("game.id"), primary_key=True),
    db.Column("player_id", db.ForeignKey("user.id"), primary_key=True),
    db.UniqueConstraint("game_id", "player_id", name="uix_game_user"),
)


class Game(db.Model):
    __tablename__ = "game"
    COLORS = {"oneshot": 0x198754, "campaign": 0x0D6EFD}

    id = db.Column(db.BigInteger(), primary_key=True)
    slug = db.Column(db.String(), unique=True, index=True)
    name = db.Column(db.String(), nullable=False)
    type = db.Column("type", Enum(*GAME_TYPES, name="game_type_enum"), nullable=False)
    length = db.Column(db.String(), nullable=False)
    gm_id = db.Column(db.String(), db.ForeignKey("user.id"), nullable=False)
    gm = db.relationship("User", back_populates="games_gm", foreign_keys=[gm_id])
    system_id = db.Column(db.Integer(), db.ForeignKey("system.id"), nullable=False)
    vtt_id = db.Column(db.Integer(), db.ForeignKey("vtt.id"), nullable=True)
    description = db.Column(db.Text(), nullable=False)
    restriction = db.Column(
        "restriction", Enum(*RESTRICTIONS, name="restriction_enum"), nullable=False
    )
    restriction_tags = db.Column(db.String())
    party_size = db.Column(db.Integer(), nullable=False, default=4)
    party_selection = db.Column(db.Boolean(), nullable=False, default=False)
    players = db.relationship("User", secondary=players_table, backref="games")
    xp = db.Column("experience", Enum(*GAME_XP, name="game_xp_enum"), default="all")
    date = db.Column(db.DateTime, nullable=False)
    session_length = db.Column(db.DECIMAL(2, 1), nullable=False)
    frequency = db.Column(
        "frequency", Enum(*GAME_FREQUENCIES, name="game_frequency_enum")
    )
    characters = db.Column("characters", Enum(*GAME_CHAR, name="game_char_enum"))
    classification = db.Column(MutableDict.as_mutable(JSONB))
    ambience = db.Column(pg.ARRAY(Enum(*AMBIENCES, name="game_ambience_enum")))
    complement = db.Column(db.Text())
    img = db.Column(db.String())
    sessions = db.relationship("GameSession", backref="game")
    channel = db.Column(db.String())
    msg_id = db.Column(db.String())
    role = db.Column(db.String())
    status = db.Column(
        "status",
        Enum(*GAME_STATUS, name="game_status_enum"),
        nullable=False,
        server_default="draft",
    )

    @orm.validates("classification")
    def validate_classification(self, key, value):
        try:
            if value:
                CLASSIFICATION_SCHEMA.validate(value)
            return value
        except SchemaError:
            raise ValueError(f"Invalid classification format {value}")

    @orm.validates("party_size")
    def validate_party_size(self, key, value):
        if int(value) < 1:
            raise ValueError(f"Number of players must be > 1, was {value}")
        return value
