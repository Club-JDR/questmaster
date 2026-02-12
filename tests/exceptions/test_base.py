import pytest

from website.exceptions.base import NotFoundError, QuestMasterError, UnauthorizedError


class TestQuestMasterError:
    """Tests for the base QuestMasterError exception."""

    def test_basic_creation(self):
        err = QuestMasterError("Something went wrong")
        assert str(err) == "Something went wrong"
        assert err.message == "Something went wrong"
        assert err.code is None
        assert err.details == {}

    def test_with_code(self):
        err = QuestMasterError("Bad input", code="INVALID_INPUT")
        assert err.message == "Bad input"
        assert err.code == "INVALID_INPUT"

    def test_with_details(self):
        details = {"field": "name", "reason": "too short"}
        err = QuestMasterError("Validation failed", details=details)
        assert err.details == details
        assert err.details["field"] == "name"

    def test_with_all_params(self):
        err = QuestMasterError("Full error", code="ERR_001", details={"key": "value"})
        assert err.message == "Full error"
        assert err.code == "ERR_001"
        assert err.details == {"key": "value"}

    def test_is_exception(self):
        err = QuestMasterError("test")
        assert isinstance(err, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(QuestMasterError) as exc_info:
            raise QuestMasterError("raised error", code="TEST")
        assert exc_info.value.message == "raised error"
        assert exc_info.value.code == "TEST"

    def test_details_default_not_shared(self):
        err1 = QuestMasterError("first")
        err2 = QuestMasterError("second")
        err1.details["key"] = "value"
        assert "key" not in err2.details

    def test_http_status_is_none(self):
        assert QuestMasterError.http_status is None
        err = QuestMasterError("test")
        assert err.http_status is None

    def test_to_dict_basic(self):
        err = QuestMasterError("Something failed", code="FAIL")
        result = err.to_dict()
        assert result == {"error": "Something failed", "code": "FAIL"}

    def test_to_dict_with_details(self):
        err = QuestMasterError("Bad input", code="ERR", details={"field": "name"})
        result = err.to_dict()
        assert result == {
            "error": "Bad input",
            "code": "ERR",
            "details": {"field": "name"},
        }

    def test_to_dict_without_details(self):
        err = QuestMasterError("No details")
        result = err.to_dict()
        assert result == {"error": "No details", "code": None}
        assert "details" not in result

    def test_repr_basic(self):
        err = QuestMasterError("test error")
        assert repr(err) == "QuestMasterError(message='test error')"

    def test_repr_with_code(self):
        err = QuestMasterError("test", code="CODE")
        assert repr(err) == "QuestMasterError(message='test', code='CODE')"

    def test_repr_with_all(self):
        err = QuestMasterError("test", code="C", details={"k": "v"})
        assert repr(err) == "QuestMasterError(message='test', code='C', details={'k': 'v'})"


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_inherits_from_questmaster_error(self):
        err = NotFoundError("Game not found.")
        assert isinstance(err, QuestMasterError)
        assert isinstance(err, Exception)

    def test_default_code(self):
        err = NotFoundError("Not found.")
        assert err.code == "NOT_FOUND"

    def test_custom_code_overrides_default(self):
        err = NotFoundError("User not found.", code="USER_NOT_FOUND")
        assert err.code == "USER_NOT_FOUND"

    def test_http_status(self):
        assert NotFoundError.http_status == 404
        err = NotFoundError("Not found.")
        assert err.http_status == 404

    def test_structured_kwargs(self):
        err = NotFoundError("Game not found.", resource_type="Game", resource_id=42)
        assert err.details["resource_type"] == "Game"
        assert err.details["resource_id"] == 42

    def test_structured_kwargs_optional(self):
        err = NotFoundError("Not found.")
        assert err.details == {}

    def test_structured_kwargs_merged_with_details(self):
        err = NotFoundError(
            "Not found.",
            resource_type="User",
            details={"extra": "info"},
        )
        assert err.details["resource_type"] == "User"
        assert err.details["extra"] == "info"

    def test_can_be_caught_as_base(self):
        with pytest.raises(QuestMasterError):
            raise NotFoundError("not found.")

    def test_can_be_caught_specifically(self):
        with pytest.raises(NotFoundError):
            raise NotFoundError("not found.")

    def test_to_dict(self):
        err = NotFoundError("Game not found.", resource_type="Game", resource_id=1)
        result = err.to_dict()
        assert result["error"] == "Game not found."
        assert result["code"] == "NOT_FOUND"
        assert result["details"]["resource_type"] == "Game"

    def test_repr(self):
        err = NotFoundError("Not found.", resource_type="Game")
        r = repr(err)
        assert "NotFoundError" in r
        assert "NOT_FOUND" in r


class TestUnauthorizedError:
    """Tests for UnauthorizedError."""

    def test_inherits_from_questmaster_error(self):
        err = UnauthorizedError("Access denied.")
        assert isinstance(err, QuestMasterError)
        assert isinstance(err, Exception)

    def test_default_code(self):
        err = UnauthorizedError("Access denied.")
        assert err.code == "UNAUTHORIZED"

    def test_custom_code_overrides_default(self):
        err = UnauthorizedError("Not allowed.", code="FORBIDDEN")
        assert err.code == "FORBIDDEN"

    def test_http_status(self):
        assert UnauthorizedError.http_status == 403
        err = UnauthorizedError("Denied.")
        assert err.http_status == 403

    def test_structured_kwargs(self):
        err = UnauthorizedError("Access denied.", user_id="user123", action="delete_game")
        assert err.details["user_id"] == "user123"
        assert err.details["action"] == "delete_game"

    def test_structured_kwargs_optional(self):
        err = UnauthorizedError("Denied.")
        assert err.details == {}

    def test_can_be_caught_as_base(self):
        with pytest.raises(QuestMasterError):
            raise UnauthorizedError("denied.")

    def test_can_be_caught_specifically(self):
        with pytest.raises(UnauthorizedError):
            raise UnauthorizedError("denied.")

    def test_to_dict(self):
        err = UnauthorizedError("Access denied.", user_id="u1", action="edit")
        result = err.to_dict()
        assert result["error"] == "Access denied."
        assert result["code"] == "UNAUTHORIZED"
        assert result["details"]["user_id"] == "u1"
