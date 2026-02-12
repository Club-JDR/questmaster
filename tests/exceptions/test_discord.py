import pytest

from website.exceptions.base import QuestMasterError
from website.exceptions.discord import DiscordAPIError, DiscordError


class TestDiscordError:
    """Tests for DiscordError."""

    def test_inherits_from_questmaster_error(self):
        err = DiscordError("Discord is down.")
        assert isinstance(err, QuestMasterError)
        assert isinstance(err, Exception)

    def test_default_code(self):
        err = DiscordError("Bot token missing.")
        assert err.code == "DISCORD_ERROR"

    def test_custom_code_overrides_default(self):
        err = DiscordError("Error.", code="CUSTOM")
        assert err.code == "CUSTOM"

    def test_no_http_status(self):
        err = DiscordError("Error.")
        assert err.http_status is None

    def test_to_dict(self):
        err = DiscordError("Bot offline.")
        result = err.to_dict()
        assert result["error"] == "Bot offline."
        assert result["code"] == "DISCORD_ERROR"

    def test_repr(self):
        err = DiscordError("Timeout.")
        r = repr(err)
        assert "DiscordError" in r
        assert "DISCORD_ERROR" in r


class TestDiscordAPIError:
    """Tests for DiscordAPIError."""

    def test_inherits_from_discord_error(self):
        err = DiscordAPIError("Not found", status_code=404)
        assert isinstance(err, DiscordError)
        assert isinstance(err, QuestMasterError)
        assert isinstance(err, Exception)

    def test_basic_creation(self):
        err = DiscordAPIError("Forbidden", status_code=403)
        assert err.status_code == 403
        assert err.response == {}
        assert err.code == "DISCORD_API_403"
        assert "[403]" in err.message

    def test_with_response(self):
        response = {"message": "Missing Access", "code": 50001}
        err = DiscordAPIError("Missing Access", status_code=403, response=response)
        assert err.response == response
        assert err.details["status_code"] == 403
        assert err.details["response"] == response

    def test_rate_limit(self):
        err = DiscordAPIError("Rate limited", status_code=429)
        assert err.status_code == 429
        assert err.code == "DISCORD_API_429"

    def test_server_error(self):
        err = DiscordAPIError("Internal error", status_code=500)
        assert err.status_code == 500
        assert err.code == "DISCORD_API_500"

    def test_str_includes_status_code(self):
        err = DiscordAPIError("Bad request", status_code=400)
        assert "[400]" in str(err)
        assert "Bad request" in str(err)

    def test_can_be_caught_as_discord_error(self):
        with pytest.raises(DiscordError):
            raise DiscordAPIError("error", status_code=500)

    def test_can_be_caught_as_questmaster_error(self):
        with pytest.raises(QuestMasterError):
            raise DiscordAPIError("error", status_code=500)

    def test_can_be_caught_specifically(self):
        with pytest.raises(DiscordAPIError) as exc_info:
            raise DiscordAPIError("test", status_code=404, response={"msg": "nope"})
        assert exc_info.value.status_code == 404
        assert exc_info.value.response == {"msg": "nope"}

    def test_default_response_not_shared(self):
        err1 = DiscordAPIError("a", status_code=400)
        err2 = DiscordAPIError("b", status_code=400)
        err1.response["key"] = "value"
        assert "key" not in err2.response

    def test_to_dict(self):
        err = DiscordAPIError("Forbidden", status_code=403)
        result = err.to_dict()
        assert result["error"] == "[403] Forbidden"
        assert result["code"] == "DISCORD_API_403"
        assert result["details"]["status_code"] == 403

    def test_repr(self):
        err = DiscordAPIError("Not found", status_code=404)
        r = repr(err)
        assert "DiscordAPIError" in r
        assert "DISCORD_API_404" in r
