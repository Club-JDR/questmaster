"""Log record formatters (human-readable and JSON)."""

# Standard library imports
import json
import logging
from datetime import datetime, timezone

#: Development-friendly single-line format; ``trace_id`` is injected by
#: :class:`website.logging_config.filters.ContextFilter`.
HUMAN_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [trace_id=%(trace_id)s]"


class CustomJsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects (stdlib only).

    Emitted fields: ``timestamp`` (ISO 8601 UTC), ``level``, ``name``,
    ``message``, ``trace_id``, ``user_id``, ``username``, ``endpoint``,
    plus ``exc_info`` when an exception is attached.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Serialize the record to a JSON string.

        Args:
            record: Log record to format.

        Returns:
            One-line JSON representation of the record.
        """
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None),
            "user_id": getattr(record, "user_id", None),
            "username": getattr(record, "username", None),
            "endpoint": getattr(record, "endpoint", None),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)
