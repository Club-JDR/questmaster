"""Request-aware logging utilities."""

import logging

from flask import g


class RequestLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that prepends the request trace ID to log messages."""

    def process(self, msg, kwargs):
        trace_id = getattr(g, "trace_id", "no-trace-id")
        return f"[trace_id={trace_id}] {msg}", kwargs


def sanitize_log_value(value: object) -> str:
    """Sanitize a user-controlled value for safe logging.

    Strips characters that could forge or break log lines (CR, LF and other
    control characters), mitigating log injection from user-supplied data.

    Args:
        value: Value to sanitize (coerced to ``str``).

    Returns:
        A single-line string safe to embed in a log message.
    """
    return "".join(c for c in str(value) if c.isprintable())


def configure_logging(level=logging.INFO):
    """Configure the root logger with a stream handler.

    Args:
        level: Logging level. Defaults to INFO.
    """
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not root_logger.handlers:
        root_logger.addHandler(handler)


logger = RequestLoggerAdapter(logging.getLogger(__name__), {})


def log_game_event(action, game_id, description=None, user_id=None):
    """Convenience wrapper to log a game event via GameEventService.

    Args:
        action: Event action type.
        game_id: ID of the related game.
        description: Optional event description.
        user_id: Optional ID of the user that performed the action.
    """
    from website.services.game_event import GameEventService

    GameEventService().log_event(action, game_id, description, user_id)
