import pytest

from website.models.user_system_interest import UserSystemInterest


@pytest.fixture
def sample_interest():
    """Reusable UserSystemInterest instance."""
    return UserSystemInterest(
        user_id="111111111111111111", system_id=1, role="player", note="Dispo le week-end"
    )


def test_to_dict(sample_interest):
    data = sample_interest.to_dict()
    assert data == {
        "user_id": "111111111111111111",
        "system_id": 1,
        "role": "player",
        "note": "Dispo le week-end",
    }


def test_from_dict_creates_interest():
    data = {"user_id": "222222222222222222", "system_id": 2, "role": "gm", "note": None}
    interest = UserSystemInterest.from_dict(data)
    assert isinstance(interest, UserSystemInterest)
    assert interest.user_id == "222222222222222222"
    assert interest.system_id == 2
    assert interest.role == "gm"
    assert interest.note is None


def test_update_from_dict(sample_interest):
    updated = sample_interest.update_from_dict({"note": "Nouvelle dispo"})
    assert updated is sample_interest
    assert sample_interest.note == "Nouvelle dispo"


def test_repr_contains_info(sample_interest):
    rep = repr(sample_interest)
    assert "UserSystemInterest" in rep
    assert "111111111111111111" in rep
    assert "player" in rep


def test_equality_and_inequality():
    i1 = UserSystemInterest(user_id="1", system_id=1, role="player", note=None)
    i2 = UserSystemInterest(user_id="1", system_id=1, role="player", note=None)
    i3 = UserSystemInterest(user_id="1", system_id=1, role="gm", note=None)

    assert i1 == i2
    assert i1 != i3


def test_equality_with_non_interest_returns_notimplemented(sample_interest):
    assert sample_interest.__eq__("not an interest") is NotImplemented
