"""Tests for the background scheduler functions."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from config.constants import DEFAULT_AVATAR
from website.scheduler import check_inactive_users, refresh_user_profiles


def _make_user(user_id="12345678901234567", name="TestUser", not_player_as_of=None):
    """Create a mock user object for scheduler tests."""
    user = MagicMock()
    user.id = user_id
    user.name = name
    user.not_player_as_of = not_player_as_of
    user.avatar = DEFAULT_AVATAR
    return user


class TestRefreshUserProfiles:
    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_skips_inactive_users(self, mock_service_cls, mock_db, test_app):
        """Inactive users should not be returned by get_active_user_ids."""
        active_user = _make_user("11111111111111111", name="Active")
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [active_user.id]
        mock_service.get_by_ids.return_value = [active_user]
        mock_service.get_user_profile.return_value = {
            "name": "Active",
            "avatar": DEFAULT_AVATAR,
        }

        refresh_user_profiles(test_app, batch_size=100)

        mock_service.get_active_user_ids.assert_called_once()
        mock_service.get_user_profile.assert_called_once_with(
            "11111111111111111", force_refresh=True
        )

    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_marks_user_inactive_on_404(self, mock_service_cls, mock_db, test_app):
        """When get_user_profile returns not_found, user should be marked inactive."""
        user = _make_user()
        user.not_player_as_of = None
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [user.id]
        mock_service.get_by_ids.return_value = [user]
        mock_service.get_user_profile.return_value = {
            "name": "Inconnu",
            "avatar": DEFAULT_AVATAR,
            "raw": None,
            "not_found": True,
        }

        refresh_user_profiles(test_app, batch_size=100)

        assert user.not_player_as_of is not None

    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_does_not_mark_active_user_inactive(self, mock_service_cls, mock_db, test_app):
        """Normal profile responses should not mark users inactive."""
        user = _make_user()
        user.not_player_as_of = None
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [user.id]
        mock_service.get_by_ids.return_value = [user]
        mock_service.get_user_profile.return_value = {
            "name": "ActiveUser",
            "avatar": "/some/avatar.png",
        }

        refresh_user_profiles(test_app, batch_size=100)

        assert user.not_player_as_of is None

    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_updates_name_and_avatar_on_success(self, mock_service_cls, mock_db, test_app):
        """Successful profile fetch should update user name and avatar."""
        user = _make_user(name="OldName")
        user.not_player_as_of = None
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = [user.id]
        mock_service.get_by_ids.return_value = [user]
        mock_service.get_user_profile.return_value = {
            "name": "NewName",
            "avatar": "/new/avatar.png",
        }

        refresh_user_profiles(test_app, batch_size=100)

        assert user.name == "NewName"
        assert user.avatar == "/new/avatar.png"

    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_no_op_when_no_active_users(self, mock_service_cls, mock_db, test_app):
        """Should not call get_user_profile when there are no active users."""
        mock_service = mock_service_cls.return_value
        mock_service.get_active_user_ids.return_value = []

        refresh_user_profiles(test_app, batch_size=100)

        mock_service.get_user_profile.assert_not_called()


class TestCheckInactiveUsers:
    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_clears_flag_when_user_rejoined(self, mock_service_cls, mock_db, test_app):
        """If an inactive user's profile resolves, clear not_player_as_of."""
        user = _make_user(not_player_as_of=datetime(2025, 1, 1))
        mock_service = mock_service_cls.return_value
        mock_service.get_inactive_user_ids.return_value = [user.id]
        mock_service.get_by_ids.return_value = [user]
        mock_service.get_user_profile.return_value = {
            "name": "ReturnedUser",
            "avatar": "/avatar.png",
        }

        check_inactive_users(test_app, batch_size=100)

        assert user.not_player_as_of is None
        assert user.name == "ReturnedUser"

    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_keeps_flag_when_still_404(self, mock_service_cls, mock_db, test_app):
        """If an inactive user still 404s, keep the flag set."""
        original_date = datetime(2025, 1, 1)
        user = _make_user(not_player_as_of=original_date)
        mock_service = mock_service_cls.return_value
        mock_service.get_inactive_user_ids.return_value = [user.id]
        mock_service.get_by_ids.return_value = [user]
        mock_service.get_user_profile.return_value = {
            "name": "Inconnu",
            "avatar": DEFAULT_AVATAR,
            "raw": None,
            "not_found": True,
        }

        check_inactive_users(test_app, batch_size=100)

        assert user.not_player_as_of == original_date

    @patch("website.scheduler.db")
    @patch("website.scheduler.UserService")
    def test_no_op_when_no_inactive_users(self, mock_service_cls, mock_db, test_app):
        """Should not call get_user_profile when there are no inactive users."""
        mock_service = mock_service_cls.return_value
        mock_service.get_inactive_user_ids.return_value = []

        check_inactive_users(test_app, batch_size=100)

        mock_service.get_user_profile.assert_not_called()
