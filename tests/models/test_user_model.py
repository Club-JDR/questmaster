from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from config.constants import DEFAULT_AVATAR
from website.exceptions import ValidationError
from website.models.user import User


@pytest.mark.parametrize("uid", ["12345678901234567", "9876543210987654321"])
def test_user_init_valid(uid):
    user = User(id=uid, name="Alice")
    assert user.id == uid
    assert user.name == "Alice"


@pytest.mark.parametrize("uid", ["123", "abc", ""])
def test_user_init_invalid(uid):
    with pytest.raises(ValidationError):
        User(id=uid)


def test_user_init_with_username():
    user = User(id="12345678901234567", name="Alice", username="alice123")
    assert user.username == "alice123"


def test_user_init_without_username():
    user = User(id="12345678901234567", name="Alice")
    assert user.username is None


def test_slug_name_returns_username_when_set():
    user = User(id="12345678901234567", name="Alice Display", username="alice123")
    assert user.slug_name == "alice123"


def test_slug_name_falls_back_to_name():
    user = User(id="12345678901234567", name="Alice Display")
    assert user.slug_name == "Alice Display"


def test_display_name_defaults(monkeypatch):
    user = User(id="12345678901234567", name="Inconnu")

    # Patch get_user_profile to return a fake profile
    monkeypatch.setattr(
        "website.models.user.get_user_profile",
        lambda uid: {"name": "Bob", "avatar": "/avatar.png", "username": "bob"},
    )
    name = user.display_name
    assert name.startswith("Bob")
    assert f"<@{user.id}>" in name


def test_trophy_summary():
    user = User(id="12345678901234567", name="Alice")
    # Mock trophies - properly configure mock attributes
    mock_trophy = MagicMock()
    mock_trophy.name = "Trophy1"
    mock_trophy.icon = "icon1"

    mock_user_trophy = MagicMock()
    mock_user_trophy.trophy = mock_trophy
    mock_user_trophy.quantity = 2

    user.trophies = [mock_user_trophy]
    summary = user.trophy_summary
    assert summary == [{"name": "Trophy1", "icon": "icon1", "quantity": 2}]


def test_to_dict():
    user = User(id="12345678901234567", name="Alice")
    d = user.to_dict()
    assert d["id"] == "12345678901234567"
    assert d["name"] == "Alice"
    assert d["username"] is None
    assert d["avatar"] == DEFAULT_AVATAR
    assert d["is_gm"] is False


def test_to_dict_includes_username():
    user = User(id="12345678901234567", name="Alice", username="alice123")
    d = user.to_dict()
    assert d["username"] == "alice123"


def test_from_dict_and_from_json():
    data = {
        "id": "12345678901234567",
        "name": "Eve",
        "username": "eve",
        "avatar": "/img/eve.png",
        "is_gm": True,
        "is_admin": True,
        "is_player": False,
    }
    user = User.from_dict(data)
    assert isinstance(user, User)
    assert user.id == "12345678901234567"
    assert user.name == "Eve"
    assert user.username == "eve"
    assert user.avatar == "/img/eve.png"
    assert user.is_gm is True
    assert user.is_admin is True
    assert user.is_player is False

    user2 = User.from_json(data)
    assert user2.id == "12345678901234567"
    assert user2.name == "Eve"


def test_from_dict_without_username():
    data = {"id": "12345678901234567", "name": "Alice"}
    user = User.from_dict(data)
    assert user.username is None


def test_update_from_dict():
    user = User(id="12345678901234567", name="Alice")
    user.update_from_dict({"name": "Bob"})
    assert user.name == "Bob"


def test_update_from_dict_sets_username():
    user = User(id="12345678901234567", name="Alice")
    user.update_from_dict({"username": "alice123"})
    assert user.username == "alice123"


def test_update_from_dict_ignores_protected_fields():
    user = User(id="12345678901234567", name="Alice")
    user.update_from_dict(
        {
            "id": "99999999999999999",
            "name": "Bob",
            "games_gm": ["should_be_ignored"],
            "trophies": ["should_be_ignored"],
        }
    )
    # Only "name" should be updated (User.update_from_dict only allows "name")
    assert user.name == "Bob"
    # id unchanged
    assert user.id == "12345678901234567"


def test_repr_eq_ne():
    u1 = User(id="12345678901234567", name="Alice")
    u2 = User(id="12345678901234567", name="Alice")
    u3 = User(id="9876543210987654321", name="Bob")

    assert repr(u1) == "Alice <12345678901234567>"
    assert u1 == u2
    assert u1 != u3


@patch("website.models.user.get_user_roles")
def test_refresh_roles(mock_get_roles):
    # Create a minimal Flask app with proper context
    app = Flask(__name__)
    app.config["DISCORD_GM_ROLE_ID"] = "gm"
    app.config["DISCORD_ADMIN_ROLE_ID"] = "admin"
    app.config["DISCORD_PLAYER_ROLE_ID"] = "player"

    user = User(id="12345678901234567", name="Alice")
    mock_get_roles.return_value = ["gm", "admin"]

    # Run within app context
    with app.app_context():
        user.refresh_roles()
        assert user.is_gm is True
        assert user.is_admin is True
        assert user.is_player is False


def test_not_player_as_of_default_none():
    user = User(id="12345678901234567", name="Alice")
    assert user.not_player_as_of is None


def test_to_dict_includes_not_player_as_of_none():
    user = User(id="12345678901234567", name="Alice")
    d = user.to_dict()
    assert "not_player_as_of" in d
    assert d["not_player_as_of"] is None


def test_to_dict_includes_not_player_as_of_set():
    user = User(id="12345678901234567", name="Alice")
    dt = datetime(2025, 6, 15, 12, 0, 0)
    user.not_player_as_of = dt
    d = user.to_dict()
    assert d["not_player_as_of"] == dt.isoformat()


def test_update_from_dict_sets_not_player_as_of():
    user = User(id="12345678901234567", name="Alice")
    dt = datetime(2025, 6, 15, 12, 0, 0)
    user.update_from_dict({"not_player_as_of": dt})
    assert user.not_player_as_of == dt


def test_update_from_dict_clears_not_player_as_of():
    user = User(id="12345678901234567", name="Alice")
    user.not_player_as_of = datetime(2025, 6, 15, 12, 0, 0)
    user.update_from_dict({"not_player_as_of": None})
    assert user.not_player_as_of is None


def test_from_dict_with_not_player_as_of_string():
    data = {
        "id": "12345678901234567",
        "name": "Alice",
        "not_player_as_of": "2025-06-15T12:00:00",
    }
    user = User.from_dict(data)
    assert user.not_player_as_of == datetime(2025, 6, 15, 12, 0, 0)


def test_from_dict_with_not_player_as_of_datetime():
    dt = datetime(2025, 6, 15, 12, 0, 0)
    data = {
        "id": "12345678901234567",
        "name": "Alice",
        "not_player_as_of": dt,
    }
    user = User.from_dict(data)
    assert user.not_player_as_of == dt


def test_from_dict_without_not_player_as_of():
    data = {"id": "12345678901234567", "name": "Alice"}
    user = User.from_dict(data)
    assert user.not_player_as_of is None


@patch("website.models.user.get_bot")
def test_get_user_profile_returns_username(mock_get_bot, test_app):
    from website.extensions import cache
    from website.models.user import get_user_profile

    mock_bot = MagicMock()
    mock_bot.get_user.return_value = {
        "user": {"username": "alice123", "global_name": "Alice", "avatar": None},
        "nick": None,
        "roles": [],
    }
    mock_get_bot.return_value = mock_bot

    with test_app.app_context():
        cache.clear()
        result = get_user_profile("99999999999999997", force_refresh=True)
        assert result["username"] == "alice123"
        assert result["name"] == "Alice"


@patch("website.models.user.get_bot")
def test_get_user_profile_caches_on_404(mock_get_bot, test_app):
    from website.exceptions import DiscordAPIError
    from website.extensions import cache
    from website.models.user import get_user_profile

    mock_bot = MagicMock()
    mock_bot.get_user.side_effect = DiscordAPIError("Unknown Member", status_code=404)
    mock_get_bot.return_value = mock_bot

    with test_app.app_context():
        cache.clear()
        result = get_user_profile("99999999999999999", force_refresh=True)
        assert result["name"] == "Inconnu"
        assert result["username"] is None
        assert result.get("not_found") is True

        cached = cache.get("user_profile_99999999999999999")
        assert cached is not None
        assert cached.get("not_found") is True


@patch("website.models.user.get_bot")
def test_get_user_profile_does_not_cache_non_404_errors(mock_get_bot, test_app):
    from website.exceptions import DiscordAPIError
    from website.extensions import cache
    from website.models.user import get_user_profile

    mock_bot = MagicMock()
    mock_bot.get_user.side_effect = DiscordAPIError("Server Error", status_code=500)
    mock_get_bot.return_value = mock_bot

    with test_app.app_context():
        cache.clear()
        result = get_user_profile("99999999999999998", force_refresh=True)
        assert result["name"] == "Inconnu"
        assert result.get("not_found") is None

        cached = cache.get("user_profile_99999999999999998")
        assert cached is None
