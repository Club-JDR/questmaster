import pytest
from website.exceptions.database import DatabaseError
from website.exceptions.base import QuestMasterError


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_inherits_from_questmaster_error(self):
        err = DatabaseError("Connection failed.")
        assert isinstance(err, QuestMasterError)
        assert isinstance(err, Exception)

    def test_default_code(self):
        err = DatabaseError("Query timeout.")
        assert err.code == "DATABASE_ERROR"

    def test_custom_code_overrides_default(self):
        err = DatabaseError("Insert failed.", code="DB_INSERT_ERROR")
        assert err.code == "DB_INSERT_ERROR"

    def test_http_status(self):
        assert DatabaseError.http_status == 500
        err = DatabaseError("Error.")
        assert err.http_status == 500

    def test_operation_kwarg(self):
        err = DatabaseError("Insert failed.", operation="insert")
        assert err.details["operation"] == "insert"

    def test_operation_kwarg_optional(self):
        err = DatabaseError("Error.")
        assert err.details == {}

    def test_operation_merged_with_details(self):
        err = DatabaseError("Failed.", operation="update", details={"table": "game"})
        assert err.details["operation"] == "update"
        assert err.details["table"] == "game"

    def test_str_representation(self):
        err = DatabaseError("timeout.")
        assert str(err) == "timeout."

    def test_can_be_raised_and_caught(self):
        with pytest.raises(DatabaseError):
            raise DatabaseError("db error.")

    def test_can_be_caught_as_questmaster_error(self):
        with pytest.raises(QuestMasterError):
            raise DatabaseError("db error.")

    def test_to_dict(self):
        err = DatabaseError("Insert failed.", operation="insert")
        result = err.to_dict()
        assert result["error"] == "Insert failed."
        assert result["code"] == "DATABASE_ERROR"
        assert result["details"]["operation"] == "insert"

    def test_repr(self):
        err = DatabaseError("Timeout.", operation="select")
        r = repr(err)
        assert "DatabaseError" in r
        assert "DATABASE_ERROR" in r
        assert "operation" in r
