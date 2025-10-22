import pytest
from website.models.channel import Channel
from config.constants import GAME_TYPES


@pytest.fixture
def sample_channel():
    """Provide a reusable Channel instance."""
    return Channel(id="main", type="campaign", size=10)


def test_to_dict(sample_channel):
    data = sample_channel.to_dict()
    assert data == {"id": "main", "type": "campaign", "size": 10}
    assert isinstance(data, dict)


def test_from_dict_creates_channel():
    data = {"id": "secondary", "type": "oneshot", "size": 5}
    ch = Channel.from_dict(data)
    assert isinstance(ch, Channel)
    assert ch.id == "secondary"
    assert ch.type == "oneshot"
    assert ch.size == 5


def test_from_dict_defaults_size():
    """Ensure size defaults to 0 when not provided."""
    ch = Channel.from_dict({"id": "third", "type": "campaign"})
    assert ch.size == 0


def test_update_from_dict(sample_channel):
    update_data = {"type": "oneshot", "size": 42}
    updated = sample_channel.update_from_dict(update_data)
    assert updated is sample_channel  # in-place update
    assert sample_channel.type == "oneshot"
    assert sample_channel.size == 42


def test_update_from_dict_ignores_unknown_fields(sample_channel):
    update_data = {"foo": "bar", "size": 99}
    sample_channel.update_from_dict(update_data)
    assert not hasattr(sample_channel, "foo")
    assert sample_channel.size == 99


def test_repr_contains_useful_info(sample_channel):
    rep = repr(sample_channel)
    assert "<Channel" in rep
    assert "main" in rep
    assert "campaign" in rep
    assert "10" in rep


def test_equality_and_inequality():
    ch1 = Channel(id="abc", type="campaign", size=5)
    ch2 = Channel(id="abc", type="campaign", size=5)
    ch3 = Channel(id="xyz", type="oneshot", size=3)

    assert ch1 == ch2
    assert ch1 != ch3


def test_equality_with_non_channel_returns_notimplemented(sample_channel):
    assert sample_channel.__eq__("not a channel") is NotImplemented


@pytest.mark.parametrize("game_type", GAME_TYPES)
def test_channel_accepts_valid_game_types(game_type):
    ch = Channel(id=f"id-{game_type}", type=game_type, size=1)
    assert ch.type in GAME_TYPES


def test_channel_handles_zero_and_negative_size():
    ch1 = Channel(id="zero", type="campaign", size=0)
    ch2 = Channel(id="negative", type="oneshot", size=-5)
    assert ch1.size == 0
    assert ch2.size == -5
