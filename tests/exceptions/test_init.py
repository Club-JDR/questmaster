"""Tests for the exceptions package public API."""

import pytest
from website import exceptions


class TestExceptionPackageExports:
    """Verify all exceptions are importable from the package."""

    def test_questmaster_error(self):
        assert hasattr(exceptions, "QuestMasterError")

    def test_not_found_error(self):
        assert hasattr(exceptions, "NotFoundError")

    def test_unauthorized_error(self):
        assert hasattr(exceptions, "UnauthorizedError")

    def test_validation_error(self):
        assert hasattr(exceptions, "ValidationError")

    def test_database_error(self):
        assert hasattr(exceptions, "DatabaseError")

    def test_discord_error(self):
        assert hasattr(exceptions, "DiscordError")

    def test_discord_api_error(self):
        assert hasattr(exceptions, "DiscordAPIError")

    def test_game_error(self):
        assert hasattr(exceptions, "GameError")

    def test_game_full_error(self):
        assert hasattr(exceptions, "GameFullError")

    def test_game_closed_error(self):
        assert hasattr(exceptions, "GameClosedError")

    def test_duplicate_registration_error(self):
        assert hasattr(exceptions, "DuplicateRegistrationError")

    def test_session_conflict_error(self):
        assert hasattr(exceptions, "SessionConflictError")

    def test_all_exports_match(self):
        expected = {
            "QuestMasterError",
            "NotFoundError",
            "UnauthorizedError",
            "ValidationError",
            "DatabaseError",
            "DiscordError",
            "DiscordAPIError",
            "GameError",
            "GameFullError",
            "GameClosedError",
            "DuplicateRegistrationError",
            "SessionConflictError",
        }
        assert set(exceptions.__all__) == expected
