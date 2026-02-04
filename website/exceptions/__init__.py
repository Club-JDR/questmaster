"""Custom exception hierarchy for the QuestMaster application."""

from website.exceptions.base import (
    QuestMasterError,
    NotFoundError,
    UnauthorizedError,
)
from website.exceptions.validation import ValidationError
from website.exceptions.database import DatabaseError
from website.exceptions.discord import DiscordError, DiscordAPIError
from website.exceptions.business import (
    GameError,
    GameFullError,
    GameClosedError,
    DuplicateRegistrationError,
    SessionConflictError,
)

__all__ = [
    "QuestMasterError",
    "NotFoundError",
    "UnauthorizedError",
    "ValidationError",
    "DatabaseError",
    "DiscordError",
    "DiscordAPIError",
    "GameError",
    "GameFullError",
    "GameClosedError",
    "DuplicateRegistrationError",
    "SessionConflictError",
]
