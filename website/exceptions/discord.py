"""Discord-related exception classes for the QuestMaster application."""

from website.exceptions.base import QuestMasterError


class DiscordError(QuestMasterError):
    """Base Discord-related error."""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("code", "DISCORD_ERROR")
        super().__init__(message, **kwargs)


class DiscordAPIError(DiscordError):
    """Discord API request failed.

    Args:
        message: Description of the API error.
        status_code: HTTP status code from the Discord API.
        response: The raw response body from Discord (optional).
    """

    def __init__(self, message: str, status_code: int, response: dict = None):
        self.status_code = status_code
        self.response = response or {}
        super().__init__(
            message=f"[{status_code}] {message}",
            code=f"DISCORD_API_{status_code}",
            details={"status_code": status_code, "response": self.response},
        )
