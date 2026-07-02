"""Tests for the background scheduler functions."""

from unittest.mock import patch

from config.constants import DEFAULT_AVATAR
from website.scheduler import (
    check_inactive_users,
    monitor_category_capacity,
    monitor_role_count,
    refresh_user_profiles,
)

USER_ID = "11111111111111111"


def _error_profile():
    """Return a transient-failure profile (non-404 fetch error)."""
    return {
        "name": "Inconnu",
        "avatar": DEFAULT_AVATAR,
        "username": None,
        "raw": None,
        "error": True,
    }


def _not_found_profile():
    """Return a 404 (user left the guild) profile."""
    return {
        "name": "Inconnu",
        "avatar": DEFAULT_AVATAR,
        "raw": None,
        "not_found": True,
        "error": True,
    }


class TestRefreshUserProfiles:
    @patch("website.scheduler.UserService")
    def test_force_refreshes_each_active_user(self, mock_service_cls, test_app):
        """Each sampled active user is fetched with force_refresh=True."""
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [USER_ID]
        mock_service.get_user_profile.return_value = {"name": "Active", "avatar": DEFAULT_AVATAR}

        refresh_user_profiles(test_app, batch_size=100)

        mock_service.get_active_user_ids.assert_called_once()
        mock_service.get_user_profile.assert_called_once_with(USER_ID, force_refresh=True)

    @patch("website.scheduler.UserService")
    def test_marks_user_inactive_on_404(self, mock_service_cls, test_app):
        """When get_user_profile returns not_found, the user is marked inactive."""
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [USER_ID]
        mock_service.get_user_profile.return_value = _not_found_profile()

        refresh_user_profiles(test_app, batch_size=100)

        mock_service.mark_inactive.assert_called_once_with(USER_ID)
        mock_service.persist_profile.assert_not_called()

    @patch("website.scheduler.UserService")
    def test_persists_profile_on_success(self, mock_service_cls, test_app):
        """A successful fetch persists the name via the service (not a no-op)."""
        profile = {"name": "NewName", "avatar": "/new/avatar.png", "username": "newname"}
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [USER_ID]
        mock_service.get_user_profile.return_value = profile

        refresh_user_profiles(test_app, batch_size=100)

        mock_service.persist_profile.assert_called_once_with(USER_ID, profile)
        mock_service.mark_inactive.assert_not_called()

    @patch("website.scheduler.UserService")
    def test_transient_error_does_not_write(self, mock_service_cls, test_app):
        """A non-404 fetch error neither persists nor marks the user inactive."""
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [USER_ID]
        mock_service.get_user_profile.return_value = _error_profile()

        refresh_user_profiles(test_app, batch_size=100)

        mock_service.persist_profile.assert_not_called()
        mock_service.mark_inactive.assert_not_called()

    @patch("website.scheduler.UserService")
    def test_no_op_when_no_active_users(self, mock_service_cls, test_app):
        """Should not call get_user_profile when there are no active users."""
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = []

        refresh_user_profiles(test_app, batch_size=100)

        mock_service.get_user_profile.assert_not_called()


class TestCheckInactiveUsers:
    @patch("website.scheduler.UserService")
    def test_reactivates_when_user_rejoined(self, mock_service_cls, test_app):
        """If an inactive user's profile resolves, persist it and reactivate."""
        profile = {"name": "ReturnedUser", "avatar": "/avatar.png"}
        mock_service = mock_service_cls.return_value
        mock_service.get_inactive_user_ids.return_value = [USER_ID]
        mock_service.get_user_profile.return_value = profile

        check_inactive_users(test_app, batch_size=100)

        mock_service.persist_profile.assert_called_once_with(USER_ID, profile, reactivate=True)

    @patch("website.scheduler.UserService")
    def test_keeps_flag_when_still_404(self, mock_service_cls, test_app):
        """If an inactive user still 404s, do not reactivate."""
        mock_service = mock_service_cls.return_value
        mock_service.get_inactive_user_ids.return_value = [USER_ID]
        mock_service.get_user_profile.return_value = _not_found_profile()

        check_inactive_users(test_app, batch_size=100)

        mock_service.persist_profile.assert_not_called()

    @patch("website.scheduler.UserService")
    def test_transient_error_does_not_reactivate(self, mock_service_cls, test_app):
        """A non-404 fetch error must not reactivate the user."""
        mock_service = mock_service_cls.return_value
        mock_service.get_inactive_user_ids.return_value = [USER_ID]
        mock_service.get_user_profile.return_value = _error_profile()

        check_inactive_users(test_app, batch_size=100)

        mock_service.persist_profile.assert_not_called()

    @patch("website.scheduler.UserService")
    def test_no_op_when_no_inactive_users(self, mock_service_cls, test_app):
        """Should not call get_user_profile when there are no inactive users."""
        mock_service = mock_service_cls.return_value
        mock_service.get_inactive_user_ids.return_value = []

        check_inactive_users(test_app, batch_size=100)

        mock_service.get_user_profile.assert_not_called()


class TestMonitorRoleCount:
    @patch("website.services.discord.DiscordService")
    @patch("website.services.setting.SettingsService")
    def test_enables_direct_permissions_past_threshold(
        self, mock_settings_cls, mock_discord_cls, test_app
    ):
        """When the role count reaches the threshold, direct permissions are enabled."""
        settings = mock_settings_cls.return_value
        settings.is_direct_permissions_enabled.return_value = False
        settings.get_role_auto_threshold.return_value = 230
        mock_discord_cls.return_value.count_roles.return_value = 240

        monitor_role_count(test_app)

        settings.set_direct_permissions.assert_called_once_with(True)

    @patch("website.services.discord.DiscordService")
    @patch("website.services.setting.SettingsService")
    def test_no_change_below_threshold(self, mock_settings_cls, mock_discord_cls, test_app):
        """Below the threshold, the setting is left untouched."""
        settings = mock_settings_cls.return_value
        settings.is_direct_permissions_enabled.return_value = False
        settings.get_role_auto_threshold.return_value = 230
        mock_discord_cls.return_value.count_roles.return_value = 100

        monitor_role_count(test_app)

        settings.set_direct_permissions.assert_not_called()

    @patch("website.services.discord.DiscordService")
    @patch("website.services.setting.SettingsService")
    def test_no_op_when_already_enabled(self, mock_settings_cls, mock_discord_cls, test_app):
        """When already enabled, no role count is fetched and nothing changes."""
        settings = mock_settings_cls.return_value
        settings.is_direct_permissions_enabled.return_value = True

        monitor_role_count(test_app)

        mock_discord_cls.return_value.count_roles.assert_not_called()
        settings.set_direct_permissions.assert_not_called()


class TestMonitorCategoryCapacity:
    @patch("website.services.discord.DiscordService")
    @patch("website.services.channel.ChannelService")
    def test_reconciles_then_provisions_each_type(
        self, mock_channels_cls, mock_discord_cls, test_app
    ):
        """Sizes are reconciled first, then each game type is checked for provisioning."""
        from config.constants import GAME_TYPES

        channels = mock_channels_cls.return_value
        channels.auto_provision_if_full.return_value = None

        monitor_category_capacity(test_app)

        channels.reconcile_sizes.assert_called_once()
        assert channels.auto_provision_if_full.call_count == len(GAME_TYPES)

    @patch("website.services.discord.DiscordService")
    @patch("website.services.channel.ChannelService")
    def test_swallows_discord_errors(self, mock_channels_cls, mock_discord_cls, test_app):
        """A Discord failure is logged and swallowed, never raised."""
        from website.exceptions import DiscordAPIError

        channels = mock_channels_cls.return_value
        channels.reconcile_sizes.side_effect = DiscordAPIError("boom", status_code=500)

        # Should not raise.
        monitor_category_capacity(test_app)

        channels.auto_provision_if_full.assert_not_called()
