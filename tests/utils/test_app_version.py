"""Unit tests for website.utils.get_app_version."""

from unittest.mock import patch

from website.utils import get_app_version


class TestGetAppVersion:
    def test_returns_package_metadata_version(self):
        with patch("website.utils.version", return_value="1.2.0"):
            assert get_app_version() == "1.2.0"

    def test_falls_back_to_tag_env_var(self, monkeypatch):
        monkeypatch.setenv("TAG", "v1.0.0-rc1")
        with patch("website.utils.version", side_effect=Exception("not installed")):
            assert get_app_version() == "v1.0.0-rc1"

    def test_falls_back_to_dev(self, monkeypatch):
        monkeypatch.delenv("TAG", raising=False)
        with patch("website.utils.version", side_effect=Exception("not installed")):
            assert get_app_version() == "dev"

    def test_metadata_takes_priority_over_tag(self, monkeypatch):
        monkeypatch.setenv("TAG", "v0.9.0")
        with patch("website.utils.version", return_value="1.2.0"):
            assert get_app_version() == "1.2.0"
