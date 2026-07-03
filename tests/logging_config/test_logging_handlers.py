"""Tests for the custom log handlers (database persistence, Discord webhook)."""

import logging
import threading
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from website.extensions import db
from website.logging_config.handlers import DatabaseLogHandler, DiscordWebhookHandler
from website.models import AppLog, System


def _record(msg, level=logging.INFO):
    record = logging.LogRecord(
        name="tests.handlers",
        level=level,
        pathname=__file__,
        lineno=42,
        msg=msg,
        args=None,
        exc_info=None,
    )
    record.trace_id = "test-trace-id"
    record.user_id = "1234"
    record.username = "testuser"
    record.endpoint = "tests.endpoint"
    return record


@pytest.fixture
def cleanup_token(test_app):
    """Yield a unique message token; delete matching app_log rows on teardown.

    The handler writes through its own connection with a real commit (outside
    the test savepoint), so rows must be cleaned up explicitly.
    """
    token = uuid4().hex
    yield token
    with db.engine.begin() as conn:
        conn.execute(
            delete(AppLog.__table__).where(AppLog.__table__.c.message.ilike(f"%{token}%"))
        )


def _fetch_rows(token):
    with db.engine.connect() as conn:
        return conn.execute(
            select(AppLog.__table__).where(AppLog.__table__.c.message.ilike(f"%{token}%"))
        ).all()


# -- DatabaseLogHandler --------------------------------------------------------


def test_emit_persists_structured_record(cleanup_token):
    DatabaseLogHandler().emit(_record(f"hello {cleanup_token}", level=logging.WARNING))

    rows = _fetch_rows(cleanup_token)
    assert len(rows) == 1
    row = rows[0]
    assert row.level == "WARNING"
    assert row.level_no == logging.WARNING
    assert row.logger == "tests.handlers"
    assert row.trace_id == "test-trace-id"
    assert row.user_id == "1234"
    assert row.username == "testuser"
    assert row.endpoint == "tests.endpoint"
    assert row.line == 42


def test_emit_does_not_disturb_db_session(cleanup_token, db_session):
    """Writing a log row never commits (or flushes) the request session."""
    pending = System(name=f"Pending {cleanup_token[:8]}")
    db_session.add(pending)

    DatabaseLogHandler().emit(_record(f"mid-transaction {cleanup_token}"))

    # The in-flight object is still pending: the handler used its own
    # connection and never touched db.session.
    assert pending in db_session.new
    assert len(_fetch_rows(cleanup_token)) == 1


def test_emit_is_noop_without_app_context(cleanup_token):
    handler = DatabaseLogHandler()
    thread = threading.Thread(target=handler.emit, args=(_record(f"no-ctx {cleanup_token}"),))
    thread.start()
    thread.join()

    assert _fetch_rows(cleanup_token) == []


def test_emit_never_raises_on_database_error(test_app):
    record = _record("boom")
    with (
        patch("website.logging_config.handlers.insert", side_effect=RuntimeError("db down")),
        patch.object(DatabaseLogHandler, "handleError") as handle_error,
    ):
        DatabaseLogHandler().emit(record)
    handle_error.assert_called_once()


# -- DiscordWebhookHandler -----------------------------------------------------


def test_webhook_posts_critical_records():
    handler = DiscordWebhookHandler("https://discord.test/webhook")
    with patch("website.logging_config.handlers.requests.post") as post:
        handler.emit(_record("meltdown", level=logging.CRITICAL))

    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "https://discord.test/webhook"
    assert "meltdown" in kwargs["json"]["content"]
    assert kwargs["timeout"] == DiscordWebhookHandler.TIMEOUT_SECONDS


def test_webhook_never_raises():
    handler = DiscordWebhookHandler("https://discord.test/webhook")
    with patch("website.logging_config.handlers.requests.post", side_effect=OSError("down")):
        with patch.object(DiscordWebhookHandler, "handleError") as handle_error:
            handler.emit(_record("meltdown", level=logging.CRITICAL))
    handle_error.assert_called_once()
