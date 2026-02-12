"""Validation exception classes for the QuestMaster application."""

from website.exceptions.base import QuestMasterError


class ValidationError(QuestMasterError):
    """Input validation failed.

    Args:
        message: Description of the validation failure.
        field: The field that failed validation (optional).
        code: Machine-readable error code.
        details: Additional context about the error.
    """

    http_status = 400

    def __init__(self, message: str, field: str = None, code: str = None, details: dict = None):
        self.field = field
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message=message, code=code or "VALIDATION_ERROR", details=details)
