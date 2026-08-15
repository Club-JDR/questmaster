"""Tests for the JSON log formatter."""

import json
import logging

from website.logging_config.formatters import CustomJsonFormatter


def _record(msg, **extra):
    record = logging.LogRecord(
        name="tests.formatters",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_format_includes_context_fields():
    record = _record(
        "hello",
        trace_id="trace-1",
        user_id="42",
        username="target_user",
        endpoint="tests.endpoint",
    )

    payload = json.loads(CustomJsonFormatter().format(record))

    assert payload["message"] == "hello"
    assert payload["trace_id"] == "trace-1"
    assert payload["user_id"] == "42"
    assert payload["username"] == "target_user"
    assert payload["endpoint"] == "tests.endpoint"
    assert payload["impersonator_id"] is None
    assert payload["impersonator_username"] is None


def test_format_includes_impersonator_fields_when_set():
    record = _record(
        "impersonated action",
        user_id="42",
        username="target_user",
        impersonator_id="1",
        impersonator_username="real_admin",
    )

    payload = json.loads(CustomJsonFormatter().format(record))

    assert payload["user_id"] == "42"
    assert payload["impersonator_id"] == "1"
    assert payload["impersonator_username"] == "real_admin"
