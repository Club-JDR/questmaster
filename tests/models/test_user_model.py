import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from website.models.user import User
from website.exceptions import ValidationError
from config.constants import DEFAULT_AVATAR


@pytest.mark.parametrize("uid", ["12345678901234567", "9876543210987654321"])
def test_user_init_valid(uid):
    user = User(id=uid, name="Alice")
    assert user.id == uid
    assert user.name == "Alice"


@pytest.mark.parametrize("uid", ["123", "abc", ""])
def test_user_init_invalid(uid):
    with pytest.raises(ValidationError):
        User(id=uid)


def test_display_name_defaults(monkeypatch):
    user = User(id="12345678901234567", name="Inconnu")

    # Patch get_user_profile to return a fake profile
    monkeypatch.setattr(
        "website.models.user.get_user_profile",
        lambda uid: {"name": "Bob", "avatar": "/avatar.png"},
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
    assert d["avatar"] == DEFAULT_AVATAR
    assert d["is_gm"] is False


def test_from_dict_and_from_json():
    data = {
        "id": "12345678901234567",
        "name": "Eve",
        "avatar": "/img/eve.png",
        "is_gm": True,
        "is_admin": True,
        "is_player": False,
    }
    user = User.from_dict(data)
    assert isinstance(user, User)
    assert user.id == "12345678901234567"
    assert user.name == "Eve"
    assert user.avatar == "/img/eve.png"
    assert user.is_gm is True
    assert user.is_admin is True
    assert user.is_player is False

    user2 = User.from_json(data)
    assert user2.id == "12345678901234567"
    assert user2.name == "Eve"


def test_update_from_dict():
    user = User(id="12345678901234567", name="Alice")
    user.update_from_dict({"name": "Bob"})
    assert user.name == "Bob"


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
