"""Application logging configuration.

Wires up the root logger with:

* a stdout handler (human-readable in development, JSON in production,
  selected via ``QM_LOG_FORMAT``),
* a database handler persisting ``QM_DB_LOG_LEVEL``-and-above records to the
  ``app_log`` table (browsable from the admin "Journaux applicatifs" page),
* an optional Discord webhook handler for ``CRITICAL`` records, and
* ``SecretRedactionFilter``/``ContextFilter`` on every handler so no secret
  ever reaches an output and every record carries request context.

Secrets and levels are read from ``os.environ`` (not ``app.config``) so the
package stays usable from the scheduler and tests without a Flask app.
"""

# Standard library imports
import logging
import os

# Local imports
from website.logging_config.filters import ContextFilter, SecretRedactionFilter
from website.logging_config.formatters import HUMAN_FORMAT, CustomJsonFormatter
from website.logging_config.handlers import (
    DatabaseLogHandler,
    DiscordWebhookHandler,
    SafeStreamHandler,
)

__all__ = [
    "configure_logging",
    "ContextFilter",
    "SecretRedactionFilter",
    "CustomJsonFormatter",
    "DatabaseLogHandler",
    "DiscordWebhookHandler",
]

#: Noisy third-party loggers silenced below WARNING by default. Keeping
#: ``sqlalchemy`` quiet is also what stops the database handler from logging
#: (and thus re-triggering) its own INSERTs.
DEFAULT_MODULE_LEVELS = {
    "werkzeug": "WARNING",
    "urllib3": "WARNING",
    "sqlalchemy": "WARNING",
    "sqlalchemy.engine": "WARNING",
}


def _coerce_level(value: str, fallback: int = logging.INFO) -> int:
    """Convert a level name to its numeric value, tolerating bad input.

    Args:
        value: Level name (e.g. ``"INFO"``), case-insensitive.
        fallback: Level returned when the name is unknown.

    Returns:
        Numeric logging level.
    """
    return logging.getLevelNamesMapping().get(value.strip().upper(), fallback)


def _apply_module_levels() -> None:
    """Apply per-module log levels from defaults and ``QM_LOG_LEVELS``.

    ``QM_LOG_LEVELS`` is a comma-separated list of ``logger=LEVEL`` pairs
    (e.g. ``"werkzeug=INFO,website.services=DEBUG"``) overriding the
    defaults for noisy libraries.
    """
    levels = dict(DEFAULT_MODULE_LEVELS)
    for pair in os.environ.get("QM_LOG_LEVELS", "").split(","):
        name, sep, level = pair.partition("=")
        if sep and name.strip():
            levels[name.strip()] = level
    for name, level in levels.items():
        logging.getLogger(name).setLevel(_coerce_level(level))


def configure_logging() -> None:
    """Configure the root logger (stdout + database + optional webhook).

    Reads its settings from the environment: ``QM_LOG_FORMAT`` (``human``
    default / ``json``), ``QM_LOG_LEVEL`` (root level, default ``INFO``),
    ``QM_DB_LOG_LEVEL`` (database persistence threshold, default ``INFO``),
    ``QM_LOG_LEVELS`` (per-module overrides) and
    ``DISCORD_ERROR_WEBHOOK_URL`` (enables the webhook handler when set).

    Idempotent: existing root handlers are replaced, so calling it again
    (tests, dev reloader) does not stack duplicate handlers.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(_coerce_level(os.environ.get("QM_LOG_LEVEL", "INFO")))
    while root_logger.handlers:
        root_logger.removeHandler(root_logger.handlers[0])

    stream_handler = SafeStreamHandler()
    if os.environ.get("QM_LOG_FORMAT", "human").strip().lower() == "json":
        stream_handler.setFormatter(CustomJsonFormatter())
    else:
        stream_handler.setFormatter(logging.Formatter(HUMAN_FORMAT))

    handlers: list[logging.Handler] = [
        stream_handler,
        DatabaseLogHandler(level=_coerce_level(os.environ.get("QM_DB_LOG_LEVEL", "INFO"))),
    ]
    webhook_url = os.environ.get("DISCORD_ERROR_WEBHOOK_URL")
    if webhook_url:
        handlers.append(DiscordWebhookHandler(webhook_url))

    context_filter = ContextFilter()
    redaction_filter = SecretRedactionFilter()
    for handler in handlers:
        handler.addFilter(context_filter)
        handler.addFilter(redaction_filter)
        root_logger.addHandler(handler)

    _apply_module_levels()
