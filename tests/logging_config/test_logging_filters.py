"""Tests for logging filters (secret redaction and context enrichment)."""

import logging

from flask import g

from website.logging_config.filters import REDACTED, ContextFilter, SecretRedactionFilter


def _record(msg, args=None, level=logging.INFO):
    return logging.LogRecord(
        name="tests.filters",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=args,
        exc_info=None,
    )


# -- SecretRedactionFilter -----------------------------------------------------


def test_redacts_known_env_secret(monkeypatch):
    secret = "super-secret-bot-token-12345"
    monkeypatch.setenv("DISCORD_BOT_TOKEN", secret)
    record = _record(f"Discord call failed with token {secret} attached")

    assert SecretRedactionFilter().filter(record) is True
    assert secret not in record.getMessage()
    assert REDACTED in record.getMessage()


def test_ignores_very_short_env_values(monkeypatch):
    """Tiny values are skipped so common substrings are not mass-redacted."""
    monkeypatch.setenv("POSTGRES_PASSWORD", "abc")
    record = _record("abcdef is a prefix of the alphabet")

    SecretRedactionFilter().filter(record)
    assert record.getMessage() == "abcdef is a prefix of the alphabet"


def test_redacts_bearer_tokens():
    record = _record("401 when retrying with Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig attached")

    SecretRedactionFilter().filter(record)
    assert "eyJhbGciOiJIUzI1NiJ9" not in record.getMessage()
    assert f"Bearer {REDACTED}" in record.getMessage()


def test_redacts_key_value_credentials():
    record = _record("retrying with password=hunter2secret and api_key: sk-123456")

    SecretRedactionFilter().filter(record)
    message = record.getMessage()
    assert "hunter2secret" not in message
    assert "sk-123456" not in message
    assert message.count(REDACTED) == 2


def test_interpolates_args_and_clears_them(monkeypatch):
    secret = "another-secret-value-6789"
    monkeypatch.setenv("DISCORD_CLIENT_SECRET", secret)
    record = _record("client secret is %s", args=(secret,))

    SecretRedactionFilter().filter(record)
    assert record.args is None
    assert secret not in record.getMessage()
    # Re-reading the message (as each handler does) stays redacted.
    assert secret not in record.getMessage()


# -- ContextFilter -------------------------------------------------------------


def test_context_fields_default_to_none_outside_request():
    record = _record("startup message")

    assert ContextFilter().filter(record) is True
    assert record.trace_id is None
    assert record.user_id is None
    assert record.username is None
    assert record.endpoint is None


def test_context_fields_populated_inside_request(test_app):
    with test_app.test_request_context("/"):
        g.trace_id = "trace-1234"
        from flask import session

        session["user_id"] = "42"
        session["username"] = "gm_maxime"
        record = _record("inside a request")
        ContextFilter().filter(record)

    assert record.trace_id == "trace-1234"
    assert record.user_id == "42"
    assert record.username == "gm_maxime"
    assert record.endpoint is not None
