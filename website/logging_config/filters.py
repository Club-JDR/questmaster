"""Logging filters: request-context enrichment and secret redaction."""

# Standard library imports
import logging
import os
import re

# Third-party imports
from flask import g, has_request_context, request, session

#: Environment variables whose values must never appear in a log line.
SECRET_ENV_VARS = (
    "DISCORD_BOT_TOKEN",
    "DISCORD_CLIENT_SECRET",
    "JWT_SECRET_KEY",
    "FLASK_AUTH_SECRET",
    "POSTGRES_PASSWORD",
    "DISCORD_ERROR_WEBHOOK_URL",
)

REDACTED = "[REDACTED]"

#: ``Authorization: Bearer <token>`` style credentials.
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[a-z0-9._~+/=-]{8,}")
#: ``token=…``, ``secret: …`` style key/value pairs.
_KEY_VALUE_PATTERN = re.compile(
    r"(?i)\b(token|secret|password|passwd|api_key|apikey|authorization)"
    r"(\s*[=:]\s*)([^\s&\"',;]+)"
)


class ContextFilter(logging.Filter):
    """Inject Flask request context fields onto every log record.

    Adds ``trace_id`` (from ``g``), ``user_id``/``username`` (from the
    session, i.e. who performed the action) and ``endpoint`` (from the
    request) so formatters and the database handler can emit structured
    fields. Outside a request context the fields are set to ``None`` so
    format strings never raise.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach request context attributes to the record.

        Args:
            record: Log record being processed.

        Returns:
            Always True (the record is never dropped).
        """
        record.trace_id = None
        record.user_id = None
        record.username = None
        record.endpoint = None
        if has_request_context():
            record.trace_id = getattr(g, "trace_id", None)
            record.user_id = session.get("user_id")
            record.username = session.get("username")
            record.endpoint = request.endpoint
        return True


class SecretRedactionFilter(logging.Filter):
    """Redact secrets from log messages before any handler emits them.

    Two redaction strategies are combined:

    * literal values of known secret environment variables (read once at
      construction time), and
    * regex patterns for bearer tokens and ``key=value`` credential pairs.

    The record's ``msg`` is rewritten to the redacted, fully interpolated
    message and ``args`` is cleared, so every downstream handler and
    formatter only ever sees redacted text.
    """

    def __init__(self):
        super().__init__()
        # Ignore very short values to avoid redacting unrelated substrings.
        self._secrets = [
            value
            for name in SECRET_ENV_VARS
            if (value := os.environ.get(name)) and len(value) >= 8
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Rewrite the record message with all secrets redacted.

        Args:
            record: Log record being processed.

        Returns:
            Always True (the record is never dropped).
        """
        message = record.getMessage()
        for secret in self._secrets:
            message = message.replace(secret, REDACTED)
        message = _BEARER_PATTERN.sub(f"Bearer {REDACTED}", message)
        message = _KEY_VALUE_PATTERN.sub(rf"\1\2{REDACTED}", message)
        record.msg = message
        record.args = None
        return True
