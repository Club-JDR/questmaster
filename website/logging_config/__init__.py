"""Application logging configuration.

Wires up the root logger with:

* a stdout handler (human-readable in development, JSON in production,
  selected via ``QM_LOG_FORMAT``), handled synchronously,
* a database handler persisting ``QM_DB_LOG_LEVEL``-and-above records to the
  ``app_log`` table (browsable from the admin "Journaux applicatifs" page),
* an optional Discord webhook handler for ``CRITICAL`` records, and
* ``SecretRedactionFilter``/``ContextFilter`` on every handler so no secret
  ever reaches an output and every record carries request context.

The database and webhook handlers do their own I/O (a DB write, an HTTP
POST), so they run off a ``QueueHandler``/``QueueListener`` pair on a
dedicated background thread instead of the request thread — a slow write or
a stalled webhook can never add latency to (or block) the request that
triggered the log line.

Secrets and levels are read from ``os.environ`` (not ``app.config``) so the
package stays usable from the scheduler and tests without a Flask app.
"""

# Standard library imports
import atexit
import logging
import os
import queue

# Local imports
from website.logging_config.filters import ContextFilter, SecretRedactionFilter
from website.logging_config.formatters import HUMAN_FORMAT, CustomJsonFormatter
from website.logging_config.handlers import (
    AppContextQueueListener,
    DatabaseLogHandler,
    DiscordWebhookHandler,
    PassthroughQueueHandler,
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

#: The active listener thread draining the DB/webhook queue, if any. Tracked
#: so a repeat call to ``configure_logging()`` (tests, the dev reloader) stops
#: the previous thread instead of leaking an idle one on every call.
_queue_listener: AppContextQueueListener | None = None


def _stop_queue_listener() -> None:
    """Stop the current queue listener, if any (no-op otherwise).

    Registered once with ``atexit`` at import time (not per
    ``configure_logging()`` call) so process shutdown flushes whatever
    listener is active without piling up redundant exit hooks across repeat
    calls (tests, the dev reloader).
    """
    if _queue_listener is not None:
        _queue_listener.stop()


atexit.register(_stop_queue_listener)

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


def configure_logging(app=None) -> None:
    """Configure the root logger (stdout + queued database + optional webhook).

    Reads its settings from the environment: ``QM_LOG_FORMAT`` (``human``
    default / ``json``), ``QM_LOG_LEVEL`` (root level, default ``INFO``),
    ``QM_DB_LOG_LEVEL`` (database persistence threshold, default ``INFO``),
    ``QM_LOG_LEVELS`` (per-module overrides) and
    ``DISCORD_ERROR_WEBHOOK_URL`` (enables the webhook handler when set).

    Idempotent: existing root handlers are replaced and any previous queue
    listener thread is stopped, so calling it again (tests, the dev reloader)
    does not stack duplicate handlers or leak idle background threads.

    Args:
        app: The Flask app being configured, if any. Passed through to the
            queue listener thread so ``DatabaseLogHandler`` can resolve
            ``current_app`` there (see ``AppContextQueueListener``). May be
            omitted for non-Flask callers (e.g. a bare script); database
            logging then silently no-ops, exactly as it does today outside
            any app context.
    """
    global _queue_listener

    root_logger = logging.getLogger()
    root_logger.setLevel(_coerce_level(os.environ.get("QM_LOG_LEVEL", "INFO")))
    while root_logger.handlers:
        root_logger.removeHandler(root_logger.handlers[0])
    if _queue_listener is not None:
        _queue_listener.stop()
        _queue_listener = None

    stream_handler = SafeStreamHandler()
    if os.environ.get("QM_LOG_FORMAT", "human").strip().lower() == "json":
        stream_handler.setFormatter(CustomJsonFormatter())
    else:
        stream_handler.setFormatter(logging.Formatter(HUMAN_FORMAT))

    # These two do their own I/O (a DB write, an HTTP POST) — never call them
    # directly from the request thread. They're driven by the queue listener
    # below instead, each still gated by its own level.
    slow_handlers: list[logging.Handler] = [
        DatabaseLogHandler(level=_coerce_level(os.environ.get("QM_DB_LOG_LEVEL", "INFO"))),
    ]
    webhook_url = os.environ.get("DISCORD_ERROR_WEBHOOK_URL")
    if webhook_url:
        slow_handlers.append(DiscordWebhookHandler(webhook_url))

    log_queue = queue.SimpleQueue()
    queue_handler = PassthroughQueueHandler(log_queue)
    _queue_listener = AppContextQueueListener(
        log_queue, *slow_handlers, app=app, respect_handler_level=True
    )
    _queue_listener.start()

    context_filter = ContextFilter()
    redaction_filter = SecretRedactionFilter()
    for handler in (stream_handler, queue_handler):
        handler.addFilter(context_filter)
        handler.addFilter(redaction_filter)
        root_logger.addHandler(handler)

    _apply_module_levels()
