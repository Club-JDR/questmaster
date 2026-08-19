"""Tests for the `clear-cache` Flask CLI command and its shared dispatch table."""

from unittest.mock import patch

import pytest

from website.cli import CACHE_TARGETS, clear_cache_target
from website.exceptions import ValidationError


class TestClearCacheTarget:
    """`clear_cache_target` is shared by the CLI command and the admin cache panel."""

    def test_all_clears_the_whole_cache_backend(self):
        with patch("website.cli.cache") as mock_cache:
            clear_cache_target("all")
        mock_cache.clear.assert_called_once_with()

    @pytest.mark.parametrize(
        ("target", "patch_path"),
        [
            ("systems", "website.services.system.SystemService.clear_cache"),
            ("vtts", "website.services.vtt.VttService.clear_cache"),
            ("calendar", "website.services.game_session.GameSessionService.clear_cache"),
            ("badges", "website.views.misc.clear_leaderboard_cache"),
            ("stats", "website.services.stats.StatsService.invalidate_all"),
            ("discord", "website.services.discord.DiscordService.clear_cache"),
        ],
    )
    def test_named_target_calls_the_owning_service(self, target, patch_path):
        """Each target dispatches to the owning service's own invalidation method."""
        with patch(patch_path) as mock_handler:
            clear_cache_target(target)
        mock_handler.assert_called_once_with()

    def test_unknown_target_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            clear_cache_target("bogus")
        assert exc_info.value.field == "target"


class TestClearCacheCommand:
    """Tests for the `flask clear-cache` CLI command."""

    def test_defaults_to_all(self, test_app):
        with patch("website.cli.clear_cache_target") as mock_clear:
            result = test_app.test_cli_runner().invoke(args=["clear-cache"])

        assert result.exit_code == 0
        mock_clear.assert_called_once_with("all")
        assert "all" in result.output

    @pytest.mark.parametrize("target", CACHE_TARGETS)
    def test_named_target(self, test_app, target):
        with patch("website.cli.clear_cache_target") as mock_clear:
            result = test_app.test_cli_runner().invoke(args=["clear-cache", target])

        assert result.exit_code == 0
        mock_clear.assert_called_once_with(target)
        assert target in result.output

    def test_invalid_target_rejected_by_click(self, test_app):
        """An unknown TARGET is rejected by `click.Choice` before the command body runs."""
        result = test_app.test_cli_runner().invoke(args=["clear-cache", "bogus"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output
