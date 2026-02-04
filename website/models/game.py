from website.extensions import db
from website.models.game_session import GameSession
from config.constants import (
    GAME_TYPES,
    GAME_STATUS,
    GAME_FREQUENCIES,
    GAME_XP,
    GAME_CHAR,
    RESTRICTIONS,
    AMBIENCES,
)
from sqlalchemy import Enum, orm
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
import sqlalchemy.dialects.postgresql as pg
from schema import Schema, SchemaError
from website.exceptions import ValidationError


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
    """
    Represents a tabletop RPG game (oneshot or campaign).
    """

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
    special_event_id = db.Column(
        db.Integer, db.ForeignKey("special_event.id"), nullable=True
    )
    special_event = db.relationship("SpecialEvent", back_populates="games")

    @orm.validates("classification")
    def validate_classification(self, key, value):
        try:
            if value:
                CLASSIFICATION_SCHEMA.validate(value)
            return value
        except SchemaError:
            raise ValidationError(
                "Invalid classification format.",
                field="classification",
                details={"value": value},
            )

    @orm.validates("party_size")
    def validate_party_size(self, key, value):
        if int(value) < 1:
            raise ValidationError(
                "Number of players must be at least one.",
                field="party_size",
                details={"value": value},
            )
        return value

    def _serialize_relation(self, obj):
        """Helper to serialize a single related object."""
        if obj and hasattr(obj, "to_dict"):
            return obj.to_dict()
        return None

    def _serialize_relation_list(self, objects):
        """Helper to serialize a list of related objects."""
        return [obj.to_dict() for obj in objects if hasattr(obj, "to_dict")]

    def _add_relationships_to_dict(self, data):
        """Add relationship data to the dictionary."""
        data["gm"] = self._serialize_relation(getattr(self, "gm", None))
        data["system"] = self._serialize_relation(getattr(self, "system", None))
        data["vtt"] = self._serialize_relation(getattr(self, "vtt", None))
        data["players"] = self._serialize_relation_list(getattr(self, "players", []))
        data["sessions"] = self._serialize_relation_list(getattr(self, "sessions", []))
        data["special_event"] = self._serialize_relation(
            getattr(self, "special_event", None)
        )

    def to_dict(self, include_relationships=False):
        """
        Serialize the Game instance into a Python dict.

        Args:
            include_relationships: If True, includes nested objects (gm, system, vtt, players, sessions).
                                   If False, only includes IDs.
        """
        data = {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "type": self.type,
            "length": self.length,
            "gm_id": self.gm_id,
            "system_id": self.system_id,
            "vtt_id": self.vtt_id,
            "description": self.description,
            "restriction": self.restriction,
            "restriction_tags": self.restriction_tags,
            "party_size": self.party_size,
            "party_selection": self.party_selection,
            "xp": self.xp,
            "date": self.date.isoformat() if self.date else None,
            "session_length": (
                float(self.session_length) if self.session_length else None
            ),
            "frequency": self.frequency,
            "characters": self.characters,
            "classification": self.classification,
            "ambience": list(self.ambience) if self.ambience else None,
            "complement": self.complement,
            "img": self.img,
            "channel": self.channel,
            "msg_id": self.msg_id,
            "role": self.role,
            "status": self.status,
            "special_event_id": self.special_event_id,
        }

        if include_relationships:
            self._add_relationships_to_dict(data)
        else:
            data["player_ids"] = [p.id for p in self.players]

        return data

    def to_json(self, include_relationships=False):
        """
        Alias for to_dict() for API compatibility.
        """
        return self.to_dict(include_relationships=include_relationships)

    @property
    def json(self):
        """
        Property alias for JSON serialization.
        """
        return self.to_dict()

    @classmethod
    def from_dict(cls, data):
        """
        Create a Game instance from a Python dict.
        Note: This does not handle relationships (gm, players, sessions, etc.).
        Those should be set separately after creation.
        """
        from datetime import datetime
        from decimal import Decimal

        # Convert date string to datetime if needed
        date_value = data.get("date")
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value)

        # Convert session_length to Decimal if needed
        session_length_value = data.get("session_length")
        if session_length_value is not None and not isinstance(
            session_length_value, Decimal
        ):
            session_length_value = Decimal(str(session_length_value))

        return cls(
            id=data.get("id"),
            slug=data.get("slug"),
            name=data.get("name"),
            type=data.get("type"),
            length=data.get("length"),
            gm_id=data.get("gm_id"),
            system_id=data.get("system_id"),
            vtt_id=data.get("vtt_id"),
            description=data.get("description"),
            restriction=data.get("restriction"),
            restriction_tags=data.get("restriction_tags"),
            party_size=data.get("party_size"),
            party_selection=data.get("party_selection"),
            xp=data.get("xp"),
            date=date_value,
            session_length=session_length_value,
            frequency=data.get("frequency"),
            characters=data.get("characters"),
            classification=data.get("classification"),
            ambience=data.get("ambience"),
            complement=data.get("complement"),
            img=data.get("img"),
            channel=data.get("channel"),
            msg_id=data.get("msg_id"),
            role=data.get("role"),
            status=data.get("status"),
            special_event_id=data.get("special_event_id"),
        )

    @classmethod
    def from_json(cls, data):
        """
        Alias for from_dict() for API compatibility.
        """
        return cls.from_dict(data)

    def update_from_dict(self, data):
        """
        Update the Game instance from a dict (in place).
        Protected fields (id, slug) are excluded from updates.
        Relationships must be handled separately.
        """
        from datetime import datetime
        from decimal import Decimal

        # Fields that should not be updated via this method
        protected_fields = {"id", "slug"}

        for key, value in data.items():
            if key in protected_fields:
                continue
            if hasattr(self, key) and key not in [
                "gm",
                "players",
                "sessions",
                "system",
                "vtt",
                "special_event",
            ]:
                # Handle special conversions
                if key == "date" and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                elif (
                    key == "session_length"
                    and value is not None
                    and not isinstance(value, Decimal)
                ):
                    value = Decimal(str(value))

                setattr(self, key, value)
        return self

    def __repr__(self):
        return f"<Game id={self.id} slug='{self.slug}' name='{self.name}' type='{self.type}' status='{self.status}'>"

    def __eq__(self, other):
        if not isinstance(other, Game):
            return NotImplemented
        return (
            self.id == other.id
            and self.slug == other.slug
            and self.name == other.name
            and self.type == other.type
            and self.status == other.status
        )

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
