"""Logging utility helpers.

Request context (trace_id, user_id, endpoint) is injected on every handler by
``website.logging_config.ContextFilter``, so callers just use a plain
``logging.getLogger(__name__)`` module logger — no adapter or shared logger
instance needed.
"""


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
