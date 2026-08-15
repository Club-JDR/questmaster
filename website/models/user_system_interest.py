"""UserSystemInterest model: a user's declared interest in a game system."""

from sqlalchemy import Enum

from config.constants import SYSTEM_INTEREST_ROLES
from website.extensions import db
from website.models.base import SerializableMixin


class UserSystemInterest(db.Model, SerializableMixin):
    """A user's declared interest in playing or running a game system.

    Purely a passive signal (not a registration) so a GM can gauge demand for
    a system before pitching a game. A user may declare interest in both
    roles for the same system — each role is its own row.

    Attributes:
        user_id: Foreign key to User.
        system_id: Foreign key to System.
        role: "player" or "gm". A GM can declare interest in a system
            they've never run (aspirational); the system page's "GMs who
            have run it" list is separate, derived from actual game history.
        note: Optional free text (availability, tone preferences, etc.).
    """

    __tablename__ = "user_system_interest"

    _exclude_fields = []
    _relationship_fields = ["user", "system"]

    user_id = db.Column(db.String(), db.ForeignKey("user.id"), primary_key=True)
    system_id = db.Column(db.BigInteger(), db.ForeignKey("system.id"), primary_key=True)
    role = db.Column(
        Enum(*SYSTEM_INTEREST_ROLES, name="system_interest_role_enum"), primary_key=True
    )
    note = db.Column(db.Text(), nullable=True)

    user = db.relationship("User")
    system = db.relationship("System")

    @classmethod
    def from_dict(cls, data):
        """
        Create a UserSystemInterest instance from a Python dict.
        """
        return cls(
            user_id=data.get("user_id"),
            system_id=data.get("system_id"),
            role=data.get("role"),
            note=data.get("note"),
        )

    def update_from_dict(self, data):
        """
        Update the UserSystemInterest instance from a dict (in place).
        """
        super().update_from_dict(data)
        return self

    def __repr__(self):
        return (
            f"<UserSystemInterest user_id={self.user_id} system_id={self.system_id} "
            f"role='{self.role}'>"
        )

    def __eq__(self, other):
        if not isinstance(other, UserSystemInterest):
            return NotImplemented
        return (
            self.user_id == other.user_id
            and self.system_id == other.system_id
            and self.role == other.role
            and self.note == other.note
        )

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
