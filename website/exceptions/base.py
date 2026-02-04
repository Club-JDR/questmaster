"""Base exception classes for the QuestMaster application."""


class QuestMasterError(Exception):
    """Base exception for all QuestMaster errors.

    Args:
        message: Human-readable error description.
        code: Machine-readable error code (e.g. "GAME_FULL").
        details: Additional context about the error.
    """

    http_status = None

    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        """Serialize the error for API responses."""
        result = {"error": self.message, "code": self.code}
        if self.details:
            result["details"] = self.details
        return result

    def __repr__(self):
        parts = [f"message={self.message!r}"]
        if self.code:
            parts.append(f"code={self.code!r}")
        if self.details:
            parts.append(f"details={self.details!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"


class NotFoundError(QuestMasterError):
    """Resource not found."""

    http_status = 404

    def __init__(self, message: str, resource_type=None, resource_id=None, **kwargs):
        kwargs.setdefault("code", "NOT_FOUND")
        details = kwargs.pop("details", {})
        if resource_type is not None:
            details["resource_type"] = resource_type
        if resource_id is not None:
            details["resource_id"] = resource_id
        super().__init__(message, details=details, **kwargs)


class UnauthorizedError(QuestMasterError):
    """User not authorized to perform this action."""

    http_status = 403

    def __init__(self, message: str, user_id=None, action=None, **kwargs):
        kwargs.setdefault("code", "UNAUTHORIZED")
        details = kwargs.pop("details", {})
        if user_id is not None:
            details["user_id"] = user_id
        if action is not None:
            details["action"] = action
        super().__init__(message, details=details, **kwargs)
