"""Tests for the SettingsService configuration resolver."""

import pytest
from flask import current_app

from website.exceptions import ValidationError
from website.models import AppSetting
from website.services.setting import OVERRIDABLE_SETTINGS, SettingsService


@pytest.fixture(autouse=True)
def clean_app_settings(db_session):
    """Ensure the app_setting table is empty around each test.

    The local test database is not rolled back between runs, and these tests
    use fixed keys, so we clear overrides before and after each test.
    """
    db_session.query(AppSetting).delete()
    db_session.commit()
    yield
    db_session.query(AppSetting).delete()
    db_session.commit()


class TestSettingsService:
    def test_get_falls_back_to_env(self, db_session):
        """With no override, get() returns the app.config (env) value."""
        service = SettingsService()
        assert service.get("DISCORD_GM_ROLE_ID") == current_app.config["DISCORD_GM_ROLE_ID"]

    def test_get_returns_override(self, db_session):
        """A stored override takes precedence over the env value."""
        service = SettingsService()
        service.set("DISCORD_GM_ROLE_ID", "override-role-id")
        assert service.get("DISCORD_GM_ROLE_ID") == "override-role-id"

    def test_empty_value_clears_override(self, db_session):
        """Setting an empty value removes the override and restores the env value."""
        service = SettingsService()
        service.set("POSTS_CHANNEL_ID", "custom-channel")
        assert service.get("POSTS_CHANNEL_ID") == "custom-channel"

        service.set("POSTS_CHANNEL_ID", "   ")
        assert db_session.get(AppSetting, "POSTS_CHANNEL_ID") is None
        assert service.get("POSTS_CHANNEL_ID") == current_app.config["POSTS_CHANNEL_ID"]

    def test_set_rejects_non_overridable_key(self, db_session):
        """Secrets and other non-allowlisted keys cannot be overridden."""
        service = SettingsService()
        with pytest.raises(ValidationError):
            service.set("DISCORD_BOT_TOKEN", "leak")

    def test_set_many_rejects_unknown_keys(self, db_session):
        """set_many validates every key before writing anything."""
        service = SettingsService()
        with pytest.raises(ValidationError):
            service.set_many({"DISCORD_GM_ROLE_ID": "ok", "SECRET": "nope"})
        # Nothing should have been persisted.
        assert db_session.get(AppSetting, "DISCORD_GM_ROLE_ID") is None

    def test_set_many_applies_and_records_author(self, db_session):
        """set_many persists each override with the author id."""
        service = SettingsService()
        service.set_many(
            {"DISCORD_ADMIN_ROLE_ID": "admin-role", "DISCORD_PLAYER_ROLE_ID": ""},
            updated_by_id="admin-123",
        )
        stored = db_session.get(AppSetting, "DISCORD_ADMIN_ROLE_ID")
        assert stored.value == "admin-role"
        assert stored.updated_by_id == "admin-123"
        # Empty value was not stored.
        assert db_session.get(AppSetting, "DISCORD_PLAYER_ROLE_ID") is None

    def test_direct_permissions_default_disabled(self, db_session):
        """With no stored value, direct-permission mode is off."""
        service = SettingsService()
        assert service.is_direct_permissions_enabled() is False

    def test_direct_permissions_round_trip(self, db_session):
        """Enabling then disabling direct-permission mode round-trips."""
        service = SettingsService()
        service.set_direct_permissions(True, updated_by_id="admin-1")
        assert service.is_direct_permissions_enabled() is True
        service.set_direct_permissions(False)
        assert service.is_direct_permissions_enabled() is False

    def test_role_auto_threshold_default(self, db_session):
        """Unset threshold falls back to the constant default."""
        from config.constants import DISCORD_ROLE_AUTO_THRESHOLD_DEFAULT

        service = SettingsService()
        assert service.get_role_auto_threshold() == DISCORD_ROLE_AUTO_THRESHOLD_DEFAULT

    def test_role_auto_threshold_round_trip(self, db_session):
        """A stored threshold is read back as an integer."""
        service = SettingsService()
        service.set_role_auto_threshold(200, updated_by_id="admin-1")
        assert service.get_role_auto_threshold() == 200

    def test_role_auto_threshold_rejects_invalid(self, db_session):
        """Non-positive or non-integer thresholds are rejected."""
        service = SettingsService()
        with pytest.raises(ValidationError):
            service.set_role_auto_threshold("nope")
        with pytest.raises(ValidationError):
            service.set_role_auto_threshold(0)

    def test_get_effective_describes_all_keys(self, db_session):
        """get_effective() exposes env, override and effective values per key."""
        service = SettingsService()
        service.set("DISCORD_GUILD_NAME", "Custom Guild")
        effective = {item["key"]: item for item in service.get_effective()}

        assert len(effective) == len(OVERRIDABLE_SETTINGS)
        guild = effective["DISCORD_GUILD_NAME"]
        assert guild["override"] == "Custom Guild"
        assert guild["effective"] == "Custom Guild"
        assert guild["env_value"] == current_app.config["DISCORD_GUILD_NAME"]
