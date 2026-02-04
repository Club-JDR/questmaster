import pytest
from website.exceptions.validation import ValidationError
from website.exceptions.base import QuestMasterError


class TestValidationError:
    """Tests for ValidationError."""

    def test_inherits_from_questmaster_error(self):
        err = ValidationError("Invalid input.")
        assert isinstance(err, QuestMasterError)
        assert isinstance(err, Exception)

    def test_basic_creation(self):
        err = ValidationError("Field is required.")
        assert err.message == "Field is required."
        assert err.field is None
        assert err.code == "VALIDATION_ERROR"
        assert err.details == {}

    def test_http_status(self):
        assert ValidationError.http_status == 400
        err = ValidationError("Bad value.")
        assert err.http_status == 400

    def test_with_field(self):
        err = ValidationError("Must be positive.", field="party_size")
        assert err.field == "party_size"
        assert err.details == {"field": "party_size"}

    def test_with_custom_code(self):
        err = ValidationError("Too long.", code="MAX_LENGTH_EXCEEDED")
        assert err.code == "MAX_LENGTH_EXCEEDED"

    def test_with_field_and_details(self):
        details = {"max": 100, "actual": 150}
        err = ValidationError("Too long.", field="name", details=details)
        assert err.field == "name"
        assert err.details["field"] == "name"
        assert err.details["max"] == 100
        assert err.details["actual"] == 150

    def test_str_representation(self):
        err = ValidationError("Bad value.")
        assert str(err) == "Bad value."

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid.", field="email")
        assert exc_info.value.field == "email"

    def test_can_be_caught_as_questmaster_error(self):
        with pytest.raises(QuestMasterError):
            raise ValidationError("Invalid.")

    def test_default_code_when_none(self):
        err = ValidationError("test.", code=None)
        assert err.code == "VALIDATION_ERROR"

    def test_to_dict_basic(self):
        err = ValidationError("Invalid.", field="email")
        result = err.to_dict()
        assert result["error"] == "Invalid."
        assert result["code"] == "VALIDATION_ERROR"
        assert result["details"]["field"] == "email"

    def test_to_dict_with_value_in_details(self):
        err = ValidationError(
            "Invalid Discord UID.", field="id", details={"value": "abc"}
        )
        result = err.to_dict()
        assert result["details"]["field"] == "id"
        assert result["details"]["value"] == "abc"

    def test_repr(self):
        err = ValidationError("Bad input.", field="name")
        r = repr(err)
        assert "ValidationError" in r
        assert "VALIDATION_ERROR" in r
