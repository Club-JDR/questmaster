"""Database exception classes for the QuestMaster application."""

from website.exceptions.base import QuestMasterError


class DatabaseError(QuestMasterError):
    """Database operation failed."""

    http_status = 500

    def __init__(self, message: str, operation=None, **kwargs):
        kwargs.setdefault("code", "DATABASE_ERROR")
        details = kwargs.pop("details", {})
        if operation is not None:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)
