"""Custom log handlers: database persistence and Discord webhook alerts."""

# Standard library imports
import logging
import threading
import traceback
from datetime import datetime, timezone
from logging.handlers import QueueHandler, QueueListener

# Third-party imports
import requests
from flask import has_app_context
from sqlalchemy import insert


class SafeStreamHandler(logging.StreamHandler):
    """StreamHandler that stays quiet once its stream is closed.

    At interpreter exit (e.g. APScheduler's ``atexit`` shutdown under pytest,
    which closes the captured stderr) a plain ``StreamHandler`` spews a
    "Logging error" traceback; this variant just drops the record.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit the record unless the underlying stream is closed.

        Args:
            record: Log record to write.
        """
        if getattr(self.stream, "closed", False):
            return
        super().emit(record)


class PassthroughQueueHandler(QueueHandler):
    """QueueHandler that hands records to the listener thread unmodified.

    The stdlib default ``prepare()`` eagerly formats the message (merging any
    traceback into it) and clears ``args``/``exc_info`` — needed so a record
    can be pickled across a process boundary. This app only ever threads
    records within a single process, and ``DatabaseLogHandler`` relies on the
    original ``exc_info`` being intact to append its own traceback, so this
    passes the record through exactly as emitted.
    """

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        """Return the record unchanged (see class docstring).

        Args:
            record: Log record about to be queued for the listener thread.

        Returns:
            The same record, untouched.
        """
        return record


class AppContextQueueListener(QueueListener):
    """QueueListener whose worker thread runs inside a persistent Flask app context.

    ``DatabaseLogHandler`` resolves ``current_app`` (via ``db.engine``) on
    whichever thread it runs on; its dedicated listener thread never has one
    pushed onto it otherwise, so every write would silently no-op behind
    ``has_app_context()``. One context is pushed for the thread's entire
    lifetime — cheap, and safe since the handler never touches ``db.session``
    (only ``db.engine``, which is thread-safe).
    """

    def __init__(self, log_queue, *handlers, app=None, **kwargs):
        super().__init__(log_queue, *handlers, **kwargs)
        self._app = app

    def _monitor(self) -> None:
        """Run the inherited listener loop inside the app context, if any."""
        if self._app is None:
            super()._monitor()
            return
        with self._app.app_context():
            super()._monitor()


class DatabaseLogHandler(logging.Handler):
    """Persist log records to the ``app_log`` table.

    Writes go through a *dedicated* connection (``db.engine.begin()``) using
    SQLAlchemy Core, never ``db.session``: a commit inside ``emit()`` would
    otherwise break the request's transaction boundary owned by the service
    layer.

    In production this only ever runs on the ``AppContextQueueListener``
    background thread (see ``configure_logging()``), never on the thread
    that emitted the record, so a slow write never adds latency to the
    request/job that triggered it. ``emit()`` is guarded by
    ``has_app_context()`` (no engine outside an app context) and a
    thread-local reentrancy flag (a log emitted while writing a log is
    dropped instead of recursing). It never raises.
    """

    def __init__(self, level: int | str = logging.INFO):
        super().__init__(level=level)
        self._local = threading.local()

    def emit(self, record: logging.LogRecord) -> None:
        """Write the record to the ``app_log`` table (best-effort).

        Args:
            record: Log record to persist. Expected to carry the structured
                fields injected by ``ContextFilter`` and an already-redacted
                message (``SecretRedactionFilter`` runs before ``emit``).
        """
        if getattr(self._local, "emitting", False) or not has_app_context():
            return
        self._local.emitting = True
        try:
            from website.extensions import db
            from website.models.app_log import AppLog

            message = record.getMessage()
            if record.exc_info:
                message = f"{message}\n{''.join(traceback.format_exception(*record.exc_info))}"

            with db.engine.begin() as conn:
                conn.execute(
                    insert(AppLog.__table__).values(
                        timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc),
                        level=record.levelname,
                        level_no=record.levelno,
                        logger=record.name,
                        message=message,
                        trace_id=getattr(record, "trace_id", None),
                        user_id=getattr(record, "user_id", None),
                        username=getattr(record, "username", None),
                        endpoint=getattr(record, "endpoint", None),
                        impersonator_id=getattr(record, "impersonator_id", None),
                        impersonator_username=getattr(record, "impersonator_username", None),
                        module=record.module,
                        func=record.funcName,
                        line=record.lineno,
                    )
                )
        except Exception:
            self.handleError(record)
        finally:
            self._local.emitting = False


class DiscordWebhookHandler(logging.Handler):
    """Best-effort POST of high-severity records to a Discord webhook.

    Intended for ``CRITICAL`` alerts only. The POST uses a short timeout and
    never raises, so a Discord outage can never take the application down.
    """

    #: Discord caps message content at 2000 characters.
    MAX_CONTENT_LENGTH = 1900
    TIMEOUT_SECONDS = 3

    def __init__(self, webhook_url: str, level: int | str = logging.CRITICAL):
        super().__init__(level=level)
        self.webhook_url = webhook_url

    def emit(self, record: logging.LogRecord) -> None:
        """Send the record to the configured Discord webhook (best-effort).

        Args:
            record: Log record to send.
        """
        try:
            content = (
                f":rotating_light: **{record.levelname}** `{record.name}`\n{record.getMessage()}"
            )[: self.MAX_CONTENT_LENGTH]
            requests.post(
                self.webhook_url, json={"content": content}, timeout=self.TIMEOUT_SECONDS
            )
        except Exception:
            self.handleError(record)
