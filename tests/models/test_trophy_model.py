import pytest
from website.models.trophy import Trophy, UserTrophy


# Trophy tests
@pytest.fixture
def sample_trophy():
    """Reusable Trophy instance."""
    return Trophy(id=1, name="First Game", unique=True, icon="/img/first-game.png")


def test_trophy_to_dict(sample_trophy):
    data = sample_trophy.to_dict()
    assert data["id"] == 1
    assert data["name"] == "First Game"
    assert data["unique"] is True
    assert data["icon"] == "/img/first-game.png"


def test_trophy_from_dict_creates_trophy():
    data = {"id": 2, "name": "Veteran Player", "unique": False, "icon": "/img/vet.png"}
    trophy = Trophy.from_dict(data)
    assert isinstance(trophy, Trophy)
    assert trophy.id == 2
    assert trophy.name == "Veteran Player"
    assert trophy.unique is False
    assert trophy.icon == "/img/vet.png"


def test_trophy_from_dict_defaults_unique():
    """Ensure unique defaults to False when not provided."""
    data = {"id": 3, "name": "Common Trophy"}
    trophy = Trophy.from_dict(data)
    assert trophy.unique is False


def test_trophy_update_from_dict(sample_trophy):
    update_data = {"name": "Updated Trophy", "icon": "/img/new.png"}
    updated = sample_trophy.update_from_dict(update_data)
    assert updated is sample_trophy  # in-place update
    assert sample_trophy.name == "Updated Trophy"
    assert sample_trophy.icon == "/img/new.png"
    # Unchanged fields
    assert sample_trophy.id == 1
    assert sample_trophy.unique is True


def test_trophy_update_from_dict_ignores_protected_fields(sample_trophy):
    sample_trophy.update_from_dict({"id": 999, "name": "Hacked Trophy"})
    # Protected field "id" unchanged
    assert sample_trophy.id == 1
    # Regular field updated normally
    assert sample_trophy.name == "Hacked Trophy"


def test_trophy_str_representation(sample_trophy):
    assert str(sample_trophy) == "First Game"


# UserTrophy tests
@pytest.fixture
def sample_user_trophy():
    """Reusable UserTrophy instance."""
    return UserTrophy(user_id="12345678901234567", trophy_id=1, quantity=3)


def test_user_trophy_to_dict(sample_user_trophy):
    data = sample_user_trophy.to_dict()
    assert data["user_id"] == "12345678901234567"
    assert data["trophy_id"] == 1
    assert data["quantity"] == 3


def test_user_trophy_from_dict_creates_user_trophy():
    data = {"user_id": "98765432109876543", "trophy_id": 2, "quantity": 5}
    user_trophy = UserTrophy.from_dict(data)
    assert isinstance(user_trophy, UserTrophy)
    assert user_trophy.user_id == "98765432109876543"
    assert user_trophy.trophy_id == 2
    assert user_trophy.quantity == 5


def test_user_trophy_from_dict_defaults_quantity():
    """Ensure quantity defaults to 1 when not provided."""
    data = {"user_id": "11111111111111111", "trophy_id": 3}
    user_trophy = UserTrophy.from_dict(data)
    assert user_trophy.quantity == 1


def test_user_trophy_update_from_dict(sample_user_trophy):
    update_data = {"quantity": 10}
    updated = sample_user_trophy.update_from_dict(update_data)
    assert updated is sample_user_trophy  # in-place update
    assert sample_user_trophy.quantity == 10
    # Unchanged fields
    assert sample_user_trophy.user_id == "12345678901234567"
    assert sample_user_trophy.trophy_id == 1


def test_user_trophy_update_ignores_unknown_fields(sample_user_trophy):
    update_data = {"unknown": "value", "quantity": 7}
    sample_user_trophy.update_from_dict(update_data)
    assert not hasattr(sample_user_trophy, "unknown")
    assert sample_user_trophy.quantity == 7


def test_user_trophy_update_from_dict_ignores_protected_fields(sample_user_trophy):
    sample_user_trophy.update_from_dict(
        {
            "user": "should_be_ignored",
            "trophy": "should_be_ignored",
            "quantity": 20,
        }
    )
    # Relationship fields "user" and "trophy" ignored
    assert sample_user_trophy.user_id == "12345678901234567"
    assert sample_user_trophy.trophy_id == 1
    # Regular field updated normally
    assert sample_user_trophy.quantity == 20
