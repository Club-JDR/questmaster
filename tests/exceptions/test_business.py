import pytest
from website.exceptions.business import (
    GameError,
    GameFullError,
    GameClosedError,
    DuplicateRegistrationError,
    SessionConflictError,
)
from website.exceptions.base import QuestMasterError


class TestGameError:
    """Tests for GameError."""

    def test_inherits_from_questmaster_error(self):
        err = GameError("Game problem.")
        assert isinstance(err, QuestMasterError)
        assert isinstance(err, Exception)

    def test_default_code(self):
        err = GameError("Something wrong with game.")
        assert err.code == "GAME_ERROR"

    def test_custom_code_overrides_default(self):
        err = GameError("Error.", code="CUSTOM")
        assert err.code == "CUSTOM"

    def test_http_status(self):
        assert GameError.http_status == 409
        err = GameError("Error.")
        assert err.http_status == 409

    def test_to_dict(self):
        err = GameError("Game problem.")
        result = err.to_dict()
        assert result["error"] == "Game problem."
        assert result["code"] == "GAME_ERROR"


class TestGameFullError:
    """Tests for GameFullError."""

    def test_inherits_from_game_error(self):
        err = GameFullError("Game is full.")
        assert isinstance(err, GameError)
        assert isinstance(err, QuestMasterError)

    def test_default_code(self):
        err = GameFullError("Game is full.")
        assert err.code == "GAME_FULL"

    def test_http_status_inherited(self):
        err = GameFullError("Game is full.")
        assert err.http_status == 409

    def test_structured_kwargs(self):
        err = GameFullError("Game is full.", game_id=1, max_players=4)
        assert err.details["game_id"] == 1
        assert err.details["max_players"] == 4

    def test_structured_kwargs_optional(self):
        err = GameFullError("Game is full.")
        assert err.details == {}

    def test_structured_kwargs_merged_with_details(self):
        err = GameFullError("Full.", game_id=1, details={"extra": "info"})
        assert err.details["game_id"] == 1
        assert err.details["extra"] == "info"

    def test_can_be_raised_and_caught_as_game_error(self):
        with pytest.raises(GameError):
            raise GameFullError("full.")

    def test_to_dict_with_details(self):
        err = GameFullError("Game is full.", game_id=1, max_players=4)
        result = err.to_dict()
        assert result["error"] == "Game is full."
        assert result["code"] == "GAME_FULL"
        assert result["details"]["game_id"] == 1
        assert result["details"]["max_players"] == 4

    def test_repr(self):
        err = GameFullError("Game is full.", game_id=1, max_players=4)
        r = repr(err)
        assert "GameFullError" in r
        assert "GAME_FULL" in r
        assert "game_id" in r


class TestGameClosedError:
    """Tests for GameClosedError."""

    def test_inherits_from_game_error(self):
        err = GameClosedError("Game is closed.")
        assert isinstance(err, GameError)
        assert isinstance(err, QuestMasterError)

    def test_default_code(self):
        err = GameClosedError("Game is closed for registration.")
        assert err.code == "GAME_CLOSED"

    def test_structured_kwargs(self):
        err = GameClosedError("Game is closed.", game_id=42)
        assert err.details["game_id"] == 42

    def test_can_be_raised_and_caught_as_game_error(self):
        with pytest.raises(GameError):
            raise GameClosedError("closed.")

    def test_can_be_caught_specifically(self):
        with pytest.raises(GameClosedError):
            raise GameClosedError("closed.")

    def test_to_dict(self):
        err = GameClosedError("Game is closed.", game_id=5)
        result = err.to_dict()
        assert result["code"] == "GAME_CLOSED"
        assert result["details"]["game_id"] == 5


class TestDuplicateRegistrationError:
    """Tests for DuplicateRegistrationError."""

    def test_inherits_from_game_error(self):
        err = DuplicateRegistrationError("Already registered.")
        assert isinstance(err, GameError)
        assert isinstance(err, QuestMasterError)

    def test_default_code(self):
        err = DuplicateRegistrationError("Already registered.")
        assert err.code == "DUPLICATE_REGISTRATION"

    def test_structured_kwargs(self):
        err = DuplicateRegistrationError(
            "User is already registered.", game_id=1, user_id="u123"
        )
        assert err.details["game_id"] == 1
        assert err.details["user_id"] == "u123"

    def test_can_be_raised_and_caught_as_game_error(self):
        with pytest.raises(GameError):
            raise DuplicateRegistrationError("duplicate.")

    def test_can_be_caught_specifically(self):
        with pytest.raises(DuplicateRegistrationError):
            raise DuplicateRegistrationError("duplicate.")

    def test_to_dict(self):
        err = DuplicateRegistrationError("Already registered.", game_id=1, user_id="u1")
        result = err.to_dict()
        assert result["code"] == "DUPLICATE_REGISTRATION"
        assert result["details"]["game_id"] == 1
        assert result["details"]["user_id"] == "u1"


class TestSessionConflictError:
    """Tests for SessionConflictError."""

    def test_inherits_from_game_error(self):
        err = SessionConflictError("Sessions overlap.")
        assert isinstance(err, GameError)
        assert isinstance(err, QuestMasterError)

    def test_default_code(self):
        err = SessionConflictError("Session overlaps.")
        assert err.code == "SESSION_CONFLICT"

    def test_structured_kwargs(self):
        err = SessionConflictError(
            "Session overlaps with an existing session.", game_id=10
        )
        assert err.details["game_id"] == 10

    def test_can_be_raised_and_caught_as_game_error(self):
        with pytest.raises(GameError):
            raise SessionConflictError("conflict.")

    def test_can_be_caught_specifically(self):
        with pytest.raises(SessionConflictError):
            raise SessionConflictError("conflict.")

    def test_to_dict(self):
        err = SessionConflictError("Overlap.", game_id=3)
        result = err.to_dict()
        assert result["code"] == "SESSION_CONFLICT"
        assert result["details"]["game_id"] == 3


class TestExceptionHierarchyCatching:
    """Test that exception hierarchy allows proper catch patterns."""

    def test_catch_all_game_errors(self):
        """All game-related exceptions should be catchable via GameError."""
        exceptions = [
            GameFullError("full."),
            GameClosedError("closed."),
            DuplicateRegistrationError("duplicate."),
            SessionConflictError("conflict."),
        ]
        for exc in exceptions:
            with pytest.raises(GameError):
                raise exc

    def test_catch_all_as_questmaster_error(self):
        """All exceptions should be catchable via QuestMasterError."""
        exceptions = [
            GameError("game."),
            GameFullError("full."),
            GameClosedError("closed."),
            DuplicateRegistrationError("duplicate."),
            SessionConflictError("conflict."),
        ]
        for exc in exceptions:
            with pytest.raises(QuestMasterError):
                raise exc

    def test_specific_catch_does_not_catch_siblings(self):
        """GameFullError catch should not catch GameClosedError."""
        with pytest.raises(GameClosedError):
            try:
                raise GameClosedError("closed.")
            except GameFullError:
                pytest.fail("GameFullError should not catch GameClosedError")

    def test_all_subclasses_have_game_error_http_status(self):
        """All game subclasses inherit http_status from GameError."""
        for cls in [
            GameFullError,
            GameClosedError,
            DuplicateRegistrationError,
            SessionConflictError,
        ]:
            assert cls("test.").http_status == 409

    def test_all_subclasses_have_specific_default_codes(self):
        """Each subclass has its own default code, not GAME_ERROR."""
        assert GameFullError("t.").code == "GAME_FULL"
        assert GameClosedError("t.").code == "GAME_CLOSED"
        assert DuplicateRegistrationError("t.").code == "DUPLICATE_REGISTRATION"
        assert SessionConflictError("t.").code == "SESSION_CONFLICT"
