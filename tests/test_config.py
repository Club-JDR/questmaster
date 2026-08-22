"""Tests for `config.settings`."""

import pytest

from config.settings import REQUIRED_ENV_VARS, Settings, check_required_env_vars


class TestCheckRequiredEnvVars:
    """Startup should fail fast, naming any missing required variable."""

    def test_passes_when_all_required_vars_are_set(self, monkeypatch):
        for name in REQUIRED_ENV_VARS:
            monkeypatch.setenv(name, "value")

        check_required_env_vars()  # does not raise

    def test_raises_with_missing_var_name_when_unset(self, monkeypatch):
        for name in REQUIRED_ENV_VARS:
            monkeypatch.setenv(name, "value")
        monkeypatch.delenv("FLASK_AUTH_SECRET", raising=False)

        with pytest.raises(RuntimeError, match="FLASK_AUTH_SECRET"):
            check_required_env_vars()

    def test_raises_with_missing_var_name_when_empty(self, monkeypatch):
        for name in REQUIRED_ENV_VARS:
            monkeypatch.setenv(name, "value")
        monkeypatch.setenv("POSTGRES_HOST", "")

        with pytest.raises(RuntimeError, match="POSTGRES_HOST"):
            check_required_env_vars()

    def test_lists_all_missing_vars_at_once(self, monkeypatch):
        for name in REQUIRED_ENV_VARS:
            monkeypatch.delenv(name, raising=False)

        with pytest.raises(RuntimeError) as exc_info:
            check_required_env_vars()

        for name in REQUIRED_ENV_VARS:
            assert name in str(exc_info.value)


class TestEngineOptions:
    """A pooled connection must be pinged/recycled, not trusted forever."""

    def test_pool_pre_ping_and_recycle_are_set(self):
        options = Settings.SQLALCHEMY_ENGINE_OPTIONS
        assert options["pool_pre_ping"] is True
        assert options["pool_recycle"] == 1800


class TestMaxContentLength:
    """An unbounded request body is a resource-exhaustion vector."""

    def test_max_content_length_is_set(self):
        assert Settings.MAX_CONTENT_LENGTH is not None
        assert Settings.MAX_CONTENT_LENGTH > 0

    def test_oversized_request_is_rejected(self, client):
        oversized = b"x" * (Settings.MAX_CONTENT_LENGTH + 1)
        response = client.post(
            "/annonce/",
            data=oversized,
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 413
