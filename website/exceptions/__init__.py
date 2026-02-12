"""Custom exception hierarchy for the QuestMaster application."""

from website.exceptions.base import NotFoundError, QuestMasterError, UnauthorizedError
from website.exceptions.business import (
    DuplicateRegistrationError,
    GameClosedError,
    GameError,
    GameFullError,
    SessionConflictError,
)
from website.exceptions.database import DatabaseError
from website.exceptions.discord import DiscordAPIError, DiscordError
from website.exceptions.validation import ValidationError

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
