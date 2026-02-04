"""Business logic exception classes for the QuestMaster application."""

from website.exceptions.base import QuestMasterError


class GameError(QuestMasterError):
    """Game-related business logic error."""

    http_status = 409

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("code", "GAME_ERROR")
        super().__init__(message, **kwargs)


class GameFullError(GameError):
    """Game has reached maximum players."""

    def __init__(self, message: str, game_id=None, max_players=None, **kwargs):
        kwargs.setdefault("code", "GAME_FULL")
        details = kwargs.pop("details", {})
        if game_id is not None:
            details["game_id"] = game_id
        if max_players is not None:
            details["max_players"] = max_players
        super().__init__(message, details=details, **kwargs)


class GameClosedError(GameError):
    """Game is closed for registration."""

    def __init__(self, message: str, game_id=None, **kwargs):
        kwargs.setdefault("code", "GAME_CLOSED")
        details = kwargs.pop("details", {})
        if game_id is not None:
            details["game_id"] = game_id
        super().__init__(message, details=details, **kwargs)


class DuplicateRegistrationError(GameError):
    """Player already registered for this game."""

    def __init__(self, message: str, game_id=None, user_id=None, **kwargs):
        kwargs.setdefault("code", "DUPLICATE_REGISTRATION")
        details = kwargs.pop("details", {})
        if game_id is not None:
            details["game_id"] = game_id
        if user_id is not None:
            details["user_id"] = user_id
        super().__init__(message, details=details, **kwargs)


class SessionConflictError(GameError):
    """Game session overlaps with an existing session."""

    def __init__(self, message: str, game_id=None, **kwargs):
        kwargs.setdefault("code", "SESSION_CONFLICT")
        details = kwargs.pop("details", {})
        if game_id is not None:
            details["game_id"] = game_id
        super().__init__(message, details=details, **kwargs)
