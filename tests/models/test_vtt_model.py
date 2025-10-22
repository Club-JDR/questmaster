import pytest
from website.models.vtt import Vtt


@pytest.fixture
def sample_vtt():
    """Reusable VTT instance."""
    return Vtt(id=1, name="Roll20", icon="/img/roll20.png")


def test_to_dict(sample_vtt):
    data = sample_vtt.to_dict()
    assert data == {"id": 1, "name": "Roll20", "icon": "/img/roll20.png"}


def test_to_json_and_json_property(sample_vtt):
    assert sample_vtt.to_json() == sample_vtt.to_dict()
    assert sample_vtt.json == sample_vtt.to_dict()


def test_from_dict_creates_vtt():
    data = {"id": 2, "name": "Foundry", "icon": "/img/fvtt.png"}
    vtt = Vtt.from_dict(data)
    assert isinstance(vtt, Vtt)
    assert vtt.id == 2
    assert vtt.name == "Foundry"
    assert vtt.icon == "/img/fvtt.png"


def test_from_json_alias():
    data = {"id": 3, "name": "Fantasy Grounds", "icon": "/img/fg.png"}
    v1 = Vtt.from_dict(data)
    v2 = Vtt.from_json(data)
    assert v1 == v2


def test_update_from_dict(sample_vtt):
    update = {"name": "Foundry", "icon": "/img/fvtt.png"}
    updated = sample_vtt.update_from_dict(update)
    assert updated is sample_vtt
    assert sample_vtt.name == "Foundry"
    assert sample_vtt.icon == "/img/fvtt.png"


def test_update_from_dict_ignores_unknown_fields(sample_vtt):
    sample_vtt.update_from_dict({"unknown": "field"})
    assert not hasattr(sample_vtt, "unknown")


def test_repr_contains_info(sample_vtt):
    rep = repr(sample_vtt)
    assert "Roll20" in rep
    assert "Vtt" in rep
    assert "/img/roll20.png" in rep


def test_equality_and_inequality():
    v1 = Vtt(id=1, name="Foundry", icon="/img/fvtt.png")
    v2 = Vtt(id=1, name="Foundry", icon="/img/fvtt.png")
    v3 = Vtt(id=2, name="Roll20", icon="/img/roll20.png")

    assert v1 == v2
    assert v1 != v3


def test_equality_with_non_vtt_returns_notimplemented(sample_vtt):
    assert sample_vtt.__eq__("not a vtt") is NotImplemented
