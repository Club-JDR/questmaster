import pytest
from website.models.special_event import SpecialEvent


@pytest.fixture
def sample_special_event():
    """Reusable SpecialEvent instance."""
    return SpecialEvent(id=1, name="Halloween", emoji="🎃", color=0xFF6600, active=True)


def test_to_dict(sample_special_event):
    data = sample_special_event.to_dict()
    assert data["id"] == 1
    assert data["name"] == "Halloween"
    assert data["emoji"] == "🎃"
    assert data["color"] == 0xFF6600
    assert data["active"] is True


def test_from_dict_creates_special_event():
    data = {
        "id": 2,
        "name": "Christmas",
        "emoji": "🎄",
        "color": 0x00FF00,
        "active": False,
    }
    event = SpecialEvent.from_dict(data)
    assert isinstance(event, SpecialEvent)
    assert event.id == 2
    assert event.name == "Christmas"
    assert event.emoji == "🎄"
    assert event.color == 0x00FF00
    assert event.active is False


def test_from_dict_defaults_active():
    """Ensure active defaults to False when not provided."""
    data = {"id": 3, "name": "New Year"}
    event = SpecialEvent.from_dict(data)
    assert event.active is False


def test_update_from_dict(sample_special_event):
    update_data = {"name": "Spooky Halloween", "active": False}
    updated = sample_special_event.update_from_dict(update_data)
    assert updated is sample_special_event  # in-place update
    assert sample_special_event.name == "Spooky Halloween"
    assert sample_special_event.active is False
    # Unchanged fields remain the same
    assert sample_special_event.id == 1
    assert sample_special_event.emoji == "🎃"


def test_update_from_dict_ignores_unknown_fields(sample_special_event):
    update_data = {"unknown": "value", "color": 0xFF0000}
    sample_special_event.update_from_dict(update_data)
    assert not hasattr(sample_special_event, "unknown")
    assert sample_special_event.color == 0xFF0000


def test_str_representation(sample_special_event):
    str_repr = str(sample_special_event)
    assert "🎃" in str_repr
    assert "Halloween" in str_repr
    assert "#ff6600" in str_repr  # hex color


def test_str_with_none_color():
    event = SpecialEvent(id=4, name="Test Event", emoji="✨", color=None, active=True)
    str_repr = str(event)
    assert "✨" in str_repr
    assert "Test Event" in str_repr
    assert "()" in str_repr  # empty parens for no color


def test_update_from_dict_ignores_protected_fields(sample_special_event):
    sample_special_event.update_from_dict(
        {
            "id": 999,
            "games": ["should_be_ignored"],
            "name": "Updated Halloween",
        }
    )
    # Protected field "id" unchanged
    assert sample_special_event.id == 1
    # Regular field updated normally
    assert sample_special_event.name == "Updated Halloween"
